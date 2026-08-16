---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1066-wait-signal-flake
seq: 1
title: 実 signal 族フレークの真因は負荷依存の race ではなく 1 テストによる worker signal mask 汚染だった (コード + テスト、branch worktree-dev-wave-t1066-wait-signal-flake)
---

## 本文

- **依頼の前提を実測が覆した。** 依頼と F306 はいずれも
  「48 worker の並列下での timing 競合」を原因としていたが、真因は
  `orchestrator/tests/test_dev_wave_wait.py` の
  `test_signal_after_receipt_publish_does_not_reverse_success` **1 件による決定的な
  worker signal mask 汚染**だった。同 test の `delayed_signal` は `SIG_BLOCK` で
  real `pthread_sigmask` を呼んで実際に mask を変える一方、復元側の `SIG_SETMASK` では
  real syscall を呼ばずに例外を送出しており、`monkeypatch` は Python 属性しか戻さない。
  **この node を実行した pytest worker は寿命の終わりまで SIGTERM/SIGHUP/SIGINT が blocked**
  になる。負荷は「配送遅延の原因」ではなく「汚染 node の後ろに誰が配られるかを変える媒介」
  にすぎない。赤 node が族内を移動する既知の観測はこれで説明される。
- **汚染源が 1 箇所であることは全件検索で確定した。** 同 file の `pthread_sigmask`
  monkeypatch 7 箇所のうち real syscall を呼ぶのは当該 1 箇所だけで、他 6 箇所は
  `set()` を返す純粋な偽物である。
- **production にも独立した欠陥があった (段 2 と段 3 が独立に real 判定)。**
  `tools/dev_wave_wait.py` の 3 箇所が
  `previous_mask = pthread_sigmask(SIG_BLOCK, _HANDLED_SIGNALS)` の形で、syscall が mask を
  変更して返った後・左辺束縛の前に Python handler が `_SignalReceived` を送出しうる。
  親 brief は 2 箇所しか挙げておらず、`_publish_acceptance_receipt` の 1 箇所を落としていた
  (段 2 と段 3 の両方が指摘)。
- **親の provisional 裁定 4 件のうち 3 件が敵対相談で崩れた。** (P2) 「P1 が今回の赤の近因」は
  refuted (mask trace が無い)、(P3) 「負荷依存の独立した wall-clock defect」は未立証、
  (P4) 「barrier で決定的に再現できる」は refuted (Python の `Barrier` は native thread の
  scheduling を止めない)。決定的な注入は **main thread 内で完結する proxy**
  (real syscall 完了直後・呼び出し元へ戻る前に一度だけ送出) に変えた。
- **段 6 の敵対レビューが、直前 commit が入れた検出力の低下を捕まえた。** production に
  問い合わせ呼び出しが増えたため、既存の `fail_sigblock` test が問い合わせの時点で
  落ちるようになり、`RETAINED` 代入後の block 失敗経路と ownership 復元を一度も
  通らなくなっていた。fix で分岐させて回復した。
- **恒真も 1 件見つかった。** 既存 2 node は事前設置した外部 handler のおかげで、
  production の `_install_signal_handlers` を丸ごと no-op にしても緑のまま通っていた。
  handler の behavior identity (復帰後に呼ぶと `_SignalReceived` が出る) を検査する node を
  3 signal で新設して塞いだ。
- **handshake の検出力について正直に記録する。** ユーザー裁定に従い実 signal 4 箇所を
  イベント同期へ置換したが、**`_SIGNAL_WATCHDOG_SECONDS` を 0.0 にしても落ちる node は 1 つも無い**
  (段 6 レンズ B が指摘)。待機に検出力を持たせるには「signal が待機開始より後に届く」ことを
  保証する必要があり、それ自体が scheduler 依存になるため採らなかった。
  **恒真な kill を捏造せず、この事実をそのまま残す。** 真因を閉じているのは
  汚染源の修正と autouse guard と production の mask 復元であって、待機ではない。
- **変異は 2 巡した。** 1 巡目は 8 件中 5 件 KILLED、3 件 (M5/M6/M8) が期待 node の
  完全集合と不一致 (MISMATCH) だった。**実測は親の予想より広く、実 signal・実 subprocess の
  node が 3 件とも検出していた** — 段 3 レンズ B が疑った「実 subprocess node の検出力」への
  実測回答である。1 巡目を probe と明記し、実測完全集合へ再登録して 2 巡目を走らせた。
- **受入の唯一の赤は非帰属で、真因は機体固有の残骸だった。**
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` は
  本 wave の test file を走行に含めなくても再現する。原因は本ログインノードに存在する
  空ディレクトリ `/tmp/.git` で、`orchestrator/campaign/layout.py:_has_git_ancestor` が
  親を上へ辿るため `/tmp` 配下の一時 repo がすべて「repository 内」と判定される。
  **削除は repo 外の共有領域なので実施せずユーザーへ返した。**
- **段 2 の子 1 本を Web 検索で全損させた。** 1242 秒・38 model call で完走し出力 21,220 bytes が
  内容検査 rc=0 だったが、codex-cli 0.147.0 の `web_search` item が JSON の `id` キー重複行を
  吐き、launcher の `parse_jsonl` が 18 行拒否して `evidence_status=invalid` になった。
  prompt に Web 検索禁止を書き忘れたのが原因で、以後の全 prompt へ明記した。
- **並行 wave との衝突を実測で検知した。** t1142 が同じ 2 file を編集していることが
  `pgrep` の出力に出た子 prompt から判明した (先方の当初申告は fix21/fix22 で古くなっていた)。
  先方が先に land し、**合成監査の義務は本 wave が持つ**ことで合意した。
  先方が名指しした合成固有の経路 (先方の新段が `_StageFailure` で落ちる →
  `_cleanup_after_claim` を `merge_pending=True` で通る → 本 wave の mask 経路を通る) を
  取り込み時の監査対象にした。

## 次の一手差分

### 新規

- {{T:run-tests-scope-cap-alignment}} **P1・新規**: `tools/run_tests.py` の bounded local が
  確率的に `rc=16` (dispatcher infrastructure failure) で止まる。
  `_scope_properties_are_enforced` は cgroup の `memory.max` を予算値と文字列で厳密比較するが、
  予算は「前回ピーク × 1.25」で算出されるため 4096 の倍数にならず、kernel は page 境界へ丸める。
  実測: 予算 4294967296 (page 境界) の 2 走は成功、2913920000 / 1417630720 / 1545958400
  (いずれも `% 4096 == 1024`) の 4 走は全滅。保存ピーク 2331136000 × 1.25 が失敗した予算値と一致。
  **ローカル焦点走を使う全セッションが確率的に踏む。** 詳細は {{F:scope-cap-page-alignment}}。
- {{T:tmp-git-artifact}} **P2・新規・ユーザー手番**: 本ログインノードの `/tmp/.git`
  (空ディレクトリ、2026-07-28 作成) が
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` を決定的に赤にする。
  削除は repo 外の共有領域のため AI では実施しない。
- {{T:cleanup-zero-once-window}} **P2・新規**: `_cleanup_lifecycle` は cleanup body の前に
  ownership を `NONE` へ消費するため、body 中に別 thread 経由の signal が割り込むと
  exactly-once でなく zero-once になりうる。修正には outcome precedence の状態機械が要り、
  受理集合を変えるため本 wave では scope 外とした (段 6 レンズ A / B が独立に指摘)。
- {{T:mutation-harness-error-nodes}} **P2・新規**: `tools/mutation_harness.py` の失敗 node 抽出が
  `FAILED ` 行しか見ないため、fixture teardown の `ERROR` で落ちる変異が `PARSE_ERROR` になり
  `KILLED` と数えられない。本 wave は test 本体側へ assertion を足して回避した。
- {{T:return-to-store-gap-others}} **P3・新規**: 同形の return-to-store gap が
  `tools/mutation_harness.py:1076` と `orchestrator/qualification/t126_driver.py:242` にもある
  (別 owner)。`orchestrator/tests/test_t139_r4_env_probe.py:696-700` にも self-signal の
  即時仮定が残る。
- {{T:mask-guard-generalization}} **P3・新規・ユーザー裁定待ち**: 本 wave が入れた
  signal mask の autouse guard を `conftest.py` へ一般化するか。独立 2 例が揃っていないため
  `DW-G03` に従い module scope に留めた。

### 見送り追記

- [T-1066] 2026-08-16 にフレーク本体を解消した (本エントリ)。見送り対象である「受入投入前に ignored file を撤去する 1 行」は据え置きで再訪条件も変わらない。
