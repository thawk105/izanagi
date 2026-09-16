## 変更点 (file:line)

[test_t2630_scan_boundary_reach.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2630-scan-boundary-reach-probe/orchestrator/tests/test_t2630_scan_boundary_reach.py)

- 392・398・404・409 行: 全 4 関数に `_detect_site_under_test` 引数を追加。
- 288 行: `environment.json` に `site_policy.current_site()` の返り値を追加。既存の hostname 記録と併存。
- compiler 呼び出し・期待値は変更なし。

## 自己検査の結果

- `python3 -m py_compile`: 成功。
- collect-only: 指定の全 4 node を収集、終了コード 0。
- `git diff --check`: 成功。

runner 経由の収集は qstat 事前確認で rc=16。実装契約の `pytest.main` 経由で収集を確認しました。

## 実走していないこと

baseline・計算ノードでの実走は未実施です。4 node の合格は未確認です。

## 総括

ソース変更は probe 1 ファイルのみです。commit・push・`.diff`／`.patch` ファイル作成は行っていません。