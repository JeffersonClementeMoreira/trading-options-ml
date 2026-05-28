#!/usr/bin/env python3
"""
Train XGBoost Models from MT5 Historical Data
Recebe dados do MT5 via HTTP POST e treina modelos XGBoost
"""

import json
import pickle
import numpy as np
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import xgboost as xgb
from threading import Thread
import sys

class IndicatorCalculator:
    """Calcular indicadores para feature engineering"""
    
    @staticmethod
    def calculate_rsi(closes, period=14):
        """RSI (Relative Strength Index)"""
        if len(closes) < period + 1:
            return np.full(len(closes), 50.0)
        
        deltas = np.diff(closes)
        seed = deltas[:period+1]
        up = seed[seed >= 0].sum() / period
        down = -seed[seed < 0].sum() / period
        
        rs = up / down if down != 0 else 1
        rsi = np.zeros_like(closes)
        rsi[:period] = 100 - 100 / (1 + rs)
        
        for i in range(period, len(closes)):
            delta = closes[i] - closes[i-1]
            if delta > 0:
                up = delta
                down = 0
            else:
                up = 0
                down = -delta
            
            up = (up * (period - 1) + up) / period
            down = (down * (period - 1) + down) / period
            
            rs = up / down if down != 0 else 1
            rsi[i] = 100 - 100 / (1 + rs)
        
        return rsi
    
    @staticmethod
    def calculate_sma(closes, period):
        """Simple Moving Average"""
        return np.convolve(closes, np.ones(period)/period, mode='same')
    
    @staticmethod
    def calculate_atr(highs, lows, closes, period=14):
        """Average True Range (em %)"""
        tr = np.maximum(
            np.maximum(highs - lows, np.abs(highs - closes[:-1])),
            np.abs(lows - closes[:-1])
        )
        tr = np.concatenate([[highs[0] - lows[0]], tr])
        atr = np.convolve(tr, np.ones(period)/period, mode='same')
        atr_pct = (atr / closes) * 100
        return atr_pct
    
    @staticmethod
    def extract_features(opens, highs, lows, closes, volumes):
        """Extrair features para XGBoost (8 features)"""
        n = len(closes)
        
        rsi_14 = IndicatorCalculator.calculate_rsi(closes, 14)
        sma_20 = IndicatorCalculator.calculate_sma(closes, 20)
        sma_50 = IndicatorCalculator.calculate_sma(closes, 50)
        atr_pct = IndicatorCalculator.calculate_atr(highs, lows, closes, 14)
        
        # Momentum (Close - SMA_20)
        momentum = closes - sma_20
        
        # Confluence (quantos indicadores apontam para cima)
        confluence = np.zeros(n)
        for i in range(n):
            score = 0
            if closes[i] > sma_20[i]: score += 1
            if closes[i] > sma_50[i]: score += 1
            if rsi_14[i] > 50: score += 1
            confluence[i] = score
        
        # Volume MA
        volume_ma = IndicatorCalculator.calculate_sma(volumes.astype(float), 20)
        
        # Stack features: [RSI_14, SMA_20, SMA_50, ATR_pct, Momentum, Confluence, Close, Volume_MA]
        features = np.column_stack([
            rsi_14,
            sma_20,
            sma_50,
            atr_pct,
            momentum,
            confluence,
            closes,
            volume_ma
        ])
        
        return features


class TrainingHandler(BaseHTTPRequestHandler):
    """Handler para receber dados e treinar modelos"""
    
    def do_POST(self):
        """Receber POST com dados históricos"""
        if self.path != '/train':
            self.send_response(404)
            self.end_headers()
            return
        
        # Ler corpo da requisição
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
            self.train_model(data)
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "success"}).encode())
            
        except Exception as e:
            print(f"❌ Erro ao processar dados: {e}")
            self.send_response(500)
            self.end_headers()
    
    def train_model(self, data):
        """Treinar modelo XGBoost com dados"""
        symbol = data.get('symbol')
        candles = data.get('data', [])
        
        if len(candles) < 100:
            print(f"⚠️  Aviso: {symbol} tem apenas {len(candles)} candles (mínimo 100)")
            return
        
        print(f"\n{'='*60}")
        print(f"📊 TREINANDO MODELO: {symbol}")
        print(f"{'='*60}")
        print(f"   Candles: {len(candles)}")
        
        # Extrair OHLCV
        opens = np.array([c['open'] for c in candles])
        highs = np.array([c['high'] for c in candles])
        lows = np.array([c['low'] for c in candles])
        closes = np.array([c['close'] for c in candles])
        volumes = np.array([c['volume'] for c in candles])
        
        # Calcular features
        X = IndicatorCalculator.extract_features(opens, highs, lows, closes, volumes)
        
        # Gerar labels: 1 se close futuro > close atual, 0 senão (leave-one-out)
        y = np.where(closes[1:] > closes[:-1], 1, 0)
        
        # Ajustar para ter mesmo tamanho
        X = X[:-1]
        
        print(f"   Features: {X.shape}")
        print(f"   Labels: {y.shape}")
        print(f"   Classes: {np.bincount(y)}")
        
        # Treinar XGBoost
        model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=5,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0
        )
        
        model.fit(X, y)
        
        # Avaliar
        score = model.score(X, y)
        print(f"   Acurácia: {score:.2%}")
        
        # Salvar modelo
        filepath = f"/home/ubuntu/pessoal/options/src/xgboost_{symbol}.pkl"
        with open(filepath, 'wb') as f:
            pickle.dump(model, f)
        
        print(f"✅ Modelo salvo: {filepath}")
    
    def log_message(self, format, *args):
        """Suprimir logs HTTP padrão"""
        pass


def run_server():
    """Rodar servidor de treinamento"""
    print("╔════════════════════════════════════════════════════════╗")
    print("║  SERVIDOR DE TREINAMENTO XGBoost (MT5 → Python)       ║")
    print("╚════════════════════════════════════════════════════════╝")
    print("")
    print("📡 Aguardando dados do MT5...")
    print("   URL: http://0.0.0.0:9999/train")
    print("")
    
    server = HTTPServer(('0.0.0.0', 9999), TrainingHandler)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Servidor encerrado")
        server.shutdown()


if __name__ == '__main__':
    run_server()
