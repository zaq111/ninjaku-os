NAME = "firewall"
VERSION = "1.2"

from lib.system import run
from lib.db import connect
from lib.policy import resolve

BASE_RULESET = r"""
table inet ninjaku {
    chain input {
        type filter hook input priority 0; policy accept;
        iif "lo" accept
        ct state established,related accept
    }

    chain forward {
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
"""

def status():
    nft = run(["nft", "list", "ruleset"], timeout=5)
    return {
        "nft_ok": nft["ok"],
        "nft_ruleset": nft["stdout"] if nft["stdout"] else nft["stderr"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def init():
    run(["nft", "delete", "table", "inet", "ninjaku"], timeout=5)
    p = run(["nft", "-f", "-"], timeout=5, input_text=BASE_RULESET)
    return {"ok": p["ok"], "stdout": p["stdout"], "stderr": p["stderr"]}

def reset():
    p = run(["nft", "delete", "table", "inet", "ninjaku"], timeout=5)
    ok = p["ok"] or "No such file or directory" in p["stderr"]
    return {"ok": ok, "stdout": p["stdout"], "stderr": p["stderr"]}

def blocked_devices():
    rows = []
    with connect() as db:
        cur = db.execute("""
            SELECT mac, ip, hostname, profile
            FROM devices
            WHERE ip IS NOT NULL AND ip != ''
        """)
        rows = cur.fetchall()

    blocked = []
    for mac, ip, hostname, profile in rows:
        pol = resolve(mac=mac)
        if pol.get("internet") == "deny":
            blocked.append({
                "mac": mac,
                "ip": ip,
                "hostname": hostname,
                "profile": profile,
            })
    return blocked

def apply_policy():
    blocked = blocked_devices()

    # Chain khusus policy. Kalau belum ada, router/nat-up harus dijalankan dulu.
    run(["nft", "delete", "chain", "inet", "ninjaku", "policy_block"], timeout=5)

    rules = """
add chain inet ninjaku policy_block
add rule inet ninjaku forward jump policy_block
"""

    for dev in blocked:
        rules += f'add rule inet ninjaku policy_block ip saddr {dev["ip"]} drop\n'

    p = run(["nft", "-f", "-"], timeout=5, input_text=rules)

    return {
        "ok": p["ok"],
        "blocked_count": len(blocked),
        "blocked": blocked,
        "stdout": p["stdout"],
        "stderr": p["stderr"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "init":
        return init()
    if command == "reset":
        return reset()
    if command == "apply-policy":
        return apply_policy()

    raise Exception(f"Unknown firewall command: {command}")
