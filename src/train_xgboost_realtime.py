#!/usr/bin/env python3
"""
Coletor de Dados MT5 + Retreinador XGBoost
- Coleta dados reais do servidor HTTP
- Calcula labels (WIN/LOSS) baseado em confluence SMC
- Treina novos modelos XGBoost
- Salva modelos retreinados
"""

import json
import asyncio
import numpy as np
import pickle
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix

try:
    import websockets
    from websockets.asyncio import client
except ImportError:
    print("❌ websockets não instalado")
    exit(1)

# ═════════════════════════════════════════════════════════════════════════════

class DataCollectorForTraining:
    """Coleta dados do servidor para retreinar XGBoost"""
    
    def __init__(self):
        self.data = {
            'GBPUSD': {'features': [], 'labels': [], 'datetimes': []},
            'EURUSD': {'features': [], 'labels': [], 'datetimes': []},
            'XAUUSD': {'features': [], 'labels': [], 'datetimes': []},
        }
        
        self.prices_history = {
            'GBPUSD': [],
            'EURUSD': [],
            'XAUUSD': [],
        }
        
        print("""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║          🤖 COLETOR DE DADOS - RETREINAMENTO XGBOOST 🤖                 ║
║                                                                            ║
║  1. Coleta 100+ candles por par do servidor                             ║
║  2. Calcula features (indicadores)                                       ║
║  3. Calcula labels (WIN/LOSS baseado em confluence)                      ║
║  4. Treina novo modelo XGBoost                                           ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
        """)
    
    def process_candle(self, candle):
        """Processar novo candle e extrair features/labels"""
        symbol = candle['symbol']
        indicators = candle['indicators']
        close = candle['close']
        open_p = candle['open']
        
        # Extrair features
        features = [
            indicators.get('rsi_14', 50),
            indicators.get('sma_20', close),
            indicators.get('sma_50', close),
            indicators.get('atr_pct', 0),
            indicators.get('momentum', 0),
            indicators.get('confluence', 2),
            close,
            candle.get('volume', 0),
        ]
        
        # Calcular label (WIN/LOSS)
        # WIN: Close próximo > Close atual OU Confluence >= 3
        # LOSS: Close próximo < Close atual
        
        self.prices_history[symbol].append(close)
        
        # Label: 1 = WIN (prédito que vai subir), 0 = LOSS (prédito que vai cair)
        # Usar confluence como sinal: se >= 3, é WIN, se < 2, é LOSS
        confluence = indicators.get('confluence', 2)
        if confluence >= 3:
            label = 1  # WIN - confluência forte
        else:
            label = 0  # LOSS - confluência fraca
        
        self.data[symbol]['features'].append(features)
        self.data[symbol]['labels'].append(label)
        self.data[symbol]['datetimes'].append(candle['datetime'])
        
        print(f"✅ {symbol} | Confluence: {confluence}/4 | Label: {'WIN' if label else 'LOSS'}")
    
    async def collect(self, duration_seconds=300):
        """Coletar dados por X segundos"""
        uri = "ws://localhost:9001"
        
        print(f"\n🔗 Conectando a {uri}...")
        print(f"⏳ Coletando dados por {duration_seconds}s (~{duration_seconds//15} candles)...\n")
        
        try:
            async with client.connect(uri) as websocket:
                print("✅ Conectado!")
                
                # Inscrever
                for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
                    await websocket.send(json.dumps({'action': 'subscribe', 'symbol': symbol}))
                
                start_time = datetime.now()
                
                async for message in websocket:
                    try:
                        candle = json.loads(message)
                        self.process_candle(candle)
                    except Exception as e:
                        print(f"⚠️  Erro: {e}")
                    
                    # Check se passou o tempo
                    if (datetime.now() - start_time).total_seconds() > duration_seconds:
                        print("\n✅ Coleta concluída!")
                        break
        
        except Exception as e:
            print(f"❌ Erro de conexão: {e}")
    
    def train_models(self):
        """Treinar modelos XGBoost com dados coletados"""
        models_dir = Path('/home/ubuntu/pessoal/options/src/models')
        models_dir.mkdir(exist_ok=True)
        
        print("\n" + "="*80)
        print("🤖 RETREINANDO MODELOS XGBOOST")
        print("="*80)
        
        for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            data = self.data[symbol]
            
            if len(data['features']) < 30:
                print(f"\n⚠️  {symbol}: Dados insuficientes ({len(data['features'])} amostras)")
                continue
            
            print(f"\n📊 Treinando {symbol}...")
            
            X = np.array(data['features'])
            y = np.array(data['labels'])
            
            # Split train/test
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y if len(np.unique(y)) > 1 else None
            )
            
            # Treinar XGBoost
            model = xgb.XGBClassifier(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=0
            )
            
            model.fit(X_train, y_train, verbose=False)
            
            # Avaliar
            y_pred = model.predict(X_test)
            accuracy = (y_pred == y_test).mean()
            
            print(f"✅ Treinado com {len(X_train)} amostras")
            print(f"   Teste: {accuracy:.2%} accuracy")
            print(f"   Distribuição: {np.bincount(y)} (Loss/Win)")
            
            # Salvar modelo
            model_path = models_dir / f'xgboost_{symbol}.pkl'
            with open(model_path, 'wb') as f:
                pickle.dump(model, f)
            print(f"   💾 Salvo em: {model_path}")
    
    def save_data_csv(self):
        """Salvar dados coletados em CSV para análise"""
        data_dir = Path('/home/ubuntu/pessoal/options/data_collected')
        data_dir.mkdir(exist_ok=True)
        
        print(f"\n💾 Salvando dados coletados...")
        
        for symbol in ['GBPUSD', 'EURUSD', 'XAUUSD']:
            data = self.data[symbol]
            
            if len(data['features']) == 0:
                continue
            
            df = pd.DataFrame(data['features'], columns=[
                'rsi_14', 'sma_20', 'sma_50', 'atr_pct', 'momentum', 'confluence', 'close', 'volume'
            ])
            df['label'] = data['labels']
            df['datetime'] = data['datetimes']
            
            csv_path = data_dir / f'{symbol}_training_data.csv'
            df.to_csv(csv_path, index=False)
            
            print(f"   ✅ {symbol}: {len(df)} amostras → {csv_path}")


async def main():
    collector = DataCollectorForTraining()
    
    # Coletar por 5 minutos (300 segundos = ~20 candles)
    await collector.collect(duration_seconds=300)
    
    # Treinar modelos
    collector.train_models()
    
    # Salvar dados
    collector.save_data_csv()
    
    print("\n" + "="*80)
    print("✅ RETREINAMENTO CONCLUÍDO!")
    print("="*80)
    print(f"\n📂 Modelos salvos em: /home/ubuntu/pessoal/options/src/models/")
    print(f"📊 Dados em: /home/ubuntu/pessoal/options/data_collected/")
    print(f"\n🚀 Reinicie o monitor para usar novos modelos!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹️  Coleta interrompida")
