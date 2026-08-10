# 親の実測 probe (逐語)

これらは repo の外 (`dev-wave-jobs/` の job dir) で走らせた運転用の使い捨て probe である。
実行可能な `.py` として repo へ入れると実装面になるため、逐語だけを markdown で残す
([T-317] 裁定: 境界は repo へ入るかどうか)。実行するときは job dir へ書き出して repo root を
cwd にする。

## `premise_probe.py` — 段 1 — 裁定前提の実測 (穴の実在確認)

```python
import json, sys
sys.path.insert(0, ".")
from orchestrator.campaign import s8c_preregistration as core
from orchestrator.campaign import s8c_preregistration_evidence as ev

raw_ok = open(core.EVIDENCE_CONTRACT_PATH, "rb").read()
v = json.loads(raw_ok)
# inject NUL into one required_evidence path and one consumer path
v["conditions"][0]["required_evidence"][0]["path"] += "\x00alias"
raw_bad = json.dumps(v, ensure_ascii=False).encode("utf-8")
print("raw contains literal NUL byte:", b"\x00" in raw_bad)
print("raw contains \\u0000 escape:", b"\\u0000" in raw_bad)

print("core.evidence_contract_sha256(bad) =", core.evidence_contract_sha256(raw_bad))
print("core.evidence_contract_sha256(ok)  =", core.evidence_contract_sha256(raw_ok))
try:
    ev.load_contract_bytes(raw_bad)
    print("load_contract_bytes(bad): ACCEPTED  <-- unexpected")
except ev.EvidenceContractError as exc:
    print("load_contract_bytes(bad): rejected reason=", exc.reason_code if hasattr(exc,'reason_code') else exc)
try:
    ev.semantic_contract_sha256(raw_bad)
    print("semantic_contract_sha256(bad): ACCEPTED <-- unexpected")
except ev.EvidenceContractError as exc:
    print("semantic_contract_sha256(bad): rejected")
```

## `oracle_probe.py` — 段 4 — 独立オラクルの実測 (実装後は再計算できない値)

```python
"""段 4 用: 実装前 (pre-T-739) の独立オラクル値を実測する。

このスクリプトの出力値は、実装後には再計算できない (新検査が拒否するため)。
テストへ literal として焼き込むための一次測定である。
"""
import hashlib
import json
import sys

sys.path.insert(0, ".")
from orchestrator.campaign import s8c_preregistration as core  # noqa: E402

# 1. legacy fixture: 自己完結の最小契約 (実契約ファイルに依存しない)
LEGACY = (
    b'{"conditions":[{"consumer_requirement":'
    b'{"path":"orchestrator/campaign/trial_registry.py\\u0000alias"}}]}'
)
print("LEGACY_NUL_CONTRACT bytes  =", LEGACY)
print("  literal NUL byte in raw  =", b"\x00" in LEGACY)
print("  pre-T-739 sha256         =", core.evidence_contract_sha256(LEGACY))

# 2. 発行 E2E 用 (既存 freeze ありの分岐) にも同じ契約を使えるか確認
value = core._strict_json(LEGACY, what=core.EVIDENCE_CONTRACT_PATH)
canonical = core._canonical_bytes(value)
print("  canonical bytes          =", canonical)
print("  recomputed               =", hashlib.sha256(core._DOMAIN_EVIDENCE + canonical).hexdigest())

# 3. 現行 g1 record の literal
g1 = json.loads(open(core.generation_path(1), "rb").read())
print("g1 evidence_contract_sha256 =", g1["evidence_contract_sha256"])
print("g1 protected_sha256         =", g1["protected_sha256"])
print("g1 generation_number        =", g1["generation_number"])

# 4. 実契約の全 path pointer を列挙 (テスト側の独立走査と同型)
real = json.loads(open(core.EVIDENCE_CONTRACT_PATH, "rb").read())


def walk(node, pointer=""):
    if isinstance(node, dict):
        for key, child in node.items():
            child_pointer = f"{pointer}/{key}"
            if key == "path" and isinstance(child, str):
                yield child_pointer
            yield from walk(child, child_pointer)
    elif isinstance(node, list):
        for index, child in enumerate(node):
            yield from walk(child, f"{pointer}/{index}")


pointers = list(walk(real))
print("real contract path pointers =", len(pointers))
print("  first =", pointers[0])
print("  last  =", pointers[-1])

# 5. malformed shape (裁定 A2): 起草案の列挙では取りこぼす形
MALFORMED = b'{"conditions":{"path":"x\\u0000alias"}}'
print("MALFORMED pre-T-739 sha256  =", core.evidence_contract_sha256(MALFORMED))
```

## `memory_probe.py` — 段 6 — レビュー所見のメモリ増幅を実測 (格下げ根拠)

```python
"""レビュー 1 の must-fix (幅広 JSON で走査 stack がメモリ増幅する) を実測する。

比較するのは同一入力に対する
  (A) 変更前相当 = _strict_json + _canonical_bytes + _sha256
  (B) 変更後     = (A) + _assert_no_nul_in_contract_paths
のピーク追加割当 (tracemalloc)。
"""
import json
import sys
import tracemalloc

sys.path.insert(0, ".")
from orchestrator.campaign import s8c_preregistration as core  # noqa: E402

print("MAX_BLOB_BYTES =", core.MAX_BLOB_BYTES)

for width in (10_000, 100_000):
    # canonicalization に成功する平坦で幅広い入力 (最悪形: 全要素が path を持つ dict)
    value = {"conditions": [{"path": f"p{i}"} for i in range(width)]}
    raw = json.dumps(value, ensure_ascii=False).encode("utf-8")
    print(f"\n--- width={width}  raw={len(raw)} bytes ---")

    tracemalloc.start()
    parsed = core._strict_json(raw, what=core.EVIDENCE_CONTRACT_PATH)
    canonical = core._canonical_bytes(parsed)
    base_cur, base_peak = tracemalloc.get_traced_memory()
    print(f"  (A) parse+canonical peak = {base_peak/1e6:.1f} MB")

    tracemalloc.reset_peak()
    core._assert_no_nul_in_contract_paths(parsed)
    walk_cur, walk_peak = tracemalloc.get_traced_memory()
    print(f"  (B) traversal peak (同一 snapshot 上の増分) = {walk_peak/1e6:.1f} MB")
    print(f"  traversal 追加分 = {(walk_peak-base_cur)/1e6:.1f} MB")
    print(f"  比 (traversal 追加 / raw bytes) = {(walk_peak-base_cur)/len(raw):.2f}x")
    tracemalloc.stop()
    del parsed, canonical, value, raw
```
