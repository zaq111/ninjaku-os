from lib.system import run
from lib.settings import get, set

DEFAULTS = {
    "qos.enabled": "false",
    "qos.wan": "eth0",
    "qos.ifb": "ifb0",
    "qos.download": "90mbit",
    "qos.upload": "90mbit",
    "qos.diffserv": "diffserv4",
    "qos.nat": "true",
    "qos.ack_filter": "true",
    "qos.wash": "false",
    "qos.split_gso": "true",
    "qos.overhead": "0",
    "qos.mpu": "0",
    "qos.rtt": "",
    "qos.strategy": "balanced",
    "qos.map.high": "cs5",
    "qos.map.normal": "cs0",
    "qos.map.low": "cs1",
}

def ensure_defaults():
    for k, v in DEFAULTS.items():
        if get(k, "") == "":
            set(k, v)

def cfg():
    ensure_defaults()
    return {k.replace("qos.", ""): get(k, v) for k, v in DEFAULTS.items()}

def boolv(v):
    return str(v).lower() in ("1", "true", "yes", "on")

def iface_exists(iface):
    return run(["ip", "link", "show", iface])["ok"]

def load_modules():
    for m in ["sch_cake", "act_mirred", "sch_ingress"]:
        run(["modprobe", m])

    run(["modprobe", "ifb", "numifbs=1"])

    # Some kernels do not auto-create ifb0 after modprobe.
    if not run(["ip", "link", "show", "ifb0"])["ok"]:
        run(["ip", "link", "add", "ifb0", "type", "ifb"])

    return {"ok": True}

def cake_args(rate, direction):
    c = cfg()
    rate = normalize_mbit(rate) or "90mbit"
    args = ["cake", "bandwidth", rate]

    if c["diffserv"]:
        args.append(c["diffserv"])

    if boolv(c["nat"]):
        args.append("nat")

    if direction == "upload":
        args.append("dual-srchost")
        if boolv(c["ack_filter"]):
            args.append("ack-filter")
    else:
        args.append("dual-dsthost")

    if boolv(c["wash"]):
        args.append("wash")

    if boolv(c["split_gso"]):
        args.append("split-gso")
    else:
        args.append("no-split-gso")

    if c["overhead"] and c["overhead"] != "0":
        args += ["overhead", c["overhead"]]

    if c["mpu"] and c["mpu"] != "0":
        args += ["mpu", c["mpu"]]

    if c["rtt"]:
        args += ["rtt", c["rtt"]]

    return args



def profile_dscp_rules():
    from lib.device_service import list_devices
    from lib.policy import resolve

    devices = list_devices()
    rules = []

    for d in devices:
        ip = d.get("ip")
        profile_name = d.get("profile") or "default"

        if not ip:
            continue

        policy = resolve(profile=profile_name)

        if not policy.get("qos_enabled"):
            continue

        mode = policy.get("qos_mode", "priority")
        if mode not in ("priority", "limiter"):
            mode = "priority"

        priority = policy.get("qos_priority", "normal")

        c = cfg()
        if priority == "high":
            dscp = c.get("map.high", "cs5")
        elif priority == "low":
            dscp = c.get("map.low", "cs1")
        else:
            dscp = c.get("map.normal", "cs0")

        if not dscp or dscp == "cs0":
            continue

        rules.append((ip, dscp, profile_name))

    return rules

def apply_dscp_marks():
    # Minimal DSCP marking for CAKE diffserv4.
    # Keep it small and safe. No CIDR/provider classification.
    run(["nft", "delete", "table", "inet", "ninjaku_qos"])

    cmds = [
        ["nft", "add", "table", "inet", "ninjaku_qos"],
        ["nft", "add", "chain", "inet", "ninjaku_qos", "mark_prerouting", "{", "type", "filter", "hook", "prerouting", "priority", "mangle", ";", "policy", "accept", ";", "}"],
        ["nft", "add", "chain", "inet", "ninjaku_qos", "mark_postrouting", "{", "type", "filter", "hook", "postrouting", "priority", "mangle", ";", "policy", "accept", ";", "}"],

        # DNS, ICMP, SSH: latency sensitive
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "udp", "dport", "53", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "53", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "ip", "protocol", "icmp", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "22", "ip", "dscp", "set", "cs5"],

        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "udp", "dport", "53", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "53", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "ip", "protocol", "icmp", "ip", "dscp", "set", "cs5"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "22", "ip", "dscp", "set", "cs5"],

        # Bulk fallback for common torrent ports
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", "cs1"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "udp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", "cs1"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", "cs1"],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "udp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", "cs1"],
    ]

    # Profile-based DSCP marking.
    for ip, dscp, profile in profile_dscp_rules():
        cmds.append(["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "ip", "saddr", ip, "ip", "dscp", "set", dscp])
        cmds.append(["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "ip", "daddr", ip, "ip", "dscp", "set", dscp])

    errors = []
    for cmd in cmds:
        r = run(cmd)
        if not r["ok"]:
            errors.append({"cmd": " ".join(cmd), "stderr": r["stderr"]})

    return {"ok": len(errors) == 0, "errors": errors, "profile_rules": profile_dscp_rules()}

def clear_dscp_marks():
    run(["nft", "delete", "table", "inet", "ninjaku_qos"])
    return {"ok": True}


def clear():
    c = cfg()
    wan = c["wan"]
    ifb = c["ifb"]

    run(["tc", "qdisc", "del", "dev", wan, "root"])
    run(["tc", "qdisc", "del", "dev", wan, "ingress"])
    run(["tc", "qdisc", "del", "dev", ifb, "root"])
    run(["ip", "link", "set", ifb, "down"])

    clear_dscp_marks()
    clear_wifi_profile_limits()
    set("qos.enabled", "false")
    return {"ok": True, "wan": wan, "ifb": ifb}

def apply():
    c = cfg()
    wan = c["wan"]
    ifb = c["ifb"]

    if not iface_exists(wan):
        return {"ok": False, "error": f"WAN interface {wan} not found"}

    load_modules()

    run(["ip", "link", "set", ifb, "up"])
    run(["tc", "qdisc", "del", "dev", wan, "root"])
    run(["tc", "qdisc", "del", "dev", wan, "ingress"])
    run(["tc", "qdisc", "del", "dev", ifb, "root"])

    dscp = apply_dscp_marks()

    # Upload shaping: LAN -> WAN
    up = run(["tc", "qdisc", "replace", "dev", wan, "root"] + cake_args(c["upload"], "upload"))

    # Download shaping: WAN ingress -> IFB egress
    run(["tc", "qdisc", "add", "dev", wan, "ingress"])
    redirect = run([
        "tc", "filter", "add", "dev", wan, "parent", "ffff:",
        "protocol", "all", "matchall",
        "action", "mirred", "egress", "redirect", "dev", ifb
    ])
    down = run(["tc", "qdisc", "replace", "dev", ifb, "root"] + cake_args(c["download"], "download"))

    wifi_limits = apply_wifi_profile_limits()

    ok = up["ok"] and redirect["ok"] and down["ok"] and wifi_limits.get("ok", False)
    set("qos.enabled", "true" if ok else "false")

    return {
        "ok": ok,
        "wan": wan,
        "ifb": ifb,
        "upload": c["upload"],
        "download": c["download"],
        "upload_result": up,
        "redirect_result": redirect,
        "download_result": down,
        "dscp_result": dscp,
        "wifi_profile_limits": wifi_limits,
    }

def set_config(values):
    allowed = {k.replace("qos.", "") for k in DEFAULTS.keys()}
    changed = {}

    for k, v in values.items():
        if k not in allowed:
            continue
        set("qos." + k, str(v))
        changed[k] = str(v)

    return {"ok": True, "changed": changed, "config": cfg()}

def status():
    c = cfg()
    wan = c["wan"]
    ifb = c["ifb"]

    return {
        "config": c,
        "enabled": get("qos.enabled", "false"),
        "wan_exists": iface_exists(wan),
        "wan_qdisc": run(["tc", "-s", "qdisc", "show", "dev", wan])["stdout"],
        "ifb_qdisc": run(["tc", "-s", "qdisc", "show", "dev", ifb])["stdout"] if iface_exists(ifb) else "",
        "profile_rules": profile_dscp_rules(),
        "profile_limit_rules": profile_limit_rules(),
        "wifi_limit_qdisc": run(["tc", "-s", "qdisc", "show", "dev", "wlan0"])["stdout"] if iface_exists("wlan0") else "",
        "wifi_ifb_qdisc": run(["tc", "-s", "qdisc", "show", "dev", "ifb-wlan0"])["stdout"] if iface_exists("ifb-wlan0") else "",
    }

def normalize_mbit(value):
    v = str(value or "").strip().lower()
    if not v:
        return ""
    if v in ("0", "0mbit", "unlimited", "none", "-"):
        return ""
    v = v.replace("mbps", "").replace("mbit", "").replace("m", "").strip()
    try:
        n = float(v)
        if n <= 0:
            return ""
        if n.is_integer():
            return f"{int(n)}mbit"
        return f"{n}mbit"
    except Exception:
        return ""

def profile_limit_rules():
    from lib.device_service import list_devices
    from lib.policy import resolve

    rules = []
    for d in list_devices():
        ip = d.get("ip")
        profile = d.get("profile") or "default"
        if not ip:
            continue

        pol = resolve(profile=profile)
        if not pol.get("qos_enabled"):
            continue

        if pol.get("qos_mode", "priority") != "limiter":
            continue

        down = normalize_mbit(pol.get("qos_download"))
        up = normalize_mbit(pol.get("qos_upload"))

        if down or up:
            rules.append({
                "ip": ip,
                "profile": profile,
                "download": down,
                "upload": up,
            })

    return rules

def clear_wifi_profile_limits():
    wlan = "wlan0"
    ifb = "ifb-wlan0"

    run(["tc", "qdisc", "del", "dev", wlan, "root"])
    run(["tc", "qdisc", "del", "dev", wlan, "ingress"])
    run(["tc", "qdisc", "del", "dev", ifb, "root"])
    run(["ip", "link", "set", ifb, "down"])
    run(["ip", "link", "del", ifb])
    return {"ok": True}

def apply_wifi_profile_limits():
    wlan = "wlan0"
    ifb = "ifb-wlan0"
    rules = profile_limit_rules()

    clear_wifi_profile_limits()

    if not iface_exists(wlan):
        return {"ok": True, "skipped": True, "reason": "wlan0 not found", "rules": rules}

    if not rules:
        return {"ok": True, "rules": []}

    run(["modprobe", "ifb", "numifbs=4"])
    if not iface_exists(ifb):
        run(["ip", "link", "add", ifb, "type", "ifb"])
    run(["ip", "link", "set", ifb, "up"])

    errors = []

    # DOWNLOAD to WiFi clients: router -> wlan0 -> client, match destination IP.
    cmds = [
        ["tc", "qdisc", "replace", "dev", wlan, "root", "handle", "1:", "htb", "default", "999"],
        ["tc", "class", "replace", "dev", wlan, "parent", "1:", "classid", "1:999", "htb", "rate", "1000mbit", "ceil", "1000mbit"],
        ["tc", "qdisc", "replace", "dev", wlan, "parent", "1:999", "fq_codel"],
    ]

    # UPLOAD from WiFi clients: client -> wlan0 ingress -> ifb-wlan0, match source IP.
    cmds += [
        ["tc", "qdisc", "replace", "dev", wlan, "ingress"],
        ["tc", "filter", "replace", "dev", wlan, "parent", "ffff:", "protocol", "all", "matchall",
         "action", "mirred", "egress", "redirect", "dev", ifb],
        ["tc", "qdisc", "replace", "dev", ifb, "root", "handle", "2:", "htb", "default", "999"],
        ["tc", "class", "replace", "dev", ifb, "parent", "2:", "classid", "2:999", "htb", "rate", "1000mbit", "ceil", "1000mbit"],
        ["tc", "qdisc", "replace", "dev", ifb, "parent", "2:999", "fq_codel"],
    ]

    idx = 10
    applied = []

    for r in rules:
        ip = r["ip"]

        if r["download"]:
            classid = f"1:{idx}"
            cmds += [
                ["tc", "class", "replace", "dev", wlan, "parent", "1:", "classid", classid,
                 "htb", "rate", r["download"], "ceil", r["download"]],
                ["tc", "qdisc", "replace", "dev", wlan, "parent", classid, "fq_codel"],
                ["tc", "filter", "replace", "dev", wlan, "protocol", "ip", "parent", "1:", "prio", str(idx),
                 "u32", "match", "ip", "dst", f"{ip}/32", "flowid", classid],
            ]

        if r["upload"]:
            classid = f"2:{idx}"
            cmds += [
                ["tc", "class", "replace", "dev", ifb, "parent", "2:", "classid", classid,
                 "htb", "rate", r["upload"], "ceil", r["upload"]],
                ["tc", "qdisc", "replace", "dev", ifb, "parent", classid, "fq_codel"],
                ["tc", "filter", "replace", "dev", ifb, "protocol", "ip", "parent", "2:", "prio", str(idx),
                 "u32", "match", "ip", "src", f"{ip}/32", "flowid", classid],
            ]

        applied.append(r)
        idx += 1

    for cmd in cmds:
        res = run(cmd)
        if not res["ok"]:
            errors.append({"cmd": " ".join(cmd), "stderr": res["stderr"]})

    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "rules": applied,
        "wlan": wlan,
        "ifb": ifb,
    }
