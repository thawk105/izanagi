# 親が repo 外で実行した script の逐語 (`scan_recent_locks.py`)

```python
"""exact-85 grammar の実在 corpus を探す: 65e94a3a7 (exact-85 化 commit、2026-09-20 21:55 JST) 以降に書かれた
campaign.lock を /work/1/SFC/tanab と /home/SFC/tanab 全域から探し、authority の key 数で分類する。

出力: recent-locks.json
"""
import json
import os
import sys
import time

J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
SINCE = time.mktime(time.strptime("2026-09-20 21:55:00", "%Y-%m-%d %H:%M:%S"))  # JST (TZ of host)
ROOTS = ["/work/1/SFC/tanab", "/home/SFC/tanab"]
SKIP_DIRS = {".git", "external", "__pycache__", "node_modules", ".cache"}

rows = []
scanned_dirs = 0
for root in ROOTS:
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda e: None):
        scanned_dirs += 1
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        if "campaign.lock" not in filenames:
            continue
        p = os.path.join(dirpath, "campaign.lock")
        try:
            st = os.stat(p)
        except OSError:
            continue
        if st.st_mtime < SINCE:
            continue
        try:
            doc = json.loads(open(p, encoding="utf-8").read())
            auth = doc.get("authority")
            blobs = auth.get("contract_loader_blob_sha256s") if isinstance(auth, dict) else None
            n = len(blobs) if isinstance(blobs, dict) else None
            rows.append({"path": p, "mtime": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(st.st_mtime)),
                         "keys": n, "schema": doc.get("schema_version")})
        except Exception as exc:  # noqa: BLE001
            rows.append({"path": p, "error": str(exc)[:200]})

out = {"since": "2026-09-20 21:55:00 JST", "roots": ROOTS, "skip_dirs": sorted(SKIP_DIRS),
       "scanned_dirs": scanned_dirs, "locks": sorted(rows, key=lambda r: r["path"])}
json.dump(out, open(J + "/recent-locks.json", "w"), indent=2, ensure_ascii=False)
from collections import Counter
print("scanned_dirs", scanned_dirs, "recent locks", len(rows))
print(Counter(str(r.get("keys")) for r in rows))
for r in rows:
    if r.get("keys") == 85:
        print(r)
```
