from flask import Blueprint
from lib.modules import execute
from api.common import ok, fail

network_bp = Blueprint("network_api", __name__)

ENDPOINTS = [
    ("GET", "/api/v1/network"),
]

@network_bp.get("/api/v1/network")
def api_network():
    try:
        return ok(execute("network", "status"))
    except Exception as e:
        return fail(e)
