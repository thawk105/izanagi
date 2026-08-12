## 変更したファイルと差分の要約 (file:line)

- [tools/collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/tools/collect_wave_usage.py:38)
  - `--help` epilog に、先頭 dash slug は `--project=<slug>` で指定する要件と rc 契約を追加。
  - `_collector_argv()` の全値付き option を等号 1 token 形へ統一。option 順序と `--project` の反復順は維持。
  - artifact を publish した後、`complete=0`、確証済み login の `blocked=3`、suspect の `blocked` とその他 status／未知 status を `1` に写像。
  - 外側 argparse の `SystemExit(0/2)` をそれぞれ rc 0/2、通常例外を rc 1へ変更。`KeyboardInterrupt` は非捕捉のまま。

- [orchestrator/tests/test_collect_wave_usage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_collect_wave_usage.py:161)
  - 全内側 argv の完全一致、先頭 dash slug の正例、全 status/site の artifact-first rc 契約、login/suspect 分離を追加。
  - help 契約、外側 split dash slug の拒否、未知 status の fail-closed も固定。
  - create-only、schema、artifact 内容、collector 呼出し回数 0、正例 `test_output_below_empty_git_directory_is_accepted` は弱めていない。

## 現行の受理・拒否挙動 → 変更後の受理・拒否挙動

現行は、外側の通常 slug split 形を受理し、先頭 dash slug の split 形を拒否する一方、等号形は外側で受理していた。しかし内側へ再び split 形で渡すため、実 slugが内側 argparse で拒否され、`error` artifact と rc 0になっていた。全 status、外側 argparse 拒否、通常例外も rc 0へ潰していた。

変更後も外側の受理集合は変えない。通常 split 形は従来どおり受理し、先頭 dash slug の split 形は rc 2で拒否、`--project=-work-1-SFC-tanab-izanagi` は受理する。内側では全値 option が等号形になり、slug がそのまま collector に1回届く。blocked 時の collector 呼出し 0、artifact-first、create-only、5 status schema は維持する。

## 実走した nodeid と結果 (走らせられない場合はその旨)

実装済み・未実走。pytest が実際に開始した nodeid は 0 件で、緑とは申告しない。

リポジトリ規律に従い、直接 pytest ではなく以下を試行した。

- `python3 tools/run_tests.py orchestrator/tests/test_collect_wave_usage.py -q`：2回とも rc=16
- 同ファイルの `--collect-only`：rc=16
- meta-test 候補 `orchestrator/tests/test_pytest_collection_config.py`：rc=16

すべて `Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1` で停止し、pytest 本体は未起動だった。`queue_state` も ENA／STS を観測不能と報告した。静的には `git diff --check`、AST parse、NFC 検査が成功した。

## 既存テストで期待値を変えたもの (node 名と、なぜ段 4 裁定の範囲内か)

rc 期待だけを裁定表へ合わせた。

- `test_zero_model_calls_is_missing_not_complete`
- `test_zero_model_calls_is_missing_before_incomplete_reasons`
- `test_limit_reached_is_incomplete`
- `test_issues_make_a_nonzero_collection_incomplete`
- `test_collector_exception_is_error_but_main_returns_one`（旧 `returns_zero`）
- `test_existing_output_is_not_overwritten_and_leaves_no_temporary_artifact`
- `test_unclassified_site_is_blocked_without_calling_collector`
- `test_collector_site_classification_fails_closed_without_evidence`
- `test_missing_project_never_falls_back_to_all_projects`
- `test_output_must_be_absolute`
- `test_output_below_any_git_marker_is_rejected`
- `test_process_returns_two_when_required_arguments_are_missing`（旧 `returns_zero`）
- `test_process_returns_one_when_project_is_missing`（旧 `returns_zero`）
- `test_process_returns_one_when_output_is_inside_repo`（旧 `returns_zero`）
- `test_process_returns_one_and_records_nonzero_collector_exit_code`（旧 `returns_zero`）
- `test_missing_output_parent_is_not_created`

これらは段 4 裁定 §3 が明示した rc 写像だけの変更であり、artifact、保存先、schema、呼出し回数などの期待は維持した。

## 所有外への波及可能性 (caller / 共有 fixture / consumer test の静的列挙)

- caller：`docs/dev-wave/core.md` の段 9 が本 helper を呼ぶ。rc 0前提の外部 supervisor が存在すれば、今後は rc 1/2/3を区別する必要がある。
- 契約文書：親所有の `docs/README.md` は help と同じ外側等号形／rc 契約へ同期する必要がある。
- 共有 fixture：該当なし。変更した `_report`、`_argv`、subprocess helper は当該テストファイル内限定。
- consumer test：直接 consumer は当該テストファイルのみ。`docs/failures.md` が名指す `test_output_below_empty_git_directory_is_accepted` は改名せず、rc 0と collector 1回を維持した。
- meta-test：専用 nodeid 固定 test は静的検索で見つからず、関連候補は `test_pytest_collection_config.py`。ただし上記理由で未実走。

## 総括

所有された2ファイルだけを変更し、内側 argv の等号1 token化、先頭 dash slug の到達保証、artifact-firstの fail-closed rc契約、helpの外側CLI契約を実装した。外側 argv正規化、docs、caller、共有 fixture、他単位のファイル、git index／commitには触れていない。静的検査は完了しているが、Pegasus dispatch基盤の preflight失敗により指定 pytestとmeta-testは実装済み・未実走である。