NAME = "system"
VERSION = "1.0"

from lib.system import system_status

def execute(command, **kwargs):
    if command == "status":
        return system_status()

    raise Exception(f"Unknown system command: {command}")
