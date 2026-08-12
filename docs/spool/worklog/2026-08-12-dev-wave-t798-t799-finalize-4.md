---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t798-t799-finalize
seq: 4
title: dev-wave 段 8 — 受入待ち手と probe 設計の改善候補 2 件を台帳へ送る
---

## 本文

[T-798] / [T-799] / [T-820] / [T-821] の land 後に、段 8 (自己改善) の候補 2 件を
失敗台帳へ送った。いずれも本 wave で実害が出ている。

- **受入待ち手の merge 競合診断** ({{F:waiter-merge-conflict-hides-paths}})。
  lease 取得後の取り込みが競合すると `stage=merge rc=70` の 1 行だけが残り、
  競合 path が出ない。親は `git merge` を手で再現して特定した。実際の競合は
  `orchestrator/tests/test_spool_fold.py` の import 3 行だけだったが、
  待ち行列 5 本を待って得た lease 1 サイクルを丸ごと捨てた。
  解決方針 (実装面を自動解決しない) は D95 に照らして正しく、直すべきは診断の粒度である。
- **land の相を測る probe に git hook が使えない** ({{F:land-phase-probe-cannot-use-hooks}})。
  `GIT_HARDENING_CONFIG` が `core.hooksPath=/dev/null` を設定しているため hook は発火しない。
  `DW-O01` は背景 job の detach 形を書いているが、この制約を書いていない。
  代替は二相 ref-watcher で、本 wave の probe が実体である。

なお [T-821] の receipt schema 拡張は land で実地確認できた。`docs/spool/FOLDED.md` の
本 wave の 2 record は `base` / `tested_tip` / `wave_ref` を持ち、直前の他 wave の
legacy record と同一ファイル内で共存している。positional cutover (本 wave が land した
D318 の設計) が意図どおり働いた。

## 次の一手差分

### 新規

- {{T:waiter-conflict-diagnostics}} **P2・新規**: 受入待ち手の merge 競合診断に競合 path を
  出させる。現状は `stage=merge rc=70` だけで、親が `git merge` を手で再現しないと
  着手できない。待ち手が abort する前に `git diff --diff-filter=U --name-only` を
  job directory のファイルへ書き出すだけで往復が 1 つ減る。
  {{F:waiter-merge-conflict-hides-paths}} の残余。
