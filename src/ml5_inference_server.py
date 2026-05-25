#!/usr/bin/env python3
"""
Servidor de Inferência com XGBoost - Recebe MQL5 → Retorna Decisão

Fluxo:
1. MQL5 envia POST com dados calculados
2. Python recebe → Valida
3. XGBoost faz predição
4. Retorna: BUY/SELL/HOLD + confiança
"""

import argparse
import json
import logging
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Optional

from core.ml5_processor import ML5DataProcessor, REQUIRED_FIELDS


# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


def build_handler(processor: ML5DataProcessor):
    """Constrói handler HTTP para receber dados MQL5."""
    
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, code: int, payload: dict) -> None:
            """Envia resposta JSON."""
            body = json.dumps(payload, ensure_ascii=True, indent=2).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        
        def log_message(self, format, *args):
            """Suprime logs automáticos."""
            pass
        
        def do_POST(self) -> None:
            """Recebe POST do MQL5."""
            
            # Validar rota
            if self.path != "/ml5/predict":
                self._send_json(404, {
                    "error": "not_found",
                    "message": "Use /ml5/predict"
                })
                return
            
            # Ler payload
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if length <= 0:
                    self._send_json(400, {"error": "empty_body"})
                    return
                
                raw = self.rfile.read(length)
                payload = json.loads(raw.decode("utf-8"))
            
            except ValueError as e:
                logger.error(f"JSON inválido: {e}")
                self._send_json(400, {"error": "invalid_json"})
                return
            
            except Exception as e:
                logger.error(f"Erro ao ler payload: {e}")
                self._send_json(400, {"error": "read_error"})
                return
            
            # Processar com XGBoost
            try:
                result = processor.predict(payload)
                logger.info(
                    f"{payload.get('symbol', 'UNKNOWN')} "
                    f"{payload.get('datetime', 'UNKNOWN')}: "
                    f"{result['decision']} (conf: {result['confidence']:.0%})"
                )
                self._send_json(200, result)
            
            except Exception as e:
                logger.error(f"Erro ao processar: {e}")
                self._send_json(500, {
                    "error": "processing_error",
                    "message": str(e)
                })
        
        def do_GET(self) -> None:
            """Health check."""
            if self.path == "/health":
                self._send_json(200, {"status": "ok", "timestamp": datetime.now().isoformat()})
            else:
                self._send_json(404, {"error": "not_found"})
    
    return Handler


def main():
    parser = argparse.ArgumentParser(
        description="Servidor de Inferência ML5 com XGBoost",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXEMPLOS:

  # Iniciar servidor na porta 9998
  python3 src/ml5_inference_server.py

  # Com modelo custom
  python3 src/ml5_inference_server.py --model /path/to/model.pkl

  # Debugar verbose
  python3 src/ml5_inference_server.py --verbose

ENDPOINT:
  POST http://localhost:9998/ml5/predict
  
  Request:
    {
      "symbol": "EURUSD",
      "datetime": "2026-05-25 15:45:00",
      "m15_trend": "UP",
      ... (todos os campos)
    }
  
  Response:
    {
      "decision": "BUY",
      "confidence": 0.85,
      "reasoning": "✅ CONFLUÊNCIA: M15 UP = H4 UP | ...",
      "features": {...},
      "xgb_score": 0.92,
      "timestamp": "2026-05-25T15:45:00.123456"
    }

TEST:
  curl -X POST http://localhost:9998/ml5/predict \
    -H "Content-Type: application/json" \
    -d @test_payload.json
        """
    )
    
    parser.add_argument("--host", default="0.0.0.0", help="Host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=9998, help="Port (default: 9998)")
    parser.add_argument("--model", type=str, help="Modelo XGBoost custom")
    parser.add_argument("--verbose", action="store_true", help="Logs verbose")
    
    args = parser.parse_args()
    
    # Carregar processor
    print("\n" + "="*80)
    print("🚀 SERVIDOR DE INFERÊNCIA ML5 COM XGBOOST")
    print("="*80)
    
    processor = ML5DataProcessor(model_path=args.model, verbose=args.verbose)
    
    # Validar que tem modelo
    if processor.xgb_model is None:
        print("\n⚠️  AVISO: Sem modelo XGBoost!")
        print("   Usando fallback: confluência + regime")
        print("   Para usar XGBoost, treine um modelo em:")
        print("   /home/ubuntu/pessoal/options/models/xgboost_model.pkl")
    
    # Iniciar servidor
    handler = build_handler(processor)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    
    print(f"\n📡 Escutando em: http://{args.host}:{args.port}")
    print(f"📍 Endpoint: POST /ml5/predict")
    print(f"🏥 Health: GET /health")
    print("\n" + "="*80)
    print("Pressione Ctrl+C para parar")
    print("="*80 + "\n")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\n🛑 Servidor parado.")
        server.shutdown()


if __name__ == "__main__":
    main()
