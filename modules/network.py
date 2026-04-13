NAME = "network"
VERSION = "1.0"

from lib.system import run

def status():
    return {
        "interfaces": run(["ip", "-br", "addr"])["stdout"],
        "routes": run(["ip", "route"])["stdout"],
        "dns": run(["cat", "/etc/resolv.conf"])["stdout"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()

    raise Exception(f"Unknown network command: {command}")
