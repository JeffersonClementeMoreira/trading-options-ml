#!/usr/bin/env python3
"""
EXECUTOR DO SISTEMA COMPLETO DE TEMPO REAL

Integra:
1. Servidor HTTP (recebe dados de MQ5)
2. Monitor de JSONs (detecta novos candles)
3. Inference Engine (gera sinais)
4. Telegram (envia notificações)

Execução:
    python3 realtime_executor.py
    
Então MQ5 envia dados para: http://127.0.0.1:8765/mt5/candle
"""

import os
import sys
import json
import threading
import time
from pathlib import Path
from datetime import datetime
from collections import defaultdict

# Adiciona src ao path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mt5_realtime_server import parse_args, build_handler
from http.server import ThreadingHTTPServer

try:
    from realtime_inference import RealtimeInferenceEngine
    from telegram_notifier import TelegramNotifier
    HAS_INFERENCE = True
except ImportError as e:
    print(f"⚠️  Não conseguiu importar inference: {e}")
    HAS_INFERENCE = False


# ═══════════════════════════════════════════════════════════════════════════════
# MONITOR DE JSONS (detecta novos candles)
# ═══════════════════════════════════════════════════════════════════════════════

class RealtimeJSONMonitor:
    """Monitora pasta de JSONs e processa novos candles"""
    
    def __init__(self, watch_dir: Path, inference_engine=None):
        self.watch_dir = Path(watch_dir)
        self.inference_engine = inference_engine
        self.last_processed = defaultdict(lambda: "")
        self.running = False
        self.thread = None
    
    def start(self):
        """Inicia monitor em thread separada"""
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        print(f"✅ Monitor iniciado: {self.watch_dir}")
    
    def stop(self):
        """Para monitor"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _monitor_loop(self):
        """Loop que monitora JSONs"""
        while self.running:
            try:
                # Processa todos os latest_*.json
                for json_file in self.watch_dir.glob("latest_*.json"):
                    try:
                        content = json_file.read_text()
                        
                        # Se mudou desde última vez, processa
                        if content != self.last_processed[json_file.name]:
                            self.last_processed[json_file.name] = content
                            
                            payload = json.loads(content)
                            self._process_candle(payload)
                    
                    except Exception as e:
                        print(f"⚠️  Erro lendo {json_file.name}: {e}")
                
                time.sleep(0.5)  # Verifica a cada 500ms
            
            except Exception as e:
                print(f"⚠️  Erro no monitor: {e}")
                time.sleep(1)
    
    def _process_candle(self, payload: dict):
        """Processa um novo candle"""
        symbol = payload.get("symbol", "?")
        timeframe = payload.get("timeframe", "?")
        datetime_str = payload.get("datetime", "?")
        
        # Log
        close = payload.get("close", "?")
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {symbol} {timeframe} {datetime_str} @ {close}")
        
        # Inferência
        if self.inference_engine and HAS_INFERENCE:
            try:
                signal = self.inference_engine.infer(
                    symbol=symbol,
                    timeframe=timeframe,
                    datetime_str=datetime_str,
                    features={
                        k: payload.get(k, 0)
                        for k in [
                            "open", "high", "low", "close",
                            "mt5_er_mean", "mt5_kama_slope", "mt5_flow_score",
                            "mt5_regime", "mt5_realized_vol", "mt5_expected_move",
                            "mt5_atr_pct", "mt5_sweep_top", "mt5_sweep_bottom",
                            "mt5_ret_1", "mt5_ret_3", "mt5_dist_mean",
                        ]
                    }
                )
                
                if signal:
                    print(f"   📊 {signal}")
            
            except Exception as e:
                print(f"   ⚠️  Erro na inferência: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    """Executa sistema completo"""
    
    print("\n" + "="*80)
    print("🚀 SISTEMA DE TRADING EM TEMPO REAL - INICIALIZANDO")
    print("="*80 + "\n")
    
    # Configuração
    output_dir = Path("/home/ubuntu/pessoal/options/src/analytics/realtime")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    host = os.getenv("MT5_SERVER_HOST", "127.0.0.1")
    port = int(os.getenv("MT5_SERVER_PORT", "8765"))
    
    # Carrega env vars
    telegram_token = os.getenv("TELEGRAM_TOKEN")
    telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID")
    
    if telegram_token and telegram_chat_id:
        print(f"✅ Telegram configurado (chat: {telegram_chat_id})")
    else:
        print("⚠️  Telegram não configurado - rode setup_telegram.py")
    
    # Carrega inference engine
    inference_engine = None
    if HAS_INFERENCE:
        try:
            model_dir = Path(__file__).parent / "models"
            inference_engine = RealtimeInferenceEngine(
                model_dir_path=model_dir,
                telegram_enabled=True
            )
            print(f"✅ Inference engine carregado")
        except Exception as e:
            print(f"⚠️  Não conseguiu carregar inference: {e}")
            inference_engine = None
    
    # Inicia servidor HTTP
    print(f"\n📡 Iniciando servidor HTTP em {host}:{port}/mt5/candle")
    handler = build_handler(output_dir=output_dir, enable_audit_log=True)
    server = ThreadingHTTPServer((host, port), handler)
    
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"✅ Servidor rodando")
    
    # Inicia monitor de JSONs
    print(f"\n👁️  Monitorando: {output_dir}")
    monitor = RealtimeJSONMonitor(watch_dir=output_dir, inference_engine=inference_engine)
    monitor.start()
    
    print("\n" + "="*80)
    print("🎉 SISTEMA PRONTO!")
    print("="*80)
    print(f"""
    Aguardando dados de MQ5...
    
    MQ5 deve enviar para: http://{host}:{port}/mt5/candle
    
    Dados ficarão em: {output_dir}
    
    Pressione Ctrl+C para parar
    """)
    
    # Loop principal
    try:
        while True:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n⏹️  Parando sistema...")
        monitor.stop()
        server.shutdown()
        print("✅ Sistema parado")


if __name__ == "__main__":
    main()
