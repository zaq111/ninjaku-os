import fcntl
import os
from contextlib import contextmanager

LOCK_PATH = "/run/ninjaku/apply.lock"

@contextmanager
def apply_lock():
    os.makedirs(os.path.dirname(LOCK_PATH), exist_ok=True)
    with open(LOCK_PATH, "w") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
