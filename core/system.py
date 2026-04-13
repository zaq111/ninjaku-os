import subprocess
from pathlib import Path

def run(cmd, timeout=10):
    p = subprocess.run(
        cmd,
        shell=True,
        text=True,
        capture_output=True,
        timeout=timeout,
    )
    return {
        "ok": p.returncode == 0,
        "code": p.returncode,
        "stdout": p.stdout.strip(),
        "stderr": p.stderr.strip(),
    }

def read_text(path):
    try:
        return Path(path).read_text().strip()
    except Exception:
        return ""

def system_status():
    return {
        "hostname": run("hostname")["stdout"],
        "kernel": run("uname -r")["stdout"],
        "os": read_text("/etc/os-release"),
        "uptime": run("uptime -p")["stdout"],
        "ip": run("ip -br addr")["stdout"],
        "failed_units": run("systemctl --failed --no-legend")["stdout"],
    }
