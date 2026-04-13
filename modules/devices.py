NAME = "devices"
VERSION = "1.2"

from pathlib import Path
from lib.db import connect
from lib.policy import resolve
from lib.modules import execute as module_execute

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

    return {"ok": True, "count": len(leases)}

def list_devices():
    with connect() as db:
        cur = db.execute("""
            SELECT mac, ip, hostname, alias, notes, profile, last_seen, seen_count
            FROM devices
            ORDER BY last_seen DESC
        """)
        rows = cur.fetchall()

    devices = []
    for r in rows:
        mac = r[0]
        effective_policy = resolve(mac=mac)
        devices.append({
            "mac": mac,
            "ip": r[1],
            "hostname": r[2],
            "alias": r[3],
            "notes": r[4],
            "profile": r[5],
            "policy_internet": effective_policy.get("internet"),
            "policy_bandwidth": effective_policy.get("bandwidth"),
            "policy_dns": effective_policy.get("dns_filter"),
            "last_seen": r[6],
            "seen_count": r[7],
        })
    return devices

def update_device(mac, field, value):
    allowed = {"alias", "notes", "profile"}
    if field not in allowed:
        return {"ok": False, "error": "field not allowed"}

    mac = mac.lower()

    with connect() as db:
        db.execute("""
            INSERT INTO devices(mac)
            VALUES(?)
            ON CONFLICT(mac) DO NOTHING
        """, (mac,))
        db.execute(f"UPDATE devices SET {field}=? WHERE mac=?", (value, mac))

    apply_result = None
    if field == "profile":
        try:
            apply_result = module_execute("policy", "apply")
        except Exception as e:
            apply_result = {"ok": False, "error": str(e)}

    return {
        "ok": True,
        "mac": mac,
        "field": field,
        "value": value,
        "policy_applied": apply_result,
    }

def status():
    sync()
    devices = list_devices()
    return {"count": len(devices), "devices": devices}

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "sync":
        return sync()
    if command == "set-alias":
        return update_device(kwargs["mac"], "alias", kwargs["value"])
    if command == "set-notes":
        return update_device(kwargs["mac"], "notes", kwargs["value"])
    if command == "set-profile":
        return update_device(kwargs["mac"], "profile", kwargs["value"])

    raise Exception(f"Unknown devices command: {command}")
