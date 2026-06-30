#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/ninjaku")

from flask import Flask, jsonify, request
from lib.modules import execute
from lib.settings import list_all, set as set_setting

app = Flask(__name__)

def ok(data=None):
    return jsonify({"ok": True, "data": data or {}})

def fail(error, code=500):
    return jsonify({"ok": False, "error": str(error)}), code

@app.get("/api/health")
def api_health():
    return ok({"service": "ninjaku-api", "status": "ok"})

@app.get("/api/status")
def api_status():
    try:
        return ok(execute("system", "status"))
    except Exception as e:
        return fail(e)

@app.get("/api/network")
def api_network():
    try:
        return ok(execute("network", "status"))
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

@app.post("/api/firewall/apply-policy")
def api_firewall_apply_policy():
    try:
        return ok(execute("firewall", "apply-policy"))
    except Exception as e:
        return fail(e)

@app.get("/api/dhcp")
def api_dhcp():
    try:
        return ok(execute("dhcp", "status"))
    except Exception as e:
        return fail(e)

@app.post("/api/dhcp/start")
def api_dhcp_start():
    try:
        return ok(execute("dhcp", "start"))
    except Exception as e:
        return fail(e)

@app.post("/api/dhcp/stop")
def api_dhcp_stop():
    try:
        return ok(execute("dhcp", "stop"))
    except Exception as e:
        return fail(e)

@app.get("/api/devices")
def api_devices():
    try:
        return ok(execute("devices", "status"))
    except Exception as e:
        return fail(e)

@app.post("/api/devices/sync")
def api_devices_sync():
    try:
        return ok(execute("devices", "sync"))
    except Exception as e:
        return fail(e)

@app.post("/api/devices/<mac>/profile")
def api_device_profile(mac):
    try:
        data = request.get_json(silent=True) or {}
        profile = data.get("profile")
        if not profile:
            return fail("profile is required", 400)
        return ok(execute("devices", "set-profile", mac=mac, value=profile))
    except Exception as e:
        return fail(e)

@app.post("/api/devices/<mac>/alias")
def api_device_alias(mac):
    try:
        data = request.get_json(silent=True) or {}
        alias = data.get("alias", "")
        return ok(execute("devices", "set-alias", mac=mac, value=alias))
    except Exception as e:
        return fail(e)

@app.post("/api/devices/<mac>/notes")
def api_device_notes(mac):
    try:
        data = request.get_json(silent=True) or {}
        notes = data.get("notes", "")
        return ok(execute("devices", "set-notes", mac=mac, value=notes))
    except Exception as e:
        return fail(e)

@app.get("/api/profiles")
def api_profiles():
    try:
        return ok(execute("profiles", "status"))
    except Exception as e:
        return fail(e)

@app.post("/api/profiles")
def api_profiles_add():
    try:
        data = request.get_json(silent=True) or {}
        name = data.get("name")
        description = data.get("description", "")
        if not name:
            return fail("name is required", 400)
        return ok(execute("profiles", "add", name=name, description=description))
    except Exception as e:
        return fail(e)

@app.delete("/api/profiles/<name>")
def api_profiles_delete(name):
    try:
        return ok(execute("profiles", "delete", name=name))
    except Exception as e:
        return fail(e)

@app.get("/api/policy")
def api_policy():
    try:
        return ok(execute("policy", "status"))
    except Exception as e:
        return fail(e)

@app.post("/api/policy")
def api_policy_set():
    try:
        data = request.get_json(silent=True) or {}
        profile = data.get("profile")
        field = data.get("field")
        value = data.get("value")
        if not profile or not field or value is None:
            return fail("profile, field, and value are required", 400)
        return ok(execute("policy", "set", profile=profile, field=field, value=value))
    except Exception as e:
        return fail(e)

@app.get("/api/policy/resolve")
def api_policy_resolve():
    try:
        mac = request.args.get("mac")
        profile = request.args.get("profile")
        return ok(execute("policy", "resolve", mac=mac, profile=profile))
    except Exception as e:
        return fail(e)

@app.post("/api/policy/apply")
def api_policy_apply():
    try:
        return ok(execute("policy", "apply"))
    except Exception as e:
        return fail(e)

@app.get("/api/settings")
def api_settings():
    try:
        return ok({"settings": [{"key": k, "value": v} for k, v in list_all()]})
    except Exception as e:
        return fail(e)

@app.post("/api/settings")
def api_settings_set():
    try:
        data = request.get_json(silent=True) or {}
        key = data.get("key")
        value = data.get("value")
        if not key or value is None:
            return fail("key and value are required", 400)
        set_setting(key, value)
        return ok({"key": key, "value": str(value)})
    except Exception as e:
        return fail(e)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8181)
