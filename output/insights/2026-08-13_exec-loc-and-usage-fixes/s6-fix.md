## 所見対応表

テスト基盤が `rc=16` で停止したため、段 6 契約に従い全項を「実装済み・未実走」の `partial` とします。

| 所見 | 状態 | 根拠 |
|---|---|---|
| FIX-1 | partial | 全 replica の `_selected()` 結果を比較し、不一致を `message_id_collision` で fail-closed。正負 fixture 追加済み |
| FIX-2 | partial | record UUID、NFC 正規化 content digest、usage、model が完全一致する clone を結合。同じ UUID で証明不成立なら fatal |
| FIX-3 | partial | root file 2 本・各 2 streaming record の fixture で、root 1 回計上と両 collision 消失を固定 |
| FIX-4 | partial | canonical 条件を `msg_` + base62・最大256文字に限定。0/1/256/257文字、非ASCII、空白、制御文字の純関数テストと結線テストを追加 |
| FIX-5 | partial | 保証を「final representative map と final invalid set は相3まで書かない」へ修正 |
| FIX-6 | partial | request collision の冗長な `planned_invalid.update(group)` を削除し、component 単位の invalid 伝播へ一本化 |
| FIX-7 | partial | 指定された evidence 逐語へ同期。canonical loader による全フィールド・bytes 検証は `rc=0` |

`regressed` と判定した所見はありません。ただし pytest 未実走なので `closed` 申告もしません。

## 変更したファイルと差分の要約

- [tools/claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/tools/claude_session_ledger.py:449)
  - canonical message ID grammar
  - NFC content digest・canonical record UUID
  - exact-clone resolver、selector 一致検査、component invalid 伝播
  - 相保証の文言修正
- [test_claude_session_ledger.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_claude_session_ledger.py:527)
  - FIX-1〜FIX-4、FIX-6 の正負 fixture を追加
- [admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/tools/pegasus/admission_registry.json:8)
  - FIX-7 の evidence 逐語差し替え
- [test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_hooks.py:1758)
  - registry golden を同期
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_check_docs.py:1251)
  - 投影 fixture と期待診断を同期

`docs/**`、commit、index、stash には触れていません。

## 過大計上・過小計上を防ぐ根拠

過大計上は次で検出します。

- `test_message_only_and_request_only_replicas_do_not_double_count`
- `test_cross_file_replica_with_equal_selector_identity_counts_once`
- `test_root_root_streaming_replicas_count_once_without_collisions`

過小計上または誤った選択除外は次で検出します。

- `test_cross_file_replica_with_divergent_cwd_selection_fails_closed`
- `test_canonical_message_id_validator_boundaries`
- `test_noncanonical_message_id_connection_reports_message_id_collision`
- `test_shared_record_uuid_without_exact_clone_evidence_fails_closed`

短い偽 message ID による別 call の統合を拒否し、証明不能な clone 疑いも黙って二重計上しません。

## 実走した nodeid と結果

緑と報告できる nodeidはありません。

- 新規8 nodeidの焦点走: `rc=16`、未収集・未実走
- 指定3ファイル全走: `rc=16`、未収集・未実走
- 共通停止理由: `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1`

非pytest検査は以下が `rc=0` です。

- Python AST parse
- `git diff --check`
- `load_admission_registry(".")` による canonical bytes、`class == unknown`、`reason`、`primary_gate`、evidence 逐語一致

## 既存テストで期待値を変えたもの

あり。FIX-7 が明示的に要求した evidence golden／投影 fixture の文字列だけを変更しました。既存の受理・拒否、件数、rc の期待値は反転・緩和・skip・削除していません。

## 所有外への波及可能性

- `docs/pegasus-runbook.md` の投影行は親所有です。現在の作業ツリーでは新 evidence と静的に一致しています。
- ledger の dedup 結果を読む `tools/collect_wave_usage.py` と外部 report consumer は、exact clone の二重計上解消によって集計値が変わり得ます。
- admission registry は Codex worker 起動時の bytes pin 対象です。親が commit するまで未commit変更として worker 起動を止め得ます。
- dedup identity の説明文・algorithm version を外部 consumer が厳密比較している場合、親側で文書・schema 整合の確認が必要です。
- 実 transcript 1,045 files／30 collision 群は実行しておらず、合成 fixture のみです。

## 総括

FIX-1〜FIX-7の実装と回帰 fixture、registry同期は所有範囲内で完了しました。canonical loader と静的検査は成功しています。一方、指定テストはPegasusのdispatch基盤障害で一件も実走できていないため、全所見を正直に `partial（実装済み・未実走）` として引き渡します。