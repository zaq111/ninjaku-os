from flask import Blueprint
from lib.modules import execute
from api.common import ok, fail

dhcp_bp = Blueprint("dhcp_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/dhcp"),
    ("POST", "/api/v1/dhcp/start"),
    ("POST", "/api/v1/dhcp/stop"),
]

@dhcp_bp.get("/api/v1/dhcp")
def api_dhcp():
    try:
        return ok(execute("dhcp", "status"))
    except Exception as e:
        return fail(e)

@dhcp_bp.post("/api/v1/dhcp/start")
def api_dhcp_start():
    try:
        return ok(execute("dhcp", "start"))
    except Exception as e:
        return fail(e)

@dhcp_bp.post("/api/v1/dhcp/stop")
def api_dhcp_stop():
    try:
        return ok(execute("dhcp", "stop"))
    except Exception as e:
        return fail(e)
