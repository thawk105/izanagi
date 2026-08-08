---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t656-walltime
seq: 3
---

## 再発

### F57

- **再発: 2026-08-08 ([T-656] 受入全走)。** 48 worker の全走 (request `896109`、7414 件) で
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が 1 件落ちた (7393 passed / 1 failed / 20 skipped)。assert 不一致ではなく
  `git -c core.useReplaceRefs=false cat-file --batch-check` の 15 秒 timeout (`returncode -9`) で、
  台帳既載の 2026-08-06 ([T-522]) / 2026-08-08 ([T-639]) と**同一 node・同一 producer**である。
  同 file の単独再走は 8 passed / 39.51 秒 (rc=0) で再現しない。本 wave の差分は
  `dispatch_compute` の既定 walltime 定数とその検査だけで当該コードへ到達せず、
  `DW-O18` により帰属しない。
  **新しい情報は、この全走が 40 分枠へ引き上げた最初の走行だったこと**である。走行そのものは
  Elapse 1213 秒で完走しており、枠不足 (F167 型) とは別型であることが同じ走行の中で分離できた。
  親は codex 子を 1 本も起動していない。恒久対応は F57 既載の失敗 artifact 保存による原因分離
  ([T-190]) のままで、本 wave では変えない。
