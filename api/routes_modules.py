from flask import Blueprint
from api.common import ok

modules_bp = Blueprint("modules_api", __name__)

ENDPOINTS = [
    ("GET", "/api/v1/modules"),
]

MODULES = [
    {"id": "overview", "title": "Overview", "icon": "home", "order": 0, "page": "overview"},
    {"id": "router", "title": "Router", "icon": "router", "order": 10, "page": "router"},
    {"id": "devices", "title": "Devices", "icon": "devices", "order": 20, "page": "devices"},
    {"id": "leases", "title": "Static Leases", "icon": "dhcp", "order": 25, "page": "leases"},
    {"id": "policy", "title": "Policy", "icon": "policy", "order": 30, "page": "policy"},
    {"id": "qos", "title": "QoS", "icon": "qos", "order": 32, "page": "qos"},
    {"id": "adguard", "title": "AdGuard Home", "icon": "firewall", "order": 35, "page": "adguard"},
    {"id": "profiles", "title": "Profiles", "icon": "profiles", "order": 40, "page": "profiles"},
    {"id": "settings", "title": "Settings", "icon": "settings", "order": 90, "page": "settings"},
]

@modules_bp.get("/api/v1/modules")
def api_modules():
    return ok({
        "modules": sorted(MODULES, key=lambda m: m.get("order", 999))
    })
