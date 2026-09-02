---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2091-openalex-cond1-order
seq: 1
---

## 再発

### F300

- **再発: 2026-09-02 (2 回、両 sub-type)** — 本走 attempt 1 は親が走行中に
  `git checkout main -- docs/` を実行して落ちた (F300 本文の型)。base digest は land 先の
  local main の現物に対して取る規則があり、この lookup は作業ツリーへ main の docs を
  一時展開する。**base digest の取得は変異走行と排他である。**
  attempt 2 は作業ツリーに一切触れずに落ちた (2026-08-25 再発項の型、並行 wave の land)。
  いずれも `child_rc = 0` で harness は完走し、結果は 10/10 KILLED・期待 node 完全一致・
  baseline PASSED だった。成果物への帰属は無い。
- **既知の回避策を読まずに走らせた。** 2026-08-25 の再発項が
  「対象 commit だけを持つ独立 clone を `--source-repo` へ渡すと観測点が 1 点に畳まれる」と
  実測付きで記録していた。**変異走行の前に本台帳の当該 F を引く**のが再発検知である。
- **回避策を `DW-M05` へ載せる 2 度目の試みも予算で止まった。** 219 bytes の 1 文に対し
  L1.5 層の余裕は 18 bytes (実測: 追記前 9,678 / 予算 9,696)。既存記述の削減は同層の
  安全義務文を削ることになるため採らず、D782 が委任する D730 の段階 2・3
  (例外収容・上限引き上げ) は本 wave の scope を超える。回避策の正本は本台帳に留まる。
