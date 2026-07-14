import sqlite3
from pathlib import Path
from contextlib import contextmanager

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
    seen_count INTEGER DEFAULT 1,
    status TEXT DEFAULT 'unknown'
);
"""

@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    db = sqlite3.connect(DB_PATH, timeout=30)
    try:
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("PRAGMA foreign_keys=ON")
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH, timeout=30) as db:
        db.execute("PRAGMA busy_timeout=30000")
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA foreign_keys=ON")
        db.executescript(SCHEMA)
        db.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
            ("os_name", "Ninjaku OS Router")
        )
        db.execute(
            "INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
            ("version", "1.0-alpha")
        )
