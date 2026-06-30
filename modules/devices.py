NAME = "devices"
VERSION = "1.2"

from pathlib import Path
from lib.system import run
from lib.db import connect
from lib.policy import resolve
from lib.modules import execute as module_execute
from lib.settings import get

LEASE_FILE = Path("/var/lib/misc/dnsmasq.leases")


def ensure_schema():
    with connect() as db:
        cols = [r[1] for r in db.execute("PRAGMA table_info(devices)").fetchall()]
        if "status" not in cols:
            db.execute("ALTER TABLE devices ADD COLUMN status TEXT DEFAULT 'unknown'")

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


def parse_neighbors():
    devices = []
    lan_if = get("router.lan", "eth1")
    out = run(["ip", "neigh"])["stdout"]

    for line in out.splitlines():
        parts = line.split()
        if len(parts) < 5:
            continue

        ip = parts[0]
        dev = ""
        mac = ""
        state = parts[-1]

        if "dev" in parts:
            dev = parts[parts.index("dev") + 1]

        if "lladdr" in parts:
            mac = parts[parts.index("lladdr") + 1].lower()

        if not mac:
            continue

        if dev != lan_if:
            continue

        devices.append({
            "ip": ip,
            "mac": mac,
            "hostname": "",
            "interface": dev,
            "state": state,
        })

    return devices

def sync():
    ensure_schema()
    leases = parse_leases()
    neighbors = parse_neighbors()

    with connect() as db:
        for d in leases:
            db.execute("""
                INSERT INTO devices(mac, ip, hostname)
                VALUES(?, ?, ?)
                ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    hostname=excluded.hostname,
                    last_seen=CURRENT_TIMESTAMP,
                    seen_count=seen_count+1,
                    status='online'
            """, (d["mac"], d["ip"], d["hostname"]))

        for d in neighbors:
            db.execute("""
                INSERT INTO devices(mac, ip)
                VALUES(?, ?)
                ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    last_seen=CURRENT_TIMESTAMP,
                    seen_count=seen_count+1,
                    status='online'
            """, (d["mac"], d["ip"]))

    return {
        "ok": True,
        "lease_count": len(leases),
        "neighbor_count": len(neighbors),
        "count": len(leases) + len(neighbors),
    }

def list_devices():
    with connect() as db:
        cur = db.execute("""
            SELECT mac, ip, hostname, alias, notes, profile, last_seen, seen_count, status
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
            "status": r[8],
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


def cleanup_wan():
    # Untuk v1, LAN subnet diambil dari router.lan_ip, contoh 192.168.10.1/24.
    # Kita ambil prefix sederhana: 192.168.10.
    lan_ip = get("router.lan_ip", "192.168.10.1/24").split("/")[0]
    prefix = ".".join(lan_ip.split(".")[:3]) + "."

    with connect() as db:
        cur = db.execute(
            "DELETE FROM devices WHERE ip != '' AND ip NOT LIKE ?",
            (prefix + "%",)
        )
        deleted = cur.rowcount

    return {
        "ok": True,
        "deleted": deleted,
        "lan_prefix": prefix,
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
    if command == "cleanup-wan":
        return cleanup_wan()
    if command == "set-alias":
        return update_device(kwargs["mac"], "alias", kwargs["value"])
    if command == "set-notes":
        return update_device(kwargs["mac"], "notes", kwargs["value"])
    if command == "set-profile":
        return update_device(kwargs["mac"], "profile", kwargs["value"])

    raise Exception(f"Unknown devices command: {command}")
