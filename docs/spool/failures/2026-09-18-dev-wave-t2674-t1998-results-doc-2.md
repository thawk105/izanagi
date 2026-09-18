---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2674-t1998-results-doc
seq: 2
---

## 再発

### F1

- **再発: 2026-09-18 (near miss、2 件)** — [T-2674] wave (T-1998 単独 results 稿、凍結物) の親が、(1) WAL の
  `tracked_diff_sha256` を Edit の本文へ**手打ちで転写**して 1 桁誤り (`…986cb…` を `…986dc…`)、(2) 是正 commit
  `4d7cd40a9` を最初に含む main first-parent 上の commit を `git log --since/--until` 付きの走査で `291892b90…`
  (11:40 JST) と導き、稿の §4 と時系列表へ書いた。(2) は同日 08:30 JST の `b1a3d45d…` が既に含んでおり、`--since`
  の絞り込みが境界を取り逃していた。(1) は親自身の機械照合 (稿の全 sha256 と数値を権威 bytes から再計算して突き合わせる
  使い捨て script) が commit 前に捕まえ、(2) は段 6 レンズ A が `git merge-base --is-ancestor` で反証して、
  land 前に両方とも直した。転写対象が日付・機構・推測の確度から **hash の手打ちと、絞り込み付き履歴走査の派生値**へ
  広がった顕在化。恒久対応は変更なし — 稿へ入れる hash は現物から貼り、履歴の境界は絞り込み無しで全区間を
  祖先判定して確かめる (`DW-O16` の「親が書いた派生値は原データから再計算して照合するまで closed としない」の対象)。
  一次資料は `output/insights/2026-09-18/t2674-t1998-results-doc/README.md` §3。
