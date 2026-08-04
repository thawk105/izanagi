H-1〜H-6 をすべて実装し、F2-01〜F2-06 は静的判定で全件 closed です。編集は許可された 3 ファイルのみで、docs 編集・commit・pytest 実行はしていません。

| 裁定 / 所見 | 判定 | 対応 |
|---|---|---|
| H-1 / F2-01 | closed | zombie を reap 前に取得し、fork 基準からの `lifetime_cpu_ticks` 全量を pin CPU へ帰属 |
| H-2 / F2-02 | closed | 開始 process→CPU、終了 CPU→process に固定。4 timestamp、端別 skew、`window_skew_ns` を記録 |
| H-3 / F2-03 | closed | CPU0 の過剰 self が CPU1 residual を相殺できない 2 CPU fixture を追加 |
| H-4 / F2-04 | closed | sham 1 tick 通過、既存 2 tick 拒否、busy 5 tick 通過・4 tick 拒否を literal で固定 |
| H-5 / F2-05 | closed | CPU key は exact `int`、MHz は exact `int/float` のみ許可。str/bool は validity reason へ |
| H-6 / F2-06 | closed | final mismatch は rc=4。wrapper.rc=4、done-marker 未発行、manifest も同契約に統一 |

変更ファイル:

- [t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.py)
- [t419_probe_causality.pbs](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/tools/pegasus/probes/t419_probe_causality.pbs)
- [test_t419_probe_causality.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/tests/test_t419_probe_causality.py)

追加テスト node（11件）:

- `test_execution_validity_rejects_coercible_vector_types_with_one_reason[string_cpu]`
- `test_execution_validity_rejects_coercible_vector_types_with_one_reason[bool_cpu]`
- `test_execution_validity_rejects_coercible_vector_types_with_one_reason[string_mhz]`
- `test_execution_validity_rejects_coercible_vector_types_with_one_reason[bool_mhz]`
- `test_sham_one_tick_inclusive_boundary_is_valid`
- `test_busy_five_tick_inclusive_boundary_is_valid`
- `test_busy_four_ticks_is_inconclusive`
- `test_completed_child_fork_to_reap_ticks_are_all_attributed`
- `test_isolation_residual_is_never_cancelled_across_cpus`
- `test_isolation_window_order_contains_cpu_window_and_records_skew`
- `test_final_binding_mismatch_returns_nonzero_and_has_no_done_marker`

既存テスト node の期待値変更は 0 件です。既存 `test_sham_above_one_tick_is_inconclusive` が sham 2 tick 拒否を引き続き固定します。

検査結果:

- `python3.10 -m py_compile`（driver・test）: rc=0
- `bash -n t419_probe_causality.pbs`: rc=0
- 純計算 `--self-test`: rc=0、17 fixture PASS
- pytest: 0件（Pegasus ログインノードのため未実行）

閾値 0.95 / 0.05 / 46 / 445、canonical band、`INVALID ⇒ NOT_EVALUATED` は不変です。

## 総括

- 集計: closed 6 / partial 0 / regressed 0（H/F の対応問題単位。ラベル単位では closed 12）。
- 残リスク: pytest・mutation matrix と、実 fork/zombie/reap の tick 挙動は未実測。
- 残リスク: final mismatch 時の PBS・manifest・wrapper.rc 統合経路は実ジョブ未確認。
- 親は計算ノードで全 pytest と mutation matrix を実行すること。
- 実機で非零 start tick、終了端 tick、4 timestamp、skew、CPU 別 residual を照合すること。
- final hash mismatch を強制し、非零 rc・wrapper.rc・done-marker 不在を確認すること。