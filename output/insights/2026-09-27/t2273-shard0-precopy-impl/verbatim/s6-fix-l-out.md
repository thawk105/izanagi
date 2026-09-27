## 変更

- [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/conftest.py:2538): join と削除の例外を個別に保持し、保存済みの生成エラーを最優先で伝播するようにしました。
- [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-impl/orchestrator/tests/test_s8b_oracle_driver.py:1135): T1 で同じ `config`・`testrunuid` を持つ別々の node から本物の hook を呼びます。実関数 spy の1回検査を維持し、signature に file mode を加えました。

## 実走

**実装済み・未実走。** `python3 tools/run_tests.py` による T1 の焦点走は `qstat -Q` の dispatch 前確認で失敗し、pytest は起動していません（rc=16）。両ファイルの `py_compile` と `git diff --check` は成功しました。

## 変異の置換表

以下の各 old は、対象 file 内でそれぞれ **1件**と静的に確認しました。T1 は `test_t080_visible_output_snapshot_starts_once_and_preserves_copy`、T2 は `test_t080_shared_base_builds_real_builder_once_across_processes` です。

| ID | file | old → new | kill node と assert |
|---|---|---|---|
| P0 | test_s8b_oracle_driver.py | `one point at configure_node` → `single point at configure_node` | 等価変異。SURVIVED |
| M1 | test_s8b_oracle_driver.py | `_t080_copy_visible_output(root / "output")` → `_copy_git_visible_output(ROOT, root / "output")` | T2: helper 呼出し回数と builder 呼出し回数の一致 |
| M2 | test_s8b_oracle_driver.py | `shutil.copytree(directory / "output", destination)` → `_copy_git_visible_output(ROOT, destination)` | T1: source 変更後の `signature(second) == signature(expected)` |
| M3 | test_s8b_oracle_driver.py | `shutil.copytree(directory / "output", destination)` → `shutil.copytree(directory / "output", destination, copy_function=shutil.copy)` | T1: signature の mtime 一致 |
| M4 / E1 | conftest.py | `if getattr(config, _T080_VISIBLE_OUTPUT_JOB_ATTR, None) is not None:\n        return` → 空文字列、かつ `directory.mkdir(exist_ok=False)` → `directory.mkdir(exist_ok=True)` | T1: 別々の2 node 呼出し後の `copy_visible.assert_called_once_with(...)` |
| M5 | conftest.py | `module._copy_git_visible_output(module.ROOT, directory / "output")` → `shutil.copytree(module.ROOT / "output", directory / "output")` | T1: `copy_visible.assert_called_once_with(...)` |
| M6 / E2 | conftest.py | `_start_early_memo_job(node)\n        _start_t080_visible_output_snapshot(node)` → `_start_early_memo_job(node)` | T1: helper 呼出し前の `result.json` 読取り |
| M7 | conftest.py | `shutil.rmtree(job["directory"])` → `pass` | T1: `assert not snapshot.exists()` |

## 総括

B1・A1・A2だけを変更し、既存テストの期待値は変更していません。変異の置換位置と想定する単一の kill 理由は静的に確認しました。実走結果の確認は親の harness に委ねます。commit は作成していません。