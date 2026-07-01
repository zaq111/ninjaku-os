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
    from lib.profiles_service import list_profiles

    profiles = {p["name"]: p for p in list_profiles()}
    devices = list_devices()

    rules = []

    for d in devices:
        ip = d.get("ip")
        profile_name = d.get("profile") or "default"
        profile = profiles.get(profile_name, {})

        if not ip:
            continue

        if not profile.get("qos_enabled"):
            continue

        priority = profile.get("qos_priority", "normal")

        if priority == "high":
            dscp = "cs5"
        elif priority == "low":
            dscp = "cs1"
        else:
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

    ok = up["ok"] and redirect["ok"] and down["ok"]
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
    }
