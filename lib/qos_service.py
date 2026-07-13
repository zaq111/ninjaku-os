from lib.system import run
from lib.settings import get, set, get_many

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
    "qos.runtime_monitor": "false",
}

def ensure_defaults():
    for k, v in DEFAULTS.items():
        if get(k, "") == "":
            set(k, v)

def cfg():
    # Read all QoS settings using one SQLite connection.
    values = get_many(DEFAULTS.keys())
    return {
        key.replace("qos.", ""): values.get(key, default)
        for key, default in DEFAULTS.items()
    }

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
    """
    Legacy compatibility only.

    Device/profile-wide DSCP marking is intentionally disabled.

    Do not re-enable rules here.

    Reason:
    Marking every packet from one device/profile as CS5/CS1 breaks
    CAKE diffserv behavior. Download, video, game, DNS, and browsing
    from the same device would all be forced into one queue.

    Current design:
    - Application/protocol marking lives in global_marking_rules()
      and apply_dscp_marks().
    - Profile priority is used only by limiter logic.
    - This function stays only so older API/UI code that expects
      "profile_rules" continues to receive an empty list safely.
    """
    return []

def global_marking_rules():
    return [
        {"name": "DNS UDP", "match": "udp dport 53", "dscp": cfg().get("map.high", "cs5"), "queue": "High / latency"},
        {"name": "DNS TCP", "match": "tcp dport 53", "dscp": cfg().get("map.high", "cs5"), "queue": "High / latency"},
        {"name": "ICMP", "match": "icmp", "dscp": cfg().get("map.high", "cs5"), "queue": "High / latency"},
        {"name": "SSH", "match": "tcp dport 22", "dscp": cfg().get("map.high", "cs5"), "queue": "High / latency"},
        {"name": "Torrent TCP", "match": "tcp dport 6881-6889,51413", "dscp": cfg().get("map.low", "cs1"), "queue": "Low / bulk"},
        {"name": "Torrent UDP", "match": "udp dport 6881-6889,51413", "dscp": cfg().get("map.low", "cs1"), "queue": "Low / bulk"},
    ]


def apply_dscp_marks():
    # Global application/protocol marking only.
    # Device-wide/profile-wide DSCP marking is intentionally disabled.
    c = cfg()
    high = c.get("map.high", "cs5")
    low = c.get("map.low", "cs1")

    run(["nft", "delete", "table", "inet", "ninjaku_qos"])

    cmds = [
        ["nft", "add", "table", "inet", "ninjaku_qos"],
        ["nft", "add", "chain", "inet", "ninjaku_qos", "mark_prerouting", "{", "type", "filter", "hook", "prerouting", "priority", "mangle", ";", "policy", "accept", ";", "}"],
        ["nft", "add", "chain", "inet", "ninjaku_qos", "mark_postrouting", "{", "type", "filter", "hook", "postrouting", "priority", "mangle", ";", "policy", "accept", ";", "}"],

        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "udp", "dport", "53", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "53", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "ip", "protocol", "icmp", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "22", "ip", "dscp", "set", high],

        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "udp", "dport", "53", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "53", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "ip", "protocol", "icmp", "ip", "dscp", "set", high],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "22", "ip", "dscp", "set", high],

        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "tcp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", low],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_prerouting", "udp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", low],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "tcp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", low],
        ["nft", "add", "rule", "inet", "ninjaku_qos", "mark_postrouting", "udp", "dport", "{", "6881-6889", ",", "51413", "}", "ip", "dscp", "set", low],
    ]

    errors = []
    for cmd in cmds:
        r = run(cmd)
        if not r["ok"]:
            errors.append({"cmd": " ".join(cmd), "stderr": r["stderr"]})

    return {"ok": len(errors) == 0, "errors": errors, "profile_rules": profile_dscp_rules(), "global_rules": global_marking_rules()}

def clear_dscp_marks():
    run(["nft", "delete", "table", "inet", "ninjaku_qos"])
    return {"ok": True}


def _clear_unlocked():
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

def qos_pipeline(strategy):
    strategy = str(strategy or "balanced").lower()

    if strategy == "priority_first":
        return ["gateway", "marking", "cake", "limiter"]

    if strategy == "limiter_first":
        return ["gateway", "limiter", "marking", "cake"]

    return ["gateway", "marking", "cake", "limiter"]

def apply_gateway_stage():
    try:
        from lib.router_service import ensure_gateway
        return ensure_gateway()
    except Exception as e:
        return {"ok": False, "error": str(e)}

def apply_marking_stage():
    return apply_dscp_marks()

def apply_cake_stage(c):
    wan = c["wan"]
    ifb = c["ifb"]

    run(["ip", "link", "set", ifb, "up"])
    run(["tc", "qdisc", "del", "dev", wan, "root"])
    run(["tc", "qdisc", "del", "dev", wan, "ingress"])
    run(["tc", "qdisc", "del", "dev", ifb, "root"])

    up = run(["tc", "qdisc", "replace", "dev", wan, "root"] + cake_args(c["upload"], "upload"))

    run(["tc", "qdisc", "add", "dev", wan, "ingress"])
    redirect = run([
        "tc", "filter", "add", "dev", wan, "parent", "ffff:",
        "protocol", "all", "matchall",
        "action", "mirred", "egress", "redirect", "dev", ifb
    ])

    down = run(["tc", "qdisc", "replace", "dev", ifb, "root"] + cake_args(c["download"], "download"))

    return {
        "ok": up.get("ok") and redirect.get("ok") and down.get("ok"),
        "upload_result": up,
        "redirect_result": redirect,
        "download_result": down,
    }

def apply_limiter_stage():
    return apply_wifi_profile_limits()

def _apply_unlocked():
    c = cfg()
    wan = c["wan"]
    ifb = c["ifb"]
    strategy = c.get("strategy", "balanced")
    pipeline = qos_pipeline(strategy)

    if not iface_exists(wan):
        return {"ok": False, "error": f"WAN interface {wan} not found"}

    load_modules()

    results = {}
    for stage in pipeline:
        if stage == "gateway":
            results["gateway"] = apply_gateway_stage()

        elif stage == "marking":
            results["dscp_result"] = apply_marking_stage()

        elif stage == "cake":
            cake = apply_cake_stage(c)
            results["cake"] = cake
            results["upload_result"] = cake.get("upload_result", {})
            results["redirect_result"] = cake.get("redirect_result", {})
            results["download_result"] = cake.get("download_result", {})

        elif stage == "limiter":
            results["wifi_profile_limits"] = apply_limiter_stage()

    ok = all(v.get("ok", False) for v in results.values() if isinstance(v, dict))
    set("qos.enabled", "true" if ok else "false")

    return {
        "ok": ok,
        "wan": wan,
        "ifb": ifb,
        "upload": c["upload"],
        "download": c["download"],
        "strategy": strategy,
        "pipeline": pipeline,
        "upload_result": results.get("upload_result", {}),
        "redirect_result": results.get("redirect_result", {}),
        "download_result": results.get("download_result", {}),
        "dscp_result": results.get("dscp_result", {}),
        "wifi_profile_limits": results.get("wifi_profile_limits", {}),
        "gateway": results.get("gateway", {}),
        "stage_results": results,
    }

VALID_STRATEGIES = {"balanced", "priority_first", "limiter_first"}
VALID_DIFFSERV = {"besteffort", "diffserv3", "diffserv4", "diffserv8"}

def validate_rate_value(value):
    raw = str(value or "").strip().lower()
    if raw in ("", "0", "0mbit", "unlimited", "none", "-"):
        return True

    normalized = normalize_mbit(raw)
    if not normalized:
        return False

    try:
        n = float(normalized.replace("mbit", ""))
        return 0 < n <= 10000
    except Exception:
        return False

def validate_qos_config(values):
    errors = {}

    if "strategy" in values and str(values["strategy"]) not in VALID_STRATEGIES:
        errors["strategy"] = "must be one of: balanced, priority_first, limiter_first"

    if "diffserv" in values and str(values["diffserv"]) not in VALID_DIFFSERV:
        errors["diffserv"] = "must be one of: besteffort, diffserv3, diffserv4, diffserv8"

    for key in ("download", "upload"):
        if key in values and not validate_rate_value(values[key]):
            errors[key] = "must be a positive Mbps value, mbit value, unlimited, none, or 0"

    return errors


def set_config(values):
    allowed = {k.replace("qos.", "") for k in DEFAULTS.keys()}
    cleaned = {k: v for k, v in values.items() if k in allowed}

    errors = validate_qos_config(cleaned)
    if errors:
        return {
            "ok": False,
            "error": "validation failed",
            "errors": errors,
            "config": cfg(),
        }

    changed = {}
    for k, v in cleaned.items():
        set("qos." + k, str(v))
        changed[k] = str(v)

    return {"ok": True, "changed": changed, "config": cfg()}

def qos_runtime_state(c=None):
    c = c or cfg()
    limits = profile_limit_rules()
    qos_on = str(c.get("enabled", "false")).lower() == "true"
    limiter_on = qos_on and len(limits) > 0

    return {
        "strategy_configured": c.get("strategy", "balanced"),
        "strategy_effective": c.get("strategy", "balanced") if qos_on else "inactive",
        "strategy_active": qos_on,
        "strategy_pipeline": qos_pipeline(c.get("strategy", "balanced")) if qos_on else [],
        "strategy_note": "Strategy changes the global QoS apply pipeline order.",
        "limiter_active": limiter_on,
        "limiter_rule_count": len(limits),
        "limiter_priority_active": limiter_on,
        "limiter_priority_note": "Limiter priority is active only when QoS is enabled and limiter rules exist. It maps to tc filter priority and class buckets.",
        "marking_active": qos_on,
        "diffserv_active": c.get("diffserv", "diffserv4") if qos_on else "inactive",
    }


def status():
    c = cfg()
    wan = c["wan"]
    ifb = c["ifb"]

    return {
        "config": c,
        "runtime": qos_runtime_state(c),
        "enabled": c.get("enabled", "false"),
        "wan_exists": iface_exists(wan),
        "wan_qdisc": run(["tc", "-s", "qdisc", "show", "dev", wan])["stdout"],
        "ifb_qdisc": run(["tc", "-s", "qdisc", "show", "dev", ifb])["stdout"] if iface_exists(ifb) else "",
        "profile_rules": profile_dscp_rules(),
        "global_marking_rules": global_marking_rules(),
        "profile_limit_rules": profile_limit_rules(),
        "wifi_limit_qdisc": run(["tc", "-s", "qdisc", "show", "dev", limiter_interfaces()[0]])["stdout"] if iface_exists(limiter_interfaces()[0]) else "",
        "wifi_ifb_qdisc": run(["tc", "-s", "qdisc", "show", "dev", limiter_interfaces()[1]])["stdout"] if iface_exists(limiter_interfaces()[1]) else "",
        "queue_runtime": qos_queue_runtime() if boolv(c.get("runtime_monitor", "false")) else {
            "enabled": False,
            "mode": c.get("diffserv", "diffserv4"),
            "count": 0,
            "flows": [],
        },
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
                "priority": pol.get("qos_priority", "normal"),
            })

    return rules

def limiter_priority_rank(priority):
    p = str(priority or "normal").lower()
    if p == "high":
        return 10
    if p == "low":
        return 90
    return 50

def limiter_filter_prio(priority):
    strategy = cfg().get("strategy", "balanced")
    p = str(priority or "normal").lower()

    maps = {
        "balanced": {
            "high": 3,
            "normal": 5,
            "low": 7,
        },
        "priority_first": {
            "high": 1,
            "normal": 5,
            "low": 9,
        },
        "limiter_first": {
            "high": 2,
            "normal": 3,
            "low": 4,
        },
    }

    return maps.get(strategy, maps["balanced"]).get(p, maps.get(strategy, maps["balanced"])["normal"])


def limiter_interfaces():
    try:
        from lib.router_service import active_client_side
        active = active_client_side()
        if active.get("ok") and active.get("interface"):
            iface = active["interface"]
            return iface, f"ifb-{iface}"
    except Exception:
        pass

    return "wlan0", "ifb-wlan0"


def clear_wifi_profile_limits():
    wlan, ifb = limiter_interfaces()

    run(["tc", "qdisc", "del", "dev", wlan, "root"])
    run(["tc", "qdisc", "del", "dev", wlan, "ingress"])
    run(["tc", "qdisc", "del", "dev", ifb, "root"])
    run(["ip", "link", "set", ifb, "down"])
    run(["ip", "link", "del", ifb])
    return {"ok": True}

def apply_wifi_profile_limits():
    wlan, ifb = limiter_interfaces()
    rules = sorted(
        profile_limit_rules(),
        key=lambda r: (limiter_priority_rank(r.get("priority")), r.get("ip", ""))
    )

    clear_wifi_profile_limits()

    if not iface_exists(wlan):
        return {"ok": True, "skipped": True, "reason": f"{wlan} not found", "rules": rules, "wlan": wlan, "ifb": ifb}

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

    counters = {"high": 0, "normal": 0, "low": 0}
    applied = []

    for r in rules:
        ip = r["ip"]
        priority = str(r.get("priority") or "normal").lower()
        if priority not in counters:
            priority = "normal"

        counters[priority] += 1
        idx = limiter_priority_rank(priority) + counters[priority]
        prio = limiter_filter_prio(priority)

        if r["download"]:
            classid = f"1:{idx}"
            cmds += [
                ["tc", "class", "replace", "dev", wlan, "parent", "1:", "classid", classid,
                 "htb", "rate", r["download"], "ceil", r["download"]],
                ["tc", "qdisc", "replace", "dev", wlan, "parent", classid, "fq_codel"],
                ["tc", "filter", "replace", "dev", wlan, "protocol", "ip", "parent", "1:", "prio", str(prio),
                 "u32", "match", "ip", "dst", f"{ip}/32", "flowid", classid],
            ]

        if r["upload"]:
            classid = f"2:{idx}"
            cmds += [
                ["tc", "class", "replace", "dev", ifb, "parent", "2:", "classid", classid,
                 "htb", "rate", r["upload"], "ceil", r["upload"]],
                ["tc", "qdisc", "replace", "dev", ifb, "parent", classid, "fq_codel"],
                ["tc", "filter", "replace", "dev", ifb, "protocol", "ip", "parent", "2:", "prio", str(prio),
                 "u32", "match", "ip", "src", f"{ip}/32", "flowid", classid],
            ]

        applied.append({
            **r,
            "tc_class_bucket": priority,
            "tc_filter_prio": prio,
            "tc_index": idx,
        })

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

def cake_queue_for_dscp(dscp, mode=None):
    mode = mode or cfg().get("diffserv", "diffserv4")
    d = (dscp or "cs0").lower()

    if mode == "besteffort":
        return {"priority": 1, "queue": "Best Effort"}

    if mode == "diffserv3":
        if d in ("cs5", "cs6", "cs7", "ef"):
            return {"priority": 1, "queue": "High / Latency"}
        if d == "cs1":
            return {"priority": 3, "queue": "Low / Bulk"}
        return {"priority": 2, "queue": "Normal"}

    if mode == "diffserv8":
        if d in ("cs7", "cs6"):
            return {"priority": 1, "queue": "Network Control"}
        if d in ("ef", "cs5"):
            return {"priority": 2, "queue": "Voice"}
        if d in ("af41", "af42", "af43"):
            return {"priority": 3, "queue": "Video"}
        if d in ("af31", "af32", "af33"):
            return {"priority": 4, "queue": "Excellent Effort"}
        if d == "cs0":
            return {"priority": 5, "queue": "Best Effort"}
        if d == "cs4":
            return {"priority": 6, "queue": "Low Latency"}
        if d in ("cs2", "cs3"):
            return {"priority": 7, "queue": "Background"}
        if d == "cs1":
            return {"priority": 8, "queue": "Bulk"}
        return {"priority": 5, "queue": "Best Effort"}

    # diffserv4
    if d in ("cs5", "ef", "cs6", "cs7"):
        return {"priority": 1, "queue": "Voice"}
    if d in ("af41", "af42", "af43"):
        return {"priority": 2, "queue": "Video"}
    if d == "cs1":
        return {"priority": 4, "queue": "Bulk"}
    return {"priority": 3, "queue": "Best Effort"}

def classify_flow(proto, sport, dport):
    proto = (proto or "").lower()
    sport = str(sport or "")
    dport = str(dport or "")

    high = cfg().get("map.high", "cs5")
    low = cfg().get("map.low", "cs1")

    if proto == "icmp":
        return high, "ICMP rule"

    if dport == "53" or sport == "53":
        return high, "DNS rule"

    if dport == "22" or sport == "22":
        return high, "SSH rule"

    torrent_ports = {"51413", "6881", "6882", "6883", "6884", "6885", "6886", "6887", "6888", "6889"}
    if dport in torrent_ports or sport in torrent_ports:
        return low, "Torrent/Bulk rule"

    return "cs0", "Default traffic"

def read_conntrack_lines():
    paths = ["/proc/net/nf_conntrack", "/proc/net/ip_conntrack"]
    for path in paths:
        try:
            with open(path, "r") as f:
                return f.read().splitlines()
        except Exception:
            pass
    return []

def parse_conntrack_line(line):
    parts = line.split()
    proto = parts[2] if len(parts) > 2 else ""

    item = {"proto": proto, "src": "", "dst": "", "sport": "", "dport": ""}

    for p in parts:
        if p.startswith("src=") and not item["src"]:
            item["src"] = p.split("=", 1)[1]
        elif p.startswith("dst=") and not item["dst"]:
            item["dst"] = p.split("=", 1)[1]
        elif p.startswith("sport=") and not item["sport"]:
            item["sport"] = p.split("=", 1)[1]
        elif p.startswith("dport=") and not item["dport"]:
            item["dport"] = p.split("=", 1)[1]

    return item

def qos_queue_runtime(limit=80):
    import ipaddress
    from lib.device_service import lan_networks, list_devices

    mode = cfg().get("diffserv", "diffserv4")
    nets = lan_networks()
    devices = {d.get("ip"): d for d in list_devices() if d.get("ip")}

    rows = []

    for line in read_conntrack_lines():
        f = parse_conntrack_line(line)
        if not f["src"] or not f["dst"]:
            continue

        try:
            src_ip = ipaddress.ip_address(f["src"])
            dst_ip = ipaddress.ip_address(f["dst"])
        except Exception:
            continue

        src_is_lan = any(src_ip in n for n in nets)
        dst_is_lan = any(dst_ip in n for n in nets)

        if not src_is_lan and not dst_is_lan:
            continue

        dscp, reason = classify_flow(f["proto"], f["sport"], f["dport"])
        q = cake_queue_for_dscp(dscp, mode)

        client_ip = f["src"] if src_is_lan else f["dst"]
        dev = devices.get(client_ip, {})

        rows.append({
            "priority": q["priority"],
            "queue": q["queue"],
            "dscp": dscp,
            "reason": reason,
            "proto": f["proto"],
            "source": f["src"],
            "source_port": f["sport"],
            "destination": f["dst"],
            "destination_port": f["dport"],
            "client_ip": client_ip,
            "client_name": dev.get("alias") or dev.get("hostname") or "",
        })

        if len(rows) >= int(limit):
            break

    rows.sort(key=lambda r: (r["priority"], r["client_ip"], r["destination"]))
    return {
        "mode": mode,
        "count": len(rows),
        "flows": rows,
    }


# NINJAKU APPLY LOCK WRAPPERS

from lib.apply_lock import apply_lock

def apply():
    with apply_lock():
        return _apply_unlocked()

def clear():
    with apply_lock():
        return _clear_unlocked()
