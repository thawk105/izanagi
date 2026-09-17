## 所見別の対応表

closed は修正完了を示します。pytest による確認は基盤障害で未実走です。

| 所見 | 対応 | file:line |
|---|---|---|
| A1 | closed | `tools/cleanup_remove_dirs.py:218` |
| A2 | closed | `tools/cleanup_remove_dirs.py:103,118,221` |
| A3-B-01 | closed | `tools/cleanup_remove_dirs.py:8,249,269` |
| A4 | closed | `orchestrator/tests/test_cleanup_remove_dirs.py:61,71,101` |
| B-02 | closed | `orchestrator/tests/test_cleanup_remove_dirs.py:215` |
| B-03 | closed | `orchestrator/tests/test_cleanup_remove_dirs.py:303` |

## 変更差分の要点

- timeout 検出時に対象子の取消を記録し、取消待機から戻った直後に全体 signal を確認。
- TERM/KILL 両段の待機に中断 callable を追加。fault 経路は既定動作を維持。
- summary 確定前に TERM/INT/HUP を `SIG_DFL` へ復帰。終了 status の優先と JSON 不完全の可能性を明記。
- 同期失敗の PID・proc 状態診断、起動例外時の chmod 復旧、summary 負例 3 ケースを追加。

既存期待値・待機期限・`summarize()` は変更していません。

## 実走結果

| command | 結果 | 所要秒 |
|---|---|---:|
| `python3 tools/run_tests.py orchestrator/tests/test_cleanup_remove_dirs.py -rf -q` | rc16、pytest 未実走 | 0.173 |
| `python3 tools/check_docs.py` | passed、rc0、違反なし | 未計測 |
| `git diff --check` | passed、rc0 | 未計測 |

テスト起動失敗理由は `qstat -Q preflight rc=1`、`child_started=false`。実走 nodeid はなく、passed／failed／skipped 件数は未取得です。修正した両ファイルの AST parse は成功しました。

## 変異 anchor の再照準

**(i)〜(x) はすべて出現回数 1 回**です。以下は空白と末尾改行を保持する Python 文字列表記です。

```python
# (i) line 208
'                    stdout=current.stdout, stderr=current.stderr)\n'
# (ii) line 210
'                if current.pgid != os.getpgrp():\n'
# (iii) line 145
'        status, reason = "interrupted", "cancelled or signal exit"\n'
# (iv) line 128
'    absent = False\n    error = child.error\n'
# (v) line 146
'    elif rc > 0 or not absent:\n'
# (vi) line 84
'            if os.path.commonpath([path, other]) in {path, other}:\n'
# (vii) line 80
'        if os.path.commonpath([path, cwd]) == path:\n'
# (viii) line 185
'    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):\n'
# (ix) line 106
'    for sig, grace in ((signum, TERM_GRACE_SECONDS),\n                       (signal.SIGKILL, KILL_GRACE_SECONDS)):\n'
# (x) line 218
'                if expired and not cancelled:\n                    for child in expired:\n                        child.cancelled = True\n                    cancel(expired, signal.SIGTERM, interrupted=lambda: cancelled)\n'
```

## 波及の静的列挙

- cleanup command §3 の launcher 呼出しに、timeout 競合修正と取消応答の変更が反映されます。
- JSON consumer は process exit status を優先する契約です。
- `_wait_until` の全呼出しに診断用 children を渡しました。共有 fixture は未変更です。
- docs・pin・他ソースは編集していません。runner が失敗 receipt を自動生成しました。
- 変異 M8 は新 anchor (x) への再照準が必要です。M2 の for 文は維持されています。

## 総括

指定 2 ファイルで全 6 件を修正しました。
文書検査・構文検査は成功し、anchor は各 1 回です。
pytest は dispatch 障害で未実走のため、受入確認は未完了です。
commit・git add は行っていません。
