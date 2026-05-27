#!/usr/bin/env python3
"""
Análise profunda dos dados reais recebidos
Calcula: volatilidade, correlações, performance do modelo XGBoost
"""

import asyncio
import websockets
import json
import numpy as np
from collections import defaultdict, deque
from datetime import datetime
import pickle
import os

class DeepRealDataAnalysis:
    def __init__(self):
        self.ws_url = "ws://127.0.0.1:9001"
        self.model_path = "/home/ubuntu/pessoal/options/models"
        self.models = {}
        self.candle_history = defaultdict(lambda: deque(maxlen=100))
        self.predictions = defaultdict(list)
        self.load_models()

    def load_models(self):
        """Carrega modelos XGBoost"""
        try:
            for symbol in ["EURUSD", "XAUUSD", "GBPUSD"]:
                model_file = f"{self.model_path}/xgboost_{symbol.lower()}.pkl"
                if os.path.exists(model_file):
                    with open(model_file, 'rb') as f:
                        self.models[symbol] = pickle.load(f)
                    print(f"✅ Modelo {symbol} carregado")
                else:
                    print(f"⚠️ Modelo {symbol} não encontrado")
        except Exception as e:
            print(f"❌ Erro ao carregar modelos: {e}")

    def calculate_indicators(self, symbol):
        """Calcula indicadores a partir do histórico"""
        hist = self.candle_history[symbol]
        if len(hist) < 50:
            return None
        
        closes = np.array([c[3] for c in hist])  # close
        highs = np.array([c[1] for c in hist])   # high
        lows = np.array([c[2] for c in hist])    # low
        volumes = np.array([c[4] for c in hist]) # volume
        
        try:
            # RSI-14
            deltas = np.diff(closes)
            seed = deltas[:14].mean()
            up = deltas.copy()
            up[up < 0] = 0
            down = -deltas.copy()
            down[down < 0] = 0
            rs = np.zeros_like(closes)
            rs[14] = up[:14].sum() / down[:14].sum()
            for i in range(15, len(closes)):
                rs[i] = (up[i] * 13 + rs[i-1] * 14) / 14 / ((down[i] * 13 + rs[i-1] * 14) / 14)
            rsi = 100 - (100 / (1 + rs[-1]))
            
            # SMA
            sma20 = closes[-20:].mean()
            sma50 = closes[-50:].mean()
            
            # ATR
            tr1 = highs - lows
            tr2 = np.abs(highs - closes[:-1])
            tr3 = np.abs(lows - closes[:-1])
            tr = np.concatenate(([tr1[0]], np.maximum(np.maximum(tr1[1:], tr2), tr3)))
            atr = tr[-14:].mean()
            atr_pct = (atr / closes[-1]) * 100
            
            # Momentum
            momentum = closes[-1] - closes[-12]
            
            # Volume MA
            vol_ma = volumes[-20:].mean()
            
            return {
                "rsi": rsi,
                "sma20": sma20,
                "sma50": sma50,
                "atr": atr,
                "atr_pct": atr_pct,
                "momentum": momentum,
                "close": closes[-1],
                "volume": volumes[-1],
                "vol_ma": vol_ma,
                "confluence": 0  # placeholder
            }
        except Exception as e:
            print(f"❌ Erro ao calcular indicadores: {e}")
            return None

    def predict_xgboost(self, symbol, indicators):
        """Faz previsão com XGBoost"""
        if symbol not in self.models or not indicators:
            return None
        
        try:
            import xgboost as xgb
            features = np.array([[
                indicators["rsi"],
                indicators["sma20"],
                indicators["sma50"],
                indicators["atr_pct"],
                indicators["momentum"],
                indicators["confluence"],
                indicators["close"],
                indicators["volume"]
            ]])
            
            pred_prob = self.models[symbol].predict_proba(features)[0]
            return {
                "probability": pred_prob[1] if len(pred_prob) > 1 else pred_prob[0],
                "prediction": 1 if pred_prob[1] > 0.5 else 0 if len(pred_prob) > 1 else 0
            }
        except Exception as e:
            print(f"❌ Erro em previsão: {e}")
            return None

    async def connect(self):
        """Conecta ao WebSocket"""
        try:
            async with websockets.connect(self.ws_url) as ws:
                print(f"\n✅ Conectado - Análise Profunda de Dados Reais\n")
                print("=" * 100)
                
                candle_count = 0
                while True:
                    try:
                        msg = await asyncio.wait_for(ws.recv(), timeout=30.0)
                        data = json.loads(msg)
                        
                        if "symbol" not in data:
                            continue
                        
                        symbol = data["symbol"]
                        dt = data.get("datetime", "")
                        
                        # Armazenar histórico
                        self.candle_history[symbol].append((
                            data.get("open", 0),
                            data.get("high", 0),
                            data.get("low", 0),
                            data.get("close", 0),
                            data.get("volume", 0)
                        ))
                        
                        candle_count += 1
                        
                        # Calcular indicadores
                        indicators = self.calculate_indicators(symbol)
                        
                        if indicators and symbol in self.models:
                            pred = self.predict_xgboost(symbol, indicators)
                            if pred:
                                self.predictions[symbol].append({
                                    "datetime": dt,
                                    "probability": pred["probability"],
                                    "prediction": pred["prediction"]
                                })
                                
                                pred_label = "COMPRA" if pred["prediction"] == 1 else "VENDA"
                                prob_pct = pred["probability"] * 100
                                
                                print(f"🎯 {symbol} | {dt} | Pred: {pred_label:6} | Prob: {prob_pct:5.1f}% | "
                                      f"RSI:{indicators['rsi']:5.1f} SMA20:{indicators['sma20']:.5f} ATR%:{indicators['atr_pct']:5.2f}%")
                        
                        # Stats a cada 20 candles
                        if candle_count % 20 == 0:
                            self.print_summary()
                            
                    except asyncio.TimeoutError:
                        print("⏳ Aguardando dados do MT5...")
                    except Exception as e:
                        print(f"❌ Erro: {e}")
                        
        except Exception as e:
            print(f"❌ Conexão erro: {e}")
            await asyncio.sleep(5)
            await self.connect()

    def print_summary(self):
        """Resumo das análises"""
        print("\n" + "=" * 100)
        print("RESUMO DAS PREVISÕES".center(100))
        print("=" * 100)
        
        for symbol in sorted(self.predictions.keys()):
            preds = self.predictions[symbol]
            if len(preds) > 0:
                probs = [p["probability"] for p in preds]
                avg_prob = np.mean(probs)
                predictions = [p["prediction"] for p in preds]
                compras = sum(predictions)
                vendas = len(predictions) - compras
                
                print(f"\n{symbol:8} | Total: {len(preds):3} | "
                      f"COMPRA: {compras:3} ({compras/len(preds)*100:5.1f}%) | "
                      f"VENDA: {vendas:3} ({vendas/len(preds)*100:5.1f}%) | "
                      f"Prob Média: {avg_prob:.3f}")

async def main():
    analyzer = DeepRealDataAnalysis()
    await analyzer.connect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n✋ Análise encerrada")
