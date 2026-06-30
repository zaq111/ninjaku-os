from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

dns_filter_bp = Blueprint("dns_filter_api", __name__)

ENDPOINTS = [
    ("GET",    "/api/v1/dns-filter"),
    ("POST",   "/api/v1/dns-filter/domains"),
    ("DELETE", "/api/v1/dns-filter/domains/<domain>"),
    ("POST",   "/api/v1/dns-filter/apply"),
]

@dns_filter_bp.get("/api/v1/dns-filter")
def api_dns_filter():
    try:
        return ok(execute("dns_filter", "status"))
    except Exception as e:
        return fail(e)

@dns_filter_bp.post("/api/v1/dns-filter/domains")
def api_dns_filter_add():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain")
    if not domain:
        return fail("domain is required", 400, "VALIDATION_ERROR")
    return ok(execute("dns_filter", "add", domain=domain))

@dns_filter_bp.delete("/api/v1/dns-filter/domains/<path:domain>")
def api_dns_filter_delete(domain):
    return ok(execute("dns_filter", "delete", domain=domain))

@dns_filter_bp.post("/api/v1/dns-filter/apply")
def api_dns_filter_apply():
    return ok(execute("dns_filter", "apply"))
