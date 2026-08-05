---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-f26-recurrence-record
seq: 2
title: F26 の同型再発を記録した — deinit 経路は 2 度目で、前回が診断した DW-S09 のポインタ欠落が予算超過で未実装のまま残る (docs のみ、branch worktree-dev-wave-f26-recurrence-record)
---

## 本文

- [T-472] の land 完了後、自分の worktree を畳む段で **F26 と同一経路の再発**を起こした。
  `git worktree remove` の submodule 無条件拒否に当たった時点で `/cleanup-branches` §3 を
  読まず、即興で `git submodule deinit` を打ち、main checkout の submodule 登録を消した。
  復元済み・実害は一時的。詳細は F26 の再発追記。
- **前回 (2026-08-01) の再発が特定した経路欠落は、今も塞がれていない。**
  `DW-S09` に「自分の worktree を畳む手順の正本は `/cleanup-branches` §3」というポインタを
  足そうとしたが、`docs/dev-wave/**` が hard ceiling 25200 bytes に対して 25377 bytes となり
  入らなかった。**docs 予算の上限は上げない規律**のため追記を撤回し、
  {{T:dw-s09-cleanup-pointer-budget}} として裁定へ返した。
- この wave は [T-472] wave の後片付けから派生した docs-only の記録であり、
  実装差分がないため変異 matrix と受入全走は対象外である (`DW-S04`)。
  受入は `python3 tools/check_docs.py` (違反なし) と影響テスト
  `test_check_docs.py` + `test_spool_fold.py` (**350 passed**、計算ノード request 889682) で閉じた。
- **念のため投入した受入全走は汚染された。** 別セッションの変異 harness
  (`dev-wave-t452-t453-clock-authority`、8 変異 × 5400s 見積りで走行中) と同時に走り、
  `test_s8b_oracle_driver.py` の `@real-repo` 系を含む 79 件が赤になった
  (request 889684、6083 passed / 79 failed)。本 wave の差分は spool fragment 2 ファイル
  67 行の追加のみで、これらのテストに到達しえない。**変異走行中に受入全走を投入しない**
  という既知の規律 ([T-476] が扱っている機序 — harness の flock は他 harness だけを排除し、
  実 repo を読むテストは mutant 入りの木を見る) を、投入前に確認しなかったのが原因である。
  他 harness の完走を待つと 12 時間規模になるため、docs-only の受入根拠 (上記) で閉じた。

## 次の一手差分

### 新規

- {{T:dw-s09-cleanup-pointer-budget}} **P2・ユーザー裁定待ち**: `DW-S09` へ
  「自分の worktree を畳む手順の正本は `.claude/commands/cleanup-branches.md` §3、
  `git worktree remove` と `submodule deinit` を即興で使わない (F26)」を追記したいが、
  `docs/dev-wave/**` が hard ceiling 25200 bytes に張り付いており 177 bytes 超過で入らない。
  F26 は 2026-08-01 と 2026-08-05 の 2 回、この経路欠落が原因で再発している (DW-G03 の
  独立 2 例を満たす)。択一 = (a) `docs/dev-wave/` 内の陳腐化した記述を削って枠を作る
  (どれを削るかの裁定が要る)、(b) 機械検査へ移す — worktree 撤去時に
  `git submodule status` の `-` prefix を検出する hook / テストを足し、docs 追記をやめる、
  (c) 現状維持で memory と F26 の判別に委ねる。親の推奨 = **(b)**
  (docs 予算を使わず、恒真でない機械防壁になるため)
