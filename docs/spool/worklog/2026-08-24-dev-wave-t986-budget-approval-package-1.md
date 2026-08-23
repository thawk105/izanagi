---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: dev-wave-t986-budget-approval-package
seq: 1
title: [T-986] freeze v2 budget pin の見積り根拠と Pegasus pilot を pre-approval dossier に整備した (docs のみ、branch worktree-dev-wave-t986-budget-approval-package)
---

## 本文

- freeze v2 budget の authority は canonical approval 不在、`BUDGET_APPROVAL_SHA256=None`、v2
  candidate 未発行のまま維持した。暫定 pin、数値承認、official guard、正式 launch は行っていない。
- Pegasus `bnode009` で取得済みの trace-disabled n-pilot raw
  (`cdd5ade4017e86ba8079a8f7c6e9ed5a42332967a779f0777e9833998417d3fd`) を再集計した。
  rr20/rr80 × 6構成 × 11 round = 132 session は seq/cell-round とも全件一意、duration は平均
  26.781041秒・最大26.868566秒、全rep rc=0だった。non-certified / single-allocation / perf-off で、
  correctness・floor・oracle・n decision の証拠には昇格しない。
- `n=8` 条件では現行名目 reservation が total=2400 / holdoutごと=1200秒、pilot最大を27秒へ
  切り上げた planning candidate が2592/1296秒となる。ただし consumer は approved limit でなく
  名目 reservation を実測 `bench_wall_s` envelope に使うため、増枠192/96秒は実行時に利用できない。
- 段2 plan + 段3敵対2レンズで、pilot session duration と consumer量のquantity equivalence、n、
  allocation間変動が未成立と確認した。数値は operational approval にせず、推奨を承認保留にした。
- 成果物は `output/insights/2026-08-24_t986-budget-approval-package/README.md`。scope外の追加計測・
  reservation実装は同 insight と専用 handoff に所見だけ記録した。
- T-1484/T-1505 は別 worktree で attempt registry の acceptance 中。編集面・性能計測面とも重複せず、
  その所有物へ介入していない。

## 次の一手差分

### 完了

- [T-986] 見積り根拠・pilot実測・不確実性・数値択を pre-approval decision dossier に整備した。
  数値承認、canonical approval、pin、official guard、formal launch は当初どおり本項のscope外。
  remaining: none
  base: 463677463e90b39fb92ccadb26fb8d3b435541389afb1850e9b73be70116a291
