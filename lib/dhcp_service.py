from lib.system import run, read_text
from lib.settings import get, set

CONF = "/etc/dnsmasq.d/ninjaku-lan.conf"

DEFAULTS = {
    "dhcp.interface": "eth1",
    "dhcp.range_start": "192.168.10.100",
    "dhcp.range_end": "192.168.10.200",
    "dhcp.netmask": "255.255.255.0",
    "dhcp.lease_time": "12h",
    "dhcp.gateway": "192.168.10.1",
    "dhcp.dns": "192.168.10.1",
    "dhcp.upstream1": "1.1.1.1",
    "dhcp.upstream2": "8.8.8.8",
}

def cfg(key):
    return get(key, DEFAULTS[key])

def ensure_defaults():
    for k, v in DEFAULTS.items():
        if get(k) is None:
            set(k, v)


def interface_exists(ifname):
    return run(["ip", "link", "show", ifname])["ok"]

def reload_dnsmasq(reason="reload"):
    ensure_defaults()
    iface = cfg("dhcp.interface")

    if not interface_exists(iface):
        return {
            "ok": True,
            "skipped": True,
            "state": "waiting_for_lan",
            "reason": reason,
            "interface": iface,
            "stdout": "",
            "stderr": f"interface {iface} not found; dnsmasq reload skipped",
        }

    r = run(["systemctl", "restart", "dnsmasq"])

    return {
        "ok": r["ok"],
        "skipped": False,
        "state": "reloaded" if r["ok"] else "error",
        "reason": reason,
        "interface": iface,
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def build_config():
    ensure_defaults()

    return f"""\
# Ninjaku OS Router LAN DHCP
interface={cfg("dhcp.interface")}
bind-interfaces

dhcp-range={cfg("dhcp.range_start")},{cfg("dhcp.range_end")},{cfg("dhcp.netmask")},{cfg("dhcp.lease_time")}
dhcp-option=3,{cfg("dhcp.gateway")}
dhcp-option=6,{cfg("dhcp.dns")}

domain-needed
bogus-priv
server={cfg("dhcp.upstream1")}
server={cfg("dhcp.upstream2")}
"""

def status():
    ensure_defaults()
    return {
        "service": run(["systemctl", "is-active", "dnsmasq"])["stdout"],
        "enabled": run(["systemctl", "is-enabled", "dnsmasq"])["stdout"],
        "config": read_text(CONF),
        "leases": read_text("/var/lib/misc/dnsmasq.leases"),
    }

def start():
    ensure_defaults()

    with open(CONF, "w") as f:
        f.write(build_config())

    run(["systemctl", "enable", "dnsmasq"])
    r = reload_dnsmasq("dhcp_start")

    if r["ok"] and not r.get("skipped"):
        set("dhcp.enabled", "true")
    elif r.get("skipped"):
        set("dhcp.enabled", "false")

    return r

def stop():
    r = run(["systemctl", "stop", "dnsmasq"])

    if r["ok"]:
        set("dhcp.enabled", "false")

    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"]}
