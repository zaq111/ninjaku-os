from flask import Blueprint, request
from api.common import ok
from lib.modules import execute

wifi_bp = Blueprint("wifi_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/wifi"),
    ("POST", "/api/v1/wifi/config"),
    ("GET",  "/api/v1/wifi/hostapd-config"),
    ("POST", "/api/v1/wifi/write-config"),
]

@wifi_bp.get("/api/v1/wifi")
def api_wifi():
    return ok(execute("wifi", "status"))

@wifi_bp.post("/api/v1/wifi/config")
def api_wifi_config():
    data = request.get_json(silent=True) or {}
    return ok(execute("wifi", "config", **data))

@wifi_bp.get("/api/v1/wifi/hostapd-config")
def api_wifi_hostapd_config():
    return ok(execute("wifi", "generate-config"))

@wifi_bp.post("/api/v1/wifi/write-config")
def api_wifi_write_config():
    return ok(execute("wifi", "write-config"))
