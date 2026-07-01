NAME = "wireguard"
VERSION = "1.0"

from lib import wireguard_service

def execute(command, **kwargs):
    if command == "status":
        return wireguard_service.runtime_status()

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

    if command == "generate-config":
        return wireguard_service.generate_config_text()

    if command == "write-config":
        return wireguard_service.write_config()

    if command == "apply":
        return wireguard_service.apply()

    if command == "stop":
        return wireguard_service.stop()

    if command == "restart":
        return wireguard_service.restart()

    if command == "export-peer-config":
        return wireguard_service.export_peer_config(
            kwargs.get("id", ""),
            kwargs.get("endpoint_host", "")
        )

    if command == "export-peer-qr":
        return wireguard_service.export_peer_qr_svg(
            kwargs.get("id", ""),
            kwargs.get("endpoint_host", "")
        )

    raise Exception(f"Unknown wireguard command: {command}")
