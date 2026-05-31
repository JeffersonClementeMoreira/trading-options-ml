//+------------------------------------------------------------------+
//| SendCandlesToServer.mq5 - Envia últimos candles REAIS para servidor |
//| Propósito: APENAS dados reais, sem simulação                       |
//+------------------------------------------------------------------+
#property copyright "Trading ML System"
#property link      "https://github.com/JeffersonClementeMoreira/trading-options-ml"
#property version   "2.00"
#property strict
#property description "Envia último candle M15 REAL fechado para servidor HTTP"

#include <JAson.mqh>

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
    Print("📊 SendCandlesToServer v2.0 INICIADO");
    Print("🌐 Servidor: " + ServerURL);
    Print("📈 Pares: " + Symbols);
    Print("⏱️  Intervalo: " + IntegerToString(SendInterval) + "s");
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
    
    // Processar todos os pares
    string symArray[];
    int count = StringSplit(Symbols, ',', symArray);
    
    for (int i = 0; i < count; i++) {
        string symbol = symArray[i];
        symbol = StringTrim(symbol);
        
        if (symbol == "") continue;
        
        // Enviar último candle M15 REAL
        SendLastRealCandle(symbol);
    }
    
    lastSendTime = currentTime;
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
    string datetime_str = TimeToString(candle_time, TIME_DATE | TIME_MINUTES);
    datetime_str = StringSubstr(datetime_str, 0, 10) + " " + StringSubstr(datetime_str, 11, 5) + ":00";
    
    // Criar JSON
    CJSONObject *json = new CJSONObject();
    json.AddString("symbol", symbol);
    json.AddString("datetime", datetime_str);
    json.AddDouble("open", candle_open);
    json.AddDouble("high", candle_high);
    json.AddDouble("low", candle_low);
    json.AddDouble("close", candle_close);
    json.AddNumber("volume", (double)candle_volume);
    
    string json_str = json.Serialize();
    
    // Enviar HTTP POST
    int request_id = 0;
    char post_data[];
    char result[];
    string headers = "Content-Type: application/json\r\n";
    
    StringToCharArray(json_str, post_data, 0, StringLen(json_str));
    
    int ret = WebRequest(
        "POST",
        ServerURL,
        headers,
        30000,  // timeout 30s
        post_data,
        result
    );
    
    if (ret == 200) {
        Log("[OK] " + symbol + " ✓ " + datetime_str + " O=" + DoubleToString(candle_open, 5) + 
            " C=" + DoubleToString(candle_close, 5) + " V=" + IntegerToString((int)candle_volume));
    }
    else if (ret == 400) {
        Log("[ERROR] " + symbol + " code=400 (requisição inválida)");
    }
    else if (ret == -1) {
        Log("[ERROR] " + symbol + " code=-1 (erro de rede/timeout)");
    }
    else {
        Log("[ERROR] " + symbol + " code=" + IntegerToString(ret));
    }
    
    delete json;
}

//+------------------------------------------------------------------+
// LOG
//+------------------------------------------------------------------+

void Log(string msg)
{
    Print(msg);
    
    if (!LogToFile) return;
    
    int file = FileOpen(logFile, FILE_READ | FILE_WRITE | FILE_CSV);
    if (file != INVALID_HANDLE) {
        FileSeek(file, 0, SEEK_END);
        FileWrite(file, TimeToString(TimeCurrent()) + " " + msg);
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
