from lib.system import run
from lib.db import connect
from lib.policy import resolve
from lib.settings import get

BASE_RULESET = r"""
table inet ninjaku_policy {
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
    run(["nft", "delete", "table", "inet", "ninjaku_policy"], timeout=5)
    p = run(["nft", "-f", "-"], timeout=5, input_text=BASE_RULESET)
    return {"ok": p["ok"], "stdout": p["stdout"], "stderr": p["stderr"]}

def reset():
    p = run(["nft", "delete", "table", "inet", "ninjaku_policy"], timeout=5)
    ok = p["ok"] or "No such file or directory" in p["stderr"]
    return {"ok": ok, "stdout": p["stdout"], "stderr": p["stderr"]}

def blocked_devices():
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

    rules = """
table inet ninjaku_policy {
    chain forward {
        type filter hook forward priority -10; policy accept;
        ct state established,related accept
"""

    for dev in blocked:
        rules += f'        ip saddr {dev["ip"]} drop\n'

    rules += """    }
}
"""

    run(["nft", "delete", "table", "inet", "ninjaku_policy"], timeout=5)
    p = run(["nft", "-f", "-"], timeout=5, input_text=rules)

    return {
        "ok": p["ok"],
        "blocked_count": len(blocked),
        "blocked": blocked,
        "stdout": p["stdout"],
        "stderr": p["stderr"],
    }
