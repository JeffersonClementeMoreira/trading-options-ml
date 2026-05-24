# 🚀 Quick Reference - Trading Decision System

## One-Liner Overview
Maps XGBoost probabilities → trading actions (CALL/PUT/STRANGLE/NO_TRADE) with Telegram alerts.

---

## 📦 What You Get

```python
# Input: XGBoost predictions
p_up=0.72, p_down=0.15, p_flat=0.13

# Process: TradingDecisionEngine
from trading_decision import TradingDecisionEngine
engine = TradingDecisionEngine()
signal = engine.decide("EURUSD", "M15", "2026-05-24 14:00", 
                       p_down=0.15, p_flat=0.13, p_up=0.72)

# Output: TradeAction
signal.action          # TradeAction.CALL
signal.confidence      # 0.72 (72%)
signal.reasoning       # "Viés positivo: P(UP)=72.00% > P(DOWN)=15.00%"
```

---

## 🎯 Decision Rules (Simplified)

```
IF confidence < 0.55       → NO_TRADE 🚫
ELIF |p_up - p_down| < 0.40 → STRANGLE ⚖️
ELIF p_up > p_down         → CALL 📈
ELSE                       → PUT 📉
```

---

## 🔧 Installation & Setup

### 1. No External Dependencies
```bash
# Uses only: os, requests (for Telegram)
# All modules ready to import
```

### 2. Configuration (Production)
```bash
export TELEGRAM_TOKEN="123456:ABC-DEF1234..."
export TELEGRAM_CHAT_ID="987654321"
```

### 3. Get Telegram Credentials
```
1. Search @BotFather on Telegram
2. /newbot → choose name → get TOKEN
3. Add bot to private group
4. Visit: https://api.telegram.org/bot{TOKEN}/getUpdates
5. Find "chat.id" → that's CHAT_ID
```

---

## 💻 Common Usage Patterns

### Pattern 1: Backtest (Batch Processing)
```python
from trading_decision import TradingDecisionEngine, format_signal_for_backtest

engine = TradingDecisionEngine()

for row in backtest_data:
    signal = engine.decide(
        symbol=row["symbol"],
        timeframe=row["timeframe"],
        datetime_str=row["datetime"],
        p_down=row["p_down"],
        p_flat=row["p_flat"],
        p_up=row["p_up"],
    )
    signal_dict = format_signal_for_backtest(signal)
    # Add to DataFrame...
```

### Pattern 2: Real-time (Single Signal)
```python
from realtime_inference import make_inference_engine

engine = make_inference_engine(
    model_dir=Path("models/"),
    telegram_enabled=True,
)

result = engine.infer(
    symbol="EURUSD",
    timeframe="M15",
    datetime_str="2026-05-24 14:00",
    features={...}  # Dict with indicator values
)
# result = {"action": "CALL", "confidence": "0.72", ...}
```

### Pattern 3: Manual Telegram
```python
from telegram_notifier import TelegramNotifier

tg = TelegramNotifier()
tg.send_signal(
    action="CALL",
    symbol="EURUSD",
    timeframe="M15",
    p_up=0.72,
    p_down=0.15,
    p_flat=0.13,
    confidence=0.72,
)
```

---

## 📊 Output Formats

### CSV Column Names
```
datetime, symbol, timeframe, close, p_up, p_down, p_flat,
action, confidence, reasoning
```

### HTML Colors
```
CALL:       #90EE90 (light green)
PUT:        #FFB6C6 (light red)
STRANGLE:   #FFD700 (gold)
NO_TRADE:   #D3D3D3 (light gray)
```

### Telegram Emojis
```
CALL:       📈
PUT:        📉
STRANGLE:   ⚖️
NO_TRADE:   🚫
```

---

## 🎚️ Tuning Thresholds

```python
# More trades (35-40% coverage)
engine = TradingDecisionEngine(confidence_threshold=0.50)

# Fewer trades (20-30% coverage)
engine = TradingDecisionEngine(confidence_threshold=0.65)

# Sell more volatility
engine = TradingDecisionEngine(strangle_threshold=0.50)

# Less volatility selling
engine = TradingDecisionEngine(strangle_threshold=0.20)
```

---

## 🐛 Quick Debugging

### Check if Telegram enabled
```python
from telegram_notifier import TelegramNotifier
tg = TelegramNotifier()
print(f"Telegram ready: {tg.enabled}")
```

### Test Telegram send
```bash
curl -X POST "https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage" \
  -d "chat_id=${TELEGRAM_CHAT_ID}&text=Test"
# Should see message in Telegram
```

### Inspect decision
```python
signal = engine.decide("EURUSD", "M15", "2026-05-24", 0.20, 0.10, 0.70)
print(f"Action: {signal.action.value}")
print(f"Confidence: {signal.confidence:.2%}")
print(f"Reasoning: {signal.reasoning}")
```

---

## 📁 Key Files

```
trading_decision.py          ← Core logic
telegram_notifier.py         ← Telegram integration
realtime_inference.py        ← Real-time wrapper
example_backtest_integration.py ← Runnable example

DECISION_ENGINE.md           ← Technical docs
PRODUCTION_GUIDE.md          ← User workflow
DECISION_SYSTEM_SUMMARY.md   ← This summary
```

---

## 🎯 Performance Targets

```
Expected Coverage:    55-65% (% of candles with signal)
Win Rate:            55-65%
False Signals:       35-45%
Sharpe Ratio:        ≥ 1.0
```

---

## ⚡ One-Command Tests

```bash
# Test decision logic
python3 -c "
from trading_decision import TradingDecisionEngine
e = TradingDecisionEngine()
s = e.decide('EUR/USD', 'M15', '2026', 0.15, 0.13, 0.72)
print(f'{s.action.value}: {s.reasoning}')
"

# Test Telegram
python3 -c "
from telegram_notifier import TelegramNotifier
TelegramNotifier().send_alert('Test', 'System working')
"

# Run example
python3 example_backtest_integration.py
```

---

## 📞 Where to Look

| Question | Look in |
|----------|----------|
| How do I set up production? | `PRODUCTION_GUIDE.md` |
| How does the algorithm work? | `DECISION_ENGINE.md` |
| What's the code structure? | `trading_decision.py` |
| Can I see an example? | `example_backtest_integration.py` |
| What are all the options? | `DECISION_SYSTEM_SUMMARY.md` |

---

## ✅ Pre-Flight Checklist

Before going live:
- [ ] TELEGRAM_TOKEN set
- [ ] TELEGRAM_CHAT_ID set
- [ ] Models trained and saved in `models/`
- [ ] Test Telegram send works
- [ ] Backtest HTML generates correctly
- [ ] Example integration runs successfully
- [ ] Thresholds reviewed and set
- [ ] Logs directory created

---

**Ready to trade! 🚀**

Start with: `python3 example_backtest_integration.py`
