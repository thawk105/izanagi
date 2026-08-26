## 総括

- 採用 A のみ実装し、Pegasus LOGIN の acceptance launcher に限って shard 数 `"3"` を注入しました。
- 既存指定、非 Pegasus、site 判定例外では環境を変更せず、従来の継承動作へ縮退します。
- 変更は production 1 file、test 1 fileだけです。
- pytest は計算ノード投入前に rc=16 となったため未実走です。

## 変更した file と関数

- [tools/dev_wave_wait.py:313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:313)
  - `_ACCEPTANCE_SHARDS_ENV`
  - `_PEGASUS_ACCEPTANCE_SHARDS`
- [tools/dev_wave_wait.py:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:817)
  - `_acceptance_launcher_environment`
- [tools/dev_wave_wait.py:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:834)
  - `_default_launch_launcher`
- [orchestrator/tests/test_dev_wave_wait.py:3266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/orchestrator/tests/test_dev_wave_wait.py:3266)
  - launcher 起動捕捉用の file-local helper と追加テスト

## 追加したテスト

- `orchestrator/tests/test_dev_wave_wait.py::test_pegasus_login_acceptance_launcher_adds_three_shards_only`
- `orchestrator/tests/test_dev_wave_wait.py::test_non_pegasus_acceptance_launcher_does_not_inject_shards`
- `orchestrator/tests/test_dev_wave_wait.py::test_acceptance_launcher_preserves_explicit_shard_request`
- `orchestrator/tests/test_dev_wave_wait.py::test_acceptance_launcher_site_error_keeps_inherited_environment`
- `orchestrator/tests/test_dev_wave_wait.py::test_acceptance_shards_are_not_injected_into_other_subprocess_paths`

## 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py`
  - runner rc=16、`qstat -Q preflight rc=1`
  - pytest child は未起動
  - 実走 0件、passed 0、failed 0、skipped 0
- grep で得た consumer 5 file の合同走行
  - runner rc=16、pytest child は未起動
  - 実走 0件、passed 0、failed 0、skipped 0
- 補助診断として追加した5関数を隔離して直接呼び出し、5件とも完了しました。pytest 緑には数えていません。
- 構文検査、結合文字検査、`git diff --check` は成功しました。
- 受入全走は投入していません。

## 現行の受理・拒否挙動と変更後の差分

現行は launcher が待ち手の `os.environ` をそのまま継承し、未指定の適格な Pegasus acceptance は `run_tests.py` が既定 K=2、非適格経路は K=1 と解決します。明示 K=2/3 は非適格 site で rc=16 となります。

変更後は、acceptance launcher 起動時に限り、Pegasus LOGIN、かつ呼び出し元が未指定の場合だけ `IZANAGI_ACCEPTANCE_SHARDS=3` を追加します。既存環境は全保持し、argv と `--env-projection-json` は変更しません。非 Pegasus、既存指定、判定例外では現行挙動のままです。受理集合、選択 node、恒久除外、保留適用には差分がありません。

## 波及可能性の静的列挙

- 所有外 caller:
  - [tools/dev_wave_wait.py:1559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:1559) の default effects 配線
  - [tools/dev_wave_wait.py:3796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t826-acceptance-closure-split/tools/dev_wave_wait.py:3796) の acceptance 起動境界
  - 他の production caller はありません。
- 共有 fixture:
  - `orchestrator/tests/conftest.py` は未変更です。
  - 追加 helper は `test_dev_wave_wait.py` 内だけで、既存 autouse signal fixture の期待値も変更していません。
- grep で得た consumer test:
  - `test_dev_wave_wait.py`
  - `test_check_docs.py`
  - `test_check_wave_startup.py`
  - `test_dev_wave_land.py`
  - `test_fold_gate_nodes_contract.py`
  - `test_resume_gate_acceptance_boundary.py`

## 破らなかったことの確認

- `tools/run_tests.py` は編集していません。
- `tools/acceptance_launcher.py` は編集していません。
- `orchestrator/tests/conftest.py` は編集していません。
- `tools/acceptance_shards.py` は編集していません。
- `docs/`、worklog、decisions、failures、handoff は編集していません。
- `git add`、`git commit` は実行していません。
- 既存テストの期待値変更、反転、緩和、skip、削除はしていません。
- collection、選択 node、恒久除外、保留適用は変更していません。
- 新しい環境変数、CLI flag、設定 file は追加していません。既存の `IZANAGI_ACCEPTANCE_SHARDS` だけを使用しています。
- Web 検索は使用していません。