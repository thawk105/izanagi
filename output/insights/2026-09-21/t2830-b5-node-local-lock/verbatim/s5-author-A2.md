1. **変更前の挙動**
   `main` は単一の`--repo-root`を検証し、`launch` は4 jobすべてを同じ`SubmitTree`・`cwd=tree.repo`で投入していました。CCBench・build cacheも共有される構造でした。

2. **変更したファイルと箇所**
   - [b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2/tools/pegasus/b5_contrast_launch.py:218): `launch`でarm別treeをcommandごとに保持し、envとcwdに使用。`main`（246行）は4必須引数を受け、`PILOT_ARMS`順に共通HEADで検証します。冒頭docstringも更新しました。
   - [test_b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2/orchestrator/tests/test_b5_contrast_launch.py:95): `_pilot`・期待envを4 tree化。argv完全一致（133行）、submit時の全4件のcwd・env一致（223行）、CLIの検証順・出力（248行）、既存の拒否・freshness検査を追従させました。

3. **静的検査**
   - `python3 - <<'PY' … PY`：両ファイルを`compile(source, path, 'exec')`で構文検査し、変更禁止の定義・validator test・fixture・自走harnessをHEADとのAST比較で確認。**rc=0**。ファイル生成なし。
   - `git diff --check`：**rc=0**。
   - `git status --short`：**rc=0**。変更は所有2ファイルのみ。

4. **meta-testと影響**
   `test_plain_runner_coverage.py`の自走harness・allowlist検査を静的確認しました。test関数の新設・改名はなく、`_run`と`__main__`も維持しています。出力先検査のparameterは`submit-tree`から`submit-tree-random`へ追従しています。

5. **所有外への波及**
   - `tools/pegasus/README.md:478`：旧`--repo-root`例は親による更新が必要です。
   - `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes`：path・登録分類は不変です。
   - 過去の`submit_pilot.py.txt:47`は旧APIの記録として保持しました。新APIで再利用する場合はarm→tree mappingが必要です。
   - 共有fixtureへの変更はありません。単一treeのvalidator fixtureも維持しています。

6. **実装済み・未実走**
   テスト・変異実走・commitは行っていません。親の焦点走候補は`orchestrator/tests/test_b5_contrast_launch.py`全体、特に以下です。

   - `::test_four_qsub_argv_and_explicit_environment_are_exact`
   - `::test_submit_only_mkdir_then_argv_runner[0]`／`[9]`
   - `::test_main_dry_run_validates_tree_and_prints_four_jobs`
   - `::test_dry_run_prints_final_argv_without_runner_or_mkdir`
   - `::test_preexisting_attempt_rejected_before_any_submission`

   README更新後は`test_p3_s4_loop_job_contract.py::test_readme_tagged_qsub_fence_routes_both_streams_to_evidence`、登録簿・plain-runnerの上記meta-testも候補です。

## 総括

A2を所有2ファイルに実装済み・未実走です。既存の検証順序を維持し、追加の拒否条件・互換層は導入していません。