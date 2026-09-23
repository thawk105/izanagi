## 変更

14 macro を [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847mr-uc/orchestrator/campaign/condition_meaning_gate.py:79) の供給・branch witness 登録に追加し、所有された 3 test の固定表を更新しました。patch 本文の `+#if <macro>` を数え直し、14 件すべてで申告された site 数と一致しました。

変更は登録、site 数、期待表、件数を示す docstring に限られます。既存の受理・拒否判定と供給経路の処理は変更していません。変更ファイルは指定の 4 件だけです。

## 検査結果

| 対象 | 結果 |
|---|---|
| `test_condition_meaning_gate.py` と `test_ccbench_spawn_sites.py` | **未実行**。passed 0 / failed 0 / skipped 0 |
| `test_p3_s4_loop.py -k "naked_izanagi_macro or registered"` | **未実行**。passed 0 / failed 0 / skipped 0 |
| 所有外の patch 全走査 `test_mocc_template_proof.py` | **未実行**。passed 0 / failed 0 / skipped 0 |

指定の直接 pytest は Pegasus ログインノードの hook に拒否されました。3 件とも `tools/run_tests.py` で再試行しましたが、`qstat -Q` 事前確認が rc=1 となり、**どの nodeid も起動していません**。対象には `test_patch_define_inventory_matches_condition_gate_registry`、`test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted`、branch 登録・site 数・domain 件数の各 test、および所有外の `test_mocc_mutation_surface_requires_auditor_live` と `test_mocc_template_gate_activation_controls` が含まれます。所有外へのテスト結果上の波及は、このため未判定です。

静的検査は Python 構文、`git diff --check`、`check_codex_agents.py`、`check_docs.py` が通過しました。gate を読み込んだ実数は define **57**、branch witness **39**、meaning **40** です。

## 総括

登録と固定表の更新は完了しました。pytest の合否は dispatch 障害により確認できておらず、緑とは報告しません。