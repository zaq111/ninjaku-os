NAME="packages"
VERSION="1.0"

from lib import package_service

def execute(command, **kwargs):

    if command=="status":
        return package_service.status()

    if command=="install":
        return package_service.apt_install(kwargs["package"])

    if command=="remove":
        return package_service.apt_remove(kwargs["package"])

    raise Exception("Unknown packages command")
