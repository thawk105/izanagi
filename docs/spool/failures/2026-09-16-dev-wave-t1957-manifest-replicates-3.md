---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t1957-manifest-replicates
seq: 3
---

## 再発

### F656

- **再発: 2026-09-16** — [T-1957] の段 6 で、親が実装 commit 直後の provenance full 監査を背景投入し
  (これも同一 worktree から計算ノードへ dispatch する)、それが走っている間に変異 harness を起動した。
  harness は collection 段で監査側の `pending-qsub` orphan hold を検出して rc=2 で止まり、
  orphan-stop sidecar を残した。変異は 1 件も注入されていない (`source_state: unchanged`)。
  監査の自然終了で hold は消え、sidecar は復旧条件 (対象 job の qstat 不在・dirty path なし・
  HEAD 一致・clean tree) を確かめてから撤去した。**種別の違う dispatch (provenance 監査) も
  直列化の対象である**という本エントリの恒久対応を、変異 harness の起動直前に確かめなかった。

### F830

- **再発: 2026-09-16** — [T-1957] の変異 probe で、orphan-hold 中断走 (attempt 2) が書いた
  `mutation-probe.done` (rc=2) を残したまま、launcher を phase だけで媒介変数化して
  attempt 3 を**同じ path へ**再投入した。親は稼働中の attempt 3 を「rc=2 で終了」と 1 度誤読し、
  台帳の記録件数 1/16 と整合しないことから `.done` の mtime (attempt 2 の時刻) と pid 生存を
  突き合わせて気づいた。本エントリの再発検知がそのまま効いた。本走は `.done` を phase 別の
  新 path にして投入した。
