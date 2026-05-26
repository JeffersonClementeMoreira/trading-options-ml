# ═════════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÃO - Monitor WebSocket MT5
# ═════════════════════════════════════════════════════════════════════════════

# WebSocket Configuration
WEBSOCKET_URL = "ws://localhost:9001"  # URL do seu servidor WebSocket MT5

# Telegram
BOT_TOKEN = "6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0"
CHAT_ID = -1001735082183

# Pares para monitorar
SYMBOLS = ["GBPUSD", "EURUSD", "XAUUSD"]

# Timeframe
TIMEFRAME = "M15"

# XGBoost Score Mínimo para Sinais
MIN_SCORE_FOR_SIGNAL = 0.70  # 70%

# ═════════════════════════════════════════════════════════════════════════════
# INSTRUÇÕES DE SETUP
# ═════════════════════════════════════════════════════════════════════════════

# OPÇÃO 1: Usar Expert Advisor no MT5
# ───────────────────────────────────────────────────────────────────────────
# Crie um EA no MT5 que envia candles via WebSocket:
# 
# #property copyright "MT5 WebSocket Adapter"
# #property version   "1.00"
# 
# #include <WebSocket.mqh>
# 
# WebSocket ws;
# 
# int OnInit() {
#     ws.Connect("localhost", 9001);
#     return INIT_SUCCEEDED;
# }
# 
# void OnTick() {
#     // Enviar candle atual (M15)
#     if (IsNewCandle()) {
#         string json = StringFormat(
#             "{\"symbol\":\"%s\",\"time\":\"%s\",\"open\":%.5f,\"high\":%.5f,\"low\":%.5f,\"close\":%.5f,\"volume\":%d}",
#             Symbol(), TimeToString(iTime(Symbol(), PERIOD_M15, 1)), 
#             iOpen(Symbol(), PERIOD_M15, 1), iHigh(Symbol(), PERIOD_M15, 1),
#             iLow(Symbol(), PERIOD_M15, 1), iClose(Symbol(), PERIOD_M15, 1),
#             (int)iVolume(Symbol(), PERIOD_M15, 1)
#         );
#         ws.Send(json);
#     }
# }

# OPÇÃO 2: Usar MT5 com Python (sem WebSocket)
# ───────────────────────────────────────────────────────────────────────────
# pip install MetaTrader5
# 
# import MetaTrader5 as mt5
# mt5.initialize(path="C:\\Program Files\\MetaTrader 5\\terminal64.exe")
# rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M15, 0, 100)

# OPÇÃO 3: Usar servidor WebSocket Python intermediário
# ───────────────────────────────────────────────────────────────────────────
# Rode em outro terminal:
# python3 mt5_websocket_server.py

# ═════════════════════════════════════════════════════════════════════════════
