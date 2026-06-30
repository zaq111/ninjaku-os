NAME = "policy"
VERSION = "1.1"

from lib import policy_service

def execute(command, **kwargs):
    if command == "status":
        return {"policies": policy_service.list_policies()}

    if command == "set":
        return policy_service.set_policy(
            kwargs.get("profile", ""),
            kwargs.get("field", ""),
            kwargs.get("value", "")
        )

    if command == "resolve":
        return policy_service.resolve_policy(
            mac=kwargs.get("mac"),
            profile=kwargs.get("profile")
        )

    if command == "apply":
        return policy_service.apply_policy()

    raise Exception(f"Unknown policy command: {command}")
