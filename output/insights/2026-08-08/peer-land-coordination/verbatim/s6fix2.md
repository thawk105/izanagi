4 件とも `closed` として実装しました。commit は作成していません。

- F-1 — `closed`
  - `O_NONBLOCK`、regular file・実効 UID の事前検査、`LOCK_NB` の最大 8 回 retry を実装しました。
  - [tools/wave_land_window.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:198)
  - [orchestrator/tests/test_wave_land_window.py:379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:379)

- F-2 — `closed`
  - policy TTL を固定 2400 秒とし、payload TTL を age 判定に使用しません。
  - malformed・oversize・型偽装・上限超過 lease も、mtime が stale なら dev/ino 再照合後に回収します。2400 秒超の future mtime も stale 扱いです。
  - [tools/wave_land_window.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:27)
  - [tools/wave_land_window.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:293)
  - [orchestrator/tests/test_wave_land_window.py:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:229)

- F-3 — `closed`
  - winner は `acquired` のまま維持し、`status` の `free` が lease 不在だけを表すことを独立テストで固定しました。
  - [tools/wave_land_window.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:290)
  - [orchestrator/tests/test_wave_land_window.py:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:170)

- F-4 — `closed`
  - MX5 の外側 open failure と内側 listdir failure を分離しました。
  - MX7 は `stale-main`、`lock-busy`、`rejected`、`fold-failed` と非文字列を検査します。
  - 両 SHA field で 39・40・41 桁、大文字、非 hex を独立検査します。
  - [orchestrator/tests/test_wave_land_window.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:334)
  - [orchestrator/tests/test_wave_land_window.py:595](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:595)
  - [orchestrator/tests/test_wave_land_window.py:694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:694)
  - [orchestrator/tests/test_wave_land_window.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:892)

受理集合は、従来の任意の正整数 `--ttl` から `1..2400` に縮小しました。`2401` 以上は rc=2 です。受理した値が 2400 未満でも、実効 TTL と保存 payload は固定 2400 秒になります。

対象テストは `tools/run_tests.py` から 2 回起動しましたが、いずれも `qstat -Q preflight rc=1` による dispatch infrastructure `rc=16` で停止しました。実走 nodeid はありません。AST 構文検査のみ成功しています。

fencing token、release capability nonce、manager transaction wrapper、docs、receiver 契約には触れていません。

## 総括

- F-1〜F-4 はすべて実装上 `closed`。
- 変更対象は指定された production と test の 2 ファイルだけ。
- TTL 受理上限は 2400 秒。
- 対象 pytest は dispatch 不能のため実装済み・未実走。
- 親の変更前 `25 passed` を今回の緑とは主張しない。
- commit は作成していない。