## 総括

T-513 の exact 比較化を実装しました。変更は3ファイルのみで、docs・共有 parser・禁止対象ファイルは編集していません。commit / git 操作も行っていません。

- [axis_trigger_gating.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/axis_trigger_gating.py:26)
  - `PREDICATE_HOLE_INDENT = "  "` を追加。
- [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:74)
  - parser は hole 行番号の特定だけに使用。
  - binary で再読し、物理行 payload を `b"  " + emit_predicate(...)` と exact 比較。
  - CRLF/CR-only の `\r` を payload に残して拒否。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5324)
  - 既存 fixture 2箇所を `render_hole` 由来へ修正。
  - 攻撃形6本と一意な BEGIN/END 閉区間による drift テストを追加。

変更・追加した9 nodeid:

1. `test_trigger_predicate_hole_indent_matches_template_patch_bytes`
2. `test_trigger_binding_rejects_materialized_predicate_with_outer_spaces`
3. `test_trigger_binding_rejects_materialized_predicate_with_leading_tab`
4. `test_trigger_binding_rejects_materialized_predicate_with_trailing_space`
5. `test_trigger_binding_rejects_materialized_predicate_with_four_space_indent`
6. `test_trigger_binding_rejects_materialized_predicate_with_crlf_line_ending`
7. `test_trigger_binding_rejects_materialized_predicate_with_cr_only_line_ending`
8. `test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds`
9. `test_trigger_binding_rejects_crossed_materialized_predicate_and_mask`

実走結果:

- 実際にテスト本体へ到達した nodeid: **0件**
- 上記9 nodeidと制約 meta-test 3 nodeidを `tools/run_tests.py` で投入しましたが、計算ノード dispatch の `qstat -Q` preflight が失敗し、rc=16で停止しました。
- `--collect-only` 再試行も同じ rc=16でした。
- ログインノード側は安全予約後の空きが約0.83–1.03 GiBで、runner の最低1 GiBを安定して満たさなかったため直接実行していません。
- したがって全12 nodeidは**実装済み・未実走**です。親の全走も未実走です。
- 静的構文検査は3変更ファイルすべて成功し、AST上で9 nodeidの定義を確認済みです。
- docs 未 land 由来の期待赤は、この限定範囲では事前指定なしです。

受理集合は、従来の `.strip()` 同値集合から、binding付き laneにおける単一raw payloadへ縮小しました。mask不一致等の既存拒否は維持し、新たに受理する形はありません。例外文言も不変です。

波及候補は**9エントリ**です（所有外caller 2、共有fixture 2、consumer-test群5）。主な対象は `loop.run_campaign`、trigger driver、`_source_evidence`、`_mock_pipeline`、`test_p3_build_authority_cli.py`、`test_p3_s4_loop_trigger_gating.py`、`test_p3_s4_loop.py`、`test_p3_autonomous_workload_trial.py`、`test_s1_direct_comparison.py`です。最後のbinding省略経路はA-7としてscope外のままです。