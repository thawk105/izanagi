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
