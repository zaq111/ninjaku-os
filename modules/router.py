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

def execute(command, **kwargs):
    if command == "status":
        return status()

    raise Exception(f"Unknown router command: {command}")
