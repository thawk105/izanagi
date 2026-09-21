## 総括

**実装済み・未実走です。** 変更は所有内の次の 4 ファイルだけです。git add / commit、docs 編集、pytest 実行は行っていません。

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a2/orchestrator/campaign/p3_s4_loop.py): pair mode、候補と stock の context／checkout 分離、session 転送、例外後の stock 試行、rc 集約を実装。
- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a2/tools/pegasus/p3_s4_loop_pegasus.sh): proposal＋stock を driver 1 起動へ変更。fixture＋stock は prebuild／trap 前に拒否。
- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a2/orchestrator/tests/test_p3_s4_loop.py): CLI 正負例、実 Pegasus 認可・claim・reservation・pipeline・WAL の結合検査を追加。
- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795r-unit-a2/orchestrator/tests/test_p3_s4_loop_job_contract.py): 起動数 3→2、pair argv、driver rc 透過、fixture pair 拒否へ契約検査を更新。

受理が増えるのは、必要な isolation と候補 authority を伴う `--run-iteration P --stock-control` の pair mode 組合せです。拒否が増えるのは、job body の fixture＋`IZANAGI_S4_STOCK_CONTROL=1` です。

**確認済み:** Python／shell 構文検査、`git diff --check`、NFC。既定 argv テストと公開 `run_one_iteration` の AST、読取専用 4 ファイルの HEAD bytes は不変です。layout 呼出し 11、`run_campaign` 呼出し 2、import 閉包 49、B-4 の直接呼出しと条件を維持したため、inventory pin は変更していません。

以下は変異を検出する設計上の対応であり、**KILLED の実測結果ではありません**。

| 新設・改名 test 名 | 変異 ID |
|---|---|
| `test_pair_cli_rejects_conflicts_before_layout_or_claim` | M12 |
| `test_pair_cli_requires_candidate_opt_in` | M13 |
| `test_pair_cli_requires_isolation` | 補助検査 |
| `test_pair_cli_separates_context_checkout_and_session` | M14、M15、M17 |
| `test_pair_cli_candidate_exception_still_attempts_stock` | M16 |
| `test_pair_cli_stock_exception_preserves_candidate_status` | M17 補助 |
| `test_pair_cli_base_exception_does_not_attempt_stock` | 補助検査 |
| `test_pair_cli_policy_mismatch_precedes_checkout` | 補助検査 |
| `test_pair_session_forwarding_at_campaign_calls` | M18（静的検査） |
| `test_pair_main_pegasus_real_claim_and_wal` | C1、C2、C3 |
| `test_pair_main_quarantine_reject_stock_acquires_first_claim` | 未束縛 session の補助検査 |
| `test_pair_main_authorized_candidate_exception_stock_reuses_claim` | M16 の結合補助検査 |
| `test_pair_job_invokes_one_driver_with_both_modes` | M19 |
| `test_pair_job_propagates_driver_status` | M19 補助 |
| `test_fixture_pair_refuses_before_prebuild_and_trap` | M20 |
| `test_pair_job_has_no_shell_stock_aggregation` | M19 |

M21 は既存の `test_default_job_invokes_driver_once` が担当し、期待値は変更していません。旧 run-iteration 排他 case は、新しい pair 正例へ置き換えました。

静的に確認した波及は次のとおりです。

- B-5 の `slot_argv` と `test_slot_argv_literal_contract` は変更不要。stock 単独口を維持しています。
- 他 driver、共有 fixture、`loop.py`、`campaign_claim.py`、`test_campaign.py` は未変更。新しい subprocess は追加していません。
- 親による `tools/pegasus/README.md` §7、`docs/phase3.md`、F1019、修復 insight／関連導線の更新が必要です。
- 実 compiler の STOCK 成立、実 checkout／patch と build の統合、Pegasus production pair は未確認です。

**親の判断・後続作業:** 統合 commit 後の結合検査と変異検査が必要です。H 群 M18 は lock を作らない静的転送検査とし、両 `run_campaign` に同一 session が届く実処理委譲 spy は結合正例へ置きました。この区分で exact node 集合を確定してください。closure 検査・resumability の回避は追加していません。