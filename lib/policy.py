from lib.db import connect

DEFAULT_POLICY = {
    "profile": "default",
    "internet": "allow",
    "bandwidth": "unlimited",
    "dns_filter": "none",
    "schedule": "always",
    "priority": "normal",
}

def resolve(mac=None, profile=None):
    """
    Resolve effective policy.

    Priority:
    1. Explicit profile argument
    2. Device profile from devices table by MAC
    3. default profile
    """
    selected_profile = profile or "default"

    with connect() as db:
        if mac and not profile:
            cur = db.execute(
                "SELECT profile FROM devices WHERE mac=?",
                (mac.lower(),)
            )
            row = cur.fetchone()
            if row and row[0]:
                selected_profile = row[0]

        cur = db.execute("""
            SELECT profile, internet, bandwidth, dns_filter, schedule, priority
            FROM policies
            WHERE profile=?
        """, (selected_profile,))
        p = cur.fetchone()

        if not p and selected_profile != "default":
            cur = db.execute("""
                SELECT profile, internet, bandwidth, dns_filter, schedule, priority
                FROM policies
                WHERE profile='default'
            """)
            p = cur.fetchone()

    if not p:
        return DEFAULT_POLICY.copy()

    return {
        "profile": p[0],
        "internet": p[1],
        "bandwidth": p[2],
        "dns_filter": p[3],
        "schedule": p[4],
        "priority": p[5],
    }
