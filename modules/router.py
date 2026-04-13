NAME = "router"
VERSION = "1.1"

from lib.system import run
from lib.settings import get, set

DEFAULTS = {
    "router.wan": "eth0",
    "router.lan": "eth1",
    "router.lan_ip": "192.168.10.1/24",
}

def cfg(key):
    return get(key, DEFAULTS[key])

def current():
    return {
        "wan": cfg("router.wan"),
        "lan": cfg("router.lan"),
        "lan_ip": cfg("router.lan_ip"),
    }

def status():
    c = current()
    return {
        "wan": c["wan"],
        "lan": c["lan"],
        "lan_ip": c["lan_ip"],
        "interfaces": run(["ip", "-br", "addr"])["stdout"],
        "routes": run(["ip", "route"])["stdout"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def lan_up():
    c = current()
    lan = c["lan"]
    lan_ip = c["lan_ip"]

    run(["ip", "link", "set", lan, "up"])
    run(["ip", "addr", "flush", "dev", lan])
    ip_result = run(["ip", "addr", "add", lan_ip, "dev", lan])

    return {
        "ok": ip_result["ok"],
        "lan": lan,
        "lan_ip": lan_ip,
        "stdout": ip_result["stdout"],
        "stderr": ip_result["stderr"],
    }

def enable_forward():
    r = run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def nat_up():
    c = current()
    wan = c["wan"]
    lan = c["lan"]

    ruleset = f"""
table inet ninjaku {{
    chain input {{
        type filter hook input priority 0; policy accept;
        iif "lo" accept
        ct state established,related accept
    }}

    chain forward {{
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
        iif "{lan}" oif "{wan}" accept
    }}

    chain output {{
        type filter hook output priority 0; policy accept;
    }}

    chain postrouting {{
        type nat hook postrouting priority srcnat; policy accept;
        oif "{wan}" masquerade
    }}
}}
"""
    run(["nft", "delete", "table", "inet", "ninjaku"])
    r = run(["nft", "-f", "-"], input_text=ruleset)
    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def nat_down():
    r = run(["nft", "delete", "table", "inet", "ninjaku"])
    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def enable_router():
    results = {}

    results["lan_up"] = lan_up()
    results["forward_on"] = enable_forward()
    results["nat_up"] = nat_up()

    dhcp = run(["systemctl", "restart", "dnsmasq"])
    results["dhcp_restart"] = {
        "ok": dhcp["ok"],
        "stdout": dhcp["stdout"],
        "stderr": dhcp["stderr"],
    }

    ok = all(v.get("ok", False) for v in results.values())

    if ok:
        c = current()
        set("router.enabled", "true")
        set("router.wan", c["wan"])
        set("router.lan", c["lan"])
        set("router.lan_ip", c["lan_ip"])
        set("dhcp.enabled", "true")
        set("firewall.enabled", "true")

    return {
        "ok": ok,
        "results": results,
    }

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "lan-up":
        return lan_up()
    if command == "forward-on":
        return enable_forward()
    if command == "nat-up":
        return nat_up()
    if command == "nat-down":
        return nat_down()
    if command == "enable":
        return enable_router()

    raise Exception(f"Unknown router command: {command}")
