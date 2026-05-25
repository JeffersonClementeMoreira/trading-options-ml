//+------------------------------------------------------------------+
//| Options Trading EA - Advanced Indicators Calculation             |
//| options.mq5                                                      |
//| Calculates sweep, displacement, flow, and entry quality metrics  |
//| Sends results via file/database to Python for XGBoost analysis   |
//+------------------------------------------------------------------+
#property copyright "Options Trading System"
#property link      "https://options.local"
#property version   "1.0"

#include <Trade\Trade.mqh>

// ===== CONFIGURATION =====
input ENUM_TIMEFRAMES ANALYSIS_TF = PERIOD_M15;     // Analysis timeframe
input string SYMBOL = "EURUSD";                     // Symbol to analyze
input int    EXPORT_INTERVAL = 100;                 // Candles before export
input string OUTPUT_FILE = "indicators_output.txt";

// ===== GLOBAL VARIABLES =====
CTrade trade;
int prev_bars = 0;
int export_counter = 0;

//+------------------------------------------------------------------+
//| Expert Initialization Function                                  |
//+------------------------------------------------------------------+
int OnInit()
{
    Print("Options EA Initialized");
    return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert Deinitialization Function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
    Print("Options EA Stopped");
}

//+------------------------------------------------------------------+
//| Expert Tick Function - Main Loop                                |
//+------------------------------------------------------------------+
void OnTick()
{
    int bars = iBars(SYMBOL, ANALYSIS_TF);
    
    // Only process when new bar forms
    if(bars == prev_bars) return;
    prev_bars = bars;
    
    // Calculate indicators every N bars
    export_counter++;
    if(export_counter >= EXPORT_INTERVAL) {
        CalculateAndExport(bars);
        export_counter = 0;
    }
}

//+------------------------------------------------------------------+
//| Calculate All Advanced Indicators                               |
//+------------------------------------------------------------------+
void CalculateAndExport(int bars)
{
    // Get current bar index
    int bar_idx = 0; // Current bar
    
    // Get OHLC
    double open = iOpen(SYMBOL, ANALYSIS_TF, bar_idx);
    double high = iHigh(SYMBOL, ANALYSIS_TF, bar_idx);
    double low = iLow(SYMBOL, ANALYSIS_TF, bar_idx);
    double close = iClose(SYMBOL, ANALYSIS_TF, bar_idx);
    
    // Previous bar
    double prev_high = iHigh(SYMBOL, ANALYSIS_TF, bar_idx+1);
    double prev_low = iLow(SYMBOL, ANALYSIS_TF, bar_idx+1);
    double prev_close = iClose(SYMBOL, ANALYSIS_TF, bar_idx+1);
    
    // ===== SWEEP DETECTION =====
    bool sweep_top = (high > prev_high) && (close < prev_high);
    bool sweep_bottom = (low < prev_low) && (close > prev_low);
    
    double atr = iATR(SYMBOL, ANALYSIS_TF, 14, bar_idx);
    double sweep_strength_top = (high - prev_high) / atr;
    double sweep_strength_bottom = (prev_low - low) / atr;
    double sweep_strength = MathMax(sweep_strength_top, sweep_strength_bottom);
    bool is_strong_sweep = sweep_strength > 1.5;
    
    // ===== DISPLACEMENT =====
    double displacement = MathAbs(close - open) / atr;
    double directional_displacement = (close - open) / atr;
    
    // Momentum: 3-candle
    double close_3 = iClose(SYMBOL, ANALYSIS_TF, bar_idx+3);
    double momentum_burst = (close - close_3) / atr;
    
    // Exhaustion: 10-candle
    double close_10 = iClose(SYMBOL, ANALYSIS_TF, bar_idx+10);
    double exhaustion = MathAbs(close - close_10) / atr;
    
    // ===== STRUCTURE BREAKS =====
    double highest_20 = iHigh(SYMBOL, ANALYSIS_TF, iHighest(SYMBOL, ANALYSIS_TF, MODE_HIGH, 20, bar_idx+1));
    double lowest_20 = iLow(SYMBOL, ANALYSIS_TF, iLowest(SYMBOL, ANALYSIS_TF, MODE_LOW, 20, bar_idx+1));
    
    bool break_high = close > highest_20;
    bool break_low = close < lowest_20;
    double break_strength = (break_high) ? (close - highest_20) / atr : (lowest_20 - close) / atr;
    
    // ===== FLOW METRICS =====
    double flow = 0, flow_volatility = 0;
    CalculateFlow(bar_idx, flow, flow_volatility);
    
    double flow_prev = 0, flow_vol_prev = 0;
    CalculateFlow(bar_idx+1, flow_prev, flow_vol_prev);
    double flow_acceleration = flow - flow_prev;
    
    // ===== POSITION METRICS =====
    double high_20 = iHigh(SYMBOL, ANALYSIS_TF, iHighest(SYMBOL, ANALYSIS_TF, MODE_HIGH, 20, bar_idx));
    double low_20 = iLow(SYMBOL, ANALYSIS_TF, iLowest(SYMBOL, ANALYSIS_TF, MODE_LOW, 20, bar_idx));
    
    double pos_range = (close - low_20) / (high_20 - low_20);
    if(pos_range < 0) pos_range = 0;
    if(pos_range > 1) pos_range = 1;
    
    double ma20 = iMA(SYMBOL, ANALYSIS_TF, 20, 0, MODE_SMA, PRICE_CLOSE, bar_idx);
    double dist_mean = (close - ma20) / ma20 * 100;
    
    // Z-score
    double mean = ma20;
    double std_dev = iStdDev(SYMBOL, ANALYSIS_TF, 20, 0, MODE_SMA, PRICE_CLOSE, bar_idx);
    double zscore = (std_dev > 0.0001) ? (close - mean) / std_dev : 0;
    
    // ===== VOLATILITY METRICS =====
    double atr_pct = (atr / close) * 100;
    double avg_atr = iMA(SYMBOL, ANALYSIS_TF, 20, 0, MODE_SMA, 14, bar_idx);
    double vol_regime = (avg_atr > 0.0001) ? atr / avg_atr : 1.0;
    bool vol_expansion = atr > avg_atr;
    
    // ===== MOVING AVERAGES =====
    double sma_20 = iMA(SYMBOL, ANALYSIS_TF, 20, 0, MODE_SMA, PRICE_CLOSE, bar_idx);
    double sma_50 = iMA(SYMBOL, ANALYSIS_TF, 50, 0, MODE_SMA, PRICE_CLOSE, bar_idx);
    double ema_12 = iMA(SYMBOL, ANALYSIS_TF, 12, 0, MODE_EMA, PRICE_CLOSE, bar_idx);
    double ema_26 = iMA(SYMBOL, ANALYSIS_TF, 26, 0, MODE_EMA, PRICE_CLOSE, bar_idx);
    
    // ===== REVERSAL SIGNAL =====
    bool direction_change = (close > sma_20 && prev_close <= sma_20) || (close < sma_20 && prev_close > sma_20);
    double reversal_score = (sweep_strength * 0.4) + (displacement * 0.4) + (direction_change ? 0.2 : 0);
    reversal_score = MathMin(reversal_score, 1.0);
    
    // ===== ENTRY QUALITY SCORE (0-100) =====
    double entry_score = 0;
    entry_score += is_strong_sweep ? 15 : 0;
    entry_score += (displacement > 1.5) ? 20 : 0;
    entry_score += (pos_range > 0.2 && pos_range < 0.8) ? 20 : 0;
    entry_score += vol_expansion ? 15 : 0;
    entry_score += (MathAbs(close - ema_12) / close < 0.01) ? 15 : 0;
    entry_score += reversal_score * 15;
    entry_score = MathMin(entry_score, 100);
    
    // ===== EXPORT TO FILE =====
    ExportIndicators(
        high, low, close, open,
        sweep_top, sweep_bottom, sweep_strength, is_strong_sweep,
        displacement, directional_displacement, momentum_burst, exhaustion,
        break_high, break_low, break_strength,
        flow, flow_acceleration, flow_volatility,
        pos_range, dist_mean, zscore,
        atr_pct, vol_regime, vol_expansion,
        sma_20, sma_50, ema_12, ema_26,
        reversal_score, entry_score
    );
}

//+------------------------------------------------------------------+
//| Calculate Flow Metrics                                          |
//+------------------------------------------------------------------+
void CalculateFlow(int bar_idx, double &flow_result, double &vol_result)
{
    flow_result = 0;
    vol_result = 0;
    
    double returns[10];
    double closes[11];
    
    // Get 10 closes
    for(int i = 0; i < 11; i++) {
        closes[i] = iClose(SYMBOL, ANALYSIS_TF, bar_idx+i);
    }
    
    // Calculate returns
    double sum_returns = 0;
    double sum_sq_devs = 0;
    double avg_return = 0;
    
    for(int i = 0; i < 10; i++) {
        returns[i] = (closes[i] - closes[i+1]) / closes[i+1] * 100;
        sum_returns += returns[i];
    }
    
    avg_return = sum_returns / 10;
    
    for(int i = 0; i < 10; i++) {
        sum_sq_devs += MathPow(returns[i] - avg_return, 2);
    }
    
    flow_result = sum_returns;
    vol_result = MathSqrt(sum_sq_devs / 10);
}

//+------------------------------------------------------------------+
//| Export Indicators to File                                       |
//+------------------------------------------------------------------+
void ExportIndicators(
    double high, double low, double close, double open,
    bool sweep_top, bool sweep_bottom, double sweep_strength, bool is_strong_sweep,
    double displacement, double directional_displacement, double momentum_burst, double exhaustion,
    bool break_high, bool break_low, double break_strength,
    double flow, double flow_acceleration, double flow_volatility,
    double pos_range, double dist_mean, double zscore,
    double atr_pct, double vol_regime, bool vol_expansion,
    double sma_20, double sma_50, double ema_12, double ema_26,
    double reversal_score, double entry_score
)
{
    string line = "";
    
    // Format: timestamp|open|high|low|close|sweep_top|sweep_bottom|sweep_strength|...|entry_score
    line += TimeToString(TimeCurrent()) + "|";
    line += DoubleToString(open, 5) + "|";
    line += DoubleToString(high, 5) + "|";
    line += DoubleToString(low, 5) + "|";
    line += DoubleToString(close, 5) + "|";
    line += (sweep_top ? "1" : "0") + "|";
    line += (sweep_bottom ? "1" : "0") + "|";
    line += DoubleToString(sweep_strength, 4) + "|";
    line += (is_strong_sweep ? "1" : "0") + "|";
    line += DoubleToString(displacement, 4) + "|";
    line += DoubleToString(directional_displacement, 4) + "|";
    line += DoubleToString(momentum_burst, 4) + "|";
    line += DoubleToString(exhaustion, 4) + "|";
    line += (break_high ? "1" : "0") + "|";
    line += (break_low ? "1" : "0") + "|";
    line += DoubleToString(break_strength, 4) + "|";
    line += DoubleToString(flow, 4) + "|";
    line += DoubleToString(flow_acceleration, 4) + "|";
    line += DoubleToString(flow_volatility, 4) + "|";
    line += DoubleToString(pos_range, 4) + "|";
    line += DoubleToString(dist_mean, 4) + "|";
    line += DoubleToString(zscore, 4) + "|";
    line += DoubleToString(atr_pct, 4) + "|";
    line += DoubleToString(vol_regime, 4) + "|";
    line += (vol_expansion ? "1" : "0") + "|";
    line += DoubleToString(sma_20, 5) + "|";
    line += DoubleToString(sma_50, 5) + "|";
    line += DoubleToString(ema_12, 5) + "|";
    line += DoubleToString(ema_26, 5) + "|";
    line += DoubleToString(reversal_score, 4) + "|";
    line += DoubleToString(entry_score, 4);
    
    // Write to file
    int file_handle = FileOpen(OUTPUT_FILE, FILE_CSV | FILE_WRITE | FILE_ANSI);
    if(file_handle != INVALID_HANDLE) {
        FileSeek(file_handle, 0, SEEK_END);  // Append mode
        FileWrite(file_handle, line);
        FileClose(file_handle);
        Print("Exported indicators: entry_score=" + DoubleToString(entry_score, 2));
    }
}

//+------------------------------------------------------------------+
//| Calculate Standard Deviation                                    |
//+------------------------------------------------------------------+
double iStdDev(string symbol, ENUM_TIMEFRAMES tf, int period, int shift, 
               ENUM_MA_METHOD method, ENUM_APPLIED_PRICE price, int bar_index)
{
    double mean = iMA(symbol, tf, period, shift, method, price, bar_index);
    double sum_sq = 0;
    
    for(int i = 0; i < period; i++) {
        double val = iClose(symbol, tf, bar_index + i);
        sum_sq += MathPow(val - mean, 2);
    }
    
    return MathSqrt(sum_sq / period);
}

//+------------------------------------------------------------------+
