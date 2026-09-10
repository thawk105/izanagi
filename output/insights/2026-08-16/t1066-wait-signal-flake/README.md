# [T-1066] 実 signal 族フレークの変異台帳と一次証拠 (2026-08-16)

wave `dev-wave-t1066-wait-signal-flake` の段 6 変異検査の生台帳。
判断・訂正の本文は worklog エントリと F306 の supersede 行が正本で、ここは数値だけを置く。

## 走行

固定 commit `f2a6688d` に対し `tools/mutation_worktree.py` の使い捨て worktree で実行。
runner は `python3 tools/run_tests.py orchestrator/tests/test_dev_wave_wait.py -rf --force-dispatch`
(`--runner-mode dispatch`)。

**F306 の恒久対応「変異検査では族を含む file を runner 範囲から外す」を退役させ、
`orchestrator/tests/test_dev_wave_wait.py` を runner 範囲へ戻して走らせた。**

| file | 内容 |
|---|---|
| `mutation-spec-probe.json` | 1 巡目 (probe)。期待 node は親の予想 |
| `mutation-spec-final.json` | 2 巡目。期待 node を 1 巡目の実測完全集合へ再登録 |
| `mutation-ledger-final.json` | 2 巡目の生台帳 |

## 結果

- **2 巡目: 8 件すべて `KILLED`。`SURVIVED` 0、`MISMATCH` 0、`PARSE_ERROR` 0、`TIMEOUT` 0。**
- baseline は `PASSED` / `rc=0` / 失敗 node 0 件 / 262.354 秒。
- 1 巡目は 5 件 `KILLED`、3 件 (M5 / M6 / M8) が `MISMATCH` だった。
  **実測の失敗集合は親の予想より広く、実 signal・実 subprocess の node
  (`test_public_main_real_signal_releases_lease`,
  `test_public_main_real_signal_after_success_uses_restored_handler`) が
  3 件の変異を検出していた。** 段 3 のレンズ B が疑った「実 subprocess node の検出力」への
  実測回答である。`DW-M08` に従い 1 巡目を probe と明記し、完全集合へ再登録して 2 巡目を走らせた。

## 反復安定性の副産物

2 巡目の 1 走行で `orchestrator/tests/test_dev_wave_wait.py` を **9 回** (baseline 1 + 変異 8)
走らせ、**8 回の変異走行すべてで失敗 node 集合が期待と完全一致した**。
= 期待外のフレークが 1 件も出ていない。

## 記録しない主張

`_SIGNAL_WATCHDOG_SECONDS` を 0.0 にして落ちる node は無い。**handshake の待機部分は
単独で kill 可能な変異を持たない。** 待機に検出力を持たせるには「signal が待機開始より後に
届く」ことを保証する必要があり、それ自体が scheduler 依存になるため採らなかった。
**恒真な kill を捏造しないため、diagnostic sensitivity pin としても登録していない。**
真因を閉じているのは汚染源の修正・autouse guard・production の mask 復元であって待機ではない。
