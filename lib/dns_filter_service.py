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
    # Read-only path.
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

def build_config(domains=None):
    if domains is None:
        domains = list_domains()

    lines = [
        "# Ninjaku OS Router DNS Filter",
        "# Generated automatically. Do not edit manually.",
        "",
    ]

    for d in domains:
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


def normalize_domain(line):
    line = line.strip()

    if not line:
        return ""

    # comments
    if line.startswith("#") or line.startswith("!"):
        return ""

    # whitelist rule, skip for now
    if line.startswith("@@"):
        return ""

    # unsupported regex / cosmetic / complex rules
    if line.startswith("/") or line.startswith("*"):
        return ""

    # AdGuard/uBlock domain rule:
    # ||example.com^
    # ||example.com^$important
    if line.startswith("||"):
        line = line[2:]
        line = line.split("^")[0]
        line = line.split("$")[0]
        line = line.split("/")[0]
        domain = line.lower().strip(".")
        return domain if is_valid_domain(domain) else ""

    # hosts style:
    # 0.0.0.0 example.com
    # 127.0.0.1 example.com
    parts = line.split()
    if len(parts) >= 2 and parts[0] in ("0.0.0.0", "127.0.0.1", "::1"):
        domain = parts[1].lower().strip(".")
        return domain if is_valid_domain(domain) else ""

    # plain domain only
    if " " not in line and "/" not in line and "$" not in line:
        domain = line.lower().strip(".")
        return domain if is_valid_domain(domain) else ""

    return ""

def is_valid_domain(domain):
    if not domain or "." not in domain:
        return False
    if len(domain) > 253:
        return False
    if "*" in domain or "/" in domain or ":" in domain:
        return False
    labels = domain.split(".")
    for label in labels:
        if not label or len(label) > 63:
            return False
        allowed = "abcdefghijklmnopqrstuvwxyz0123456789-"
        if any(c not in allowed for c in label):
            return False
        if label.startswith("-") or label.endswith("-"):
            return False
    return True

def import_file(path, list_name="imported"):
    ensure_table()
    count = 0
    skipped = 0

    with open(path, "r", errors="ignore") as f:
        lines = f.readlines()

    with connect() as db:
        for line in lines:
            domain = normalize_domain(line)
            if not domain:
                skipped += 1
                continue

            db.execute("""
                INSERT OR REPLACE INTO dns_filter_domains(domain, list_name, enabled)
                VALUES(?, ?, 1)
            """, (domain, list_name))
            count += 1

    apply()

    return {
        "ok": True,
        "imported": count,
        "skipped": skipped,
        "list_name": list_name,
    }

def status():
    domains = list_domains()
    return {
        "enabled_domains": len([d for d in domains if d["enabled"]]),
        "domains": domains,
        "config": build_config(domains),
        "conf": CONF,
    }
