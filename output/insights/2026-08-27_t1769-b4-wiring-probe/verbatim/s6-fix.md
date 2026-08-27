## F1〜F12 の対応表

正式 pytest が child 未起動のため、`closed` とはせず全項目を `partial（実装済み・formal 未実走）` とします。

|項目|状態|根拠|
|---|---|---|
|F1|partial|source/destination、`dir_fd`、pre-opened fd を個別 realpath 解決。`p3_b4_wiring_probe.py:242,312,493`。4 operation 負例と fd 負例は `test_p3_b4_wiring_probe.py:641,687`|
|F2|partial|39-module import 閉包の exact manifest/hash、inventory の unresolved 検査、alias resolver を実装。`probe.py:998,1020,1130,1845`、`test.py:152,192,338`|
|F3|partial|静的 preflight を runtime import 前へ移動。local import-time call closure、decorator、fresh single-thread 条件を実装。`probe.py:862,1171,1927`、`test.py:246,256`|
|F4|partial|profile setter、code generation/assignment を遮断。swap→実 writer→restore 後の publish ledger 拒否を実装。`probe.py:354,516,581,623`、`test.py:716,767`|
|F5|partial|evidence SHA を `view.decision.overlay_ledger_sha256` 由来に変更し、事後再読は一致確認だけに限定。`probe.py:1966,2019,2057`|
|F6|partial|固定 versioned domain prefix＋NUL、cfg locator 非一致検査、trigger の実 `_current_site`→contract→cfg path を実装。`probe.py:56,1607,1646`、`test.py:509`|
|F7|partial|全 static edge の逐語 guard、狭い check 名、top-level 非主張、実 write/link 境界観測を実装。`probe.py:1041,1669,1718,1800`、`test.py:126,460`|
|F8|partial|single-main-thread、unprofiled、interpreter 内 1 回限りを強制。`probe.py:1422,1927`、`test.py:1000`|
|F9|partial|`_run()` / `__main__` harness を追加。allowlist は未変更。`test.py:1049`|
|F10|partial|環境指定 protected root を `tmp_path` 配下に置き、実 writer 前の binding gate と manifest 不変を検査。`probe.py:1269,1388`、`test.py:533`|
|F11|partial|consumer を名前推測ではなく glob/rglob/git-list/source-scan の参照行から再列挙。下記「波及可能性」に記載|
|F12|partial|primary exception を維持し、cleanup failure を `__cause__` に保持。`probe.py:1269,1439,1976`、`test.py:868`|

## 実走した検査

正式 runner は以下を要求しましたが、`qstat -Q` preflight failure、`rc=16`、`child_started=false` で、実走 nodeid は 0 件です。

- `orchestrator/tests/test_plain_runner_coverage.py`
- `test_p3_b4_wiring_probe.py::test_static_candidate_paths_and_driver_specific_guards`
- `test_p3_b4_wiring_probe.py::test_aliased_dynamic_bindings_on_proof_path_fail_closed`
- `test_p3_b4_wiring_probe.py::test_inventory_builder_rejects_recorded_unresolved_issue`

runner は ignored 領域の `output/pegasus-dispatch/3842676fca1078a4e151861e573b7b43/receipt.json` を自動生成しました。親の `output/insights/2026-08-27_t1769-b4-wiring-probe/` は編集・削除していません。

pytest 外の child diagnostic では次を確認しました。

- F1: rename/replace/link/symlink destination と pre-opened fd、全て manifest 不変
- F2/F3/F6/F7: 39-module static/runtime 閉包、19-entry inventory、alias 4 種、decorator/helper、全 edge guard、domain prefix
- F4: profile setter/code assignment 3 種、swap→writer→restore 後 publish 拒否
- F8/F10/F12: 2 回目 main 拒否、安全な binding 負例、primary/cause 保持
- F9: `test_plain_runner_coverage.py` の 3 assertion を直接実行して成功
- 実 `main()`: base/sort 正例は全 evidence assertion 成功
- trigger 正例は login node の実 resolver が `PEGASUS_LOGIN` を返し、production `_admit_env_contract` が拒否。compute node 未実走
- 実 `main()`→実 `pipeline.evaluate` は `OutcomeGenerationError`、evidence 0 件
- `tools/check_subprocess_bytecode_guard.py --repo .`: exit 0
- 両ファイル AST parse、whitespace check: 成功

## 変異の単一理由性

|変異|期待 node|過剰決定|
|---|---|---|
|main から遮断装着を外す|`test_main_wiring_interdicts_real_pipeline_and_publishes_nothing`|あり。`seal()` 除去は3 driver正例とsecond-mainも落ちる。`install_audit()` 除去は正例群が落ちる一方、main writer負例はprofileで通る|
|anchor seed を外す|`test_anchor_seed_alone_load_bears_pipeline_evaluate`|あり。inventory census、producer parameter、3 driver正例にも波及|
|save seed を外す|`test_save_loop_state_seed_is_independently_load_bearing`|あり。save producer parameterと3 driver正例にも波及|
|project seed を外す|`test_project_whiteboard_seed_is_independently_load_bearing`|あり。project producer parameterと3 driver正例にも波及|
|multi-path destination 解決を外す|`test_audit_blocks_each_protected_destination_with_dir_fd_without_mutation[...]`|あり。共有 resolver の除去で operation parameter 4 node が落ちる|
|unresolved inventory 検査を外す|`test_inventory_builder_rejects_recorded_unresolved_issue`|なし（`_build_inventory()` の exact issue gate）。visitor/proof 全体を外す変異は alias parameter 群にも波及|
|publish 観測を事前観測へ戻す|`test_publish_observes_each_real_write_and_link_boundary`|なし。publisher の exact stage 列だけを固定|
|restore 後 publish 拒否を外す|`test_module_swap_writer_restore_is_rejected_at_publish`|なし。`blocked_outcome_attempts` publish gate の exact site|
|失敗時 publish 抑止を外す|`test_failed_check_publish_gate_is_schema_independent`|なし。schema と独立した `failed_check_attempts` gate を直接固定|

seed・装着・multi-path の変異は現状過剰決定です。親の再設計時に、専用照合 site へ再照準が必要です。

## 波及可能性

- 所有外の直接 caller: 新 `main()`、private fixture、private guard を呼ぶ既存 production caller はありません。
- 共有 fixture: 既存 fixture は流用せず、`static_runtime` と child seam は新 test file 内だけです。
- 参照関係から確認した consumer test:

|consumer|参照根拠|
|---|---|
|`test_plain_runner_coverage.py`|全 `test_*.py` 列挙、`:44-74`|
|`test_p3_exploration_namespace.py`|campaign `*.py` discovery、`:123-139`|
|`test_p3_build_authority_cli.py`|tracked Python/source census、`:195,1191`|
|`test_s8b_floor_campaign.py`|orchestrator/campaign recursive scan、`:1428,6088`|
|`test_s8b_oracle_manifest_contract.py`|campaign `*.py` scan、`:49`|
|`test_s1_known_axes_freeze.py`|campaign `*.py` scan、`:537-540`|
|`test_campaign_import_invariant.py`|campaign shape/import scan、`:1040-1083`|
|`test_campaign.py`|repository Python census、`:5130`|
|`test_s8b_floor_stats.py`|campaign `*.py` scan、`:861-864`|
|`test_s8b_ratified_freeze.py`|campaign `*.py` scan、`:2377-2379`|
|`test_ccbench_spawn_sites.py`|production recursive AST scans、`:309,359,465`|
|`test_check_subprocess_bytecode_guard.py`|real-repository subprocess scan、`:204-205`|
|`test_login_headroom.py`|tracked/untracked literal census、local constant census、`:1602-1643`|
|`test_p3_s4_loop.py`|全 production Python の ingress census、`:1107-1119`|
|`test_reflux_ir.py`|全 production Python の golden consumer census、`:274-298`|
|`test_t1286_commit_receipt.py`|production commit-call census、`:657-700`|
|`test_s8b_oracle_report.py`|全 production Python caller census、`:5488-5508`|
|`test_t338_submission_gate_unit5.py`|repository-wide receipt-call census、`:490-516`|

`test_frozen_artifacts.py` は固定 output だけを対象とし、新規2ファイルの consumer ではないため除外しました。

## 総括

- F1〜F12 は許可された新規2ファイル内へ実装済みです。
- 正式 pytest は dispatch infrastructure failure のため 0 nodeid 実走です。
- base/sort 正例と主要負例は child diagnostic で確認済みです。
- trigger 正例は actual site contract に従い login node で拒否され、compute 未実走です。
- 親確定の plain-runner 赤は harness 追加後、direct assertion では解消しました。
- seed・装着・multi-path 変異には過剰決定が残るため明示しました。
- commit/add/stash/branch 操作は行っていません。