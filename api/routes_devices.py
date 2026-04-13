from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

devices_bp = Blueprint("devices_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/devices"),
    ("POST", "/api/v1/devices/sync"),
    ("POST", "/api/v1/devices/<mac>/profile"),
    ("POST", "/api/v1/devices/<mac>/alias"),
    ("POST", "/api/v1/devices/<mac>/notes"),
]

@devices_bp.get("/api/v1/devices")
def api_devices():
    try:
        return ok(execute("devices", "status"))
    except Exception as e:
        return fail(e)

@devices_bp.post("/api/v1/devices/sync")
def api_devices_sync():
    try:
        return ok(execute("devices", "sync"))
    except Exception as e:
        return fail(e)

@devices_bp.post("/api/v1/devices/<mac>/profile")
def api_device_profile(mac):
    data = request.get_json(silent=True) or {}
    profile = data.get("profile")
    if not profile:
        return fail("profile is required", 400, "VALIDATION_ERROR")
    return ok(execute("devices", "set-profile", mac=mac, value=profile))

@devices_bp.post("/api/v1/devices/<mac>/alias")
def api_device_alias(mac):
    data = request.get_json(silent=True) or {}
    return ok(execute("devices", "set-alias", mac=mac, value=data.get("alias", "")))

@devices_bp.post("/api/v1/devices/<mac>/notes")
def api_device_notes(mac):
    data = request.get_json(silent=True) or {}
    return ok(execute("devices", "set-notes", mac=mac, value=data.get("notes", "")))
