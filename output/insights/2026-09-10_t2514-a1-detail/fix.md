## 総括

**実装済み・未実走です。** [test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2514-a1-detail-author/orchestrator/tests/test_ccbench_spawn_sites.py:903) の指定2リテラル（903行・2670行）だけを `7209→7268` に更新しました。実在する `run_campaign` の位置と一致し、`git diff --check` は通過しました。

assert・集合要素・scope/kind/owner・受理拒否の判定内容は変更していません。元拒否の `PaperStoryError` 保持と `admission=True` の成功経路にも変更はありません。T-2417の別probe行、実装本体、docs、fixture/hashには触れず、git add・commitも行っていません。

波及確認対象は以下です。

- consumer：同ファイルのledger照合、`_deferred_member` を使うsink被覆検査。
- meta-test：`test_plain_runner_coverage.py`、`test_real_repo_serialization.py` のcollection一致検査、`test_growth_test_holds_contract.py` のfixture consumer検査、`test_pytest_collection_config.py`。

テスト実走は親に委ねます。no-touch manifestの既知の赤は未修正で、親commit後の再走対象です。