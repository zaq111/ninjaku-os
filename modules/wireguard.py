NAME = "wireguard"
VERSION = "1.0"

from lib import wireguard_service

def execute(command, **kwargs):
    if command == "status":
        return wireguard_service.status()

    if command == "server":
        return wireguard_service.update_server(kwargs)

    if command == "save-peer":
        return wireguard_service.save_peer(kwargs)

    if command == "delete-peer":
        return wireguard_service.delete_peer(kwargs.get("id", ""))

    if command == "generate-server-keys":
        return wireguard_service.generate_server_keys()

    if command == "generate-peer-keys":
        return wireguard_service.generate_peer_keys(
            kwargs.get("id", ""),
            kwargs.get("preshared", True)
        )

    raise Exception(f"Unknown wireguard command: {command}")
