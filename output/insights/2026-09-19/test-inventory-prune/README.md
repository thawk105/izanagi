# 低価値テストの棚卸しと掃除 — 4 分類 inventory と重複 6 node の削除

- authority: none
- default_effect: no-state-change
- wave: dev-wave-test-inventory-prune (背景 job 151d1045)。着手時 local main `a99425b66`、段 5 前に `657e1e5a7` を ff 取込。
- 削除 commit: `0917fc400b00c9a83df9e01f508dbfb15614e9ee` (Codex author、test 2 file、+3/−18 行)。
- 原ログ (prompt・plan・相談・変異 spec/結果・scanner 実体・inventory.json 17,123,127 bytes sha256 `05e67b2d5a7e248c58b4bb4168bf27e2583139d2672b4ec76e691527cb173cbf`): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/`。
- 依頼: 4 分類 (A 死んだ対象 / B 冗長 / C 撤回済み機構 / D 派生値 pin) で棚卸しし、(A)(B)(C) は Codex author が削除して変異 harness で冗長性を示す、(D) は削除せず裁定パッケージで返す。verifier・hooks・check_docs・provenance・受入 launcher の test は最初から除外 (規律 2)。scope 外 = production 変更・hold 方針変更・新 gate。
- 成果物影響 (DW-G05、段 4 裁定 #13): 放置しても certified 選択・レポート・台帳値は変わらず、重複 6 node の台帳換算 worker 秒が残るだけ。誤削除は earliest-eligible 選択違反 / value-literal 帰属の回帰防壁を欠落させ得るため、残存 case の同値性 (§3) と登録変異の pre/post 検出集合 (§4) で確認した。

## 結論 (最初に読む)

**今回抽出して意味確認した候補の範囲で、削除できると確定したのは重複 6 node (台帳換算 33.005 worker 秒、収集 node の 0.02%) だけだった。** (A) 死んだ対象と (C) 撤回済み機構は 0 件。(D) は 41 file の代表 45 関数を読んだ結果、関数単位で、純粋な定数 pin 7、資料・派生値 pin (production を通さない) 5、pin と挙動検査の併存 3、読んだ代表が挙動検査 (D でない) 26 file だった (§5)。

静的 scanner の候補数 (A 112 / B 35 / C 1 / D 291 関数) を「削除可能数」と読んではいけない。(A) 112 件は全件が合成入力・拒否負例・表示文字列で生きた検査、(B) の本文同一 7 組は同名 alias が別 production module を指すか helper が別実装、parametrize の `==` 重複 27 row のうち 26 row は `1`/`1.0`/`True`/`0`/`False` の型境界 (別入力)。scanner が拾わない型の重複 (通常関数 ⊂ parametrize row、別 decorator 間の同値 row) は相談 B が 1 file で 5 件見つけており、suite 全体に同型が残らないとは言えない (§7)。

| 項目 | 値 |
|---|---|
| 削除 node | 6 (`test_s8b_holdout_freeze.py` 1、`test_p3_s4_loop.py` 5) |
| 削除行 (純減) | 15 行 (592,860 → 592,845、`orchestrator/tests/*.py` 391 file の blob 改行数、削除前 `657e1e5a7` → 削除後 `0917fc400`。着手時 `a99425b66` は 592,832) |
| 収集 node | 25,381 → 25,375 (前者は受入形 `--collect-only` の実測、2026-09-19 22:02 JST、job 10724、commit `a99425b66`。後者は 6 を引いた差引値) |
| 受入台帳の worker 秒 | 17,958.848 → 17,925.843 s (台帳 `acceptance_duration_ledger.json` 24,379 entry の合計から削除 node の entry 値 33.005 s を引いた**換算値**。台帳 file は編集しない) |
| worker 時間換算 | 4.9886 h → 4.9794 h (−0.18%) |

受入 wall の短縮は主張しない (T-2617: wall の主因は最長単体 test と混雑)。

## 1. 母数と時点

| 母数 | 値 | 時点・出所 |
|---|---|---|
| `orchestrator/tests/*.py` | 391 file / 592,832 行 (着手時 `a99425b66`)、592,860 行 (削除前 `657e1e5a7`) | blob 改行数 (conftest・helper・fixture module を含む) |
| うち `test_*.py` | 363 file | scanner の glob |
| 分類対象外 (規律 2) | 30 file / 67,920 行 | `inventory/excluded-suites.txt` |
| 分類対象 | 333 file / 510,327 行 / 14,416 test 関数 / 345,321 関数行 | scanner v1 |
| 収集 node | 25,381 | 受入形 collection (`collect.txt`) |
| 対象 file の収集 node | 21,882 (台帳秒合計 15,587.593 s、台帳に無い node 949) | scanner v1 |
| 受入台帳 | 24,379 entry / 17,958.848 s | `orchestrator/tests/acceptance_duration_ledger.json` (48 worker 下の値、整数丸め) |
| conftest | 3,388 行 | 同 commit |

## 2. 4 分類の inventory (scanner v1 → 意味確認)

scanner は Codex author が書いた静的走査器 (`verbatim/scan_tests.py.md`、実体は job dir、20 秒で完走、親が wave worktree で再実走して出力 byte 一致)。初版 (v0) は (A) が合成 fixture の literal を拾い (B) が decorator を無視していたので fix1 で修正した (`verbatim/scanner-fix1-findings.md`)。v0 の集計は `inventory/inventory-v0.md`。

| 分類 | 定義 | scanner v1 候補 (protected 除く) | 意味確認 (plan + 相談 2 本) | 削除確定 |
|---|---|---|---|---|
| A | 対象の module・関数・CLI 引数・docs 節が main に無い | 112 関数 / 2,961 行 / 153 node / 49.96 s | 112/112 を本文確認: 全件 (a) 合成入力・拒否負例・表示文字列・実在 CLI の help、対象不在で恒真な test (b) は 0 | **0** |
| B | 本文が他 file と AST 同一 (decorator 込み)、parametrize が同一入力を重ねる | 35 関数 / 419 行 / 147 node / 125.97 s (B1 7 組 14 関数、B2 27 row) | B1 7 組: 同名 alias が別 module (s6_sort_sweep vs s8a_trigger_sweep 等) か別 helper 実装 (t080 snapshot の参照実装 vs production 委譲) で全組非重複。B2: 26 row は型違い (`1`/`1.0`/`True`、`0`/`False`)、1 row (`test_s8b_holdout_freeze.py:2381` の 3 行目 `True`) が真の重複。**相談 B が scanner 外で `test_p3_s4_loop.py` の重複 5 件を発見** (通常関数 ⊂ parametrize row、別 decorator 間の同値 row) | **6 node** (§3) |
| C | 撤回済み決定・見送り台帳の機構だけを検査 | 1 関数 (`test_campaign.py:10615`、D158 参照) | D641 は D158 の official 部分だけを supersede し、exploration の resolver (`layout.py:375`) は現存・到達可能 | **0** |
| D | docs の bytes・派生値・定数を exact pin するだけ | 291 関数 / 10,099 行 / 356 node / 225.39 s (41 file) | 41/41 file の代表 (45 関数) を読んだ: 純粋な定数 pin 7 関数、資料・派生値 pin 5 関数、pin と挙動検査の併存 3 関数、代表が挙動検査 26 file (D でない)。残り 246 関数は個別未確認 | 削除しない (§5) |

分類間は重複しうる (scanner は関数単位で分類ごとに 1 回数える)。protected (conftest の real-repo / oracle / receipt / growth / flaky 登録、golden、台帳 add-only 凍結 8 suite、他 test の文字列 literal 参照) は 634 関数 / 918 node / 4,969 s で、分類に関わらず削除対象から除いた (P1)。並行 wave `dev-wave-acceptance-worker-time-trim` の所有 6 file (`inventory/sibling-owned-files.txt`) も除いた (P2)。

## 3. 削除した 6 node と根拠

| file | 変更 | 削除 node | 同値な残存 node | 台帳秒 |
|---|---|---|---|---:|
| `test_s8b_holdout_freeze.py:2381` | parametrize の 3 行目 `True` と id `drop-candidate-selection` を除去 | `test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[drop-candidate-selection]` | 同関数 `[min-to-max]` (同型・同入力 `True`、本文は id に分岐しない、fixture は tmp repo を毎回作る) | 33.000 |
| `test_p3_s4_loop.py:3238` | 関数 `test_value_literal_consistency_accepts_match` を削除 | 同名 1 node | `test_coder_proposal_value_domain_accepts_declared_integral_boundaries[middle-int]`/`[middle-float]` (同じ `CoderProposal(value=20/20.0, implementation="double now_backoff = 20/20.0;")` を `assert_value_literal_consistent` に通す) | 0.001 |
| `test_p3_s4_loop.py:3271` | row `nonintegral`/`bool`/`zero`/`above-upper` と id を除去 (残り nan/inf/negative/decimal/floatable-object) | `test_coder_proposal_rejects_values_outside_exact_integral_domain[nonintegral|bool|zero|above-upper]` | `test_backoff_value_adapter_preserves_main_exception_and_structured_rule[…]` の同値 row (20.5/"20.5"、True/"1"、0/"0"、1001/"1001"; 残存側は type・message・rule_id に加え stage・reason も検査) | 0.004 |

関数本文・docstring・期待値・helper・fixture・import・conftest・台帳・production は不変。test 名集合の差は `test_value_literal_consistency_accepts_match` の削除 1 件だけ (基底 `657e1e5a7` と比較、親が検算)。削除後の 2 file の焦点走: 670 passed / 2 skipped (計算ノード job 10888、36.4 秒)。

## 4. 変異 harness による検出力保存の確認 (module ごと 1 spec)

手順 (段 4 で事前登録、`verbatim/adjudication.md`): 変更前 commit `657e1e5a7` で probe (全件 SURVIVED 期待、失敗 node の完全集合 S_pre を記録、DW-M08 の erratum) → 削除 commit `0917fc400` で S_post = S_pre − Del を KILLED 期待に登録して本走。runner は module ごとに当該 test file 1 本 (`tools/run_tests.py --force-dispatch <file> -q -rf`、両走で同一)、`tools/mutation_harness.py --repo <固定 commit の worktree> --runner-mode dispatch --detached`。spec と結果 JSON は `mutation/` にある。

erratum (実行手順と裁定の差、DW-O12): 裁定は「独立 clone の固定 commit worktree」(DW-M07 の `mutation_worktree.py --source-repo` 経路) を書いたが、実際は主 repo に登録した専用 worktree `.codex/worktrees/tinv-mut-{h,l}` (branch `mut-tinv-mut-*`、submodule 初期化済み、clean) へ `tools/mutation_harness.py --repo` を直接当てた (DW-M05 の正本経路)。理由: fresh clone は submodule の供給 URL が非 local で `dev_wave_submodule_init.py` が拒否し、wrapper 経路の共有木検査は並行 wave の churn で落ちるため。harness 自身が固定 HEAD 束縛 (`repo_head` を結果 JSON に記録: probe `657e1e5a7`、post `0917fc400`)・起動/復元時の内容比較・flock・逐次 flush を強制しており、観測事実は変わらないが、DW-M07 の文言どおりの独立 clone では走らせていない。

| spec | 変異 (anchor は file 内で一意) | probe 失敗 node | うち削除 node | post 期待 = 実測 | 状態 |
|---|---|---:|---:|---:|---|
| H `orchestrator/campaign/s8b_holdout_freeze.py` | M1 `min(eligible, …)`→`max(…)` (最早適格 run の選択を最遅へ) | 6 | 1 | 5 = 5 | KILLED |
| H | M2 `if required_run_id != selected_run_id:`→`if False and …` (選択不一致の拒否を無効化) | 6 | 1 | 5 = 5 | KILLED |
| H | E1 encoding comment への comment 追加 (等価対照) | 0 | 0 | 0 = 0 | SURVIVED |
| L `orchestrator/campaign/p3_s4_loop.py` | M1 `assigned_value != coder_value`→`==` (value↔literal 整合の反転) | 23 | 1 | 22 = 22 | KILLED |
| L | M2 `if decision.accepted:`→`if decision.accepted or True:` (値域拒否の無効化) | 20 | 4 | 16 = 16 | KILLED |
| L | E1 encoding comment (等価対照) | 0 | 0 | 0 = 0 | SURVIVED |

- 全負例で S_post は S_pre から削除 node だけを除いた集合と完全一致し、非空。H では `[min-to-max]`・`[use-reported-eligible]` ほか 3 test、L では `…accepts_declared_integral_boundaries[middle-int]`/`[middle-float]` (M1) と `test_backoff_value_adapter_preserves_main_exception_and_structured_rule[…]` の同値 row (M2) が残存検出に含まれる。
- 対照 E1 は前後とも赤 0 で、両 runner に drift mask (source の HEAD blob 比較で一律に赤になる gate) は無い。非 ASCII id は 0 件。
- baseline: H は変更前 162 passed / 2 skipped、削除後 161 passed / 2 skipped。両 post とも harness summary は `matching 3 / registered 3`。
- 主張の範囲: 登録した変異 (module ごと負例 2 + 対照 1) に限り、削除 node が検出していた変異を残存 node が全件検出する。あらゆる欠陥に対する検出力の一般保存の証明ではない (相談 A-brief-4 / B-4)。主根拠は §3 の同値性で、変異はその裏取り。
- 実行期間 (queue 待ち込みの外側 wall、所要ではない): probe 22:57→23:26 JST、post 23:29→23:48 JST (各 spec = collection 1 + baseline 1 + 変異 3 = dispatch job 5 本、2 spec 並列)。runner 自身の報告時間は H baseline 35.0 s (probe) / 35.4 s (post)、各 job の Elapse は結果 JSON の receipt path から辿れる。

## 5. (D) 裁定パッケージ — 削除しない、件数・file・pin 先

ユーザー裁定: DW-O18/O25 の exact pin は意図された防壁なので本 wave では緩めない。以下は次の裁定材料であり、削除の提案ではない。

確認済み (D)、純粋な定数 pin — production 定数を literal と比較するだけの test (7 file / 7 関数):

| file:行 (関数) | pin 先 (定数名 = literal) |
|---|---|
| `test_floor_pair_driver.py:636` (`test_all_four_semantic_schema_identifiers_are_bumped`) | `floor_pair_driver.SPEC_SCHEMA`="floor-pair-spec/v3"、`PLAN_SCHEMA`="floor-pair-plan/v2"、`WINDOW_SCHEMA`="floor-pair-window/v3"、`SUMMARY_SCHEMA`="floor-pair-summary/v3" |
| `test_p3_b4_proposal_binding.py:556` (`test_non_guarantees_are_the_verbatim_ruling_set`) | `B4_PROPOSAL_BINDING_NON_GUARANTEES` の逐語 tuple |
| `test_pegasus_dispatch_compute.py:662` (`test_relay_limits_are_literal_four_and_sixty_four_kib`) | `DEFAULT_SUCCESS_RELAY_LIMIT_BYTES`=4096、`DEFAULT_FAILURE_RELAY_LIMIT_BYTES`=65536 |
| `test_s8b_experiment_numbers.py:61` (`test_approved_numbers_match_independent_golden_literals`) | `APPROVED_EXTIME_S`=5、`APPROVED_REPS`=5 |
| `test_s8c_preregistration_core.py:2618` (`test_decider_version_binds_cross_module_semantics_to_v9`) | `DECIDER_VERSION`="s8c-decider/v9" |
| `test_t793_publication_ledger.py:87` (`test_publication_identity_literals_and_schema_are_exact`) | `PUBLICATION_FAMILY_ROOT`="88d68f91…"、`PUBLICATION_LEDGER_KIND`="individual_publication"、`PUBLICATION_LEDGER_SCHEMA_VERSION`="t139-publication-reservation/v1" |
| `test_trial_registry.py:9042` (`test_t1957_schema_versions`) | `MANIFEST_SCHEMA_VERSION`="p3-8c-trial-manifest/v3"、`REGISTRATION_SCHEMA_VERSION`="p3-8c-trial-registration/v3" |

資料・派生値 pin (production の関数や shell を通さない、5 file / 5 関数):

| file:行 (関数) | pin 先 |
|---|---|
| `test_paper_story_a1_headline.py:1232` (`test_existing_a1_non_touch_manifest_is_empty_from_base`) | manifest 17 path が固定 2 区間 (base..tip) で変更されていないこと、区間の祖先関係、対象 path の作業木が clean であること (`git diff --exit-code`) |
| `test_paper_story_a1_paired.py:903` (`test_legacy_frozen_bytes_have_independent_literal_goldens`) | v2 policy・2026-08-26/27 preregistration 一式・headline code・sizing tools の実 bytes の SHA256 literal と file 集合 |
| `test_skip_classification.py:315` (`test_readme_conditional_unrun_census_names_all_nodes`) | `orchestrator/tests/README.md` の「条件付き未実走」節が既定 nodeid を列挙していること |
| `test_t1434_t1222_science_slice.py:409` (`test_pinned_jobs_requirements_are_exact`) | test 内 helper が資料から導出した path 集合 = literal tuple (T-1222/T-1434 外部 jobs prompt・receipt・oracle) |
| `test_t189_oracle_wiring_slice.py:132` (`test_pinned_jobs_requirements_are_exact`) | 同上 (T-1222/T-1393 外部 jobs prompt・receipt) |

pin と挙動検査の併存 (同じ関数が資料の hash・文字列を pin し、かつ production の関数か shell を実行する、3 file / 3 関数):

| file:行 | pin 先 | 併存する挙動検査 |
|---|---|---|
| `test_b10_backoff_grid_submit.py:137` | `docs/b10-backoff-static-tail-preregistration.md` §8.2 の文字列 | shell 構文検査 |
| `test_floor_pair_job_contract.py:91` | `docs/decisions.md` D2138 の 3 spec hash | shell `select_pin` の実挙動 |
| `test_t2187_adaptive_const_probe.py:4130` | `docs/backoff-policy-performance-preregistration.md` の SHA256 | production reader の実行 |

(D) でない (読んだ代表が production の挙動を検査、26 file): audit_dangling_commits、calibrator_certify、campaign_import_invariant、check_branch_landed、check_branch_rescue、check_wave_startup、codex_agents、codex_reasoning_ab (sibling)、codex_worker_launch、codex_worker_launch_budget、codex_worker_ledger、dev_wave_codex、dev_wave_land、flaky_test_holds_contract、plot_a1_sized_paired (`:388,471` とも production の closure 検査を含む)、plot_a2_certification、plot_b10_static_tail_formal (`:414` は fig8 成果物の存在・production の `validate_repo_closure`・caption 整合)、ruleops、s8b_floor_campaign (sibling)、s8b_ratified_freeze、s8c_preregistration_invariant (check_docs 本番 gate の負例)、s8c_preregistration_predicates、spool_fold (`:500` は `plan_fold` の番号導出、`:1753` は helper 経由の byte-exact 挿入挙動)、t189_task_catalog、task_run_aggregate、wave_land_window。

未確認候補: 291 − 45 = 246 関数 (`inventory/list-D.txt` の全件から上の代表を除いたもの)。file 単位の件数・台帳秒は `verbatim/plan-result.md` の「(D) 裁定パッケージ案」表にある。scanner の (D) 判定は「docs/.md path literal + read/hash/== 比較 + `orchestrator.*`/`tools.*` の直接 call が無い」という heuristic で、tools/ 系 test の import (sys.path 経由) を解決できないため過剰に拾う。

## 6. 受入 worker 時間の差 (台帳換算)

- 削除 node の台帳 entry: 33.000 + 0.001 × 5 = 33.005 s。
- 台帳合計 17,958.848 s (24,379 entry) → 換算 17,925.843 s。worker 時間 4.9886 h → 4.9794 h (−0.184%)。
- 台帳 file は編集しない (consumer は余剰 entry を許容し、collection との完全一致を要求しない。`test_acceptance_schedule_order.py` の coverage 検査は「収集 node のうち台帳にある割合 ≥ 0.90」で、今回の 6 node は全件台帳にあるため割合はごく僅かに下がるが、閾値には遠い)。
- wall・setup 費用・collection 時間の短縮は測っていないし主張しない。

## 7. scanner の限界と取りこぼし

- 合成 fixture の抑制 (引数 `tmp_path`/`pytester`/`monkeypatch`、本文の `write_text`/`mkdir` 等) は真の不在も落としうる (抑制 273 関数 / 510 証拠)。
- `production_targets` は `orchestrator.`/`tools.` の module-level import しか解決せず、tools/ 系 test (sys.path 経由・subprocess 経由) で空になる (A/B/C 候補の 101 関数)。
- AST 同一 (decorator 込み) は「同じ code」を示すだけで、alias が指す module や helper の実装が違えば別の受理集合を検査している。
- parametrize の `==` 比較は型境界を消す。型まで一致 (repr 一致) する row だけが重複。
- **通常関数 ⊂ parametrize row、別 decorator 間の同値 row は拾えない** (相談 B が `test_p3_s4_loop.py` で 5 件を発見。同型の取りこぼしは他 file にも残りうる)。
- 未評価 parametrize row 1,198 件 / container 133 件、flag literal の source 未解決 3,880 件。
- 動的 import・path 組立・fixture/helper 経由・継承 test は追跡しない。

## 8. この dir の中身

- `inventory/inventory.md` — scanner v1 の集計 (4 分類・B1 group・B2 row・C・D pin 先・抑制内訳)。`inventory-v0.md` は初版。
- `inventory/list-{A,B,C,D}.txt` — 分類別の候補 (protected 除く)。1 行 = `file:開始-終了 qualname | node 数・台帳秒 | 証拠種別 | production_targets`。
- `inventory/excluded-suites.txt`、`sibling-owned-files.txt` — 除外 file。
- `verbatim/` — brief、段 4 裁定、plan、相談 A/B、scanner author/fix1 の報告と所見、author 報告、scanner 実体の逐語 (`.md`)。
- `mutation/` — 変異 spec (probe/post × H/L)、harness 結果 JSON (probe/post × H/L、baseline と各変異の失敗 node・dispatch receipt path)、`mutation-summary.md`、`deleted-nodes.txt`。
- `verbatim-normalization.json` — 逐語 4 file (相談 A/B、レビュー A/B) の行末 space/tab だけを可逆に除去した記録 (原文 sha256・byte 数・行別 suffix hex・復元法)。可視文字は不変。
- inventory.json (17 MB) は repo へ入れない。job dir に sha256 付きで残す。

## 9. 主張しないこと

- 「検出力を失わない」の一般証明。示すのは §3 の同値性と §4 の登録変異に対する検出集合の保存だけ。
- 受入 wall の短縮。
- (A)(C) の網羅的な不在証明。plan の 112 件確認は 1 本の read-only 子の読解で、相談 A は独立再確認していない。
- (D) 246 件の個別分類。§5 の「pin と挙動検査の併存」3 関数は純粋な pin ではなく、「(D) でない」26 file は読んだ代表 1〜2 本での判定。
- 変異走の実行元は DW-M07 が書く独立 clone ではない (§4 erratum)。
