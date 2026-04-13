NAME = "dhcp"
VERSION = "1.0"

from lib.system import run, read_text

CONF = "/etc/dnsmasq.d/ninjaku-lan.conf"

DNSMASQ_CONF = """\
# Ninjaku OS Router LAN DHCP
interface=eth1
bind-interfaces

dhcp-range=192.168.10.100,192.168.10.200,255.255.255.0,12h
dhcp-option=3,192.168.10.1
dhcp-option=6,192.168.10.1

domain-needed
bogus-priv
server=1.1.1.1
server=8.8.8.8
"""

def status():
    return {
        "service": run(["systemctl", "is-active", "dnsmasq"])["stdout"],
        "enabled": run(["systemctl", "is-enabled", "dnsmasq"])["stdout"],
        "config": read_text(CONF),
        "leases": read_text("/var/lib/misc/dnsmasq.leases"),
    }

def start():
    with open(CONF, "w") as f:
        f.write(DNSMASQ_CONF)

    run(["systemctl", "enable", "dnsmasq"])
    r = run(["systemctl", "restart", "dnsmasq"])

    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def stop():
    r = run(["systemctl", "stop", "dnsmasq"])
    return {
        "ok": r["ok"],
        "stdout": r["stdout"],
        "stderr": r["stderr"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "start":
        return start()
    if command == "stop":
        return stop()

    raise Exception(f"Unknown dhcp command: {command}")
