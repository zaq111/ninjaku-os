import json
import urllib.request
import urllib.error

from lib.system import run
from lib.settings import get, set

DEFAULT_URL = "http://127.0.0.1:3000"

def base_url():
    return get("adguard.url", DEFAULT_URL).rstrip("/")

def http_get(path):
    url = base_url() + path
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            body = r.read().decode("utf-8", errors="ignore")
            try:
                return {"ok": True, "json": json.loads(body), "text": body}
            except Exception:
                return {"ok": True, "json": None, "text": body}
    except Exception as e:
        return {"ok": False, "error": str(e), "json": None, "text": ""}

def service_status():
    return {
        "service": run(["systemctl", "is-active", "AdGuardHome"])["stdout"],
        "enabled": run(["systemctl", "is-enabled", "AdGuardHome"])["stdout"],
    }

def status():
    svc = service_status()
    api = http_get("/control/status")
    stats = http_get("/control/stats")

    return {
        "url": base_url(),
        "service": svc.get("service"),
        "enabled": svc.get("enabled"),
        "api_ok": api.get("ok"),
        "status": api.get("json"),
        "stats_ok": stats.get("ok"),
        "stats": stats.get("json"),
        "api_error": api.get("error", ""),
        "stats_error": stats.get("error", ""),
    }


def install():
    r = run([
        "sh", "-c",
        "curl -sSL https://raw.githubusercontent.com/AdguardTeam/AdGuardHome/master/scripts/install.sh | sh -s -- -v"
    ], timeout=300)

    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def set_url(url):
    set("adguard.url", url.rstrip("/"))
    return {"ok": True, "url": base_url()}
