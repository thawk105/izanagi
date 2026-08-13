## 総括

1. [test_dev_wave_wait.py:1876](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1876)  
   `dangling-symlink-probe-root` の期待 stage を `acceptance-receipt-preflight` に修正しました。

2. [test_dev_wave_wait.py:1889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t907-recovery/orchestrator/tests/test_dev_wave_wait.py:1889)  
   `/receipts` 外の log fixture を使い、log preflight 後に probe root が dangling となる分離 case を追加しました。`acceptance-red-check-preflight`、rc 2、claim 未実行を固定します。

3. 検査結果:
   - `python3 -m py_compile orchestrator/tests/test_dev_wave_wait.py`: 成功
   - `git diff --check`: 成功
   - テスト実走: 未実施

4. 裁定外の判断:
   - `probe_root` は常に `log_file.parent` のため、fixture は log preflight 時には健在、probe 時には dangling となる状態遷移を表現しました。

指定ファイル以外は編集せず、commit もしていません。実装済み・未実走です。