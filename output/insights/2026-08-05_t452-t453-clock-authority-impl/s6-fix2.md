| 所見 | 状態 | 対応 |
|---|---|---|
| NREG-CPU-1 | **partial** | gate と負例は実装済み。scheduler 障害で pytest 未実走 |
| IMP-R1 | **partial** | `sys.path` 完全復元と fresh subprocess 契約を実装済み。pytest 未実走 |
| regressed | **なし（静的確認）** | 既存期待値の反転・緩和・skip・xfail・削除なし |

### 実装内容

- [env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/campaign/env_attestation.py:519) で validation copy による迂回を除去しました。返却される `ObservedAttestationProfile` 自体が `model_name_normalized == normalize_cpu_model_name(model_name_raw)` を満たす場合だけ受理されます。
- [test_env_attestation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_env_attestation.py:185) の比較器 mismatch test は parser を経由せず型 fixture を直接構築します。期待 verdict は変更していません。
- 同ファイルに v1/v2 forged pair の parser 負例を追加しました。
- [test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:789) で v1/v2 の live 経路を `InfraFailure(reason_code="parse_failure")` に固定しました。
- 同ファイルの [raw replay 負例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_silo_ladder_rung1_driver.py:1928) は v1/v2 とも `EvidenceFailure(reason_code="raw_bundle")` に固定しました。
- [fetch_third_party.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/tools/pegasus/fetch_third_party.py:52) は repo root と orchestrator root を一時挿入し、成功・例外の双方で元の `sys.path` を完全復元します。
- [test_pegasus_thirdparty_fetch.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t452-t453-clock-authority/orchestrator/tests/test_pegasus_thirdparty_fetch.py:836) は module cache のない fresh subprocess で完全一致を検査します。

### 受理集合の対比

変更前は、raw=`Intel Xeon Platinum 8468H`、normalized=`Intel Xeon Platinum 8468` の forged pair が v1/v2 parser を通過しました。他条件と clock が帯内なら、Silo live/raw は normalized 値だけで `cpu_model_match=True`、最終的に `all_pass=True` と判定できました。

変更後は `normalize_profile()` の導出整合性検査で v1/v2 とも `AttestationError` になります。Silo live は `parse_failure`、raw replay は `raw_bundle` として fail-closed になります。整合する既存 v1/v2 profile の受理集合は変更していません。

IMP-R1 は成果物の受理集合を変更せず、fetcher 呼出し後の interpreter 状態だけを呼出し前へ戻します。

### テスト・検査

次の nodeid を `tools/run_tests.py -rf` で計算ノードへ dispatch しました。

- `test_env_attestation.py::test_compare_profiles_reports_each_field_mismatch`
- `test_env_attestation.py::test_compare_profiles_normalizes_raw_name_and_applies_expected_clock_tolerance`
- `test_env_attestation.py::test_probe_output_rejects_forged_cpu_name_pair`
- `test_env_attestation.py::test_observed_hash_projection_preserves_source_schema_preimage`
- `test_silo_ladder_rung1_driver.py::test_live_attestation_rejects_forged_cpu_name_pair`
- `test_silo_ladder_rung1_driver.py::test_raw_attestation_rejects_forged_cpu_name_pair`
- `test_silo_ladder_rung1_driver.py::test_live_attestation_parser_failures_preserve_infra_reason`
- `test_silo_ladder_rung1_driver.py::test_raw_attestation_parser_failures_remain_raw_bundle_evidence`
- `test_pegasus_thirdparty_fetch.py::test_driver_import_removes_only_its_temporary_sys_path_entry`

結果は **rc=16、pytest 実行 0 node** です。`qstat -Q` preflight は二度とも **rc=1**、`NQSconnect: Can't create socket` でした。ログインノード上の pytest には迂回していません。

静的検査:

- 変更 Python 5 ファイルの `py_compile`: **rc=0**
- `git diff --check`: **rc=0**
- `python3 tools/check_codex_agents.py`: **rc=0**
- `python3 tools/check_docs.py`: **rc=0**
- 保護対象の diff 検査: **rc=0**
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` の AST 件数検査: **exact 1**

### 所有外への波及可能性

静的に確認した範囲です。

- parser caller: Silo live、Silo raw replay、履歴 evidence replay。
- observed fixture consumer: calibrator certify、execution receipt、S8b floor/oracle、T126 回帰。
- CPU 名を個別変更する既存 fixture は `test_env_attestation.py` の比較器 test と `test_pegasus_tools.py`。後者は raw/normalized を同時更新しており整合しています。
- no-edit consumer regression 候補: `test_execution_guard.py`、`test_calibrator_certify.py`、`test_s8b_floor_campaign.py`、`test_s8b_oracle_driver.py`、`test_silo_ladder_rung1_evidence.py`、`test_t126_qualification_driver.py`。
- fetcher 側 caller は `_load_policy()`。復元後に使う `third_party_policy()` と `_dependency_pins()` に遅延 import は見つかりませんでした。
- module cache、import 順序、third-party fetch 全体は親の受入全走で再確認が必要です。

### 境界確認

- R-1: loader self-pass は追加していません。
- R-2: `t126_driver.py` は未変更です。
- R-3 後半: T126 envelope は上げていません。
- `output/`、docs、`external/ccbench` は無変更です。
- registry calibration path/SHA、`contract_sha256`、`FROZEN_MANIFEST` は無変更です。
- `KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は exact 1 件です。
- `git add`／`git commit` は実行していません。

## 総括

- NREG-CPU-1 の正しさ gate を返却値まで復旧した。
- 比較器の独立 mismatch 検査は parser 外の型 fixture へ分離した。
- v1/v2 × parser/live/raw の forged pair 負例を追加した。
- IMP-R1 は両 import root の完全復元で修正した。
- 受理集合は forged pair のみ拒否へ戻した。
- 静的検査はすべて rc=0。
- pytest は scheduler 障害で rc=16・0 node のため、closed 申告は保留する。