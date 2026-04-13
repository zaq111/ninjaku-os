NAME = "profiles"
VERSION = "1.0"

from lib.db import connect

DEFAULT_PROFILES = [
    ("default", "Default profile"),
    ("staff", "Staff / trusted users"),
    ("guest", "Guest users"),
    ("blocked", "Blocked devices"),
]

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS profiles (
                name TEXT PRIMARY KEY,
                description TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        for name, desc in DEFAULT_PROFILES:
            db.execute(
                "INSERT OR IGNORE INTO profiles(name, description) VALUES(?,?)",
                (name, desc)
            )

def list_profiles():
    ensure_table()
    with connect() as db:
        cur = db.execute("SELECT name, description FROM profiles ORDER BY name")
        rows = cur.fetchall()
    return [{"name": r[0], "description": r[1]} for r in rows]

def execute(command, **kwargs):
    if command == "status":
        return {"profiles": list_profiles()}

    raise Exception(f"Unknown profiles command: {command}")
