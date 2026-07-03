NAME = "router"
VERSION = "1.3"

from lib import router_service

def execute(command, **kwargs):
    if command == "status":
        return router_service.status()

    if command == "lan-up":
        return router_service.lan_up()

    if command == "forward-on":
        return router_service.enable_forward()

    if command == "nat-up":
        return router_service.nat_up()

    if command == "nat-down":
        return router_service.nat_down()

    if command == "ensure-gateway":
        return router_service.ensure_gateway()

    if command == "enable":
        return router_service.enable_router()

    if command == "disable":
        return router_service.disable_router()

    raise Exception(f"Unknown router command: {command}")
