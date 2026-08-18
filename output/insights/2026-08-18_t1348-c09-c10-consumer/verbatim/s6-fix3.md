## 総括

修正完了。

- [test_autonomous_trial_completeness.py:2806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/tests/test_autonomous_trial_completeness.py:2806) で、対象 fixture の WAL だけ `bench_wall_s` 欠損にした。
- Layer3 は欠損 WAL から通常生成するため、variant 被覆・digest 束縛を保ったまま bench ゲートへ到達する。
- 対象テストは [同ファイル:3132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/tests/test_autonomous_trial_completeness.py:3132)。monkeypatch は除去した。
- 期待メッセージは production 実装 [autonomous_trial_completeness.py:3138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1348-c09-c10-consumer/orchestrator/campaign/autonomous_trial_completeness.py:3138) と一致する。

追加の過剰決定候補は、同テストの `build_records` mutation（3183〜3185行）。variants 変更に対して `source_refs` が stale のまま。今回は未修正。pytest は親の測定に委譲し、`git diff --check` のみ通過。