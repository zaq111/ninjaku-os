NAME = "firewall"
VERSION = "1.0"

from lib.system import run

def status():
    nft = run(["nft", "list", "ruleset"], timeout=5)
    return {
        "nft_ok": nft["ok"],
        "nft_ruleset": nft["stdout"] if nft["stdout"] else nft["stderr"],
        "ip_forward": run(["cat", "/proc/sys/net/ipv4/ip_forward"])["stdout"],
    }

def execute(command, **kwargs):
    if command == "status":
        return status()

    raise Exception(f"Unknown firewall command: {command}")
