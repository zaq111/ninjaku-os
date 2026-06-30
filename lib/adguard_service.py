import json
import urllib.request
import urllib.error
import http.cookiejar

from lib.system import run
from lib.settings import get, set

DEFAULT_URL = "http://127.0.0.1:80"

def base_url():
    return get("adguard.url", DEFAULT_URL).rstrip("/")

def credentials():
    return (
        get("adguard.username", "root"),
        get("adguard.password", ""),
    )

def service_status():
    return {
        "service": run(["systemctl", "is-active", "AdGuardHome"])["stdout"],
        "enabled": run(["systemctl", "is-enabled", "AdGuardHome"])["stdout"],
    }

def opener_with_session():
    username, password = credentials()

    cj = http.cookiejar.CookieJar()
    opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

    if not username or not password:
        return opener, False, "missing credentials"

    payload = json.dumps({
        "name": username,
        "password": password,
    }).encode("utf-8")

    req = urllib.request.Request(
        base_url() + "/control/login",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        opener.open(req, timeout=5).read()
        return opener, True, ""
    except Exception as e:
        return opener, False, str(e)

def http_get(path):
    opener, logged_in, login_error = opener_with_session()

    if not logged_in:
        return {
            "ok": False,
            "error": f"login failed: {login_error}",
            "json": None,
            "text": "",
        }

    url = base_url() + path

    try:
        with opener.open(url, timeout=5) as r:
            body = r.read().decode("utf-8", errors="ignore")
            try:
                return {"ok": True, "json": json.loads(body), "text": body}
            except Exception:
                return {"ok": True, "json": None, "text": body}
    except Exception as e:
        return {"ok": False, "error": str(e), "json": None, "text": ""}


def http_post(path, payload=None):
    opener, logged_in, login_error = opener_with_session()

    if not logged_in:
        return {
            "ok": False,
            "error": f"login failed: {login_error}",
            "json": None,
            "text": "",
        }

    data = json.dumps(payload or {}).encode("utf-8")

    req = urllib.request.Request(
        base_url() + path,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with opener.open(req, timeout=10) as r:
            body = r.read().decode("utf-8", errors="ignore")
            try:
                return {"ok": True, "json": json.loads(body), "text": body}
            except Exception:
                return {"ok": True, "json": None, "text": body}
    except Exception as e:
        return {"ok": False, "error": str(e), "json": None, "text": ""}



def querylog(limit=20, client=""):
    path = f"/control/querylog?limit={int(limit)}"
    if client:
        path += "&search=" + str(client)
    r = http_get(path)
    return {
        "ok": r["ok"],
        "error": r.get("error", ""),
        "data": r.get("json"),
        "text": r.get("text", ""),
    }


def update_filters():
    r = http_post("/control/filtering/refresh", {})
    return {
        "ok": r["ok"],
        "error": r.get("error", ""),
        "response": r.get("json"),
        "text": r.get("text", ""),
    }


def set_protection(enabled):
    r = http_post("/control/protection", {"enabled": bool(enabled)})
    return {
        "ok": r["ok"],
        "enabled": bool(enabled),
        "error": r.get("error", ""),
        "response": r.get("json"),
        "text": r.get("text", ""),
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

def set_url(url):
    set("adguard.url", url.rstrip("/"))
    return {"ok": True, "url": base_url()}

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
