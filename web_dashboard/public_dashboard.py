#!/usr/bin/env python3
import json, os, time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8787"))
STATE = {"updated": 0, "trading": "DISABLED", "engine": {}, "mt5": {}, "phone": {}}

HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>XChief AI Monitor</title><style>body{margin:0;padding:18px;background:#0d1117;color:#eee;font-family:Arial,sans-serif}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px}.card{background:#161b22;border:1px solid #30363d;border-radius:12px;padding:16px}.v{margin-top:9px;font-size:20px;font-weight:bold}.ok{color:#3fb950}.bad{color:#f85149}.wait{color:#d29922}pre{white-space:pre-wrap;word-break:break-word}</style></head><body><h1>🤖 XChief AI Monitor</h1><div class="grid"><div class="card"><b>AI ENGINE</b><div id="e" class="v">...</div></div><div class="card"><b>MT5</b><div id="m" class="v">...</div></div><div class="card"><b>PHONE FEED</b><div id="p" class="v">...</div></div><div class="card"><b>TRADING</b><div id="t" class="v">DISABLED</div></div></div><div class="card" style="margin-top:14px"><b>LIVE STATUS</b><pre id="raw">Loading...</pre></div><script>async function refresh(){try{let x=await (await fetch('/api/status',{cache:'no-store'})).json(),e=x.engine||{},m=x.mt5||{},p=x.phone||{};let E=document.getElementById('e'),M=document.getElementById('m'),P=document.getElementById('p');E.textContent=e.ok?'ONLINE':'OFFLINE';E.className='v '+(e.ok?'ok':'bad');M.textContent=m.connected?'CONNECTED':'WAITING FOR EA';M.className='v '+(m.connected?'ok':'wait');P.textContent=p.connected?'ONLINE':'OFFLINE';P.className='v '+(p.connected?'ok':'bad');document.getElementById('t').textContent=x.trading||'DISABLED';document.getElementById('raw').textContent=JSON.stringify(x,null,2)}catch(e){document.getElementById('raw').textContent=String(e)}}refresh();setInterval(refresh,3000);</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def reply(self, obj, code=200):
        data=json.dumps(obj,ensure_ascii=False).encode(); self.send_response(code); self.send_header('Content-Type','application/json; charset=utf-8'); self.send_header('Cache-Control','no-store'); self.end_headers(); self.wfile.write(data)
    def do_GET(self):
        if self.path == '/health': self.reply({'ok':True,'service':'XChief AI Web Dashboard','trading':'DISABLED'}); return
        if self.path == '/api/status': self.reply(dict(STATE)); return
        if self.path == '/' or self.path.startswith('/?'):
            data=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.end_headers(); self.wfile.write(data); return
        self.reply({'ok':False,'error':'not found'},404)
    def do_POST(self):
        if self.path != '/api/push': self.reply({'ok':False,'error':'not found'},404); return
        try:
            n=int(self.headers.get('Content-Length','0')); body=json.loads(self.rfile.read(n) or b'{}')
            STATE.update(body); STATE['updated']=time.time(); STATE['trading']='DISABLED'
            self.reply({'ok':True,'updated':STATE['updated']})
        except Exception as e: self.reply({'ok':False,'error':str(e)},400)
    def log_message(self,*a): pass

if __name__ == '__main__': ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
