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

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "lan-up":
        return lan_up()

    raise Exception(f"Unknown router command: {command}")
