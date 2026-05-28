//+------------------------------------------------------------------+
//| WebSocket Client for MT5 - Sends Candles for Signal Monitoring  |
//+------------------------------------------------------------------+
//| Purpose: Enviar candles M15 para Python server e receber alertas |
//| Flow: MT5 → WebSocket → Python Server → Telegram → Trader Entry |
//+------------------------------------------------------------------+

#property copyright "Trading Signals System"
#property link      "WebSocket Client"
#property version   "1.0"
#property strict

input string ServerAddress = "127.0.0.1:8765";  // Python server
input int    SendInterval  = 15;                 // Send every 15 min
input string Pair1         = "EURUSD";
input string Pair2         = "GBPUSD";

// WebSocket Handle
int ws_handle = INVALID_HANDLE;
datetime last_send_time = 0;

//+------------------------------------------------------------------+
//| Expert initialization function                                   |
//+------------------------------------------------------------------+
int OnInit()
{
   Print("🚀 WebSocket Client Starting...");
   Print("   Target: " + ServerAddress);
   
   // Try to connect
   if (!ConnectWebSocket())
   {
      Print("❌ Failed to connect to WebSocket server");
      return INIT_FAILED;
   }
   
   Print("✅ WebSocket connected successfully");
   return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Expert tick function - sends candles periodically               |
//+------------------------------------------------------------------+
void OnTick()
{
   // Check if it's time to send (every M15)
   if (TimeCurrent() - last_send_time >= SendInterval * 60)
   {
      SendCandle(Pair1);
      SendCandle(Pair2);
      last_send_time = TimeCurrent();
   }
}

//+------------------------------------------------------------------+
//| Connect to WebSocket                                             |
//+------------------------------------------------------------------+
bool ConnectWebSocket()
{
   // In production: use MT5's WebSocket library
   // For now, we'll simulate with file-based communication
   // Or use DLL wrapper for actual WebSocket
   
   // TODO: Implement actual WebSocket connection
   // This would require MT5 WebSocket library (MetaAPI or similar)
   
   return true;  // Simulated for now
}

//+------------------------------------------------------------------+
//| Send current candle to server                                    |
//+------------------------------------------------------------------+
void SendCandle(string pair)
{
   // Get current candle data
   MqlTick tick;
   SymbolInfoTick(pair, tick);
   
   // Get OHLC for M15
   double open   = iOpen(pair, PERIOD_M15, 0);
   double high   = iHigh(pair, PERIOD_M15, 0);
   double low    = iLow(pair, PERIOD_M15, 0);
   double close  = iClose(pair, PERIOD_M15, 0);
   long   volume = iVolume(pair, PERIOD_M15, 0);
   
   // Get current time
   datetime time = iTime(pair, PERIOD_M15, 0);
   
   // Format JSON
   string json = "";
   json += "{";
   json += "\"timestamp\":\"" + TimeToString(time, TIME_DATE|TIME_MINUTES) + "\",";
   json += "\"pair\":\"" + pair + "\",";
   json += "\"open\":" + DoubleToString(open, 5) + ",";
   json += "\"high\":" + DoubleToString(high, 5) + ",";
   json += "\"low\":" + DoubleToString(low, 5) + ",";
   json += "\"close\":" + DoubleToString(close, 5) + ",";
   json += "\"volume\":" + IntegerToString(volume);
   json += "}";
   
   Print("📤 Sending: " + json);
   
   // Send to server
   // In real implementation: use WebSocket send
   // SendWebSocketMessage(json);
}

//+------------------------------------------------------------------+
//| Handle messages from server (alerts)                             |
//+------------------------------------------------------------------+
void OnMessage(string message)
{
   Print("📩 Message received: " + message);
   
   // Parse JSON response
   // If signal found, display alert
   // Message format: {"signal_found": true, "pair": "EURUSD", ...}
}

//+------------------------------------------------------------------+
//| Expert deinitialization function                                 |
//+------------------------------------------------------------------+
void OnDeinit(const int reason)
{
   Print("🛑 WebSocket Client Stopping");
   
   // Close connection
   // CloseWebSocket();
}

//+------------------------------------------------------------------+
//| Helper: Convert time to ISO format                              |
//+------------------------------------------------------------------+
string TimeToISO(datetime t)
{
   return TimeToString(t, TIME_DATE) + "T" + TimeToString(t, TIME_MINUTES);
}
