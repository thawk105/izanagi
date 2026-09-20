# 段 1 brief — [T-2800]/[T-2276] dead-code 削除 wave (dev-wave-t2800-dead-code-delete)

- 日時: 2026-09-20 13:5x JST。base = local main `947fd160a` (origin/main `371674ea6` より先)。worktree `.claude/worktrees/dev-wave-t2800-dead-code-delete`、branch `worktree-dev-wave-t2800-dead-code-delete`。
- 裁定 (確定済み、ユーザー 07:5x「推奨通りで」): D2172 項 5 = 第 24 回 /rulings 項 5 (控え `rulings-inbox/2026-09-20-rulings-full24-verdicts.md`)。一次資料 `output/insights/2026-09-19/dw-dead-code-inventory/README.md` §3 D 表・§5 R1〜R8。inbox 再走査 (13:4x) で T-2800 関連の更新なし。

## 研究前進 / 土台

- 研究前進は直接には無い。土台: ユーザー直接起票 (T-2800) の掃除で、裁定済み集合の削除により (a) 保守面 (Python 8,623 行 = 17 file) を減らし、(b) 受入から test node 162 本 / 台帳 worker 秒 11.58 秒 (台帳 24,379 node / 17,958.8 秒の 0.06 %) を外す (受入 wall の短縮量へは換算しない、D2172 項 6 と同じ)、(c) 将来 wave の pin 閉包・spawn-site・build-authority 閉包の走査対象を減らす。完了判定 = 削除集合が main に着地し、受入全走 child-green、[T-2276] が R1 / R2 で閉じる。

## scope (削除するもの — 実アンカー表)

R1 (a) 6 file (裁定どおり、歴史記録の参照は残す — 規律 7):
`orchestrator/campaign/p2_5.py` (167)、`orchestrator/campaign/s6_amendment_20260713_fence.py` (117)、`orchestrator/manual_probes/t1994_capdrop_probe.py` (99)、`t1994_readonly_snapshot_liveness.py` (100)、`t1994_rootview_probe.py` (100)、`t1994_seccomp_probe.py` (96)。現行 code・設定・運用文書からの参照 0 (repo 側 grep、13:4x)。

R3 (c) で段 1 の 3 条件 (一回限り / 結果が insight・成果物・図に凍結済み / 現行機構の実装でない) を module ごとに確認できた **6 対** (15 対中):

| # | module (行) | 専用 test | 共有 test の pin 行 | 3 条件の根拠 |
|---|---|---|---|---|
| 4 | `orchestrator/campaign/backoff_requested_us.py` (1,262) | `orchestrator/tests/test_backoff_requested_us.py` (1,221、36 node) | `test_ccbench_spawn_sites.py:75` (`("campaign/backoff_requested_us.py", "<module>._run_rep"): 1`)、`test_p3_build_authority_cli.py:152` (`"backoff_requested_us.py": "BACKOFF_PROFILE"`) | T-1941 の 1 workload × 1 rep 診断 (`diagnostic_only: true`)、結果 = `output/insights/2026-08-28_t1941-backoff-requested-us/` (request 957236.nqsv)。以後の 5 commit は族ゲート (D1198 / T-2061 / 静的上限符号化 / T-2419) の一括改修のみ。`patches/silo-backoff-requested-us.patch` と `condition_meaning_gate.DEFINE_SPECS["BACKOFF_REQUESTED_US"]` は残す (patch は R3 集合外、gate は patch を読む) |
| 8 | `orchestrator/campaign/s6_canary_rename.py` (312) | なし | `test_ccbench_spawn_sites.py:215–218` (export_stock 3 / git_apply / normalize_cxx / verify) | D52 §3 の独立再命名 canary、07-13 に 1 回実施、結果 = `output/insights/2026-07-13_s6-canary-rename.md`、`docs/phase3.md` S-1 closure checklist「独立再命名 canary の人間追認」[x] |
| 10 | `tools/insights_date_layout.py` (411) | `orchestrator/tests/test_insights_date_layout.py` (447、62 node) + `orchestrator/tests/README.md` PYTEST_ONLY_ALLOWLIST の 1 行 (`test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` が不在 file を赤にする) | docstring「一回限りの日付別移行」、09-10 実施済み (insights が日付 dir 配下)、結果 = `output/insights/2026-09-10/insights-date-layout/` |
| 11 | `tools/migrate_output_gzip.py` (885) | `orchestrator/tests/test_migrate_output_gzip.py` (473、12 node) | T-201 択 (b) の一回限り移行、08-20 実施 (worklog entry 723、tracked `.gz` 1,773 本)。読み手側の `.gz` fallback は本 tool に無い |
| 13 | `tools/plotting/plot_t2266_tail_mechanism.py` (625) | `orchestrator/tests/test_plot_t2266_tail_mechanism.py` (505、22 node) | T-2266 tail 機序の記述的図 1 枚、結果 = `output/insights/2026-09-07_backoff-tail-mechanism/` (fig + provenance json)。論文図 (`docs/paper-story/figures/*.provenance.json`) と `docs/paper-story-backoff/` は参照せず、後続 (09-10 / 09-15 / 09-16) は「v1 に束縛・無改変」と記すのみ |
| 14 | `tools/t1434_t1222_science_slice.py` (1,282) | `orchestrator/tests/test_t1434_t1222_science_slice.py` (521、30 node) | 凍結済み回顧 slice の検証器、08-28 実施、結果 = `output/insights/2026-08-28/t1434-science-slice/`。09-03 以降の参照は test 一覧の census のみ |

削除 file 合計 17 (module 12 + 専用 test 5)、Python 8,623 行 + 共有 test の pin 7 行 + README 1 行。

## 残すもの (R3 15 対のうち 9 対 — 3 条件のどれかを確認できない)

| module | 確認できない条件と根拠 |
|---|---|
| `backoff_counterfactual_analysis.py` / `backoff_counterfactual_cohort2_analysis.py` | 現行機構: 凍結事前登録 `docs/backoff-counterfactual-preregistration.md` が「解析器は…独立した定数として pin しなければならない」「v2 用の解析器はこの cohort 専用」と解析器に義務を課す (proof chain の一部)。T-2586 (09-16) が三者照合の consumer 側に使い、live な `test_t2187_adaptive_const_probe.py::test_probe_seed_table_matches_cohort2_preregistered_seeds` が cohort2 の `PREREGISTERED_SEEDS` に pin。ITT の主題は 2 本目論文 (D1637) で保持 |
| `backoff_nonmonotonicity_analysis.py` | 一回限りでない: T-2583 (09-15)・T-2635 (09-16) の probe が解析 library として関数 6 本を再利用 (両 README §8「解析器 (無改変)」sha `134b33d2…`)。高域の D2080 は裁定パッケージのまま |
| `backoff_sweep_report.py` | 現行機構: D12 材料レポート射影器 (`docs/orchestrator-design.md` §材料レポート、再現性が一級市民)。T-2187 (09-02) が基準線差し替えで改修、T-2702 (09-16) が digest consumer に数える |
| `floor_liveness.py` | 現行機構: D546 の診断 consumer (producer = `floor_job_checkpoint`、live な `s8b_floor_campaign.py` / `submit_floor.sh` / `floor_campaign.sh` が使用)。official floor campaign は稼働中 (T-1851 / T-2698)、[T-1402] が carry |
| `mocc_trace_pair_anchor.py` | 現行機構: D1110 (外部 anchor の 3 段階) の実装 (`mocc-trace-pair-anchor/v1`、`EXTERNAL_PIN_SCHEMA`)、checker `mocc_trace_pair.py` は live、mocc 観測は進行中 |
| `manual_probes/t1994_readonly_snapshot_qualification.py` | 現行機構: D2035 の errno 連言述語 (`build_case` の `:seal` require) の実装で、D2035 が「負例テストで守る」と名指す test (`test_buildcache_v2.py::test_qualification_seal_require_errno_conjunction` ほか 4 本) の被検体 |
| `tools/mutation_fanout.py` | 一回限り・結果凍結でない: D433 が本機体で実行不能と確定し、T-1177 (見送り台帳) が schema v2 で直す計画を保持。`mutation_fanout_contract.py` (1,583 行) は R3 集合外で残る |
| `tools/verify_paper_story_a1_balanced_sizing.py` | 現行機構: A-1 sized 事前登録 (`output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` §5.7) が受領証で sha256 束縛する別実装検証器。専用 test は live な生成器 `size_paper_story_a1_balanced.py` も検査 (共有 test)。A-1 sized attempt-0002 は本日認可 (T-2792) |

R2 / R4 は残す。R5 / R7 は見送り。R6 (a) 相乗り = 削除 wave が触る file に C の小組 (plotting 3 組・t189 2 組) は含まれないので発火なし。

## 不変条件

- 削除のみ。新しい gate・検査・台帳・一般化・互換層を足さない (DW-G05)。残す module は 1 byte も変えない。
- 共有 test の変更は上記 pin 行の削除だけ。`test_p3_b4_wiring_probe.py` の閉包 module 数 pin (47) には触れない (削除集合の module は閉包外、grep 0 件で確認)。
- 凍結成果物・事前登録・`patches/`・`output/` は変えない。`orchestrator/tests/acceptance_duration_ledger.json` の 162 node の stale 行は残す (conftest は lookup 専用で未知 key を無視、`tools/acceptance_shards.py` も同じ。台帳更新は R4 の tool の手番)。
- 削除に伴う挙動変化 = 受理集合の縮小 (162 node + pin 7 行) だけ。残る test の受理集合は不変。
- DW-O09: 削除集合の path / stem / sha256 / blob sha (40・12 桁) を repo 側 (output 以外) で走査 → sha/blob hit 0、path/stem hit は本表の pin 行・README 行・受入所要台帳のみ。output/ 側は背景走査 (`pin-closure-output.sh`、pid 2498951) の結果を段 4 前に確認する。
- DW-O11: 削除は `git rm` で stage する (run_tests が未 stage 削除を止める)。
- (P1) 親 provisional: `test_t1434_t1222_science_slice.py::test_pinned_jobs_requirements_are_exact` は D2172 項 6 (T-2799、派生値 pin は維持) の list-D に載る派生値 pin だが、項 5 R3 が同 test file を名指しで対削除の集合に置いており、項 5 が優先する。攻撃対象。
- (P2) 親 provisional: `test_backoff_requested_us.py::test_reproduction_body_binds_site_dispatch_budget_and_atomic_failure_log` は `output/insights/2026-08-28_t1941-backoff-requested-us/job-body.sh` (歴史 insight 成果物) の内容 pin。専用 test ごと消す (成果物自体は残る、規律 7)。攻撃対象。
- (P3) 親 provisional: `backoff_requested_us.py` 削除後、`patches/silo-backoff-requested-us.patch` は driver を持たない patch として残る (condition gate の DEFINE_SPECS が読む)。R3 集合外なので残す。攻撃対象。

## 成果物の形

- 実装 commit (Codex author): 17 file の `git rm` + 共有 test 2 file の pin 7 行削除。親の統合 commit: `orchestrator/tests/README.md` の 1 行。
- 変異 matrix: 削除 wave なので「消した test が守っていた性質」の変異は登録しない (被検体ごと消える)。残る共有 test の受理集合が変わらないことは焦点走 (`test_ccbench_spawn_sites.py`、`test_p3_build_authority_cli.py`、`test_plain_runner_coverage.py`、`test_acceptance_schedule_order.py`、`test_t2187_adaptive_const_probe.py`) で示す。負例 = pin 行を残したまま file を消すと `test_machine_callers_use_closed_generator_receipts` / spawn-site 表 / allowlist stale 検査が赤 (DW-M の「gate が発火する正例」)。
- insight `output/insights/2026-09-20/t2800-dead-code-delete/README.md`、spool fragment (worklog / decisions)、[T-2276] の完了記録。
- 受入全走 → land。

## 並列分割

- 段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A = 「残すべき物を消していないか」: 各削除 module の consumer・pin・凍結束縛の見落とし、レンズ B = 「消すべき物を残していないか / 削除の副作用」: 残す 9 対の根拠の反証、README・台帳・patch の孤児、受入 gate の赤)。
- 段 5 author 1 本 (17 file の削除 + pin 7 行、所有 = 削除集合 + 2 共有 test)。段 6 review 2 本 (敵対) + fix 子。

## 追記 (13:5x) — DW-O09 の output/ 側の結果

`pin-closure-output.sh` (pid 2498951、rc=0、`pin-closure-output.out` 225 行): sha256 / blob sha の hit は歴史記録だけ —
(a) `output/insights/2026-09-16/t2638-codex-worktree-retirement/data/reach2.tsv` / `reach_all.tsv` (到達性台帳) が T-1994 probe 4 本の blob sha を持つ (裁定 R1 が想定済み、規律 7 でそのまま残す)、
(b) `output/insights/2026-09-07_backoff-tail-mechanism/README.md` と `fig_tail_mechanism.provenance.json` が `plot_t2266_tail_mechanism.py` の生成時 sha256 を記録 (図の provenance。現行 file と照合する test は無い — 一次資料 R6 の確認と同じ)。
path / stem の hit は逐語・verbatim・棚卸し README・台帳だけで、live consumer は無い。
