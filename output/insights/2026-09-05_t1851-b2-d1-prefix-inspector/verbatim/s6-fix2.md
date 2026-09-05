方針 1 で修正しました。

- [test_s8b_floor_stats.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-fix1/orchestrator/tests/test_s8b_floor_stats.py:1084) のみ変更: `+44/-2`、net `+42` 行。
- 世代 B を固有の campaign identity `run-b` で予約・消費する helper を追加。
- A/B の claim が同じ directory に実在し、別 identity であることを assert。
- 指定された `shared_admission_root(repo_a) == shared_admission_root(linked)` を維持。
- production API で両方の v2 registry proof を生成し、A/A の `[]` 受理正例も維持。
- attempt registry inspector は monkeypatch していません。
- production、他 test、docs は変更せず、commit もしていません。

検査は `AST OK`、`git diff --check` 成功です。単独 node の実走は `qstat -Q` preflight の infrastructure failureで `rc=16`、`child_started=false` となり、pytest child が開始されませんでした。

## 総括

- 方針: 1、世代 B に固有 campaign identity を付与。
- 変更: `test_s8b_floor_stats.py` のみ、`+44/-2`。
- 同一 root の A/B 実在 assert: あり。
- 実走: 実装済み・未実走、Pegasus dispatch infrastructure failure。
- production 変更・commit: なし。