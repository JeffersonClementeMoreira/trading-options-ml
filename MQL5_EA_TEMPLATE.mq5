// ✅ EA TEMPLATE MQL5 PARA INTEGRAÇÃO COM PYTHON XGBOOST
// 
// Fluxo:
// 1. Calcula indicadores
// 2. Detecta confluência
// 3. Detecta sweeps
// 4. POST para Python
// 5. Recebe decisão (BUY/SELL/HOLD)
// 6. Executa trade
//
// Colocar em: MT5 → Experts → Advisors → seu_ea.mq5

#property copyright "Your Name"
#property link      "https://github.com/JeffersonClementeMoreira/options"
#property version   "1.00"
#property strict

// === CONFIGURAÇÕES ===
input double riskPercent = 1.0;          // Risco por trade (%)
input double confidenceThreshold = 0.65; // Confiança mínima
input bool enableTrading = true;         // Ativar trades
input bool debugMode = true;             // Debug logs


// === ARRAYS PARA INDICADORES ===
double sma20[], sma50[], sma200[];
double ema12[], ema26[];
double rsi14[], macd[], signal[], hist[];
double stoch_k[], stoch_d[];
double bb_upper[], bb_lower[];


void OnInit() {
    Print("✅ EA Iniciado");
    
    // Setup indicadores
    SetupIndicators();
}


void OnDeinit(const int reason) {
    Print("🛑 EA Finalizado: " + reason);
}


void OnTick() {
    // Esperar novo candle
    static datetime lastCandle = 0;
    if (TimeCurrent() <= lastCandle) return;
    lastCandle = TimeCurrent();
    
    if (debugMode) {
        Print("📊 Novo candle em " + TimeToString(TimeCurrent()));
    }
    
    // Calcular indicadores
    double indicators[];
    CalculateIndicators(indicators);
    
    // Detectar confluência
    string m15_trend = DetectM15Trend();
    string h4_trend = DetectH4Trend();
    bool is_aligned = (m15_trend == h4_trend);
    double alignment_score = is_aligned ? 0.90 : 0.50;
    
    // Detectar sweeps
    string h4_sweep_type = DetectH4Sweep();
    string m15_confirmation = ValidateM15(h4_sweep_type);
    string momentum_trend = AnalyzeMomentum();
    
    // Calcular flow
    double flow_score = CalculateFlowScore();
    string regime = DetectRegime();
    
    // Montar JSON
    string json = BuildJSON(
        m15_trend, h4_trend, is_aligned, alignment_score,
        h4_sweep_type, m15_confirmation, momentum_trend,
        flow_score, regime, indicators
    );
    
    // Enviar para Python
    if (debugMode) {
        Print("📤 Enviando para Python...");
    }
    
    string response = SendToPython(json);
    
    // Processar resposta
    if (response != "") {
        ProcessResponse(response);
    }
}


// === CÁLCULO DE INDICADORES ===

void SetupIndicators() {
    // Setup arrays
    // Exemplo com iMA, iRSI, etc
}


void CalculateIndicators(double &indicators[]) {
    // SMA
    double sma20 = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma50 = iMA(_Symbol, PERIOD_M15, 50, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma200 = iMA(_Symbol, PERIOD_M15, 200, 0, MODE_SMA, PRICE_CLOSE, 0);
    
    // EMA
    double ema12 = iMA(_Symbol, PERIOD_M15, 12, 0, MODE_EMA, PRICE_CLOSE, 0);
    double ema26 = iMA(_Symbol, PERIOD_M15, 26, 0, MODE_EMA, PRICE_CLOSE, 0);
    
    // RSI
    double rsi14 = iRSI(_Symbol, PERIOD_M15, 14, PRICE_CLOSE, 0);
    
    // ATR
    double atr = iATR(_Symbol, PERIOD_M15, 14, 0);
    double atr_pct = (atr / Close[0]) * 100;
    
    // Retornos
    double close_prev1 = Close[1];
    double close_prev3 = Close[3];
    double close_prev5 = Close[5];
    double ret_1 = (Close[0] - close_prev1) / close_prev1;
    double ret_3 = (Close[0] - close_prev3) / close_prev3;
    double ret_5 = (Close[0] - close_prev5) / close_prev5;
    
    // Volatilidade (simplified)
    double realized_vol = CalculateVolatility(14);
    double expected_move = CalculateExpectedMove();
    
    // Bollinger Bands
    double bb_middle = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
    double bb_std = iStdDev(_Symbol, PERIOD_M15, 20, 0, PRICE_CLOSE, 0);
    double bb_upper = bb_middle + (2 * bb_std);
    double bb_lower = bb_middle - (2 * bb_std);
    double bb_position = (Close[0] - bb_lower) / (bb_upper - bb_lower);
    
    // MACD
    double macd = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
    double signal = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE, MODE_SIGNAL, 0);
    double macd_hist = macd - signal;
    
    // Stochastic
    double stoch_k = iStochastic(_Symbol, PERIOD_M15, 14, 3, 3, MODE_RSI, MODE_MAIN, 0);
    double stoch_d = iStochastic(_Symbol, PERIOD_M15, 14, 3, 3, MODE_RSI, MODE_SIGNAL, 0);
    
    // Guardar em array
    indicators[0] = sma20;
    indicators[1] = sma50;
    indicators[2] = sma200;
    indicators[3] = ema12;
    indicators[4] = ema26;
    indicators[5] = rsi14;
    indicators[6] = atr_pct;
    indicators[7] = bb_upper;
    indicators[8] = bb_lower;
    indicators[9] = bb_position;
    indicators[10] = macd;
    indicators[11] = signal;
    indicators[12] = macd_hist;
    indicators[13] = stoch_k;
    indicators[14] = stoch_d;
    indicators[15] = ret_1;
    indicators[16] = ret_3;
    indicators[17] = ret_5;
    indicators[18] = realized_vol;
    indicators[19] = expected_move;
}


// === DETECÇÃO DE CONFLUÊNCIA ===

string DetectM15Trend() {
    double sma20 = iMA(_Symbol, PERIOD_M15, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma50 = iMA(_Symbol, PERIOD_M15, 50, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma200 = iMA(_Symbol, PERIOD_M15, 200, 0, MODE_SMA, PRICE_CLOSE, 0);
    double close = Close[0];
    
    if (close > sma20 && sma20 > sma50 && sma50 > sma200) {
        return "UP";
    } else if (close < sma20 && sma20 < sma50 && sma50 < sma200) {
        return "DOWN";
    } else {
        return "NEUTRAL";
    }
}


string DetectH4Trend() {
    double sma20 = iMA(_Symbol, PERIOD_H4, 20, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma50 = iMA(_Symbol, PERIOD_H4, 50, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma200 = iMA(_Symbol, PERIOD_H4, 200, 0, MODE_SMA, PRICE_CLOSE, 0);
    double close = iClose(_Symbol, PERIOD_H4, 0);
    
    if (close > sma20 && sma20 > sma50 && sma50 > sma200) {
        return "UP";
    } else if (close < sma20 && sma20 < sma50 && sma50 < sma200) {
        return "DOWN";
    } else {
        return "NEUTRAL";
    }
}


// === DETECÇÃO DE SWEEPS ===

string DetectH4Sweep() {
    // Implementar lógica de breakout em H4
    // Para agora, placeholder
    return "NONE";  // ou "HIGH", "LOW"
}


string ValidateM15(string sweep_type) {
    // Validar se M15 confirma o sweep
    if (sweep_type == "NONE") return "NONE";
    // Implementar lógica
    return "STRONG";  // ou "WEAK", "NONE"
}


string AnalyzeMomentum() {
    // Verificar se aceleração está reduzindo
    double macd_curr = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 0);
    double macd_prev = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 1);
    double macd_prev2 = iMACD(_Symbol, PERIOD_M15, 12, 26, 9, PRICE_CLOSE, MODE_MAIN, 2);
    
    if (MathAbs(macd_curr - macd_prev) < MathAbs(macd_prev - macd_prev2)) {
        return "REDUCING";
    } else if (MathAbs(macd_curr - macd_prev) > MathAbs(macd_prev - macd_prev2)) {
        return "INCREASING";
    } else {
        return "STABLE";
    }
}


// === FLOW E REGIME ===

double CalculateFlowScore() {
    // Implementar lógica de flow
    // Score -1.0 a 1.0
    double close = Close[0];
    double open = Open[0];
    return (close > open) ? 0.5 : -0.5;
}


string DetectRegime() {
    double sma50 = iMA(_Symbol, PERIOD_M15, 50, 0, MODE_SMA, PRICE_CLOSE, 0);
    double sma200 = iMA(_Symbol, PERIOD_M15, 200, 0, MODE_SMA, PRICE_CLOSE, 0);
    
    if (sma50 > sma200 && Close[0] > sma50) {
        return "UPTREND";
    } else if (sma50 < sma200 && Close[0] < sma50) {
        return "DOWNTREND";
    } else {
        return "SIDEWAYS";
    }
}


double CalculateVolatility(int period) {
    // Volatilidade realizada
    double sum_sq = 0;
    for (int i = 0; i < period; i++) {
        double ret = (Close[i] - Close[i+1]) / Close[i+1];
        sum_sq += ret * ret;
    }
    return MathSqrt(sum_sq / period);
}


double CalculateExpectedMove() {
    // Expected move estimado
    double atr = iATR(_Symbol, PERIOD_M15, 14, 0);
    return atr / Close[0];
}


// === MONTAR JSON ===

string BuildJSON(
    string m15_trend, string h4_trend, bool is_aligned, double alignment_score,
    string h4_sweep_type, string m15_confirmation, string momentum_trend,
    double flow_score, string regime, double &indicators[]
) {
    
    string json = "{";
    json += "\"symbol\":\"" + _Symbol + "\",";
    json += "\"timeframe\":\"M15\",";
    json += "\"datetime\":\"" + TimeToString(TimeCurrent(), TIME_DATE|TIME_MINUTES) + "\",";
    json += "\"open\":" + DoubleToString(Open[0], 5) + ",";
    json += "\"high\":" + DoubleToString(High[0], 5) + ",";
    json += "\"low\":" + DoubleToString(Low[0], 5) + ",";
    json += "\"close\":" + DoubleToString(Close[0], 5) + ",";
    json += "\"volume\":" + IntegerToString((int)Volume[0]) + ",";
    
    json += "\"sma_20\":" + DoubleToString(indicators[0], 5) + ",";
    json += "\"sma_50\":" + DoubleToString(indicators[1], 5) + ",";
    json += "\"sma_200\":" + DoubleToString(indicators[2], 5) + ",";
    json += "\"ema_12\":" + DoubleToString(indicators[3], 5) + ",";
    json += "\"ema_26\":" + DoubleToString(indicators[4], 5) + ",";
    json += "\"rsi_14\":" + DoubleToString(indicators[5], 1) + ",";
    json += "\"atr_pct\":" + DoubleToString(indicators[6], 4) + ",";
    
    json += "\"bb_upper\":" + DoubleToString(indicators[7], 5) + ",";
    json += "\"bb_lower\":" + DoubleToString(indicators[8], 5) + ",";
    json += "\"bb_position\":" + DoubleToString(indicators[9], 2) + ",";
    
    json += "\"macd_line\":" + DoubleToString(indicators[10], 6) + ",";
    json += "\"macd_signal\":" + DoubleToString(indicators[11], 6) + ",";
    json += "\"macd_hist\":" + DoubleToString(indicators[12], 6) + ",";
    
    json += "\"stoch_k\":" + DoubleToString(indicators[13], 1) + ",";
    json += "\"stoch_d\":" + DoubleToString(indicators[14], 1) + ",";
    
    json += "\"ret_1\":" + DoubleToString(indicators[15], 6) + ",";
    json += "\"ret_3\":" + DoubleToString(indicators[16], 6) + ",";
    json += "\"ret_5\":" + DoubleToString(indicators[17], 6) + ",";
    
    json += "\"realized_vol\":" + DoubleToString(indicators[18], 4) + ",";
    json += "\"expected_move\":" + DoubleToString(indicators[19], 5) + ",";
    
    json += "\"m15_trend\":\"" + m15_trend + "\",";
    json += "\"h4_trend\":\"" + h4_trend + "\",";
    json += "\"is_aligned\":" + (is_aligned ? "true" : "false") + ",";
    json += "\"alignment_score\":" + DoubleToString(alignment_score, 2) + ",";
    
    json += "\"h4_sweep_type\":\"" + h4_sweep_type + "\",";
    json += "\"m15_confirmation\":\"" + m15_confirmation + "\",";
    json += "\"momentum_trend\":\"" + momentum_trend + "\",";
    
    json += "\"flow_score\":" + DoubleToString(flow_score, 2) + ",";
    json += "\"regime\":\"" + regime + "\"";
    
    json += "}";
    
    return json;
}


// === ENVIAR PARA PYTHON ===

string SendToPython(string json) {
    string url = "http://localhost:9998/ml5/predict";
    char response_data[];
    int timeout = 2000; // 2 segundos
    
    int res = WebRequest("POST",
                        url,
                        NULL,
                        timeout,
                        json,
                        response_data);
    
    if (res == -1) {
        if (debugMode) {
            Print("❌ Erro ao conectar com Python: " + IntegerToString(GetLastError()));
        }
        return "";
    }
    
    string response = CharArrayToString(response_data);
    return response;
}


// === PROCESSAR RESPOSTA ===

void ProcessResponse(string response) {
    // Parse JSON response
    // {"decision": "BUY", "confidence": 0.85, ...}
    
    string decision = "HOLD";
    double confidence = 0.0;
    
    // Extrair decisão
    int pos_decision = StringFind(response, "\"decision\":\"");
    if (pos_decision >= 0) {
        pos_decision += 12;
        int end = StringFind(response, "\"", pos_decision);
        decision = StringSubstr(response, pos_decision, end - pos_decision);
    }
    
    // Extrair confiança
    int pos_conf = StringFind(response, "\"confidence\":");
    if (pos_conf >= 0) {
        pos_conf += 13;
        int end = StringFind(response, ",", pos_conf);
        if (end < 0) end = StringFind(response, "}", pos_conf);
        string conf_str = StringSubstr(response, pos_conf, end - pos_conf);
        confidence = StringToDouble(conf_str);
    }
    
    if (debugMode) {
        Print("📥 Resposta: Decisão=" + decision + " Confiança=" + DoubleToString(confidence, 2));
    }
    
    // Validar confiança
    if (confidence < confidenceThreshold) {
        if (debugMode) {
            Print("⚠️ Confiança baixa (" + DoubleToString(confidence, 2) + " < " + DoubleToString(confidenceThreshold, 2) + "), ignorando");
        }
        return;
    }
    
    // Executar trade
    if (!enableTrading) return;
    
    if (decision == "BUY") {
        ExecuteBuyOrder();
    } else if (decision == "SELL") {
        ExecuteSellOrder();
    } else {
        if (debugMode) Print("➜ HOLD - Sem ação");
    }
}


void ExecuteBuyOrder() {
    // Executar ordem de compra
    if (debugMode) Print("✅ Executando BUY");
    
    // Implementar lógica de ordem
    // ticket = OrderSend(...)
}


void ExecuteSellOrder() {
    // Executar ordem de venda
    if (debugMode) Print("✅ Executando SELL");
    
    // Implementar lógica de ordem
    // ticket = OrderSend(...)
}
