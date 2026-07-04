from flask import Blueprint, request

from api.common import ok, fail
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

def _package_from_request():
    data = request.get_json(silent=True) or {}
    package = str(data.get("package", "")).strip()

    if not package:
        return None

    return package

@packages_bp.post("/api/v1/packages/install")
def install():
    package = _package_from_request()
    if not package:
        return fail("package is required", 400, "VALIDATION_ERROR")

    return ok(execute("packages", "install", package=package))

@packages_bp.post("/api/v1/packages/remove")
def remove():
    package = _package_from_request()
    if not package:
        return fail("package is required", 400, "VALIDATION_ERROR")

    return ok(execute("packages", "remove", package=package))
