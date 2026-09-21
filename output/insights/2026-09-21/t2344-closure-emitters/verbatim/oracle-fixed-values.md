# 親が repo 外で実行した script の逐語 (`oracle_fixed_values.py`)

```python
"""親の独立 oracle: 提案 tuple 順 (既存 85 の順 + 11 本を sorted 順で末尾) から、
test_artifact_admission.py の固定値 (合成 E1 epoch、順序付き path 列 sha256) と、
exact-85 歴史 grammar の固定 epoch を production 定数を import せずに計算する (D1652)。
tuple は closure-head.json (着手 commit 5efd69367 の記録) から取る。
正例対照: 現行 85 から計算した値が、着手 commit の test 固定値 (_FIXED_SYNTHETIC_E1_EPOCH /
_FIXED_ORDERED_CLOSURE_PATHS_SHA256) と一致することを確かめる。
"""
import hashlib
import json
import re

J = "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-source-bound-emitters"
W = "/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2344-source-bound-emitters"
head = json.load(open(J + "/closure-head.json"))
enrolled85 = list(head["enrolled"])
assert len(enrolled85) == 85
new11 = list(head["new_members_sorted"])
assert new11 == sorted(new11) and len(new11) == 11 and not set(new11) & set(enrolled85)
proposed96 = enrolled85 + new11
assert proposed96 == head["proposed"]

DOMAIN = b"campaign-verifier-epoch/v1"


def fixture_epoch(paths):
    payload = DOMAIN + b"".join(
        rel.encode("utf-8") + b"\0"
        + hashlib.sha256(f"epoch closure fixture {i}\n".encode("ascii")).digest()
        for i, rel in enumerate(paths, start=1)
    )
    return "E1:" + hashlib.sha256(payload).hexdigest()


def ordered_sha(paths):
    return hashlib.sha256(b"".join(r.encode("utf-8") + b"\0" for r in paths)).hexdigest()


test_src = open(W + "/orchestrator/tests/test_artifact_admission.py", encoding="utf-8").read()
m_epoch = re.search(r'_FIXED_SYNTHETIC_E1_EPOCH\s*=\s*\(?\s*"(E1:[0-9a-f]{64})"', test_src)
m_sha = re.search(r'_FIXED_ORDERED_CLOSURE_PATHS_SHA256\s*=\s*\(?\s*"([0-9a-f]{64})"', test_src)

out = {
    "commit": head["commit"],
    "proposed_96": proposed96,
    "fixed_synthetic_e1_epoch_96": fixture_epoch(proposed96),
    "fixed_ordered_closure_paths_sha256_96": ordered_sha(proposed96),
    "exact85_fixed_epoch": fixture_epoch(enrolled85),
    "exact85_ordered_sha256": ordered_sha(enrolled85),
    "control_test_fixed_epoch_at_head": m_epoch.group(1) if m_epoch else None,
    "control_test_fixed_sha_at_head": m_sha.group(1) if m_sha else None,
}
out["control_epoch_matches"] = out["exact85_fixed_epoch"] == out["control_test_fixed_epoch_at_head"]
out["control_sha_matches"] = out["exact85_ordered_sha256"] == out["control_test_fixed_sha_at_head"]
json.dump(out, open(J + "/oracle-fixed-values.json", "w"), indent=2)
for k, v in out.items():
    if k != "proposed_96":
        print(k, v)
```
