//+------------------------------------------------------------------+
//| SendCandlesToServer.mq5 - Envia últimos candles REAIS para servidor |
//| Propósito: APENAS dados reais, sem simulação                       |
//+------------------------------------------------------------------+
#property copyright "Trading ML System"
#property link      "https://github.com/JeffersonClementeMoreira/trading-options-ml"
#property version   "2.04"
#property strict
#property description "Envia último candle M15 REAL fechado para servidor HTTP"

//+------------------------------------------------------------------+
// CONFIGURAÇÃO
//+------------------------------------------------------------------+

input string ServerURL = "http://127.0.0.1:8765/mt5/candle/real";  // ← EDITE AQUI
input string Symbols = "EURUSD,GBPUSD,EURJPY,NZDUSD";
input int SendInterval = 60;  // segundos entre envios
input bool LogToFile = true;

//+------------------------------------------------------------------+
// VARIÁVEIS GLOBAIS
//+------------------------------------------------------------------+

int lastSendTime = 0;
string logFile = "SendCandlesToServer.log";

//+------------------------------------------------------------------+
// INIT
//+------------------------------------------------------------------+

int OnInit()
{
    Print("📊 SendCandlesToServer v2.03 INICIADO");
    Print("🌐 Servidor: " + ServerURL);
    Print("📈 Pares: " + Symbols);
    Print("⏱️  Intervalo: " + IntegerToString(SendInterval) + "s");
    Print("");
    
    // Puxar 21 candles históricos imediatamente ao anexar!
    Print("⏳ Puxando 21 candles históricos...");
    SendHistoricalCandles("EURUSD");
    SendHistoricalCandles("GBPUSD");
    SendHistoricalCandles("EURJPY");
    SendHistoricalCandles("NZDUSD");
    Print("✅ Histórico carregado!");
    Print("");
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
// TIMER - Verifica novos candles M15
//+------------------------------------------------------------------+

void OnTick()
{
    // Verificar a cada segundo
    int currentTime = (int)TimeCurrent();
    
    // Enviar apenas se passou intervalo
    if (currentTime - lastSendTime < SendInterval) {
        return;
    }
    
    // Processar pares manualmente (sem StringSplit para compatibilidade)
    SendLastRealCandle("EURUSD");
    SendLastRealCandle("GBPUSD");
    SendLastRealCandle("EURJPY");
    SendLastRealCandle("NZDUSD");
    
    lastSendTime = currentTime;
}

//+------------------------------------------------------------------+
// ENVIAR ÚLTIMOS 21 CANDLES M15 HISTÓRICOS
//+------------------------------------------------------------------+

void SendHistoricalCandles(string symbol)
{
    // Copiar últimos 21 candles M15 HISTÓRICOS
    datetime time[];
    double open[], high[], low[], close[];
    long volume[];
    
    if (CopyTime(symbol, PERIOD_M15, 0, 21, time) != 21 ||
        CopyOpen(symbol, PERIOD_M15, 0, 21, open) != 21 ||
        CopyHigh(symbol, PERIOD_M15, 0, 21, high) != 21 ||
        CopyLow(symbol, PERIOD_M15, 0, 21, low) != 21 ||
        CopyClose(symbol, PERIOD_M15, 0, 21, close) != 21 ||
        CopyTickVolume(symbol, PERIOD_M15, 0, 21, volume) != 21)
    {
        Log("[ERROR] " + symbol + " não conseguiu copiar 21 candles históricos");
        return;
    }
    
    // Enviar todos os 21 candles (do mais antigo para o mais novo)
    for(int i = 20; i >= 0; i--)
    {
        datetime candle_time = time[i];
        double candle_open = open[i];
        double candle_high = high[i];
        double candle_low = low[i];
        double candle_close = close[i];
        long candle_volume = volume[i];
        
        // Formatar timestamp
        MqlDateTime dt;
        TimeToStruct(candle_time, dt);
        string datetime_str = StringFormat("%04d.%02d.%02d %02d:%02d:00", 
                                            dt.year, dt.mon, dt.day, dt.hour, dt.min);
        
        // Criar JSON
        string json_str = "{";
        json_str += "\"symbol\":\"" + symbol + "\",";
        json_str += "\"datetime\":\"" + datetime_str + "\",";
        json_str += "\"open\":" + DoubleToString(candle_open, 5) + ",";
        json_str += "\"high\":" + DoubleToString(candle_high, 5) + ",";
        json_str += "\"low\":" + DoubleToString(candle_low, 5) + ",";
        json_str += "\"close\":" + DoubleToString(candle_close, 5) + ",";
        json_str += "\"volume\":" + IntegerToString((int)candle_volume);
        json_str += "}";
        
        // Enviar HTTP POST
        uchar post_data[];
        uchar result[];
        string result_headers;
        string headers = "Content-Type: application/json";
        
        // Limpar array
        ArrayFree(post_data);
        ArrayResize(post_data, 0);
        
        // Converter com tamanho exato
        int json_len = StringLen(json_str);
        ArrayResize(post_data, json_len);
        for(int j = 0; j < json_len; j++) {
            post_data[j] = (uchar)json_str[j];
        }
        
        int ret = WebRequest("POST", ServerURL, headers, 30000, post_data, result, result_headers);
        
        if (ret == 200) {
            Log("[HIST] " + symbol + " ✓ " + datetime_str + " O=" + DoubleToString(candle_open, 5) + 
                " C=" + DoubleToString(candle_close, 5) + " V=" + IntegerToString((int)candle_volume));
        }
        else {
            Log("[HIST-ERROR] " + symbol + " code=" + IntegerToString(ret));
        }
    }
}

//+------------------------------------------------------------------+
// ENVIAR ÚLTIMO CANDLE M15 REAL
//+------------------------------------------------------------------+

void SendLastRealCandle(string symbol)
{
    // Copiar último candle M15 FECHADO
    datetime time[];
    double open[], high[], low[], close[];
    long volume[];
    
    // Último candle (index 1 = candle anterior completamente fechado)
    if (CopyTime(symbol, PERIOD_M15, 1, 1, time) <= 0 ||
        CopyOpen(symbol, PERIOD_M15, 1, 1, open) <= 0 ||
        CopyHigh(symbol, PERIOD_M15, 1, 1, high) <= 0 ||
        CopyLow(symbol, PERIOD_M15, 1, 1, low) <= 0 ||
        CopyClose(symbol, PERIOD_M15, 1, 1, close) <= 0 ||
        CopyTickVolume(symbol, PERIOD_M15, 1, 1, volume) <= 0)
    {
        Log("[ERROR] " + symbol + " não conseguiu copiar dados");
        return;
    }
    
    datetime candle_time = time[0];
    double candle_open = open[0];
    double candle_high = high[0];
    double candle_low = low[0];
    double candle_close = close[0];
    long candle_volume = volume[0];
    
    // Formatar timestamp: "YYYY.MM.DD HH:MM:SS"
    MqlDateTime dt;
    TimeToStruct(candle_time, dt);
    string datetime_str = StringFormat("%04d.%02d.%02d %02d:%02d:00", 
                                        dt.year, dt.mon, dt.day, dt.hour, dt.min);
    
    // Criar JSON manualmente (sem biblioteca)
    string json_str = "{";
    json_str += "\"symbol\":\"" + symbol + "\",";
    json_str += "\"datetime\":\"" + datetime_str + "\",";
    json_str += "\"open\":" + DoubleToString(candle_open, 5) + ",";
    json_str += "\"high\":" + DoubleToString(candle_high, 5) + ",";
    json_str += "\"low\":" + DoubleToString(candle_low, 5) + ",";
    json_str += "\"close\":" + DoubleToString(candle_close, 5) + ",";
    json_str += "\"volume\":" + IntegerToString((int)candle_volume);
    json_str += "}";
    
    // Enviar HTTP POST (sintaxe MQL5 correta)
    uchar post_data[];
    uchar result[];
    string result_headers;
    string headers = "Content-Type: application/json";
    
    // Limpar array e converter com tamanho exato
    ArrayFree(post_data);
    ArrayResize(post_data, 0);
    
    int json_len = StringLen(json_str);
    ArrayResize(post_data, json_len);
    for(int j = 0; j < json_len; j++) {
        post_data[j] = (uchar)json_str[j];
    }
    
    // WebRequest com assinatura correta
    int ret = WebRequest("POST", ServerURL, headers, 30000, post_data, result, result_headers);
    
    if (ret == 200) {
        Log("[OK] " + symbol + " ✓ " + datetime_str + " O=" + DoubleToString(candle_open, 5) + 
            " C=" + DoubleToString(candle_close, 5) + " V=" + IntegerToString((int)candle_volume));
    }
    else if (ret == 400) {
        Log("[ERROR] " + symbol + " code=400");
    }
    else if (ret == -1) {
        Log("[ERROR] " + symbol + " code=-1 (rede/timeout)");
    }
    else {
        Log("[ERROR] " + symbol + " code=" + IntegerToString(ret));
    }
}

//+------------------------------------------------------------------+
// LOG
//+------------------------------------------------------------------+

void Log(string msg)
{
    Print(msg);
    
    if (!LogToFile) return;
    
    int file = FileOpen("SendCandlesToServer.log", FILE_READ | FILE_WRITE | FILE_CSV);
    if (file != INVALID_HANDLE) {
        FileSeek(file, 0, SEEK_END);
        MqlDateTime dt;
        TimeToStruct(TimeCurrent(), dt);
        string time_log = StringFormat("%04d.%02d.%02d %02d:%02d:%02d", 
                                       dt.year, dt.mon, dt.day, dt.hour, dt.min, dt.sec);
        FileWrite(file, time_log + " " + msg);
        FileClose(file);
    }
}

//+------------------------------------------------------------------+
// DEINIT
//+------------------------------------------------------------------+

void OnDeinit(const int reason)
{
    Print("❌ EA PARADO");
}
