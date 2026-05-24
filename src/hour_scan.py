from pathlib import Path

import pandas as pd

import options_v3 as ov3


csv_file = Path('/home/pm077155/pessoal/options/dados/XAUUSD_M15_202001020600_202604131545.csv')
results = []

for h in range(8, 21):
    try:
        df, _, _ = ov3._run_backtest_table(
            csv_file=csv_file,
            iv=0.25,
            days=5,
            tail_size=10000,
            analysis_hour=h,
            analysis_minute=0,
            expiry_hour=14,
            expiry_minute=0,
            backtest_days=120,
            strategy_mode='strangle',
            save_html=False,
        )
    except Exception as exc:
        results.append({'hour': h, 'error': str(exc)})
        continue

    total = len(df)
    hit_rate = df['satisfactory'].mean() * 100 if total else 0
    any_sweep_hit = (df['hit_next_top_sweep'] | df['hit_next_bottom_sweep']).mean() * 100 if total else 0
    both_sweep_hit = (df['hit_next_top_sweep'] & df['hit_next_bottom_sweep']).mean() * 100 if total else 0

    em_le_50 = df[df['expected_move'] <= 50]
    em_le_50_hit = em_le_50['satisfactory'].mean() * 100 if len(em_le_50) else float('nan')

    results.append(
        {
            'hour': h,
            'n': total,
            'hit_rate': round(hit_rate, 2),
            'any_sweep_hit_rate': round(any_sweep_hit, 2),
            'both_sweep_hit_rate': round(both_sweep_hit, 2),
            'n_em_le_50': int(len(em_le_50)),
            'hit_rate_em_le_50': round(em_le_50_hit, 2) if pd.notna(em_le_50_hit) else None,
        }
    )

res = pd.DataFrame(results).sort_values('hour')
print('=== HOUR SCAN (8h-20h, tail=10000, backtest_days=120) ===')
print(res.to_string(index=False))

print('\n=== TOP HORARIOS POR HIT RATE (min n>=40) ===')
valid = res[(res['n'] >= 40) & res['hit_rate'].notna()].sort_values(['hit_rate', 'n'], ascending=[False, False]).head(8)
print(valid[['hour', 'n', 'hit_rate', 'any_sweep_hit_rate', 'both_sweep_hit_rate']].to_string(index=False))
