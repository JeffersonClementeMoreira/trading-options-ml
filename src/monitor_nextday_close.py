#!/usr/bin/env python3
"""
Monitor em tempo real - Prever fechamento D+1 às 14:00

Sistema:
1. Recebe dados live do MT5 a cada 15 min
2. Faz previsão do fechamento D+1 às 14:00
3. Armazena previsão
4. Valida no D+1 às 14:00
5. Mostra taxa de acerto
"""

import pickle
import numpy as np
import os
import json
from datetime import datetime, timedelta
from collections import defaultdict

class NextDayMonitor:
    """Monitor em tempo real das previsões D+1 14:00"""
    
    def __init__(self, models_dir="/home/ubuntu/pessoal/options/src"):
        self.models_dir = models_dir
        self.symbols = ['EURUSD', 'GBPUSD', 'XAUUSD']
        self.models_clf = {}  # Classificadores
        self.models_reg = {}  # Regressores
        self.predictions = defaultdict(list)  # Armazenar previsões
        self.predictions_file = "/tmp/nextday_predictions.json"
        
    def load_models(self):
        """Carregar modelos treinados"""
        print("\n🔄 Carregando modelos...")
        
        for symbol in self.symbols:
            clf_path = f"{self.models_dir}/nextday_clf_{symbol}.pkl"
            reg_path = f"{self.models_dir}/nextday_reg_{symbol}.pkl"
            
            if os.path.exists(clf_path):
                with open(clf_path, 'rb') as f:
                    self.models_clf[symbol] = pickle.load(f)
                print(f"   ✅ {symbol}: Classificador carregado")
            else:
                print(f"   ❌ {symbol}: Classificador não encontrado")
            
            if os.path.exists(reg_path):
                with open(reg_path, 'rb') as f:
                    self.models_reg[symbol] = pickle.load(f)
                print(f"   ✅ {symbol}: Regressor carregado")
            else:
                print(f"   ❌ {symbol}: Regressor não encontrado")
    
    def calculate_features(self, candle_data):
        """
        Calcular features a partir de um candle
        
        candle_data: {
            'close': 1.0851,
            'rsi': 65,
            'sma_20': 1.0845,
            'sma_50': 1.0840,
            'atr_pct': 0.0003,
            'momentum': 0.0001,
            'distance_std': 1.5,
            'volume': 150000
        }
        """
        features = np.array([[
            candle_data.get('rsi', 50),
            candle_data.get('sma_20', candle_data['close']),
            candle_data.get('sma_50', candle_data['close']),
            candle_data.get('atr_pct', 0.001),
            candle_data.get('momentum', 0),
            candle_data.get('distance_std', 0),
            candle_data['close'],
            candle_data.get('volume_ratio', 1)
        ]])
        
        return features
    
    def predict_nextday_close(self, symbol, candle_data):
        """
        Fazer previsão de fechamento D+1 às 14:00
        
        Retorna:
        {
            'symbol': 'EURUSD',
            'prediction_time': '2024-01-15 10:30:00',
            'current_price': 1.0851,
            'predicted_close_d1': 1.0865,
            'predicted_direction': 'UP',
            'confidence': 0.87,
            'expected_pips': 14
        }
        """
        if symbol not in self.models_clf or symbol not in self.models_reg:
            return None
        
        try:
            features = self.calculate_features(candle_data)
            
            # Classificação (UP/DOWN)
            clf_pred = self.models_clf[symbol].predict(features)[0]
            clf_proba = np.max(self.models_clf[symbol].predict_proba(features))
            
            # Regressão (preço exato)
            reg_pred = self.models_reg[symbol].predict(features)[0]
            
            # Calcular pips esperados
            current_price = candle_data['close']
            expected_pips = abs(reg_pred - current_price) * 10000
            
            # Determinar direção
            direction = 'UP' if clf_pred == 1 else 'DOWN'
            
            prediction = {
                'symbol': symbol,
                'prediction_time': datetime.now().isoformat(),
                'current_price': current_price,
                'predicted_close_d1': float(reg_pred),
                'predicted_direction': direction,
                'confidence': float(clf_proba),
                'expected_pips': float(expected_pips),
                'clf_pred': int(clf_pred),
                'status': 'PENDING'  # Será 'HIT' ou 'MISS' no D+1
            }
            
            return prediction
            
        except Exception as e:
            print(f"   ❌ Erro na previsão: {e}")
            return None
    
    def save_prediction(self, prediction):
        """Salvar previsão em arquivo"""
        symbol = prediction['symbol']
        self.predictions[symbol].append(prediction)
        
        # Salvar em JSON
        with open(self.predictions_file, 'w') as f:
            predictions_dict = {s: self.predictions[s] for s in self.symbols}
            json.dump(predictions_dict, f, indent=2, default=str)
    
    def demo_predictions(self):
        """Demo: Fazer previsões com dados de exemplo"""
        print("\n" + "="*80)
        print("📊 DEMO - PREVISÕES PARA FECHAMENTO D+1 ÀS 14:00")
        print("="*80 + "\n")
        
        # Dados de exemplo
        example_candles = {
            'EURUSD': {
                'close': 1.0851,
                'rsi': 65,
                'sma_20': 1.0845,
                'sma_50': 1.0840,
                'atr_pct': 0.0003,
                'momentum': 0.0001,
                'distance_std': 1.5,
                'volume': 150000,
                'volume_ratio': 1.2
            },
            'GBPUSD': {
                'close': 1.2720,
                'rsi': 42,
                'sma_20': 1.2710,
                'sma_50': 1.2700,
                'atr_pct': 0.0004,
                'momentum': -0.0002,
                'distance_std': 0.8,
                'volume': 120000,
                'volume_ratio': 0.9
            },
            'XAUUSD': {
                'close': 2398.5,
                'rsi': 72,
                'sma_20': 2390.0,
                'sma_50': 2385.0,
                'atr_pct': 0.003,
                'momentum': 0.003,
                'distance_std': 2.2,
                'volume': 180000,
                'volume_ratio': 1.5
            }
        }
        
        for symbol in self.symbols:
            print(f"📈 {symbol}")
            print("-" * 80)
            
            candle_data = example_candles[symbol]
            prediction = self.predict_nextday_close(symbol, candle_data)
            
            if prediction:
                print(f"  ⏰ Hora da previsão: {prediction['prediction_time']}")
                print(f"  💰 Preço atual: {prediction['current_price']:.5f}")
                print(f"  🎯 Previsão D+1 14:00: {prediction['predicted_close_d1']:.5f}")
                print(f"  📊 Direção: {prediction['predicted_direction']}")
                print(f"  🔐 Confiança: {prediction['confidence']*100:.1f}%")
                print(f"  📏 Pips esperados: {prediction['expected_pips']:.1f}")
                print()
                
                self.save_prediction(prediction)
            else:
                print(f"  ❌ Erro ao fazer previsão\n")


def main():
    print("\n" + "╔" + "="*78 + "╗")
    print("║" + " "*15 + "🎯 MONITOR - PREVER FECHAMENTO D+1 ÀS 14:00" + " "*20 + "║")
    print("╚" + "="*78 + "╝")
    
    monitor = NextDayMonitor()
    monitor.load_models()
    
    if not monitor.models_clf:
        print("\n❌ Nenhum modelo carregado!")
        return
    
    print("\n✅ Modelos carregados com sucesso")
    print("\nFazer previsões a cada 15 minutos do próximo candle M15...")
    print("Validar resultado no D+1 às 14:00")
    
    # Demo
    monitor.demo_predictions()
    
    print("\n" + "="*80)
    print("📊 Previsões armazenadas em:", monitor.predictions_file)
    print("="*80 + "\n")


if __name__ == '__main__':
    main()
