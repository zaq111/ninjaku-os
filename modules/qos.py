NAME = "qos"
VERSION = "1.0"

from lib import qos_service

def execute(command, **kwargs):
    if command == "status":
        return qos_service.status()

    if command == "apply":
        return qos_service.apply()

    if command == "disable":
        return qos_service.clear()

    if command == "set":
        return qos_service.set_config(kwargs)

    raise Exception(f"Unknown qos command: {command}")
