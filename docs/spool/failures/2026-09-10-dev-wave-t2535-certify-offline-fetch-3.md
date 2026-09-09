---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2535-certify-offline-fetch
seq: 3
---

## 再発

### F500

- **再発: 2026-09-10** — 同じ job script へ新しい python3 呼出しを足す実装が、再び裸の
  `python3` を使った。今回の呼び先は pristine source verifier で、その import 経路には
  `orchestrator/holdout_observation.py` の `@dataclass(..., slots=True)` と
  `orchestrator/campaign/attempt_registry_core.py` の `typing.TypeAlias` があり、いずれも 3.10 以降
  でしか動かない。計算ノードの既定 `python3` は 3.9 に解決されるため、この呼出しは configure へ
  到達する前に必ず失敗する構成だった。**計算ノードへ投入する前に段 6 の敵対レビューが静的に検出し、
  同 file が既に持っていた版数 smoke check と同型の解決を verifier 用に置いて閉じた。**
  実害は出ていないが、同じ file の同じ型が 2 度目である。恒久対応は
  `orchestrator/tests/test_pegasus_calibration_workload.py` の
  `test_certify_third_party_verifier_uses_version_checked_interpreter` と
  `test_certify_third_party_verifier_interpreter_resolution_fails_closed` で、
  前者は裸 `python3` への差し戻しを変異走行で KILLED として実測している。
