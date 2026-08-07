# 段 1 の前提実測 (親、現 HEAD `c9990bc2` の worktree)

probe は **repo 外**の job directory
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/probe_premises.py`) に置き、
worktree へは 1 byte も書いていない。実行可能資材を repo へ持ち込まないため、
本書には**逐語と出力だけ**を凍結する。

## probe 逐語

```python
"""段 1 前提実測 probe (read-only)。repo 外に置き、worktree root を cwd にして実行する。"""
import importlib
import pathlib
import sys

sys.path.insert(0, ".")
m = importlib.import_module("orchestrator.campaign.reflux_origin_ledger")

budget = {
    "imax": 4,
    "qmax": 68,
    "kmax": 1,
    "batch_member_row_count_min": 2,
    "batch_distinct_candidate_count_min": 1,
    "query_floor_constraints": [
        {
            "formula_id": "q-lower-bound/base+perRound*R+Emin/v1",
            "base_queries": 1,
            "queries_per_round": 32,
            "rounds": 1,
            "evidence_min": 0,
        }
    ],
}
p = m._budget_from_object(budget)
print("parsed:", p.imax, p.qmax, p.kmax, p.batch_member_row_count_min,
      p.batch_distinct_candidate_count_min)
print("F(required_queries):", p.query_floor_constraints[0].required_queries)
print("codec feasibility (origin_bytes, head_tx_bytes):",
      m._check_budget_codec_feasibility(p))
print("MAX_BATCH_ROWS:", m._MAX_BATCH_MEMBER_ROW_COUNT)
effective = max(p.batch_member_row_count_min, p.batch_distinct_candidate_count_min)
print("batch_count = min(imax, qmax//effective) =", min(p.imax, p.qmax // effective))
print("AUTHORITY_RELATIVE_PATH:", m.AUTHORITY_RELATIVE_PATH)
ap = pathlib.Path(m.AUTHORITY_RELATIVE_PATH)
raw = ap.read_bytes()
print("authority bytes:", len(raw))
print("authority sha256:", m._sha256(raw))
print("authority content:", raw.decode())

# outcome/evidence の受理表を実測する。
cases = [
    ("accepted", m.EvidenceDigest("a" * 64), None),
    ("accepted", None, None),
    ("accepted", m.EvidenceDigest("a" * 64), "b" * 64),
    ("rejected", m.EvidenceDigest("a" * 64), "b" * 64),
    ("rejected", m.EvidenceDigest("a" * 64), None),
    ("tombstoned", None, None),
    ("tombstoned", m.EvidenceDigest("a" * 64), None),
    ("skipped", None, None),
]
for outcome, digest, constraint in cases:
    try:
        m._validate_result_matrix(
            outcome=outcome, evidence_digest=digest, constraint_sha256=constraint
        )
        verdict = "OK"
    except Exception as exc:  # noqa: BLE001 - 受理/拒否の実測が目的
        verdict = f"REJECT ({exc})"
    print(f"outcome={outcome} evidence={digest is not None} "
          f"constraint={constraint is not None} -> {verdict}")
```

## 出力 (逐語)

```text
parsed: 4 68 1 2 1
F(required_queries): 33
codec feasibility (origin_bytes, head_tx_bytes): (75206, 30753)
MAX_BATCH_ROWS: 2248
batch_count = min(imax, qmax//effective) = 4
AUTHORITY_RELATIVE_PATH: orchestrator/campaign/reflux_origin_authority_v2.json
authority bytes: 71
authority sha256: 76fb551fa6aa637487211039fca5c365275c5f49cb926d59bba3511da152ffd2
authority content: {"authority_schema":"izanagi-reflux-origin-authority/v2","origins":[]}

outcome=accepted evidence=True constraint=False -> OK
outcome=accepted evidence=False constraint=False -> REJECT (accepted result lacks evidence)
outcome=accepted evidence=True constraint=True -> REJECT (accepted result has a constraint digest)
outcome=rejected evidence=True constraint=True -> OK
outcome=rejected evidence=True constraint=False -> REJECT (invalid constraint digest)
outcome=tombstoned evidence=False constraint=False -> OK
outcome=tombstoned evidence=True constraint=False -> REJECT (tombstoned result has evidence)
outcome=skipped evidence=False constraint=False -> REJECT (invalid sealed outcome)
```

## この実測が示すこと / 示さないこと

- **示す**: 批准値が現 parser を通ること、`F=33`、本番 authority が 71 bytes・`origins: []` である
  こと、seal outcome の受理表。
- **示さない**: `batch_count=4` は `_check_budget_codec_feasibility` の**容量計算上の値**であり、
  実 producer topology の batch 数ではない (実 topology は 1 batch — 設計 §5.1)。
  codec bytes (75,206 / 30,753) も feasibility estimator の合成 frame 値であって、
  本 topology を公開経路で流した実測値ではない。
- probe は `_budget_from_object` / `_validate_result_matrix` という **private 関数**を直接呼んでいる。
  公開経路の挙動を測ったものではない。

## 段 4 で追加した現物確認 (grep と直接読解、probe 外)

- `reflux_origin_ledger.py:1618-1629` — certifiable seal の candidate 下限検査は
  `0 < batch.sealed_distinct_candidate_count < minimum`。全 tombstone batch は左辺 0 で検査に入らない。
- `reflux_origin_ledger.py:2917-2919` — `if not store.fixture: _fail("production runtime
  initialization is forbidden")`。
- `reflux_origin_ledger.py:2510-2542` — `_state_commitment` の preimage は全 origin と runtime head を含む。
- `loop.py:242-246` — `v = variant_id(g, src_tok); if v in done: s.skipped += 1; continue`。
- `trial_registry.py:1295-1321` と `autonomous_trial_completeness.py:63-70` — launch admission record の
  exact 7 key が両側で一致している。
