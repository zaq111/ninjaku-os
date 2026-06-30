from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

qos_pipes_bp = Blueprint("qos_pipes_api", __name__)

ENDPOINTS = [
    ("GET",    "/api/v1/qos/pipes"),
    ("POST",   "/api/v1/qos/pipes"),
    ("DELETE", "/api/v1/qos/pipes/<pipe_id>"),
]

@qos_pipes_bp.get("/api/v1/qos/pipes")
def api_qos_pipes():
    try:
        return ok(execute("qos_pipes", "status"))
    except Exception as e:
        return fail(e)

@qos_pipes_bp.post("/api/v1/qos/pipes")
def api_qos_pipes_save():
    data = request.get_json(silent=True) or {}
    try:
        return ok(execute("qos_pipes", "save", **data))
    except Exception as e:
        return fail(e)

@qos_pipes_bp.delete("/api/v1/qos/pipes/<pipe_id>")
def api_qos_pipes_delete(pipe_id):
    try:
        return ok(execute("qos_pipes", "delete", id=pipe_id))
    except Exception as e:
        return fail(e)
