from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

qos_bp = Blueprint("qos_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/qos"),
    ("POST", "/api/v1/qos"),
    ("POST", "/api/v1/qos/apply"),
    ("POST", "/api/v1/qos/disable"),
]

@qos_bp.get("/api/v1/qos")
def api_qos():
    try:
        return ok(execute("qos", "status"))
    except Exception as e:
        return fail(e)

@qos_bp.post("/api/v1/qos")
def api_qos_set():
    data = request.get_json(silent=True) or {}
    return ok(execute("qos", "set", **data))

@qos_bp.post("/api/v1/qos/apply")
def api_qos_apply():
    return ok(execute("qos", "apply"))

@qos_bp.post("/api/v1/qos/disable")
def api_qos_disable():
    return ok(execute("qos", "disable"))
