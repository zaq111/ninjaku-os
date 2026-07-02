from lib.db import connect

DEFAULT_POLICY = {
    "profile": "default",
    "internet": "allow",
    "bandwidth": "unlimited",
    "dns_filter": "none",
    "schedule": "always",
    "priority": "normal",
    "qos_enabled": False,
    "qos_download": "",
    "qos_upload": "",
    "qos_priority": "normal",
    "qos_mode": "priority",
}

def ensure_profile_policy_columns():
    with connect() as db:
        cols = [r[1] for r in db.execute("PRAGMA table_info(profiles)").fetchall()]
        extra_cols = {
            "internet": "TEXT DEFAULT 'allow'",
            "bandwidth": "TEXT DEFAULT 'unlimited'",
            "dns_filter": "TEXT DEFAULT 'none'",
            "schedule": "TEXT DEFAULT 'always'",
            "priority": "TEXT DEFAULT 'normal'",
            "qos_enabled": "INTEGER DEFAULT 0",
            "qos_download": "TEXT DEFAULT ''",
            "qos_upload": "TEXT DEFAULT ''",
            "qos_priority": "TEXT DEFAULT 'normal'",
            "qos_mode": "TEXT DEFAULT 'priority'",
        }
        for col, spec in extra_cols.items():
            if col not in cols:
                db.execute(f"ALTER TABLE profiles ADD COLUMN {col} {spec}")

def resolve(mac=None, profile=None):
    selected_profile = profile or "default"

    ensure_profile_policy_columns()

    with connect() as db:
        if mac and not profile:
            row = db.execute(
                "SELECT profile FROM devices WHERE mac=?",
                (mac.lower(),)
            ).fetchone()
            if row and row[0]:
                selected_profile = row[0]

        p = db.execute("""
            SELECT name, internet, bandwidth, dns_filter, schedule, priority,
                   qos_enabled, qos_download, qos_upload, qos_priority, qos_mode
            FROM profiles
            WHERE name=?
        """, (selected_profile,)).fetchone()

        if not p and selected_profile != "default":
            p = db.execute("""
                SELECT name, internet, bandwidth, dns_filter, schedule, priority,
                       qos_enabled, qos_download, qos_upload, qos_priority, qos_mode
                FROM profiles
                WHERE name='default'
            """).fetchone()

    if not p:
        return DEFAULT_POLICY.copy()

    return {
        "profile": p[0],
        "internet": p[1],
        "bandwidth": p[2],
        "dns_filter": p[3],
        "schedule": p[4],
        "priority": p[5],
        "qos_enabled": bool(p[6]),
        "qos_download": p[7],
        "qos_upload": p[8],
        "qos_priority": p[9],
        "qos_mode": p[10] if len(p) > 10 and p[10] else "priority",
    }
