## 総括

1. 衝突解決

[ p3_autonomous_workload_trial.py ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-epoch/orchestrator/campaign/p3_autonomous_workload_trial.py:1819) を次の合成にしました。

- `critic_digest_generated` は exact `bool` 必須。
- `True` の場合、digest は通常 file かつ非 symlink 必須。
- admission は `purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE` を明示。
- `False` の場合、同名の stale digest は読まない。

main の fail-closed 強化と、本 wave の epoch gate の両方を保存しています。

2. 合成監査

穴は2件で、いずれもテスト側の purpose 省略でした。

- [test_p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-epoch/orchestrator/tests/test_p3_autonomous_workload_trial.py:3779): `CERTIFIED_ACCEPTANCE` を追加。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t817-epoch/orchestrator/tests/test_campaign.py:8163): admission 状態だけを確認するため `HISTORICAL_RAW` を追加。

編集後の全件集計:

- `grep -rn --include='*.py'`: 104 textual hits。
- AST で確認した実呼び出し: 65件。
- production: 16/16件が purpose 明示。
- tests: 48/49件が purpose 明示。
- 残る省略1件は、purpose 必須を確認する意図的な `TypeError` 負例。

追加機構については、`autonomous_trial_completeness` は `CERTIFIED_ACCEPTANCE` を通過します。S8b の `VerifiedOracleVerdict` は `judge_oracle` 再導出により E1・`certified_eligible=True` を要求します。`s8c_generation_projection` は `scientific_claim=False` の探索用射影で、certified 出力を発行しません。揮発する working-tree/HEAD hash を固定期待値へ追加した箇所はゼロ件でした。

現行挙動は、基礎 admission 拒否を両 purpose で維持し、`CERTIFIED_ACCEPTANCE` は E0/E1-stale を拒否、`HISTORICAL_RAW` は epoch 診断付きで生値を保持します。受理集合の追加変更はありません。

3. 検査

指定された5ファイル走は実装済み・未実走です。

- pass: 0 nodeid
- fail: 0 nodeid
- collection/execution: 0 nodeid
- infrastructure error: 1件、`rc=16`
- 原因: Pegasus の `qstat -Q preflight rc=1`

単独ファイル走と collect-only も同じ `rc=16` でした。直接 pytest で runner の配置判断を迂回していません。`git diff --check` と全 Python ファイルの AST parse は成功しました。

4. 波及可能性

- `_pending_critics` を構築する caller/fixture は `critic_digest_generated` の exact bool が必須。
- digest がある certified critic 経路では、E0/E1-stale campaign が拒否される。
- stale digest は `critic_digest_generated=False` なら再利用されない。
- `require_admitted_campaign` を monkeypatch する fixture は `purpose` keyword を受け取る必要がある。
- S8b observations の epoch 証拠や manifest consumer 集合の変更は `VerifiedOracleVerdict` 再導出へ波及する。
- `docs/`、`output/`、`external/ccbench` は編集していません。

5. 残る不確実性

pytest が未実走のため、動的回帰は未確認です。また、指示どおり `git add` を行っていないため、marker は除去済みですが index 上は対象ファイルが `UU` のままです。merge の stage・確定と再テストは親作業が必要です。