---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t244-p3-liveness
seq: 4
title: [T-244] 生死実験エントリの受入件数を最終走の実測へ訂正する (docs のみ、branch worktree-dev-wave-t244-p3-liveness)
---

## 本文

- **訂正。** 直前エントリの見出しは受入全走を「6454 passed / 20 skipped」と書いたが、これは
  land した tip での値ではない。本 wave は受入全走を 3 回走らせている。
  (i) main 取り込み後の `b01a5aac` で **6454 passed / 20 skipped**、
  (ii) 記録・段 8 commit 後の `ed3550b8` で **6454 passed / 20 skipped**、
  (iii) 走行中に main が 6 commit 進んだため取り込み直した `b1c7deea` で
  **6483 passed / 20 skipped**。**land した tip は (iii) で、正しい値は 6483 passed / 20 skipped**
  (request 891952.nqsv、elapse 921.90s、rc=0)。
- 件数が増えたのは、取り込んだ main が別 wave のテストを持ち込んだためで、本 wave の差分が
  テストを増やしたわけではない。3 走とも rc=0、失敗ゼロである。
- 直前エントリの見出しは fold 済みで、fragment 段階での訂正 (先例あり) は使えない。
  canonical 台帳を直接編集しない規律に従い、本エントリで訂正を明示する。

## 次の一手差分

### carry

- [T-244]
