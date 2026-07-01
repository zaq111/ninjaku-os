import json
import re
import shutil
from lib.system import run

def extract_login_url(text):
    m = re.search(r"https://login\.tailscale\.com/[^\s]+", text or "")
    return m.group(0) if m else ""

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

    args = ["tailscale", "up", "--timeout=5s"]
    if extra_args:
        args += extra_args

    r = run(args, timeout=15)
    combined = (r["stdout"] or "") + "\n" + (r["stderr"] or "")
    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
        "login_url": extract_login_url(combined),
        "status": status()
    }

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

def install():
    if installed():
        return {"ok": True, "already_installed": True, "status": status()}

    cmds = [
        ["apt-get", "update"],
        ["apt-get", "-y", "install", "curl", "ca-certificates", "gnupg"],
        ["sh", "-c", "mkdir -p /usr/share/keyrings"],
        ["sh", "-c", "curl -fsSL https://pkgs.tailscale.com/stable/debian/trixie.noarmor.gpg -o /usr/share/keyrings/tailscale-archive-keyring.gpg"],
        ["sh", "-c", "curl -fsSL https://pkgs.tailscale.com/stable/debian/trixie.tailscale-keyring.list -o /etc/apt/sources.list.d/tailscale.list"],
        ["apt-get", "update"],
        ["apt-get", "-y", "install", "tailscale"],
        ["systemctl", "enable", "--now", "tailscaled"],
    ]

    logs = []
    ok_all = True

    for cmd in cmds:
        timeout = 600 if cmd[0] in ("apt-get",) else 120
        r = run(cmd, timeout=timeout)
        logs.append({
            "cmd": " ".join(cmd),
            "ok": r["ok"],
            "stdout": r["stdout"][-2000:],
            "stderr": r["stderr"][-2000:],
        })
        if not r["ok"]:
            ok_all = False
            break

    return {
        "ok": ok_all,
        "logs": logs,
        "status": status(),
    }
