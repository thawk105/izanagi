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
