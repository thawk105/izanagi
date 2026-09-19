# 参照されないコードの棚卸しと掃除 — inventory と裁定パッケージ (dw-dead-code-inventory)

authority: none
default_effect: no-state-change

- 日付: 2026-09-19〜20 (JST)。wave branch `worktree-dw-dead-code-inventory`、計測 HEAD `18736b502` (最終走査)、実装 base `8fd1eecf9` (local main へ ff 後)。
- 依頼: orchestrator / tools / hooks / tools/pegasus の Python を import graph と参照 grep で棚卸しし、(A) どこからも参照されない module を削除、(B) 自分の test だけが参照する module を test と対で扱う、(C) 同一機能の重複 helper を統合、(D) docs の歴史記録からだけ参照される module は削除せず裁定へ返す。凍結成果物 (事前登録・campaign.lock・凍結 spec) とその producer / validator、verifier・calibrator・hooks は対象外 (規律 1・2)。scope 外 = リファクタ・一般化・新 framework。
- 本書は可変状態の正本ではない。裁定待ちの項目は §5 にまとめ、実装した変更は §4 に書く。

## 1. 方法 (再現手順)

- probe は job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dead-code-inventory/import_graph.py`、repo には入れない) で、次を行う。
  1. `git ls-files` の `orchestrator/**/*.py`・`tools/**/*.py`・`hooks/*.py` (819 file = orchestrator 692、tools 123、hooks 4) を `ast` で解析し、`import` / `from … import` (相対 import、`from pkg import submodule` 形、**`a.b.c` を import したときの親 package `a/__init__.py`・`a/b/__init__.py` への暗黙辺**を含む) と `importlib.import_module` / `runpy` の文字列引数を解決して import graph を作る。import 元が `/tests/` 配下か `test_*.py` なら test 側、それ以外を prod 側と数える。
  2. `external/` と binary (`.gz .png .pdf` 等) を除く tracked file 26,383 本を GNU `grep -aoHF` (多パターン同時照合) で走査し、各 Python file の **強い形** = 完全 path (`tools/x.py`)、拡張子なし path、dotted module 名 (`orchestrator.campaign.x`、`campaign.x`)、basename (`x.py`) と、**弱い形** = stem 単独 (10 文字以上かつ `_` を含むものだけ、`-w` 単語一致) の出現を集める。
  3. 参照元を分類する: **exec** (`.sh` / `.pbs`、`.claude/`、`.agents/`、`hooks/`、`pyproject`/`pytest.ini`、`AGENTS.md`/`CLAUDE.md`/`README.md`、prod の `.py` 内の文字列)、**docs-op** (上記以外の `docs/**` と `*.md`、runbook や dev-wave 契約、事前登録文書を含む)、**docs-hist** (`docs/worklog*`、`docs/archive/`、`docs/decisions.md`、`docs/failures.md`、`docs/roadmap-history/`、`docs/handoff/`、`docs/spool/`、`output/**` 全部)、**data** (それ以外)。
  4. 区分: prod import か exec 参照か data 参照があれば **live**。それが無く test の import / 文字列参照だけなら **B** (docs-op 参照があれば B2、無ければ B1)。test も無く docs-op だけなら **docs-op-only**、docs-hist だけなら **D**、何も無ければ **A**。verifier / calibrator / hooks / preregistration 配下は **protected** として区分前に除外。
  5. 重複 helper (C): test file を除く全 top-level 関数 (4 行以上) の docstring を除いた AST dump を関数名を匿名化して比較し、異なる file で一致する組を出す。同名関数の分布も出す (job dir の `inventory.md` §same-name)。
- 削除候補の pin 閉包 (DW-O09): 候補 file の path / stem に加え、**sha256 と git blob sha (完全形と 12 桁)** を同じ file 集合で走査した (F370)。hit 0。
- 走査の性質と限界: 部分文字列一致なので静的な文字列参照については上位集合だが、**参照の全体保証ではない。** 拾えない形 = 文字列を組み立てる動的 import (実例: `orchestrator/tests/test_p3_exploration_namespace.py:138–154` が glob と `source.stem` から import する)、`python -m` の短い top-level 名、subprocess argv の断片合成、`__main__` 実行の暗黙辺、entry point 解決。弱い形の hit は表に別欄で出し、区分には prod の弱い hit だけを「要確認 live」として使った (2 件、`sanity_silo.py`・`task_run_report.py`、実体を読んで live と確定)。
- 走査の履歴 (訂正込み): 初回 (拡張子 allowlist、19,042 file) → 短 stem の basename 形を追加 → `output/` 配下の `.sh`/`.py` を歴史記録へ再分類 → author 子が `.tsv` の到達性台帳の参照を発見したため対象を全 text へ拡大 (26,383 file) → 段 6 review が親 package の暗黙辺の欠落 (`tools/spool_fold.py:1307` の `orchestrator.publication.approval_guard` import が `publication/__init__.py` を実行する) を指摘したため辺を追加。最終走査は HEAD 18736b502。所要は 1 走 約 5 分 (Python の巨大交替 regex では 10 分で終わらず `grep -F` のバッチへ切替)。

## 2. 集計

| 区分 | file | 行 | 意味 |
|---|---|---|---|
| A | 0 | 0 | どこからも参照されない。段 1 の初回走査 (拡張子 allowlist、19,042 file) では 3 file を A と数えたが、author 子の削除前 grep が `.tsv` の到達性台帳 (T-2638) の参照を見つけ、走査対象を外部 submodule と binary 以外の全 tracked file (26,383 file) に広げて再走した結果 A は 0 になった |
| D | 6 | 679 | docs / insights の歴史記録からだけ参照される (上の 3 file を含む) |
| docs-op-only | 1 | 65 | 運用文書 (事前登録文書) だけが参照する (`s6_proposal_rounds_power.py`) |
| B1 | 29 | 21,600 | 自分の test だけが参照し、運用文書の参照なし (専用 test 18 本 / 12,217 行、file 名で重複排除) |
| B2 | 19 | 15,216 | test に加え runbook・dev-wave 契約・事前登録・図 provenance が名指しする (現用扱い、専用 test 15 本 / 12,152 行) |
| live | 334 | 396,365 | prod の import か、shell / command / hook 配線 / data からの参照がある (弱参照だけの 2 file `sanity_silo.py`・`task_run_report.py` を実体確認で live に含む) |
| protected | 36 | 16,033 | verifier / calibrator / hooks / preregistration (対象外) |
| test | 394 | 596,597 | test file 自身 (対象外) |
| C | 118 組 | 単純合計 1,429 | 完全一致の重複関数 (≥4 行、test 除外、HEAD 18736b502 = C8 統合後)。最長 15 行以上は 22 組 / 534 行。「単純合計」= 各組で最長 1 本を残し他を消した行数で、import 追加・意味論差を無視した上限側の目安 |

- 母数: Python 819 file (orchestrator 692 = prod 301 + tests 391、tools 123、hooks 4)。行数は `wc -l` 相当。

- 依頼が例示した `tools/t1434_t1222_science_slice.py` (B1)・`tools/t189_*.py` (`t189_price_snapshot.py` は `tools/codex_reasoning_ab.py:50` が path で起動する live、`t189_task_catalog.py` は `t189_oracle_wiring_slice.py` が import する live、`t189_oracle_wiring_slice.py` は B2)・`tools/t2216_backoff_walk_model.py` (B2) は、いずれも A ではない。
- 観察: `hooks/enforcement-source-closure-ratifications.v1.jsonl` は repo 内に消費者が 0 (自分以外に文字列 `closure_digest_sha256` / file 名の hit 無し)。hooks は対象外なので触らない。

## 3. 表

### A — どこからも参照されない (0 file / 0 行)

該当なし (走査対象を external/ と binary 以外の全 tracked file 26,383 本へ広げた再走査の結果)。

### D — docs / insights の歴史記録からだけ参照される (6 file / 679 行)

| file | 行 | 参照 file 数 | 参照元 (先頭 6) |
|---|---|---|---|
| `orchestrator/campaign/p2_5.py` | 167 | 4 (+弱 0) | `docs/archive/audit-2026-06-30.md`, `docs/archive/worklog-phase3-0903-1231.md`, `docs/decisions.md`, `output/insights/2026-08-03/t342-t344-provenance-capability/s3-lens-a.md` |
| `orchestrator/campaign/s6_amendment_20260713_fence.py` | 117 | 3 (+弱 3) | `docs/archive/worklog-phase3-0903-1231.md`, `output/insights/2026-07-17_repo-refinement-consultations.md`, `output/insights/2026-07-29_t149-review-verbatim/lensB.md` |
| `orchestrator/manual_probes/t1994_capdrop_probe.py` | 99 | 2 (+弱 0) | `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv`, `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach_all.tsv` |
| `orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py` | 100 | 3 (+弱 0) | `output/insights/2026-09-14/t1994-readonly-snapshot/verbatim/login-node-probe.txt`, `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv`, `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach_all.tsv` |
| `orchestrator/manual_probes/t1994_rootview_probe.py` | 100 | 2 (+弱 0) | `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv`, `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach_all.tsv` |
| `orchestrator/manual_probes/t1994_seccomp_probe.py` | 96 | 2 (+弱 0) | `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv`, `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach_all.tsv` |

### docs-op-only — 運用文書 (事前登録文書) だけが参照する (D と分けて数える) (1 file / 65 行)

| file | 行 | 参照 file 数 | 参照元 (先頭 6) |
|---|---|---|---|
| `orchestrator/campaign/s6_proposal_rounds_power.py` | 65 | 3 (+弱 3) | `docs/phase3-main-experiment.md`, `docs/archive/worklog-phase3-0903-1231.md`, `output/insights/2026-07-13_s6-n-determination.md` |

### B1 — 自分の test だけが参照する (運用文書の参照なし) (29 file / module 21600 行、専用 test 18 本 / 12217 行 (file 名で重複排除))

| module | 行 | 専用 test (行) | 共有 test が名指し (pin 表など) | 歴史記録 file 数 | 運用文書の参照 |
|---|---|---|---|---|---|
| `orchestrator/campaign/backoff_counterfactual_analysis.py` | 694 | `test_backoff_counterfactual_analysis.py` (662) | `test_backoff_counterfactual_cohort2_analysis.py` | 42 |  |
| `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py` | 786 | `test_backoff_counterfactual_cohort2_analysis.py` (661) | `test_t2187_adaptive_const_probe.py` | 23 |  |
| `orchestrator/campaign/backoff_nonmonotonicity_analysis.py` | 1365 (main) | `test_backoff_nonmonotonicity_analysis.py` (808) |  | 16 |  |
| `orchestrator/campaign/backoff_requested_us.py` | 1262 (main) | `test_backoff_requested_us.py` (1221) | `test_ccbench_spawn_sites.py`, `test_p3_build_authority_cli.py` | 55 |  |
| `orchestrator/campaign/backoff_sweep_report.py` | 219 (main) |  | `test_backoff_consumers.py` | 56 |  |
| `orchestrator/campaign/floor_liveness.py` | 926 (main) |  | `test_ccbench_spawn_sites.py`, `test_pegasus_floor_tools.py` | 22 |  |
| `orchestrator/campaign/mocc_g2_repro_ledger.py` | 926 (main) | `test_mocc_g2_repro_ledger.py` (622) |  | 8 |  |
| `orchestrator/campaign/mocc_trace_pair_anchor.py` | 721 (main) |  | `test_ccbench_spawn_sites.py`, `test_mocc_trace_pair.py` | 6 |  |
| `orchestrator/campaign/p3_b4_prerun_caller.py` | 172 (main) | `test_p3_b4_prerun_caller.py` (270) |  | 11 |  |
| `orchestrator/campaign/p3_b4_producer_auth_experiment.py` | 2328 | `test_p3_b4_producer_auth_experiment.py` (1928) | `test_ccbench_spawn_sites.py` | 22 |  |
| `orchestrator/campaign/s6_canary_rename.py` | 312 (main) |  | `test_ccbench_spawn_sites.py` | 5 |  |
| `orchestrator/campaign/s8b_oracle_exploration.py` | 91 (main) |  | `test_s8b_oracle_artifacts.py` | 15 |  |
| `orchestrator/campaign/s8c_gate_report.py` | 178 (main) | `test_s8c_gate_report.py` (517) | `test_s8c_cli_entrypoints.py` | 29 |  |
| `orchestrator/manual_probes/t1994_readonly_snapshot_qualification.py` | 961 (main) |  | `test_buildcache_v2.py` | 14 |  |
| `orchestrator/publication/addendum_p_envelope.py` | 28 | `test_t793_addendum_p_envelope.py` (54) |  | 9 |  |
| `orchestrator/publication/ledger.py` | 389 | `test_t793_publication_ledger.py` (360) | `test_ccbench_spawn_sites.py` | 53 |  |
| `orchestrator/submission_gate/_attempt_authority.py` | 845 |  | `test_t338_submission_gate_unit4.py`, `test_t338_submission_gate_unit5.py` | 1 |  |
| `orchestrator/submission_gate/_writer.py` | 84 |  | `test_campaign.py`, `test_t338_submission_gate_unit5.py` | 20 |  |
| `tools/acceptance_issuer_reference.py` | 591 (main) |  | `test_external_acceptance_signing.py` | 24 |  |
| `tools/check_silo_validation_isolation.py` | 1501 (main) |  | `test_silo_validation_isolation.py` | 13 |  |
| `tools/check_subprocess_bytecode_guard.py` | 427 (main) | `test_check_subprocess_bytecode_guard.py` (228) |  | 23 |  |
| `tools/hold_inventory.py` | 251 (main) | `test_hold_inventory.py` (899) |  | 57 |  |
| `tools/insights_date_layout.py` | 411 (main) | `test_insights_date_layout.py` (447) |  | 6 |  |
| `tools/migrate_output_gzip.py` | 885 (main) | `test_migrate_output_gzip.py` (473) |  | 0 |  |
| `tools/mutation_fanout.py` | 1893 (main) | `test_mutation_fanout.py` (1039) |  | 66 |  |
| `tools/plotting/plot_t2266_tail_mechanism.py` | 625 (main) | `test_plot_t2266_tail_mechanism.py` (505) |  | 12 |  |
| `tools/t1434_t1222_science_slice.py` | 1282 (main) | `test_t1434_t1222_science_slice.py` (521) |  | 3 |  |
| `tools/update_acceptance_duration_ledger.py` | 610 (main) | `test_update_acceptance_duration_ledger.py` (1002) |  | 98 |  |
| `tools/verify_paper_story_a1_balanced_sizing.py` | 837 (main) |  | `test_paper_story_a1_balanced_sizing.py` | 10 |  |

### B2 — test に加え運用文書が名指しする (現用扱い、削除候補にしない) (19 file / module 15216 行、専用 test 15 本 / 12152 行 (file 名で重複排除))

| module | 行 | 専用 test (行) | 共有 test が名指し (pin 表など) | 歴史記録 file 数 | 運用文書の参照 |
|---|---|---|---|---|---|
| `orchestrator/campaign/backoff_policy_performance_analysis.py` | 869 | `test_backoff_policy_performance_analysis.py` (1062) | `test_t2187_adaptive_const_probe.py` | 16 | `docs/backoff-policy-performance-preregistration.md` |
| `orchestrator/campaign/calibration_freeze_stage6_candidate_gate.py` | 59 | `test_calibration_freeze_stage6_candidate_gate.py` (613) | `calibration_freeze_authority_contract.py`, `test_calibration_freeze_authority_contract.py` | 3 | `docs/calibration-freeze-authority-bundle-design.md`, `docs/env-contract-activation-prerequisites.md` |
| `orchestrator/campaign/p3_b4_wiring_probe.py` | 2258 (main) | `test_p3_b4_wiring_probe.py` (1548) | `test_t671_source_binding.py` | 98 | `docs/phase3-b4-reflux-ablation-preregistration.md` |
| `orchestrator/campaign/s1_report.py` | 1175 (main) | `test_s1_report.py` (747) | `test_ccbench_spawn_sites.py` | 92 | `docs/freeze-permanent-design-s2.md`, `docs/freeze-permanent-design.md`, `docs/paper-story/figures/README.md` … |
| `orchestrator/campaign/s1_verify_extime_calibration.py` | 494 (main) | `test_s1_verify_extime_calibration.py` (254) | `test_ccbench_spawn_sites.py`, `test_p3_build_authority_cli.py`, `test_s1_known_axes_freeze.py` | 96 | `docs/freeze-permanent-design-s2.md`, `docs/freeze-permanent-design.md` |
| `orchestrator/campaign/s8b_floor_evacuation.py` | 267 (main) | `test_s8b_floor_evacuation.py` (407) | `test_ccbench_spawn_sites.py`, `test_s8b_holdout_freeze.py` | 7 | `docs/phase3-8b-restart-runbook.md` |
| `orchestrator/campaign/s8b_verdict.py` | 880 (main) | `test_s8b_verdict.py` (1776) | `test_official_perf_closure.py`, `test_s8b_oracle_artifacts.py`, `test_s8b_oracle_manifest_contract.py`, `test_s8c_preregistration_predicates.py` | 98 | `docs/freeze-permanent-design-s2.md`, `docs/freeze-permanent-design.md` |
| `tools/collect_wave_usage.py` | 251 (main) | `test_collect_wave_usage.py` (793) |  | 39 | `docs/README.md`, `docs/dev-wave/core.md`, `docs/phase3.md` |
| `tools/issue_env_contract_activation.py` | 237 (main) |  | `test_env_contract_activation.py` | 61 | `docs/calibration-freeze-authority-bundle-design.md`, `docs/env-contract-activation-prerequisites.md` |
| `tools/plotting/plot_a1_sized_paired.py` | 472 (main) | `test_plot_a1_sized_paired.py` (554) |  | 11 | `docs/paper-story/README.md`, `docs/paper-story/figures/README.md`, `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.provenance.json` … |
| `tools/plotting/plot_a2_certification.py` | 924 (main) | `test_plot_a2_certification.py` (1666) |  | 68 | `docs/paper-story/figures/README.md`, `docs/paper-story/figures/fig5_a2_certification_reject.provenance.json`, `docs/paper-story/figures/fig6_a2_certification_observed_positive.provenance.json` … |
| `tools/plotting/plot_b10_extended_backoff.py` | 1196 (main) | `test_plot_b10_extended_backoff.py` (424) | `test_b10_extended_figure_provenance.py` | 32 | `docs/paper-story/figures/README.md`, `docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json`, `docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` … |
| `tools/plotting/plot_b10_static_tail_formal.py` | 521 (main) | `test_plot_b10_static_tail_formal.py` (453) |  | 26 | `docs/paper-story/2026-09-17.md`, `docs/paper-story/README.md`, `docs/paper-story/figures/README.md` … |
| `tools/plotting/plot_dynamic_backoff.py` | 1852 (main) | `test_plot_dynamic_backoff.py` (1017) |  | 42 | `docs/dynamic-backoff-preregistration.md`, `tools/plotting/README.md` |
| `tools/plotting/plot_s1_9pair.py` | 1571 (main) |  | `test_official_perf_closure.py`, `test_s1_9pair_figure_provenance.py` | 34 | `docs/paper-story/figures/README.md`, `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json`, `tools/plotting/README.md` |
| `tools/plotting/plot_ss2pl_lock_study.py` | 837 (main) |  | `test_ss2pl_lock_study.py` | 9 | `tools/plotting/README.md` |
| `tools/plotting/plot_t2216_backoff_walk.py` | 908 (main) |  | `test_t2216_backoff_walk_model.py` | 4 | `tools/plotting/README.md` |
| `tools/s8b_budget_approval_preflight.py` | 235 (main) | `test_s8b_budget_approval_preflight.py` (563) |  | 12 | `docs/s8b-budget-approval-user-turn.md` |
| `tools/scan_env_coincidence.py` | 210 (main) | `test_scan_env_coincidence.py` (275) |  | 3 | `docs/test-environment-coincidence-ledger.md` |

### C — 完全一致の重複関数 (≥4 行、file 跨ぎ、test file を除く、docstring を除いた AST が関数名を除いて一致)

| # | 重複組 (file:関数 (行数)) | 1 本残して消せる行数 | 帰属 (path から機械付与) |
|---|---|---|---|
| C1 | `tools/check_ai_provenance.py:_sample_scope` (52) ↔ `tools/run_tests.py:_sample_scope` (52) | 52 | gate tool |
| C2 | `orchestrator/campaign/s6_sort_sweep.py:_rows_from_certified_view` (32) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_rows_from_certified_view` (32) | 32 | freeze / registry / 事前登録系 |
| C3 | `tools/t189_price_snapshot.py:_copy_json_value` (31) ↔ `tools/t189_task_catalog.py:_copy_json_value` (31) | 31 | その他 |
| C4 | `orchestrator/campaign/s6_sort_sweep.py:_replay_snapshot` (30) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_replay_snapshot` (30) | 30 | freeze / registry / 事前登録系 |
| C5 | `orchestrator/preregistration/addendum_envelope.py:_outside_fences` (29) ↔ `orchestrator/publication/approval_d291.py:_outside_fences` (27) ↔ `orchestrator/publication/report.py:_outside_fences` (27) | 54 | freeze / registry / 事前登録系, protected |
| C6 | `orchestrator/campaign/s3_lock_coverage.py:_build_broken` (28) ↔ `orchestrator/campaign/s5_permutation_coverage.py:_build_broken` (28) | 28 | coverage/verify (規律 2) |
| C7 | `orchestrator/campaign/s3_mocc_lock_coverage.py:_build_variant` (27) ↔ `orchestrator/campaign/s3_mocc_mutation_proof.py:_build_variant` (27) | 27 | coverage/verify (規律 2) |
| C8 | `tools/check_ai_provenance.py:_dispatch_timeout_overrides` (24) ↔ `tools/mutation_harness.py:_dispatch_timeout_overrides` (24) | 24 | gate tool |
| C9 | `orchestrator/campaign/pipeline.py:_read_exact_json` (23) ↔ `orchestrator/campaign/verify_fanout_worker.py:_read_exact_json` (21) | 21 | B-4 閉包 / core loop |
| C10 | `tools/check_ai_provenance.py:_stop_bounded_scope` (23) ↔ `tools/run_tests.py:_stop_bounded_scope` (23) | 23 | gate tool |
| C11 | `tools/plotting/plot_s1_9pair.py:_strict_json` (22) ↔ `tools/plotting/plot_t2216_backoff_walk.py:_strict_json` (22) | 22 | plotting |
| C12 | `orchestrator/campaign/p3_b4_analysis_contract.py:as_b4_exact_fraction` (21) ↔ `orchestrator/campaign/p3_b4_analysis_ledgers.py:_exact_ratio` (14) | 14 | freeze / registry / 事前登録系 |
| C13 | `orchestrator/campaign/backoff_counterfactual_analysis.py:_primary_decision` (20) ↔ `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:_primary_decision` (20) | 20 | B (test だけ) |
| C14 | `orchestrator/campaign/s6_sort_sweep.py:_replay_outcome` (18) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_replay_outcome` (18) | 18 | freeze / registry / 事前登録系 |
| C15 | `tools/check_ai_provenance.py:_scope_properties_are_enforced` (18) ↔ `tools/run_tests.py:_scope_properties_are_enforced` (18) | 18 | gate tool |
| C16 | `tools/check_ai_provenance.py:_scope_command` (8) ↔ `tools/mutation_fanout.py:_scope_command` (18) | 8 | gate tool |
| C17 | `orchestrator/preregistration/blobref.py:_git_env` (17) ↔ `orchestrator/submission_gate/_git.py:_git_env` (16) | 16 | freeze / registry / 事前登録系, protected |
| C18 | `tools/plotting/plot_s1_9pair.py:_atomic_json` (15) ↔ `tools/plotting/plot_t2187_adaptive_consts.py:_atomic_json` (17) ↔ `tools/plotting/plot_t2216_backoff_walk.py:_atomic_json` (17) | 32 | plotting |
| C19 | `orchestrator/campaign/reflux_origin_ledger.py:_git_env` (16) ↔ `tools/dev_waves/git_state.py:_git_env` (12) | 12 | freeze / registry / 事前登録系, その他 |
| C20 | `orchestrator/campaign/p3_s4_loop.py:_campaign_cfg_for_site` (15) ↔ `orchestrator/campaign/p3_s4_loop_trigger_gating.py:_campaign_cfg_for_site` (15) | 15 | B-4 閉包 / core loop |
| C21 | `orchestrator/campaign/patchharness.py:_read_only_git_env` (11) ↔ `orchestrator/campaign/source_digest.py:_sanitized_git_env` (11) ↔ `orchestrator/campaign/t1998_stock_inline_pair.py:_read_only_git_env` (15) | 22 | freeze / registry / 事前登録系, その他 |
| C22 | `tools/check_ai_provenance.py:_parse_unified_cgroup` (15) ↔ `tools/run_tests.py:_parse_unified_cgroup` (15) | 15 | gate tool |
| C23 | `orchestrator/campaign/backoff_counterfactual_analysis.py:_secondary_result` (14) ↔ `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:_secondary_result` (14) | 14 | B (test だけ) |
| C24 | `orchestrator/submission_gate/_attempt_authority.py:_freeze_json_value` (14) ↔ `orchestrator/submission_gate/_receipt_io.py:_freeze_json_value` (14) | 14 | B (test だけ), freeze / registry / 事前登録系 |
| C25 | `tools/check_ai_provenance.py:_load_login_headroom` (14) ↔ `tools/run_tests.py:_load_login_headroom` (14) | 14 | gate tool |
| C26 | `orchestrator/axis1_search/runner.py:_openalex_oqo` (12) ↔ `orchestrator/axis1_search/validator.py:_openalex_structure` (12) | 12 | freeze / registry / 事前登録系 |
| C27 | `orchestrator/campaign/s8b_floor_campaign.py:_floor_git_environment` (12) ↔ `orchestrator/campaign/sort_swo_dependency_material.py:_git_environment` (12) | 12 | freeze / registry / 事前登録系 |
| C28 | `tools/plotting/plot_t2187_adaptive_consts.py:_regularized_incomplete_beta` (12) ↔ `tools/size_paper_story_a1_balanced.py:_regularized_beta` (12) | 12 | plotting |
| C29 | `orchestrator/campaign/attempt_registry_core.py:_exact_keys` (11) ↔ `orchestrator/campaign/trial_registry.py:_exact_keys` (6) | 6 | freeze / registry / 事前登録系 |
| C30 | `orchestrator/campaign/backoff_overthrottle.py:_canonical_json_bytes` (11) ↔ `orchestrator/campaign/backoff_requested_us.py:_canonical_json_bytes` (11) | 11 | B (test だけ), freeze / registry / 事前登録系 |
| C31 | `orchestrator/campaign/floor_pair_driver.py:_canonical_bytes` (11) ↔ `orchestrator/campaign/p3_b4_wiring_probe.py:_canonical_bytes` (7) | 7 | B (test だけ), freeze / registry / 事前登録系 |
| C32 | `tools/codex_reasoning_ab.py:_file_identity` (9) ↔ `tools/t189_oracle_wiring_slice.py:_full_identity` (11) | 9 | その他 |
| C33 | `hooks/guard_bash.py:_string_values` (10) ↔ `hooks/guard_write.py:_string_values` (10) | 10 | protected |
| C34 | `orchestrator/campaign/s2_verify_calibration.py:_run_cmake_build` (10) ↔ `orchestrator/campaign/s3_lock_coverage.py:_run_cmake_build` (10) ↔ `orchestrator/campaign/s5_permutation_coverage.py:_run_cmake_build` (10) ↔ `orchestrator/campaign/s8a_trigger_coverage.py:_run_cmake_build` (10) | 30 | coverage/verify (規律 2) |
| C35 | `orchestrator/campaign/s8b_oracle_manifest.py:_mutable_json_tree` (10) ↔ `orchestrator/campaign/s8b_oracle_spec.py:_mutable_json_tree` (8) | 8 | freeze / registry / 事前登録系 |
| C36 | `tools/check_ai_provenance.py:_read_scope_events` (10) ↔ `tools/run_tests.py:_read_scope_events` (10) | 10 | gate tool |
| C37 | `tools/check_ai_provenance.py:_start_scope_sampler` (10) ↔ `tools/run_tests.py:_start_scope_sampler` (10) | 10 | gate tool |
| C38 | `tools/dev_wave_land.py:_same_inode` (10) ↔ `tools/dev_wave_wait.py:_same_inode` (10) | 10 | gate tool |
| C39 | `tools/size_paper_story_a1_balanced.py:_parser` (10) ↔ `tools/size_paper_story_a1_headline.py:_parser` (10) | 10 | plotting |
| C40 | `orchestrator/axis1_search/runner.py:_openalex_json_object` (9) ↔ `orchestrator/axis1_search/validator.py:_openalex_json_object` (9) | 9 | freeze / registry / 事前登録系 |
| C41 | `orchestrator/campaign/attempt_registry_core.py:_object_without_duplicate_keys` (9) ↔ `orchestrator/campaign/autonomous_trial_completeness.py:_object_without_duplicate_keys` (9) ↔ `orchestrator/campaign/trial_registry.py:_object_without_duplicate_keys` (9) ↔ `orchestrator/publication/ledger.py:_object_without_duplicate_keys` (9) | 27 | B (test だけ), freeze / registry / 事前登録系, その他 |
| C42 | `orchestrator/campaign/autonomous_trial_completeness.py:_arm_binding_digest` (9) ↔ `orchestrator/campaign/s8c_acceptance_receipt.py:_arm_binding_digest` (9) | 9 | freeze / registry / 事前登録系, その他 |
| C43 | `orchestrator/campaign/p3_s4_loop.py:_fsync_b4_consumption_directory` (9) ↔ `orchestrator/campaign/paper_story_a1_paired.py:_fsync_directory` (9) | 9 | B-4 閉包 / core loop, freeze / registry / 事前登録系 |
| C44 | `orchestrator/axis1_search/runner.py:_logical_query` (8) ↔ `orchestrator/axis1_search/validator.py:_logical_query` (8) | 8 | freeze / registry / 事前登録系 |
| C45 | `orchestrator/campaign/backoff_overthrottle.py:_flags` (8) ↔ `orchestrator/campaign/backoff_requested_us.py:_flags` (8) | 8 | B (test だけ), freeze / registry / 事前登録系 |
| C46 | `orchestrator/campaign/build_admission.py:_is_sha256` (8) ↔ `orchestrator/campaign/s8b_binary_admission.py:_is_sha256` (8) ↔ `orchestrator/campaign/source_digest.py:_is_sha256` (8) | 16 | freeze / registry / 事前登録系, その他 |
| C47 | `orchestrator/campaign/knowledge_manifest.py:canonical_json_bytes` (8) ↔ `tools/t1434_t1222_science_slice.py:canonical_bytes` (5) | 5 | B (test だけ), freeze / registry / 事前登録系 |
| C48 | `orchestrator/campaign/p3_b4_admission_record.py:_canonical_json_bytes` (8) ↔ `orchestrator/campaign/p3_b4_launcher.py:_canonical_json_bytes` (8) ↔ `orchestrator/campaign/s8c_preregistration.py:_canonical_bytes` (8) ↔ `orchestrator/campaign/s8c_result_judge.py:_canonical_json_bytes` (8) ↔ `orchestrator/codex_roles/spec.py:_canonical_json` (5) | 29 | freeze / registry / 事前登録系, その他 |
| C49 | `orchestrator/campaign/s1_known_axes_freeze.py:_load_json` (8) ↔ `orchestrator/campaign/s1_measurement_freeze.py:_load_json` (8) | 8 | freeze / registry / 事前登録系 |
| C50 | `orchestrator/campaign/s6_sort_sweep.py:_capability_resolver` (8) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_capability_resolver` (7) | 7 | freeze / registry / 事前登録系 |
| C51 | `orchestrator/submission_gate/_attempt_authority.py:_thaw_json_value` (8) ↔ `orchestrator/submission_gate/_receipt_schema.py:_thaw_json_value` (8) | 8 | B (test だけ), freeze / registry / 事前登録系 |
| C52 | `tools/check_ai_provenance.py:_attest_scope_oom_group` (8) ↔ `tools/run_tests.py:_attest_scope_oom_group` (8) | 8 | gate tool |
| C53 | `tools/mutation_harness.py:_path_present_fail_closed` (8) ↔ `tools/mutation_worktree.py:_path_present_fail_closed` (8) | 8 | gate tool, その他 |
| C54 | `tools/mutation_worktree.py:_git_env` (8) ↔ `tools/run_tests.py:_git_env` (7) | 7 | gate tool, その他 |
| C55 | `tools/size_paper_story_a1_balanced.py:runtime_contract` (5) ↔ `tools/size_paper_story_a1_headline.py:runtime_contract` (8) ↔ `tools/verify_paper_story_a1_balanced_sizing.py:runtime_contract` (5) ↔ `tools/verify_paper_story_a1_headline_sizing.py:runtime_contract` (8) | 18 | B (test だけ), freeze / registry / 事前登録系, plotting |
| C56 | `tools/size_paper_story_a1_balanced.py:_positive_int` (8) ↔ `tools/size_paper_story_a1_headline.py:_positive_int` (8) ↔ `tools/verify_paper_story_a1_balanced_sizing.py:_positive_arg` (8) ↔ `tools/verify_paper_story_a1_headline_sizing.py:_positive` (8) | 24 | B (test だけ), freeze / registry / 事前登録系, plotting |
| C57 | `tools/t189_oracle_wiring_slice.py:_relative_path` (8) ↔ `tools/t189_task_catalog.py:_relative_path` (8) | 8 | その他 |
| C58 | `orchestrator/axis1_search/checkpoint.py:_read_all` (7) ↔ `orchestrator/campaign/p3_b4_prerun_issuer.py:_read_all` (7) | 7 | freeze / registry / 事前登録系 |
| C59 | `orchestrator/campaign/attempt_registry_core.py:_text` (7) ↔ `orchestrator/campaign/trial_registry.py:_attempt_text` (4) | 4 | freeze / registry / 事前登録系 |
| C60 | `orchestrator/campaign/calibration_verify.py:_duplicate_object` (7) ↔ `orchestrator/campaign/env_attestation.py:_duplicate_object` (7) | 7 | その他 |
| C61 | `orchestrator/campaign/floor_job_checkpoint.py:_directory_flags` (7) ↔ `orchestrator/campaign/trial_registry.py:_directory_open_flags` (7) | 7 | freeze / registry / 事前登録系 |
| C62 | `orchestrator/campaign/mocc_trace_pair.py:_object_pairs` (7) ↔ `orchestrator/campaign/mocc_trace_pair_anchor.py:_object_pairs` (7) | 7 | B (test だけ), freeze / registry / 事前登録系 |
| C63 | `orchestrator/campaign/p3_b4_raw_record_producer.py:_json_pairs` (7) ↔ `orchestrator/campaign/s8c_arm_inputs.py:_object_without_duplicates` (7) | 7 | freeze / registry / 事前登録系 |
| C64 | `orchestrator/campaign/p3_s4_loop.py:_admit_env_contract` (7) ↔ `orchestrator/campaign/p3_s4_loop_trigger_gating.py:_admit_env_contract` (7) | 7 | B-4 閉包 / core loop |
| C65 | `orchestrator/campaign/paper_story_a2_certification.py:_fsync_dir` (6) ↔ `orchestrator/qualification/collector.py:_fsync_directory` (7) ↔ `tools/mutation_fanout.py:_sync_directory` (6) ↔ `tools/pegasus/probes/t139_r4_env_probe.py:_fsync_directory` (6) ↔ `tools/pegasus/probes/t316_sandbox_backend_probe.py:_fsync_directory` (6) | 24 | freeze / registry / 事前登録系, gate tool, その他 |
| C66 | `orchestrator/campaign/s6_proposal_rounds.py:fisher_one_sided_p` (5) ↔ `orchestrator/campaign/s6_proposal_rounds_power.py:fisher_one_sided_p` (7) | 5 | その他 |
| C67 | `orchestrator/campaign/s6_sort_sweep.py:_load_certified_rows` (7) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_load_certified_rows` (7) | 7 | freeze / registry / 事前登録系 |
| C68 | `orchestrator/campaign/s8b_binary_admission.py:_plain_json` (7) ↔ `orchestrator/campaign/s8b_sort_swo_receipt.py:_plain_json` (6) | 6 | freeze / registry / 事前登録系 |
| C69 | `tools/dev_wave_wait.py:_no_duplicate_keys` (7) ↔ `tools/wave_land_window.py:_no_duplicate_keys` (7) | 7 | gate tool, その他 |
| C70 | `tools/mutation_harness.py:_refusing_local_site` (7) ↔ `tools/mutation_worktree.py:_refusing_local_site` (7) | 7 | gate tool, その他 |
| C71 | `tools/pegasus/dispatch_compute.py:_canonical_json_text` (6) ↔ `tools/pegasus/probes/t293_perf_site_probe.py:_encode` (7) | 6 | その他 |
| C72 | `tools/plotting/plot_s1_9pair.py:_bbox_contains` (7) ↔ `tools/plotting/plot_t2187_adaptive_consts.py:_contains` (7) ↔ `tools/plotting/plot_t2216_backoff_walk.py:_contains` (5) | 12 | plotting |
| C73 | `tools/size_paper_story_a1_balanced.py:_no_duplicate_keys` (7) ↔ `tools/size_paper_story_a1_headline.py:_no_duplicate_keys` (7) | 7 | plotting |
| C74 | `tools/size_paper_story_a1_balanced.py:_root_seed_policy` (7) ↔ `tools/size_paper_story_a1_headline.py:_root_seed_policy` (7) ↔ `tools/verify_paper_story_a1_headline_sizing.py:_root_seed_policy` (7) | 14 | freeze / registry / 事前登録系, plotting |
| C75 | `tools/verify_paper_story_a1_balanced_sizing.py:_unique` (7) ↔ `tools/verify_paper_story_a1_headline_sizing.py:_unique_object` (7) | 7 | B (test だけ), freeze / registry / 事前登録系 |
| C76 | `orchestrator/campaign/attempt_registry_core.py:_digest` (6) ↔ `orchestrator/campaign/trial_registry.py:_attempt_digest` (6) | 6 | freeze / registry / 事前登録系 |
| C77 | `orchestrator/campaign/mutation_attempt_marker.py:_path_within` (6) ↔ `orchestrator/campaign/p3_b4_wiring_probe.py:_is_relative_to` (6) ↔ `tools/dev_wave_wait.py:_is_within` (6) ↔ `tools/mutation_fanout.py:_within` (6) ↔ `tools/mutation_harness.py:_path_within` (6) ↔ `tools/mutation_worktree.py:_path_within` (6) ↔ `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:_is_within` (6) | 36 | B (test だけ), gate tool, その他 |
| C78 | `orchestrator/campaign/p3_b4_analysis_adapter.py:_is_sha256` (6) ↔ `orchestrator/campaign/p3_b4_analysis_contract.py:_is_sha256` (6) ↔ `orchestrator/campaign/p3_b4_analysis_ledgers.py:_is_sha256` (6) ↔ `orchestrator/campaign/p3_b4_prerun_issuer.py:_is_sha256` (6) ↔ `orchestrator/campaign/p3_b4_producer_auth_experiment.py:_is_sha256` (6) | 24 | B (test だけ), freeze / registry / 事前登録系 |
| C79 | `orchestrator/campaign/p3_b4_material_report.py:_is_relative_to` (6) ↔ `orchestrator/campaign/paper_story_a1_paired.py:_is_within` (6) ↔ `tools/acceptance_shards.py:_is_within` (6) | 12 | freeze / registry / 事前登録系, その他 |
| C80 | `orchestrator/campaign/p3_b4_wiring_probe.py:_sha256_file` (6) ↔ `tools/check_codex_hooks.py:_sha256` (6) ↔ `tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:_sha256_file` (6) | 12 | B (test だけ), その他 |
| C81 | `orchestrator/campaign/p3_kickoff.py:_perf` (6) ↔ `orchestrator/campaign/p3_s4_loop.py:default_perf` (6) ↔ `orchestrator/campaign/p3_s4_red.py:_perf` (5) | 11 | B-4 閉包 / core loop, その他 |
| C82 | `orchestrator/campaign/paper_story_a1_paired.py:_sha256_file` (6) ↔ `orchestrator/campaign/t1998_stock_inline_pair.py:_sha256_file` (6) | 6 | freeze / registry / 事前登録系 |
| C83 | `orchestrator/campaign/s3_mocc_lock_coverage.py:_sha256_file` (6) ↔ `tools/pegasus/probes/t139_r4_env_probe.py:_sha256_file` (6) ↔ `tools/pegasus/probes/t316_sandbox_backend_probe.py:_sha256_file` (6) ↔ `tools/pegasus/run_acceptance_nproc_study.py:_sha256_file` (6) ↔ `tools/pegasus/run_ss2pl_lock_study.py:sha256_file` (6) ↔ `tools/plotting/plot_ss2pl_lock_study.py:sha256_file` (6) | 30 | coverage/verify (規律 2), plotting, その他 |
| C84 | `orchestrator/campaign/s8b_compiler_input.py:_is_sha256` (6) ↔ `orchestrator/campaign/s8b_expected_materialization.py:_is_sha256` (6) ↔ `orchestrator/campaign/trigger_gate_binding.py:_is_lower_hex_64` (6) | 12 | freeze / registry / 事前登録系, その他 |
| C85 | `orchestrator/campaign/s8b_holdout_admission.py:_fsync_directory` (6) ↔ `orchestrator/campaign/s8b_prediction_runner.py:_fsync_directory` (6) ↔ `orchestrator/campaign/s8c_result_judge.py:_sync_directory` (6) | 12 | freeze / registry / 事前登録系 |
| C86 | `orchestrator/qualification/artifacts.py:_fsync_dir` (6) ↔ `orchestrator/qualification/atomic_publish.py:_fsync_directory` (6) | 6 | freeze / registry / 事前登録系 |
| C87 | `tools/plotting/plot_b10_extended_backoff.py:_sha256` (6) ↔ `tools/plotting/plot_t2266_tail_mechanism.py:_sha256` (6) | 6 | plotting |
| C88 | `tools/check_ai_provenance.py:_print_granted_budget` (6) ↔ `tools/run_tests.py:_print_granted_budget` (6) | 6 | gate tool |
| C89 | `tools/pegasus/probes/t293_perf_site_probe.py:_sha256` (6) ↔ `tools/pegasus/probes/t419_probe_causality.py:_sha256_path` (6) | 6 | その他 |
| C90 | `tools/plotting/plot_s1_9pair.py:_bbox_intersection_area` (6) ↔ `tools/plotting/plot_t2187_adaptive_consts.py:_intersection_area` (6) | 6 | plotting |
| C91 | `tools/t1434_t1222_science_slice.py:_object` (6) ↔ `tools/t189_oracle_wiring_slice.py:_object` (6) | 6 | B (test だけ), その他 |
| C92 | `tools/t189_price_snapshot.py:_object` (6) ↔ `tools/t189_task_catalog.py:_object` (6) | 6 | その他 |
| C93 | `orchestrator/campaign/backoff_counterfactual_analysis.py:_matches_exact` (5) ↔ `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:_matches_exact` (5) ↔ `orchestrator/campaign/backoff_policy_performance_analysis.py:_matches_exact` (5) | 10 | B (test だけ) |
| C94 | `orchestrator/campaign/buildcache.py:_ccbench_dir` (5) ↔ `orchestrator/campaign/patchharness.py:_default_ccbench_dir` (4) ↔ `orchestrator/campaign/source_digest.py:_ccbench_dir` (4) | 8 | その他 |
| C95 | `orchestrator/campaign/mocc_trace_pair.py:_sha256` (5) ↔ `orchestrator/campaign/mocc_trace_pair_anchor.py:_sha256` (5) | 5 | B (test だけ), freeze / registry / 事前登録系 |
| C96 | `orchestrator/campaign/pipeline.py:_canonical_json_bytes` (5) ↔ `orchestrator/campaign/verify_fanout_worker.py:_canonical_json_bytes` (5) | 5 | B-4 閉包 / core loop |
| C97 | `orchestrator/campaign/s6_sort_sweep.py:perf_for` (5) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:perf_for` (5) | 5 | freeze / registry / 事前登録系 |
| C98 | `tools/check_ai_provenance.py:_read_scope_current` (5) ↔ `tools/run_tests.py:_read_scope_current` (5) | 5 | gate tool |
| C99 | `tools/collect_wave_usage.py:_absolute_path` (5) ↔ `tools/s8b_budget_approval_preflight.py:_absolute_path` (5) | 5 | B (test だけ) |
| C100 | `tools/mutation_fanout_contract.py:_compact_sha256` (5) ↔ `tools/mutation_harness.py:_json_sha256` (5) | 5 | gate tool, その他 |
| C101 | `tools/size_paper_story_a1_balanced.py:certification_condition_alpha` (4) ↔ `tools/size_paper_story_a1_headline.py:certification_condition_alpha` (5) | 4 | plotting |
| C102 | `tools/t189_oracle_wiring_slice.py:_digest` (5) ↔ `tools/t189_task_catalog.py:_digest` (5) | 5 | その他 |
| C103 | `orchestrator/axis1_search/runner.py:_get` (4) ↔ `orchestrator/axis1_search/validator.py:_get` (4) | 4 | freeze / registry / 事前登録系 |
| C104 | `orchestrator/axis1_search/validator.py:_worktree_bytes` (4) ↔ `orchestrator/axis_b5_search/preflight.py:_worktree_bytes` (4) | 4 | freeze / registry / 事前登録系, その他 |
| C105 | `orchestrator/campaign/backoff_counterfactual_analysis.py:_sha256` (4) ↔ `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:_sha256` (4) | 4 | B (test だけ) |
| C106 | `orchestrator/campaign/backoff_counterfactual_analysis.py:_exact_int` (4) ↔ `orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:_exact_int` (4) ↔ `orchestrator/campaign/backoff_nonmonotonicity_analysis.py:_exact_int` (4) | 8 | B (test だけ) |
| C107 | `orchestrator/campaign/mocc_trace_pair.py:_dict` (4) ↔ `orchestrator/campaign/mocc_trace_pair_anchor.py:_dict` (4) | 4 | B (test だけ), freeze / registry / 事前登録系 |
| C108 | `orchestrator/campaign/s6_sort_sweep.py:_preflight_condition_gate` (4) ↔ `orchestrator/campaign/s8a_trigger_sweep.py:_preflight_condition_gate` (4) | 4 | freeze / registry / 事前登録系 |
| C109 | `orchestrator/campaign/s8b_oracle_judge.py:_write_create_only` (4) ↔ `orchestrator/campaign/s8b_oracle_report.py:_write_create_only` (4) ↔ `orchestrator/campaign/s8b_verdict.py:_write_create_only` (4) | 8 | B (test だけ), freeze / registry / 事前登録系 |
| C110 | `orchestrator/submission_gate/_binding.py:_commit` (4) ↔ `orchestrator/submission_gate/_git.py:_require_commit_id` (4) | 4 | freeze / registry / 事前登録系 |
| C111 | `tools/acceptance_launcher.py:_normalize_child_rc` (4) ↔ `tools/dev_wave_wait.py:_normalize_child_rc` (4) | 4 | gate tool, その他 |
| C112 | `tools/dev_wave_land.py:_land_fold_date` (4) ↔ `tools/spool_fold.py:_current_fold_date` (4) | 4 | gate tool |
| C113 | `tools/dev_waves/daemon.py:_utc_now` (4) ↔ `tools/dev_waves/ledger.py:_utc_now` (4) | 4 | その他 |
| C114 | `tools/plotting/plot_a1_sized_paired.py:_figure_number` (4) ↔ `tools/plotting/plot_b10_static_tail_formal.py:_figure_number` (4) | 4 | plotting |
| C115 | `tools/plotting/plot_dynamic_backoff.py:_string` (4) ↔ `tools/plotting/plot_t2187_adaptive_consts.py:_string` (4) | 4 | plotting |
| C116 | `tools/size_paper_story_a1_balanced.py:_decimal` (4) ↔ `tools/size_paper_story_a1_headline.py:_decimal` (4) | 4 | plotting |
| C117 | `tools/t1434_t1222_science_slice.py:_text` (4) ↔ `tools/t189_oracle_wiring_slice.py:_string` (4) | 4 | B (test だけ), その他 |
| C118 | `tools/t189_oracle_wiring_slice.py:_integer` (4) ↔ `tools/t189_task_catalog.py:_int` (4) | 4 | その他 |

組数 = 118、うち最長 15 行以上 = 22 組。各組で最長の 1 本を残し他を消した場合の単純合計 = 1429 行 (15 行以上の組だけなら 534 行)。import の追加行や意味論の差 (module global 依存など) は考慮しない単純計算。

帰属別の組数: freeze / registry / 事前登録系 26, gate tool 14, その他 12, plotting 12, B (test だけ), freeze / registry / 事前登録系 12, freeze / registry / 事前登録系, その他 8, B (test だけ) 6, gate tool, その他 6, B-4 閉包 / core loop 4, coverage/verify (規律 2) 3, B (test だけ), その他 3, freeze / registry / 事前登録系, protected 2, B (test だけ), freeze / registry / 事前登録系, plotting 2, protected 1, B (test だけ), freeze / registry / 事前登録系, その他 1, B-4 閉包 / core loop, freeze / registry / 事前登録系 1, freeze / registry / 事前登録系, gate tool, その他 1, freeze / registry / 事前登録系, plotting 1, B (test だけ), gate tool, その他 1, B-4 閉包 / core loop, その他 1, coverage/verify (規律 2), plotting, その他 1

### 対象外 (protected: verifier / calibrator / hooks / preregistration、36 file / 16033 行)

`hooks/guard_agent.py`, `hooks/guard_bash.py`, `hooks/guard_read.py`, `hooks/guard_write.py`, `orchestrator/calibrate.py`, `orchestrator/calibrator/__init__.py`, `orchestrator/calibrator/__main__.py`, `orchestrator/calibrator/analyze.py`, `orchestrator/calibrator/benchparse.py`, `orchestrator/calibrator/cli.py`, `orchestrator/calibrator/effective_clock_policy.py`, `orchestrator/calibrator/model.py`, `orchestrator/calibrator/perf_preflight.py`, `orchestrator/calibrator/perfparse.py`, `orchestrator/calibrator/report.py`, `orchestrator/calibrator/runner.py`, `orchestrator/calibrator/schema_v2.py`, `orchestrator/calibrator/stability.py`, `orchestrator/calibrator/sweep.py`, `orchestrator/calibrator/tsc.py`, `orchestrator/preregistration/__init__.py`, `orchestrator/preregistration/addendum_envelope.py`, `orchestrator/preregistration/approval_payload.py`, `orchestrator/preregistration/blobref.py`, `orchestrator/preregistration/erratum.py`, `orchestrator/preregistration/stress_check_simulation.py`, `orchestrator/verifier/__init__.py`, `orchestrator/verifier/__main__.py`, `orchestrator/verifier/cli.py`, `orchestrator/verifier/commit_receipt.py`, `orchestrator/verifier/core.py`, `orchestrator/verifier/dsg.py`, `orchestrator/verifier/model.py`, `orchestrator/verifier/parse.py`, `orchestrator/verifier/report.py`, `orchestrator/verify.py`

### 集計 (probe の区分そのまま)

| 区分 | file | 行 |
|---|---|---|
| B-test-only | 29 | 21600 |
| B-test-only+docs-op | 19 | 15216 |
| D-docs-hist-only | 6 | 679 |
| docs-op-only | 1 | 65 |
| live | 332 | 396272 |
| live?-weak-prod-string | 2 | 93 |
| protected | 36 | 16033 |
| test | 394 | 596597 |



## 4. 実装 (本 wave で行った変更)

- **C8 統合 (実装済み、commit `18736b502`)**: `tools/check_docs.py` の `_mask_html_comments` 定義 (27 行 + 空行 2 行) を削除し、既存の `from dev_waves.launch_authority import (…)` へ `_mask_html_comments,` を追加。差分は 1 file、+1 / −29 行。author 子 (Codex gpt-6-astra、medium) が AST で関数範囲を取り、2 本の nonblank bytes が 912 == 912 で一致することを確認してから削除した。呼出し 2 箇所 (`check_docs.py` の dispatch 可視行抽出と fence 検査) は名前・引数不変。段 6 review も `git show 18736b502` と `launch_authority.py:126–151` を独立に照合し、意味論同一・循環 import なし・check_docs 自身の bytes / 行番号 pin なし (`test_check_docs.py:1250–1270` の fixture は checker を複製して定数を置換する形) を確認した。
- 親の実測: `python3 tools/check_docs.py` rc=0 (違反なし)。焦点走 `tools/run_tests.py -q -rf orchestrator/tests/test_check_docs.py orchestrator/tests/test_dev_wave_launch_authority.py` = 644 passed / 3 skipped (計算ノード dispatch、request 11156.nqsv、Elapse 19 秒、2026-09-19 23:22 JST)。全史 provenance 監査 `tools/check_ai_provenance.py` = 11,635 件、新規違反なし (rc=0)。
- **A の削除は行っていない** (0 件になったため)。author 子は「参照 0 件」の前提が崩れた時点で削除を保留し C8 だけ実装した (prompt の fail-closed 指示どおり)。
- 削減行数 = 純減 28 行 (`git diff --shortstat 8fd1eecf9..18736b502`: 1 file changed, 1 insertion(+), 29 deletions(-))。依頼が想定した規模 (one-off script の削除) には届かない。理由は §2 のとおり、未参照の module が実測 0 件で、one-off script はすべて自分の test が import している (B) ため。

## 5. 裁定パッケージ (ユーザー裁定待ち、本 wave では変更しない)

各項は 1 語 (a / b / c) で答えられるよう、対象集合を固定して書く。「問わない」は推奨どおりに扱い、異論があるときだけ答える項。

### R1 — D の 6 file (679 行) を削除するか

対象集合 (固定): `orchestrator/campaign/p2_5.py` (167)、`orchestrator/campaign/s6_amendment_20260713_fence.py` (117)、`orchestrator/manual_probes/t1994_capdrop_probe.py` (99)、`orchestrator/manual_probes/t1994_rootview_probe.py` (100)、`orchestrator/manual_probes/t1994_seccomp_probe.py` (96)、`orchestrator/manual_probes/t1994_readonly_snapshot_liveness.py` (100)。

- 参照元はすべて歴史記録: `p2_5.py` は `docs/decisions.md` (D21 周辺) と `docs/archive/*` 2 本と insight 1 本、`s6_amendment_*` は archive 1 本と insight 逐語 2 本、T-1994 の probe 4 本は `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv` / `reach_all.tsv` (Codex worktree 撤去監査の到達性台帳: path・blob sha・着地状態の表) と、`t1994_readonly_snapshot_liveness.py` だけ `output/insights/2026-09-14/t1994-readonly-snapshot/verbatim/login-node-probe.txt`。
- 択: **(a) 6 本とも削除し、歴史記録の参照はそのまま残す** (参照先の無い file 名が記録に残るが、記録は測定時点の事実 — 規律 7)。**(b) 残す。** (archive dir へ移す案は、Python として import 不能な置き場を新設することになり「新 framework」に近いので択に入れない。)
- 推奨 = **(a)**。理由: 6 本とも一回限りの driver / probe で、結果は insight と成果物に固定済み、再実行の予定がない。[T-2276] が p2_5 / s6_amendment を「test から一度も名指しされない」として carry 中。(a) なら次 wave で Codex author が削除する (実装面)。やらない理由の最も強い形: 到達性台帳が「現在の main に blob が存在する」ことを前提に読まれる場合、削除後は台帳の `LANDED-CURRENT` 行が現状と食い違う (台帳自体は当時の事実として有効)。

### R2 — `orchestrator/campaign/s6_proposal_rounds_power.py` (65 行、docs-op-only)

- 参照元は事前登録文書 `docs/phase3-main-experiment.md:201` (「検定力 (厳密計算・全数総和 = 本 file)」) だけ。test からは名指しされない ([T-2276] の 3 本目)。
- 推奨 = **残す (問わない)**。事前登録の producer は依頼の対象外条件に当たる。[T-2276] の本項は「名指しされないが事前登録 producer として残す」で閉じる。

### R3 — B1 のうち一回限りの解析・probe・移行 tool 17 対 (module 15,606 行 + 専用 test) を対で削除するか

対象集合 (固定、module → 参照する test):
`backoff_counterfactual_analysis.py` (694 → test_backoff_counterfactual_analysis.py 662)、`backoff_counterfactual_cohort2_analysis.py` (786 → test_backoff_counterfactual_cohort2_analysis.py 661、test_t2187_adaptive_const_probe.py が名指し)、`backoff_nonmonotonicity_analysis.py` (1,365 → test_backoff_nonmonotonicity_analysis.py 808)、`backoff_requested_us.py` (1,262 → test_backoff_requested_us.py 1,221、test_ccbench_spawn_sites.py・test_p3_build_authority_cli.py が名指し)、`backoff_sweep_report.py` (219 → test_backoff_consumers.py 513)、`floor_liveness.py` (926 → test_pegasus_floor_tools.py 8,648 の一部、test_ccbench_spawn_sites.py が名指し)、`mocc_g2_repro_ledger.py` (926 → test_mocc_g2_repro_ledger.py 622)、`mocc_trace_pair_anchor.py` (721 → test_mocc_trace_pair.py 5,618 の一部、test_ccbench_spawn_sites.py が名指し)、`s6_canary_rename.py` (312 → test_ccbench_spawn_sites.py の pin 行 3 本だけ)、`manual_probes/t1994_readonly_snapshot_qualification.py` (961 → test_buildcache_v2.py 6,407 の一部)、`tools/check_silo_validation_isolation.py` (1,501 → test_silo_validation_isolation.py 612)、`tools/insights_date_layout.py` (411 → test_insights_date_layout.py 447、一回限りの日付別移行)、`tools/migrate_output_gzip.py` (885 → test_migrate_output_gzip.py 473、移行済み)、`tools/mutation_fanout.py` (1,893 → test_mutation_fanout.py 1,039、変異 harness の N-shard fan-out driver。dev-wave 契約・runbook に記載なし、歴史記録 66 file)、`tools/plotting/plot_t2266_tail_mechanism.py` (625 → test_plot_t2266_tail_mechanism.py 505)、`tools/t1434_t1222_science_slice.py` (1,282 → test_t1434_t1222_science_slice.py 521)、`tools/verify_paper_story_a1_balanced_sizing.py` (837 → test_paper_story_a1_balanced_sizing.py 394)。

- 択: **(a) 17 対を専用 wave で一括削除** (module + 専用 test + 共有 test の pin 行。受理集合が変わるので敵対検証子付き)。**(b) 残す。** **(c) 一部** (残す module を名指し)。
- 推奨 = **(a)**。理由: いずれも結果が insight / 成果物 / 図に固定済みで、runbook・dev-wave 契約・事前登録文書のどれも名指ししない。やらない理由の最も強い形: `mutation_fanout.py` と `floor_liveness.py` は運用 tool として AI session が記憶から使いうる (文書には無い) — (c) でこの 2 本を残す択が最も安全。共有 test (`test_ccbench_spawn_sites.py`・`test_campaign.py` の spawn-site pin 表、`test_buildcache_v2.py`) の該当行は同じ commit で落とす。

### R4 — B1 のうち凍結・gate 側の 12 module (5,994 行) は残す (問わない)

対象集合 (固定): `p3_b4_prerun_caller.py`、`p3_b4_producer_auth_experiment.py`、`s8b_oracle_exploration.py`、`s8c_gate_report.py`、`orchestrator/publication/addendum_p_envelope.py`、`orchestrator/publication/ledger.py`、`orchestrator/submission_gate/_attempt_authority.py`、`orchestrator/submission_gate/_writer.py`、`tools/acceptance_issuer_reference.py` (署名の参照実装)、`tools/check_subprocess_bytecode_guard.py` (guard の検査)、`tools/hold_inventory.py`・`tools/update_acceptance_duration_ledger.py` (台帳 tool)。

- 「test だけが参照」でも役割が凍結成果物・gate・台帳側なので、依頼の対象外条件に準じて残す。削除したい module があれば名指しで答える。

### R5 — C の最大の組 (gate tool 3 本の scope 系 helper、統合で約 150 行減) を専用 wave にするか

- 対象: `tools/run_tests.py` ↔ `tools/check_ai_provenance.py` の `_sample_scope` (52)・`_stop_bounded_scope` (23)・`_scope_properties_are_enforced` (18)・`_parse_unified_cgroup` (15)・`_load_login_headroom` (14) = 122 行、`_dispatch_timeout_overrides` (24) ↔ `tools/mutation_harness.py`、`_scope_command` ↔ `tools/mutation_fanout.py`。
- 事実: `orchestrator/tests/test_check_ai_provenance.py:6135–6137,6168–6171` は 2 実装の判定を**固定期待値**と比較する (統合しても恒真にはならない — 段 6 review の訂正)。private 名の `monkeypatch.setattr` は provenance 側 6 箇所 + `test_run_tests_preflight.py:1972,2007,2034,2063,2116,2153` の 6 箇所 + `test_run_tests_task_run.py:430` の 1 箇所 = 13 箇所で、共有 module へ移すと patch 先の付け替えが要る。受入 runner・provenance 監査・変異 harness の 3 gate を同時に触る。
- 択: **(a) 専用 wave を立てる** (brief → plan → consult 付き、置き場は `tools/pegasus/dispatch_compute.py` の隣か新 module、test の patch 先 13 箇所を付け替え)。**(b) 見送り。**
- 推奨 = **(b)**。理由: 削減 約 150 行に対し gate 3 本の同時改修と test 13 箇所の付け替えで、研究の前進に効かない (研究最優先・プロトタイプ基準)。やらない理由の最も強い形: 3 本が黙って乖離する事故 (login scope の判定が tool ごとに違う) を今後防げるのは統合だけで、parity test は 2 本の乖離しか検出しない。

### R6 — C の小さい統合可能組 (plotting 3 組 + t189 2 組、単純合計 約 90 行) をどう扱うか

- 対象: `tools/plotting/plot_s1_9pair.py` ↔ `plot_t2216_backoff_walk.py` の `_strict_json` (22)、同 2 本 + `plot_t2187_adaptive_consts.py` の `_atomic_json` (15–17)、`plot_t2187_adaptive_consts.py:_regularized_incomplete_beta` ↔ `tools/size_paper_story_a1_balanced.py:_regularized_beta` (12)、`tools/t189_price_snapshot.py` ↔ `t189_task_catalog.py` の `_copy_json_value` (31)・`_object` (6)。
- 事実: `tools/plotting/README.md:72–83` は既存生成器の再利用を認め、`plot_b10_extended_backoff.py:30` が実際に別の生成器を import している (「自己完結」は同 README:139, 170 の特定 2 生成器の説明で、全体規約ではない — 段 6 review の訂正)。図 provenance (`docs/paper-story/figures/*.provenance.json`) は生成時の generator source sha を記録するだけで、現行 file と照合する test は無い (pin 閉包 hit 0)。`_copy_json_value` は module global (`_fail`) に依存し、AST 一致だけでは移設後の意味論を保証しない。
- 択: **(a) 次にその file を触る wave へ相乗り** (単独 wave は立てない)。**(b) 今すぐ専用 wave。** **(c) 見送り。**
- 推奨 = **(a)**。

### R7 — C の残り (freeze / registry / 事前登録系、coverage / verify 系、B-4 閉包 / core loop、protected、4〜14 行の小物) は見送り (問わない)

- 組ごとの帰属は §3 の C 表の「帰属」列 (path から機械付与) に出した。見送り理由は帰属ごと:
  - **freeze / registry / 事前登録系**: 依頼の対象外条件。加えて `orchestrator/campaign/t080_freeze_migration.py:91–102` は `s6_sort_sweep.py`・`s8a_trigger_sweep.py` 等の **source hash の表**を持ち、`s8c_preregistration.py:2006–2025` は core bytes と依存 module identity を検査し、`reflux_origin_ledger.py:114–120` は自前の hash / JSON helper を持つ。これらの module で helper を共有 module へ移すと、pin 済み source hash の更新か「hash 不変で挙動が変わりうる」経路のどちらかを作る (閉包の設計ごとに評価が要り、一括では決められない)。
  - **coverage / verify 系** (`s3_lock_coverage.py:68–74` が verifier の certify 側と coverage assertion の負例を分離): 規律 2 の正例・負例を作る側で、verifier と同じ扱い。
  - **B-4 閉包 / core loop** (`p3_s4_loop*`、`pipeline.py` ↔ `verify_fanout_worker.py`): `orchestrator/tests/test_p3_b4_wiring_probe.py:327` が閉包の module 数を pin (現在 47) し、`p3_b4_wiring_probe.py:965–976` が import 時の副作用 (`.start` 呼出し等) を拒否する。既存閉包内の import 辺なら件数は増えないが、15〜23 行のために core loop を触らない。
  - **protected**: verifier / calibrator / hooks / preregistration。
  - **小物 (4〜14 行)**: import 行の追加と相殺し、多くが freeze 系。
- 同名だが本体が異なる関数 (例: `_sha256` 12 module、`_canonical_json_bytes` 15 module、`_git` 15 module、`_strict_json` 9 module) は機械的に統合できないので候補に入れない (一覧は job dir の `inventory.md` §same-name)。

### R8 — [T-2276] の扱い (問わない)

- carry 項目「`orchestrator/campaign/` の 186 module のうち `p2_5.py`、`s6_amendment_20260713_fence.py`、`s6_proposal_rounds_power.py` の 3 本が test suite から一度も名指しされない」は本 wave の全数走査で再確認した (前 2 本は D、3 本目は docs-op-only)。R1 が (a) なら削除 wave で、R2 と合わせて閉じる。

## 6. 変異台帳・受入

### 6.1 変異台帳 (DW-M01〜M08)

- 対象: C8 の統合だけが挙動を持つ実装面。削除は 0 件 (A が空) なので削除側の変異は登録しない。
- M1 = `tools/dev_waves/launch_authority.py:_mask_html_comments` の本体先頭 (`visible: list[str] = []` の直前) へ `return line, False` を挿入 (HTML comment を一切 mask しない)。置換対象は 1 箇所 (anchor_counts `{"0": 1}`)。統合後、mask を行う層はこの 1 箇所だけ (check_docs 側の `_dispatch_visible_markdown_lines` は authority への委譲、`check_docs.py:4907–4912` の inline code 内 delimiter 拒否は別入力の検査 — 段 6 review の確認)。
- harness: `tools/mutation_worktree.py` (独立 clone `mutation-source`、main = 18736b502、D1009) → `tools/mutation_harness.py` (dispatch、`--force-dispatch`)。runner = `tools/run_tests.py -q -rf orchestrator/tests/test_check_docs.py orchestrator/tests/test_dev_wave_launch_authority.py`。spec sha256 `f0e90014c5fb8597…`、tool `186490af92835bd3…`、runner `44058b18cd7b2fee…`。
- **初回は probe** (DW-M08 の erratum): 期待 node の完全集合を事前に確定できなかったので、`expected_status: SURVIVED`・`expected_nodes: []` の probe spec (`mutations-probe.json`、sha256 `2bec96a354ed82f7…`) で走らせ、観測 node を集めた。結果 = baseline PASSED (rc 0、222.0 秒、queue 込み)、M1 は `test_check_docs.py` の 14 node が赤 (rc 1、38.0 秒) で status MISMATCH (probe 設計どおり)。2026-09-19 23:35〜23:42 JST。
- **本走**: 観測した 14 node を `expected_nodes` に固定し `expected_status: KILLED` で再登録 (`mutations.json`)。結果 = baseline PASSED (rc 0、644 passed / 3 skipped、37.8 秒、request 11261.nqsv)、**M1 KILLED** (rc 1、failed 14 == expected 14、完全一致、37.6 秒、request 11265.nqsv)。harness rc=0。投入 23:45 JST、queue 待ち (11225.nqsv が PRR のまま約 15 分) を経て 2026-09-20 00:04 JST 完了。
- 赤になった 14 node (全部 `orchestrator/tests/test_check_docs.py`): `test_dev_wave_reasoning_effort_pin_production_path_rejects_hidden_s06_a_exact`、`test_backlog_guard_fences_and_multiline_comment_do_not_satisfy_sink`、`test_backlog_guard_hidden_ledger_items_are_not_live_items`、`test_backlog_guard_hidden_ledger_items_do_not_satisfy_sink`、`test_command_docs_guard_positive_controls[single_dispatch_agents_comment_decoy]`、`test_command_docs_guard_positive_controls[single_dispatch_operations_comment_decoy]`、`test_provenance_dispatch_table_structure_is_exact[header-hidden-…]`、`test_inline_code_comment_delimiter_is_rejected_fail_closed`、`test_admission_projection_mutations_each_have_one_primary_finding`、`test_fence_inside_html_comment_does_not_mask_following_h2`、`test_dev_wave_layer_slicing_ignores_fenced_heading[html-comment]`、`test_html_commented_provenance_dispatch_table_is_not_visible`、`test_dev_wave_reasoning_effort_pins_ignore_comment_and_fence_examples`、`test_dev_wave_reasoning_effort_pin_rejects_hidden_whole_s06_sections`。`test_dev_wave_launch_authority.py` 側は赤にならない (同 file の test は `_mask_html_comments` を直接検査しない)。
- 読み: check_docs の HTML comment 依存の検査 14 本が、統合後は `launch_authority._mask_html_comments` を経由して判定していることを示す (kill は受理集合の変化で数えた。DW-M03)。author 子の login 上の `python3 tools/check_docs.py` (現行 docs への lint) は同じ変異で緑のままだった = 現行 docs に「HTML comment で隠した見出し」が無いだけで、検査自体の実効性は上の 14 node が担う。
- 原本: `mutation-probe-results.json`、`mutation-results.json`、`mutation-attempt1.json`、dispatch evidence (`mutation-results.json.dispatch-evidence/`)。

### 6.2 受入全走

- 本書を含む記録 commit の後、land 対象 tip へ `tools/dev_wave_wait.py acceptance` (計算ノード dispatch、`-- python3 tools/run_tests.py`) を投入する。本書の commit 時点では**未実施**。結果 (child-green 受領証、tested main / tip、所要) の原本は job dir の `acceptance-receipt-*.json` と `acceptance-*.chain.log` に残り、land 後の worklog エントリ (fold が描画) から辿る。本書へは追記しない (受領証と tip を一致させるため)。
- 焦点走 (記録前): `test_check_docs.py` + `test_dev_wave_launch_authority.py` = 644 passed / 3 skipped (request 11156.nqsv、Elapse 19 秒、2026-09-19 23:22 JST)。


## 7. 原本

- brief / 裁定 / prompt / 子の報告 (author・review) / probe と inventory.json / 変異 spec と結果: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dead-code-inventory/`。
