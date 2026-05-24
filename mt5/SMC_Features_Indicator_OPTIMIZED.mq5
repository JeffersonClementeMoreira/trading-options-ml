//+------------------------------------------------------------------+
//|                    SMC_Features_Indicator_OPTIMIZED.mq5           |
//|                 Version 2: TOP 5 Features Only                    |
//|                                                                    |
//| Otimizado para exportar APENAS as features com melhor impacto:    |
//|  1. dist_top_liquidity       (6.23%)                              |
//|  2. dist_bottom_liquidity    (5.80%)                              |
//|  3. vol_regime               (5.51%)                              |
//|  4. premium_discount_score   (4.73%)                              |
//|  5. range_duration           (4.66%)                              |
//|                                                                    |
//| Total = 27% da decisão do XGBoost                                 |
//| Arquivo: smc_features_optimized.csv                               |
//+------------------------------------------------------------------+

#property copyright "Trading System"
#property version "2.00"
#property strict
#property indicator_chart_window

// ===== CONFIGURAÇÕES =====
#define EXPORT_FILE "smc_features_optimized.csv"
#define FEATURE_WINDOW 20

// ===== ESTRUTURA =====

struct OptimizedSMCFeatures {
    double dist_top_liquidity;         // 6.23% importance
    double dist_bottom_liquidity;      // 5.80% importance
    double vol_regime;                 // 5.51% importance (0 ou 1)
    double premium_discount_score;     // 4.73% importance
    double range_duration;             // 4.66% importance
};

struct Extreme {
    datetime datetime;
    double price;
    int type; // 0 = top, 1 = bottom
};

// ===== VARIÁVEIS GLOBAIS =====

Extreme extremes[];
int extremes_count = 0;
datetime last_export = 0;

//+------------------------------------------------------------------+
//| Função: Calcular ATR                                             |
//+------------------------------------------------------------------+

double CalculateATR(int period, int shift) {
    double tr = 0;
    double atr = 0;
    
    for (int i = shift; i < shift + period; i++) {
        double hl = High[i] - Low[i];
        double hc = MathAbs(High[i] - Close[i+1]);
        double lc = MathAbs(Low[i] - Close[i+1]);
        tr = MathMax(hl, MathMax(hc, lc));
        
        if (i == shift) {
            atr = tr;
        } else {
            atr = (atr * (period - 1) + tr) / period;
        }
    }
    return atr;
}

//+------------------------------------------------------------------+
//| Função: Detectar Extremes (Tops e Bottoms)                      |
//+------------------------------------------------------------------+

void DetectExtremes() {
    if (Bars < 10) return;
    
    extremes_count = 0;
    ArrayResize(extremes, 0);
    
    // Detectar tops e bottoms usando Zig-Zag lógica
    for (int i = 2; i < Bars - 1; i++) {
        // Top: High > anterior e > próximo
        if (High[i] > High[i+1] && High[i] > High[i-1]) {
            if (extremes_count == 0 || extremes[extremes_count-1].type != 0 || 
                High[i] > extremes[extremes_count-1].price) {
                
                ArrayResize(extremes, extremes_count + 1);
                extremes[extremes_count].datetime = Time[i];
                extremes[extremes_count].price = High[i];
                extremes[extremes_count].type = 0; // TOP
                extremes_count++;
            }
        }
        
        // Bottom: Low < anterior e < próximo
        if (Low[i] < Low[i+1] && Low[i] < Low[i-1]) {
            if (extremes_count == 0 || extremes[extremes_count-1].type != 1 || 
                Low[i] < extremes[extremes_count-1].price) {
                
                ArrayResize(extremes, extremes_count + 1);
                extremes[extremes_count].datetime = Time[i];
                extremes[extremes_count].price = Low[i];
                extremes[extremes_count].type = 1; // BOTTOM
                extremes_count++;
            }
        }
    }
}

//+------------------------------------------------------------------+
//| FEATURE 1: Distance to Liquidity                                |
//+------------------------------------------------------------------+

void CalculateDistanceToLiquidity(OptimizedSMCFeatures &features, int shift) {
    double current_price = Close[shift];
    double atr = CalculateATR(14, shift);
    
    if (atr < 0.0001) atr = 0.0001;
    
    features.dist_top_liquidity = 0;
    features.dist_bottom_liquidity = 0;
    
    // Procurar próximo top (acima do preço atual)
    for (int i = extremes_count - 1; i >= 0; i--) {
        if (extremes[i].type == 0 && extremes[i].price > current_price) {
            features.dist_top_liquidity = (extremes[i].price - current_price) / atr;
            break;
        }
    }
    
    // Procurar próximo bottom (abaixo do preço atual)
    for (int i = extremes_count - 1; i >= 0; i--) {
        if (extremes[i].type == 1 && extremes[i].price < current_price) {
            features.dist_bottom_liquidity = (current_price - extremes[i].price) / atr;
            break;
        }
    }
}

//+------------------------------------------------------------------+
//| FEATURE 2: Vol Regime (Compressed or Normal?)                   |
//+------------------------------------------------------------------+

void CalculateVolRegime(OptimizedSMCFeatures &features, int shift) {
    int fast = 5;
    int slow = 50;
    
    double fast_atr = CalculateATR(fast, shift);
    double slow_atr = CalculateATR(slow, shift);
    
    if (slow_atr > 0) {
        double compression_ratio = fast_atr / slow_atr;
        // Vol regime: 1 = normal/expanded, 0 = compressed
        features.vol_regime = (compression_ratio > 0.7) ? 1.0 : 0.0;
    } else {
        features.vol_regime = 1.0;
    }
}

//+------------------------------------------------------------------+
//| FEATURE 3: Premium / Discount Position                          |
//+------------------------------------------------------------------+

void CalculatePremiumDiscount(OptimizedSMCFeatures &features, int shift) {
    int window = 20;
    double highest = High[shift];
    double lowest = Low[shift];
    
    for (int i = 0; i < window && shift + i < Bars; i++) {
        highest = MathMax(highest, High[shift + i]);
        lowest = MathMin(lowest, Low[shift + i]);
    }
    
    double range = highest - lowest;
    
    if (range > 0) {
        double premium_position = (Close[shift] - lowest) / range;
        features.premium_discount_score = premium_position - 0.5;
    } else {
        features.premium_discount_score = 0.0;
    }
}

//+------------------------------------------------------------------+
//| FEATURE 4: Range Duration (Há quantos candles em range)        |
//+------------------------------------------------------------------+

void CalculateRangeDuration(OptimizedSMCFeatures &features, int shift) {
    int window = 50;
    
    // Detectar se estamos em range (HHs e LLs não quebrando)
    bool higher_high = true;
    bool lower_low = true;
    
    int duration = 0;
    
    for (int i = 0; i < window - 1 && shift + i < Bars - 1; i++) {
        double prev_high = High[shift + i];
        double next_high = High[shift + i + 1];
        double prev_low = Low[shift + i];
        double next_low = Low[shift + i + 1];
        
        // Se break HH ou break LL, range terminou
        if (next_high <= prev_high && next_low >= prev_low) {
            duration++;
        } else {
            break;
        }
    }
    
    features.range_duration = (double)duration;
}

//+------------------------------------------------------------------+
//| Função: Gerar todas as features otimizadas                      |
//+------------------------------------------------------------------+

void GenerateOptimizedFeatures(OptimizedSMCFeatures &features, int shift) {
    // Detectar extremes uma vez
    DetectExtremes();
    
    // Calcular cada feature IMPORTANTE
    CalculateDistanceToLiquidity(features, shift);      // 6.23 + 5.80 = 12.03%
    CalculateVolRegime(features, shift);                // 5.51%
    CalculatePremiumDiscount(features, shift);          // 4.73%
    CalculateRangeDuration(features, shift);            // 4.66%
    
    // Total: 27% do poder preditivo com APENAS 5 features
}

//+------------------------------------------------------------------+
//| Função: Exportar Features para CSV                              |
//+------------------------------------------------------------------+

void ExportFeaturesToCSV() {
    // Exportar apenas uma vez por candle
    if (Time[0] == last_export) return;
    last_export = Time[0];
    
    // Abrir arquivo para append
    int file_handle = FileOpen(EXPORT_FILE, FILE_READ | FILE_WRITE | FILE_CSV, '\t');
    
    if (file_handle == INVALID_HANDLE) {
        // Criar novo arquivo com cabeçalho
        file_handle = FileOpen(EXPORT_FILE, FILE_WRITE | FILE_CSV, '\t');
        
        // Cabeçalho: APENAS 5 features importantes
        FileWrite(file_handle, 
            "datetime\tdist_top_liquidity\tdist_bottom_liquidity\t"
            "vol_regime\tpremium_discount_score\trange_duration");
    }
    
    // Gerar features para o candle atual
    OptimizedSMCFeatures features;
    GenerateOptimizedFeatures(features, 0);
    
    // Escrever linha COM APENAS 5 variáveis
    string line = StringFormat(
        "%s\t%.5f\t%.5f\t%.0f\t%.5f\t%.0f",
        
        TimeToString(Time[0]),
        features.dist_top_liquidity,
        features.dist_bottom_liquidity,
        features.vol_regime,
        features.premium_discount_score,
        features.range_duration
    );
    
    FileWrite(file_handle, line);
    FileClose(file_handle);
}

//+------------------------------------------------------------------+
//| Função: OnInit                                                   |
//+------------------------------------------------------------------+

int OnInit() {
    Print("SMC Features Indicator OPTIMIZED (TOP 5 only) Started");
    Print("Symbol: ", Symbol(), " | Period: ", Period());
    Print("Exporting to: ", EXPORT_FILE);
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Função: OnDeinit                                                 |
//+------------------------------------------------------------------+

void OnDeinit(const int reason) {
    Print("SMC Features Indicator OPTIMIZED Stopped");
}

//+------------------------------------------------------------------+
//| Função: OnTick                                                   |
//+------------------------------------------------------------------+

int OnTick() {
    // Exportar features a cada novo candle
    ExportFeaturesToCSV();
    
    return 0;
}

//+------------------------------------------------------------------+
