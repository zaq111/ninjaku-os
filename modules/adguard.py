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

    if command == "protection":
        return adguard_service.set_protection(kwargs.get("enabled", True))

    if command == "update-filters":
        return adguard_service.update_filters()

    if command == "querylog":
        return adguard_service.querylog(kwargs.get("limit", 20))

    raise Exception(f"Unknown adguard command: {command}")
