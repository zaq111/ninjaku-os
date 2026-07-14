from pathlib import Path
import ipaddress

from lib.system import run
from lib.db import connect
from lib.policy import resolve
from lib.modules import execute as module_execute
from lib.settings import get

LEASE_FILE = Path("/var/lib/misc/dnsmasq.leases")

def lan_networks():
    nets = []

    lan_ip = get("router.lan_ip", "192.168.10.1/24")
    try:
        nets.append(ipaddress.ip_interface(lan_ip).network)
    except Exception:
        pass

    try:
        from lib.wifi_service import get_config
        wifi_ip = get_config().get("ip", "")
        if wifi_ip:
            nets.append(ipaddress.ip_interface(wifi_ip).network)
    except Exception:
        pass

    return nets

def lan_network():
    nets = lan_networks()
    return nets[0]

def is_lan_ip(ip):
    try:
        addr = ipaddress.ip_address(ip)
        return any(addr in net for net in lan_networks())
    except Exception:
        return False

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

def client_interfaces():
    try:
        from lib.router_service import active_client_side
        active = active_client_side()
        if active.get("ok") and active.get("interface"):
            return {active["interface"]}
    except Exception:
        pass

    return {get("router.lan", "eth1")}


def parse_neighbors():
    devices = []
    allowed_ifs = client_interfaces()
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

        if dev not in allowed_ifs:
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
            if not is_lan_ip(d["ip"]):
                continue

            db.execute("""
                INSERT INTO devices(mac, ip, hostname, status)
                VALUES(?, ?, ?, 'online')
                ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    hostname=excluded.hostname,
                    last_seen=CURRENT_TIMESTAMP,
                    seen_count=seen_count+1,
                    status='online'
            """, (d["mac"], d["ip"], d["hostname"]))

        for d in neighbors:
            if not is_lan_ip(d["ip"]):
                continue

            db.execute("""
                INSERT INTO devices(mac, ip, status)
                VALUES(?, ?, 'online')
                ON CONFLICT(mac) DO UPDATE SET
                    ip=excluded.ip,
                    last_seen=CURRENT_TIMESTAMP,
                    seen_count=seen_count+1,
                    status='online'
            """, (d["mac"], d["ip"]))

    return {
        "ok": True,
        "lease_count": len([d for d in leases if is_lan_ip(d["ip"])]),
        "neighbor_count": len([d for d in neighbors if is_lan_ip(d["ip"])]),
        "count": len(leases) + len(neighbors),
    }

def qos_label(policy):
    if not policy.get("qos_enabled"):
        return {
            "qos_enabled": False,
            "qos_label": "QoS off",
            "qos_queue_label": "-",
        }

    mode = policy.get("qos_mode", "priority") or "priority"
    prio = policy.get("qos_priority", "normal") or "normal"

    if mode == "limiter":
        down = str(policy.get("qos_download") or "0").replace("mbit", "")
        up = str(policy.get("qos_upload") or "0").replace("mbit", "")

        if prio == "high":
            queue = "High limiter priority"
        elif prio == "low":
            queue = "Low limiter priority"
        else:
            queue = "Normal limiter priority"

        return {
            "qos_enabled": True,
            "qos_mode": mode,
            "qos_priority": prio,
            "qos_download": policy.get("qos_download", ""),
            "qos_upload": policy.get("qos_upload", ""),
            "qos_label": f"Limiter {down}/{up} Mbps",
            "qos_queue_label": queue,
        }

    return {
        "qos_enabled": True,
        "qos_mode": mode,
        "qos_priority": "",
        "qos_download": "",
        "qos_upload": "",
        "qos_label": "CAKE / Marking",
        "qos_queue_label": "Global application/protocol marking",
    }


def effective_device_status(last_seen, stored_status):
    from datetime import datetime, timezone

    if not last_seen:
        return "unknown"

    try:
        dt = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).total_seconds()
    except Exception:
        return stored_status or "unknown"

    if age <= 90:
        return "online"
    if age <= 300:
        return "idle"
    if age <= 1800:
        return "away"
    return "offline"

def last_seen_age_label(last_seen):
    from datetime import datetime, timezone

    if not last_seen:
        return "-"

    try:
        dt = datetime.fromisoformat(str(last_seen).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        sec = int((datetime.now(timezone.utc) - dt).total_seconds())
    except Exception:
        return str(last_seen)

    if sec < 60:
        return f"{sec}s ago"
    if sec < 3600:
        return f"{sec // 60}m ago"
    if sec < 86400:
        return f"{sec // 3600}h ago"
    return f"{sec // 86400}d ago"


def list_devices():
    # Read-only path. Schema migration belongs to init/write paths.
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
        q = qos_label(effective_policy)
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
            "qos_enabled": q.get("qos_enabled"),
            "qos_mode": q.get("qos_mode"),
            "qos_priority": q.get("qos_priority"),
            "qos_download": q.get("qos_download"),
            "qos_upload": q.get("qos_upload"),
            "qos_label": q.get("qos_label"),
            "qos_queue_label": q.get("qos_queue_label"),
            "last_seen": r[6],
            "last_seen_age": last_seen_age_label(r[6]),
            "seen_count": r[7],
            "status": effective_device_status(r[6], r[8]),
        })

    rank = {"online": 0, "idle": 1, "away": 2, "unknown": 3, "offline": 4}
    devices.sort(key=lambda d: (
        rank.get(d.get("status"), 9),
        (d.get("alias") or d.get("hostname") or d.get("ip") or "").lower()
    ))
    return devices

def status():
    # Read-only. Do not sync/discover here.
    # Overview and Devices pages must not block on DB writes or neighbor discovery.
    devices = list_devices()
    counts = {}
    for d in devices:
        st = d.get("status", "unknown")
        counts[st] = counts.get(st, 0) + 1

    return {
        "count": len(devices),
        "online": counts.get("online", 0),
        "idle": counts.get("idle", 0),
        "away": counts.get("away", 0),
        "offline": counts.get("offline", 0),
        "unknown": counts.get("unknown", 0),
        "devices": devices,
    }

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
    net = lan_network()
    with connect() as db:
        cur = db.execute("SELECT mac, ip FROM devices WHERE ip != ''")
        rows = cur.fetchall()

        deleted = 0
        for mac, ip in rows:
            try:
                if ipaddress.ip_address(ip) not in net:
                    db.execute("DELETE FROM devices WHERE mac=?", (mac,))
                    deleted += 1
            except Exception:
                db.execute("DELETE FROM devices WHERE mac=?", (mac,))
                deleted += 1

    return {
        "ok": True,
        "deleted": deleted,
        "lan_prefix": str(net),
    }

def mark_offline(minutes=5):
    with connect() as db:
        cur = db.execute("""
            UPDATE devices
            SET status='offline'
            WHERE status='online'
              AND datetime(last_seen) < datetime('now', ?)
        """, (f"-{int(minutes)} minutes",))
        changed = cur.rowcount

    return {
        "ok": True,
        "changed": changed,
        "minutes": minutes,
    }
