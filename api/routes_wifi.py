from flask import Blueprint, request
from api.common import ok
from lib.modules import execute

wifi_bp = Blueprint("wifi_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/wifi"),
    ("GET",  "/api/v1/wifi/stations"),
    ("POST", "/api/v1/wifi/config"),
    ("GET",  "/api/v1/wifi/hostapd-config"),
    ("POST", "/api/v1/wifi/write-config"),
    ("POST", "/api/v1/wifi/start"),
    ("POST", "/api/v1/wifi/stop"),
    ("POST", "/api/v1/wifi/restart"),
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


@wifi_bp.post("/api/v1/wifi/start")
def api_wifi_start():
    return ok(execute("wifi", "start"))

@wifi_bp.post("/api/v1/wifi/stop")
def api_wifi_stop():
    return ok(execute("wifi", "stop"))

@wifi_bp.post("/api/v1/wifi/restart")
def api_wifi_restart():
    return ok(execute("wifi", "restart"))


@wifi_bp.get("/api/v1/wifi/stations")
def api_wifi_stations():
    return ok(execute("wifi","stations"))
