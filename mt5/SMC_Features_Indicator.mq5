//+------------------------------------------------------------------+
//|                           SMC Features Indicator                  |
//|                  for MetaTrader 5 / XGBoost Integration            |
//|                                                                    |
//| Calcula 25+ features contínuas baseadas em SMC                     |
//| Exporta para arquivo CSV que o Python lê                          |
//+------------------------------------------------------------------+

#property copyright "Trading System"
#property link "https://example.com"
#property version "1.00"
#property strict
#property indicator_chart_window

#include <Math/Stat/Normal.mqh>

// ===== CONFIGURAÇÕES =====
#define EXPORT_FILE "smc_features.csv"
#define EXTREMES_LOOKBACK 100
#define FEATURE_WINDOW 20

// ===== ESTRUTURAS =====

struct SMCFeatures {
    double dist_top_liquidity;
    double dist_bottom_liquidity;
    double sweep_top_count;
    double sweep_bottom_count;
    double sweep_imbalance;
    double bos_bull_count;
    double bos_bear_count;
    double bos_ratio;
    double candles_since_choch;
    double choch_type;
    double bull_fvg_count;
    double bear_fvg_count;
    double fvg_pressure;
    double mean_displacement;
    double max_displacement;
    double displacement_efficiency;
    double premium_position;
    double premium_discount_score;
    double atr_compression_ratio;
    double vol_regime;
    double liquidity_void_score;
    double stop_hunt_prob;
    double trend_duration;
    double range_duration;
    double regime_strength;
};

struct Extreme {
    datetime datetime;
    double price;
    int type; // 0 = top, 1 = bottom
};

// ===== VARIÁVEIS GLOBAIS =====

Extreme extremes[];
int extremes_count = 0;
double atr_buffer[];
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
//| Função: Calcular Distance to Liquidity                           |
//+------------------------------------------------------------------+

void CalculateDistanceToLiquidity(SMCFeatures &features, int shift) {
    double current_price = Close[shift];
    double atr = CalculateATR(14, shift);
    
    if (atr < 0.0001) atr = 0.0001;
    
    features.dist_top_liquidity = -1;
    features.dist_bottom_liquidity = -1;
    
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
    
    // Se não encontrou, colocar valor default
    if (features.dist_top_liquidity < 0) features.dist_top_liquidity = 0;
    if (features.dist_bottom_liquidity < 0) features.dist_bottom_liquidity = 0;
}

//+------------------------------------------------------------------+
//| Função: Calcular Sweep Pressure                                 |
//+------------------------------------------------------------------+

void CalculateSweepPressure(SMCFeatures &features, int shift) {
    features.sweep_top_count = 0;
    features.sweep_bottom_count = 0;
    features.sweep_imbalance = 0;
    
    int window = FEATURE_WINDOW;
    int count_top = 0;
    int count_bottom = 0;
    
    // Contar sweeps nos últimos N candles
    for (int i = 0; i < window && shift + i < Bars; i++) {
        for (int j = extremes_count - 1; j >= 0; j--) {
            if (extremes[j].datetime >= Time[shift + i] && 
                extremes[j].datetime <= Time[shift + i - 1]) {
                
                if (extremes[j].type == 0) count_top++;
                else count_bottom++;
            }
        }
    }
    
    features.sweep_top_count = count_top;
    features.sweep_bottom_count = count_bottom;
    
    int total = count_top + count_bottom;
    if (total > 0) {
        features.sweep_imbalance = (double)(count_top - count_bottom) / total;
    }
}

//+------------------------------------------------------------------+
//| Função: Calcular Premium/Discount                               |
//+------------------------------------------------------------------+

void CalculatePremiumDiscount(SMCFeatures &features, int shift) {
    int window = 20;
    double highest = High[shift];
    double lowest = Low[shift];
    
    for (int i = 0; i < window && shift + i < Bars; i++) {
        highest = MathMax(highest, High[shift + i]);
        lowest = MathMin(lowest, Low[shift + i]);
    }
    
    double range = highest - lowest;
    
    if (range > 0) {
        features.premium_position = (Close[shift] - lowest) / range;
        features.premium_discount_score = features.premium_position - 0.5;
    } else {
        features.premium_position = 0.5;
        features.premium_discount_score = 0.0;
    }
}

//+------------------------------------------------------------------+
//| Função: Calcular ATR Compression                                |
//+------------------------------------------------------------------+

void CalculateATRCompression(SMCFeatures &features, int shift) {
    int fast = 5;
    int slow = 50;
    
    double fast_atr = CalculateATR(fast, shift);
    double slow_atr = CalculateATR(slow, shift);
    
    if (slow_atr > 0) {
        features.atr_compression_ratio = fast_atr / slow_atr;
    } else {
        features.atr_compression_ratio = 1.0;
    }
    
    // Vol regime: 1 = normal, 0 = compressed
    features.vol_regime = (features.atr_compression_ratio > 0.7) ? 1 : 0;
}

//+------------------------------------------------------------------+
//| Função: Calcular Displacement Score                            |
//+------------------------------------------------------------------+

void CalculateDisplacementScore(SMCFeatures &features, int shift) {
    int window = 20;
    double total_displacement = 0;
    double max_displacement = 0;
    
    for (int i = 0; i < window && shift + i < Bars; i++) {
        double range = High[shift + i] - Low[shift + i];
        double displacement = MathAbs(Close[shift + i] - Open[shift + i]);
        
        if (range > 0.0001) {
            double efficiency = displacement / range;
            total_displacement += efficiency;
            max_displacement = MathMax(max_displacement, efficiency);
        }
    }
    
    features.mean_displacement = total_displacement / window;
    features.max_displacement = max_displacement;
    features.displacement_efficiency = (High[shift] - Low[shift] > 0.0001) ? 
        MathAbs(Close[shift] - Open[shift]) / (High[shift] - Low[shift]) : 0;
}

//+------------------------------------------------------------------+
//| Função: Calcular FVG (Fair Value Gap)                           |
//+------------------------------------------------------------------+

void CalculateFVG(SMCFeatures &features, int shift) {
    features.bull_fvg_count = 0;
    features.bear_fvg_count = 0;
    features.fvg_pressure = 0;
    
    int window = 20;
    
    // Procurar FVGs nos últimos N candles
    for (int i = 0; i < window - 2 && shift + i < Bars; i++) {
        // Bull FVG: Low[i+2] > High[i]
        if (Low[shift + i + 2] > High[shift + i]) {
            features.bull_fvg_count++;
        }
        // Bear FVG: High[i+2] < Low[i]
        if (High[shift + i + 2] < Low[shift + i]) {
            features.bear_fvg_count++;
        }
    }
    
    int total = (int)(features.bull_fvg_count + features.bear_fvg_count);
    if (total > 0) {
        features.fvg_pressure = (features.bull_fvg_count - features.bear_fvg_count) / total;
    }
}

//+------------------------------------------------------------------+
//| Função: Gerar todas as features SMC                             |
//+------------------------------------------------------------------+

void GenerateSMCFeatures(SMCFeatures &features, int shift) {
    // Detecção de extremes deve ser feita uma vez
    DetectExtremes();
    
    // Calcular cada feature
    CalculateDistanceToLiquidity(features, shift);
    CalculateSweepPressure(features, shift);
    CalculatePremiumDiscount(features, shift);
    CalculateATRCompression(features, shift);
    CalculateDisplacementScore(features, shift);
    CalculateFVG(features, shift);
    
    // Features não implementadas (default 0)
    features.bos_bull_count = 0;
    features.bos_bear_count = 0;
    features.bos_ratio = 0;
    features.candles_since_choch = 0;
    features.choch_type = 0;
    features.liquidity_void_score = 0;
    features.stop_hunt_prob = 0;
    features.trend_duration = 0;
    features.range_duration = 0;
    features.regime_strength = 0;
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
        
        // Cabeçalho
        FileWrite(file_handle, 
            "datetime\tdist_top_liquidity\tdist_bottom_liquidity\t"
            "sweep_top_count\tsweep_bottom_count\tsweep_imbalance\t"
            "bos_bull_count\tbos_bear_count\tbos_ratio\t"
            "candles_since_choch\tchoch_type\t"
            "bull_fvg_count\tbear_fvg_count\tfvg_pressure\t"
            "mean_displacement\tmax_displacement\tdisplacement_efficiency\t"
            "premium_position\tpremium_discount_score\t"
            "atr_compression_ratio\tvol_regime\t"
            "liquidity_void_score\tstop_hunt_prob\t"
            "trend_duration\trange_duration\tregime_strength");
    }
    
    // Gerar features para o candle atual
    SMCFeatures features;
    GenerateSMCFeatures(features, 0);
    
    // Escrever linha
    string line = StringFormat(
        "%s\t%.5f\t%.5f\t%.0f\t%.0f\t%.5f\t%.0f\t%.0f\t%.5f\t%.0f\t%.0f\t"
        "%.0f\t%.0f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.5f\t%.0f\t"
        "%.5f\t%.5f\t%.0f\t%.0f\t%.5f",
        
        TimeToString(Time[0]),
        features.dist_top_liquidity,
        features.dist_bottom_liquidity,
        features.sweep_top_count,
        features.sweep_bottom_count,
        features.sweep_imbalance,
        features.bos_bull_count,
        features.bos_bear_count,
        features.bos_ratio,
        features.candles_since_choch,
        features.choch_type,
        features.bull_fvg_count,
        features.bear_fvg_count,
        features.fvg_pressure,
        features.mean_displacement,
        features.max_displacement,
        features.displacement_efficiency,
        features.premium_position,
        features.premium_discount_score,
        features.atr_compression_ratio,
        features.vol_regime,
        features.liquidity_void_score,
        features.stop_hunt_prob,
        features.trend_duration,
        features.range_duration,
        features.regime_strength
    );
    
    FileWrite(file_handle, line);
    FileClose(file_handle);
}

//+------------------------------------------------------------------+
//| Função: OnInit                                                   |
//+------------------------------------------------------------------+

int OnInit() {
    SetIndexBuffer(0, atr_buffer);
    
    Print("SMC Features Indicator Started for: ", Symbol(), " ", Period());
    
    return INIT_SUCCEEDED;
}

//+------------------------------------------------------------------+
//| Função: OnDeinit                                                 |
//+------------------------------------------------------------------+

void OnDeinit(const int reason) {
    Print("SMC Features Indicator Stopped");
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
