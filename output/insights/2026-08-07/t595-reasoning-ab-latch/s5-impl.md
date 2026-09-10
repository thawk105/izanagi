変更前は reasoning effort の検査がなく、現行文書・S02/S03 の `max→high`・値削除をすべて受理していました。変更後は現行文書を受理しつつ、DW-S02/DW-S03 の各節で `` `reasoning=max` `` が exact 1 件でない場合だけ、節別の D207 finding で拒否します。DW-S05 の `reasoning=high` は検査対象外です。

実装内容:

- [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:264)
  - 節別 literal・finding 定数を追加。
  - `_reference_id_sections()` を使った独立 pin 検査を追加。
  - finding に「引き下げは D207 の A/B 未充足のため不可」を明記。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4766)
  - 実物正例、S02-high、S03-high、S02-value削除を追加。
  - 負例は一時ディレクトリへ実物をコピーし、tracked file を変更しません。
  - finding 期待値は `check_docs` の定数を参照します。

追加 nodeid:

- `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pins_accept_current_workers_contract`
- `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_rejects_dw_s02_high`
- `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_rejects_dw_s03_high`
- `orchestrator/tests/test_check_docs.py::test_dev_wave_reasoning_effort_pin_rejects_missing_dw_s02_value`

関連 meta-test として以下も実行対象に指定しました。

- `orchestrator/tests/test_check_docs.py::test_command_docs_guard_positive_controls`
- `orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted`

ただし `tools/run_tests.py` は admission 台帳を sandbox 内から更新できず compute dispatch に移行し、`qstat -Q preflight rc=1`、最終 rc=16 となりました。上記 node は収集・実走とも未了で、緑とは申告しません。

実走済み:

- `python3 tools/check_docs.py`: rc=0、`check_docs: 違反なし`
- `python3 tools/check_codex_agents.py`: rc=0
- AST parse、`git diff --check`: 成功
- 検査関数への軽量 probe: 現行正例・S02-high・S03-high・S02削除の4ケース成功

所有外への静的波及は、`main()` → `_check_command_docs_guard()` の caller、`_build_min_repo()` が共有する合成 workers fixture、および同 fixture を使う `test_check_docs.py` の consumer testsです。新しい private 検査関数の外部 caller は追加テスト以外にありません。

## 総括

- 変更: `tools/check_docs.py`、`orchestrator/tests/test_check_docs.py` の2ファイルのみ。
- 追加検査: DW-S02/DW-S03 の `reasoning=max` を節別に exact pin。
- 追加テスト: 正例1 node、独立負例3 node。
- 実走成功: `check_docs` rc=0、`check_codex_agents`、AST、diff check、4ケース probe。
- pytest: 新規4 node＋関連meta-test 2 nodeは基盤rc=16のため実装済み・未実走。
- docs編集、git add、commitはいずれも実施していません。