from flask import Blueprint, request
from lib.settings import list_all, set as set_setting
from api.common import ok, fail

settings_bp = Blueprint("settings_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/settings"),
    ("POST", "/api/v1/settings"),
]

SECRET_KEYS = {
    "adguard.password",
    "adguard.username",
    "telegram.token",
    "telegram.chat_id",
    "openai.api_key",
    "cloudflare.api_token",
}

def mask_setting(key, value):
    if key in SECRET_KEYS:
        if value in (None, ""):
            return ""
        return "********"
    return value


@settings_bp.get("/api/v1/settings")
def api_settings():
    return ok({
        "settings": [
            {
                "key": k,
                "value": mask_setting(k, v)
            }
            for k, v in list_all()
        ]
    })

@settings_bp.post("/api/v1/settings")
def api_settings_set():
    data = request.get_json(silent=True) or {}
    key = data.get("key")
    value = data.get("value")

    if not key or value is None:
        return fail("key and value are required", 400, "VALIDATION_ERROR")

    set_setting(key, value)
    return ok({"key": key, "value": str(value)})
