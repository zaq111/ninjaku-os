NAME = "network"
VERSION = "1.1"

from lib import network_service

def execute(command, **kwargs):
    if command == "status":
        return network_service.status()

    raise Exception(f"Unknown network command: {command}")
