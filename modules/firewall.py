NAME = "firewall"
VERSION = "1.3"

from lib import firewall_service

def execute(command, **kwargs):
    if command == "status":
        return firewall_service.status()

    if command == "init":
        return firewall_service.init()

    if command == "reset":
        return firewall_service.reset()

    if command == "apply-policy":
        return firewall_service.apply_policy()

    raise Exception(f"Unknown firewall command: {command}")
