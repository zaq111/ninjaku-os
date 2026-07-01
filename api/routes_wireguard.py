from flask import Blueprint, request
from lib.modules import execute
from api.common import ok, fail

wireguard_bp = Blueprint("wireguard_api", __name__)

ENDPOINTS = [
    ("GET",    "/api/v1/wireguard"),
    ("POST",   "/api/v1/wireguard/server"),
    ("POST",   "/api/v1/wireguard/peers"),
    ("DELETE", "/api/v1/wireguard/peers/<peer_id>"),
    ("POST",   "/api/v1/wireguard/server/generate-keys"),
    ("POST",   "/api/v1/wireguard/peers/<peer_id>/generate-keys"),
    ("GET",    "/api/v1/wireguard/config"),
    ("POST",   "/api/v1/wireguard/write-config"),
    ("POST",   "/api/v1/wireguard/apply"),
    ("POST",   "/api/v1/wireguard/stop"),
    ("POST",   "/api/v1/wireguard/restart"),
    ("GET",    "/api/v1/wireguard/peers/<peer_id>/config"),
    ("GET",    "/api/v1/wireguard/peers/<peer_id>/qr"),
]

@wireguard_bp.get("/api/v1/wireguard")
def api_wireguard():
    try:
        return ok(execute("wireguard", "status"))
    except Exception as e:
        return fail(e)

@wireguard_bp.post("/api/v1/wireguard/server")
def api_wireguard_server():
    data = request.get_json(silent=True) or {}
    return ok(execute("wireguard", "server", **data))

@wireguard_bp.post("/api/v1/wireguard/peers")
def api_wireguard_peer_save():
    data = request.get_json(silent=True) or {}
    return ok(execute("wireguard", "save-peer", **data))

@wireguard_bp.delete("/api/v1/wireguard/peers/<peer_id>")
def api_wireguard_peer_delete(peer_id):
    return ok(execute("wireguard", "delete-peer", id=peer_id))


@wireguard_bp.post("/api/v1/wireguard/server/generate-keys")
def api_wireguard_server_generate_keys():
    return ok(execute("wireguard", "generate-server-keys"))

@wireguard_bp.post("/api/v1/wireguard/peers/<peer_id>/generate-keys")
def api_wireguard_peer_generate_keys(peer_id):
    data = request.get_json(silent=True) or {}
    preshared = data.get("preshared", True)
    return ok(execute("wireguard", "generate-peer-keys", id=peer_id, preshared=preshared))


@wireguard_bp.get("/api/v1/wireguard/config")
def api_wireguard_config():
    return ok(execute("wireguard", "generate-config"))


@wireguard_bp.post("/api/v1/wireguard/write-config")
def api_wireguard_write_config():
    return ok(execute("wireguard", "write-config"))


@wireguard_bp.post("/api/v1/wireguard/apply")
def api_wireguard_apply():
    return ok(execute("wireguard", "apply"))

@wireguard_bp.post("/api/v1/wireguard/stop")
def api_wireguard_stop():
    return ok(execute("wireguard", "stop"))

@wireguard_bp.post("/api/v1/wireguard/restart")
def api_wireguard_restart():
    return ok(execute("wireguard", "restart"))


@wireguard_bp.get("/api/v1/wireguard/peers/<peer_id>/config")
def api_wireguard_peer_config(peer_id):
    endpoint_host = request.args.get("endpoint", "")
    return ok(execute("wireguard", "export-peer-config", id=peer_id, endpoint_host=endpoint_host))


@wireguard_bp.get("/api/v1/wireguard/peers/<peer_id>/qr")
def api_wireguard_peer_qr(peer_id):
    endpoint_host = request.args.get("endpoint", "")
    return ok(execute("wireguard", "export-peer-qr", id=peer_id, endpoint_host=endpoint_host))
