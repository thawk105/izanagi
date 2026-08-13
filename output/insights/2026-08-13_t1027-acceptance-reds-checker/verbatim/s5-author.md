## 現行挙動と scope

変更前は、green または全 rerun rc=1 を rc=0、rerun rc=0 を含む赤を rc=1、入力・環境異常を rc=2 としていました。一方、collection は relay の部分出力を完全と見なし、rerun rc=1 の内容を検証していませんでした。

三値契約は維持し、裁定された完全 receipt、footer 文法、singular・deselected のみ受理します。証明不能な rc=0 経路は rc=2 へ閉じました。

## R1〜R9 の変更

- R1: dispatch collection/rerun のみ timeout を 4200 秒へ変更。git 等は 120 秒を維持。[check_acceptance_reds.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:25)
- R2: 非 relay の一意な保存行から receipt を特定し、location、v2 schema、request args、child outcome、accounting、stdout pathを検証。[check_acceptance_reds.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:183)
- R3: footer の selected 件数、deselection 算術、unique nodeid 件数を検査。欠落、複数、未知、重複、0 件を拒否。[check_acceptance_reds.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:830)
- R4: 検証済み nonce directory と exact fallback receipt のみ `finally` で除去。失敗は rc=2。[check_acceptance_reds.py:359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:359)
- R5: rerun rc=1 は、その selector の FAILED/ERROR と完全な pytest summary が確認できた場合だけ非帰属化。[check_acceptance_reds.py:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:870)
- R6: collection/rerun で `PYTEST_ADDOPTS` を空にし、選択へ影響する pytest 環境変数を除去。[check_acceptance_reds.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:650)
- R7: footer 欠落を default production runner 経由で固定。[test_check_acceptance_reds.py:1332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:1332)
- R8: receipt tail とローカル stdout の U+FFFD を拒否。[check_acceptance_reds.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:343)
- R9: checker receipt の `collections` に receipt path、nonce、request ID、stdout SHA-256 を記録。[check_acceptance_reds.py:1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/tools/check_acceptance_reds.py:1435)

既存 fixture には 7 件 footer を追加しました。[test_check_acceptance_reds.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1027-acceptance-reds-checker/orchestrator/tests/test_check_acceptance_reds.py:60)  
`test_ignored_artifact_from_node_fails_closed` は無変更です。

## 新設テスト nodeid

M0〜M8:

- `test_truncated_relay_uses_complete_dispatch_receipt`
- `test_collection_footer_count_mismatch_fails_closed_before_rerun`
- `test_dispatch_receipt_with_omitted_scheduler_stdout_fails_closed`
- `test_dispatch_receipt_size_mismatch_fails_closed`
- `test_dispatch_collection_receipt_requires_bound_request_args`
- `test_dispatch_receipt_outside_probe_root_fails_closed_before_rerun`
- `test_single_test_collection_footer_is_accepted`
- `test_rerun_rc_one_without_matching_outcome_fails_closed`
- `test_dispatch_commands_use_dispatch_aware_timeout`
- `test_collection_environment_neutralizes_pytest_addopts`

追加契約:

- `test_truncated_relay_without_receipt_fails_closed_before_rerun`
- `test_dispatch_collection_receipt_requires_v2_child_outcome`（3 cases）
- `test_dispatch_receipt_replacement_character_fails_closed`
- `test_collection_footer_missing_fails_closed_on_production_path`
- `test_deselected_collection_footer_uses_selected_count`
- `test_zero_or_all_deselected_collection_fails_closed`（3 cases）
- `test_default_dispatched_rerun_removes_verified_dispatch_artifacts`
- `test_collection_duplicate_or_invalid_footer_fails_closed`（4 cases）
- `test_each_logged_path_has_an_independent_complete_collection_gate`
- `test_injected_collection_failure_cannot_reach_rerun_or_status`
- `test_checker_receipt_records_collection_provenance`

制約 meta-test を検索しましたが、この test file や node 集合を列挙する外部テストはありませんでした。

## 実走結果

指定の焦点走を 2 回試行しましたが、いずれもテスト開始前に失敗しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
returncode=16
```

したがって全焦点 nodeid は実装済み・未実走で、緑とは申告しません。

実施済みの静的検査:

- AST parse、module import、`git diff --check`: 成功
- footer と rerun 証拠 parser の smoke: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功
- 変更ファイルは指定された 2 ファイルのみ

## 残った赤

テスト assertion の赤は未観測です。残っているのは焦点走 2 回の dispatch infrastructure rc=16であり、テスト本体は未実行です。

## 波及可能性

- 所有外 producer: `tools/run_tests.py` の argv 正規化と `tools/pegasus/dispatch_compute.py` の v2 receipt schemaに依存します。
- 共有 fixture: `committed_repo` の collect 出力へ footer を追加したため、この fixture を使う既存テスト全体に完全性 gate が適用されます。
- consumer: checker receipt に `collections` が増えました。現時点で repo 内に当該 schemaの外部 consumer、`dev_wave_wait.py` / `dev_wave_land.py` からの caller は見つかりませんでした。
- 将来 caller は exact rc=0、`status=non-attributable-only`、log hash 束縛を同時検査する必要があります。

## 総括

R1〜R9 と M0〜M8、裁定と整合する追加テストを指定 2 ファイル内へ実装しました。  
判定不能な collection・selector・rerun から rc=0 を出す経路は rc=2 へ閉じています。  
静的検査と正本 checker は成功しました。  
焦点 pytest はキュー基盤 rc=16 のため未実走で、closed／緑とは申告しません。