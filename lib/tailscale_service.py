import json
import shutil
from lib.system import run

def installed():
    return shutil.which("tailscale") is not None

def service_state():
    r = run(["systemctl", "is-active", "tailscaled"])
    return {
        "active": r["stdout"].strip() == "active",
        "state": r["stdout"].strip() or "unknown",
    }

def status_json():
    if not installed():
        return None

    r = run(["tailscale", "status", "--json"])
    if not r["ok"]:
        return None

    try:
        return json.loads(r["stdout"])
    except Exception:
        return None

def status():
    svc = service_state()
    js = status_json()

    self_info = (js or {}).get("Self", {}) if js else {}
    tailscale_ips = self_info.get("TailscaleIPs", []) or []

    return {
        "installed": installed(),
        "service": svc,
        "connected": bool(js and self_info.get("Online")),
        "hostname": self_info.get("HostName", ""),
        "dns_name": self_info.get("DNSName", ""),
        "tailscale_ips": tailscale_ips,
        "ip": tailscale_ips[0] if tailscale_ips else "",
        "user": ((js or {}).get("User", {}) or {}).get("LoginName", ""),
        "backend_state": (js or {}).get("BackendState", ""),
        "raw_ok": bool(js),
    }

def up(extra_args=None):
    if not installed():
        return {"ok": False, "error": "tailscale is not installed"}

    args = ["tailscale", "up"]
    if extra_args:
        args += extra_args

    r = run(args)
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"], "status": status()}

def down():
    if not installed():
        return {"ok": False, "error": "tailscale is not installed"}

    r = run(["tailscale", "down"])
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"], "status": status()}

def logout():
    if not installed():
        return {"ok": False, "error": "tailscale is not installed"}

    r = run(["tailscale", "logout"])
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"], "status": status()}
