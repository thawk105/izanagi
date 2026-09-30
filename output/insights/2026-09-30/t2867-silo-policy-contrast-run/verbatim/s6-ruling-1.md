# [T-2867] 本走 wave 段 6 裁定 1 (親、2026-09-30 12:4x JST)

対象: review `codex/s6-review-1/out.md` (NO-GO、must-fix 4)。

| # | 裁定 | 処置 |
|---|---|---|
| 1 stale pid の排他 | real (must-fix) | runner の生存期間中 `runner-state/runner.lock` に `fcntl.flock(LOCK_EX|LOCK_NB)` を保持し、取れなければ rc=2。pid file は記録用に残す |
| 2 親起動と state 保存の窓 | real (窓は極小、fail-closed で直す) | `Popen` の前に `item['parent'] = {'pid': None, 'a': a, 'starting': True, ...}` を保存し、成功後に pid を入れて `starting` を外して保存。再起動時 (`Runner.__init__`) に `starting` の親があれば attention `parent-start-unknown` (自動で起こし直さない) |
| 3 init・submit と state 保存の窓 | real (同上) | 起動器の `init`・`submit` の直前に `item['intent'] = {'action', 'ts'}` を保存し、結果を反映した保存で消す。再起動時に `intent` が残っていれば attention `intent-unknown` |
| 4 qstat の遅延表示 | real (must-fix) | job の不在は「投入から 120 秒以上経過」かつ「連続 2 回の成功した qstat で不在」でだけ確定する (`item['job_missing']` の計数を state に持つ)。在れば計数を 0 に戻す |
| 5 写しの試験の台帳参照 | 既知・処置済み (試験は実装子の木の元の位置で走らせ、写しとの bytes 一致を記録した) | 変えない |
| 6 停止後の init | real (should-fix) | `open_series` の各 init の直前に `STOP` と `pause` を確かめて止める |
| 7 本走 config の checkout 不在 | 作成中 (コードの所見ではない) | 変えない |
| 8 deque | nit | 変えない |

state の新しい key (`intent`・`job_missing`、親の `starting`) は、既存の state file を読んだとき欠けていれば既定値 (None・0・False) とする (走行中の前走の state を新版で読み直すため)。
既存の 7 試験の期待値は変えない。1・2・3・4・6 それぞれに試験を 1 本ずつ足す。
