NAME = "tailscale"
VERSION = "1.0"

from lib import tailscale_service

def execute(command, **kwargs):
    if command == "status":
        return tailscale_service.status()

    if command == "up":
        return tailscale_service.up(kwargs.get("args", []))

    if command == "down":
        return tailscale_service.down()

    if command == "logout":
        return tailscale_service.logout()

    raise Exception(f"Unknown tailscale command: {command}")
