#!/usr/bin/env python3
import json, os, time, sys
from pathlib import Path
from urllib.request import urlopen
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT=int(os.environ.get("PORT","10000"))
STATE={"updated":0,"trading":"DISABLED","engine":{"ok":False},"mt5":{"connected":False,"source":"waiting"},"phone":{"decision":"WAIT"}}
ACCOUNT_FILE=Path(os.environ.get("ACCOUNT_FILE",str(Path.home()/"MT5"/"account_demo.json")))

def fetch(url):
    try:
        with urlopen(url,timeout=2.5) as r: return json.loads(r.read().decode())
    except Exception as e: return {"ok":False,"error":str(e)}

def load_account():
    try: return json.loads(ACCOUNT_FILE.read_text())
    except Exception: return {"mode":"DEMO","login":"","server":"","password_set":False}

def save_account(d):
    safe={"mode":d.get("mode","DEMO"),"login":str(d.get("login","")).strip(),"server":str(d.get("server","")).strip(),"password_set":bool(d.get("password_set",False))}
    ACCOUNT_FILE.parent.mkdir(parents=True,exist_ok=True)
    ACCOUNT_FILE.write_text(json.dumps(safe,ensure_ascii=False)); ACCOUNT_FILE.chmod(0o600)
    return safe

def live_state():
    # On Render, MT5/Android data arrives through /api/push.
    if STATE.get("updated"):
        return STATE
    e=fetch("http://127.0.0.1:8080/health")
    m=fetch("http://127.0.0.1:8090/market")
    p=fetch("http://127.0.0.1:8091/market")
    return {"updated":time.time(),"trading":"DISABLED","engine":e,"mt5":m,"phone":p}

HTML=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"><meta name="theme-color" content="#0a0f16"><title>MT5 Mobile Pro</title><style>
:root{--bg:#080c12;--panel:#10161f;--panel2:#151d27;--line:#26313d;--text:#f5f7fa;--muted:#84909d;--blue:#4c9aff;--green:#35d07f;--red:#ff5d6c;--amber:#f5c451}*{box-sizing:border-box}body{margin:0;background:radial-gradient(900px 500px at 50% -180px,#16263a 0,#080c12 65%);color:var(--text);font:14px system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}main{max-width:540px;margin:auto;padding:16px 14px 30px}.top{display:flex;justify-content:space-between;align-items:center;margin-bottom:14px}.brand{font-size:21px;font-weight:850;letter-spacing:-.5px}.sub{font-size:11px;color:var(--muted);margin-top:3px}.pill{padding:7px 10px;border:1px solid var(--line);border-radius:99px;background:#101721;font-size:10px;font-weight:850;letter-spacing:.5px}.dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:var(--red);margin-right:6px;box-shadow:0 0 8px currentColor}.online .dot{background:var(--green)}.hero{position:relative;overflow:hidden;background:linear-gradient(150deg,#162331,#0e141c 70%);border:1px solid #2b3948;border-radius:24px;padding:21px 18px;text-align:center;box-shadow:0 18px 45px #0008}.hero:after{content:"";position:absolute;inset:auto -30% -80%;height:180px;background:#4c9aff12;border-radius:50%}.symbol{position:relative;z-index:1;font-size:11px;color:#a9b5c2;letter-spacing:2px;font-weight:750}.price{position:relative;z-index:1;font-size:44px;font-weight:900;letter-spacing:-2px;margin:3px 0 7px}.signal{position:relative;z-index:1;display:inline-block;min-width:105px;padding:9px 20px;border-radius:13px;background:#1d2733;border:1px solid #354352;font-size:18px;font-weight:900}.mini{font-size:11px;color:var(--muted);margin-top:7px}.row{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}.card{background:linear-gradient(145deg,var(--panel2),var(--panel));border:1px solid var(--line);border-radius:17px;padding:14px}.label{font-size:10px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;font-weight:700}.value{font-size:20px;font-weight:820;margin-top:5px;overflow:hidden;text-overflow:ellipsis}.section{margin-top:12px}.bar{display:flex;justify-content:space-between;align-items:center;margin-bottom:9px}.bar b{font-size:12px;letter-spacing:.5px}.status{font-size:10px;font-weight:800;color:var(--amber)}.reason{line-height:1.55;color:#cbd5df}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:9px}.metric{padding:11px;border-radius:12px;background:#0d131b;border:1px solid #202a35}.metric span{display:block;color:var(--muted);font-size:10px}.metric strong{display:block;margin-top:3px;font-size:14px}.form{display:grid;gap:8px}input,select,button{width:100%;padding:12px;border-radius:11px;border:1px solid #303c49;background:#0b1118;color:#fff;outline:none}button{background:#2563eb;border:0;font-weight:850}button:active{transform:scale(.99)}.danger{color:var(--amber);font-size:10px;font-weight:800}.raw{font:9px ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap;word-break:break-word;color:#758290;max-height:100px;overflow:auto}.footer{text-align:center;color:#5f6b77;font-size:10px;margin-top:16px}.good{color:var(--green)}.bad{color:var(--red)}
</style></head><body><main>
<div class="top"><div><div class="brand">MT5 Mobile Pro</div><div class="sub" id="server">Checking MT5…</div></div><div id="conn" class="pill"><span class="dot"></span>OFFLINE</div></div>
<div class="hero"><div class="symbol" id="sym">EURUSD</div><div class="price" id="price">—</div><div id="signal" class="signal">WAIT</div><div class="mini" id="time">Waiting for MT5 EA</div></div>
<div class="row"><div class="card"><div class="label">Balance</div><div class="value" id="bal">—</div></div><div class="card"><div class="label">Equity</div><div class="value" id="eq">—</div></div><div class="card"><div class="label">Free Margin</div><div class="value" id="fm">—</div></div><div class="card"><div class="label">Profit / Loss</div><div class="value" id="pl">—</div></div></div>
<div class="row"><div class="card"><div class="label">Positions</div><div class="value" id="pos">—</div></div><div class="card"><div class="label">Account</div><div class="value" id="login">—</div><div class="mini" id="currency">—</div></div></div>
<div class="section card"><div class="bar"><b>AI SIGNAL</b><span id="engine" class="status">AI + RISK</span></div><div class="metrics"><div class="metric"><span>Score</span><strong id="score">—</strong></div><div class="metric"><span>Risk</span><strong id="risk">—</strong></div><div class="metric"><span>Stop Loss</span><strong id="sl">—</strong></div><div class="metric"><span>Take Profit</span><strong id="tp">—</strong></div></div><div class="reason" id="reason" style="margin-top:10px">Waiting for live MT5 data…</div></div>
<div class="section card"><div class="bar"><b>ACCOUNT CONNECTION</b><span class="danger">LIVE ORDERS LOCKED</span></div><div class="form"><select id="mode"><option>DEMO</option><option>LIVE</option></select><input id="loginIn" placeholder="Login"><input id="srv" placeholder="Server"><input id="pw" type="password" placeholder="Password (not stored)"><button id="connect">CONNECT DEMO</button><div class="mini" id="msg"></div></div></div>
<div class="section card"><div class="bar"><b>DATA SOURCE</b><span class="mini" id="source">—</span></div><div class="metrics"><div class="metric"><span>Bid</span><strong id="bid">—</strong></div><div class="metric"><span>Ask</span><strong id="ask">—</strong></div></div><div class="raw" id="raw"></div></div><div class="footer">Android local • 3s refresh • Real trading disabled</div></main>
<script>
const $=id=>document.getElementById(id);const f=(v,c='')=>v==null?'—':(typeof v==='number'?v.toFixed(2):v)+(c?' '+c:'');
async function refresh(){try{let x=await(await fetch('/api/status',{cache:'no-store'})).json(),m=x.mt5||{},p=x.phone||{},c=!!m.connected&&m.source==='MT5 EA';$('conn').innerHTML='<span class="dot"></span>'+(c?'CONNECTED':'OFFLINE');$('conn').className='pill '+(c?'online':'');$('server').textContent=m.server||'LiteFinance-MT5-Demo';$('sym').textContent=m.symbol||p.symbol||'EURUSD';$('price').textContent=f(m.price??m.bid??p.price);$('bal').textContent=f(m.balance,m.currency||'');$('eq').textContent=f(m.equity,m.currency||'');$('fm').textContent=f(m.freeMargin,m.currency||'');$('pl').textContent=f(m.profit,m.currency||'');$('pos').textContent=m.positions??'—';$('login').textContent=m.login??'—';$('currency').textContent=m.currency||'—';$('bid').textContent=f(m.bid);$('ask').textContent=f(m.ask);$('source').textContent=m.source||'—';$('time').textContent=c?'MT5 EA • live account data':'MT5 EA not reporting • market fallback';$('signal').textContent=p.decision||'WAIT';$('score').textContent=p.score==null?'—':p.score;$('risk').textContent=p.riskPercent==null?'—':p.riskPercent+'%';$('reason').textContent=p.reason||'Waiting for AI signal';$('sl').textContent=p.stopLoss??'—';$('tp').textContent=p.takeProfit??'—';$('engine').textContent=p.engine||'AI + RISK';$('raw').textContent=JSON.stringify({mt5:m,ai:p},null,2)}catch(e){$('raw').textContent=String(e)}}refresh();setInterval(refresh,3000);
fetch('/api/account').then(r=>r.json()).then(a=>{$('mode').value=a.mode||'DEMO';$('loginIn').value=a.login||'';$('srv').value=a.server||''});$('connect').onclick=async()=>{if($('mode').value!=='DEMO'){$('msg').textContent='LIVE is locked';return}$('msg').textContent='Connecting…';let r=await fetch('/api/connect',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({mode:'DEMO',login:$('loginIn').value,server:$('srv').value,password:$('pw').value})});let x=await r.json();$('msg').textContent=x.ok?'Connection started — verifying MT5…':(x.error||'Connection failed');$('pw').value='';setTimeout(refresh,5000)};
</script></body></html>'''

class Handler(BaseHTTPRequestHandler):
    def reply(self,obj,code=200):
        b=json.dumps(obj,ensure_ascii=False).encode();self.send_response(code);self.send_header('Content-Type','application/json; charset=utf-8');self.send_header('Cache-Control','no-store');self.end_headers();self.wfile.write(b)
    def do_GET(self):
        if self.path=='/health': return self.reply({'ok':True,'service':'MT5 Web Monitor','trading':'DISABLED'})
        if self.path=='/api/account': return self.reply(load_account())
        if self.path=='/api/status': return self.reply(live_state())
        if self.path=='/' or self.path.startswith('/?'):
            b=HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.end_headers();self.wfile.write(b);return
        self.reply({'ok':False,'error':'not found'},404)
    def do_POST(self):
        global STATE
        try:
            n=int(self.headers.get('Content-Length','0')); d=json.loads(self.rfile.read(n) or b'{}')
            if self.path=='/api/push':
                token=os.environ.get('RELAY_TOKEN','')
                if token and self.headers.get('X-Relay-Token')!=token: return self.reply({'ok':False,'error':'unauthorized'},401)
                if not isinstance(d,dict): return self.reply({'ok':False,'error':'invalid state'},400)
                d['updated']=time.time(); d['trading']='DISABLED'; STATE=d
                return self.reply({'ok':True,'updated':STATE['updated']})
            if self.path=='/api/account': return self.reply({'ok':True,'account':save_account(d)})
            if self.path=='/api/connect':
                if d.get('mode','DEMO')!='DEMO': return self.reply({'ok':False,'error':'LIVE connection is locked during testing'},403)
                from mt5_connect import connect
                r=connect(d.get('login'),d.get('server'),d.get('password'))
                if r.get('ok'): save_account({**d,'password_set':True})
                return self.reply(r)
            self.reply({'ok':False,'error':'not found'},404)
        except Exception as e: self.reply({'ok':False,'error':str(e)},400)
    def log_message(self,*a): pass

if __name__=='__main__': ThreadingHTTPServer(('0.0.0.0',PORT),Handler).serve_forever()
