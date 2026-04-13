NAME = "firewall"
VERSION = "1.1"

from lib.system import run

BASE_RULESET = r"""
table inet ninjaku {
    chain input {
        type filter hook input priority 0; policy accept;
        iif "lo" accept
        ct state established,related accept
    }

    chain forward {
        type filter hook forward priority 0; policy accept;
        ct state established,related accept
    }

    chain output {
        type filter hook output priority 0; policy accept;
    }
}
"""

def status():
    nft = run(["nft", "list", "ruleset"], timeout=5)
    return {
        "nft_ok": nft["ok"],
        "nft_ruleset": nft["stdout"] if nft["stdout"] else nft["stderr"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def init():
    run(["nft", "delete", "table", "inet", "ninjaku"], timeout=5)
    p = run(["nft", "-f", "-"], timeout=5, input_text=BASE_RULESET)
    return {
        "ok": p["ok"],
        "stdout": p["stdout"],
        "stderr": p["stderr"],
    }

def reset():
    p = run(["nft", "delete", "table", "inet", "ninjaku"], timeout=5)
    return {
        "ok": p["ok"],
        "stdout": p["stdout"],
        "stderr": p["stderr"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()
    if command == "init":
        return init()
    if command == "reset":
        return reset()

    raise Exception(f"Unknown firewall command: {command}")
