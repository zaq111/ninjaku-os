from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

adguard_bp = Blueprint("adguard_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/adguard"),
    ("POST", "/api/v1/adguard/url"),
    ("POST", "/api/v1/adguard/install"),
]

@adguard_bp.get("/api/v1/adguard")
def api_adguard():
    try:
        return ok(execute("adguard", "status"))
    except Exception as e:
        return fail(e)


@adguard_bp.post("/api/v1/adguard/install")
def api_adguard_install():
    try:
        return ok(execute("adguard", "install"))
    except Exception as e:
        return fail(e)

@adguard_bp.post("/api/v1/adguard/url")
def api_adguard_url():
    data = request.get_json(silent=True) or {}
    url = data.get("url")
    if not url:
        return fail("url is required", 400, "VALIDATION_ERROR")
    return ok(execute("adguard", "set-url", url=url))
