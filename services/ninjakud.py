#!/usr/bin/env python3
import time
import sys

sys.path.insert(0, "/opt/ninjaku")

from lib.db import init_db, connect
from lib.settings import get_bool
from lib.modules import execute

HEARTBEAT_SECONDS = 60
last_discovery = None

def log(action, detail=""):
    with connect() as db:
        db.execute(
            "INSERT INTO audit_logs(action, detail) VALUES(?,?)",
            (action, detail)
        )

def restore_state():
    if get_bool("router.enabled", False):
        try:
            result = execute("router", "enable")
            log("router_restore", f"router enable ok={result.get('ok')}")
        except Exception as e:
            log("router_restore_failed", str(e))


def restore_router_if_needed():
    try:
        from lib.settings import get
        enabled = get("router.enabled", "false")
        state = get("router.state", "unknown")

        if enabled == "true" and state != "running":
            result = execute("router", "enable")
            log("router_retry", f"state={state} ok={result.get('ok')}")
    except Exception as e:
        log("router_retry_failed", str(e))

def discover_devices():
    global last_discovery

    try:
        result = execute("devices", "sync")
        lease_count = result.get("lease_count", result.get("count", 0))
        neighbor_count = result.get("neighbor_count", 0)
        detail = f"lease_count={lease_count} neighbor_count={neighbor_count}"

        if detail != last_discovery or lease_count > 0 or neighbor_count > 0:
            log("device_discovery", detail)
            last_discovery = detail

    except Exception as e:
        log("device_discovery_failed", str(e))

def main():
    init_db()
    log("daemon_start", "ninjakud started")

    restore_state()
    discover_devices()

    while True:
        time.sleep(HEARTBEAT_SECONDS)
        restore_router_if_needed()
        restore_router_if_needed()
        discover_devices()

if __name__ == "__main__":
    main()
