# output/ を動的・固定に読む code/test の洗い出し (Explore sonnet 子、2026-09-29 14:5x、main 035fc11fa、静的読取のみ・未実走)

## 削除で赤になる確度が高いもの (必ず D)
1. `output/insights/2026-08-04_wave-a-campaign-transport-smoke/evidence/campaign-layout/campaigns/*/campaign.lock` 2 件 — orchestrator/tests/test_artifact_admission.py:1383-1398 (`output/**/campaign.lock` の集合が 32 件と完全一致)、:1421-1433。
2. `output/insights/2026-08-27_t1969-axis1-search-execution` (126 file) — orchestrator/axis1_search/validator.py:731-745,768-815 `FROZEN_PREDECESSOR_PATHS` を os.walk で履歴 tree と突合 (tools/run_axis1_search.py の preflight)。
3. `output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration` — test_paper_story_a1_paired.py:903-940 が rglob で file 集合を 9 件に完全一致 pin。
4. `output/insights/2026-09-20/t2797-b5-contrast` の `ledgers/llm/header.json`、`ledgers/llm/events/*.json` (glob)、`llm/round-1/*`、`llm/verbatim/*`、`verbatim/critic-N.md`、`llm/leakproof-context-b5.md` — test_b5_llm_round.py。`2026-09-18/t2746-k2-loop-round2/materials/knowledge-input.json`、`verbatim/critic-2.md` (test_p3_s4_loop.py:10214)。
5. `output/insights/2026-09-19/mocc-witlight-arm-run/verbatim/{summary.json,W1..W4-result.json}` — tools/plotting/plot_mocc_witlight_four_arm.py:29,126-138 と test (sha256)。
6. certification.json / raw-manifest.json / result.json / receipt.json / .complete.json / README.md — sha256 pin (orchestrator/campaign/paper_story_*.json、tools/plotting/*、docs/paper-story/figures/*.provenance.json 13 本) か LIVING_DOCS 参照。

## Path 連結で読む (文字列 "output/insights/..." の literal 検索に掛からない)
- test_codex_reasoning_ab.py:128-145,13503-13529,13714 — `2026-07-29_t153e-t15423-review-verbatim/{focus1,focus2}.md`、`2026-08-09_t181-certified-rerun/run-outputs/s0*-*.md`
- test_t338_submission_gate_unit2.py:454、unit3.py:34 — `2026-08-11_t139-manifest-land1/receipt-schema-v1.json`
- p3_b4_wiring_probe.py:49 ほか
- → 規則: root の名前 (最後の成分) が tools/ orchestrator/ hooks/ .claude/ .codex/ のどこかに部分文字列で現れる root は丸ごと D。

## 固定で読む test (他)
test_t471_restore_bound.py (2026-08-05_t471-restore-bound/driver)、test_t244_p3_liveness_probe.py (2026-08-05_t244-p3-liveness)、test_vhash_forwarding_prototype.py (2026-09-29/vhash-forwarding-prototype/make_figures.py)、test_mocc_trace_pair.py (2026-08-26_mocc-trace-pair-receipt.json)、test_mocc_g2_repro_ledger.py (2026-08-26_mocc-g2-repro/pre-registration.md)、test_paper_story_a1_paired.py:1140-1165,5241、test_paper_story_a2_certification.py:4968、test_plot_a2_certification.py、test_s8b_oracle_n_pilot.py:291-320、test_t139_*、test_t793_*、test_backoff_profile_pegasus.py:1227、test_backoff_requested_us.py、test_campaign_import_invariant.py:155-179、test_p3_b4_producer_auth_experiment.py:1804-1815、test_frozen_artifacts.py:50-131 (2026-07-16_s8b-* md 5 本)。
mocc_g2_repro_ledger.py:246,331 の CLI 既定 root = 2026-08-26_mocc-g2-repro (runs/N を列挙; test は tmp 構築)。

## 全走査するが削除で落ちないもの
tools/ruleops.py (件数 pin なし)、s8b_holdout_freeze.py の repo 全走査 (hit 0 と positive control のみ)、conftest の output 複製・output_snapshot_ignores の前後比較、acceptance_duration_ledger.json。

## check_docs
- md 相対リンク検査なし。PATH_REF の実在検査は LIVING_DOCS (README.md、docs/phase3.md、docs/roadmap.md、docs/phase3-*.md、docs/dev-wave/*.md、output/README.md、output/task-runs/README.md など) だけ。archive・worklog・decisions・insights 自身は対象外。
- `_literal_placeholder_targets` (:2595-2720): insights 直下と日付 dir 直下 (深さ 1) の *.md を列挙。深い raw は無関係。
- test_check_docs.py::test_real_repo_clean が実 repo で走る。

## provenance / guard
- 実装面 = suffix .py .sh .bash .c .cc .cpp .cxx .h .hh .hpp .hxx .cmake .patch .diff (所在不問)、削除 (D) も数える。insights 内 64 件。→ 外さない。
- hooks/guard_bash.py: `git rm` の引数に literal `campaign.lock` / `wal.jsonl` があると拒否。`$()`・heredoc・xargs との同居も拒否。
