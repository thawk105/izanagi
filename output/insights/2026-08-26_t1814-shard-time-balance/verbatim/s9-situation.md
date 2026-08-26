# 相談事項 — 受入全走で `test_dev_wave_cleanup.py` が毎回 1 件落ちる

wave `dev-wave-t1814-shard-time-balance` (実装差分ゼロ、docs のみ) の段 9 で止まっている。
決めたいのは「この file を受入全走でどう扱うか」の 1 点だけである。

## 観測

受入全走を 2 走した。どちらも `1 failed / 17097 passed / 62 skipped`。

| 走 | 落ちた node | 本文 |
|---|---|---|
| 1 走目 | `test_forward_merged_landing_tip_is_used_for_cleanup[asserted]` | `dev-wave-cleanup: status=rejected phase=occupancy reason=occupancy result is indeterminate or inconsistent; attempts=1 retry_count=0` (rc=22) |
| 2 走目 | `test_reentry_states_run_only_remaining_cleanup[b]` | 同上・逐語一致 |

- **落ちた node は走ごとに違う。** 本文は逐語一致。
- 同 file の単独走は **94 passed / 3.93 秒 / rc=0** で非再現。
- 本 wave の差分は `docs/spool/**` と `output/insights/**` だけで、
  `tools/check_worktree_occupancy.py` や `tools/dev_wave_cleanup.py` へ到達する経路は無い。
- 受入は Pegasus の計算ノードへ dispatch され、K=2 の shard 分割で各 shard 48 worker が走る。
  占有検査は当該計算ノードの `/proc` 全体を走査する。全走中は短命 process が大量に生滅する。

## 脆弱な node の実測 (本文書の親が数えた)

`test_dev_wave_cleanup.py` は 94 node を収集する。そのうち
**「占有検査が成功して rc=0 を返すこと」を前提にする正例は 15 node** である
(`_assert_success_output` を呼ぶ 7 関数の展開)。観測された赤 2 件はどちらもこの 15 の中にある。

```
test_accepts_arbitrary_same_uid_unreachable_process_with_diagnostics
test_accepts_nonblocking_occupancy_diagnostics[cwd-deleted]
test_accepts_nonblocking_occupancy_diagnostics[cwd-permission]
test_accepts_nonblocking_occupancy_diagnostics[same-uid-cwd]
test_forward_merged_landing_tip_is_used_for_cleanup[asserted]
test_forward_merged_landing_tip_is_used_for_cleanup[derived]
test_git_argv_spy_sees_only_allowlisted_cleanup_commands
test_landed_attached_worktree_is_removed[locked]
test_landed_attached_worktree_is_removed[unlocked]
test_reentry_states_run_only_remaining_cleanup[a]
test_reentry_states_run_only_remaining_cleanup[b]
test_reentry_states_run_only_remaining_cleanup[c]
test_reentry_states_run_only_remaining_cleanup[d]
test_reentry_states_run_only_remaining_cleanup[e]
test_retries_disappeared_pid_issue_then_removes
```

## 履歴 (materials/F489.md が逐語)

- 2026-08-24: 同型が出て、**ユーザー直接裁定**で `orchestrator/test_selection_contract.py` の
  `SANCTIONED_EXCLUSIONS` へ **file 単位の一時除外**を入れた。解除条件は
  「`dev-wave-cleanup-occupancy-churn` task が land し、明示 file 走が全緑」。
- 2026-08-25: `[T-1623]` が占有検査を修理して land し (D793)、除外を空集合へ戻した。
  現在 `SANCTIONED_EXCLUSIONS = ()` である。
- 2026-08-26 (今): 修理後に再発した。落ちる node が動く点が今回の新しい観測である。

## 決めたい 3 択

- **(a) file 単位の一時除外を戻す。** `SANCTIONED_EXCLUSIONS` へ 2026-08-24 と同じ形で
  `test_dev_wave_cleanup.py` を入れる。受入から 94 node が消える。
- **(b) class 単位の hold を作る。** `orchestrator/tests/flaky_test_holds.py` へ上記 15 node を
  登録する。受入から 15 node が消え、79 node は残る。
  ただし現行 registry は node ごとに「赤の実測」を要求する形で、
  実測で赤を見たのは 2 node だけである。
- **(c) 占有検査を計算ノードの process churn に依らない形へ作り替える。**
  `[T-1623]` の続き。実装量は不明。

## 制約

- `DW-O18`: 受入の受理は `child-green` だけ。非帰属の赤でも受領証は作られず land できない。
  再赤は「main 既存の F を証拠に Codex `role=author` が `flaky_test_holds.py` へ登録」または
  「F 不在なら裁定へ送り停止」と定める。
- 絶対規律 2: 正しさゲートを緩める変更を性能や利便のために採らない。
- 除外・hold はどちらも受入の受理集合を変える。
- 本 wave 自身は docs のみの wave で、この件とは無関係の結論
  (shard 割付を duration 重みへ変えない) を既に出して commit してある。
