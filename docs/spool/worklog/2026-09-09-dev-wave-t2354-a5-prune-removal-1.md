---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2354-a5-prune-removal
seq: 1
title: [T-2354] A-5 job 本体の共有 gitdir prune を撤去した — 後に終わる job が必ず落ちる構造を断ち、受理形は「静的な prune 不在」と「実 git 上の挙動」に分けた (コード + テスト + 台帳 + insight、branch worktree-dev-wave-t2354-a5-prune-removal、変異 5/5 KILLED + 事前登録した検出漏れ probe 1 件が期待どおり SURVIVED・期待 node 完全一致)
---

## 本文

- 依頼文は「workload ごとに checkout を分けるか prune を自 path の remove に限定するか」の二択を
  再掲していたが、D1700 は実装方向まで裁定済みで、checkout 分割案は却下されていた。裁定に従い
  二択へ戻さず prune 撤去だけを実装した。依頼文の二択は裁定前の worklog 項の写しである。
- 段 3 レンズ A の指摘で、段 2 plan が置こうとした remove 逐語の `count(...) == 1` pin を落とした。
  D1700 を満たす等価実装まで拒否し、依頼が意図した 1 点を超えて受理集合を狭めるため。設計判断は
  {{D:a5-cleanup-acceptance-split}}。
- 同じく段 3 の指摘で、失敗系 fixture を「登録されていない path を渡す」形から「自 path を
  `worktree lock` して remove を失敗させる」形へ変えた。前者だと入力をそのまま書き戻すだけの
  実装でも緑になり、残置が実在することを検査できない。lock 済み worktree の
  `remove --force` が rc=128 で登録・directory とも残すことは、裁定前に親が使い捨て
  repository で実測した。
- 段 6 レンズ A の「cleanup 2 関数の外へ置いた難読化 prune は静的層も runtime 層も通過する」は
  real だが、bash token 解析の gate 追加は依頼の scope 外として不採用にした。代わりに変異 m5 として
  事前登録し、期待どおり SURVIVED することを実測して限界を明記した。
- 段 3 レンズ A の「receipt 書き込み失敗の `|| true` を cleanup rc へ合成せよ」も real だが、
  `|| true` は現行コードに既に在り本 wave の退行ではないので不採用。合成は依頼が求めていない
  失敗経路を job rc へ足す。
- 受入所要時間台帳の被覆 gate は、新 node 2 件を登録する前から緑だった (79 passed)。
  F902 が記録する「main 側の余裕は 1 node 未満」は現在は解消している。登録自体は恒久対応どおり
  正本 producer の `--add-only` で Codex author 子が行った。
- 実装子は sandbox の制約で `run_tests.py` が rc=16 になり pytest を走らせられず、自走 harness
  だけで緑を出した。焦点走 5 本と JUnit 取得はすべて親が login 経由の dispatch で実走した。
- `dev_wave_codex.py` の `--reasoning` は plan/consult 専用で、author 段に付けると argparse が
  rc=2 で即死する。1 回踏んで runner を直した。
- 稼働中の `/cleanup-branches` session から worktree 撤去の照会があり、本 wave の worktree と
  branch を除外させた。先方の撤去判定は「worktree HEAD が main の祖先であること」なので、
  commit 済み未 land の本 wave は元々候補外だった。
- 記録は `output/insights/2026-09-09_t2354-a5-prune-removal/`。

## 次の一手差分

### 完了

- [T-2354] A-5 job 本体の終了処理から共有 submodule gitdir への `git worktree prune --expire now` を撤去し、自 path 2 つの `worktree remove --force` だけに限った。remove 失敗時は残置 path を receipt へ明示する。契約テストは prune の実行可能な不在だけを静的に固定し、remove の実挙動・receipt・rc 伝播は実 git repository 上で cleanup 関数を走らせる runtime test 2 本が固定する。登録簿は path key で sha256 pin を持たないため変更不要で、F660 は発火しない。
  remaining: none
  base: d59b46df85a16934e7f6ec567891e0b274297b6bbdff410bdea86ff4a336175c

### 新規

- {{T:t1998-prereg-new-job-body-digest}} **P2・新規**: T-1998 の事前登録を、着地後の A-5 job body digest `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` で作り直す。T-1998 launcher は同じ job body を再利用し、submitter が実 file を hash して reservation の `script_sha256` へ運び、consumer (`orchestrator/campaign/t1998_stock_inline_pair.py`) が事前登録の `launcher_script_sha256` と exact 比較する。旧 digest `0ef4d41e…` を持つ live な事前登録は repo 内に無く、T-1998 の正式測定も未実施なので既存の適格成果物は壊れないが、次の事前登録を旧値で作ると `launcher-script-identity-mismatch` で拒否される。歴史成果物の digest は書き換えない。正式測定の人間認可は代行しない。
