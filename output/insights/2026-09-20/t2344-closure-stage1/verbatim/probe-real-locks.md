# 実 lock 20 本での受入到達点 probe (親が repo 外で実行、逐語)

`python3 -I -B probe_real_locks.py <wave worktree> <out.json>` で実行した。結果は `../real-locks-probe.json`。

```python
"""s4-ruling §3 の受入到達点: 記録済み exact-63 lock 20 本を、wave worktree (commit 済み) の code で読む。
- 必達 A: 20 本すべて decode_historical_campaign_lock_bytes が成功し recorded tuple が exact-63 literal。
- 必達 B: 代表 3 本で require_campaign_verifier_epoch(HISTORICAL_RAW) が HistoricalCampaignVerifierEpoch (E1、旧 63 scope)。
- 必達 C: 同 3 本で通常 decoder が CampaignLockCodecError、CERTIFIED_ACCEPTANCE の epoch API が拒否。
- bytes 不変: 前後で lock の sha256 不変。
usage: python3 -I probe_real_locks.py <wave worktree abs> <out.json>
"""
import hashlib
import json
import sys
from pathlib import Path

W = sys.argv[1]
OUT = Path(sys.argv[2])
sys.path.insert(0, W)
from orchestrator.campaign import artifact_admission as A  # noqa: E402
from orchestrator.campaign import campaign_lock as CL  # noqa: E402

J = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-stage")
locks = json.load(open(J / "exact63-locks-verify.json"))["locks"]
REPR = (
    "b10-backoff-grid-t2500-formal/b10-backoff-grid-20260919T131526Z-2235286-balanced",
    "izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2489-20260918a/jobs/rr5",
    "t1998-balanced-stock-inline-runs",
)
old_scope = getattr(CL, "T2429_EXACT63_CONTRACT_LOADER_RELATIVE_PATHS")
res = {"worktree": W, "n": len(locks), "A": [], "B": [], "C": [], "bytes_unchanged": True}
for l in locks:
    p = Path(l["path"])
    raw = p.read_bytes()
    before = hashlib.sha256(raw).hexdigest()
    rowA = {"path": l["path"], "recorded_sha256_match": before == l["lock_sha256"]}
    try:
        d = CL.decode_historical_campaign_lock_bytes(raw)
        rowA["decoded"] = type(d).__name__
        rowA["grammar_is_exact63"] = (
            d.authority is not None
            and d.authority.recorded_contract_loader_relative_paths == old_scope
        )
        rowA["ok"] = rowA["decoded"] == "DecodedHistoricalCampaignLock" and rowA["grammar_is_exact63"]
    except Exception as exc:  # noqa: BLE001
        rowA["error"] = f"{type(exc).__name__}: {exc}"[:300]
        rowA["ok"] = False
    res["A"].append(rowA)
    if any(r in l["path"] for r in REPR):
        campaign_dir = p.parent
        rowB = {"path": l["path"]}
        try:
            ep = A.require_campaign_verifier_epoch(campaign_dir, purpose=A.CampaignReadPurpose.HISTORICAL_RAW)
            rowB.update({
                "type": type(ep).__name__, "state": ep.state, "reason": ep.reason_code,
                "epoch": ep.campaign_verifier_epoch,
                "identity_scope_is_old63": ep.identity_scope == A.T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_SCOPE,
                "excluded_scope_is_old63": ep.excluded_scope == A.T2429_EXACT63_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE,
                "conformance": ep.current_verifier_conformance,
            })
            rowB["ok"] = (rowB["type"] == "HistoricalCampaignVerifierEpoch" and ep.state == "E1"
                          and rowB["identity_scope_is_old63"] and rowB["excluded_scope_is_old63"])
        except Exception as exc:  # noqa: BLE001
            rowB["error"] = f"{type(exc).__name__}: {exc}"[:400]
            rowB["ok"] = False
        res["B"].append(rowB)
        rowC = {"path": l["path"]}
        try:
            CL.decode_campaign_lock_bytes(raw)
            rowC["normal_decoder"] = "ACCEPTED (violation)"
            rowC["ok_normal"] = False
        except CL.CampaignLockCodecError as exc:
            rowC["normal_decoder"] = f"rejected: {exc}"[:200]
            rowC["ok_normal"] = True
        try:
            A.require_campaign_verifier_epoch(campaign_dir, purpose=A.CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
            rowC["certified_epoch"] = "ACCEPTED (violation)"
            rowC["ok_certified"] = False
        except Exception as exc:  # noqa: BLE001
            rowC["certified_epoch"] = f"rejected: {type(exc).__name__}: {exc}"[:200]
            rowC["ok_certified"] = True
        rowC["ok"] = rowC["ok_normal"] and rowC["ok_certified"]
        res["C"].append(rowC)
    after = hashlib.sha256(p.read_bytes()).hexdigest()
    if after != before:
        res["bytes_unchanged"] = False
res["A_ok"] = sum(r["ok"] for r in res["A"])
res["B_ok"] = sum(r["ok"] for r in res["B"])
res["C_ok"] = sum(r["ok"] for r in res["C"])
OUT.write_text(json.dumps(res, indent=2, ensure_ascii=False))
print("A", res["A_ok"], "/", len(res["A"]), " B", res["B_ok"], "/", len(res["B"]),
      " C", res["C_ok"], "/", len(res["C"]), " bytes_unchanged", res["bytes_unchanged"])
for r in res["B"]:
    print("B", r.get("ok"), r.get("type"), r.get("state"), r.get("epoch"), r.get("error", ""))
for r in res["C"]:
    print("C", r.get("ok"), r.get("normal_decoder"), "|", r.get("certified_epoch"))
```
