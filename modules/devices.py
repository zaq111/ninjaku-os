NAME = "devices"
VERSION = "1.3"

from lib import device_service

def execute(command, **kwargs):
    if command == "status":
        return device_service.status()

    if command == "sync":
        return device_service.sync()

    if command == "cleanup-wan":
        return device_service.cleanup_wan()

    if command == "mark-offline":
        return device_service.mark_offline(int(kwargs.get("minutes", 5)))

    if command == "set-alias":
        return device_service.update_device(kwargs["mac"], "alias", kwargs["value"])

    if command == "set-notes":
        return device_service.update_device(kwargs["mac"], "notes", kwargs["value"])

    if command == "set-profile":
        return device_service.update_device(kwargs["mac"], "profile", kwargs["value"])

    raise Exception(f"Unknown devices command: {command}")
