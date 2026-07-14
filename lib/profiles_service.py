from lib.db import connect
from lib.modules import execute as module_execute
from lib import policy_service
from lib.policy import resolve

SYSTEM_PROFILES = {"default", "staff", "guest", "blocked"}

DEFAULT_PROFILES = [
    ("default", "Default profile", 1),
    ("staff", "Staff / trusted users", 1),
    ("guest", "Guest users", 1),
    ("blocked", "Blocked devices", 1),
]

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                is_system INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        cols = [r[1] for r in db.execute("PRAGMA table_info(profiles)").fetchall()]
        if "is_system" not in cols:
            db.execute("ALTER TABLE profiles ADD COLUMN is_system INTEGER DEFAULT 0")

        extra_cols = {
            "qos_enabled": "INTEGER DEFAULT 0",
            "qos_download": "TEXT DEFAULT ''",
            "qos_upload": "TEXT DEFAULT ''",
            "qos_priority": "TEXT DEFAULT 'normal'",
            "qos_mode": "TEXT DEFAULT 'priority'",
            "internet": "TEXT DEFAULT 'allow'",
            "bandwidth": "TEXT DEFAULT 'unlimited'",
            "dns_filter": "TEXT DEFAULT 'none'",
            "schedule": "TEXT DEFAULT 'always'",
            "priority": "TEXT DEFAULT 'normal'"
        }

        for col, spec in extra_cols.items():
            if col not in cols:
                db.execute(f"ALTER TABLE profiles ADD COLUMN {col} {spec}")

        for name, desc, is_system in DEFAULT_PROFILES:
            db.execute(
                "INSERT OR IGNORE INTO profiles(name, description, is_system) VALUES(?,?,?)",
                (name, desc, is_system)
            )
            db.execute(
                "UPDATE profiles SET is_system=1 WHERE name=?",
                (name,)
            )

def list_profiles():
    # Read-only path.
    with connect() as db:
        cur = db.execute("""
            SELECT name, description, is_system, qos_enabled, qos_download, qos_upload, qos_priority
            FROM profiles
            ORDER BY is_system DESC, name
        """)
        rows = cur.fetchall()

    result = []
    for r in rows:
        policy = resolve(profile=r[0])
        result.append({
            "name": r[0],
            "description": r[1],
            "is_system": bool(r[2]),
            "qos_enabled": bool(policy.get("qos_enabled")),
            "qos_download": policy.get("qos_download", ""),
            "qos_upload": policy.get("qos_upload", ""),
            "qos_priority": policy.get("qos_priority", "normal"),
        })

    return result

def add_profile(name, description=""):
    ensure_table()
    name = name.strip().lower()

    if not name:
        return {"ok": False, "error": "profile name is required"}

    with connect() as db:
        db.execute(
            "INSERT OR REPLACE INTO profiles(name, description, is_system) VALUES(?,?,0)",
            (name, description)
        )

    return {"ok": True, "name": name, "description": description}

def delete_profile(name):
    ensure_table()
    name = name.strip().lower()

    if name in SYSTEM_PROFILES:
        return {"ok": False, "error": "system profile cannot be deleted"}

    with connect() as db:
        cur = db.execute("DELETE FROM profiles WHERE name=?", (name,))
        deleted = cur.rowcount

    return {"ok": deleted > 0, "name": name, "deleted": deleted}


def update_profile(name, data):
    ensure_table()
    name = name.strip().lower()

    allowed = {
        "description",
        "qos_enabled",
        "qos_download",
        "qos_upload",
        "qos_priority",
    }

    fields = []
    values = []

    for k, v in data.items():
        if k not in allowed:
            continue

        if k == "qos_enabled":
            v = 1 if str(v).lower() in ("1", "true", "yes", "on") else 0

        fields.append(f"{k}=?")
        values.append(v)

    if not fields:
        return {"ok": False, "error": "no valid fields"}

    values.append(name)

    with connect() as db:
        cur = db.execute(
            "UPDATE profiles SET " + ", ".join(fields) + " WHERE name=?",
            values
        )

    for k in ("qos_enabled", "qos_download", "qos_upload", "qos_priority"):
        if k in data:
            policy_service.set_policy(name, k, data[k])

    apply_result = None
    try:
        apply_result = module_execute("qos", "apply")
    except Exception as e:
        apply_result = {"ok": False, "error": str(e)}

    return {"ok": cur.rowcount > 0, "profile": name, "qos_applied": apply_result}
