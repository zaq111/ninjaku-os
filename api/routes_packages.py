from flask import Blueprint, request

from api.common import ok
from lib.modules import execute

packages_bp=Blueprint("packages_api",__name__)

ENDPOINTS=[
("GET","/api/v1/packages"),
("POST","/api/v1/packages/install"),
("POST","/api/v1/packages/remove"),
]

@packages_bp.get("/api/v1/packages")
def packages():
    return ok(execute("packages","status"))

@packages_bp.post("/api/v1/packages/install")
def install():
    data=request.get_json() or {}
    return ok(execute("packages","install",package=data["package"]))

@packages_bp.post("/api/v1/packages/remove")
def remove():
    data=request.get_json() or {}
    return ok(execute("packages","remove",package=data["package"]))
