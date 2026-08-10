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
