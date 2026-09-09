## 実装結果

F1〜F4 をすべて実装しました。

- F1: 系列別 lock SHA-256 literal 3 本を追加し、raw bytes 読取直後かつ歴史 decoder 前に exact 比較して、相違を `resume-binding` で拒否します。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3104)
- F2: 歴史値 `b10-backoff-shape/v2` を exact pin し、その固定値と固定 spec digest から trial を導出しました。stem 比較と separator 分岐は削除済みです。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:3189)
- F3: report は `formal_runtime()` を呼ばず、`resolve_campaign_output_root("official")` のみ使用します。locked calibration の `env_tag`、`threads`、locked clocks による residual 検査は維持しました。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4343)
- F4: `_require_binary_path_policy()` を report return 後へ移し、policy 未設定の report 正例を追加しました。[実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/campaign/b10_backoff_shape_sweep.py:4378) [正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2866)

F5 の M1〜M8 主診断 test はすべて実在します。M8 は [test_report_lock_digest_rejects_recanonicalized_forged_locks](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2408-b10-lock-identity/orchestrator/tests/test_b10_backoff_shape_sweep.py:2653) です。

## テスト結果

関連 selector 9 nodeid、parametrize 展開後 11 case:

- `test_report_lock_identity_accepts_exact_pre_t733_real_snapshots` 3 case
- `test_report_lock_digest_rejects_recanonicalized_forged_locks`
- `test_report_lock_identity_rejects_paired_space_and_trial_drift`
- `test_report_lock_identity_rejects_recanonicalized_false_authority`
- `test_report_lock_identity_rejects_analysis_binding_drift`
- `test_report_lock_identity_rejects_locked_spec_drift`
- `test_run_formal_report_accepts_unset_binary_path_policy`
- `test_run_formal_report_reaches_locked_collection_and_writer_without_live_inputs`
- `test_report_collector_reads_only_three_formal_series_and_discloses_sources`

結果は `11 passed` です。

指定 plain runner:

```text
PYTHONPATH=. python3 orchestrator/tests/test_b10_backoff_shape_sweep.py
```

結果は `190 collected / 187 passed / 3 failed` でした。失敗は事前指定された非帰属赤だけです。

- `test_t1905_m2_job_root_passes_real_external_and_claim_capability_gates`: `/var/tmp` read-only
- `test_t1905_a5_non_forbidden_external_official_root_is_accepted`: `/var/tmp` read-only
- `test_t1905_a5_tmp_official_root_is_rejected_by_real_durable_policy`: `/tmp/.git` による repository 判定

`py_compile`、`git diff --check`、構造 AST pin も通過しています。現物への `--phase report` は未実走です。

## M8 変異確認

digest 値比較だけを一時的に外して実走し、その後復元しました。

- calibration を3 fixtureすべて同じ値へ改変: `_assert_report_lock_binding` が例外なく通過し、負例が赤。
- 実在する balanced authority を write-heavy へ交換: 同じく入口全体を通過し、負例が赤。
- `space_version` と `trial` の対改変: digest gate は通過しましたが、F2 の exact identity gateで拒否されました。負例は digest 固有メッセージを得られず赤。

したがって、3 型すべてが digest 防壁へ帰属することは確認できましたが、「3 型すべてが report 入口全体を通過する」という条件は、F2 の独立した exact 比較と両立しません。最終 M8 nodeid は digest 比較削除時に `1 failed`、復元後に `1 passed` でした。

## 静的波及

- `_assert_report_lock_binding` と `_collect_report_inputs` の所有外 production caller はありません。
- `run_formal` の CLI syntax、job argv、非 report 経路は不変です。binary policy は非 report で引き続き必須です。
- `test_ccbench_spawn_sites.py` の source 行 pinは `build_v2:3644`、`run_campaign:4460` のままです。同ファイルの変更は作業開始時から存在し、本 fix では触れていません。
- `test_official_perf_closure.py` は module membership、`test_campaign.py` は `run_campaign` call count、`test_condition_meaning_gate.py` は module importへの波及可能性がありますが、いずれも構造は不変で未実走です。
- `test_p3_build_authority_cli.py` と `materializer_admission.py` の `_compile_probe_harnesses` 登録は不変です。
- lock fixture の直接 consumer は対象 test fileだけです。3 fixtureの内容は未変更で、SHA-256 は裁定値と一致しています。
- `campaign_lock.py`、docs、保護対象の disclosure 本体と collector 内2行は未変更です。

## 既存テスト期待値

既存 assertion literal、期待 error code、skip条件は変更していません。

既存テストへの変更は次だけです。

- `_assert_report_lock_binding` callsiteへ `expected_lock_sha256` を追加。内側 gateの既存診断では再 canonical 化した candidate digestを渡し、従来の期待 codeを維持しています。
- report 到達 testの policy設定を `setenv` から明示的な未設定へ変更。
- report 到達 testの site/runtime/claim成功 stubを禁止呼出しへ変更し、`resolve_campaign_output_root("official")` の到達確認へ変更。
- 新規期待値はF1〜F4用テスト内だけです。

135 record digest literal、3 digest集合比較、fixture bytesは変更していません。

## 総括

F1〜F4 の実装所見は閉じました。残した問題は既知のsandbox起因3赤と、F1の対改変がF2でも拒否されるため「digest削除時に入口全体を通る」という説明が成立しない点です。

親が必ず確認すべき点は、M8の単一主診断 nodeid、上記F1/F2の防壁重複、fixture 3本の収載、所有外に残る既存 `test_ccbench_spawn_sites.py` 差分です。commit、branch操作、push、docs編集は行っていません。