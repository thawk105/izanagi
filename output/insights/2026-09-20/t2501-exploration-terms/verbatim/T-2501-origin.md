# [T-2501] 依頼文の逐語 (/dev-wave の引数、2026-09-20)

[T-2501] (P2、D1879、実装手番 = 語の整理だけ) `docs/pegasus-runbook.md` の `IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す「exploration
  campaign」と D1813 の「探索」(B-10 第 1 段 `t2418-explore`) が別語である件を整理する docs-only wave。両語の定義と対応を runbook (必要なら
  glossary) に 1 節で書き、既存の凍結成果物・正式 consumer の受理集合・`run_kind` 必須化には触れない (D1879 が採らないと決めた 2 件)。D1859
  を全経路の保証へ広げない。着手直前の local main から fresh worktree。規律 2 を緩めない。語の整理だけ。仮想リスク向けの
  gate・検査・台帳・一般化の追加は scope 外。

# 起点 (worklog archive `docs/archive/worklog-phase3-0909-1390.md`、[T-2501] 起票行の逐語)

- [T-2501] **P2・ユーザー裁定待ち**: [T-2418] が scope 外として
  返した 4 件。(1) 正値 `BACKOFF_FIXED` の pointwise meaning witness を確立する gate の新設
  (現状は探索走に限らず既存 sweep 全体が `unestablished`)、(2) B-10 job 本体へ driver・patch・
  `pin.py`・condition gate の working bytes を HEAD へ拘束する検査の追加 (現状は job script の
  sha256 だけ)、(3) 既存の正式 consumer へ `completion["run_kind"] == "extended"` を必須化する案、
  (4) runbook の `IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す「exploration campaign」と D1813 の
  「探索」が別語であることの整理。いずれも既存の正式系列と共通の性質で、探索走に固有の弱体化ではない。
