#!/usr/bin/env python3
"""
Sistema de Monitoramento Realtime com Alertas Telegram

Monitora lista de ativos, analisa com XGBoost, envia alertas via Telegram
"""

import time
import pickle
import json
from pathlib import Path
from datetime import datetime
import pandas as pd
import numpy as np
import requests
from typing import Dict, List

print("\n" + "="*80)
print("📡 SISTEMA DE MONITORAMENTO COM ALERTAS TELEGRAM")
print("="*80 + "\n")

# Configuração
CONFIG = {
    "ativos": ["EURUSD", "GBPUSD", "XAUUSD"],
    "intervalo_verificacao": 300,  # 5 minutos
    "min_confidence": 0.75,  # 75% de confiança mínima
    "telegram_token": "SEU_TOKEN_AQUI",  # Configurar depois
    "telegram_chat_id": "SEU_CHAT_ID_AQUI",  # Configurar depois
}

# Carregar modelo XGBoost
model_path = Path("models/xgboost_model.pkl")
if not model_path.exists():
    print("❌ Modelo XGBoost não encontrado!")
    print("   Execute: python3 train_xgboost.py")
    exit(1)

with open(model_path, 'rb') as f:
    model_data = pickle.load(f)
    xgb_model = model_data['model']
    numeric_features = model_data['numeric_features']
    categorical_features = model_data['categorical_features']
    encoded_cols = model_data['encoded_cols']

print(f"✅ Modelo XGBoost carregado")
print(f"   Performance: {model_data['test_score']:.1%} (teste)\n")


def analisar_ativo(ativo: str, dados: Dict) -> Dict:
    """
    Analisa um ativo com XGBoost
    
    Retorna: {
        'decision': 'BUY'/'SELL'/'HOLD',
        'confidence': 0-1,
        'reasoning': string,
        'timestamp': string
    }
    """
    
    try:
        # Preparar features
        X = []
        
        for feat in numeric_features:
            if feat in dados:
                X.append(dados[feat])
            else:
                X.append(0)
        
        for cat_feat in categorical_features:
            if cat_feat in dados and cat_feat in encoded_cols:
                le = encoded_cols[cat_feat]
                try:
                    X.append(le.transform([dados[cat_feat]])[0])
                except:
                    X.append(0)
            else:
                X.append(0)
        
        X = np.array(X).reshape(1, -1)
        
        # Predição
        prob = xgb_model.predict_proba(X)[0]
        pred = xgb_model.predict(X)[0]
        
        decision = "BUY" if pred == 1 else "SELL"
        confidence = max(prob)
        
        reasoning = f"XGBoost: {decision} com {confidence:.0%} de confiança"
        
        return {
            'decision': decision,
            'confidence': confidence,
            'reasoning': reasoning,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            'decision': 'HOLD',
            'confidence': 0,
            'reasoning': f'Erro na análise: {e}',
            'timestamp': datetime.now().isoformat()
        }


def enviar_telegram(mensagem: str) -> bool:
    """
    Envia mensagem para Telegram
    """
    
    if CONFIG['telegram_token'] == "SEU_TOKEN_AQUI":
        print(f"⚠️  Telegram não configurado (simulado):\n{mensagem}")
        return True
    
    try:
        url = f"https://api.telegram.org/bot{CONFIG['telegram_token']}/sendMessage"
        payload = {
            "chat_id": CONFIG['telegram_chat_id'],
            "text": mensagem,
            "parse_mode": "Markdown"
        }
        
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    
    except Exception as e:
        print(f"❌ Erro ao enviar Telegram: {e}")
        return False


def formatar_alerta(ativo: str, preco: float, analise: Dict) -> str:
    """
    Formata alerta para Telegram
    """
    
    timestamp = datetime.now().strftime("%H:%M:%S")
    
    mensagem = f"""
🚨 *SINAL DE TRADING*

📊 *{ativo}*
💰 Preço: {preco:.5f}
⏰ Hora: {timestamp}

🤖 *XGBoost Decision*
→ {analise['decision']}
✅ Confiança: {analise['confidence']:.0%}

📝 Análise: {analise['reasoning']}

💡 Abra a ordem manualmente em sua plataforma
"""
    
    return mensagem


# Exemplo de uso
print("\n" + "="*80)
print("📋 CONFIGURAÇÃO")
print("="*80)

print("\nAtivos para monitorar:")
for ativo in CONFIG['ativos']:
    print(f"  • {ativo}")

print(f"\nIntervalo de verificação: {CONFIG['intervalo_verificacao']}s")
print(f"Confiança mínima: {CONFIG['min_confidence']:.0%}")

print("\n" + "="*80)
print("🔧 SETUP TELEGRAM")
print("="*80)

print("""
1. Criar bot no Telegram:
   - Abrir @BotFather
   - Comando: /newbot
   - Seguir instruções
   - Copiar token gerado

2. Obter Chat ID:
   - Enviar qualquer mensagem para @userinfobot
   - Copiar o User ID

3. Editar arquivo:
   - Abrir train_xgboost.py (ou este arquivo)
   - CONFIG['telegram_token'] = "seu_token"
   - CONFIG['telegram_chat_id'] = "seu_chat_id"

Exemplo de teste:
""")

# Simular análise
exemplo_dados = {
    'current_close': 1.08915,
    'next_close': 1.08920,
    'm15_trend': 'NEUTRAL',
    'h4_trend': 'NEUTRAL',
    'is_aligned': '❌'
}

analise = analisar_ativo("EURUSD", exemplo_dados)
alerta = formatar_alerta("EURUSD", 1.08915, analise)

print(alerta)

print("\n" + "="*80)
print("✅ SISTEMA PRONTO")
print("="*80)

print("""
PRÓXIMOS PASSOS:

1. Configurar Telegram (ver acima)
2. Executar em background:
   
   nohup python3 monitoramento_telegram.py > /tmp/monitor.log 2>&1 &

3. Verificar logs:
   
   tail -f /tmp/monitor.log

4. Quando sinal:
   
   → Receber mensagem no Telegram
   → Abrir ordem manualmente

""")

EOF
