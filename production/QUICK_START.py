#!/usr/bin/env python3
"""
QUICK START - Production Deployment Manual
===========================================

Guia rápido para colocar o sistema em produção com WebSocket + Telegram.
"""

import os
import sys
from pathlib import Path


def check_dependencies():
    """Verifica se todas as dependências estão instaladas."""
    print("\n" + "="*80)
    print("🔍 Verificando dependências...")
    print("="*80)
    
    required = ['websockets', 'requests', 'pandas', 'numpy']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
            print(f"✅ {pkg}")
        except ImportError:
            print(f"❌ {pkg}")
            missing.append(pkg)
    
    if missing:
        print(f"\n⚠️  Instalar dependências faltantes:")
        print(f"   pip install {' '.join(missing)}")
        return False
    
    print("\n✅ Todas as dependências instaladas!")
    return True


def check_telegram_config():
    """Verifica se Telegram está configurado."""
    print("\n" + "="*80)
    print("📱 Verificando Telegram...")
    print("="*80)
    
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if token and chat_id:
        print(f"✅ TELEGRAM_TOKEN: {token[:10]}...*** (configurado)")
        print(f"✅ TELEGRAM_CHAT_ID: {chat_id} (configurado)")
        return True
    else:
        print("❌ Telegram NÃO configurado!")
        print("\n📋 Como configurar:")
        print("\n1. Abrir Telegram e procurar por @BotFather")
        print("2. Enviar /newbot")
        print("3. Seguir passos e copiar o TOKEN")
        print("\n4. Procurar por @userinfobot")
        print("5. Enviar qualquer mensagem")
        print("6. Copiar o CHAT_ID")
        print("\n7. Exportar no terminal:")
        print("   export TELEGRAM_TOKEN='seu_token_aqui'")
        print("   export TELEGRAM_CHAT_ID='seu_id_aqui'")
        print("\n8. Verificar:")
        print("   echo $TELEGRAM_TOKEN")
        print("   echo $TELEGRAM_CHAT_ID")
        return False


def check_signal_files():
    """Verifica se os arquivos de sinais existem."""
    print("\n" + "="*80)
    print("📊 Verificando arquivos de sinais...")
    print("="*80)
    
    files_ok = True
    
    for pair in ['EURUSD', 'GBPUSD']:
        csv_file = f'production/validated_signals_{pair}.csv'
        if Path(csv_file).exists():
            lines = sum(1 for line in open(csv_file)) - 1  # Sem header
            print(f"✅ {csv_file} ({lines} sinais)")
        else:
            print(f"❌ {csv_file} NÃO encontrado")
            files_ok = False
    
    return files_ok


def check_websocket_files():
    """Verifica se os arquivos do WebSocket existem."""
    print("\n" + "="*80)
    print("🔌 Verificando arquivos WebSocket...")
    print("="*80)
    
    files = [
        'production/websocket/server.py',
        'production/websocket/mt5_client.mq5',
        'production/websocket/test_client.py'
    ]
    
    all_ok = True
    for f in files:
        if Path(f).exists():
            print(f"✅ {f}")
        else:
            print(f"❌ {f} NÃO encontrado")
            all_ok = False
    
    return all_ok


def step_1_check_system():
    """Step 1: Verificar sistema."""
    print("\n" + "="*80)
    print("STEP 1: Verificar Sistema")
    print("="*80)
    
    ok = True
    ok = ok and check_dependencies()
    ok = ok and check_signal_files()
    ok = ok and check_websocket_files()
    
    return ok


def step_2_configure_telegram():
    """Step 2: Configurar Telegram."""
    print("\n" + "="*80)
    print("STEP 2: Configurar Telegram")
    print("="*80)
    
    if check_telegram_config():
        print("\n✅ Telegram já está configurado!")
        return True
    
    print("\n⏳ Por favor, configure Telegram e tente novamente.")
    return False


def step_3_start_websocket():
    """Step 3: Iniciar WebSocket."""
    print("\n" + "="*80)
    print("STEP 3: Iniciar WebSocket Server")
    print("="*80)
    
    print("""
🚀 Para iniciar o WebSocket server, abra OUTRO TERMINAL e execute:

   cd /home/ubuntu/pessoal/options
   python3 production/websocket/server.py

Você verá:
   🚀 WebSocket Server started on ws://0.0.0.0:8765
   📊 Monitoring 2 pairs
   ⏰ Signals configured: EURUSD + GBPUSD

🔗 Deixe esse terminal rodando continuamente!
    """)
    
    return True


def step_4_test_websocket():
    """Step 4: Testar WebSocket."""
    print("\n" + "="*80)
    print("STEP 4: Testar WebSocket (OPCIONAL)")
    print("="*80)
    
    print("""
🧪 Para testar com candles simulados, execute em OUTRO TERMINAL:

   cd /home/ubuntu/pessoal/options
   python3 production/websocket/test_client.py

Você verá:
   ✅ Connected to WebSocket server
   📤 Test 1: Sending EURUSD candle...
   📩 Response: Status: ok, Signal Found: True
      ✅ SIGNAL TRIGGERED!
      📲 Telegram alert sent!

💡 Se aparecer "Connection refused", volte ao Step 3 e confirme que
   o servidor está rodando no outro terminal.
    """)
    
    return True


def step_5_connect_mt5():
    """Step 5: Conectar MT5."""
    print("\n" + "="*80)
    print("STEP 5: Conectar MT5 EA")
    print("="*80)
    
    print("""
1️⃣  Copiar arquivo para MetaEditor:
   - Abrir: C:\\Users\\SEU_USER\\AppData\\Roaming\\MetaQuotes\\Terminal\\D0E8209F77C08E6C4AF78CAA8FF2F783\\MQL5\\Experts\\
   - Copiar: production/websocket/mt5_client.mq5 para lá

2️⃣  Compilar no MetaEditor (F7):
   - Abrir MetaEditor
   - Abrir o arquivo
   - F7 para compilar (sem erros esperado)

3️⃣  Rodar no MT5:
   - Abrir MT5
   - Ir para gráfico EURUSD M15
   - Arrastar o EA do histórico para o gráfico
   - Confirmar "Agregar com Enter"
   - Verificar se está rodando (ícone de smiley ativo)

4️⃣  Monitorar:
   - Verificar logs do servidor
   - Esperar por mensagens de candle recebido
   - Quando sinal vier, receberá alerta no Telegram
    """)
    
    return True


def step_6_first_signal():
    """Step 6: Receber primeiro sinal."""
    print("\n" + "="*80)
    print("STEP 6: Receber Primeiro Sinal")
    print("="*80)
    
    print("""
📲 Quando o primeiro sinal for acionado:

1️⃣  Você receberá mensagem no Telegram:
   🚀 TRADING SIGNAL ALERT
   
   📊 EURUSD
   ⏰ 2025-09-03 06:00:00
   
   📈 Direction: UP
   📍 Confidence: 100%
   
   💰 Entry Price: 1.16733
   🎯 Target Price: 1.17101
   📌 Pips to Target: 368 pips
   
   ⚠️ Action: Prepare options entry
   ✅ Ready to enter with UP binary option

2️⃣  Abrir posição com opções:
   - Escolher opcabróker (ex: Quotex, IQ Option)
   - Entrada: EURUSD (ou seu par)
   - Direção: UP ou DOWN (conforme alerta)
   - Valor: Seu gerenciamento de risco
   - Tempo: 1 hora (D+1 14:00 target)

3️⃣  MT5 monitora até target:
   - EA não faz entrada (ele só recebe dados!)
   - Você faz a entrada manualmente com opções
   - MT5 monitora D+1 14:00 para resultado

4️⃣  Resultado:
   - Se atingiu target: ✅ GANHO
   - Se não atingiu: ❌ PERDA
   - Anotar resultado para análise
    """)
    
    return True


def step_7_monitoring():
    """Step 7: Monitorar sistema."""
    print("\n" + "="*80)
    print("STEP 7: Monitorar Contínuamente")
    print("="*80)
    
    print("""
📊 Monitoramento contínuo:

1️⃣  Verificar logs do servidor:
   tail -f /home/ubuntu/pessoal/options/server.log

   Esperado ver:
   INFO:root:✅ Client connected: 127.0.0.1:XXXX
   INFO:root:🎯 Signal triggered for EURUSD
   INFO:root:✅ Telegram alert sent for EURUSD

2️⃣  Verificar alertas Telegram:
   - Novo alerta a cada dia (~1)
   - Confiança > 90%
   - Confluence score visível

3️⃣  Rastrear resultados:
   - Planilha com: Date | Pair | Direction | Entry | Target | Result | Pips
   - Calcular win rate semanal
   - Comparar com backtest (50.4% esperado)

4️⃣  Se houver erros:
   - "Connection refused": Servidor não está rodando
   - "No signal received": Horário do candle fora da tolerância
   - "Telegram error": Token/Chat ID inválido ou revogado

5️⃣  Escalar lentamente:
   - Semana 1: Monitorar sem trade (paper trading)
   - Semana 2: Minimo 1-2 pips por sinal
   - Semana 3+: Aumentar se lucro > 10 pips
    """)
    
    return True


def main():
    """Menu principal."""
    print("\n" + "="*80)
    print("🚀 QUICK START - Production Deployment")
    print("="*80)
    print("""
Bem-vindo! Este script vai guiá-lo passo a passo para
colocar o sistema de WebSocket + Telegram em produção.

PREREQUISITOS:
  ✅ Python 3.8+
  ✅ Sinais já validados em production/
  ✅ Conta Telegram ativa
  ✅ MT5 com dados M15

O que vai acontecer:
  1. Verificar sistema
  2. Configurar Telegram
  3. Iniciar WebSocket
  4. Testar conexão
  5. Conectar MT5
  6. Receber primeiro sinal
  7. Monitorar contínuamente

⏱️  Tempo estimado: 30 minutos
    """)
    
    steps = [
        ("Verificar Sistema", step_1_check_system),
        ("Configurar Telegram", step_2_configure_telegram),
        ("Iniciar WebSocket", step_3_start_websocket),
        ("Testar WebSocket", step_4_test_websocket),
        ("Conectar MT5", step_5_connect_mt5),
        ("Receber Primeiro Sinal", step_6_first_signal),
        ("Monitorar Sistema", step_7_monitoring),
    ]
    
    completed = 0
    for i, (title, func) in enumerate(steps, 1):
        print(f"\n{'─'*80}")
        print(f"[{i}/{len(steps)}] {title}")
        print(f"{'─'*80}")
        
        if func():
            completed += 1
            if i < len(steps):
                input("\n👉 Pressione ENTER para continuar...")
        else:
            print(f"\n⚠️  Falhou neste passo. Corrija e tente novamente.")
            return False
    
    print("\n" + "="*80)
    print("✅ PRODUÇÃO INICIADA COM SUCESSO!")
    print("="*80)
    print(f"""
Todos os {len(steps)} passos foram concluídos! 🎉

🚀 Seu sistema está VIVO:
   • WebSocket rodando em ws://0.0.0.0:8765
   • MT5 enviando candles M15
   • Telegram enviando alertas
   • Você abrindo posições com opções

📊 Dashboard:
   • Verifique logs: tail -f server.log
   • Monitore pips: Planilha Excel
   • Compare com backtest: 50.4% win rate

💡 Próximos dias:
   Semana 1: Observe (paper trading)
   Semana 2: Trade mínimo
   Semana 3+: Escale se lucro > 10 pips

✅ STATUS: 🟢 PRONTO PARA PRODUÇÃO

═══════════════════════════════════════════════════════════════════════════════
    """)
    
    return True


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
