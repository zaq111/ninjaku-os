#!/usr/bin/env python3
import time
import sys
from pathlib import Path

sys.path.insert(0, "/opt/ninjaku")

from lib.db import init_db, connect

def log(action, detail=""):
    with connect() as db:
        db.execute(
            "INSERT INTO audit_logs(action, detail) VALUES(?,?)",
            (action, detail)
        )

def main():
    init_db()
    log("daemon_start", "ninjakud started")

    while True:
        time.sleep(60)
        log("heartbeat", "ninjakud alive")

if __name__ == "__main__":
    main()
