NAME = "dns_filter"
VERSION = "1.0"

from lib import dns_filter_service

def execute(command, **kwargs):
    if command == "status":
        return dns_filter_service.status()

    if command == "add":
        return dns_filter_service.add_domain(kwargs.get("domain", ""))

    if command == "delete":
        return dns_filter_service.delete_domain(kwargs.get("domain", ""))

    if command == "apply":
        return dns_filter_service.apply()

    if command == "import":
        return dns_filter_service.import_file(
            kwargs.get("path", ""),
            kwargs.get("list_name", "imported")
        )

    raise Exception(f"Unknown dns_filter command: {command}")
