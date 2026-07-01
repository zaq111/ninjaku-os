NAME = "wifi"
VERSION = "1.0"

from lib import wifi_service

def execute(command, **kwargs):
    if command == "status":
        return wifi_service.status()

    if command == "config":
        return wifi_service.update_config(kwargs)

    if command == "generate-config":
        return wifi_service.hostapd_config_text()

    if command == "write-config":
        return wifi_service.write_hostapd_config()

    raise Exception(f"Unknown wifi command: {command}")
