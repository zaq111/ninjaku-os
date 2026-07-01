from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

profiles_bp = Blueprint("profiles_api", __name__)

ENDPOINTS = [
    ("GET",    "/api/v1/profiles"),
    ("POST",   "/api/v1/profiles"),
    ("DELETE", "/api/v1/profiles/<name>"),
    ("POST",   "/api/v1/profiles/<name>"),
]

@profiles_bp.get("/api/v1/profiles")
def api_profiles():
    try:
        return ok(execute("profiles", "status"))
    except Exception as e:
        return fail(e)

@profiles_bp.post("/api/v1/profiles")
def api_profiles_add():
    data = request.get_json(silent=True) or {}
    name = data.get("name")
    if not name:
        return fail("name is required", 400, "VALIDATION_ERROR")
    return ok(execute("profiles", "add", name=name, description=data.get("description", "")))

@profiles_bp.delete("/api/v1/profiles/<name>")
def api_profiles_delete(name):
    return ok(execute("profiles", "delete", name=name))


@profiles_bp.post("/api/v1/profiles/<name>")
def api_profiles_update(name):
    data = request.get_json(silent=True) or {}
    return ok(execute("profiles", "update", name=name, **data))
