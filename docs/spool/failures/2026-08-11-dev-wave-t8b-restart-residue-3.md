---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-11
wave: dev-wave-t8b-restart-residue
seq: 3
---

## 再発

### F57

- **再発: 2026-08-11 (8b 再開残余 wave の受入全走 2 走目)。** 1 走目 (tip `ba73d199`) が
  **8483 passed / 20 skipped / 547.73 秒 / rc=0** で緑だったのに対し、
  **docs 2 commit だけを積んだ** tip `73c8ba95` の 2 走目は
  `test_codex_worker_launch.py::test_fake_stdout_matches_observed_cli_event_shape` が 1 件落ちた
  (**1 failed / 8482 passed / 20 skipped / 538.44 秒**)。述語は既載と同じ 2 本
  (`failed_predicates=["process_group_residual","termination_verified"]`) で、
  `codex_exit_code=0` / `validator_rc=0` / `evidence_status='complete'` /
  `metering_status='complete'` はすべて正常、`wall_clock_s=0.139159472` も上限に対し十分小さい。
  同 file の単独再走は **97 passed / 6.27 秒 / rc=0** で再現しない。
  本 wave の差分は **docs のみ**で launcher 実装にも同 test file にも到達しえず、
  `DW-O18` により帰属しない。
  **新しい情報が 2 つある。** (1) `loadavg=(12.92, 3.66, 1.90)` で発火した。
  既載は 15.05 と 12.67 で、12 台での発火は 2 例目となり
  「1 分平均 15 台が閾値ではない」という既載の観察を補強する。
  (2) **同一 file の 3 つ目の node** (`test_fake_stdout_matches_observed_cli_event_shape`) である。
  既載は `test_late_rollout_writer_does_not_change_sealed_receipt` と
  `test_all_repo_policy_reasoning_values_are_accepted[xhigh]` で、
  述語系の不成立が同 file 内を移動し続けることの 3 例目にあたる。
  **同一 wave で docs 2 commit しか違わない 2 tip の全走が、緑 → 赤と割れた対照は初出**であり、
  差分ではなく走行そのものに依存することの直接の証拠になる
- **再発: 2026-08-11 (同 wave の受入全走 6 走目、別 test file)。** main 取り込み後の tip
  `73fe73bc` の全走で
  `test_campaign.py::test_pipeline_stale_screening_falls_back_to_verify_first_and_records_trace`
  が 1 件落ちた (**1 failed / 8573 passed / 20 skipped / 555.67 秒**)。
  単独 node の再走は **1 passed / 2.40 秒 / rc=0** で再現しない。
  本 wave の差分は docs のみで同 test file へ到達しえず、`DW-O18` により帰属しない。
  同 node は 2026-08-11 の 8b 統合 wave でも変異 MU-1 の判定を MISMATCH にした既載であり、
  **launcher 系 (`test_codex_worker_launch.py`) 以外の node も同じ性質を示す**ことの 2 例目。
  **新しい情報は、docs のみの 1 wave の中で受入全走 4 本のうち 2 本が別 node で赤になったこと**
  である。既載の再発はいずれも「1 走で当たり、次走または単独走で緑」であり、
  **同一 wave 内で 2 件・別 file というのは初出**である。並行 wave の land が続く時間帯には
  「再走すれば緑が取れる」という運用上の前提が成り立ちにくいことを示す
