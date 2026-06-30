NAME = "qos_pipes"
VERSION = "1.0"

from lib import qos_pipe_service

def execute(command, **kwargs):
    if command == "status":
        return qos_pipe_service.status()

    if command == "save":
        return qos_pipe_service.save_pipe(kwargs)

    if command == "delete":
        return qos_pipe_service.delete_pipe(kwargs.get("id", ""))

    raise Exception(f"Unknown qos_pipes command: {command}")
