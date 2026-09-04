---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-04
wave: worktree-dev-wave-t2262-floor-staged-transport
seq: 1
---

## 新規

### {{F:runner-hangs-after-pytest-completes}}. 焦点走の runner が pytest 完走後の後処理で 23 時間ハングし、`.done` 待ちの待ち手が永遠に返らなかった [セッション死・救出] [手順漏れ]

- 事象: `python3 tools/run_tests.py orchestrator/tests/test_pegasus_floor_tools.py -q` を
  login node で起動した。pytest 自体は完走し、log には失敗 digest まで完全に出力されていた
  (`IZANAGI_FAILURE_DIGEST_ACCOUNT failures=5 ...` と `=== IZANAGI FAILURE DIGEST v1 END ===`)。
  しかし runner process は終了せず `.done` file も書かれなかった。
  `ps -o etime,stat,wchan` の実測は `23:14:17 SNl futex_wait_queue_me` で、
  `pgrep -P <pid>` は 0 件、子 process を持たないまま futex で待っていた。
- 影響: `.done` の実在で完了を判定する待ち手は返らない。
  **log には結果が全部出ているのに wave は止まったままになる。**
  親は「まだ走っている」と誤認し、待たずに次の走行を重ねて同一 worktree からの並行 dispatch を招き、
  `queue-wait-timeout` の rc=16 と孤児 hold を発生させた。
- 根本原因: 未特定。同じ夜の同じ login node で `floor_job_checkpoint` の時間制限つき操作を使う
  テスト 5 件も落ちており、単独再走では 7 passed (rc=0) で再現しなかった。実行環境側の要因を疑う。
  runner のどの段で futex を待っていたかまでは特定していない。
- 恒久対応: `docs/dev-wave/core.md` の `DW-C00` が定める「完了は `.done` 非空で決める」に、
  親側の生死判定を足す — 待ちが長いときは `.done` の不在を稼働中と読まず、
  `ps -o etime,stat,wchan <pid>` と `pgrep -P <pid>` を実測する。
  pytest の結果行が log に出ているのに `.done` が無い状態はハングであり、親が止めて
  `git status` で作業ツリーの復元を確認してから先へ進む。
  同時に `DW-O26` の「同一 worktree からの dispatch は全種を直列にする」を守り、
  待ち手が返る前に次の走行を投入しない。
- 再発検知: 孤児 hold の発生そのものが検知になる。
  `output/pegasus-dispatch/orphan-hold.json` が立ったら、直前に完了を待たずに投入した走行が
  無かったかを必ず遡って確認する。
