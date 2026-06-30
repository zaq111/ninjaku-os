#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/ninjaku")

from flask import Flask, send_from_directory
from api.common import ok, APP_NAME, APP_VERSION, API_VERSION

from api.routes_system import system_bp, ENDPOINTS as SYSTEM_ENDPOINTS
from api.routes_network import network_bp, ENDPOINTS as NETWORK_ENDPOINTS
from api.routes_router import router_bp, ENDPOINTS as ROUTER_ENDPOINTS
from api.routes_firewall import firewall_bp, ENDPOINTS as FIREWALL_ENDPOINTS
from api.routes_dhcp import dhcp_bp, ENDPOINTS as DHCP_ENDPOINTS
from api.routes_devices import devices_bp, ENDPOINTS as DEVICES_ENDPOINTS
from api.routes_profiles import profiles_bp, ENDPOINTS as PROFILES_ENDPOINTS
from api.routes_policy import policy_bp, ENDPOINTS as POLICY_ENDPOINTS
from api.routes_settings import settings_bp, ENDPOINTS as SETTINGS_ENDPOINTS

app = Flask(__name__)

ALL_ENDPOINTS = (
    SYSTEM_ENDPOINTS
    + NETWORK_ENDPOINTS
    + ROUTER_ENDPOINTS
    + FIREWALL_ENDPOINTS
    + DHCP_ENDPOINTS
    + DEVICES_ENDPOINTS
    + PROFILES_ENDPOINTS
    + POLICY_ENDPOINTS
    + SETTINGS_ENDPOINTS
)

app.register_blueprint(system_bp)
app.register_blueprint(network_bp)
app.register_blueprint(router_bp)
app.register_blueprint(firewall_bp)
app.register_blueprint(dhcp_bp)
app.register_blueprint(devices_bp)
app.register_blueprint(profiles_bp)
app.register_blueprint(policy_bp)
app.register_blueprint(settings_bp)

@app.get("/api/v1/endpoints")
def api_full_endpoints():
    return ok({"endpoints": [{"method": m, "path": p} for m, p in ALL_ENDPOINTS]})

@app.get("/api/v1")
def api_index_full():
    return ok({
        "name": APP_NAME,
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "documentation": "/api/v1/endpoints",
        "endpoints": [{"method": m, "path": p} for m, p in ALL_ENDPOINTS],
    })


@app.get("/")
def webui_index():
    return send_from_directory("/opt/ninjaku/webui", "index.html")

@app.get("/static/<path:path>")
def webui_static(path):
    return send_from_directory("/opt/ninjaku/webui", path)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8181)
