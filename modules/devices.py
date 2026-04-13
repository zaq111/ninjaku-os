NAME = "devices"
VERSION = "1.1"

from pathlib import Path
from lib.db import connect

LEASE_FILE = Path("/var/lib/misc/dnsmasq.leases")

def parse_leases():
    devices = []

    if not LEASE_FILE.exists():
        return devices

    for line in LEASE_FILE.read_text().splitlines():
        parts = line.split()
        if len(parts) < 4:
            continue

        devices.append({
            "expires": parts[0],
            "mac": parts[1].lower(),
            "ip": parts[2],
            "hostname": parts[3],
            "client_id": parts[4] if len(parts) > 4 else "",
        })

    return devices

def sync():
    leases = parse_leases()

    with connect() as db:
        for d in leases:
            db.execute("""
                INSERT INTO devices(mac, ip, hostname)
                VALUES(?, ?, ?)
                ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    hostname=excluded.hostname,
                    last_seen=CURRENT_TIMESTAMP,
                    seen_count=seen_count+1
            """, (d["mac"], d["ip"], d["hostname"]))

    return {
        "ok": True,
        "count": len(leases),
    }

def list_devices():
    with connect() as db:
        cur = db.execute("""
            SELECT mac, ip, hostname, alias, profile, last_seen, seen_count
            FROM devices
            ORDER BY last_seen DESC
        """)
        rows = cur.fetchall()

    return [{
        "mac": r[0],
        "ip": r[1],
        "hostname": r[2],
        "alias": r[3],
        "profile": r[4],
        "last_seen": r[5],
        "seen_count": r[6],
    } for r in rows]

def status():
    sync()
    devices = list_devices()
    return {
        "count": len(devices),
        "devices": devices,
    }

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "sync":
        return sync()

    raise Exception(f"Unknown devices command: {command}")
