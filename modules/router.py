NAME = "router"
VERSION = "1.0"

from lib.system import run

DEFAULT = {
    "wan": "eth0",
    "lan": "eth1",
    "lan_ip": "192.168.10.1/24",
}

def status():
    return {
        "wan": DEFAULT["wan"],
        "lan": DEFAULT["lan"],
        "lan_ip": DEFAULT["lan_ip"],
        "interfaces": run(["ip", "-br", "addr"])["stdout"],
        "routes": run(["ip", "route"])["stdout"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def lan_up():
    lan = DEFAULT["lan"]
    lan_ip = DEFAULT["lan_ip"]

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
    wan = DEFAULT["wan"]
    lan = DEFAULT["lan"]

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

    raise Exception(f"Unknown router command: {command}")
