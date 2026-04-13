#!/usr/bin/env python3
import time
import sys

sys.path.insert(0, "/opt/ninjaku")

from lib.db import init_db, connect
from lib.settings import get_bool
from lib.modules import execute

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

def main():
    init_db()
    log("daemon_start", "ninjakud started")

    restore_state()

    while True:
        time.sleep(60)
        log("heartbeat", "ninjakud alive")

if __name__ == "__main__":
    main()
