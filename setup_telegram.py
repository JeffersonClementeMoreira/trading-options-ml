#!/usr/bin/env python3
"""
Script para obter seu CHAT_ID do Telegram.

Instruções:
1. Execute este script
2. Copie a URL que aparecer
3. Abra a URL no navegador
4. Converse com o bot (envie uma mensagem)
5. O script mostrará seu chat_id
"""

import requests
import json

TELEGRAM_TOKEN = "6024515460:AAFGPwqNStgL0mv3VfxCQ_ZyQS3CtdzOeF0"

def get_chat_id():
    """Obtém chat_id das mensagens recentes do bot"""
    
    print("\n" + "="*80)
    print("🤖 CONFIGURAÇÃO DO CHAT ID DO TELEGRAM")
    print("="*80)
    
    # URL para conversar com o bot
    bot_username = "options_smc_bot"  # Assumindo nome (você precisa confirmar)
    print(f"\n1️⃣  Abra Telegram e procure por: @{bot_username}")
    print("2️⃣  Clique em 'Start' ou envie uma mensagem qualquer")
    print("3️⃣  Aguarde 5 segundos e volte aqui...\n")
    
    input("Pressione ENTER quando tiver enviado uma mensagem ao bot...")
    
    # Tenta obter updates
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        if not data.get('ok'):
            print("❌ Erro ao conectar com Telegram!")
            print(f"   Resposta: {data}")
            return None
        
        updates = data.get('result', [])
        if not updates:
            print("❌ Nenhuma mensagem encontrada!")
            print("   Verifique se enviou mensagem ao bot")
            return None
        
        # Pega o último update
        latest = updates[-1]
        chat_id = latest.get('message', {}).get('chat', {}).get('id')
        
        if not chat_id:
            print("❌ Não consegui extrair o chat_id")
            return None
        
        print(f"\n✅ SUCESSO! Seu CHAT_ID é: {chat_id}\n")
        return str(chat_id)
    
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return None


def test_notification(chat_id):
    """Testa enviando uma notificação"""
    if not chat_id:
        return
    
    print("📨 Enviando mensagem de teste...")
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(
            url,
            json={
                "chat_id": chat_id,
                "text": "✅ *Bot SMC Options* funcionando!\n\n"
                        "Agora você receberá sinais de trading em tempo real.",
                "parse_mode": "Markdown"
            },
            timeout=5
        )
        
        if response.status_code == 200:
            print("✅ Mensagem enviada! Verifique seu Telegram.\n")
        else:
            print(f"❌ Erro ao enviar: {response.text}\n")
    
    except requests.RequestException as e:
        print(f"❌ Erro: {e}\n")


def save_config(chat_id):
    """Salva configuração em .env"""
    if not chat_id:
        return
    
    env_file = "/home/ubuntu/pessoal/options/.env"
    
    env_content = f"""# Configuração Telegram
TELEGRAM_TOKEN={TELEGRAM_TOKEN}
TELEGRAM_CHAT_ID={chat_id}

# Configuração do Servidor
MT5_SERVER_HOST=127.0.0.1
MT5_SERVER_PORT=8765
MT5_SERVER_OUTPUT_DIR=/home/ubuntu/pessoal/options/src/analytics/realtime

# Configuração de Inferência
CONFIDENCE_THRESHOLD=0.55
STRANGLE_THRESHOLD=0.40
ENABLE_TELEGRAM=true
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Configuração salva em: {env_file}\n")


if __name__ == "__main__":
    chat_id = get_chat_id()
    
    if chat_id:
        test_notification(chat_id)
        save_config(chat_id)
        
        print("="*80)
        print("🎉 CONFIGURAÇÃO COMPLETA!")
        print("="*80)
        print(f"\nToken:  {TELEGRAM_TOKEN}")
        print(f"Chat ID: {chat_id}")
        print("\n✅ Sistema pronto para receber sinais em tempo real!")
        print("   Próximo passo: Rodar mt5_realtime_server.py + realtime_inference.py\n")
    else:
        print("\n❌ Não conseguimos configurar o Telegram")
        print("   Tente novamente mais tarde\n")
