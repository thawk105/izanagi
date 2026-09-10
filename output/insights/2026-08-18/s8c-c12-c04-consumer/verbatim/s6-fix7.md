## 修正

- [orchestrator/tests/test_p3_autonomous_workload_trial.py:2095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-s8c-c12-c04-c11/orchestrator/tests/test_p3_autonomous_workload_trial.py:2095)
- 新設 nodeid: `test_run_trial_reservation_rejects_when_remaining_time_is_less_than_max_wall`
- production、共有 fixture、docs は未変更。commit も未実施。

## 検出力

予約期限まで約 1800 秒、`max_wall_s=3600` のため、現行 `required_s=max_wall_s` は `ReservationError` になる。変異で `required_s=1` にすると `1 < 約1800` なので予約検査を通過し、provider または campaign の poison が発火して `pytest.raises(ReservationError)` が赤くなる。

## 実走

- 新設 nodeid: 1 passed
- 既存 3 拒否対照: 3 passed
- `-k reservation`: 7 passed
- `python3 tools/check_codex_agents.py`: passed
- `python3 tools/check_docs.py`: 違反なし
- 初回 Pegasus dispatch は `qstat` 認証失敗で child 未実行。local runner 経由で再実走済み。

## 停止・未達

`required_s=1` 変異そのものの再走は未実施。親の実測結果と、残時間約 1800 秒対要求 1 秒の差で検出可能性を固定した。

## 総括

新しい残時間不足の負の対照を 1 件追加した。  
`max_wall_s=3600` と約 1800 秒の予約期限を使用した。  
provider/campaign の launch 前拒否も assert している。  
コード・テスト以外の変更と commit はない。