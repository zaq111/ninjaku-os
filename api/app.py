#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/ninjaku")

from flask import Flask, jsonify
from lib.modules import execute

app = Flask(__name__)

def ok(data=None):
    return jsonify({"ok": True, "data": data or {}})

def fail(error, code=500):
    return jsonify({"ok": False, "error": str(error)}), code

@app.get("/api/status")
def api_status():
    try:
        return ok(execute("system", "status"))
    except Exception as e:
        return fail(e)

@app.get("/api/router")
def api_router():
    try:
        return ok(execute("router", "status"))
    except Exception as e:
        return fail(e)

@app.post("/api/router/enable")
def api_router_enable():
    try:
        return ok(execute("router", "enable"))
    except Exception as e:
        return fail(e)

@app.post("/api/router/disable")
def api_router_disable():
    try:
        return ok(execute("router", "disable"))
    except Exception as e:
        return fail(e)

@app.get("/api/firewall")
def api_firewall():
    try:
        return ok(execute("firewall", "status"))
    except Exception as e:
        return fail(e)

@app.get("/api/devices")
def api_devices():
    try:
        return ok(execute("devices", "status"))
    except Exception as e:
        return fail(e)

@app.get("/api/profiles")
def api_profiles():
    try:
        return ok(execute("profiles", "status"))
    except Exception as e:
        return fail(e)

@app.get("/api/policy")
def api_policy():
    try:
        return ok(execute("policy", "status"))
    except Exception as e:
        return fail(e)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8181)
