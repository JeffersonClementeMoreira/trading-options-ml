//+------------------------------------------------------------------+
//| GetCandleData.mq5                                               |
//| MQL5 Script - Copy last closed candle data to clipboard         |
//| Usage: Attach to any chart, it will show last M15 candle data   |
//+------------------------------------------------------------------+
#property strict

void OnStart()
{
    Print("═══════════════════════════════════════════════════════════");
    Print("Getting last closed M15 candle data...");
    Print("═══════════════════════════════════════════════════════════");
    
    // Get current symbol
    string symbol = Symbol();
    
    // Get last closed candle (index=1)
    double o = iOpen(symbol, PERIOD_M15, 1);
    double h = iHigh(symbol, PERIOD_M15, 1);
    double l = iLow(symbol, PERIOD_M15, 1);
    double c = iClose(symbol, PERIOD_M15, 1);
    long v = iVolume(symbol, PERIOD_M15, 1);
    datetime time_bar = iTime(symbol, PERIOD_M15, 1);
    
    // Format datetime
    MqlDateTime dt;
    TimeToStruct(time_bar, dt);
    string dt_str = StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",
        dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
    
    // Map symbol names
    string symbol_api = symbol;
    if (symbol == "GOLD") symbol_api = "XAUUSD";
    
    // Show data
    Print("");
    Print("Symbol:   ", symbol);
    Print("DateTime: ", dt_str);
    Print("Open:     ", DoubleToString(o, 5));
    Print("High:     ", DoubleToString(h, 5));
    Print("Low:      ", DoubleToString(l, 5));
    Print("Close:    ", DoubleToString(c, 5));
    Print("Volume:   ", IntegerToString(v));
    Print("");
    
    // Format as JSON
    string json = "{";
    json = json + "\"symbol\":\"" + symbol_api + "\",";
    json = json + "\"datetime\":\"" + dt_str + "\",";
    json = json + "\"open\":" + DoubleToString(o, 5) + ",";
    json = json + "\"high\":" + DoubleToString(h, 5) + ",";
    json = json + "\"low\":" + DoubleToString(l, 5) + ",";
    json = json + "\"close\":" + DoubleToString(c, 5) + ",";
    json = json + "\"volume\":" + IntegerToString(v);
    json = json + "}";
    
    Print("JSON:");
    Print(json);
    Print("");
    Print("═══════════════════════════════════════════════════════════");
    Print("Copy the JSON above and use test_mt5_data.py to send it");
    Print("═══════════════════════════════════════════════════════════");
}
//+------------------------------------------------------------------+
