from lib.db import connect
from lib.system import run
from lib import dhcp_service

CONF = "/etc/dnsmasq.d/ninjaku-dns-filter.conf"

DEFAULT_BLOCKS = [
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "ads.youtube.com",
    "adservice.google.com",
]

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS dns_filter_domains (
                domain TEXT PRIMARY KEY,
                list_name TEXT DEFAULT 'manual',
                enabled INTEGER DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for d in DEFAULT_BLOCKS:
            db.execute("""
                INSERT OR IGNORE INTO dns_filter_domains(domain, list_name, enabled)
                VALUES(?, 'default', 1)
            """, (d,))

def list_domains():
    ensure_table()
    with connect() as db:
        rows = db.execute("""
            SELECT domain, list_name, enabled, created_at
            FROM dns_filter_domains
            ORDER BY domain
        """).fetchall()
    return [{
        "domain": r[0],
        "list_name": r[1],
        "enabled": bool(r[2]),
        "created_at": r[3],
    } for r in rows]

def add_domain(domain, list_name="manual"):
    ensure_table()
    domain = domain.lower().strip().strip(".")
    with connect() as db:
        db.execute("""
            INSERT OR REPLACE INTO dns_filter_domains(domain, list_name, enabled)
            VALUES(?, ?, 1)
        """, (domain, list_name))
    apply()
    return {"ok": True, "domain": domain}

def delete_domain(domain):
    ensure_table()
    domain = domain.lower().strip().strip(".")
    with connect() as db:
        cur = db.execute("DELETE FROM dns_filter_domains WHERE domain=?", (domain,))
    apply()
    return {"ok": cur.rowcount > 0, "domain": domain, "deleted": cur.rowcount}

def build_config():
    lines = [
        "# Ninjaku OS Router DNS Filter",
        "# Generated automatically. Do not edit manually.",
        "",
    ]

    for d in list_domains():
        if d["enabled"]:
            lines.append(f"address=/{d['domain']}/0.0.0.0")

    lines.append("")
    return "\n".join(lines)

def apply():
    ensure_table()
    with open(CONF, "w") as f:
        f.write(build_config())

    r = dhcp_service.reload_dnsmasq("dns_filter_apply")
    return {
        "ok": r["ok"],
        "skipped": r.get("skipped", False),
        "state": r.get("state"),
        "conf": CONF,
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def status():
    domains = list_domains()
    return {
        "enabled_domains": len([d for d in domains if d["enabled"]]),
        "domains": domains,
        "config": build_config(),
        "conf": CONF,
    }
