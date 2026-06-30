NAME = "static_leases"
VERSION = "1.0"

from lib import static_lease_service

def execute(command, **kwargs):
    if command == "status":
        return static_lease_service.status()

    if command == "set":
        return static_lease_service.set_lease(
            kwargs.get("mac", ""),
            kwargs.get("ip", ""),
            kwargs.get("hostname", "")
        )

    if command == "delete":
        return static_lease_service.delete_lease(kwargs.get("mac", ""))

    if command == "apply":
        return static_lease_service.apply()

    raise Exception(f"Unknown static_leases command: {command}")
