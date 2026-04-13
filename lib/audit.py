from lib.db import connect

def list_logs(limit=20):
    with connect() as db:
        cur = db.execute(
            "SELECT id, ts, actor, action, detail FROM audit_logs ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cur.fetchall()
