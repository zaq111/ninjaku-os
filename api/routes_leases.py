from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

leases_bp = Blueprint("leases_api", __name__)

ENDPOINTS = [
    ("GET",    "/api/v1/leases"),
    ("POST",   "/api/v1/leases"),
    ("DELETE", "/api/v1/leases/<mac>"),
    ("POST",   "/api/v1/leases/apply"),
]

@leases_bp.get("/api/v1/leases")
def api_leases():
    try:
        return ok(execute("static_leases", "status"))
    except Exception as e:
        return fail(e)

@leases_bp.post("/api/v1/leases")
def api_leases_set():
    data = request.get_json(silent=True) or {}
    mac = data.get("mac")
    ip = data.get("ip")
    hostname = data.get("hostname", "")

    if not mac or not ip:
        return fail("mac and ip are required", 400, "VALIDATION_ERROR")

    return ok(execute("static_leases", "set", mac=mac, ip=ip, hostname=hostname))

@leases_bp.delete("/api/v1/leases/<mac>")
def api_leases_delete(mac):
    return ok(execute("static_leases", "delete", mac=mac))

@leases_bp.post("/api/v1/leases/apply")
def api_leases_apply():
    return ok(execute("static_leases", "apply"))
