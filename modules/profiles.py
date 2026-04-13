NAME = "profiles"
VERSION = "1.1"

from lib.db import connect

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

        # migrate older table if is_system belum ada
        cols = [r[1] for r in db.execute("PRAGMA table_info(profiles)").fetchall()]
        if "is_system" not in cols:
            db.execute("ALTER TABLE profiles ADD COLUMN is_system INTEGER DEFAULT 0")

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
    ensure_table()
    with connect() as db:
        cur = db.execute("""
            SELECT name, description, is_system
            FROM profiles
            ORDER BY is_system DESC, name
        """)
        rows = cur.fetchall()

    return [{
        "name": r[0],
        "description": r[1],
        "is_system": bool(r[2]),
    } for r in rows]

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

def execute(command, **kwargs):
    if command == "status":
        return {"profiles": list_profiles()}

    if command == "add":
        return add_profile(kwargs.get("name", ""), kwargs.get("description", ""))

    if command == "delete":
        return delete_profile(kwargs.get("name", ""))

    raise Exception(f"Unknown profiles command: {command}")
