from lib.system import run
from lib.settings import get, set

DEFAULTS = {
    "router.wan": "eth0",
    "router.lan": "eth1",
    "router.lan_ip": "192.168.10.1/24",
}

def cfg(key):
    return get(key, DEFAULTS[key])

def current():
    return {
        "wan": cfg("router.wan"),
        "lan": cfg("router.lan"),
        "lan_ip": cfg("router.lan_ip"),
        "enabled": get("router.enabled", "false"),
        "state": get("router.state", "unknown"),
    }

def service_active(name):
    return run(["systemctl", "is-active", name])["stdout"]


def interface_exists(ifname):
    r = run(["ip", "link", "show", ifname])
    return r["ok"]

def interface_state(ifname):
    if not interface_exists(ifname):
        return "missing"
    out = run(["ip", "-br", "link", "show", ifname])["stdout"].strip()
    if not out:
        return "unknown"
    parts = out.split()
    return parts[1] if len(parts) > 1 else "unknown"

def status():
    c = current()
    return {
        "state": c["state"],
        "enabled": c["enabled"],
        "wan": c["wan"],
        "lan": c["lan"],
        "lan_ip": c["lan_ip"],
        "dhcp": service_active("dnsmasq"),
        "wan_state": interface_state(c["wan"]),
        "lan_state": interface_state(c["lan"]),
        "interfaces": run(["ip", "-br", "addr"])["stdout"],
        "routes": run(["ip", "route"])["stdout"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def lan_up():
    c = current()
    lan = c["lan"]
    lan_ip = c["lan_ip"]

    if not interface_exists(lan):
        return {
            "ok": False,
            "lan": lan,
            "lan_ip": lan_ip,
            "stdout": "",
            "stderr": f"LAN interface {lan} not found",
            "state": "waiting_for_lan",
        }

    run(["ip", "link", "set", lan, "up"])
    run(["ip", "addr", "flush", "dev", lan])
    ip_result = run(["ip", "addr", "add", lan_ip, "dev", lan])

    return {
        "ok": ip_result["ok"],
        "lan": lan,
        "lan_ip": lan_ip,
        "stdout": ip_result["stdout"],
        "stderr": ip_result["stderr"],
    }

def enable_forward():
    r = run(["sysctl", "-w", "net.ipv4.ip_forward=1"])
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"]}

def disable_forward():
    r = run(["sysctl", "-w", "net.ipv4.ip_forward=0"])
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"]}

def nat_up():
    c = current()
    wan = c["wan"]
    lan = c["lan"]

    ruleset = f"""
table inet ninjaku {{
    chain input {{
        type filter hook input priority 0; policy accept;
        iif "lo" accept
        ct state established,related accept
    }}

    chain forward {{
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
        iif "{lan}" oif "{wan}" accept
    }}

    chain output {{
        type filter hook output priority 0; policy accept;
    }}

    chain postrouting {{
        type nat hook postrouting priority srcnat; policy accept;
        oif "{wan}" masquerade
    }}
}}
"""
    run(["nft", "delete", "table", "inet", "ninjaku"])
    r = run(["nft", "-f", "-"], input_text=ruleset)
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"]}

def nat_down():
    r = run(["nft", "delete", "table", "inet", "ninjaku"])
    ok = r["ok"] or "No such file or directory" in r["stderr"]
    return {"ok": ok, "stdout": r["stdout"], "stderr": r["stderr"]}

def enable_router():
    set("router.state", "restoring")
    results = {}

    results["lan_up"] = lan_up()

    if not results["lan_up"].get("ok"):
        set("router.enabled", "true")
        set("router.state", results["lan_up"].get("state", "waiting_for_lan"))
        set("dhcp.enabled", "false")
        set("firewall.enabled", "false")
        return {"ok": False, "state": get("router.state", "waiting_for_lan"), "results": results}

    results["gateway"] = ensure_gateway()

    dhcp = run(["systemctl", "restart", "dnsmasq"])
    results["dhcp_restart"] = {
        "ok": dhcp["ok"],
        "stdout": dhcp["stdout"],
        "stderr": dhcp["stderr"],
    }

    ok = all(v.get("ok", False) for v in results.values())

    c = current()
    set("router.enabled", "true" if ok else "false")
    set("router.state", "running" if ok else "error")
    set("router.wan", c["wan"])
    set("router.lan", c["lan"])
    set("router.lan_ip", c["lan_ip"])
    set("dhcp.enabled", "true" if ok else "false")
    set("firewall.enabled", "true" if ok else "false")

    return {"ok": ok, "results": results}

def disable_router():
    set("router.state", "stopping")
    results = {}

    dhcp = run(["systemctl", "stop", "dnsmasq"])
    results["dhcp_stop"] = {
        "ok": dhcp["ok"],
        "stdout": dhcp["stdout"],
        "stderr": dhcp["stderr"],
    }

    results["nat_down"] = nat_down()
    results["forward_off"] = disable_forward()

    ok = all(v.get("ok", False) for v in results.values())

    set("router.enabled", "false")
    set("router.state", "stopped" if ok else "error")
    set("dhcp.enabled", "false")
    set("firewall.enabled", "false")

    return {"ok": ok, "results": results}

def ensure_gateway():
    """
    Ensure Ninjaku acts as an IPv4 gateway.

    Idempotent:
    - enable ip_forward
    - ensure FORWARD rules
    - ensure MASQUERADE for router LAN and WiFi subnet
    """
    results = {}

    wan = cfg("router.wan")

    subnets = []
    lan_ip = cfg("router.lan_ip")
    if lan_ip:
        import ipaddress
        try:
            subnets.append(str(ipaddress.ip_interface(lan_ip).network))
        except Exception:
            pass

    try:
        from lib.wifi_service import get_config
        wifi = get_config()
        wifi_ip = wifi.get("ip")
        if wifi_ip:
            import ipaddress
            subnets.append(str(ipaddress.ip_interface(wifi_ip).network))
    except Exception:
        pass

    subnets = sorted(__import__('builtins').set(subnets))

    results["forward_on"] = enable_forward()

    # Persist ip_forward.
    try:
        with open("/etc/sysctl.d/99-ninjaku-router.conf", "w") as f:
            f.write("net.ipv4.ip_forward=1\n")
        results["forward_persist"] = {"ok": True}
    except Exception as e:
        results["forward_persist"] = {"ok": False, "error": str(e)}

    def ensure_rule(name, check_cmd, add_cmd):
        c = run(check_cmd)
        if c.get("ok"):
            return {"ok": True, "exists": True}

        a = run(add_cmd)
        return {
            "ok": a.get("ok", False),
            "exists": False,
            "stdout": a.get("stdout", ""),
            "stderr": a.get("stderr", ""),
        }

    for subnet in subnets:
        key = subnet.replace("/", "_").replace(".", "_")

        results[f"nat_{key}"] = ensure_rule(
            f"nat_{subnet}",
            ["iptables", "-t", "nat", "-C", "POSTROUTING", "-s", subnet, "-o", wan, "-j", "MASQUERADE"],
            ["iptables", "-t", "nat", "-A", "POSTROUTING", "-s", subnet, "-o", wan, "-j", "MASQUERADE"],
        )

        results[f"forward_out_{key}"] = ensure_rule(
            f"forward_out_{subnet}",
            ["iptables", "-C", "FORWARD", "-s", subnet, "-o", wan, "-j", "ACCEPT"],
            ["iptables", "-A", "FORWARD", "-s", subnet, "-o", wan, "-j", "ACCEPT"],
        )

        results[f"forward_back_{key}"] = ensure_rule(
            f"forward_back_{subnet}",
            ["iptables", "-C", "FORWARD", "-d", subnet, "-i", wan, "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
            ["iptables", "-A", "FORWARD", "-d", subnet, "-i", wan, "-m", "conntrack", "--ctstate", "RELATED,ESTABLISHED", "-j", "ACCEPT"],
        )

    return {
        "ok": all(v.get("ok", False) for v in results.values()),
        "wan": wan,
        "subnets": subnets,
        "results": results,
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }
