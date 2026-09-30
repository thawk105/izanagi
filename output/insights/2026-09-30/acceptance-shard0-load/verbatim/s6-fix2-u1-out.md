F4 を [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/conftest.py:2562) と [test_s8b_oracle_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/as0-u1/orchestrator/tests/test_s8b_oracle_driver.py:1311) に実装しました。prewarm は `result.json` を 180 秒で打ち切らず、finish が立てる停止 event まで待ちます。T2 を改訂し、写し公開前に停止する新テストを追加しました。T4 は期待値を維持し、builder の終了を待つ同期だけ足しました。commit はしていません。

| 場面 | 変更前 | 変更後 |
|---|---|---|
| 写しが遅い・未公開 | 180 秒で例外 | finish 時に停止し、builder を呼ばず静かに終了 |
| 写しが `ok: false` | prewarm も例外 | prewarm は静かに終了。写しの失敗は既存の snapshot finish が送出 |
| 写しが `ok: true` | 2 key を構築 | 停止前に開始できれば従来どおり構築 |
| builder 例外 | errors に記録し finish で送出 | 同じ |
| join 超過 | 生存 thread があれば木と lock を保持して例外 | 同じ。finish は先に停止 event を立てる |
| 起動失敗 | 上限付き後始末後、起動例外を送出 | 同じ停止 event を使って後始末 |

**検査:** AST 解析と `git diff --check` は通過しました。新設 2 テストと指定の `-k 't080_shared_base or t080_visible_output'` 範囲をそれぞれ `python3 tools/run_tests.py` 経由で試みましたが、どちらも `qstat -Q preflight rc=1` により dispatch が `rc=16` で失敗しました。子プロセスは起動しておらず、両範囲とも**実装済み・未実走**です。

**変異の静的照合:** M1、M3、M4、M5、M6 の置換元は対象コード内で各 1 箇所です。旧 M2 の「180 秒 deadline」逐語は 0 箇所で、新しい停止 event 付き待機は 1 箇所です。期待 node は M1→T1、M3→T3、M4→T4、再照準した M5′→T5、M6→E7 の 3 node の見込みです。M2 は T2 に加え、新しい停止前テストも競合次第で検出しうるため、**T2 だけ**とは静的には断定できません。M4 は T4 だけの見込みです。いずれも変異実走による確認は残ります。

## 総括

F4 の修正は指定の 2 ファイルに収め、commit はしていません。
テストランナーの dispatch 障害により、テストと変異の実走結果はありません。