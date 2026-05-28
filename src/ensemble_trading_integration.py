#!/usr/bin/env python3
"""
Integração dos modelos Ensemble com código de trading realtime
Este script demonstra como usar os modelos em uma estratégia de trading
"""

import pickle
import numpy as np
from dataclasses import dataclass
from enum import Enum

class TradeSignal(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"

@dataclass
class Signal:
    direction: str
    confidence: float
    action: TradeSignal
    position_size: float  # Porcentagem do capital (0.0 a 1.0)
    reason: str

class EnsembleTrader:
    """
    Classe principal para integração com sistema de trading realtime
    """
    
    def __init__(self, symbol, confidence_threshold=0.60):
        """
        Inicializa trader com modelos ensemble
        
        Args:
            symbol: 'EURUSD' ou 'GBPUSD'
            confidence_threshold: Confiança mínima para executar (padrão 60%)
        """
        self.symbol = symbol
        self.confidence_threshold = confidence_threshold
        self.model = None
        self.scaler = None
        self.feature_names = ['rsi', 'sma20', 'sma50', 'macd', 'atr', 'momentum',
                             'price_above_sma20', 'price_above_sma50',
                             'rsi_oversold', 'rsi_overbought', 'macd_positive', 'momentum_positive']
        self._load_models()
    
    def _load_models(self):
        """Carrega modelos ensemble"""
        try:
            model_file = f"/home/ubuntu/pessoal/options/models/ml_ensemble_{self.symbol.lower()}.pkl"
            scaler_file = f"/home/ubuntu/pessoal/options/models/ml_scaler_{self.symbol.lower()}.pkl"
            
            with open(model_file, 'rb') as f:
                self.model = pickle.load(f)
            with open(scaler_file, 'rb') as f:
                self.scaler = pickle.load(f)
        except FileNotFoundError as e:
            print(f"❌ Erro ao carregar modelos: {e}")
            raise
    
    def get_signal(self, indicators):
        """
        Gera sinal de trading baseado nos indicadores
        
        Args:
            indicators: Dicionário com 12 indicadores calculados
        
        Returns:
            Signal: Objeto com direção, confiança, ação e tamanho da posição
        """
        
        # Prepara features
        features = np.array([[indicators[name] for name in self.feature_names]])
        features_scaled = self.scaler.transform(features)
        
        # Predição
        prediction = self.model.predict(features_scaled)[0]
        probabilities = self.model.predict_proba(features_scaled)[0]
        
        direction = 'UP' if prediction == 1 else 'DOWN'
        confidence = float(probabilities[prediction])
        
        # Gera ação baseado em confiança
        if confidence < self.confidence_threshold:
            action = TradeSignal.HOLD
            position_size = 0.0
            reason = f"Confiança baixa ({confidence*100:.1f}% < {self.confidence_threshold*100:.1f}%)"
        
        elif direction == 'UP':
            action = TradeSignal.BUY
            # Tamanho da posição baseado em confiança
            if confidence > 0.80:
                position_size = 1.0
                reason = "Confiança alta: BUY FULL"
            elif confidence > 0.70:
                position_size = 0.75
                reason = "Confiança moderada-alta: BUY 75%"
            else:
                position_size = 0.50
                reason = "Confiança moderada: BUY 50% (micro)"
        
        else:  # DOWN
            action = TradeSignal.SELL
            if confidence > 0.80:
                position_size = 1.0
                reason = "Confiança alta: SELL FULL"
            elif confidence > 0.70:
                position_size = 0.75
                reason = "Confiança moderada-alta: SELL 75%"
            else:
                position_size = 0.50
                reason = "Confiança moderada: SELL 50% (micro)"
        
        return Signal(
            direction=direction,
            confidence=confidence,
            action=action,
            position_size=position_size,
            reason=reason
        )
    
    def get_multiple_signals(self, indicators_list):
        """Processa múltiplos candles de uma vez"""
        signals = []
        for indicators in indicators_list:
            signals.append(self.get_signal(indicators))
        return signals

def example_live_trading():
    """
    Exemplo de como usar em um loop de trading realtime
    """
    print("\n" + "="*80)
    print("🚀 EXEMPLO: INTEGRAÇÃO COM TRADING REALTIME")
    print("="*80 + "\n")
    
    # Inicializa traders para ambas moedas
    eurusd_trader = EnsembleTrader('EURUSD', confidence_threshold=0.60)
    gbpusd_trader = EnsembleTrader('GBPUSD', confidence_threshold=0.60)
    
    # Simulação de dados realtime (cada candle M15)
    print("📊 Simulando trading realtime (M15):\n")
    
    # Exemplo 1: EURUSD Bullish
    print("Candle 1: EURUSD - Cenário Bullish")
    print("-" * 80)
    
    eurusd_bullish = {
        'rsi': 72.5,
        'sma20': 1.16520,
        'sma50': 1.16450,
        'macd': 0.00035,
        'atr': 0.00160,
        'momentum': 0.00045,
        'price_above_sma20': 1,
        'price_above_sma50': 1,
        'rsi_oversold': 0,
        'rsi_overbought': 1,
        'macd_positive': 1,
        'momentum_positive': 1
    }
    
    signal = eurusd_trader.get_signal(eurusd_bullish)
    
    print(f"""
    Preço Atual: 1.1652
    RSI: {eurusd_bullish['rsi']} (OVERBOUGHT)
    Acima SMA20/50: Sim
    MACD: Positivo
    
    🔮 Predição: {signal.direction}
    📊 Confiança: {signal.confidence*100:.2f}%
    
    💰 AÇÃO: {signal.action.value}
    📈 Tamanho: {signal.position_size*100:.0f}% do capital
    💭 Razão: {signal.reason}
    """)
    
    # Exemplo 2: EURUSD Indeciso
    print("\n" + "="*80)
    print("Candle 2: EURUSD - Cenário Indeciso")
    print("-" * 80)
    
    eurusd_indeciso = {
        'rsi': 50.0,
        'sma20': 1.16505,
        'sma50': 1.16500,
        'macd': 0.00001,
        'atr': 0.00150,
        'momentum': 0.00001,
        'price_above_sma20': 1,
        'price_above_sma50': 1,
        'rsi_oversold': 0,
        'rsi_overbought': 0,
        'macd_positive': 1,
        'momentum_positive': 0
    }
    
    signal = eurusd_trader.get_signal(eurusd_indeciso)
    
    print(f"""
    Preço Atual: 1.16505
    RSI: {eurusd_indeciso['rsi']} (NEUTRO)
    Acima SMA20/50: Sim
    MACD: Quasi-zero
    
    🔮 Predição: {signal.direction}
    📊 Confiança: {signal.confidence*100:.2f}%
    
    💰 AÇÃO: {signal.action.value}
    📈 Tamanho: {signal.position_size*100:.0f}% do capital
    💭 Razão: {signal.reason}
    """)
    
    # Exemplo 3: GBPUSD Bearish
    print("\n" + "="*80)
    print("Candle 3: GBPUSD - Cenário Bearish")
    print("-" * 80)
    
    gbpusd_bearish = {
        'rsi': 25.5,
        'sma20': 1.26400,
        'sma50': 1.26480,
        'macd': -0.00045,
        'atr': 0.00180,
        'momentum': -0.00055,
        'price_above_sma20': 0,
        'price_above_sma50': 0,
        'rsi_oversold': 1,
        'rsi_overbought': 0,
        'macd_positive': 0,
        'momentum_positive': 0
    }
    
    signal = gbpusd_trader.get_signal(gbpusd_bearish)
    
    print(f"""
    Preço Atual: 1.26400
    RSI: {gbpusd_bearish['rsi']} (OVERSOLD)
    Abaixo SMA20/50: Sim
    MACD: Negativo
    
    🔮 Predição: {signal.direction}
    📊 Confiança: {signal.confidence*100:.2f}%
    
    💰 AÇÃO: {signal.action.value}
    📈 Tamanho: {signal.position_size*100:.0f}% do capital
    💭 Razão: {signal.reason}
    """)
    
    # Resumo de boas práticas
    print("\n" + "="*80)
    print("💡 BOAS PRÁTICAS PARA TRADING REALTIME")
    print("="*80 + "\n")
    
    print("""
    1. **Filtrar por Timeframe**
       - Use sinais apenas em M15 ou acima
       - Avoid ruído em menores timeframes
    
    2. **Filtrar por Confiança**
       - Estabeleça threshold mínimo (ex: 70% ou 80%)
       - Rode com baixa confiança apenas em micro-posições
    
    3. **Monitorar Drawdown**
       - Pare trading se equity cair > 20% em 1 semana
       - Aguarde sinais mais fortes antes de retomar
    
    4. **Validar Consistência**
       - Verifique se predições correlacionam com preço real
       - Compare com moving averages e suporte/resistência
    
    5. **Log Todos os Sinais**
       - Timestamp, indicadores, predição, confiança
       - Resultado real (ganho/perda)
       - Use para análise posterior
    
    6. **Re-treinar Mensal**
       - Adicione novos 30 dias de dados
       - Verifique se accuracy mantém acima de 82%
       - Re-treinar se cair abaixo
    """)
    
    print("\n" + "="*80)
    print("✅ PRONTO PARA DEPLOY EM PRODUÇÃO")
    print("="*80 + "\n")

if __name__ == '__main__':
    example_live_trading()
