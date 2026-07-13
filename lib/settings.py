from lib.db import connect

def get(key, default=None):
    with connect() as db:
        cur = db.execute("SELECT value FROM settings WHERE key=?", (key,))
        row = cur.fetchone()
        return row[0] if row else default

def set(key, value):
    with connect() as db:
        db.execute(
            "INSERT INTO settings(key,value) VALUES(?,?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, str(value))
        )

def get_many(keys):
    keys = list(keys)
    if not keys:
        return {}

    placeholders = ",".join("?" for _ in keys)

    with connect() as db:
        cur = db.execute(
            f"SELECT key, value FROM settings WHERE key IN ({placeholders})",
            keys,
        )
        return {key: value for key, value in cur.fetchall()}


def get_bool(key, default=False):
    value = get(key, None)
    if value is None:
        return default
    return str(value).lower() in ("1", "true", "yes", "on", "enabled")

def list_all():
    with connect() as db:
        cur = db.execute("SELECT key, value FROM settings ORDER BY key")
        return cur.fetchall()
