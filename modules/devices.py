NAME = "devices"
VERSION = "1.0"

from pathlib import Path

LEASE_FILE = Path("/var/lib/misc/dnsmasq.leases")

def parse_leases():
    devices = []

    if not LEASE_FILE.exists():
        return devices

    for line in LEASE_FILE.read_text().splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue

        expires = parts[0]
        mac = parts[1]
        ip = parts[2]
        hostname = parts[3]
        client_id = parts[4] if len(parts) > 4 else ""

        devices.append({
            "expires": expires,
            "mac": mac,
            "ip": ip,
            "hostname": hostname,
            "client_id": client_id,
        })

    return devices

def status():
    return {
        "count": len(parse_leases()),
        "devices": parse_leases(),
    }

def execute(command, **kwargs):
    if command == "status":
        return status()

    raise Exception(f"Unknown devices command: {command}")
