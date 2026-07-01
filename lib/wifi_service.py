from lib.db import connect
from lib.system import run

DEFAULT_WIFI = {
    "id": "main",
    "enabled": 0,
    "interface": "wlan0",
    "ssid": "Ninjaku",
    "password": "ninjaku12345",
    "country": "ID",
    "channel": "6",
    "hw_mode": "g",
    "bridge": "",
    "ip": "192.168.50.1/24",
}

def boolv(v):
    return str(v).lower() in ("1", "true", "yes", "on")

def ensure_table():
    with connect() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS wifi (
                id TEXT PRIMARY KEY,
                enabled INTEGER DEFAULT 0,
                interface TEXT DEFAULT 'wlan0',
                ssid TEXT DEFAULT 'Ninjaku',
                password TEXT DEFAULT 'ninjaku12345',
                country TEXT DEFAULT 'ID',
                channel TEXT DEFAULT '6',
                hw_mode TEXT DEFAULT 'g',
                bridge TEXT DEFAULT '',
                ip TEXT DEFAULT '192.168.50.1/24',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        db.execute("""
            INSERT OR IGNORE INTO wifi
            (id, enabled, interface, ssid, password, country, channel, hw_mode, bridge, ip)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            DEFAULT_WIFI["id"],
            DEFAULT_WIFI["enabled"],
            DEFAULT_WIFI["interface"],
            DEFAULT_WIFI["ssid"],
            DEFAULT_WIFI["password"],
            DEFAULT_WIFI["country"],
            DEFAULT_WIFI["channel"],
            DEFAULT_WIFI["hw_mode"],
            DEFAULT_WIFI["bridge"],
            DEFAULT_WIFI["ip"],
        ))

def detect_radios():
    out = run(["sh", "-c", "iw dev 2>/dev/null"])["stdout"]
    radios = []
    current = None

    for line in out.splitlines():
        line = line.strip()
        if line.startswith("Interface "):
            if current:
                radios.append(current)
            current = {"interface": line.split()[1], "type": "", "addr": ""}
        elif current and line.startswith("type "):
            current["type"] = line.split()[1]
        elif current and line.startswith("addr "):
            current["addr"] = line.split()[1]

    if current:
        radios.append(current)

    return radios

def ap_capable():
    out = run(["sh", "-c", "iw list 2>/dev/null | sed -n '/Supported interface modes:/,/Band 1:/p'"])["stdout"]
    return "* AP" in out or "\n\t\t * AP" in out

def get_config():
    ensure_table()
    with connect() as db:
        r = db.execute("""
            SELECT id, enabled, interface, ssid, password, country, channel,
                   hw_mode, bridge, ip, created_at, updated_at
            FROM wifi WHERE id='main'
        """).fetchone()

    return {
        "id": r[0],
        "enabled": bool(r[1]),
        "interface": r[2],
        "ssid": r[3],
        "password_set": bool(r[4]),
        "country": r[5],
        "channel": r[6],
        "hw_mode": r[7],
        "bridge": r[8],
        "ip": r[9],
        "created_at": r[10],
        "updated_at": r[11],
    }

def update_config(data):
    ensure_table()

    allowed = {"enabled", "interface", "ssid", "password", "country", "channel", "hw_mode", "bridge", "ip"}
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

    values.append("main")

    with connect() as db:
        db.execute(
            "UPDATE wifi SET " + ", ".join(fields) + ", updated_at=CURRENT_TIMESTAMP WHERE id=?",
            values
        )

    return {"ok": True, "config": get_config()}

def raw_config():
    ensure_table()
    with connect() as db:
        return db.execute("""
            SELECT interface, ssid, password, country, channel, hw_mode, bridge
            FROM wifi WHERE id='main'
        """).fetchone()

def hostapd_config_text():
    r = raw_config()
    if not r:
        return {"ok": False, "error": "wifi config not found"}

    interface, ssid, password, country, channel, hw_mode, bridge = r

    if len(password or "") < 8:
        return {"ok": False, "error": "wifi password must be at least 8 characters"}

    lines = [
        f"interface={interface}",
        "driver=nl80211",
        f"ssid={ssid}",
        f"country_code={country}",
        f"hw_mode={hw_mode}",
        f"channel={channel}",
        "ieee80211n=1",
        "wmm_enabled=1",
        "auth_algs=1",
        "wpa=2",
        f"wpa_passphrase={password}",
        "wpa_key_mgmt=WPA-PSK",
        "rsn_pairwise=CCMP",
    ]

    if bridge:
        lines.append(f"bridge={bridge}")

    return {
        "ok": True,
        "path": "/etc/hostapd/hostapd.conf",
        "config": "\n".join(lines) + "\n",
    }

def write_hostapd_config():
    import os

    generated = hostapd_config_text()
    if not generated.get("ok"):
        return generated

    os.makedirs("/etc/hostapd", exist_ok=True)

    tmp = generated["path"] + ".tmp"
    with open(tmp, "w") as f:
        f.write(generated["config"])

    os.chmod(tmp, 0o600)
    os.replace(tmp, generated["path"])

    # Debian hostapd default file
    with open("/etc/default/hostapd", "w") as f:
        f.write('DAEMON_CONF="/etc/hostapd/hostapd.conf"\n')

    return {
        "ok": True,
        "path": generated["path"],
        "bytes": len(generated["config"]),
    }

def runtime():
    cfg = get_config()
    iface = cfg["interface"]

    return {
        "hostapd_active": run(["systemctl", "is-active", "hostapd"])["stdout"] == "active",
        "interface": run(["ip", "-br", "addr", "show", iface])["stdout"],
        "iw": run(["iw", "dev", iface, "info"])["stdout"],
    }

def status():
    return {
        "config": get_config(),
        "radios": detect_radios(),
        "ap_capable": ap_capable(),
        "runtime": runtime(),
    }

def apply_ip():
    cfg = get_config()
    iface = cfg["interface"]
    ip = cfg["ip"]

    run(["ip", "link", "set", iface, "down"])
    run(["ip", "addr", "flush", "dev", iface])
    run(["ip", "addr", "add", ip, "dev", iface])
    run(["ip", "link", "set", iface, "up"])

    return {"ok": True, "interface": iface, "ip": ip}

def start():
    cfg_written = write_hostapd_config()
    if not cfg_written.get("ok"):
        return cfg_written

    ip_result = apply_ip()

    run(["systemctl", "unmask", "hostapd"])
    run(["systemctl", "enable", "hostapd"])

    r = run(["systemctl", "restart", "hostapd"], timeout=30)

    if r["ok"]:
        update_config({"enabled": True})

    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
        "config": cfg_written,
        "ip": ip_result,
        "status": status(),
    }

def stop():
    r = run(["systemctl", "stop", "hostapd"], timeout=30)

    if r["ok"]:
        update_config({"enabled": False})

    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
        "status": status(),
    }

def restart():
    stop()
    return start()

import re

def stations():
    cfg = get_config()
    iface = cfg["interface"]

    r = run(["iw","dev",iface,"station","dump"])

    if not r["ok"]:
        return {
            "ok":False,
            "count":0,
            "stations":[]
        }

    stations=[]
    current=None

    for line in r["stdout"].splitlines():

        if line.startswith("Station "):
            if current:
                stations.append(current)

            mac=line.split()[1]

            current={
                "mac":mac
            }

            continue

        if current is None:
            continue

        s=line.strip()

        if s.startswith("signal:"):
            m=re.search(r'(-?\d+)',s)
            if m:
                current["signal"]=int(m.group(1))

        elif s.startswith("inactive time:"):
            m=re.search(r'(\d+)',s)
            if m:
                current["inactive"]=int(m.group(1))

        elif s.startswith("connected time:"):
            m=re.search(r'(\d+)',s)
            if m:
                current["connected"]=int(m.group(1))

        elif s.startswith("authorized:"):
            current["authorized"]=s.endswith("yes")

        elif s.startswith("rx bitrate:"):
            current["rx_bitrate"]=s.split(":",1)[1].strip()

        elif s.startswith("tx bitrate:"):
            current["tx_bitrate"]=s.split(":",1)[1].strip()

    if current:
        stations.append(current)

    return {
        "ok":True,
        "count":len(stations),
        "stations":stations
    }

