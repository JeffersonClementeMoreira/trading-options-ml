# VPS Deployment Guide

## 1. Clone Repository on VPS

```bash
# SSH into VPS
ssh user@your_vps_ip

# Clone the repo
cd ~/pessoal/
git clone https://github.com/YOUR_USERNAME/options.git
cd options
```

## 2. Setup Python Environment

```bash
# Create venv
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install pandas numpy scipy xgboost scikit-learn joblib

# For GPU support (if available)
pip install nvidia-nccl-cu12
```

## 3. Prepare Data

```bash
# Create data directory
mkdir -p dados

# Copy your OHLC CSV
# Option A: From local machine
scp dados/XAUUSD_M15_202001020600_202604131545.csv user@vps_ip:~/pessoal/options/dados/

# Option B: Download if available on cloud storage
wget https://your_bucket/XAUUSD_M15_202001020600_202604131545.csv -O dados/
```

## 4. Test Installation

```bash
# Verify environment
source venv/bin/activate
python3 -c "import pandas, xgboost, sklearn; print('✓ All dependencies OK')"

# Run quick smoke test (20-day backtest)
python3.10 options_v3.py \
  --file dados/XAUUSD_M15_202001020600_202604131545.csv \
  --backtest --backtest-days 20 --tail 5000 \
  --analysis-hour 10 --expiry-days 1
```

## 5. Setup Cron Jobs (Optional)

### Daily backtest run (9:00 UTC)
```bash
0 9 * * * cd ~/pessoal/options && source venv/bin/activate && \
  python3.10 options_v3.py --file dados/features_mt5.csv --prefer-external-features \
  --backtest --backtest-days 1 >> logs/daily_backtest.log 2>&1
```

### MT5 Feature Export (every 15 min, if available)
```bash
*/15 * * * * cd ~/pessoal/options && scp user@local_machine:~/MT5/features_mt5.csv dados/ 2>/dev/null || true
```

## 6. MT5 Integration (if running MT5 on VPS too)

### Option A: MT5 on VPS
1. Install MT5 on VPS (Wine + MT5 container)
2. Run `options.mq5` as Expert Advisor
3. Set export path to `/home/user/pessoal/options/dados/features_mt5.csv`

### Option B: MT5 on Local, Export to VPS
1. Run MT5 locally with `options.mq5`
2. Setup SFTP sync:
   ```bash
   # On local machine, add to crontab:
   */5 * * * * scp ~/MT5/MQL5/Files/features_mt5.csv \
     user@vps_ip:~/pessoal/options/dados/ 2>/dev/null || true
   ```

3. Use on VPS:
   ```bash
   python3.10 options_v3.py \
     --file dados/features_mt5.csv \
     --prefer-external-features \
     --analysis-hour 10
   ```

## 7. Monitor Logs

```bash
# Watch real-time backtest logs
tail -f logs/backtest_latest.log

# Check for errors
grep ERROR logs/*.log

# Full analytics
tail -20 analytics/stats/backtest_latest.csv
```

## 8. Update Code from GitHub

```bash
cd ~/pessoal/options
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # If added later
```

## 9. Troubleshooting

### Memory issues on small VPS
```bash
# Use tail to limit data
python3.10 options_v3.py \
  --file dados/XAUUSD_M15.csv \
  --tail 5000 \  # Only use last 5000 rows
  --backtest-days 60
```

### Slow training on VPS
```bash
# Reduce dataset (fewer hours/days)
python3.10 xgb_entry_optimizer.py \
  --backtest-days 30 \
  --hour-start 10 --hour-end 14 \
  --expiry-days-list 1,2
```

### Network timeouts with large data
```bash
# Transfer in chunks
split -b 100M dados/large_file.csv dados/chunk_
# Transfer, then: cat dados/chunk_* > dados/large_file.csv
```

## 10. Backup Strategy

```bash
# Backup analytics locally (before reset)
scp -r user@vps_ip:~/pessoal/options/analytics/stats logs_backup/

# Backup models (if saved)
scp user@vps_ip:~/pessoal/options/*.pkl ~/.

# Git commit & push changes
cd ~/pessoal/options
git add -A && git commit -m "VPS sync" && git push
```
