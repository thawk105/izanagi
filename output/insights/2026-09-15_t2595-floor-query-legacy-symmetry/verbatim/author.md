## 変更した file:line

- [s8b_holdout_admission.py:5881](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_holdout_admission.py:5881)：裁定の逐語コードへ置換。
- [test_s8b_holdout_admission.py:3543](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_holdout_admission.py:3543)：指定の 2 本を追加。

## 変更前後の受理・拒否挙動

- 使用済み legacy trigger に recovery 候補がある履歴：query は変更前の認可から拒否へ。consume・最終 inspection は従来どおり拒否。
- registry 不在：同じ trigger による retry1・retry2 の認可と consume を維持。
- 現行 production の成果物・certified 受理集合は変わりません。

## 追加テストと実走 nodeid

共通接頭辞は `orchestrator/tests/test_s8b_holdout_admission.py::`。

- `test_used_legacy_trigger_query_rejects_registry_recovery_candidates[valid-one]`
- `test_used_legacy_trigger_query_rejects_registry_recovery_candidates[corrupt-one]`
- `test_used_legacy_trigger_query_rejects_registry_recovery_candidates[valid-plus-corrupt]`
- `test_used_legacy_trigger_without_registry_authorizes_second_retry`

自走 harness で対象ファイル全体 **183 passed**。復元後の上記 4 nodeid も **4 passed**。

`test_plain_runner_coverage.py` の以下も実走し、**3 passed**。

- `test_every_test_file_is_self_runnable_or_allowlisted`
- `test_allowlist_has_no_stale_or_self_runnable_entries`
- `test_this_metatest_is_itself_self_runnable`

## 変更前に落ちることの確認

実装を一時復元して実走し、負例 3 ケースはすべて `DID NOT RAISE` で失敗。保存性の正例は変更前も通過しました。したがって「2 本とも落ちる」とは報告しません。

登録済み 4 変異もすべて予定どおり検出。最終ツリーは実装後へ復元済みです。

## 所有外への波及 (静的列挙)

- query の production 参照：`s8b_floor_campaign.py:6073`。
- テスト helper の参照元：`test_s8b_attempt_registry.py`、`test_s8b_floor_attempt_launcher.py`、`test_s8b_floor_stats.py`。
- 所有外の変更なし。新規ファイル・docs 編集・stage・commit なし。

## 残した赤

実装後の実走範囲に失敗なし。

duration 台帳の `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` は、内部で利用不可の `python -m pytest` を起動するため未実走。周辺 12 ファイルの回帰集合も全走していません。

## 総括

プラン v2 の実装と対象ファイルの検証を完了しました。`git diff --check` 通過。未実走の検査が残るため、全体の `closed` は申告しません。