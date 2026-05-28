//+------------------------------------------------------------------+
//| SendCandleForNextDayPrediction.mq5                               |
//| Coletar candle atual e enviar para servidor fazer previsão D+1   |
//+------------------------------------------------------------------+
#property copyright "2024"
#property version   "1.0"
#property strict

input string   SYMBOL_TO_MONITOR = "EURUSD";
input ENUM_TIMEFRAMES TIMEFRAME = PERIOD_M15;
input int      SERVER_PORT = 9876;
input string   SERVER_HOST = "127.0.0.1";

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("EA iniciado: ", SYMBOL_TO_MONITOR, " M15");
   Print("Servidor: ", SERVER_HOST, ":", SERVER_PORT);
   return(INIT_SUCCEEDED);
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("EA finalizado");
}

//+------------------------------------------------------------------+
//| Expert tick function                                             |
//+------------------------------------------------------------------+
void OnTick()
{
   // Verificar se novo candle
   static int last_bar_time = 0;
   int current_bar_time = (int)iTime(_Symbol, _Period, 0);
   
   if (current_bar_time == last_bar_time)
      return;
   
   last_bar_time = current_bar_time;
   
   // Coletar dados
   double close = iClose(_Symbol, _Period, 1);  // Candle anterior (fechado)
   double open = iOpen(_Symbol, _Period, 1);
   double high = iHigh(_Symbol, _Period, 1);
   double low = iLow(_Symbol, _Period, 1);
   long volume = iVolume(_Symbol, _Period, 1);
   
   // Calcular indicadores simples
   double rsi = CalculateRSI(14);
   double sma_20 = CalculateSMA(20);
   double sma_50 = CalculateSMA(50);
   double atr_pct = CalculateATR() / close;
   double momentum = (close - iClose(_Symbol, _Period, 11)) / iClose(_Symbol, _Period, 11);
   double distance_std = CalculateDistanceStd(20);
   double volume_ratio = (double)volume / CalculateVolumeMA(20);
   
   // Preparar JSON
   string json_data = "{";
   json_data += "\"symbol\":\"" + _Symbol + "\",";
   json_data += "\"candle\":{";
   json_data += "\"close\":" + DoubleToString(close, _Digits) + ",";
   json_data += "\"rsi\":" + DoubleToString(rsi, 2) + ",";
   json_data += "\"sma_20\":" + DoubleToString(sma_20, _Digits) + ",";
   json_data += "\"sma_50\":" + DoubleToString(sma_50, _Digits) + ",";
   json_data += "\"atr_pct\":" + DoubleToString(atr_pct, 6) + ",";
   json_data += "\"momentum\":" + DoubleToString(momentum, 6) + ",";
   json_data += "\"distance_std\":" + DoubleToString(distance_std, 2) + ",";
   json_data += "\"volume\":" + IntegerToString(volume) + ",";
   json_data += "\"volume_ratio\":" + DoubleToString(volume_ratio, 2);
   json_data += "}";
   json_data += "}";
   
   // Enviar para servidor
   SendPredictionRequest(json_data, close, rsi);
}

//+------------------------------------------------------------------+
//| Enviar requisição para servidor                                  |
//+------------------------------------------------------------------+
void SendPredictionRequest(string json_data, double price, double rsi)
{
   char data[];
   char result[];
   
   StringToCharArray(json_data, data);
   
   // Remove null terminator
   if (ArraySize(data) > 0 && data[ArraySize(data)-1] == 0)
      ArrayResize(data, ArraySize(data)-1);
   
   string url = "http://" + SERVER_HOST + ":" + IntegerToString(SERVER_PORT) + "/predict/nextday";
   
   int timeout = 5000;  // 5 segundos
   
   int response_code = WebRequest("POST", 
                                  url,
                                  "Content-Type: application/json\r\n",
                                  timeout,
                                  data,
                                  result);
   
   if (response_code == 200)
   {
      // Parsear resposta
      string response_str = CharArrayToString(result);
      
      // Extrair previsão (simples)
      int pos_direction = StringFind(response_str, "predicted_direction");
      int pos_confidence = StringFind(response_str, "confidence");
      int pos_expected_pips = StringFind(response_str, "expected_pips");
      
      if (pos_direction >= 0)
      {
         Print("✅ Previsão recebida para ", _Symbol, " @ ", price);
         Print("   Resposta: ", response_str);
      }
   }
   else
   {
      Print("❌ Erro no request. Código: ", response_code);
   }
}

//+------------------------------------------------------------------+
//| Calcular RSI                                                     |
//+------------------------------------------------------------------+
double CalculateRSI(int period)
{
   double rsi_values = iRSI(_Symbol, _Period, period, PRICE_CLOSE, 0);
   return rsi_values;
}

//+------------------------------------------------------------------+
//| Calcular SMA                                                     |
//+------------------------------------------------------------------+
double CalculateSMA(int period)
{
   double sma = iMA(_Symbol, _Period, period, 0, MODE_SMA, PRICE_CLOSE, 0);
   return sma;
}

//+------------------------------------------------------------------+
//| Calcular ATR                                                     |
//+------------------------------------------------------------------+
double CalculateATR()
{
   double atr = iATR(_Symbol, _Period, 14, 0);
   return atr;
}

//+------------------------------------------------------------------+
//| Calcular distância do SMA (em desvios padrão)                    |
//+------------------------------------------------------------------+
double CalculateDistanceStd(int period)
{
   double sma = iMA(_Symbol, _Period, period, 0, MODE_SMA, PRICE_CLOSE, 0);
   double close = iClose(_Symbol, _Period, 0);
   double std = iStdDev(_Symbol, _Period, period, 0, MODE_SMA, PRICE_CLOSE, 0);
   
   if (std == 0) return 0;
   return (close - sma) / std;
}

//+------------------------------------------------------------------+
//| Calcular volume médio                                            |
//+------------------------------------------------------------------+
double CalculateVolumeMA(int period)
{
   double vol_sum = 0;
   
   for (int i = 0; i < period; i++)
      vol_sum += iVolume(_Symbol, _Period, i);
   
   return vol_sum / period;
}
