| 変異 | 分類 | 何を変えると | 期待 | 結果 | 落ちた node 数 (代表) | 備考 |
|---|---|---|---|---|---|---|
| m0-control-docstring-only | 対照 | docstring の 1 文に「(対照)」 | SURVIVED | SURVIVED | 0 (—) | 等価変異、harness の SURVIVED 検出の正例 |
| m1-child-delete-uses-lowercase-d | 正例 | 子専用 -D を -d へ | KILLED | KILLED | 7 (test_remove_child_already_clean_with_receipt ほか 6) | 非祖先の子は -d が拒否され rc=30 |
| m2-child-delete-call-skipped | 正例 | 子 branch 削除の呼出しを省略 | KILLED | KILLED | 9 (test_remove_child_archives_dirty_integrated_author_and_deletes_branch ほか 8) | ref 不在 assertion が落ちる |
| m3-history-bundle-skipped | 正例 | 履歴 bundle の作成を省略 | KILLED | KILLED | 3 (test_remove_child_archives_dirty_integrated_author_and_deletes_branch ほか 2) | 正例の bundle 実在検査と verify 失敗 fixture が注入点に到達しない |
| m4-integration-rejection-disabled | 負例 | integration 不一致の拒否を無効化 | KILLED | KILLED | 2 (test_remove_child_rejects_unintegrated_author_commit ほか 1) | 未統合の子が受理される |
| m5-wave-delete-uses-force | 負例 | wave 本体の削除を -D へ | KILLED | KILLED | 27 (test_forbidden_git_verbs_absent_from_source_calls_and_runtime_allowlist ほか 26) | 共通 runner が -D を拒否し wave 経路が全て失敗 = 正常受理の縮小の検出 (安全境界の突破証明ではない) |
| m6-common-runner-accepts-force | 負例 | 共通 runner の -D 拒否を除去 | KILLED | KILLED | 1 (test_common_git_runner_rejects_force_delete) | 共通 runner の実効 gate |
| m7-bundle-failure-ignored | 負例 | bundle create/verify の失敗を無視 | KILLED | KILLED | 1 (test_remove_child_bundle_verify_failure_is_partial[verify]) | [verify] が主証拠。[create] は後続の directory 読込み失敗に mask され証拠から外す |
| m8-branch-delete-phase-mislabeled | 診断 pin | branch 削除 phase 名を postcondition へ | KILLED | KILLED | 1 (test_remove_child_branch_delete_failure_is_partial) | diagnostic sensitivity pin (kill 数に入れない) |
| m9-receipt-reappearance-check-removed | 負例 | receipt 再実行時の branch 再出現検査を除去 | KILLED | KILLED | 1 (test_remove_child_receipt_rejects_recreated_branch) | 再出現 branch が already-clean に流れる |
| m8b-branch-delete-fail-open-cumulative | 負例 (累積 4 置換) | 削除 rc 無視 + 診断 malformed 無視 + sha 照合無視 + 不在確認無視 | KILLED | KILLED | 1 (test_remove_child_branch_delete_failure_is_partial) | 4 層が独立に守るため単独置換では殺されない (RB-6)。DW-M04 の累積適用 |

final: baseline PASSED (27.004 秒/run、201 passed)、KILLED 10 / SURVIVED 1 / MISMATCH 0 (期待 node 完全一致 11/11)。repo_head `cdc5ddb59`、spec sha256 `f60590a1e030…`、runner = `tools/run_tests.py orchestrator/tests/test_dev_wave_cleanup.py -q -rf --force-dispatch` (dispatch)。probe (M0〜M9、02:33〜02:45、head `c82f42da7`) と probe2 (M8b、02:46〜02:48) で観測した node を final に固定。kill に数えるのは M1〜M7・M9・M8b の 9 件、M8 は診断 pin。
