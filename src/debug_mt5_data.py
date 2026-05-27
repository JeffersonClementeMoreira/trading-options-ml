#!/usr/bin/env python3
"""
Debug script to monitor what data is arriving from MT5
Shows each candle with source IP and exact JSON
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread
import sys

class DebugHTTPHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        """Handle incoming POST requests"""
        if self.path == "/mt5/candle":
            # Read content length
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body.decode('utf-8'))
                
                print("\n" + "="*80)
                print(f"[DATA RECEIVED] from {self.client_address[0]}")
                print("="*80)
                print(f"Symbol:    {data.get('symbol')}")
                print(f"DateTime:  {data.get('datetime')}")
                print(f"Open:      {data.get('open')}")
                print(f"High:      {data.get('high')}")
                print(f"Low:       {data.get('low')}")
                print(f"Close:     {data.get('close')}")
                print(f"Volume:    {data.get('volume')}")
                print("="*80)
                print(f"Raw JSON: {body.decode('utf-8')}")
                print("="*80 + "\n")
                
                # Return OK response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"ok": true}')
                
            except Exception as e:
                print(f"[ERROR] Failed to parse JSON: {e}")
                self.send_response(400)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def start_debug_server(port=8766):
    """Start debug HTTP server on different port to avoid conflicts"""
    server = HTTPServer(('127.0.0.1', port), DebugHTTPHandler)
    print(f"[DEBUG SERVER] Listening on http://127.0.0.1:{port}")
    print("[DEBUG SERVER] Waiting for MT5 data...")
    print("[DEBUG SERVER] Configure MT5's SendCandlesToServer.mq5 to send to:")
    print(f"               http://127.0.0.1:{port}/mt5/candle")
    print("")
    
    server.serve_forever()


if __name__ == "__main__":
    try:
        start_debug_server(8766)
    except KeyboardInterrupt:
        print("\n[DEBUG SERVER] Stopped")
        sys.exit(0)
