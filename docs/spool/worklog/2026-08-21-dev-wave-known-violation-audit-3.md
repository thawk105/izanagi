---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-known-violation-audit
seq: 3
title: 段8自己改善候補2件を発見したが dev-wave docs の byte 予算逼迫のため実装せず記録に留めた
---

## 本文

- 段8 自己改善で候補2件を発見した。`.claude/commands/dev-wave.md` が 9487/9500 bytes と
  ほぼ満杯であることを実測確認し (T-1362・T-1334・T-1434(4) 等の既知の逼迫と一致)、
  `docs/dev-wave/**` の3層 byte 予算も同様に逼迫していると判断し、いずれの reference 節も
  編集せず候補記録のみに留めた (通常の自己改善に予算変更を含めない契約どおり)。
  1. 汎用的な command 引数 (特定 ticket 不指名) の一次資料特定に archive worklog の広範な
     探索を要した。`DW-S01` へ「引数文言の逐語検索を先に行う」旨を追加する候補。
  2. shared main checkout (worktree 隔離前) で探索目的の全テスト走行を行うと、並行 wave の
     land 活動と衝突し near-miss の赤を生む (本 wave で実測: 12 failed+3 errorのうち11+3件が
     near-miss)。`DW-O18` または `DW-C00` へ「探索目的の全走も隔離 worktree で行う」旨を
     追加する候補。

## 次の一手差分
