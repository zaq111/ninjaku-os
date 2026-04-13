from flask import Blueprint
from lib.modules import execute
from lib.db import connect
from lib.system import run
from api.common import ok, fail, APP_NAME, APP_VERSION, API_VERSION

system_bp = Blueprint("system_api", __name__)

ENDPOINTS = [
    ("GET",  "/api/v1/status"),
]

def db_ok():
    try:
        with connect() as db:
            db.execute("SELECT 1")
        return True
    except Exception:
        return False

@system_bp.get("/api/v1/health")
def api_health():
    return ok({
        "service": "ninjaku-api",
        "status": "ok",
        "database": "ok" if db_ok() else "error",
        "ninjaku_api": run(["systemctl", "is-active", "ninjaku-api"])["stdout"],
        "ninjakud": run(["systemctl", "is-active", "ninjakud"])["stdout"],
    })

@system_bp.get("/api/v1/status")
def api_status():
    try:
        return ok(execute("system", "status"))
    except Exception as e:
        return fail(e)

@system_bp.get("/api/health")
def api_health_legacy():
    return api_health()
