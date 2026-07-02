from lib.db import connect
from lib.policy import resolve
from lib.modules import execute as module_execute

DEFAULT_POLICIES = {
    "default": {
        "internet": "allow",
        "bandwidth": "unlimited",
        "dns_filter": "none",
        "schedule": "always",
        "priority": "normal",
    },
    "staff": {
        "internet": "allow",
        "bandwidth": "unlimited",
        "dns_filter": "none",
        "schedule": "always",
        "priority": "high",
    },
    "guest": {
        "internet": "allow",
        "bandwidth": "limited",
        "dns_filter": "basic",
        "schedule": "always",
        "priority": "low",
    },
    "blocked": {
        "internet": "deny",
        "bandwidth": "none",
        "dns_filter": "none",
        "schedule": "never",
        "priority": "blocked",
    },
}

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS policies (
                profile TEXT PRIMARY KEY,
                internet TEXT DEFAULT 'allow',
                bandwidth TEXT DEFAULT 'unlimited',
                dns_filter TEXT DEFAULT 'none',
                schedule TEXT DEFAULT 'always',
                priority TEXT DEFAULT 'normal',
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cols = [r[1] for r in db.execute("PRAGMA table_info(policies)").fetchall()]
        extra_cols = {
            "qos_enabled": "INTEGER DEFAULT 0",
            "qos_download": "TEXT DEFAULT ''",
            "qos_upload": "TEXT DEFAULT ''",
            "qos_priority": "TEXT DEFAULT 'normal'",
        }
        for col, spec in extra_cols.items():
            if col not in cols:
                db.execute(f"ALTER TABLE policies ADD COLUMN {col} {spec}")

        for profile, p in DEFAULT_POLICIES.items():
            db.execute("""
                INSERT OR IGNORE INTO policies
                (profile, internet, bandwidth, dns_filter, schedule, priority)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                profile,
                p["internet"],
                p["bandwidth"],
                p["dns_filter"],
                p["schedule"],
                p["priority"],
            ))

def sync_profiles_to_policies():
    from lib.profiles_service import list_profiles
    ensure_table()
    with connect() as db:
        for prof in list_profiles():
            name = prof.get("name")
            if not name:
                continue
            db.execute("""
                INSERT OR IGNORE INTO policies
                (profile, internet, bandwidth, dns_filter, schedule, priority,
                 qos_enabled, qos_download, qos_upload, qos_priority)
                VALUES (?, 'allow', 'unlimited', 'none', 'always', 'normal',
                        0, '', '', 'normal')
            """, (name,))


def list_policies():
    sync_profiles_to_policies()

    with connect() as db:
        cur = db.execute("""
            SELECT profile, internet, bandwidth, dns_filter, schedule, priority,
                   qos_enabled, qos_download, qos_upload, qos_priority, updated_at
            FROM policies
            ORDER BY profile
        """)
        rows = cur.fetchall()

    return [{
        "profile": r[0],
        "internet": r[1],
        "bandwidth": r[2],
        "dns_filter": r[3],
        "schedule": r[4],
        "priority": r[5],
        "qos_enabled": bool(r[6]),
        "qos_download": r[7],
        "qos_upload": r[8],
        "qos_priority": r[9],
        "updated_at": r[10],
    } for r in rows]

def set_policy(profile, field, value):
    ensure_table()

    allowed = {
        "internet", "bandwidth", "dns_filter", "schedule", "priority",
        "qos_enabled", "qos_download", "qos_upload", "qos_priority"
    }
    if field not in allowed:
        return {"ok": False, "error": "field not allowed"}

    if field == "qos_enabled":
        value = 1 if str(value).lower() in ("1", "true", "yes", "on") else 0

    with connect() as db:
        db.execute("INSERT OR IGNORE INTO policies(profile) VALUES(?)", (profile,))
        db.execute(
            f"UPDATE policies SET {field}=?, updated_at=CURRENT_TIMESTAMP WHERE profile=?",
            (value, profile)
        )

    return {"ok": True, "profile": profile, "field": field, "value": value}

def apply_policy():
    firewall = module_execute("firewall", "apply-policy")

    qos = None
    try:
        qos = module_execute("qos", "apply")
    except Exception as e:
        qos = {"ok": False, "error": str(e)}

    return {
        "ok": bool(firewall.get("ok", False)) and bool(qos.get("ok", False)),
        "firewall": firewall,
        "qos": qos,
    }

def resolve_policy(mac=None, profile=None):
    return resolve(mac=mac, profile=profile)


def update_policy(profile, data):
    ensure_table()

    allowed = {
        "internet", "bandwidth", "dns_filter", "schedule", "priority",
        "qos_enabled", "qos_download", "qos_upload", "qos_priority"
    }

    changed = {}

    for k, v in data.items():
        if k not in allowed:
            continue
        r = set_policy(profile, k, v)
        if r.get("ok"):
            changed[k] = v

    return {
        "ok": True,
        "profile": profile,
        "changed": changed,
        "policy": resolve_policy(profile=profile),
    }
