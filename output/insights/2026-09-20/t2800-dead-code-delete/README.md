# 参照されない一回限りの tool の削除 — D2172 項 5 (R1 (a) / R3 (c)) の実施記録 (t2800-dead-code-delete)

authority: none
default_effect: no-state-change

- 日付: 2026-09-20 (JST)。wave branch `worktree-dev-wave-t2800-dead-code-delete`、着手時 local main `947fd160a`、実装 commit `455b03f36`、main 取り込み `d9fe4b353` (main `4726b6493`)。
- 依頼: 第 24 回 /rulings 項 5 = D2172 項 5 (T-2800 / T-2276) の削除 wave。R1 (a) = 歴史記録だけが参照する 6 file を削除、R3 (c) = 一回限り tool 17 対のうち 2 対 (`tools/check_silo_validation_isolation.py`、`orchestrator/campaign/mocc_g2_repro_ledger.py`) を残し、他 15 対は段 1 で「一回限り・結果凍結済み・現行機構の実装でない」を module ごとに確認できたものだけ削除 (確認できなければ残す)。R2 / R4 は残す、R5 / R7 見送り、R6 は相乗りのみ。Codex author + 敵対検証子。本題の削除だけ。
- 一次資料: `output/insights/2026-09-19/dw-dead-code-inventory/README.md` §3・§5。裁定の逐語は `verbatim/s4-adjudication.md` 冒頭と D2172 項 5。
- 本書は可変状態の正本ではない。

## 1. 結果

| 区分 | 削除 | 残す |
|---|---|---|
| R1 (a) | 6 file 全部: `orchestrator/campaign/p2_5.py`、`orchestrator/campaign/s6_amendment_20260713_fence.py`、`orchestrator/manual_probes/t1994_capdrop_probe.py`、`t1994_readonly_snapshot_liveness.py`、`t1994_rootview_probe.py`、`t1994_seccomp_probe.py` | — (歴史記録・到達性台帳の参照はそのまま、規律 7) |
| R3 (c) 15 対 | **4 対 (7 file)**: `orchestrator/campaign/s6_canary_rename.py` (専用 test なし)、`tools/insights_date_layout.py` + `orchestrator/tests/test_insights_date_layout.py`、`tools/migrate_output_gzip.py` + `orchestrator/tests/test_migrate_output_gzip.py`、`tools/plotting/plot_t2266_tail_mechanism.py` + `orchestrator/tests/test_plot_t2266_tail_mechanism.py` | **11 対** (§3) |

追随: `orchestrator/tests/test_ccbench_spawn_sites.py` の `_EXPLICIT_NON_CCBENCH_PROCESS_SITES` から canary の 4 site (export_stock 3 / git_apply / normalize_cxx / verify、旧 :215–218) を削除 (Codex author)。`orchestrator/tests/README.md` の `PYTEST_ONLY_ALLOWLIST` から `- test_insights_date_layout.py` の 1 行を削除 (親、docs)。

差分: `git diff --stat 947fd160a 455b03f36` = **15 files changed, 4,342 deletions(-)** = 削除 13 file の 4,337 行 + pin 4 行 + README 1 行。author の unit commit `8f6aee197` は 14 file / 4,341 deletions、統合 tip との実装面差分は空。

受入所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` には削除 test 3 本の **96 node (62 + 12 + 22) / 6.349 worker 秒** (台帳の記録値、17,958.8 秒の 0.035 %) が stale として残る。conftest (`:1739–1758`) と `tools/acceptance_shards.py` (`:392–404`) は収集 item からの lookup なので余剰 key は使われない。台帳は編集していない (更新は R4 の tool の手番)。受入 wall の短縮量へは換算しない (D2172 項 6 と同じ)。

## 2. 段 1 で削除を確認できた 4 対の根拠

| module | 一回限り | 結果凍結済み | 現行機構の実装でない |
|---|---|---|---|
| `s6_canary_rename.py` (312 行) | D52 §3 の独立再命名 canary、2026-07-13 に 1 回実施 | `output/insights/2026-07-13_s6-canary-rename.md`、`docs/phase3.md` S-1 closure checklist「独立再命名 canary の人間追認」[x] | 共有 spawn 表以外の live 呼出しなし |
| `insights_date_layout.py` (411) + test (447) | docstring「一回限りの日付別移行」、2026-09-10 実施 | `output/insights/2026-09-10/insights-date-layout/` (移動実績と固定計画) | 専用 test の import 以外に consumer なし。test も一時 tree 上で削除 tool 自身を検査 |
| `migrate_output_gzip.py` (885) + test (473) | T-201 択 (b) の一回限り移行、2026-08-20 実施 (worklog entry 723) | tracked `.gz` 1,773 本 | 読み手側の `.gz` fallback は本 tool に無い。test は migrator 自身の round-trip / stage / rollback |
| `plot_t2266_tail_mechanism.py` (625) + test (505) | T-2266 tail 機序の記述的図 1 枚 (2026-09-07) | `output/insights/2026-09-07_backoff-tail-mechanism/` (fig + provenance json、生成時 sha256 `034a3721…6139aaa` は削除前 file と一致) | 論文図 `docs/paper-story/figures/*.provenance.json` と `docs/paper-story-backoff/` は参照せず、後続 wave (09-10 / 09-15 / 09-16) は「v1 に束縛・無改変」と記すだけ。現 checkout での再生成・継続検査は失われる (記録は書き換えない) |

## 3. 残す 11 対と、確認できなかった条件

| module | 確認できない条件 (根拠) |
|---|---|
| `orchestrator/campaign/backoff_counterfactual_analysis.py` | 現行機構でないと言えない: 凍結事前登録 `docs/backoff-counterfactual-preregistration.md` (§v2 改訂後の解析) が「解析器は…独立した定数として pin しなければならない」「v2 用の解析器はこの cohort 専用」と解析器に契約を課し、`:20–25, 332, 582` がそれを実装。T-2586 (09-16) が事前登録 / producer / consumer の三者照合の consumer 側に使った |
| `backoff_counterfactual_cohort2_analysis.py` | 同上に加え、live な `orchestrator/tests/test_t2187_adaptive_const_probe.py:24–26, 1974–1980` が probe の certification seed 表を本 module の `PREREGISTERED_SEEDS` と照合 |
| `backoff_nonmonotonicity_analysis.py` | 一回限りでない: T-2583 (09-15) と T-2635 (09-16) の probe が解析 library として関数 6 本を再利用 (両 README §8「解析器 (無改変)」、sha `134b33d2…`)。高域の D2080 は裁定パッケージのまま |
| `backoff_sweep_report.py` | 現行機構でないと言えない: 固定図専用でなく campaign を探索して certified view と digest を読む D12 材料レポート射影器 (`docs/orchestrator-design.md` §材料レポート)。T-2187 (09-02) が基準線差し替えで改修、T-2702 (09-16) が digest consumer に数える |
| `floor_liveness.py` | 現行機構でないと言えない: D546 の診断 consumer (投入ごとの receipt / checkpoint / journal を読む)。producer `floor_job_checkpoint` は live な `s8b_floor_campaign.py` / `submit_floor.sh` / `floor_campaign.sh` が使う (producer が本 module を呼ぶわけではない)。official floor campaign は稼働中、[T-1402] が carry |
| `mocc_trace_pair_anchor.py` | 一回限り・結果凍結を確認できない: D1110 (外部 anchor の 3 段階) の検証器で、任意の pair receipt に対する外部 pin・署名検証を実装 (`:342–403, 513–574, 577–670`)。成果物が repo に無いことは「結果凍結済み」の証拠にならない |
| `orchestrator/manual_probes/t1994_readonly_snapshot_qualification.py` | 現行機構でないと言えない: 自身は一回限りの qualification 観測器と明記するが、D2035 の errno 連言 (`:716–722`) を `test_buildcache_v2.py:5787–5823` が直接検査し、`:5627–5657` が helper `ParentSourceSubstitution` を実 session の保護検査に再利用 |
| `tools/mutation_fanout.py` | 一回限り・結果凍結の分類が成立しない: D433 が本機体で実行不能と確定 (`:401–418` が実行不能条件を保持)、完了した一回限り処理ではない。T-1177 (schema v2) は見送り台帳で active 外なので「将来直すから」は保持理由にしない。`mutation_fanout_contract.py` (1,583 行) は本 driver が使う |
| `tools/verify_paper_story_a1_balanced_sizing.py` | 現行機構でないと言えない: A-1 sized 事前登録 (`output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md` §5.7) の証明書・再現受領証の検証器 (`:711–772`)。専用 test `test_paper_story_a1_balanced_sizing.py:21–22` は live な生成器 `size_paper_story_a1_balanced.py` との共有 test で、対削除の前提が成立しない |
| `orchestrator/campaign/backoff_requested_us.py` + `test_backoff_requested_us.py` | **段 3 で判明 (A-2)**: module は T-1941 の 1 workload × 1 rep 診断で 3 条件を満たすが、test が専用でない — `:1092` が live な `dispatch_compute._child_environment()` の PBS 3 変数除去を検査し (他 test に同等 assert なし、親が `test_pegasus_dispatch_compute.py` で検算)、`:688` が policy registry の包含 / 非包含を pin、`:230 / :297 / :1061` が残る `patches/silo-backoff-requested-us.patch` の mu01 / mu02 意味を検査。被覆を残す test 分割は削除でなく新しい編集になるので残す |
| `tools/t1434_t1222_science_slice.py` + `test_t1434_t1222_science_slice.py` | **段 2〜3 で判明 (P1)**: module は 3 条件を満たすが、test の `test_pinned_jobs_requirements_are_exact` (`:409–442`) は D2172 項 6 (T-2799、派生値 pin は「確認済み 15 関数も未確認候補 246 関数も削らず」) の `inventory/list-D.txt:283` に載る。項 5 R3 の対削除と項 6 の維持が重なり、項 5 が項 6 を上書きする逐語は無い。両裁定を同時に満たす保持を選んだ (優先順位を新設しない) |

追加削除を支持する反証は段 3 の 2 レンズ・段 6 の 2 レビューとも 0 対。

## 4. 手順と実測

- **重複検査 (13:1x)**: 対象 40 path で branch tip (merge-base 基準)・全 42 worktree の作業ツリー (`scanned=42 unreadable=0 hits=0`)・peer 12 session の主題、いずれも重複なし。
- **DW-O09 pin 閉包**: 削除集合の path / stem / sha256 / blob sha (40・12 桁) を repo 側 (`verbatim/pin-closure-repo.txt`) と output 側 (`verbatim/pin-closure-output.txt`) で走査。sha / blob の hit は歴史記録だけ — t2638 到達性台帳 (`reach2.tsv` / `reach_all.tsv`) の T-1994 probe 4 本の blob (裁定 R1 が想定済み)、tail 図 provenance の生成器 sha。path / stem の hit は逐語・棚卸し README・受入所要台帳・README allowlist だけ。
- **段 2 plan** (Codex gpt-6-astra / medium、read-only、13:55〜14:03): 削除手順を file:line で起草、共有 pin は「7 行」でなく 6 行 + 付属コメント 2 行と訂正、残す 9 対の反証 0、(P1) を留保。`verbatim/s2-plan.md`。
- **段 3 相談** (2 本並列、14:06〜14:12、レンズ A = 消しすぎ (sol)、B = 残しすぎ・過剰 (luna)): A は must-fix 2 (P1 と A-2)、B は must-fix 1 (P1)。両者とも追加削除 0 対。`verbatim/s3-consult-a.md` / `s3-consult-b.md`。
- **段 4 裁定**: 削除集合を 17 file → 13 file へ。変異 m0 / m2 / m4 を事前登録。`verbatim/s4-adjudication.md`。
- **段 5 author** (Codex gpt-6-astra / medium、workspace-write、unit worktree `t2800-unit-delete`): 1 巡目 (14:19) は親の prompt が指示した `git rm` が sandbox の `.git/worktrees/*/index.lock` 書込み拒否 (Read-only file system) で失敗し変更なし (`verbatim/s5-author-1.md`、F359 の同型再発)。2 巡目 (14:22〜14:25) は作業ツリーの `rm` + 4 行編集で 14 file / 4,341 deletions (`verbatim/s5-author-2.md`)。実際の stage 経路: author は未 stage のまま報告 → 起動器が終端契約 (D2044 項 16) で残差を unit commit `8f6aee197` に記録 → 親が所有 path 限定 patch を `git apply --index` で wave worktree へ展開 → README 1 行を親が落として統合 commit `455b03f36`。
- **焦点走** (計算ノード dispatch、request 12686.nqsv、Elapse 93 秒、2026-09-20 14:30〜14:32 JST): `test_ccbench_spawn_sites.py` + `test_plain_runner_coverage.py` + `test_acceptance_schedule_order.py` + `test_p3_build_authority_cli.py` + `test_p3_b4_wiring_probe.py` + `test_campaign_import_invariant.py` + `test_t2187_adaptive_const_probe.py` = **557 passed / 8 skipped、87.80 秒**。台帳 coverage (`test_acceptance_schedule_order.py:704`) は被覆済み node を除くので低下方向だが閾値 0.90 を維持 (G5 緑)。閉包 47 pin (`test_p3_b4_wiring_probe.py`) は無傷。
- **全史 provenance 監査**: `tools/check_ai_provenance.py` = 11,883 件、新規違反なし (rc=0)。`python3 tools/check_docs.py` 違反なし。
- **段 6 レビュー** (2 本並列、14:36〜14:4x、A = 過剰・削除、B = 整合・実効性・受入): must-fix 0 / 0、条件付き GO。should = 実際の stage 経路を記録する (RA-1 / RB-2、上に記した)、coverage の方向を正しく書く (RB-1)、確定案の台帳比は 0.06 % でなく 0.035 % (RA)。fix 子は起動していない。`verbatim/s6-review-a.md` / `s6-review-b.md`。

## 5. 変異台帳 (DW-M01〜M08)

- spec `mutation-spec.json` (sha256 `bdf01455b5d06b18550425cf62847662118bb9dd7e0d49d6f1a7c505bce4c44a`)、baseline = 削除 + 追随を commit した tip `455b03f36`、harness `tools/mutation_harness.py` (sha256 `4f85ec88…`)、登録 worktree `mut-t2800-delete` (固定 commit、DW-M05 正本経路)、runner = `tools/run_tests.py --force-dispatch orchestrator/tests/test_ccbench_spawn_sites.py orchestrator/tests/test_plain_runner_coverage.py -q -rf` (計算ノード dispatch)。probe 走は行っていない (期待 node が事前に 1 本ずつ確定)。投入から完了まで親は登録 worktree へ書いていない。
- 結果 (`mutation-results.json`、2026-09-20 14:34:55〜14:41:26 JST、harness rc=0、summary `KILLED 2 / SURVIVED 1 / MISMATCH 0 / matching 3 / registered 3`):

| id | 変異 | 期待 | 結果 | request | 所要 |
|---|---|---|---|---|---|
| (collection) | — | — | rc 0 | 12697.nqsv | — |
| baseline | なし | PASSED | **PASSED** (rc 0) | 12699.nqsv | 114.8 秒 |
| m0-equivalent-comment | spawn 表の直前へコメント 1 行 (等価、過剰拒否の正例) | SURVIVED | **SURVIVED** (rc 0) | 12704.nqsv | 99.7 秒 |
| m2-spawn-line-left | canary の `export_stock: 3` を表へ戻す (module は削除済み) | KILLED、`test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact` | **KILLED**、失敗 node 完全一致 (1 == 1) | 12713.nqsv | 99.4 秒 |
| m4-readme-line-left | README allowlist へ `test_insights_date_layout.py` を戻す (test は削除済み) | KILLED、`test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries` | **KILLED**、完全一致 (1 == 1) | 12716.nqsv | 104.2 秒 |

- 単一理由 (F820): m2 は exact Counter 比較 (`:2840–2847`) だけが赤で、measurement 側 (`:4098–4108`) は Counter 減算が非正値を落とすので赤にならない。m4 は `:81–83` の stale 検査が先に拒否し、self-runnable 検査へ到達しない。段 3 B・段 6 A/B が静的に確認、本走で node 完全一致。
- 登録しなかった変異: 「消した test が守っていた性質」(被検体ごと消える)、未 stage 削除 (harness で表現できず、DW-O11 の gate は `test_run_tests_preflight.py::test_unstaged_deletion_gate_detects_count_and_scrubs_git_env` ほかが既に守る)。

## 6. 受入全走

本書の commit 時点では**未実施**。land 対象 tip へ `tools/dev_wave_wait.py acceptance` (計算ノード dispatch) を投入し、結果 (child-green 受領証、tested main / tip、所要) は job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2800-dead-code-delete/acceptance-*` に残り、land 後の worklog エントリから辿る。本書へは追記しない。

## 7. 裁定パッケージ候補 (本 wave では変更しない)

- **science-slice の対** (`tools/t1434_t1222_science_slice.py` 1,282 行 + test 521 行): D2172 項 5 R3 の対削除集合と項 6 (派生値 pin 維持) が 1 test 関数で重なる。削除するには項 6 の例外指定 (この 1 関数、または file ごと) が要る。指定が無ければ残したまま。
- **requested-us の対** (`orchestrator/campaign/backoff_requested_us.py` 1,262 行 + test 1,221 行): module は 3 条件を満たすが test が live 被覆 3 群 (dispatch の PBS 除去、registry pin、patch の mu01 / mu02) を持つ。削除するなら被覆 3 群を別 file へ移す編集 (削除でない) が先で、それは別依頼。

## 8. 原本

- brief / 裁定 / prompt / 子の報告 / 変異 spec と結果 / 走査 script と出力 / 焦点走・provenance・受入の log: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2800-dead-code-delete/`。
- 本 dir の `verbatim/` は brief・裁定・子 7 本の報告・走査結果の写し。author の patch は写していない (実装面は commit `8f6aee197` / `455b03f36` が正本)。
