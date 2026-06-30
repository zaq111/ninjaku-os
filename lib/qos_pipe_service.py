from lib.db import connect

DEFAULT_PIPES = [
    ("office", "Office", "90mbit", "90mbit", "high", "Default office QoS pipe"),
    ("guest", "Guest", "20mbit", "5mbit", "low", "Guest users QoS pipe"),
    ("kids", "Kids", "5mbit", "2mbit", "low", "Kids QoS pipe"),
]

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS qos_pipes (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                download TEXT NOT NULL DEFAULT 'unlimited',
                upload TEXT NOT NULL DEFAULT 'unlimited',
                priority TEXT NOT NULL DEFAULT 'normal',
                engine TEXT NOT NULL DEFAULT 'cake',
                diffserv TEXT NOT NULL DEFAULT 'diffserv4',
                nat INTEGER NOT NULL DEFAULT 1,
                ack_filter INTEGER NOT NULL DEFAULT 1,
                overhead TEXT NOT NULL DEFAULT '0',
                mpu TEXT NOT NULL DEFAULT '0',
                rtt TEXT NOT NULL DEFAULT '',
                description TEXT NOT NULL DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        for pid, name, down, up, prio, desc in DEFAULT_PIPES:
            db.execute("""
                INSERT OR IGNORE INTO qos_pipes
                (id, name, download, upload, priority, description)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pid, name, down, up, prio, desc))

def list_pipes():
    ensure_table()
    with connect() as db:
        rows = db.execute("""
            SELECT id, name, download, upload, priority, engine, diffserv,
                   nat, ack_filter, overhead, mpu, rtt, description,
                   created_at, updated_at
            FROM qos_pipes
            ORDER BY name
        """).fetchall()

    return [{
        "id": r[0],
        "name": r[1],
        "download": r[2],
        "upload": r[3],
        "priority": r[4],
        "engine": r[5],
        "diffserv": r[6],
        "nat": bool(r[7]),
        "ack_filter": bool(r[8]),
        "overhead": r[9],
        "mpu": r[10],
        "rtt": r[11],
        "description": r[12],
        "created_at": r[13],
        "updated_at": r[14],
    } for r in rows]

def get_pipe(pipe_id):
    ensure_table()
    for p in list_pipes():
        if p["id"] == pipe_id:
            return p
    return None

def save_pipe(data):
    ensure_table()

    pipe_id = (data.get("id") or data.get("name") or "").lower().strip().replace(" ", "-")
    if not pipe_id:
        raise Exception("pipe id is required")

    name = data.get("name") or pipe_id
    download = data.get("download", "unlimited")
    upload = data.get("upload", "unlimited")
    priority = data.get("priority", "normal")
    engine = data.get("engine", "cake")
    diffserv = data.get("diffserv", "diffserv4")
    nat = 1 if str(data.get("nat", "true")).lower() in ("1", "true", "yes", "on") else 0
    ack_filter = 1 if str(data.get("ack_filter", "true")).lower() in ("1", "true", "yes", "on") else 0
    overhead = data.get("overhead", "0")
    mpu = data.get("mpu", "0")
    rtt = data.get("rtt", "")
    description = data.get("description", "")

    with connect() as db:
        db.execute("""
            INSERT INTO qos_pipes
            (id, name, download, upload, priority, engine, diffserv, nat,
             ack_filter, overhead, mpu, rtt, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                download=excluded.download,
                upload=excluded.upload,
                priority=excluded.priority,
                engine=excluded.engine,
                diffserv=excluded.diffserv,
                nat=excluded.nat,
                ack_filter=excluded.ack_filter,
                overhead=excluded.overhead,
                mpu=excluded.mpu,
                rtt=excluded.rtt,
                description=excluded.description,
                updated_at=CURRENT_TIMESTAMP
        """, (
            pipe_id, name, download, upload, priority, engine, diffserv,
            nat, ack_filter, overhead, mpu, rtt, description
        ))

    return {"ok": True, "pipe": get_pipe(pipe_id)}

def delete_pipe(pipe_id):
    ensure_table()
    with connect() as db:
        cur = db.execute("DELETE FROM qos_pipes WHERE id=?", (pipe_id,))
    return {"ok": cur.rowcount > 0, "id": pipe_id, "deleted": cur.rowcount}

def status():
    pipes = list_pipes()
    return {"count": len(pipes), "pipes": pipes}
