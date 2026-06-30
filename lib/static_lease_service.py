from lib.db import connect
from lib.system import run
from lib.settings import get

CONF = "/etc/dnsmasq.d/ninjaku-static-leases.conf"

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS static_leases (
                mac TEXT PRIMARY KEY,
                ip TEXT NOT NULL,
                hostname TEXT DEFAULT '',
                enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

def list_leases():
    ensure_table()
    with connect() as db:
        rows = db.execute("""
            SELECT mac, ip, hostname, enabled, created_at, updated_at
            FROM static_leases
            ORDER BY ip
        """).fetchall()

    return [{
        "mac": r[0],
        "ip": r[1],
        "hostname": r[2],
        "enabled": bool(r[3]),
        "created_at": r[4],
        "updated_at": r[5],
    } for r in rows]

def set_lease(mac, ip, hostname=""):
    ensure_table()
    mac = mac.lower().strip()

    with connect() as db:
        db.execute("""
            INSERT INTO static_leases(mac, ip, hostname, enabled)
            VALUES(?, ?, ?, 1)
            ON CONFLICT(mac) DO UPDATE SET
                ip=excluded.ip,
                hostname=excluded.hostname,
                enabled=1,
                updated_at=CURRENT_TIMESTAMP
        """, (mac, ip, hostname))

        db.execute("""
            INSERT INTO devices(mac, ip, hostname)
            VALUES(?, ?, ?)
            ON CONFLICT(mac) DO UPDATE SET
                ip=excluded.ip,
                hostname=excluded.hostname
        """, (mac, ip, hostname))

    apply()

    return {"ok": True, "mac": mac, "ip": ip, "hostname": hostname}

def delete_lease(mac):
    ensure_table()
    mac = mac.lower().strip()

    with connect() as db:
        cur = db.execute("DELETE FROM static_leases WHERE mac=?", (mac,))
        deleted = cur.rowcount

    apply()

    return {"ok": deleted > 0, "mac": mac, "deleted": deleted}

def build_config():
    lines = [
        "# Ninjaku OS Router static DHCP leases",
        "# Generated automatically. Do not edit manually.",
        "",
    ]

    for lease in list_leases():
        if not lease["enabled"]:
            continue

        mac = lease["mac"]
        ip = lease["ip"]
        hostname = lease["hostname"]

        if hostname:
            lines.append(f"dhcp-host={mac},{ip},{hostname},infinite")
        else:
            lines.append(f"dhcp-host={mac},{ip},infinite")

    lines.append("")
    return "\n".join(lines)

def apply():
    ensure_table()

    with open(CONF, "w") as f:
        f.write(build_config())

    r = run(["systemctl", "restart", "dnsmasq"])

    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
        "conf": CONF,
    }

def status():
    return {
        "leases": list_leases(),
        "config": build_config(),
    }
