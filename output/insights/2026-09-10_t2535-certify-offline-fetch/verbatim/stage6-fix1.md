## 総括

X1〜X5 はすべて `closed`。3 ファイルを変更し、M8〜M10 は変異注入で実際に赤になることを確認しました。docs・`submit_certify.sh`・walltime 式・timeout 値は変更せず、commit/stage も行っていません。

## 所見対応表 (X1-X5 を closed / partial / regressed で)

| 所見 | 状態 | 対応 |
|---|---|---|
| X1 | closed | verifier 専用 Python 3.10 resolverを追加。未解決時は `interpreter` で rc=2 |
| X2 | closed | production の `run_condition_gate` を実行し、外部 `python3 -m ...` stub が実 argv を記録 |
| X3 | closed | production の configure 起動行を実行し、stub `timeout` が完全な argv を記録 |
| X4 | closed | consumer test の fixture に三依存の staging layout を追加。assert は不変 |
| X5 | closed | ignored artifact を三依存で検査、regular-file child を追加、staging tree 全ファイルの bytes を比較 |

## 変更した file と行

- [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-fix1/tools/pegasus/certify_calibration.sh:556): verifier resolver。実呼出しは 591 行。
- [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-fix1/orchestrator/tests/test_pegasus_calibration_workload.py:116): production gate fixture、configure use-site、interpreter 正負例、X5 fixture 強化。
- [test_pegasus_tools.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2535-fix1/orchestrator/tests/test_pegasus_tools.py:1643): X4 staging fixture。
- `tools/pegasus/submit_certify.sh` は変更なし。

## 変異 M1-M10 をどのテストが殺すか

| 変異 | 殺すテスト |
|---|---|
| M1 | `test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols` |
| M2 | `test_certify_offline_configure_resolves_three_local_sources_and_fails_without_each` |
| M3 | `test_certify_job_rejects_a_staging_source_with_ignored_artifacts` |
| M4 | `test_certify_offline_fetchcontent_contract_is_identical_for_all_protocols`、offline configure 正例 |
| M5 | `test_certify_condition_gate_receives_the_same_fetchcontent_tokens` |
| M6 | `test_certify_offline_configure_resolves_three_local_sources_and_fails_without_each` |
| M7 | `test_submitter_rejects_a_missing_or_malformed_third_party_staging_root` |
| M8 | `test_certify_condition_gate_receives_the_same_fetchcontent_tokens` |
| M9 | `test_certify_configure_use_site_passes_the_complete_configure_argv` |
| M10 | `test_certify_third_party_verifier_uses_version_checked_interpreter` |

M8・M9・M10 は一時的な in-memory source 変異を注入し、3 件とも `KILLED` を確認しました。

## 実走した検査 (nodeid と範囲)

`PYTHONPATH=. /usr/bin/python3.10` の自走 harness で、31 の test case 本体を実行しました。

- X1: `test_certify_third_party_verifier_uses_version_checked_interpreter`、`test_certify_third_party_verifier_interpreter_resolution_fails_closed`
- X2/X3: `test_certify_condition_gate_receives_the_same_fetchcontent_tokens`、`test_certify_configure_use_site_passes_the_complete_configure_argv`
- X4: `test_submit_dry_run_does_not_resolve_cluster_commands`
- X5: copy 全 tree 比較、malformed staging、ignored artifact `[masstree|mimalloc|googletest]`
- 実 CMake: `test_certify_offline_configure_resolves_three_local_sources_and_fails_without_each` の正例・4 負例・coupled control
- 共有 helper 回帰範囲: protocol define/target/binary の全 protocol、non-silo 2 protocol、offline contract、既定 silo argv
- 近傍既存検査: calibrator interpreter 正負例、CMake path、glog stage、PBS policy
- shell 構文: `test_calibration_shell_scripts_parse`
- `git diff --check`: 成功

## 実装済み・未実走

- pytest runner は環境 hook に起動前拒否されたため、pytest の緑は主張しません。
- 両 test file の全 pytest collection は未実走です。
- 計算ノード上の certification job、configure/build、本番 verifier は指示どおり未投入です。
- M1〜M7 の変異注入再走は未実施です。対応 test 本体は上記範囲で実走済みです。

## 既存テストへの影響

- X4 の既存 assert は一切変更していません。
- skip・削除・期待値の反転／緩和はありません。
- production gate を使うよう共有 helper を強化した後も、その既存 consumer 群は自走 harness で通過しました。
- 変更は3ファイルとも unstaged で、commit はありません。

## 未解決

X1〜X5 内の未解決事項はありません。敵対レビューの scope 外所見と、公式 pytest／計算ノード実走は未変更・未実走のままです。