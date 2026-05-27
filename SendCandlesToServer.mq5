//+------------------------------------------------------------------+
//| SendCandlesToServer.mq5                                          |
//| MQL5 Script - Envia OHLC do MT5 para servidor Python via HTTP    |
//+------------------------------------------------------------------+
#property strict

input string ServerURL = "http://127.0.0.1:8765/mt5/candle";
input int IntervalMs = 15000;

//+------------------------------------------------------------------+
// Enviar candle
//+------------------------------------------------------------------+
void SendCandle(string symbol_mt5, string symbol_api)
{
    // Ler OHLC da corretora (usa símbolo da corretora: EURUSD, GBPUSD, GOLD)
    double o = iOpen(symbol_mt5, PERIOD_M15, 0);
    double h = iHigh(symbol_mt5, PERIOD_M15, 0);
    double l = iLow(symbol_mt5, PERIOD_M15, 0);
    double c = iClose(symbol_mt5, PERIOD_M15, 0);
    long v = iVolume(symbol_mt5, PERIOD_M15, 0);
    datetime time_bar = iTime(symbol_mt5, PERIOD_M15, 0);
    
    // String datetime em ISO 8601 (YYYY-MM-DDTHH:MM:SS)
    MqlDateTime dt;
    TimeToStruct(time_bar, dt);
    string dt_str = StringFormat("%04d-%02d-%02dT%02d:%02d:%02d",
        dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
    
    // Montar JSON (envia com símbolo padronizado: XAUUSD em vez de GOLD)
    string json = "{";
    json = json + "\"symbol\":\"" + symbol_api + "\",";
    json = json + "\"datetime\":\"" + dt_str + "\",";
    json = json + "\"open\":" + DoubleToString(o, 5) + ",";
    json = json + "\"high\":" + DoubleToString(h, 5) + ",";
    json = json + "\"low\":" + DoubleToString(l, 5) + ",";
    json = json + "\"close\":" + DoubleToString(c, 5) + ",";
    json = json + "\"volume\":" + IntegerToString(v);
    json = json + "}";
    
    // Enviar via HTTP
    uchar data[];
    uchar result[];
    string result_headers;
    
    StringToCharArray(json, data);
    
    string headers = "Content-Type: application/json";
    
    int res = WebRequest("POST", ServerURL, headers, 5000, data, result, result_headers);
    
    if(res == 200)
    {
        Print("[OK] ", symbol_mt5, " → ", symbol_api, " ", dt_str, " ", c);
    }
    else
    {
        Print("[ERROR] ", symbol_mt5, " code=", res);
    }
}

//+------------------------------------------------------------------+
void OnStart()
{
    Print("Start - sending to ", ServerURL);
    
    while(true)
    {
        SendCandle("EURUSD", "EURUSD");
        Sleep(500);
        
        SendCandle("GBPUSD", "GBPUSD");
        Sleep(500);
        
        SendCandle("GOLD", "XAUUSD");  // Corretora: GOLD | API: XAUUSD
        Sleep(500);
        
        Sleep(IntervalMs);
    }
}
//+------------------------------------------------------------------+
