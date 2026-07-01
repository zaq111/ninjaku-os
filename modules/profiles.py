NAME = "profiles"
VERSION = "1.2"

from lib import profiles_service

def execute(command, **kwargs):
    if command == "status":
        return {"profiles": profiles_service.list_profiles()}

    if command == "add":
        return profiles_service.add_profile(
            kwargs.get("name", ""),
            kwargs.get("description", "")
        )

    if command == "delete":
        return profiles_service.delete_profile(kwargs.get("name", ""))

    if command == "update":
        name = kwargs.pop("name", "")
        return profiles_service.update_profile(name, kwargs)

    raise Exception(f"Unknown profiles command: {command}")
