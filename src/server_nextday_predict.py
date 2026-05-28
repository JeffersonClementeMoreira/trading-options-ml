#!/usr/bin/env python3
"""
Server HTTP para receber dados em tempo real do MT5
e fazer previsões de fechamento D+1 às 14:00

Porta: 9876 (diferente das anteriores)
Endpoint: POST /predict/nextday
"""

import http.server
import socketserver
import json
import threading
import pickle
import numpy as np
from datetime import datetime
from urllib.parse import urlparse
import os

PORT = 9876

class PredictionHandler(http.server.BaseHTTPRequestHandler):
    """Handler para requisições de previsão"""
    
    models_clf = {}  # Classificadores
    models_reg = {}  # Regressores
    
    def do_POST(self):
        """Receber POST com dados do candle e fazer previsão"""
        
        if self.path != '/predict/nextday':
            self.send_error(404, "Endpoint não encontrado")
            return
        
        try:
            # Ler dados do POST
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            # Parse JSON
            data = json.loads(body.decode('utf-8'))
            symbol = data.get('symbol')
            candle_data = data.get('candle')
            
            if not symbol or not candle_data:
                self.send_error(400, "Dados incompletos")
                return
            
            # Fazer previsão
            prediction = self.make_prediction(symbol, candle_data)
            
            if prediction:
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(prediction, default=str).encode())
            else:
                self.send_error(400, "Erro na previsão")
        
        except Exception as e:
            self.send_error(500, str(e))
    
    def make_prediction(self, symbol, candle_data):
        """Fazer previsão com os modelos carregados"""
        
        if symbol not in self.models_clf:
            return None
        
        try:
            # Preparar features
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
            
            # Classificação
            clf_pred = self.models_clf[symbol].predict(features)[0]
            clf_proba = np.max(self.models_clf[symbol].predict_proba(features))
            
            # Regressão
            reg_pred = self.models_reg[symbol].predict(features)[0]
            
            # Pips esperados
            current_price = candle_data['close']
            expected_pips = abs(reg_pred - current_price) * 10000
            
            return {
                'symbol': symbol,
                'prediction_time': datetime.now().isoformat(),
                'current_price': current_price,
                'predicted_close_d1_14h': float(reg_pred),
                'predicted_direction': 'UP' if clf_pred == 1 else 'DOWN',
                'confidence': float(clf_proba),
                'expected_pips': float(expected_pips),
                'status': 'OK'
            }
        
        except Exception as e:
            print(f"Erro: {e}")
            return None
    
    def log_message(self, format, *args):
        """Suprimir logs padrão"""
        pass


def load_models():
    """Carregar modelos no handler"""
    models_dir = "/home/ubuntu/pessoal/options/src"
    
    for symbol in ['EURUSD', 'GBPUSD', 'XAUUSD']:
        clf_path = f"{models_dir}/nextday_clf_{symbol}.pkl"
        reg_path = f"{models_dir}/nextday_reg_{symbol}.pkl"
        
        if os.path.exists(clf_path):
            with open(clf_path, 'rb') as f:
                PredictionHandler.models_clf[symbol] = pickle.load(f)
        
        if os.path.exists(reg_path):
            with open(reg_path, 'rb') as f:
                PredictionHandler.models_reg[symbol] = pickle.load(f)


def main():
    print(f"\n🚀 Servidor de Previsão D+1 iniciando...")
    print(f"📡 Porta: {PORT}")
    print(f"🔗 Endpoint: POST http://0.0.0.0:{PORT}/predict/nextday")
    print()
    
    # Carregar modelos
    load_models()
    
    if not PredictionHandler.models_clf:
        print("❌ Nenhum modelo carregado!")
        return
    
    print(f"✅ Modelos carregados: {list(PredictionHandler.models_clf.keys())}")
    print()
    
    # Iniciar servidor
    try:
        with socketserver.TCPServer(("", PORT), PredictionHandler) as httpd:
            print(f"✅ Servidor rodando. Pressione Ctrl+C para parar.\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n⏹️  Servidor parado.")


if __name__ == '__main__':
    main()
