---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1316-postclaim-merge-escalation
seq: 2
---

## 再発

### F50

- **再発: 2026-08-19** — [T-1316] wave (背景 job + worktree 隔離) で、wave 開始時の brief 読み込みが
  `DW-C00`/`DW-STOP` の通読に留まり、条件 dispatch 表の「20 | 背景 job + worktree 隔離の wave 開始時」
  行を辿らなかったため、段4裁定完了・段5投入準備の直前まで `tools/check_wave_startup.py` を
  実行しなかった。実行して初めて submodule 未初期化・専用 handoff の worktree 内残留・HEAD が
  local main から6 commit 遅れの3件を検出し、実装着手前 (段5 投入前) に是正した (実害なし)。
  過去2回 (2026-07-29, 2026-08-03) の再発と同じ「置き場・読了タイミングを誤る」型で、F50 の
  恒久対応 (dispatch 前倒し、条件表20番の文言是正) は既に適用済みだったにもかかわらず、
  wave 開始時にその条件表自体を辿らなかったことが根本原因である。
