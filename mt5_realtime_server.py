#!/usr/bin/env python3
"""Lightweight MT5 realtime ingestion server.

Receives one-candle JSON payloads from MQL5 WebRequest and stores:
- latest per symbol/timeframe JSON
- append-only NDJSON audit log (optional)
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


REQUIRED_FIELDS = {
    "symbol",
    "timeframe",
    "datetime",
    "open",
    "high",
    "low",
    "close",
    "mt5_er_mean",
    "mt5_kama_slope",
    "mt5_flow_score",
    "mt5_regime",
    "mt5_realized_vol",
    "mt5_expected_move",
    "mt5_atr_pct",
    "mt5_sweep_top",
    "mt5_sweep_bottom",
    "mt5_ret_1",
    "mt5_ret_3",
    "mt5_dist_mean",
}


def _safe_key(value: str) -> str:
    return "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)


def build_handler(output_dir: Path, enable_audit_log: bool):
    class Handler(BaseHTTPRequestHandler):
        def _send_json(self, code: int, payload: dict) -> None:
            body = json.dumps(payload, ensure_ascii=True).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self) -> None:  # noqa: N802
            if self.path != "/mt5/candle":
                self._send_json(404, {"ok": False, "error": "not_found"})
                return

            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                self._send_json(400, {"ok": False, "error": "invalid_content_length"})
                return

            raw = self.rfile.read(max(length, 0))
            try:
                payload = json.loads(raw.decode("utf-8"))
            except Exception:
                self._send_json(400, {"ok": False, "error": "invalid_json"})
                return

            if not isinstance(payload, dict):
                self._send_json(400, {"ok": False, "error": "payload_must_be_object"})
                return

            missing = sorted(REQUIRED_FIELDS - set(payload.keys()))
            if missing:
                self._send_json(400, {"ok": False, "error": "missing_fields", "missing": missing})
                return

            symbol = _safe_key(str(payload.get("symbol", "UNKNOWN")))
            timeframe = _safe_key(str(payload.get("timeframe", "UNKNOWN")))
            payload["received_utc"] = datetime.now(timezone.utc).isoformat()

            output_dir.mkdir(parents=True, exist_ok=True)
            latest_file = output_dir / f"latest_{symbol}_{timeframe}.json"
            latest_file.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")

            if enable_audit_log:
                audit_file = output_dir / f"stream_{symbol}_{timeframe}.ndjson"
                with audit_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(payload, ensure_ascii=True) + "\n")

            print(
                f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] "
                f"{symbol} {timeframe} {payload.get('datetime')} close={payload.get('close')}"
            )
            self._send_json(200, {"ok": True})

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    return Handler


def parse_args() -> argparse.Namespace:
    default_output = str((Path(__file__).resolve().parent / "analytics" / "realtime"))
    parser = argparse.ArgumentParser(description="MT5 realtime ingestion server")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--output-dir", default=default_output)
    parser.add_argument("--no-audit-log", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    output_dir = Path(args.output_dir).expanduser().resolve()
    handler = build_handler(output_dir=output_dir, enable_audit_log=not args.no_audit_log)
    server = ThreadingHTTPServer((args.host, args.port), handler)

    print(f"MT5 realtime server listening on http://{args.host}:{args.port}/mt5/candle")
    print(f"Output dir: {output_dir}")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
