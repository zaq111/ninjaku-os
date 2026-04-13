from datetime import datetime, timezone
from flask import jsonify

APP_NAME = "Ninjaku OS Router API"
APP_VERSION = "1.0-alpha"
API_VERSION = "v1"

def now():
    return datetime.now(timezone.utc).isoformat()

def ok(data=None):
    return jsonify({
        "success": True,
        "timestamp": now(),
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "data": data or {},
    })

def fail(message, code=500, errcode="ERROR"):
    return jsonify({
        "success": False,
        "timestamp": now(),
        "version": APP_VERSION,
        "api_version": API_VERSION,
        "error": {
            "code": errcode,
            "message": str(message),
        },
    }), code
