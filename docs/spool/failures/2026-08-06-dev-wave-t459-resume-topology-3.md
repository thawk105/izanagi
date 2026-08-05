---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t459-resume-topology
seq: 3
---

## 再発

### F57

- **再発: 2026-08-06 ([T-459] 受入全走 2 回目)。** 計算ノードの全走で
  `test_codex_worker_launch.py::test_all_repo_policy_reasoning_values_are_accepted[high]` が
  launcher returncode 1 / stderr 空で 1 件落ちた。同 file の単独再走は 145 passed / 3.29 秒
  (request `891949`) で再現せず、main 取り込み後の全走も 6512 passed / 0 failed だった。
  **新しい情報は、この全走が親の起動した codex 子 (焦点再レビュー) と同時に走っていたこと**で、
  資源競合という既存の見立てと整合する。`DW-O18` により当該 wave の差分 (WAL 回復面) へは
  帰属しない。恒久対応は F57 既載のとおり失敗 artifact 保存による原因分離であり、
  本 wave では受入全走の隣で子 process を走らせない運用で回避した。
- **再発: 2026-08-06 (同 [T-459] の land 前受入)。** 同じ wave の別の全走で、今度は
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が `PreregistrationError: git-timeout` で 1 件落ちた。同 file の単独再走は 8 passed / 28.12 秒で
  再現しない。**新しい情報は、subprocess が codex launcher ではなく git であること** —
  全走の並列度が subprocess の wall-clock gate を押し出す型は、launcher 固有ではなく
  「全走中に外部 process を待つテスト」一般に及ぶ。この wave 単独で 2 つの独立した
  producer (codex launcher / git) が同型を出したため、族として扱う。
  `DW-O18` により当該 wave の差分 (WAL 回復面) へは帰属しない。
