NAME = "dhcp"
VERSION = "1.2"

from lib import dhcp_service

def execute(command, **kwargs):
    if command == "status":
        return dhcp_service.status()

    if command == "start":
        return dhcp_service.start()

    if command == "stop":
        return dhcp_service.stop()

    raise Exception(f"Unknown dhcp command: {command}")
