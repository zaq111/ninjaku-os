#!/usr/bin/env python3
import time
import sys
from pathlib import Path

sys.path.insert(0, "/opt/ninjaku")

from lib.db import connect
from lib.schema_init import initialize_schema
from lib.settings import get_bool
from lib.modules import execute

HEARTBEAT_SECONDS = 60
DISCOVERY_FORCE_SECONDS = 300
LEASE_FILE = Path("/var/lib/misc/dnsmasq.leases")

last_discovery = None
last_lease_sig = None
last_discovery_ts = 0

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

    if get_bool("qos.enabled", False):
        try:
            result = execute("qos", "apply")
            log("qos_restore", f"qos apply ok={result.get('ok')}")
        except Exception as e:
            log("qos_restore_failed", str(e))


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

def lease_signature():
    try:
        st = LEASE_FILE.stat()
        return f"{st.st_mtime_ns}:{st.st_size}"
    except Exception:
        return "missing"

def discover_devices(force=False):
    global last_discovery, last_lease_sig, last_discovery_ts

    now = time.time()
    sig = lease_signature()

    if not force:
        lease_changed = sig != last_lease_sig
        force_due = (now - last_discovery_ts) >= DISCOVERY_FORCE_SECONDS

        if not lease_changed and not force_due:
            return {"ok": True, "skipped": True, "reason": "no lease change"}

    try:
        result = execute("devices", "sync")
        lease_count = result.get("lease_count", result.get("count", 0))
        neighbor_count = result.get("neighbor_count", 0)
        detail = f"lease_count={lease_count} neighbor_count={neighbor_count}"

        last_lease_sig = sig
        last_discovery_ts = now

        if detail != last_discovery:
            log("device_discovery", detail)
            last_discovery = detail

        return result

    except Exception as e:
        log("device_discovery_failed", str(e))
        return {"ok": False, "error": str(e)}

def main():
    initialize_schema()
    log("daemon_start", "ninjakud started")

    restore_state()
    discover_devices(force=True)

    while True:
        time.sleep(HEARTBEAT_SECONDS)
        restore_router_if_needed()
        discover_devices()

if __name__ == "__main__":
    main()
