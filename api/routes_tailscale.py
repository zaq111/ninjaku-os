from flask import Blueprint, request
from api.common import ok
from lib.modules import execute

tailscale_bp = Blueprint("tailscale_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/tailscale"),
    ("POST", "/api/v1/tailscale/up"),
    ("POST", "/api/v1/tailscale/down"),
    ("POST", "/api/v1/tailscale/logout"),
]

@tailscale_bp.get("/api/v1/tailscale")
def api_tailscale():
    return ok(execute("tailscale", "status"))

@tailscale_bp.post("/api/v1/tailscale/up")
def api_tailscale_up():
    data = request.get_json(silent=True) or {}
    return ok(execute("tailscale", "up", args=data.get("args", [])))

@tailscale_bp.post("/api/v1/tailscale/down")
def api_tailscale_down():
    return ok(execute("tailscale", "down"))

@tailscale_bp.post("/api/v1/tailscale/logout")
def api_tailscale_logout():
    return ok(execute("tailscale", "logout"))
