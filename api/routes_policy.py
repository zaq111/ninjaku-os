from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

policy_bp = Blueprint("policy_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/policy"),
    ("POST", "/api/v1/policy"),
    ("GET",  "/api/v1/policy/resolve"),
    ("POST", "/api/v1/policy/apply"),
]

@policy_bp.get("/api/v1/policy")
def api_policy():
    try:
        return ok(execute("policy", "status"))
    except Exception as e:
        return fail(e)

@policy_bp.post("/api/v1/policy")
def api_policy_set():
    data = request.get_json(silent=True) or {}
    profile = data.get("profile")
    field = data.get("field")
    value = data.get("value")

    if not profile or not field or value is None:
        return fail("profile, field, and value are required", 400, "VALIDATION_ERROR")

    return ok(execute("policy", "set", profile=profile, field=field, value=value))

@policy_bp.get("/api/v1/policy/resolve")
def api_policy_resolve():
    return ok(execute(
        "policy",
        "resolve",
        mac=request.args.get("mac"),
        profile=request.args.get("profile")
    ))

@policy_bp.post("/api/v1/policy/apply")
def api_policy_apply():
    return ok(execute("policy", "apply"))
