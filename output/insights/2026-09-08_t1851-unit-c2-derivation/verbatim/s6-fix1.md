## 旧 test が主張していたこと

全 341 combination で、改訂前後の `exec_failures`、`rep_integrity_failures`、qualified throughputs がすべて一致すると誤って主張していました。

## 新 test が固定すること (変わらない量 / 変わる量)

[test_s8b_floor_stats.py:311](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c2-s2/orchestrator/tests/test_s8b_floor_stats.py:311) を characterization test へ変更しました。

- `exec_failures` は exact に一致。
- qualified throughputs は exact に一致。
- `session_median` による有効性判定と median は exact に一致。
- `rep_integrity_failures` は `post_spawn_execution_exception` の本数だけ増加。
- post-spawn がない combination では integrity failure 数も一致。
- pre-spawn exception は旧実装でも integrity failure だったため増分には含みません。

## 網羅した outcome class の一覧

perf 無効時、3 rep の 5 クラス直積、125 combination:

- `success`
- `nonzero_rc`
- `pre_spawn_execution_exception`
- `post_spawn_execution_exception`
- `nonfinite`

perf 有効時は次を追加した6クラス直積、216 combination:

- `counter_missing`

合計 341 combination です。

## 実走した関数と結果

`test_formula_v2_preserves_session_outputs_but_counts_post_spawn_integrity_failures`

結果: PASS、rc=0。

対象 file には `__main__` 自走 harness がないため、file 単独実走はしていません。作業 root の一時 script から関数を直接 import して呼び出しました。

## 残した一時 file (無ければ「無し」)

無し

## 総括

偽の全量不変テストを、session 結果の不変性と post-spawn integrity failure の exact な増分を同時に固定するテストへ修正しました。production、docs、output は変更せず、git も実行していません。