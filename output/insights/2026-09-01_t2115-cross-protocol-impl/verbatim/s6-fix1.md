## 対応表

| 項目 | 状態 | 根拠 |
|---|---|---|
| P-1 | closed（pytest 未実走） | fixture を実際の `calibration/` 配下へ修正し、例外と bytes 保持を検査。[test_between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:191) |
| P-2 | closed（pytest 未実走） | `CMakeLists.txt` の `ccbench_add_protocol(... SOURCES ...)` だけを走査。欠落・読取不能・未列挙 source は拒否。[between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:111)、[test_between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:256) |
| P-3 | closed（pytest 未実走） | コメントを照合前に除去し、literal `#if 0` block だけを除外。一般のプリプロセッサ条件評価器は追加していない。[between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:161)、[test_between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:324) |
| P-4 | closed（pytest 未実走） | body を整数化して `Genome.canonical()` と完全一致させ、空・重複・非整数・非整列を拒否。[genome.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/genome.py:121)、[test_layer3_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_layer3_report.py:2926) |
| P-5 | closed（pytest 未実走） | JSON/Markdown 両内容を先に構築し、作成途中の例外では作成済み file を rollback。[between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/between_run_floor.py:258)、[test_between_run_floor.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_between_run_floor.py:219) |
| P-6 | closed（pytest 未実走） | wrong-protocol floor 1 件だけを置く単一理由負例を追加。[test_screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/tests/test_screening_driver.py:250)、[screening_driver.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/orchestrator/campaign/screening_driver.py:150) |

## 変更内容

この fix 段で変更したのは次の 5 file です。

- `orchestrator/campaign/between_run_floor.py`
- `orchestrator/campaign/genome.py`
- `orchestrator/tests/test_between_run_floor.py`
- `orchestrator/tests/test_screening_driver.py`
- `orchestrator/tests/test_layer3_report.py`

production の残り 6 file と、既存テストの期待値、docs、submodule、既存 campaign/freeze 成果物は変更していません。commit、add、stash 等も実行していません。

## 実走結果

実走した pytest nodeidはありません。2 回とも `tools/run_tests.py` が `qstat -Q preflight rc=1`、`rc=16 / child_started=false` で停止し、pytest child は開始されませんでした。

以下はすべて実装済み・未実走です。

- `test_between_run_floor.py::test_write_out_is_create_only_and_preserves_existing_bytes`
- `test_between_run_floor.py::test_write_out_rolls_back_json_when_markdown_creation_fails`
- `test_between_run_floor.py::test_trace_hook_admission_is_bound_to_source_facts`
- `test_between_run_floor.py::test_trace_hook_admission_requires_readable_cmake_sources`
- `test_between_run_floor.py::test_trace_hook_admission_ignores_uncompiled_source`
- `test_between_run_floor.py::test_trace_hook_admission_accepts_listed_source`
- `test_between_run_floor.py::test_trace_hook_admission_rejects_commented_out_hook`
- `test_between_run_floor.py::test_trace_hook_admission_rejects_hook_only_in_if_zero`
- `test_between_run_floor.py::test_mocc_floor_rejected_before_build_or_measure_without_trace_hook`
- `test_between_run_floor.py::test_hook_bearing_source_routes_mocc_baseline_through_main`
- `test_screening_driver.py::test_load_between_run_floor_selects_requested_protocol_among_same_workload`
- `test_screening_driver.py::test_load_between_run_floor_rejects_single_wrong_protocol_floor`
- `test_screening_driver.py::test_load_between_run_floor_rejects_missing_or_malformed_genome`
- `test_layer3_report.py::test_campaign_protocol_rejects_missing_malformed_and_multiple_canonical_values`
- `test_layer3_report.py::test_between_run_floor_rejects_missing_or_malformed_genome`

代替の非 pytest 検査結果:

- `git diff --check`: 通過
- 変更対象 5 file の AST parse: 通過
- 一時 directory probe: silo=True、mocc/tictoc/cicada=False、未コンパイル decoy=False、列挙 source 正例=True、コメント・`#if 0` 負例=False
- consumer probe: malformed 5 形の floor/WAL 拒否、wrong-protocol 1 件拒否、create-only bytes 保持、P-5 rollback を確認

## 受理集合

受理:

- 読取可能な `cc/<protocol>/CMakeLists.txt` の `SOURCES` に列挙された実コンパイル source。
- コメントと literal `#if 0` block を除いた同一 file に、trace include、`#if TRACE`、`izanagi_trace::` 呼出しが揃うもの。
- 現行 tree の silo。直接 probe で引き続き True を確認。
- `protocol|A=0,Z=1` のように body が非空で、名前が重複せず名前順、値が整数である canonical genome。

拒否:

- CMakeLists/SOURCES を読めない、未コンパイル file にしか証拠がない、コメントまたは literal `#if 0` にしか hook がない protocol。
- 現行 tree の mocc、tictoc、cicada。
- 欠落、非文字列、`|` 不在、空 protocol/body、非整数、重複名、非整列 genome。
- 指定された `mocc|garbage`、`silo|B=x`、`silo|Z=1,A=0`、`silo|A=1,A=2`、`silo|`。
- requested protocol と異なる floor しか存在しない場合。

## 波及

production caller:

- `screening_driver.load_between_run_floor`
- `layer3_report._campaign_protocol`
- `layer3_report._calibration_floors`
- `between_run_floor.main`

共有 fixture は増やしておらず、変更した `_floor_result`、`_write_floor`、`_campaign`/`_record` 利用は各 test file 内に閉じています。

静的に波及しうる未実走 consumer test:

- screening 系: `test_screening_opt_in.py`、`test_backoff_sweep.py`、`test_s6_sort_sweep.py`、`test_s8a_trigger_sweep.py`、`test_guided.py`、`test_p2_2_site_aware.py`、`test_t1416_backoff_compiler_binding.py`
- Layer 3 系: `test_autonomous_trial_completeness.py`、`test_layer3_admission_diagnosis.py`、`test_p3_autonomous_workload_trial.py`、`test_trial_registry.py`
- source/schema/hash 内容走査系: `test_s8b_floor_campaign.py`、`test_official_perf_closure.py`、`test_ccbench_spawn_sites.py`、`test_pegasus_floor_scoping.py`、`test_s1_known_axes_freeze.py`、`test_s8b_oracle_driver.py`、`test_t126_pegasus_tools.py`、`test_t126_qualification_artifacts.py`

## 未完・懸念

- pytest は infrastructure failure のため未実走であり、緑とは報告しません。
- runner が失敗 receipt を [b748…/receipt.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/output/pegasus-dispatch/b7486062ca790773e579ceb01a72fd10/receipt.json) と [b20b…/receipt.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2115-author/output/pegasus-dispatch/b20beefc4695393ab5e442858f49e0a2/receipt.json) に自動生成しました。禁止に従い削除・変更していません。
- nit 3 件には手を出していません。焦点走集合の拡張、TOCTOU 対応、共通 header include の受理は未変更です。
- docs、既存 `output/` 成果物、submodule、hooks/tools、既存テスト期待値は編集していません。

## 総括

P-1〜P-6 はコードと指定負例まで実装しました。  
直接 probe と静的検査は通過しています。  
pytest は Pegasus dispatch 障害で全 nodeid 未実走です。  
commit は作成していません。