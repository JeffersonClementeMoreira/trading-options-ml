#!/usr/bin/env python3
"""
Exemplo de uso dos modelos Ensemble em produção
Carrega os modelos treinados e faz predições em tempo real
"""

import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler

class EnsemblePredictor:
    def __init__(self, symbol):
        self.symbol = symbol
        self.model = None
        self.scaler = None
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self._load_models()
    
    def _load_models(self):
        """Carrega modelo ensemble e scaler"""
        model_file = f"/home/ubuntu/pessoal/options/models/ml_ensemble_{self.symbol.lower()}.pkl"
        scaler_file = f"/home/ubuntu/pessoal/options/models/ml_scaler_{self.symbol.lower()}.pkl"
        
        try:
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
            print(f"✅ Modelo {self.symbol} carregado")
        except FileNotFoundError as e:
            print(f"❌ Erro ao carregar modelo: {e}")
            raise
    
    def predict(self, indicators_dict):
        """
        Faz predição com base em um dicionário de indicadores
        
        Exemplo:
            indicators = {
                'rsi': 65.5,
                'sma20': 1.1650,
                'sma50': 1.1645,
                'macd': 0.0002,
                'atr': 0.0015,
                'momentum': 0.0003,
                'price_above_sma20': 1,
                'price_above_sma50': 1,
                'rsi_oversold': 0,
                'rsi_overbought': 0,
                'macd_positive': 1,
                'momentum_positive': 1
            }
            
            direction, confidence = predictor.predict(indicators)
        """
        
        # Converte dicionário para array na ordem correta dos features
        features = np.array([[indicators_dict[name] for name in self.feature_names]])
        
        # Normaliza (escalador foi treinado)
        features_scaled = self.scaler.transform(features)
        
        # Predição
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        direction = 'UP' if prediction == 1 else 'DOWN'
        confidence = probabilities[prediction]
        
        return direction, confidence
    
    def predict_batch(self, indicators_list):
        """
        Faz múltiplas predições de uma vez
        
        Exemplo:
            indicators_list = [
                {'rsi': 65, ...},
                {'rsi': 45, ...},
            ]
        """
        
        features = np.array([[ind[name] for name in self.feature_names] for ind in indicators_list])
        features_scaled = self.scaler.transform(features)
        
        predictions = self.model.predict(features_scaled)
        probabilities = self.model.predict_proba(features_scaled)
        
        results = []
        for i in range(len(indicators_list)):
            direction = 'UP' if predictions[i] == 1 else 'DOWN'
            confidence = probabilities[i][predictions[i]]
            results.append({
                'direction': direction,
                'confidence': confidence
            })
        
        return results

def main():
    print("\n" + "="*80)
    print("🚀 EXEMPLO: USO DO ENSEMBLE EM PRODUÇÃO")
    print("="*80 + "\n")
    
    # Inicializa preditores
    eurusd_pred = EnsemblePredictor('EURUSD')
    gbpusd_pred = EnsemblePredictor('GBPUSD')
    
    # Exemplo 1: Predição simples para EURUSD
    print("Exemplo 1: Predição para EURUSD")
    print("-" * 80)
    
    eurusd_indicators = {
        'rsi': 65.5,              # RSI acima de 50 (bullish)
        'sma20': 1.16520,         # Preço acima das médias móveis
        'sma50': 1.16450,
        'macd': 0.00025,          # MACD positivo
        'atr': 0.00150,           # Volatilidade
        'momentum': 0.00035,      # Momentum positivo
        'price_above_sma20': 1,   # Preço > SMA20
        'price_above_sma50': 1,   # Preço > SMA50
        'rsi_oversold': 0,        # Não oversold
        'rsi_overbought': 0,      # Não overbought
        'macd_positive': 1,       # MACD positivo
        'momentum_positive': 1    # Momentum positivo
    }
    
    direction, confidence = eurusd_pred.predict(eurusd_indicators)
    
    print(f"""
    Indicadores:
      RSI: {eurusd_indicators['rsi']}
      SMA20: {eurusd_indicators['sma20']}
      SMA50: {eurusd_indicators['sma50']}
      MACD: {eurusd_indicators['macd']}
      ATR: {eurusd_indicators['atr']}
    
    ✅ Predição: {direction}
    📊 Confiança: {confidence*100:.2f}%
    
    Interpretação:
      - {direction}: Expectativa de movimento para cima
      - Confiança {confidence*100:.2f}%: {'FORTE' if confidence > 0.75 else 'MODERADA' if confidence > 0.60 else 'FRACA'}
    """)
    
    # Exemplo 2: Predição com cenário bearish
    print("\n" + "="*80)
    print("Exemplo 2: Predição para EURUSD (cenário bearish)")
    print("-" * 80)
    
    eurusd_bearish = {
        'rsi': 35.2,              # RSI baixo (bearish)
        'sma20': 1.16400,         # Preço abaixo das médias
        'sma50': 1.16480,
        'macd': -0.00015,         # MACD negativo
        'atr': 0.00150,
        'momentum': -0.00025,     # Momentum negativo
        'price_above_sma20': 0,   # Preço < SMA20
        'price_above_sma50': 0,   # Preço < SMA50
        'rsi_oversold': 1,        # Oversold detectado
        'rsi_overbought': 0,
        'macd_positive': 0,       # MACD negativo
        'momentum_positive': 0    # Momentum negativo
    }
    
    direction, confidence = eurusd_pred.predict(eurusd_bearish)
    
    print(f"""
    Indicadores:
      RSI: {eurusd_bearish['rsi']}
      SMA20: {eurusd_bearish['sma20']}
      SMA50: {eurusd_bearish['sma50']}
      MACD: {eurusd_bearish['macd']}
      ATR: {eurusd_bearish['atr']}
    
    ✅ Predição: {direction}
    📊 Confiança: {confidence*100:.2f}%
    """)
    
    # Exemplo 3: GBPUSD
    print("\n" + "="*80)
    print("Exemplo 3: Predição para GBPUSD")
    print("-" * 80)
    
    gbpusd_indicators = {
        'rsi': 58.0,
        'sma20': 1.26520,
        'sma50': 1.26450,
        'macd': 0.00018,
        'atr': 0.00160,
        'momentum': 0.00028,
        'price_above_sma20': 1,
        'price_above_sma50': 1,
        'rsi_oversold': 0,
        'rsi_overbought': 0,
        'macd_positive': 1,
        'momentum_positive': 1
    }
    
    direction, confidence = gbpusd_pred.predict(gbpusd_indicators)
    
    print(f"""
    Indicadores:
      RSI: {gbpusd_indicators['rsi']}
      SMA20: {gbpusd_indicators['sma20']}
      SMA50: {gbpusd_indicators['sma50']}
    
    ✅ Predição: {direction}
    📊 Confiança: {confidence*100:.2f}%
    """)
    
    # Regra de uso para trading
    print("\n" + "="*80)
    print("📋 REGRA DE CONFIANÇA PARA TRADING")
    print("="*80 + "\n")
    
    test_confidences = [0.52, 0.65, 0.78, 0.92]
    
    for conf in test_confidences:
        if conf > 0.80:
            action = "✅ EXECUTE FULL - Confiança alta, operação confirmada"
        elif conf > 0.70:
            action = "⚠️  EXECUTE 75% - Confiança moderada-alta, reduzir posição"
        elif conf > 0.60:
            action = "⚠️  EXECUTE 50% - Confiança moderada, micro-posição"
        else:
            action = "❌ SKIP - Confiança baixa, aguardar próximo sinal"
        
        print(f"  Confiança {conf*100:.0f}%: {action}")
    
    print("\n" + "="*80)
    print("✅ PRONTO PARA USAR EM PRODUÇÃO")
    print("="*80 + "\n")

if __name__ == '__main__':
    main()
