#!/usr/bin/env python3
"""
Exemplo de integração: XGBoost → TradingDecisionEngine → Output (CSV + HTML colorido)

Este script mostra como os sinais de trading aparecem no backtest.
Não requer pandas/numpy - usa apenas estruturas Python nativas.
"""

import csv
from pathlib import Path
from trading_decision import TradingDecisionEngine, format_signal_for_backtest, ACTION_COLOR_MAP, TradeAction


def example_backtest_integration():
    """Simula um backtest com sinais de trading."""
    
    engine = TradingDecisionEngine(
        confidence_threshold=0.55,
        strangle_threshold=0.40,
    )
    
    # Simular dados de teste (como se viessem do XGBoost)
    # REGRA: Previsão é SEMPRE para o fechamento do PRÓXIMO DIA às 14:00
    # Não muda o horário (sempre 14:00), só o dia: D+1, D+2, D+3...
    test_data = [
        {
            "datetime": "2026-05-24 10:30",  # Previsão feita às 10:30
            "prediction_date": "2026-05-25",  # Para o próximo dia (D+1)
            "prediction_time": "14:00",       # Sempre 14:00
            "symbol": "EURUSD",
            "timeframe": "D1",  # Dia inteiro (D1)
            "close": 1.0950,
            "p_up": 0.72,
            "p_down": 0.15,
            "p_flat": 0.13,
        },
        {
            "datetime": "2026-05-24 11:45",  # Previsão feita às 11:45
            "prediction_date": "2026-05-25",  # Para o próximo dia (D+1)
            "prediction_time": "14:00",       # Sempre 14:00
            "symbol": "EURUSD",
            "timeframe": "D1",
            "close": 1.0955,
            "p_up": 0.60,
            "p_down": 0.30,
            "p_flat": 0.10,
        },
        {
            "datetime": "2026-05-24 13:00",  # Previsão feita às 13:00
            "prediction_date": "2026-05-25",  # Para o próximo dia (D+1)
            "prediction_time": "14:00",       # Sempre 14:00
            "symbol": "EURUSD",
            "timeframe": "D1",
            "close": 1.0960,
            "p_up": 0.40,
            "p_down": 0.50,
            "p_flat": 0.10,
        },
        {
            "datetime": "2026-05-25 10:15",  # Previsão feita no dia seguinte
            "prediction_date": "2026-05-26",  # Para D+1 (dia após-amanhã)
            "prediction_time": "14:00",       # Sempre 14:00
            "symbol": "EURUSD",
            "timeframe": "D1",
            "close": 1.0958,
            "p_up": 0.68,
            "p_down": 0.20,
            "p_flat": 0.12,
        },
        {
            "datetime": "2026-05-25 14:30",  # Previsão feita após 14:00
            "prediction_date": "2026-05-26",  # Para D+1 (dia após-amanhã)
            "prediction_time": "14:00",       # Sempre 14:00
            "symbol": "EURUSD",
            "timeframe": "D1",
            "close": 1.0965,
            "p_up": 0.35,
            "p_down": 0.55,
            "p_flat": 0.10,
        },
    ]
    
    # Aplicar engine de decisão
    result = []
    for row in test_data:
        # A previsão é SEMPRE para o próximo dia às 14:00
        prediction_datetime = f"{row['prediction_date']} {row['prediction_time']}"
        
        signal = engine.decide(
            symbol=row["symbol"],
            timeframe=row["timeframe"],
            datetime_str=prediction_datetime,  # Usa DATA + HORA da previsão (D+1 14:00)
            p_down=float(row["p_down"]),
            p_flat=float(row["p_flat"]),
            p_up=float(row["p_up"]),
        )
        signal_dict = format_signal_for_backtest(signal)
        merged = {**row, **signal_dict, "prediction_datetime": prediction_datetime}
        result.append(merged)
    
    return result


def save_backtest_csv(data, output_path):
    """Salva backtest em CSV."""
    if not data:
        return
    
    # Get all keys
    fieldnames = list(data[0].keys())
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"✅ CSV salvo em: {output_path}")


def save_backtest_html(data, output_path):
    """Salva backtest em HTML com cores por ação."""
    
    if not data:
        return
    
    # Build HTML table
    html = """<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        table { border-collapse: collapse; width: 100%; }
        th { background-color: #333; color: white; padding: 10px; text-align: left; }
        td { padding: 8px; border-bottom: 1px solid #ddd; }
        tr:hover { background-color: #f5f5f5; }
    </style>
</head>
<body>
    <h1>📊 Backtest Results with Trading Signals</h1>
    <table>
        <tr>
"""
    
    # Header row
    fieldnames = list(data[0].keys())
    for col in fieldnames:
        html += f"            <th>{col}</th>\n"
    html += "        </tr>\n"
    
    # Data rows with color based on action
    for row in data:
        action = row.get("action", "")
        
        # Convert action string to enum for lookup
        try:
            action_enum = TradeAction(action) if action else None
            bg_color = ACTION_COLOR_MAP.get(action_enum, "#FFFFFF")
        except:
            bg_color = "#FFFFFF"
        
        html += f'        <tr style="background-color: {bg_color};">\n'
        for col in fieldnames:
            value = row[col]
            html += f"            <td>{value}</td>\n"
        html += "        </tr>\n"
    
    html += """    </table>
    <br>
    <h3>Legend:</h3>
    <ul>
        <li><span style="background-color: #90EE90;">🟢 PUT_SELL</span> - Bullish (vender PUT)</li>
        <li><span style="background-color: #FFB6C6;">🔴 CALL_SELL</span> - Bearish (vender CALL)</li>
        <li><span style="background-color: #FFD700;">🟡 STRANGLE</span> - Incerteza (vender volatilidade)</li>
        <li><span style="background-color: #D3D3D3;">⚪ NO_TRADE</span> - Confiança baixa</li>
    </ul>
</body>
</html>"""
    
    with open(output_path, "w") as f:
        f.write(html)
    print(f"✅ HTML colorido salvo em: {output_path}")


if __name__ == "__main__":
    print("=== Exemplo: Integração XGBoost + Decision Engine ===\n")
    
    # Gerar backtest simulado
    result = example_backtest_integration()
    
    print("Dados de backtest com sinais:\n")
    for row in result:
        print(row)
    
    # Salvar outputs
    output_dir = Path("predictions")
    output_dir.mkdir(exist_ok=True)
    
    save_backtest_csv(result, output_dir / "example_backtest.csv")
    save_backtest_html(result, output_dir / "example_backtest.html")
    
    print("\n✅ Exemplo completo gerado!")
    print(f"   CSV: {output_dir / 'example_backtest.csv'}")
    print(f"   HTML: {output_dir / 'example_backtest.html'}")
