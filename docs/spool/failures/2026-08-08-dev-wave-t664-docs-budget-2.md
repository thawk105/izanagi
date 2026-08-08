---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-08
wave: dev-wave-t664-docs-budget
seq: 2
---

## 再発

### F57

- **再発: 2026-08-08 ([T-664] 受入全走)** — 48 worker の全走 (request `896508`、Elapse 1255 秒) で
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が 1 件落ちた (**7458 passed / 1 failed / 20 skipped**)。既載の 2026-08-06 ([T-522]) /
  2026-08-08 ([T-639]) / 2026-08-08 ([T-656]) と**同一 node・同一 producer・同一原因**で、
  `git -c core.useReplaceRefs=false cat-file --batch-check` の 15 秒 timeout (`returncode -9`) である。
  同 file の単独再走は 8 passed / 41.82 秒 (rc=0) で再現しない。本 wave の差分は docs のみ
  (insights と spool fragment) で当該コードへ到達しえず、`DW-O18` により帰属しない。
  親は codex 子を 1 本も並走させていない (走行中の子 process は lease poll の 60 秒間隔 1 プロセスのみ)。
  **新しい情報は 2 点。**(i) 収集件数が 7,479 件へ増えた走行でも発生率は変わらず、
  同 node が 4 走連続で当たっている — 「失敗 node は毎回移動する」型ではなく
  「特定 node が繰り返し当たる」型であることをさらに補強する。
  (ii) 単独再走の 1 回目は `run_tests.py` の bounded local 経路で rc=16
  (`memory.max` / `memory.oom.group` を走行中に attest できず dispatcher infrastructure failure)
  となり、テスト結果を得られなかった。`--force-dispatch` を付けた 2 回目で 8 passed を得た。
  **F57 の再現性判定を bounded local の単独再走で行うと、判定そのものが基盤側の理由で空振りする。**
  恒久対応は F57 既載の失敗 artifact 保存による原因分離 ([T-190]) のままで、本 wave では変えない。
