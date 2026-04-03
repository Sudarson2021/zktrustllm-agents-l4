import hashlib
import json
import time

def stable_hash(obj) -> str:
    data = json.dumps(obj, sort_keys=True).encode()
    return "0x" + hashlib.sha256(data).hexdigest()

def now_ts() -> int:
    return int(time.time())
