#!/usr/bin/env python3
import json, os, time
from urllib.request import Request, urlopen

RELAY = os.environ.get("DASHBOARD_RELAY_URL", "").rstrip("/")
TOKEN = os.environ.get("DASHBOARD_RELAY_TOKEN", "")
INTERVAL = float(os.environ.get("DASHBOARD_RELAY_INTERVAL", "3"))

def get(url):
    try:
        with urlopen(url, timeout=2.5) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"ok": False, "error": str(e)}

def push(payload):
    if not RELAY:
        raise RuntimeError("DASHBOARD_RELAY_URL is not set")
    body = json.dumps(payload, ensure_ascii=False).encode()
    req = Request(RELAY + "/api/push", data=body, method="POST",
                  headers={"Content-Type": "application/json", "X-Relay-Token": TOKEN})
    with urlopen(req, timeout=4) as r:
        return json.loads(r.read().decode())

print("MT5 LiteFinance dashboard relay pusher started", flush=True)
while True:
    payload = {
        "mt5": get("http://127.0.0.1:8090/market"),
        "phone": get("http://127.0.0.1:8091/market"),
        "engine": get("http://127.0.0.1:8080/status"),
    }
    try:
        r = push(payload)
        print("RELAY_PUSH", r.get("ok"), flush=True)
    except Exception as e:
        print("RELAY_PUSH_ERROR", repr(e), flush=True)
    time.sleep(INTERVAL)
