NAME = "api"
VERSION = "1.0"

from lib.system import run

def status():
    return {
        "service": run(["systemctl", "is-active", "ninjaku-api"])["stdout"],
        "enabled": run(["systemctl", "is-enabled", "ninjaku-api"])["stdout"],
        "listen": run(["ss", "-tlnp"])["stdout"],
        "health": run(["curl", "-s", "http://127.0.0.1:8181/api/health"])["stdout"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()

    raise Exception(f"Unknown api command: {command}")
