## 変更の要約

指定の **5 file だけ**を変更しました。**stock の admission に仕様衝突が残り、完了には至っていません。**

1. **同 job pair**
   - `p3_s4_loop.py`: stock CLI・排他、独立した評価関数、適応枝用 condition gate、非 STOCK 成功拒否、skip の rc=1、digest 更新を実装。
   - `p3_s4_loop_pegasus.sh`: stock env、manifest 転送、候補失敗後の stock 起動、候補非零優先の rc 集約を実装。
   - digest 更新は `_refresh_critic_digest()` に共通化し、既存 AST 検査の期待値を維持しました。
2. **較正 CLI**
   - `calibrated_perf()`、較正二口、動作点の identity 束縛を実装。
3. **exact correctness**
   - verify opt-in を既存 loop／pipeline へ接続。production の `pipeline.py`／`loop.py` は変更していません。

commit・stage・新規 file 作成・job dir への書込みは行っていません。

## 既定挙動不変の確認

変更前の扱い：

- `--value -1`: 候補値域で拒否。build 時は authority 検査が先行。
- `--stock-control`: 未知 option。
- `--calibrated-perf`: 未知 option。

確認結果：

- `default_cfg()`、`default_perf()`、`_assert_coder_value_domain()`、`_resolve_duplicate()` は変更前と **bytes 一致**。
- 候補の `_require_condition_gate(sub, genome)` を逐語で維持。
- 変更前 preimage を文字列定数として固定し、実 CLI と照合。
- fixture／proposal／K2 の既定 argv を実 shell で exact 照合。
- 既存 CLI golden・既存 pin の期待値は維持。許可された TJ の呼出し数・stage-order・helper consumer のみ更新。
- 受容済みの差として、`--v` は新 option により曖昧になります。

## 新 test 一覧

以下、TL=`test_p3_s4_loop.py`、TJ=`test_p3_s4_loop_job_contract.py`、TV=`test_pipeline_verify_result_retention.py`。名前にはすべて `test_` 接頭辞があります。

| file | test 名 | 独立した根拠／変異 |
|---|---|---|
| TL | `stock_control_reaches_campaign_under_applied_template` | 固定 genome・順序・契約・receipt／M1・M2 |
| TL | `stock_control_does_not_touch_loop_state` | 禁止呼出しと checkpoint bytes／M3 |
| TL | `stock_control_cli_rejects_conflicting_modes` | 実 argparse の排他／M4 |
| TL | `fixture_value_minus_one_remains_rejected` | 実 main と構築後変異の再検査／M5 |
| TL | `stock_control_rejects_non_stock_certified_source` | variant／source の独立負例／M7 |
| TL | `stock_condition_gate_declares_adaptive_branch` | 実 gate の request・MeaningCase／M10 |
| TL | `stock_control_reports_skipped_without_restore` | 復元禁止・ID 非捏造 |
| TL | `stock_and_candidate_share_manifest_campaign_identity` | 実 manifest・receipt・両 CLI |
| TL | `stock_digest_refresh_keeps_checkpoint` | 実 loop／pipeline／WAL。**現在失敗** |
| TL | `calibrated_perf_uses_p2_constants_and_exact_workload` | P2・S2 定数 |
| TL | `calibrated_cli_binds_effective_perf_before_layout` | emit／stock の identity と実効値／M8 |
| TL | `calibrated_candidate_cli_reaches_effective_perf` | fixture／proposal の実効値 |
| TL | `default_cli_preserves_preimage_bytes` | 変更前の固定 bytes／M9 |
| TL | `perf_cli_rejects_partial_and_invalid_options` | 片指定・未知 workload |
| TL | `verify_opt_in_reaches_real_loop_evaluate_options` | 実 loop の追加 correctness／M14 |
| TL | `campaign_lock_preimage_reconstructs_performance_correctness` | 実 lock からの復元 |
| TL | `candidate_cli_rc_zero_on_rejected_outcome_is_not_pair_success` | 実 proposal 拒否と既存 rc 契約 |
| TL | `stock_perf_cli_ingestion_exclusion` | 既存 ingestion 排他の優先 |
| TJ | `stock_fragment_mutants_have_one_static_failure` | 7 pin の一意性・単一 failure |
| TJ | `default_job_invokes_driver_once` | 実 shell の既定 argv・履歴／M11 |
| TJ | `pair_job_runs_candidate_then_stock` | 実 shell の順序・manifest／M6 |
| TJ | `pair_job_runs_stock_after_candidate_failure` | 履歴・rc・実 EXIT trap／M12・M13 |
| TJ | `invalid_stock_environment_refuses_before_prebuild` | 空値等の事前拒否 |
| TV | `performance_verify_keeps_legacy_and_all_repetitions` | 実 verifier・全 rep・COMMIT |
| TV | `performance_anomaly_at_first_repetition_aborts_before_bench` | 初回 anomaly の即停止 |
| TV | `performance_anomaly_at_last_repetition_aborts_before_bench` | 最終 anomaly・bench 禁止／M15 |
| TV | `legacy_anomaly_skips_performance_pass` | legacy 拒否時の停止 |
| TV | `performance_verify_requires_exact_contract_numactl` | 不一致の build 前拒否・空 prefix 正例 |

## 実走結果

指定の Python harness／`pytest.main()` 形式で実行しました。

| nodeid／選択範囲 | 件数・結果 | rc |
|---|---:|---:|
| `orchestrator/tests/test_p3_s4_loop_job_contract.py` 全件 | **107 passed** | 0 |
| `orchestrator/tests/test_pipeline_verify_result_retention.py` 全件 | **11 passed** | 0 |
| TL 指定 `-k` 焦点走 | **42 passed、1 failed** | 1 |
| TL 全件 | **548 passed、1 failed** | 1 |
| `test_plain_runner_coverage.py` 全件 | **3 passed** | 0 |
| `test_hooks.py::test_bash_pegasus_registry_schema_and_fixed_classes` | **1 passed** | 0 |
| `test_pegasus_tools.py::test_certify_gflags_stage_is_pinned_fail_closed_and_precedes_ccbench` | **1 passed** | 0 |

唯一の失敗 nodeid：

`orchestrator/tests/test_p3_s4_loop.py::test_stock_digest_refresh_keeps_checkpoint`

変異はファイルを変更せずプロセス内で実行し、**M0 SURVIVED、M1〜M15 KILLED**。M15 は旧 TV 6 件が通過し、新しい最終 repetition 負例が失敗する新旧差も確認しました。README fence 検査は TJ 全件に含まれます。`git diff --check` も通過しました。

## 波及

- sort／trigger driver はそれぞれ自前の condition gate を持ち、変更不要。
- `p3_b4_launcher.py` の base route は `p3_s4_loop.main` を呼びます。B4＋stock は排他です。
- TJ helper consumer は履歴の先頭参照と rc 確認へ更新し、既存 argv 期待値を維持。
- 親向け README 差分案：stock env の値域を追加し、「manifest・宣言値は proposal のみ」を「pair 時は stock にも転送」へ置換。coder-role は proposal のみ。候補優先 rc、fresh layout、skip 非成功、別 worktree、digest 更新、rc と対照成立の区別を記載。qsub fence は既存 1 個を更新してください。

## 未了・懸念

[build_admission.py:674](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2795-unit-impl/orchestrator/campaign/build_admission.py:674) の stock-baseline 条件は、STOCK・tracked_clean に加え、`source.ccbench_commit == CURRENT_PIN` を要求します。

現在の `CURRENT_PIN` は短縮形 `511c953`、S4 の PIN は full SHA です。裁定指定の authority なし context では generator receipt もなく、実 pipeline が **`admission-error`** を返します。実 template は tracked-clean 条件にも関わります。

このため成功 fixture を緩めず、失敗 test を残しました。裁定 §2-1 にない **driver での既存 generator receipt 発行・転送**を追加してよいか確認中です。所有外 admission の変更はしていません。実 compiler での STOCK 成立も未測定です。

## 総括

5 file の実装・回帰検証・変異検証を行い、既存テストは通過しています。ただし **stock 正例が admission で停止するため未完了**です。差分は working tree に残しています。