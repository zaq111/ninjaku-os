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
table inet ninjaku_gateway {{
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
    run(["nft", "delete", "table", "inet", "ninjaku_gateway"])
    r = run(["nft", "-f", "-"], input_text=ruleset)
    return {"ok": r["ok"], "stdout": r["stdout"], "stderr": r["stderr"]}

def nat_down():
    r = run(["nft", "delete", "table", "inet", "ninjaku_gateway"])
    ok = r["ok"] or "No such file or directory" in r["stderr"]
    return {"ok": ok, "stdout": r["stdout"], "stderr": r["stderr"]}

def _enable_router_unlocked():
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

    try:
        from lib import firewall_service
        results["firewall_policy"] = firewall_service.apply_policy()
    except Exception as e:
        results["firewall_policy"] = {"ok": False, "error": str(e)}

    try:
        from lib import qos_service
        results["qos_apply"] = qos_service.apply()
    except Exception as e:
        results["qos_apply"] = {"ok": False, "error": str(e)}

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

def _disable_router_unlocked():
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
    Ensure Ninjaku acts as an IPv4 gateway using nftables native rules.

    Idempotent:
    - enable ip_forward
    - create/update table inet ninjaku
    - allow subnet -> WAN forwarding
    - allow established WAN -> subnet forwarding
    - masquerade LAN/WiFi subnets to WAN
    """
    import ipaddress
    import builtins

    results = {}
    wan = cfg("router.wan")

    subnets = []

    lan_ip = cfg("router.lan_ip")
    if lan_ip:
        try:
            subnets.append(str(ipaddress.ip_interface(lan_ip).network))
        except Exception:
            pass

    try:
        from lib.wifi_service import get_config
        wifi = get_config()
        wifi_ip = wifi.get("ip")
        if wifi_ip:
            subnets.append(str(ipaddress.ip_interface(wifi_ip).network))
    except Exception:
        pass

    subnets = sorted(builtins.set(subnets))

    results["forward_on"] = enable_forward()

    try:
        with open("/etc/sysctl.d/99-ninjaku-router.conf", "w") as f:
            f.write("net.ipv4.ip_forward=1\n")
        results["forward_persist"] = {"ok": True}
    except Exception as e:
        results["forward_persist"] = {"ok": False, "error": str(e)}

    subnet_forward_rules = []
    subnet_nat_rules = []

    for subnet in subnets:
        subnet_forward_rules.append(f'        ip saddr {subnet} oifname "{wan}" accept')
        subnet_forward_rules.append(f'        ip daddr {subnet} iifname "{wan}" ct state established,related accept')
        subnet_nat_rules.append(f'        ip saddr {subnet} oifname "{wan}" masquerade')

    ruleset = f"""
table inet ninjaku_gateway {{
    chain input {{
        type filter hook input priority 0; policy accept;
        iifname "lo" accept
        ct state established,related accept
    }}

    chain forward {{
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
{chr(10).join(subnet_forward_rules)}
    }}

    chain output {{
        type filter hook output priority 0; policy accept;
    }}

    chain postrouting {{
        type nat hook postrouting priority srcnat; policy accept;
{chr(10).join(subnet_nat_rules)}
    }}
}}
"""

    run(["nft", "delete", "table", "inet", "ninjaku_gateway"])
    nft = run(["nft", "-f", "-"], input_text=ruleset)
    results["nft_apply"] = {
        "ok": nft.get("ok", False),
        "stdout": nft.get("stdout", ""),
        "stderr": nft.get("stderr", ""),
    }

    verify = run(["nft", "list", "table", "inet", "ninjaku_gateway"])
    results["verify"] = {
        "ok": verify.get("ok", False),
        "stdout": verify.get("stdout", ""),
        "stderr": verify.get("stderr", ""),
    }

    return {
        "ok": all(v.get("ok", False) for v in results.values()),
        "wan": wan,
        "subnets": subnets,
        "results": results,
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }


# NINJAKU APPLY LOCK WRAPPERS

from lib.apply_lock import apply_lock

def enable_router():
    with apply_lock():
        return _enable_router_unlocked()

def disable_router():
    with apply_lock():
        return _disable_router_unlocked()
