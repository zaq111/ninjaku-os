from flask import Blueprint
from lib.modules import execute
from api.common import ok, fail

router_bp = Blueprint("router_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/router"),
    ("POST", "/api/v1/router/enable"),
    ("POST", "/api/v1/router/disable"),
]

@router_bp.get("/api/v1/router")
def api_router():
    try:
        return ok(execute("router", "status"))
    except Exception as e:
        return fail(e)

@router_bp.post("/api/v1/router/enable")
def api_router_enable():
    try:
        return ok(execute("router", "enable"))
    except Exception as e:
        return fail(e)

@router_bp.post("/api/v1/router/disable")
def api_router_disable():
    try:
        return ok(execute("router", "disable"))
    except Exception as e:
        return fail(e)
