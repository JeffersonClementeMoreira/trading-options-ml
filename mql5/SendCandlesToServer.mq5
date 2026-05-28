//+------------------------------------------------------------------+
//| SendCandlesToServer.mq5                                          |
//| MQL5 Script - Envia OHLC do MT5 para servidor Python via HTTP    |
//+------------------------------------------------------------------+
#property strict

input string ServerURL = "http://127.0.0.1:8765/mt5/candle";
input int IntervalMs = 15000;

//+------------------------------------------------------------------+
// Enviar candle (índice 0=atual, 1=último fechado, 2=anterior)
//+------------------------------------------------------------------+
void SendCandle(string symbol_mt5, string symbol_api, int index = 0)
{
    // Ler OHLC da corretora (usa símbolo da corretora: EURUSD, GBPUSD, GOLD)
    double o = iOpen(symbol_mt5, PERIOD_M15, index);
    double h = iHigh(symbol_mt5, PERIOD_M15, index);
    double l = iLow(symbol_mt5, PERIOD_M15, index);
    double c = iClose(symbol_mt5, PERIOD_M15, index);
    long v = iVolume(symbol_mt5, PERIOD_M15, index);
    datetime time_bar = iTime(symbol_mt5, PERIOD_M15, index);
    
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
    
    // Remove null terminator that StringToCharArray adds
    ArrayResize(data, ArraySize(data) - 1);
    
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
    Print("═══════════════════════════════════════════════════════════");
    Print("SendCandlesToServer.mq5 INICIADO");
    Print("Enviando para: ", ServerURL);
    Print("═══════════════════════════════════════════════════════════");
    
    // Rastrear últimos datetimes para detectar novos candles
    datetime last_time_eur = iTime("EURUSD", PERIOD_M15, 0);
    datetime last_time_gbp = iTime("GBPUSD", PERIOD_M15, 0);
    datetime last_time_xau = iTime("GOLD", PERIOD_M15, 0);
    
    Print("✓ Enviando ÚLTIMO CANDLE FECHADO inicial...");
    Print("");
    
    // Enviar último candle fechado (index=1) ao iniciar
    SendCandle("EURUSD", "EURUSD", 1);
    Sleep(500);
    SendCandle("GBPUSD", "GBPUSD", 1);
    Sleep(500);
    SendCandle("GOLD", "XAUUSD", 1);
    Sleep(500);
    
    Print("");
    Print("✓ Iniciando monitoramento de NOVOS candles...");
    Print("  (próximas 15 min, novo candle será enviado automaticamente)");
    Print("");
    
    // Agora monitorar novos candles
    while(true)
    {
        datetime current_time_eur = iTime("EURUSD", PERIOD_M15, 0);
        datetime current_time_gbp = iTime("GBPUSD", PERIOD_M15, 0);
        datetime current_time_xau = iTime("GOLD", PERIOD_M15, 0);
        
        // EURUSD: novo candle?
        if(current_time_eur != last_time_eur)
        {
            SendCandle("EURUSD", "EURUSD", 1);  // Enviar candle que acabou de fechar
            last_time_eur = current_time_eur;
            Sleep(500);
        }
        
        // GBPUSD: novo candle?
        if(current_time_gbp != last_time_gbp)
        {
            SendCandle("GBPUSD", "GBPUSD", 1);
            last_time_gbp = current_time_gbp;
            Sleep(500);
        }
        
        // GOLD/XAUUSD: novo candle?
        if(current_time_xau != last_time_xau)
        {
            SendCandle("GOLD", "XAUUSD", 1);
            last_time_xau = current_time_xau;
            Sleep(500);
        }
        
        Sleep(IntervalMs);
    }
}
//+------------------------------------------------------------------+
