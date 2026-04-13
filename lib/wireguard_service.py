import subprocess
from lib.db import connect
from lib.system import run

DEFAULT_SERVER = {
    "id": "server",
    "enabled": 0,
    "interface": "wg0",
    "listen_port": "51820",
    "address": "10.99.0.1/24",
    "private_key": "",
    "public_key": "",
    "dns": "10.99.0.1",
    "mtu": "1420",
}

def ensure_tables():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS wireguard (
                id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                interface TEXT DEFAULT 'wg0',
                listen_port TEXT DEFAULT '51820',
                address TEXT DEFAULT '10.99.0.1/24',
                private_key TEXT DEFAULT '',
                public_key TEXT DEFAULT '',
                dns TEXT DEFAULT '10.99.0.1',
                mtu TEXT DEFAULT '1420',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            CREATE TABLE IF NOT EXISTS wireguard_peers (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                enabled INTEGER DEFAULT 1,
                public_key TEXT DEFAULT '',
                private_key TEXT DEFAULT '',
                preshared_key TEXT DEFAULT '',
                allowed_ips TEXT DEFAULT '',
                endpoint TEXT DEFAULT '',
                persistent_keepalive TEXT DEFAULT '25',
                description TEXT DEFAULT '',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            INSERT OR IGNORE INTO wireguard
            (id, enabled, interface, listen_port, address, private_key, public_key, dns, mtu)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            DEFAULT_SERVER["id"],
            DEFAULT_SERVER["enabled"],
            DEFAULT_SERVER["interface"],
            DEFAULT_SERVER["listen_port"],
            DEFAULT_SERVER["address"],
            DEFAULT_SERVER["private_key"],
            DEFAULT_SERVER["public_key"],
            DEFAULT_SERVER["dns"],
            DEFAULT_SERVER["mtu"],
        ))


def wg_available():
    return run(["sh", "-c", "command -v wg"])["ok"]

def gen_private_key():
    r = run(["wg", "genkey"])
    if not r["ok"] or not r["stdout"]:
        raise Exception(r["stderr"] or "wg genkey failed")
    return r["stdout"].strip()

def gen_public_key(private_key):
    p = subprocess.run(
        ["wg", "pubkey"],
        input=(private_key + "\n").encode(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
    )
    if p.returncode != 0 or not p.stdout:
        raise Exception(p.stderr.decode(errors="ignore").strip() or "wg pubkey failed")
    return p.stdout.decode().strip()

def gen_preshared_key():
    r = run(["wg", "genpsk"])
    if not r["ok"] or not r["stdout"]:
        raise Exception(r["stderr"] or "wg genpsk failed")
    return r["stdout"].strip()

def generate_server_keys():
    ensure_tables()

    if not wg_available():
        return {"ok": False, "error": "wg command not found. Install wireguard-tools first."}

    private_key = gen_private_key()
    public_key = gen_public_key(private_key)

    with connect() as db:
        db.execute("""
            UPDATE wireguard
            SET private_key=?, public_key=?, updated_at=CURRENT_TIMESTAMP
            WHERE id='server'
        """, (private_key, public_key))

    return {
        "ok": True,
        "server": status()["server"],
    }

def generate_peer_keys(peer_id, preshared=True):
    ensure_tables()
    peer_id = normalize_id(peer_id)

    if not wg_available():
        return {"ok": False, "error": "wg command not found. Install wireguard-tools first."}

    peer = get_peer(peer_id)
    if not peer:
        return {"ok": False, "error": "peer not found", "id": peer_id}

    private_key = gen_private_key()
    public_key = gen_public_key(private_key)
    preshared_key = gen_preshared_key() if preshared else ""

    with connect() as db:
        db.execute("""
            UPDATE wireguard_peers
            SET private_key=?, public_key=?, preshared_key=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=?
        """, (private_key, public_key, preshared_key, peer_id))

    return {
        "ok": True,
        "peer": get_peer(peer_id),
    }


def boolv(v):
    return str(v).lower() in ("1", "true", "yes", "on")

def status():
    ensure_tables()

    with connect() as db:
        s = db.execute("""
            SELECT id, enabled, interface, listen_port, address,
                   private_key, public_key, dns, mtu, created_at, updated_at
            FROM wireguard
            WHERE id='server'
        """).fetchone()

        peers = db.execute("""
            SELECT id, name, enabled, public_key, private_key, preshared_key,
                   allowed_ips, endpoint, persistent_keepalive, description,
                   created_at, updated_at
            FROM wireguard_peers
            ORDER BY name
        """).fetchall()

    server = {
        "id": s[0],
        "enabled": bool(s[1]),
        "interface": s[2],
        "listen_port": s[3],
        "address": s[4],
        "has_private_key": bool(s[5]),
        "public_key": s[6],
        "dns": s[7],
        "mtu": s[8],
        "created_at": s[9],
        "updated_at": s[10],
    }

    peer_list = [{
        "id": r[0],
        "name": r[1],
        "enabled": bool(r[2]),
        "public_key": r[3],
        "has_private_key": bool(r[4]),
        "has_preshared_key": bool(r[5]),
        "allowed_ips": r[6],
        "endpoint": r[7],
        "persistent_keepalive": r[8],
        "description": r[9],
        "created_at": r[10],
        "updated_at": r[11],
    } for r in peers]

    return {
        "server": server,
        "peers": peer_list,
        "peer_count": len(peer_list),
        "running": False,
        "phase": "framework",
    }

def update_server(data):
    ensure_tables()

    allowed = {
        "enabled",
        "interface",
        "listen_port",
        "address",
        "private_key",
        "public_key",
        "dns",
        "mtu",
    }

    fields = []
    values = []

    for k, v in data.items():
        if k not in allowed:
            continue
        if k == "enabled":
            v = 1 if boolv(v) else 0
        fields.append(f"{k}=?")
        values.append(v)

    if not fields:
        return {"ok": False, "error": "no valid fields"}

    values.append("server")

    with connect() as db:
        db.execute(
            "UPDATE wireguard SET " + ", ".join(fields) + ", updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values
        )

    return {"ok": True, "server": status()["server"]}

def normalize_id(value):
    return (value or "").strip().lower().replace(" ", "-")

def save_peer(data):
    ensure_tables()

    peer_id = normalize_id(data.get("id") or data.get("name"))
    if not peer_id:
        return {"ok": False, "error": "peer id/name is required"}

    name = data.get("name") or peer_id
    enabled = 1 if boolv(data.get("enabled", True)) else 0

    with connect() as db:
        db.execute("""
            INSERT INTO wireguard_peers
            (id, name, enabled, public_key, private_key, preshared_key,
             allowed_ips, endpoint, persistent_keepalive, description)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name,
                enabled=excluded.enabled,
                public_key=excluded.public_key,
                private_key=excluded.private_key,
                preshared_key=excluded.preshared_key,
                allowed_ips=excluded.allowed_ips,
                endpoint=excluded.endpoint,
                persistent_keepalive=excluded.persistent_keepalive,
                description=excluded.description,
                updated_at=CURRENT_TIMESTAMP
        """, (
            peer_id,
            name,
            enabled,
            data.get("public_key", ""),
            data.get("private_key", ""),
            data.get("preshared_key", ""),
            data.get("allowed_ips", ""),
            data.get("endpoint", ""),
            data.get("persistent_keepalive", "25"),
            data.get("description", ""),
        ))

    return {"ok": True, "peer": get_peer(peer_id)}

def get_peer(peer_id):
    ensure_tables()
    peer_id = normalize_id(peer_id)

    with connect() as db:
        r = db.execute("""
            SELECT id, name, enabled, public_key, private_key, preshared_key,
                   allowed_ips, endpoint, persistent_keepalive, description,
                   created_at, updated_at
            FROM wireguard_peers
            WHERE id=?
        """, (peer_id,)).fetchone()

    if not r:
        return None

    return {
        "id": r[0],
        "name": r[1],
        "enabled": bool(r[2]),
        "public_key": r[3],
        "has_private_key": bool(r[4]),
        "has_preshared_key": bool(r[5]),
        "allowed_ips": r[6],
        "endpoint": r[7],
        "persistent_keepalive": r[8],
        "description": r[9],
        "created_at": r[10],
        "updated_at": r[11],
    }

def delete_peer(peer_id):
    ensure_tables()
    peer_id = normalize_id(peer_id)

    with connect() as db:
        cur = db.execute("DELETE FROM wireguard_peers WHERE id=?", (peer_id,))

    return {"ok": cur.rowcount > 0, "id": peer_id, "deleted": cur.rowcount}
