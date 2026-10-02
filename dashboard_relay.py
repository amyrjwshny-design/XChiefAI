#!/usr/bin/env python3
import json
import os
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from web_dashboard.public_dashboard import HTML as BASE_HTML

HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", "10000"))
TOKEN = os.environ.get("RELAY_TOKEN", "").strip()

STATE = {
    "updated": 0,
    "mt5": {"connected": False, "broker": "LiteFinance / MT5", "trading": "DISABLED"},
    "phone": {"ok": False, "trading": "DISABLED"},
    "engine": {"ok": False, "trading": "DISABLED"},
}
LOCK = threading.Lock()

HTML = BASE_HTML.replace(
    "<title>MT5 Mobile Pro</title>",
    "<title>MT5 LiteFinance Web Dashboard</title>"
).replace(
    "MT5 Mobile Pro",
    "MT5 LiteFinance Web Dashboard"
).replace(
    '<div class="section card"><div class="bar"><b>ACCOUNT CONNECTION</b>',
    '<div class="section card" style="display:none"><div class="bar"><b>ACCOUNT CONNECTION</b>'
).replace(
    "Android local • 3s refresh • Real trading disabled",
    "Remote relay • 3s refresh • Real trading disabled"
)

def allowed(h):
    return (not TOKEN) or h.get("X-Relay-Token", "") == TOKEN

def reply(h, obj, code=200):
    raw = json.dumps(obj, ensure_ascii=False).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json; charset=utf-8")
    h.send_header("Cache-Control", "no-store")
    h.send_header("Content-Length", str(len(raw)))
    h.end_headers()
    h.wfile.write(raw)

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_GET(self):
        if self.path == "/health":
            with LOCK:
                age = int(time.time() - STATE["updated"]) if STATE["updated"] else None
            return reply(self, {
                "ok": True,
                "service": "MT5 LiteFinance Web Relay",
                "trading": "DISABLED",
                "data_age_seconds": age,
                "data_connected": bool(age is not None and age <= 15),
            })
        if self.path == "/api/status":
            with LOCK:
                s = json.loads(json.dumps(STATE))
            s["updated"] = STATE["updated"]
            return reply(self, s)
        if self.path == "/" or self.path.startswith("/?"):
            raw = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)
            return
        return reply(self, {"ok": False, "error": "not_found"}, 404)

    def do_POST(self):
        if self.path != "/api/push":
            return reply(self, {"ok": False, "error": "not_found"}, 404)
        if not allowed(self.headers):
            return reply(self, {"ok": False, "error": "unauthorized"}, 401)
        try:
            n = int(self.headers.get("Content-Length", "0"))
            data = json.loads(self.rfile.read(n) or b"{}")
            if not isinstance(data, dict):
                raise ValueError("payload must be an object")
            mt5 = data.get("mt5") if isinstance(data.get("mt5"), dict) else {}
            phone = data.get("phone") if isinstance(data.get("phone"), dict) else {}
            engine = data.get("engine") if isinstance(data.get("engine"), dict) else {}
            with LOCK:
                STATE["mt5"] = mt5
                STATE["phone"] = phone
                STATE["engine"] = engine
                STATE["updated"] = int(time.time())
            return reply(self, {"ok": True, "accepted": True, "trading": "DISABLED"})
        except Exception as e:
            return reply(self, {"ok": False, "error": str(e)}, 400)

if __name__ == "__main__":
    print(f"MT5 LiteFinance Web Relay listening on 0.0.0.0:{PORT}", flush=True)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
