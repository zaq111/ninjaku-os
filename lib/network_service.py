from lib.system import run

def status():
    return {
        "interfaces": run(["ip", "-br", "addr"])["stdout"],
        "routes": run(["ip", "route"])["stdout"],
        "dns": run(["cat", "/etc/resolv.conf"])["stdout"],
    }
