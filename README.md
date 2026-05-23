# Options Trading Strategy Engine

Automated hedge (trava) and rolling (rolagem) strategies for option positions with ML-driven decision making and MT5 integration.

## Features

- **Risk Management**: Automated trava (10% hedge) and rolagem (20% roll trigger, 35% roll target)
- **Options Pricing**: Black-Scholes with IV, delta, theta, gamma calculations
- **Regime Detection**: Trend/Range/Bull-Bear classification with flow scoring
- **ML Pipeline**: XGBoost multiclass direction prediction + binary strategy success models
- **MT5 Integration**: Real-time external feature loading (KAMA, SD, flow from MT5)
- **Backtesting**: Full day-by-day validation with 50+ metrics per trade

## Setup

### Requirements
- Python 3.10+
- pandas 2.x, numpy 2.3.5, scipy 1.17.1
- xgboost 3.2.0, scikit-learn 1.8.0
- joblib 1.5.3

### Installation

```bash
# Create venv
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install pandas numpy scipy xgboost scikit-learn joblib

# For GPU support (NVIDIA)
pip install nvidia-nccl-cu12
```

## Data Structure

```
dados/
  ├── XAUUSD_M15_202001020600_202604131545.csv  # OHLC M15 (10k candles)
  └── features_mt5.csv                           # MT5 export (optional, faster)
```

MT5 CSV format (from options.mq5):
```
datetime,date,time,open,high,low,close,
mt5_er_mean,mt5_kama_slope,mt5_flow_score,mt5_regime,
mt5_realized_vol,mt5_expected_move,mt5_atr_pct,
mt5_sweep_top,mt5_sweep_bottom,mt5_ret_1,mt5_ret_3,mt5_dist_mean
```

## Usage

### 1. Backtest Analysis (Options Engine)

```bash
python3.10 options_v3.py \
  --file dados/XAUUSD_M15_202001020600_202604131545.csv \
  --backtest --backtest-days 120 --tail 10000 \
  --analysis-hour 19 --analysis-minute 0 \
  --expiry-hour 14 --expiry-minute 0 \
  --expiry-days 1
```

**Output**: analytics/stats/backtest_*.csv with 50+ metrics (entry, exit, trava/rolagem hits)

### 2. Generate Training Dataset

```bash
python3.10 xgb_entry_optimizer.py \
  --file dados/XAUUSD_M15_202001020600_202604131545.csv \
  --backtest-days 220 \
  --hour-start 8 --hour-end 20 \
  --expiry-days-list 1,2,3,4,5 \
  --dataset-only
```

**Output**: xgb_dataset_full.csv (training data, ~6975 rows)

### 3. Train ML Models

```bash
python3.10 xgb_entry_optimizer.py \
  --file dados/XAUUSD_M15_202001020600_202604131545.csv \
  --backtest-days 60 \
  --hour-start 10 --hour-end 14 \
  --expiry-days-list 1,2 \
  --no-trade-threshold 0.62
```

**Output**: 
- xgb_training_results_*.csv (policy actions: CALL_ONLY/PUT_ONLY/STRANGLE/NO_TRADE)
- Feature importance rankings

### 4. Use MT5 Real-Time Data

```bash
# Copy features_mt5.csv from MT5 to dados/
python3.10 options_v3.py \
  --file dados/features_mt5.csv \
  --prefer-external-features \
  --analysis-hour 10
```

## Architecture

### Core Modules

| Module | Purpose |
|--------|---------|
| `options_v3.py` | Main pipeline: OHLC → indicators → regime → pricing → backtest/predict |
| `xgb_entry_optimizer.py` | Dataset generation & XGBoost training (direction + strategy success) |
| `core/options_engine.py` | Strike ranking by edge_score (prob_otm + reversal - delta) |
| `core/indicators.py` | KAMA, ATR, SD confluence, sweeps |
| `core/regime.py` | Flow score, Efficiency Ratio, trend/range detection |
| `core/sd_confluence.py` | S&D level detection and confluences |
| `options.mq5` | MT5 Expert Advisor (exports features_mt5.csv real-time) |

### Data Flow

```
MT5 OHLC
   ↓
options_v3.py (build_context)
   ├→ Indicators: KAMA, ATR, EMA, SD zones
   ├→ Regime: trend/range/bull-bear
   ├→ Options: strikes, delta, IV, theta
   └→ Risk Mgmt: trava/rolagem levels
   ↓
Backtest Validation (_run_backtest_table)
   ├→ Daily outcome grading
   ├→ Trava/rolagem trigger detection
   └→ CSV metrics
   ↓
xgb_entry_optimizer.py (training)
   ├→ Feature engineering (25-30 features)
   ├→ XGBoost direction (DOWN/FLAT/UP)
   ├→ Binary success (CALL/PUT/STRANGLE)
   └→ Policy scoring
   ↓
Policy Actions: CALL_ONLY | PUT_ONLY | STRANGLE | NO_TRADE
```

## Key Metrics

- **Hit Rate**: 95-100% on validation (executed trades vs non-trades)
- **Direction Accuracy**: 60% on small windows (multiclass DOWN/FLAT/UP)
- **Strategy Success**: 94-96% (PUT on supported, CALL on resisted)
- **NO_TRADE Coverage**: ~60% globally (high precision, prevents false signals)

## Flags Reference

| Flag | Purpose |
|------|---------|
| `--prefer-external-features` | Load mt5_* columns from MT5 CSV |
| `--backtest` | Run historical validation |
| `--backtest-days N` | Number of backtest days |
| `--expiry-days N` | Expiry horizon (D+N) |
| `--hour-start H` | Analysis hour start (0-23) |
| `--hour-end H` | Analysis hour end |
| `--tail N` | Use last N rows from CSV |
| `--dataset-only` | Generate dataset without training |
| `--allow-post-entry-features` | Include zone touches (default: leak-safe) |
| `--no-trade-threshold T` | Policy NO_TRADE score threshold (0-1) |

## MT5 Setup

1. Copy `options.mq5` to `Documents/MetaTrader 5/Experts/`
2. Compile in MetaEditor
3. Attach to any chart (M15 recommended)
4. Check `MQL5/Files/features_mt5.csv` for real-time exports
5. Copy to `dados/features_mt5.csv` in Python workspace

## Deployment on VPS

See `DEPLOYMENT.md` for VPS setup instructions.

## License

Internal Use Only
