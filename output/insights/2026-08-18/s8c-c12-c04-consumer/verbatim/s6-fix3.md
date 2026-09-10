## 修正

- `p3_autonomous_workload_trial.py:3463` に Python 3.10 用 `__notes__` fallback を追加。
- `conftest.py:97` の予約時間を 7200 秒へ変更。
- `test_p3_autonomous_workload_trial.py:6183` で各回の `run_root` を mutable box から観測。

## 恒真化していないことの確認

- 負の対照は既存の3 nodeid（job-id、boot-id、remaining-time）で、各々 `ReservationError`、launch 未到達、root 未生成を要求する。
- 補助 probe で3条件すべての拒否を確認。正例は残時間 `7139.989 > 3600`。
- Python 3.10 probe で元例外の `__notes__` に `restart-forbid=OSError` と `terminal-record=OSError` が載ることを確認。

## 実走

pytest は未実走。`tools/run_tests.py` は `qstat -Q` の `EACCTAUTH` により dispatch infrastructure failure、rc=16。本体未到達。AST解析と `git diff --check` は成功。

## 停止・未達

pytestの実走結果だけ未達。docs編集・commitは行っていない。

## 総括

3件すべて独立に実装した。  
note握り潰しを互換fallbackへ置換した。  
予約fixtureは有効な残時間を持つ形へ修正した。  
重複起動テストは各rootを正しく観測する。