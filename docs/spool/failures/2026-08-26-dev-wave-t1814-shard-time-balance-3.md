---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1814-shard-time-balance
seq: 3
---

## 再発

### F489

- **再発: 2026-08-26** — **D793 の恒久対応と `[T-1623]` の land 後も、受入全走で再発した。**
  実装差分ゼロ (docs のみ) の wave の受入全走が 2 走とも
  `1 failed / 17097 passed / 62 skipped` で戻り、赤はどちらも
  `orchestrator/tests/test_dev_wave_cleanup.py` の中だが**別の node** だった
  (1 走目 `test_forward_merged_landing_tip_is_used_for_cleanup[asserted]`、
  2 走目 `test_reentry_states_run_only_remaining_cleanup[b]`)。
  本文は 2 走とも逐語一致で
  `dev-wave-cleanup: status=rejected phase=occupancy reason=occupancy result is indeterminate or inconsistent; attempts=1 retry_count=0` の rc=22 である。
  同 file の単独走は **94 passed / 3.93 秒 / rc=0** で非再現だった。
  本 wave の差分は `docs/spool/**` と `output/insights/**` だけで、
  `tools/check_worktree_occupancy.py` へ到達する経路は無い。
  **落ちる node が走ごとに動くため、node 単位の hold では塞がらない。**
  脆弱なのは「占有検査の成功を前提に rc=0 を要求する正例」という class であり、
  この class は同 file 内に複数ある。
  2026-08-24 の再発では `orchestrator/test_selection_contract.py` の
  `SANCTIONED_EXCLUSIONS` へ file 単位の一時除外を入れて凌いだが、その除外は
  `[T-1623]` の land 時に空集合へ戻されている (現在 `SANCTIONED_EXCLUSIONS = ()`)。
  除外を戻すか、class 単位の hold を作るか、占有検査を計算ノードの
  process churn に依らない形へ変えるかは受理集合を変える判断であり、
  ユーザー裁定へ返した。本 wave は land せずに停止した。
