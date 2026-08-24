---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1623-t1635-occupancy
seq: 5
---

## 再発

### F273

- **再発: 2026-08-25** — 受入全走 (tested tip `da3d774f`) が **15566 passed / 60 skipped /
  1 failed** で戻り、唯一の赤が `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed`
  だった。同日の別 wave と**同一の node・同一の症状**だが、こちらは **1 件だけ**である。
  台帳の再発検知どおり実測した — 受入時の login node は並行 `run_tests.py` が 17 本、
  load average 1.89 / 3.82 / 4.27。同 node の単独走 (`-k` で当該 1 件へ絞る) は
  **1 passed / 7.21 秒 / rc=0** で緑。
  当該テストは `max_wall=3` 秒と child pid の 2 秒 deadline を持つ時間境界依存であり、
  本 wave の差分 (`tools/check_worktree_occupancy.py`、`tools/dev_wave_cleanup.py`、
  `orchestrator/test_selection_contract.py` と各 test) から `tools/codex_worker_launch.py` への
  到達経路は無い。よって実装差分へ帰属させない。
- **ただし本 wave には差分から到達しうる経路が 1 本ある**ので記録する。本 wave の S4 は
  受入除外を空集合へ戻して `test_dev_wave_cleanup.py` を全走の母集合へ復帰させており、
  全走の node 数と負荷がその分だけ増える。時間境界依存のテストにとっては負荷が入力なので、
  「触っていないから無関係」だけでは切れない。1 件のみで系統的な形をしておらず、
  単独走が緑で、同日に同一 node の 4 件赤が別 wave でも起きていることから負荷由来と判定したが、
  この経路の存在自体は次に同型が出たときの検査対象として残す。
