import sqlite3
from pathlib import Path

DB_PATH = Path("/var/lib/ninjaku/ninjaku.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts DATETIME DEFAULT CURRENT_TIMESTAMP,
    actor TEXT DEFAULT 'system',
    action TEXT NOT NULL,
    detail TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS devices (
    mac TEXT PRIMARY KEY,
    ip TEXT DEFAULT '',
    hostname TEXT DEFAULT '',
    alias TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    profile TEXT DEFAULT 'default',
    first_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_seen DATETIME DEFAULT CURRENT_TIMESTAMP,
    seen_count INTEGER DEFAULT 1
);
"""

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    with connect() as db:
        db.executescript(SCHEMA)
        db.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
            ("os_name", "Ninjaku OS Router")
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
            ("version", "1.0-alpha")
        )
