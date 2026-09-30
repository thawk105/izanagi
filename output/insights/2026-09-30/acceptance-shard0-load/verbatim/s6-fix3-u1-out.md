[_t080_publish_visible_result](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/test_s8b_oracle_driver.py:1271) を修正し、JSON を `result.json.pending` に書いてから `replace` で原子的に公開するようにしました。テストの期待値と名前は変更していません。`git diff --check` は通過しました。

## 総括

- T2 と `-k "t080_shared_base or t080_visible_output"` を、それぞれ `python3 tools/run_tests.py` 経由で試みました。
- 両方とも Pegasus の `qstat -Q` 事前確認失敗（`rc=16`）で子プロセスが起動せず、**実装済み・未実走**です。実走できたテストはありません。
- 変異 M1〜M6 の置換元である `conftest.py` と `_t080_stub_free_e2e_repo` には触れていません。commit も作成していません。