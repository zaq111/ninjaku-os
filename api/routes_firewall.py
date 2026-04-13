from flask import Blueprint
from lib.modules import execute
from api.common import ok, fail

firewall_bp = Blueprint("firewall_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/firewall"),
    ("POST", "/api/v1/firewall/apply-policy"),
]

@firewall_bp.get("/api/v1/firewall")
def api_firewall():
    try:
        return ok(execute("firewall", "status"))
    except Exception as e:
        return fail(e)

@firewall_bp.post("/api/v1/firewall/apply-policy")
def api_firewall_apply_policy():
    try:
        return ok(execute("firewall", "apply-policy"))
    except Exception as e:
        return fail(e)
