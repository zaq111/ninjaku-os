NAME = "adguard"
VERSION = "1.0"

from lib import adguard_service

def execute(command, **kwargs):
    if command == "status":
        return adguard_service.status()

    if command == "set-url":
        return adguard_service.set_url(kwargs.get("url", ""))

    if command == "install":
        return adguard_service.install()

    raise Exception(f"Unknown adguard command: {command}")
