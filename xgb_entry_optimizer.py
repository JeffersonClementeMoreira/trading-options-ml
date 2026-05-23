#!/usr/bin/env python3
"""Gera dataset multi-horario/multi-horizonte e treina XGBoost para direcao e estrategia.

Objetivos:
- Target ternario de direcao (DOWN / FLAT / UP) no fechamento D+N 14:00.
- Probabilidade de acerto para CALL-ONLY, PUT-ONLY e STRANGLE.
- Politica com opcao de NO_TRADE (nao entrar) por limiar de confianca.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

import options_v3 as ov3


DIRECTION_DOWN = 0
DIRECTION_FLAT = 1
DIRECTION_UP = 2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Treino XGBoost para direcao + estrategia")
    parser.add_argument("--file", type=str, required=True, help="CSV OHLC")
    parser.add_argument("--tail", type=int, default=10000)
    parser.add_argument("--backtest-days", type=int, default=220)
    parser.add_argument("--hour-start", type=int, default=8)
    parser.add_argument("--hour-end", type=int, default=20)
    parser.add_argument("--minute", type=int, default=0)
    parser.add_argument("--expiry-hour", type=int, default=14)
    parser.add_argument("--expiry-minute", type=int, default=0)
    parser.add_argument("--expiry-days-list", type=str, default="1,2,3", help="Ex: 1,2,3,5")
    parser.add_argument("--flat-threshold-ratio", type=float, default=0.10, help="Faixa FLAT como percentual do expected_move")
    parser.add_argument("--no-trade-threshold", type=float, default=0.62, help="Limiar minimo para entrar")
    parser.add_argument("--test-ratio", type=float, default=0.25)
    parser.add_argument("--iv", type=float, default=0.25)
    parser.add_argument("--days", type=int, default=5)
    parser.add_argument("--strategy-mode", type=str, default="strangle", choices=["strangle", "call-only", "put-only"])
    parser.add_argument(
        "--prefer-external-features",
        action="store_true",
        help="Usa features pre-calculadas do MT5 no backtest interno (quando disponiveis)",
    )
    parser.add_argument(
        "--allow-post-entry-features",
        action="store_true",
        help="Inclui touched_support/touched_resistance/entered_zone no treino (somente para estudo; pode gerar vazamento)",
    )
    parser.add_argument("--dataset-only", action="store_true", help="Gera dataset/targets sem treinar modelos")
    parser.add_argument("--keep-intermediate", action="store_true", help="Mantem CSVs intermediarios gerados pelo backtest interno")
    parser.add_argument("--output", type=str, default="analytics/stats/xgb_entry_optimizer_results.csv")
    return parser.parse_args()


def _load_ml_dependencies() -> tuple[object | None, object | None, object | None]:
    try:
        from sklearn.metrics import accuracy_score, classification_report
        from xgboost import XGBClassifier
        return XGBClassifier, accuracy_score, classification_report
    except Exception:
        return None, None, None


def _build_target_ternary(df: pd.DataFrame, flat_threshold_ratio: float) -> pd.Series:
    move = pd.to_numeric(df["next_day_close"], errors="coerce") - pd.to_numeric(df["analysis_price"], errors="coerce")
    em = pd.to_numeric(df["expected_move"], errors="coerce").abs()
    flat_band = em * float(flat_threshold_ratio)

    target = pd.Series(np.full(len(df), DIRECTION_FLAT), index=df.index)
    target = target.mask(move > flat_band, DIRECTION_UP)
    target = target.mask(move < (-flat_band), DIRECTION_DOWN)
    return target.astype(int)


def _safe_num(df: pd.DataFrame, col: str, default: float = 0.0) -> pd.Series:
    if col not in df.columns:
        return pd.Series(np.full(len(df), default), index=df.index)
    return pd.to_numeric(df[col], errors="coerce").fillna(default)


def _prepare_features(df: pd.DataFrame, allow_post_entry_features: bool = False) -> pd.DataFrame:
    out = pd.DataFrame(index=df.index)

    # Features de contexto/fluxo
    out["analysis_price"] = _safe_num(df, "analysis_price")
    out["expected_move"] = _safe_num(df, "expected_move")
    out["sd_confluence"] = _safe_num(df, "sd_confluence")
    out["flow_score"] = _safe_num(df, "flow_score")
    out["er_mean"] = _safe_num(df, "er_mean")
    out["kama_slope"] = _safe_num(df, "kama_slope")

    # Features de precificacao/probabilidade
    out["best_call_delta"] = _safe_num(df, "best_call_delta")
    out["best_put_delta"] = _safe_num(df, "best_put_delta")
    out["mean_primary_delta"] = _safe_num(df, "mean_primary_delta")
    out["chance_call_only_pct"] = _safe_num(df, "chance_call_only_pct")
    out["chance_put_only_pct"] = _safe_num(df, "chance_put_only_pct")
    out["chance_strangle_pct"] = _safe_num(df, "chance_strangle_pct")

    # Features de zona/condicao
    if allow_post_entry_features:
        out["touched_support"] = _safe_num(df, "touched_support")
        out["touched_resistance"] = _safe_num(df, "touched_resistance")
        out["entered_zone"] = _safe_num(df, "entered_zone")

    # Features de timing/horizonte
    out["entry_hour"] = _safe_num(df, "entry_hour")
    out["entry_minute"] = _safe_num(df, "entry_minute")
    out["expiry_days"] = _safe_num(df, "expiry_days", default=1.0)

    # Derivadas de moneyness / simetria
    call_strike = _safe_num(df, "expected_call_strike")
    put_strike = _safe_num(df, "expected_put_strike")
    spot = out["analysis_price"].replace(0, np.nan)
    em = out["expected_move"].replace(0, np.nan)

    out["dist_call_over_em"] = ((call_strike - spot) / em).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["dist_put_over_em"] = ((spot - put_strike) / em).replace([np.inf, -np.inf], np.nan).fillna(0.0)
    out["strike_asymmetry"] = out["dist_call_over_em"] - out["dist_put_over_em"]

    # Regime categorical
    if "regime" in df.columns:
        regime = df["regime"].fillna("UNKNOWN").astype(str)
        regime_dummies = pd.get_dummies(regime, prefix="regime", dtype=float)
        out = pd.concat([out, regime_dummies], axis=1)

    return out.fillna(0.0)


def _train_multiclass_xgb(XGBClassifier: object, X_train: pd.DataFrame, y_train: pd.Series, num_class: int) -> object:
    model = XGBClassifier(
        objective="multi:softprob",
        num_class=num_class,
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=4,
        eval_metric="mlogloss",
    )
    model.fit(X_train, y_train)
    return model


def _train_binary_xgb(XGBClassifier: object, X_train: pd.DataFrame, y_train: pd.Series) -> object:
    model = XGBClassifier(
        objective="binary:logistic",
        n_estimators=250,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.9,
        colsample_bytree=0.9,
        reg_lambda=1.0,
        random_state=42,
        n_jobs=4,
        eval_metric="logloss",
    )
    model.fit(X_train, y_train.astype(int))
    return model


def _build_policy_actions(df_test: pd.DataFrame, no_trade_threshold: float) -> pd.DataFrame:
    work = df_test.copy()

    # Heuristica combinando direcao + probabilidade de sucesso da estrategia.
    work["score_call"] = work["p_call_success"] + 0.20 * work["p_up"] + 0.08 * work["touched_support"]
    work["score_put"] = work["p_put_success"] + 0.20 * work["p_down"] + 0.08 * work["touched_resistance"]
    work["score_strangle"] = work["p_strangle_success"] + 0.12 * work["p_flat"] - 0.05 * work["entered_zone"]

    best = work[["score_call", "score_put", "score_strangle"]].idxmax(axis=1)
    work["best_strategy"] = best.map(
        {
            "score_call": "CALL_ONLY",
            "score_put": "PUT_ONLY",
            "score_strangle": "STRANGLE",
        }
    )
    work["best_score"] = work[["score_call", "score_put", "score_strangle"]].max(axis=1)

    # NO_TRADE se confianca baixa
    work["action"] = np.where(work["best_score"] >= no_trade_threshold, work["best_strategy"], "NO_TRADE")

    # Outcome da acao
    work["action_hit"] = 0
    work.loc[(work["action"] == "CALL_ONLY") & (work["success_call_only"] == 1), "action_hit"] = 1
    work.loc[(work["action"] == "PUT_ONLY") & (work["success_put_only"] == 1), "action_hit"] = 1
    work.loc[(work["action"] == "STRANGLE") & (work["success_strangle"] == 1), "action_hit"] = 1

    # Para NO_TRADE, nao conta como erro; medimos separadamente taxa de cobertura.
    work["entered_trade"] = (work["action"] != "NO_TRADE").astype(int)
    return work


def _collect_training_rows(args: argparse.Namespace) -> pd.DataFrame:
    csv_file = Path(args.file).expanduser().resolve()
    if not csv_file.exists():
        raise FileNotFoundError(f"Arquivo nao encontrado: {csv_file}")

    expiry_days_list = [int(x.strip()) for x in args.expiry_days_list.split(",") if x.strip()]
    hours = list(range(args.hour_start, args.hour_end + 1))

    rows = []
    for expiry_days in expiry_days_list:
        for hour in hours:
            bt_df, out_csv, out_html = ov3._run_backtest_table(
                csv_file=csv_file,
                iv=args.iv,
                days=args.days,
                expiry_days=expiry_days,
                tail_size=args.tail,
                analysis_hour=hour,
                analysis_minute=args.minute,
                expiry_hour=args.expiry_hour,
                expiry_minute=args.expiry_minute,
                backtest_days=args.backtest_days,
                strategy_mode=args.strategy_mode,
                save_html=False,
                prefer_external_features=args.prefer_external_features,
            )

            bt_df = bt_df.copy()
            bt_df["entry_hour"] = hour
            bt_df["entry_minute"] = args.minute
            bt_df["expiry_days"] = expiry_days
            rows.append(bt_df)

            if not args.keep_intermediate:
                try:
                    out_csv.unlink(missing_ok=True)
                except Exception:
                    pass
                if out_html is not None:
                    try:
                        out_html.unlink(missing_ok=True)
                    except Exception:
                        pass

            print(f"Coletado: hour={hour:02d}:{args.minute:02d} | D+{expiry_days} | linhas={len(bt_df)}")

    if not rows:
        raise ValueError("Nenhuma linha coletada para treino")

    full = pd.concat(rows, ignore_index=True)
    full["analysis_timestamp"] = pd.to_datetime(full["analysis_timestamp"], errors="coerce")
    full = full.dropna(subset=["analysis_timestamp"]).sort_values("analysis_timestamp").reset_index(drop=True)
    return full


def _print_feature_importance(model: object, feature_names: list[str], top_n: int = 15) -> None:
    importances = getattr(model, "feature_importances_", None)
    if importances is None:
        return
    imp = pd.DataFrame({"feature": feature_names, "importance": importances})
    imp = imp.sort_values("importance", ascending=False).head(top_n)
    print("\nTop features (direcao):")
    print(imp.to_string(index=False))


def main() -> int:
    args = parse_args()

    df = _collect_training_rows(args)
    df["target_direction"] = _build_target_ternary(df, flat_threshold_ratio=args.flat_threshold_ratio)

    dataset_out = Path(args.output).expanduser()
    dataset_out.parent.mkdir(parents=True, exist_ok=True)
    dataset_ready = df.copy()
    dataset_ready.to_csv(dataset_out, index=False)
    print(f"Dataset consolidado salvo em: {dataset_out.resolve()}")

    XGBClassifier, accuracy_score, classification_report = _load_ml_dependencies()
    if args.dataset_only or XGBClassifier is None:
        print(
            "Modo dataset-only ativo (ou dependencias ML indisponiveis). "
            "Treino XGBoost pulado, dataset pronto para uso posterior."
        )
        return 0

    # Alvos de sucesso por estrategia
    df["success_call_only"] = df["success_call_only"].astype(int)
    df["success_put_only"] = df["success_put_only"].astype(int)
    df["success_strangle"] = df["success_strangle"].astype(int)

    X = _prepare_features(df, allow_post_entry_features=args.allow_post_entry_features)
    y_dir = df["target_direction"]

    split_idx = int(len(df) * (1.0 - args.test_ratio))
    split_idx = max(1, min(split_idx, len(df) - 1))

    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train, y_test = y_dir.iloc[:split_idx], y_dir.iloc[split_idx:]
    test_meta = df.iloc[split_idx:].copy()

    # Modelo direcional com classes dinamicas (evita falha quando FLAT nao aparece no recorte)
    present_classes = sorted(pd.Series(y_train).dropna().astype(int).unique().tolist())
    class_to_idx = {cls: i for i, cls in enumerate(present_classes)}
    idx_to_class = {i: cls for cls, i in class_to_idx.items()}

    y_train_mapped = y_train.map(class_to_idx).astype(int)
    y_test_mapped = y_test.map(class_to_idx)

    valid_test_mask = y_test_mapped.notna()
    X_test_eval = X_test.loc[valid_test_mask]
    y_test_eval = y_test_mapped.loc[valid_test_mask].astype(int)

    model_dir = _train_multiclass_xgb(XGBClassifier, X_train, y_train_mapped, num_class=len(present_classes))
    y_prob_eval = model_dir.predict_proba(X_test_eval)
    y_pred = np.argmax(y_prob_eval, axis=1)
    y_prob = model_dir.predict_proba(X_test)

    print("\n=== DIRECAO TERNARIA ===")
    if len(y_test_eval) > 0:
        print(f"Acuracia teste: {accuracy_score(y_test_eval, y_pred) * 100:.2f}%")
        names_map = {0: "DOWN", 1: "FLAT", 2: "UP"}
        target_names = [names_map.get(idx_to_class[i], str(idx_to_class[i])) for i in sorted(idx_to_class.keys())]
        print(classification_report(y_test_eval, y_pred, target_names=target_names, zero_division=0))
    else:
        print("Sem classes sobrepostas entre treino e teste para avaliar direcao.")
    _print_feature_importance(model_dir, list(X.columns))

    # Modelos binarios de sucesso por estrategia
    model_call = _train_binary_xgb(XGBClassifier, X_train, df["success_call_only"].iloc[:split_idx])
    model_put = _train_binary_xgb(XGBClassifier, X_train, df["success_put_only"].iloc[:split_idx])
    model_str = _train_binary_xgb(XGBClassifier, X_train, df["success_strangle"].iloc[:split_idx])

    # Reconstrucao de probabilidades para eixo fixo DOWN/FLAT/UP mesmo quando nem todas classes existem.
    prob_by_class = {int(idx_to_class[i]): y_prob[:, i] for i in range(y_prob.shape[1])}
    test_meta["p_down"] = prob_by_class.get(DIRECTION_DOWN, np.zeros(len(test_meta)))
    test_meta["p_flat"] = prob_by_class.get(DIRECTION_FLAT, np.zeros(len(test_meta)))
    test_meta["p_up"] = prob_by_class.get(DIRECTION_UP, np.zeros(len(test_meta)))

    test_meta["p_call_success"] = model_call.predict_proba(X_test)[:, 1]
    test_meta["p_put_success"] = model_put.predict_proba(X_test)[:, 1]
    test_meta["p_strangle_success"] = model_str.predict_proba(X_test)[:, 1]

    for col in ["touched_support", "touched_resistance", "entered_zone"]:
        test_meta[col] = pd.to_numeric(test_meta[col], errors="coerce").fillna(0).astype(int)

    policy = _build_policy_actions(test_meta, no_trade_threshold=args.no_trade_threshold)

    traded = policy[policy["entered_trade"] == 1]
    n_total = len(policy)
    n_traded = len(traded)
    coverage = (n_traded / n_total * 100.0) if n_total else 0.0
    hit_rate_traded = (traded["action_hit"].mean() * 100.0) if n_traded else 0.0

    print("\n=== POLITICA (COM NO_TRADE) ===")
    print(f"Amostra teste: {n_total}")
    print(f"Operacoes executadas: {n_traded} ({coverage:.2f}%)")
    print(f"Hit rate apenas trades executados: {hit_rate_traded:.2f}%")
    print("Distribuicao de acoes:")
    print(policy["action"].value_counts(dropna=False).to_string())

    # Melhor horario/horizonte por score esperado
    grp = policy.groupby(["entry_hour", "expiry_days"], dropna=False).agg(
        n=("action", "size"),
        coverage=("entered_trade", "mean"),
        hit_traded=("action_hit", lambda s: s.mean() if len(s) else np.nan),
        p_call=("p_call_success", "mean"),
        p_put=("p_put_success", "mean"),
        p_str=("p_strangle_success", "mean"),
        p_up=("p_up", "mean"),
        p_down=("p_down", "mean"),
    ).reset_index()

    grp["coverage"] = grp["coverage"] * 100.0
    grp["hit_traded"] = grp["hit_traded"] * 100.0
    grp["quality_score"] = 0.7 * grp["hit_traded"].fillna(0) + 0.3 * grp["coverage"].fillna(0)
    grp = grp.sort_values(["quality_score", "n"], ascending=[False, False])

    print("\n=== TOP 12 CONDICOES (hora x D+N) ===")
    print(grp.head(12).to_string(index=False))

    policy_out = dataset_out.with_name(f"{dataset_out.stem}_policy{dataset_out.suffix}")
    policy.to_csv(policy_out, index=False)
    print(f"\nResultados de politica salvos em: {policy_out.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
