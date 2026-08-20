---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1257-wait-producer-failclosed
seq: 3
title: '[T-1257] dev_wave_wait.py producer へ完了確定の fails-closed 検査を追加した — F355 再発検知条件を実装し変異2/2 KILLED、docs 予算制約で運用結線は次の一手へ (コード+テスト、branch worktree-dev-wave-t1257-wait-producer-failclosed)'
---

## 本文

依頼は worklog archive entry (602) が新規起票した T-1257 で、`tools/dev_wave_wait.py producer` が
producer 生存・完了印不在・出力ゼロで rc=0 終了する事象 (F355) の再発検知条件 (2 例目成立) を
満たしたための機序特定+fails-closed 検査の実装。段2 codex プラン (plan、1本) は「producer 起動時の
自己 detach」「一発検証モード」「両方の組合せ」の3案を評価し、自己 detach は SIGKILL/OOM/cgroup
reap を防げないため、成功時にだけ atomic に receipt を publish する一発検証モードを推奨した。

**段3 敵対相談2レンズ (consult、sol/luna 各1本) が2件の real 所見を出した。** レンズA (正しさ境界) は
「`--receipt-file` を再利用すると失敗回の古い receipt が残り stale success になりうる」を指摘、
親は run-id 方式でなく一意 path 規約 + mtime 記録で対処すると裁定した ({{D:producer-receipt-fails-closed}})。
レンズB (運用実効性) は「コードに `--check-only` を足すだけで呼び出し側が使わなければ絵に描いた餅」
と指摘し、この所見が段4裁定の scope 拡大 (運用契約への結線を必須化) の主因になった。

段5実装 (author、1本) は `_atomic_publish_json`/`_derive_producer_state`/`--check-only`/
`--receipt-file` を実装し、実 SIGKILL/SIGTERM 統合テストを新設した。段6敵対レビュー2本
(review) のうちレンズB が「固定 timeout (5秒) の環境依存フレーク」と「DW-M01 変異オラクルの
検出漏れ (producer 死亡判定を弱める変異が `_FakeEffects` の未キュー例外に紛れて SURVIVED
になりうる)」を real 所見として出した。親も独立に `-n` 並列実行下でのみ再現する赤を実測し
(単独 `-n 1` では 33 秒で緑)、fix を2巡投入した (5→30秒でも通常並列度でまだ赤、30→120秒で
解消)。fix1 は `_ProducerState` を直接注入し実ファイルで検証する専用テストを新設して
変異検出漏れも閉じた。焦点再レビュー (1本) は GO 判定。

親が `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -rf` (通常並列度) で
394 passed / 0 failed を実測し、統合commit `54bc579d` を作成した。変異matrix本走は初回 probe
(baseline PASSED、M1/M2 とも実際には KILLED だが親の事前登録 `expected_nodes` が不完全で
MISMATCH と判定) を実測し、`test_producer_check_only_missing_condition_is_fail_closed` も
診断文字列の不一致という別経路で同じ変異を正しく検出していたと判明したため
`expected_nodes` を完全集合へ補正して再登録した (DW-M08 の「初回 probe → 完全集合再登録」)。
再走は baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0。

**docs/dev-wave/core.md (DW-C00) と operations.md (DW-O01) への運用結線 (段4裁定の一部) は
本 wave では実施できなかった。** `python3 tools/check_docs.py` で `docs/dev-wave/**` の
L1 (443 byte 追記で 442 byte 超過)・L1.5 (73 byte 追記で 69 byte 超過) がいずれも予算超過し、
`.claude/commands/dev-wave.md` 自体も `COMMAND_LIMITS` の 9500 byte 上限に対し現在 9487 byte
(残り13 byte) とほぼ満杯で、条件 dispatch 表の拡張も入らないと判明した。3層とも実質スラック
ゼロという構造的制約のため、運用契約は F355 (`docs/failures.md` の supersede 追記) へ
書き、`{{T:dev-wave-docs-budget-check-only-wiring}}` を次の一手へ回した。

`--check-only` は本 wave 自身の待ち合わせ (focus-run2 の完了確認) で実運用として使用し、
schema `dev-wave-producer-receipt/v1` の receipt が正しく publish されることを確認した
(command 引数の dogfood 要求を満たす)。

工数: codex 子7本 (plan 1・consult 2・author 1・review 2・fix 2)、全て `check_codex_output.py`
rc=0。段8自己改善: 候補ゼロ (段構成・実装子権限・正しさ防壁・裁定境界・予算の変更を要する
候補は無かった)。

## 次の一手差分

### 完了

- [T-1257] `tools/dev_wave_wait.py producer` へ `--check-only`/`--receipt-file` の一発 fails-closed
  検査を追加した。producer 死亡+`.done`+artifact の3点照合が揃った場合だけ atomic に receipt を
  publish し、通知・stdout・rc は完了の証拠にしない。実 SIGKILL/SIGTERM 統合テストで F355 の症状を
  再現し正しく fail-closed することを確認、変異2/2 KILLED。運用契約 (DW-C00/DW-O01) への結線は
  docs 予算制約で次の一手へ回した (`{{T:dev-wave-docs-budget-check-only-wiring}}`)。
  remaining: none
  base: 844136858d5f5bbac955fc4a0cdcc2b2964397adf794592b7c2ba9153f644651

### 新規

- {{T:dev-wave-docs-budget-check-only-wiring}} **P2・新規**: `producer --check-only` を dev-wave
  運用契約 (`docs/dev-wave/core.md` DW-C00、`docs/dev-wave/operations.md` DW-O01) へ結線する。
  `docs/dev-wave/**` の L1/L1.5 byte 予算と `.claude/commands/dev-wave.md` (`COMMAND_LIMITS`
  9500 byte、残り13 byte) がいずれも実質スラック 0 のため、[T-1257] では実施できなかった。
  既存文言の圧縮を先に行うか、ユーザー裁定で予算例外を得てから結線する。一次資料は F355
  supersede 追記 (2026-08-20) と本エントリ。
