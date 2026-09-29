---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-scoped-acceptance
seq: 1
title: 知識面だけの wave を縮小受入で land できるようにした — 分類は機械、land が lock 内で再導出し、実装面が混ざれば拒否する。独立 clone で docs だけの tip の land・実装混入の拒否・検査違反の赤を実物で確かめ、同時刻対照では wall は縮まらず無関係な赤で止まらない効果が出た (コード + test + docs + insight、branch worktree-dev-wave-scoped-acceptance)
---

## 本文

- 依頼: `/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/md_1.txt` (親 manager: vhash が作成、ユーザー発言の逐語を含む)。ユーザー発言を裁定として {{D:scoped-acceptance}} に記録した。一次資料 `output/insights/2026-09-29/scoped-acceptance/README.md`。
- 段構成: 全 9 段。段 2 plan 1 本、段 3 相談 3 本 (見逃す赤 / 受理集合の漏れ・偽造 / 過剰・削除)、段 5 Codex author 1 単位 (分類選択器と land 側を直列依存のため 1 単位に統合)、段 6 レビュー 2 本 + 焦点再レビュー 2 巡、fix 3 回 (fix3 は変異の再照準で test 追加のみ)。
- 実装 commit: 93af8d5b2 (段 5 統合)、b58ee226a (fix1)、88fa8f1f1 (fix2)、6ba3f5c72 (fix3、実装 anchor)。docs: d37c18fe3 (DW-S04 と decisions)、1e97b58e0 (新 test 2 本を pytest 専用 allowlist へ)。
- 新事実 (段 1 brief の前提を一部覆した): login の実効メモリ天井 15.0 GB を同じ user の他 session が使い切っており (23 時台に使用 17.0 GB)、縮小集合も計算ノードへ dispatch される。依頼文の「計算ノードの混雑に左右される全テスト待ちから外れる」は queue 待ちについては成り立たない。
- 効果 (同時刻対照 1 回、2026-09-30 01:26 JST、独立 clone、同じ tip): 縮小受入は child-green (3,889 passed、pytest 195.9 s、直接実行の検査 2 本 約 91 s、wall 14 分 14 秒)、受入全走は 3 shard で 3 failed / 28,254 passed (wall 11 分 22 秒)。wall は縮まらなかった (全受入は shard 並列、縮小は 1 job + 検査の直列)。効いたのは、受入全走が 2 回とも本 wave と無関係な赤で受領証を出さなかったのに対し、縮小受入は緑でそのまま land できたこと。
- 実物確認 (独立 clone): (a) docs だけの tip を縮小受領証で land (status=landed)、(b) 実装面 1 file 混入の tip は分類で不適格、縮小受領証での land は rc=23 で拒否、(c) 形式違反の spool fragment の tip は分類適格だが直接実行の check_docs が赤で受領証なし。
- 変異: MS1〜MS9・MF1〜MF6 の 15 本を事前登録。初回 probe で MS8 が生存 (既存 test が launcher 全体を走らせ後段の失敗が rc 検査の欠落を覆う mask)、`_gate` 直接呼び出しの test に再照準した。final は 15/15 が期待 node と完全一致で KILLED。
- 段 6 で直したもの: 引用文字列内だけの照合がコメントのアポストロフィで参照を見逃す、鍵が粗く実在の知識面 land が 0/10 しか縮小可にならない、insight の「日付_slug」形の深さ 3 dir を読む実在 reader の見逃し、既存関数の signature 変更で既存 D987 test 4 件を壊した回帰。最終版で実在の知識面 land 10 区間中 4 区間が縮小可。
- 棄却・訂正: 段 1 brief (P5) の login 完結は refuted。段 2 plan の production reader の AST 全走査は過剰として不採用 (文字列照合 + 点検済み入れ物 reader 一覧)。依頼文の負例「pin された節の改変」は許可集合の外なので、許可 path 内の検査違反に置き換えた。焦点再レビュー 2 の残り (下位の入れ物 path・分割文字列・日付 dir を列挙する reader) は、現行 tree の実例が開発道具 1 本 (test は選択される) だけで実害なしとして限界に記録し、fix は 3 巡のうち 2 巡で閉じた。
- 取りこぼし: 親の焦点走が新規 test file 用の plain runner meta-test (`test_plain_runner_coverage.py`) を含めておらず (DW-O26 の義務)、独立 clone の受入全走で初めて allowlist 漏れが見つかった。1e97b58e0 で直した。
- 異常: 背景 job の EnterWorktree(name) が git config の読み取りエラー、path 形は worktree list の 10 秒 timeout で失敗し、手動 add と絶対 path で作業した。子木の gitdir に 0 byte の index.lock 残骸が残り、起動器・待ち手の残差 commit が add-all で失敗した (生存 process なしを確かめて削除し、待ち手を再実行して回復)。独立 clone は user 設定が無く最初の commit で止まった。
- 受入 attempt 1 の赤の判定 (DW-O18): 記録 commit f72f5deda に local main 6581ef6cd を post-claim merge した木 6f4209fb0 で 28,261 passed / 74 skipped / 赤 1 件 —
  `orchestrator/tests/test_dev_wave_cleanup.py::test_repository_removal_lock_is_nonblocking_and_released[sigkill-remove-child]`。**非帰属**: 本 wave の変更 module
  (dev_wave_land・dev_wave_wait・run_tests・scoped_acceptance*) を test も対象 tool も import しない。同じ木で当該 test を計算ノードで単独再走して 4 passed (8.04 s) で非再現。
  受入を投げ直す。独立 clone の受入全走 2 回でも同じ file の別 node が赤になっていた (clone 環境、同じく本 wave 非帰属)。
- 受入全走はこの記録 commit の tip で行い、受領証は job dir (`/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/`) に残す (受入後にこの fragment を書き足すと受入のやり直しになるため、結果は書き足さない)。

## 次の一手差分

### 新規

- {{T:scoped-acceptance-wall}} **P2・新規**: 縮小受入の wall を縮める。受入全走は shard 並列、縮小受入は 1 job で直接実行の検査 2 本 (約 91 s) を login で先に直列に走らせるため、同時刻対照で wall が全受入より長かった (一次資料 `output/insights/2026-09-29/scoped-acceptance/README.md` §7)。shard 分割と検査の並列化を、受理集合を変えずに試す。
- {{T:scoped-acceptance-container-readers}} **P3・新規**: 縮小受入の分類が拾わない入れ物 reader (下位の入れ物 path・分割文字列・日付 dir を列挙する reader) を、実例が出たときに点検済み一覧か鍵へ足す。現行 tree の実例は `tools/dev_waves/git_state.py` だけ (同 §10)。
