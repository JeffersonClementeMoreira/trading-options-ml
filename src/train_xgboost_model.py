#!/usr/bin/env python3
"""
Treinador de Modelos XGBoost - Para qualquer par (XAUUSD, EURUSD, GBPUSD, USDJPY, etc)

Uso:
  python3 train_xgboost_model.py --symbol USDJPY --csv dados_USDJPY.csv

Saída:
  xgboost_USDJPY.pkl (pronto para usar)
"""

import csv
import pickle
import numpy as np
import xgboost as xgb
from datetime import datetime
import argparse
from pathlib import Path

# ═════════════════════════════════════════════════════════════════════════════

class XGBoostTrainer:
    """Treina modelo XGBoost para um par específico"""
    
    def __init__(self, symbol):
        self.symbol = symbol
        self.model = None
        
    def calculate_indicators(self, closes, highs, lows, volumes):
        """Calcula indicadores (mesmos do servidor)"""
        try:
            if len(closes) < 50:
                return None
            
            close = closes[-1]
            
            # RSI
            def rsi(prices, period):
                deltas = np.diff(prices)
                seed = deltas[:period+1]
                up = seed[seed >= 0].sum() / period
                down = -seed[seed < 0].sum() / period
                rs = up / down if down != 0 else 0
                return 100 - 100 / (1 + rs)
            
            rsi_14 = float(rsi(closes, 14)) if len(closes) > 14 else 50.0
            
            # SMAs
            sma_20 = float(np.mean(closes[-20:])) if len(closes) > 20 else close
            sma_50 = float(np.mean(closes[-50:])) if len(closes) > 50 else close
            ema_12 = float(np.mean(closes[-12:])) if len(closes) > 12 else close
            ema_26 = float(np.mean(closes[-26:])) if len(closes) > 26 else close
            
            # ATR
            tr_list = []
            for i in range(max(1, len(highs)-14), len(highs)):
                tr = highs[i] - lows[i]
                if i > 0:
                    tr = max(tr, highs[i] - closes[i-1], closes[i-1] - lows[i])
                tr_list.append(tr)
            atr = float(np.mean(tr_list)) if tr_list else 0
            atr_pct = float(atr / close * 100) if close != 0 else 0
            
            # Momentum
            momentum = float(closes[-1] - closes[-15]) if len(closes) > 15 else 0
            
            # Confluence
            confluence = 2
            if sma_20 > sma_50:
                confluence += 1
            if close > sma_20:
                confluence += 1
            
            # Volume MA
            volume_ma = float(np.mean(volumes[-20:])) if len(volumes) > 20 else 0
            
            # Retornar 8 features para XGBoost
            features = [
                rsi_14,
                sma_20,
                sma_50,
                atr_pct,
                momentum,
                confluence,
                close,
                volume_ma,
            ]
            
            return features
        
        except Exception as e:
            print(f"Erro ao calcular indicadores: {e}")
            return None
    
    def load_data(self, csv_file):
        """Carregar dados de CSV"""
        print(f"📂 Carregando dados de: {csv_file}")
        
        closes = []
        highs = []
        lows = []
        opens = []
        volumes = []
        labels = []
        
        try:
            with open(csv_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            print(f"   Total de linhas: {len(rows)}")
            
            # Processar dados
            for i, row in enumerate(rows):
                try:
                    close = float(row.get('close', row.get('Close', 0)))
                    high = float(row.get('high', row.get('High', close)))
                    low = float(row.get('low', row.get('Low', close)))
                    open_ = float(row.get('open', row.get('Open', close)))
                    volume = float(row.get('volume', row.get('Volume', 0)))
                    
                    closes.append(close)
                    highs.append(high)
                    lows.append(low)
                    opens.append(open_)
                    volumes.append(volume)
                    
                    # Label: se próximo close > current close = 1, senão 0
                    if i < len(rows) - 1:
                        next_close = float(rows[i+1].get('close', rows[i+1].get('Close', close)))
                        label = 1 if next_close > close else 0
                        labels.append(label)
                
                except (ValueError, TypeError, KeyError):
                    continue
            
            print(f"   ✅ Dados carregados: {len(closes)} candles")
            
            # Remover último label (não tem próximo candle)
            labels.pop()
            
            return closes, highs, lows, opens, volumes, labels
        
        except FileNotFoundError:
            print(f"   ❌ Arquivo não encontrado: {csv_file}")
            return None, None, None, None, None, None
        except Exception as e:
            print(f"   ❌ Erro ao carregar CSV: {e}")
            return None, None, None, None, None, None
    
    def train(self, csv_file):
        """Treinar modelo"""
        print(f"\n🤖 Treinando modelo XGBoost para {self.symbol}...")
        
        # Carregar dados
        closes, highs, lows, opens, volumes, labels = self.load_data(csv_file)
        
        if closes is None:
            return False
        
        if len(closes) < 100:
            print(f"❌ Precisa de mínimo 100 candles, tem {len(closes)}")
            return False
        
        # Calcular features
        print(f"📊 Calculando indicadores...")
        X = []
        y = []
        
        for i in range(50, len(closes) - 1):  # Mínimo 50 candles para indicadores
            closes_window = closes[:i+1]
            highs_window = highs[:i+1]
            lows_window = lows[:i+1]
            volumes_window = volumes[:i+1]
            
            features = self.calculate_indicators(closes_window, highs_window, lows_window, volumes_window)
            
            if features and i < len(labels):
                X.append(features)
                y.append(labels[i])
        
        print(f"   ✅ Features calculadas: {len(X)} exemplos")
        
        if len(X) < 10:
            print(f"❌ Precisa de mínimo 10 exemplos de treino, tem {len(X)}")
            return False
        
        # Converter para numpy
        X = np.array(X)
        y = np.array(y)
        
        print(f"   X shape: {X.shape}")
        print(f"   y distribution: {np.sum(y)} positivos, {len(y) - np.sum(y)} negativos")
        
        # Treinar
        print(f"\n⚙️  Treinando XGBoost...")
        
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=0,
        )
        
        self.model.fit(X, y)
        
        # Avaliar
        train_score = self.model.score(X, y)
        print(f"\n✅ Acurácia de treinamento: {train_score:.2%}")
        
        return True
    
    def save(self, output_dir="/home/ubuntu/pessoal/options/src"):
        """Salvar modelo"""
        if self.model is None:
            print("❌ Modelo não foi treinado")
            return False
        
        output_file = Path(output_dir) / f"xgboost_{self.symbol}.pkl"
        
        print(f"\n💾 Salvando modelo em: {output_file}")
        
        with open(output_file, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"✅ Modelo salvo com sucesso!")
        print(f"   Arquivo: {output_file}")
        print(f"   Pronto para usar em: monitor_mt5_real.py")
        
        return True


# ═════════════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Treinar modelo XGBoost para um par')
    parser.add_argument('--symbol', required=True, help='Símbolo (ex: USDJPY, GBPUSD)')
    parser.add_argument('--csv', required=True, help='Arquivo CSV com dados históricos')
    parser.add_argument('--output', default='/home/ubuntu/pessoal/options/src', help='Diretório de saída')
    
    args = parser.parse_args()
    
    # Validar
    if not Path(args.csv).exists():
        print(f"❌ Arquivo CSV não existe: {args.csv}")
        print("\nExemplo de uso:")
        print("  python3 train_xgboost_model.py --symbol USDJPY --csv USDJPY_M15_data.csv")
        return
    
    # Treinar
    trainer = XGBoostTrainer(args.symbol)
    
    if trainer.train(args.csv):
        trainer.save(args.output)
        print(f"\n✨ Modelo treinado e pronto!")
    else:
        print(f"\n❌ Erro ao treinar modelo")


if __name__ == "__main__":
    main()
