from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

adguard_bp = Blueprint("adguard_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/adguard"),
    ("POST", "/api/v1/adguard/url"),
    ("POST", "/api/v1/adguard/install"),
    ("POST", "/api/v1/adguard/protection"),
    ("POST", "/api/v1/adguard/update-filters"),
    ("GET",  "/api/v1/adguard/querylog"),
    ("GET",  "/api/v1/adguard/dns-config"),
    ("POST", "/api/v1/adguard/upstream"),
]

@adguard_bp.get("/api/v1/adguard")
def api_adguard():
    try:
        return ok(execute("adguard", "status"))
    except Exception as e:
        return fail(e)






@adguard_bp.get("/api/v1/adguard/dns-config")
def api_adguard_dns_config():
    try:
        return ok(execute("adguard", "dns-config"))
    except Exception as e:
        return fail(e)

@adguard_bp.post("/api/v1/adguard/upstream")
def api_adguard_upstream():
    data = request.get_json(silent=True) or {}
    upstreams = data.get("upstreams", [])
    if not upstreams:
        return fail("upstreams is required", 400, "VALIDATION_ERROR")
    return ok(execute("adguard", "set-upstream", upstreams=upstreams))

@adguard_bp.get("/api/v1/adguard/querylog")
def api_adguard_querylog():
    try:
        limit = request.args.get("limit", 20)
        client = request.args.get("client", "")
        return ok(execute("adguard", "querylog", limit=limit, client=client))
    except Exception as e:
        return fail(e)

@adguard_bp.post("/api/v1/adguard/update-filters")
def api_adguard_update_filters():
    try:
        return ok(execute("adguard", "update-filters"))
    except Exception as e:
        return fail(e)

@adguard_bp.post("/api/v1/adguard/protection")
def api_adguard_protection():
    data = request.get_json(silent=True) or {}
    enabled = data.get("enabled")
    if enabled is None:
        return fail("enabled is required", 400, "VALIDATION_ERROR")
    return ok(execute("adguard", "protection", enabled=bool(enabled)))

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
