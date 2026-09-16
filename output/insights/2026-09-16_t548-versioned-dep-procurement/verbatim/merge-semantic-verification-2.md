## 総括

**編集0件・検証のみ。** 4 file で wave/main 双方の変更が両立し、指定5本は**257件すべて成功**しました。重複定義・fixture の衝突・shell 段の順序破壊は見つかりませんでした。HEAD・index は変更していません。

| file | wave 側が生きている根拠 | main 側が生きている根拠 |
|---|---|---|
| `b4_binary_record.py` | [66行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/campaign/b4_binary_record.py:66)：hydrate後にgflags/glogをbuild。関数ASTもwaveと一致 | [149行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/campaign/b4_binary_record.py:149)：repo相対位置への配置。配置・CLI関数ASTはmainと一致 |
| `test_b4_binary_record.py` | [194行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/tests/test_b4_binary_record.py:194)：hydrate先行・7呼出し・source pathを検査 | [308行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/tests/test_b4_binary_record.py:308)：配置path・bytes・実行権限を検査。配置テスト9件が残存 |
| `test_pegasus_tools.py` | [529行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/tests/test_pegasus_tools.py:529)：15 jobの解決順序とmoccのhydrate契約 | [445行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/tests/test_pegasus_tools.py:445)：SIGKILLによるprobe_error fixture。[476行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/orchestrator/tests/test_pegasus_tools.py:476)：候補全滅時の3分岐 |
| `certify_calibration.sh` | [155行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/tools/pegasus/certify_calibration.sh:155)：staging rootから依存を解決。perf配列開始位置も9に整合 | [907行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t548-merge-verify/tools/pegasus/certify_calibration.sh:907)：選択成功時だけshimを作成。候補全滅後もcanonical probeへ進み、probe_errorは停止 |

台帳は実測と一致し、修正不要でした。`prepare_dependencies` のsubprocess起動箇所は**1**、`build_v2` は**118行目**。台帳の917行・2716行もともに**118**です。

全て `PYTHONPATH=. python3 orchestrator/tests/<file>` で、**file全体・全parameter caseを実走**しました。

| file | 成功件数 | rc |
|---|---:|---:|
| `test_b4_binary_record.py` | 30 | 0 |
| `test_pegasus_tools.py` | 72 | 0 |
| `test_ccbench_spawn_sites.py` | 47 | 0 |
| `test_pegasus_thirdparty_fetch.py` | 105 | 0 |
| `test_plain_runner_coverage.py` | 3 | 0 |

実走nodeidのうち、merge境界を直接確認したもの（接頭辞は `orchestrator/tests/`）：

- `test_b4_binary_record.py::test_dependency_commands_use_verified_and_hydrated_paths`
- `test_b4_binary_record.py::test_place_cli_success_and_failure`
- `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench`
- `test_pegasus_tools.py::test_perf_stage_all_candidates_failed_uses_canonical_receipt[probe_error]`（`available`・`unavailable`も成功）
- `test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
- `test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`

mergeの噛み合わせ以外に新たに発見した問題：**なし**。今回の検証範囲は現物レビューと指定harnessであり、実機の認証job全走ではありません。