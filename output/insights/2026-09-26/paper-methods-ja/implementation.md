# 日本語方法節の実装対応メモ (2026-09-26 版)

対象本文は [方法節草稿](methods.md)。本稿は前稿 (2026-09-21 版、`output/insights/2026-09-21/paper-methods-ja/implementation.md`、
worklog entry 1816) の表と節を継承し、採用時点の local main `6d198ca8a` (2026-09-26 17:17 JST の fold) と一次資料で次を照合して
足し・直した: 前稿の採用時点 `36fb14a3d` より後に着地した機構の表 (下の「09-22 以後の機構」、全行を `6d198ca8a` で `ls` / `grep` 照合)、
状態が動いた既存行 (K2 の同 job pair、MoCC の X / P 計装と温度述語、A-1 の認可 record の使用、B-4 の carrier)、境界節と読み分けの表。
**それ以外の行 (「主要記述とコードの対応」の表ほか) は前稿・前々稿の照合 (local main `482f19b88` / `36fb14a3d`) のままで、本稿では
関数名の再照合をしていない。** 本資料のための新規 CC 合成・性能測定は行っていない。以下の「実装済み」は記載した関数・経路が照合した
main に存在し、その挙動が本文の記述に対応することを指し、その機能を使った正式実験の完走を含まない。「使用」は、その機構を実際に使った
attempt・走行を worklog entry または insight で名指しできることを指す。本資料は新しい論文シリーズ、実験登録、判定器ではない。前稿以前の
ファイルは書き換えず、本稿は別稿である。

## 正本の優先関係と執筆裁定

- `docs/decisions.md` D1598: 方法の核を CC、対象実装の action vocabulary の拡張、毎反復の正しさゲートに
  置く。説明の忠実性、proof chain、試行 provenance は補助に留める。
- 同 D1936 (全 50 項)・D2044 (全 39 項)・D2104・D2120・D2148・D2150・D2172・D2174: 採用済みの変更と
  実装完了を分ける。裁定本文だけでは実施済みにならない。本稿は各変更の追跡台帳を作らない。
- 同 D2148 項 11: 一次資料から事実を再抽出する docs-only wave には段 6 の read-only 独立レビュー 1 本を
  残す。本稿はその適用例である (README.md)。
- `docs/paper-story/2026-09-20.md` §6: certified の意味は「固定条件で certified な correctness の観測
  (性能の判定ではない)」であり、「certified は実際に build された bytes についての判定であり、要求した
  構成が build されたことは含意しない」。本文 §1 の定義はこの 2 文に揃えた。同版は local main `b7f970dfa`
  (2026-09-20 07:04 JST) から導出されており、前稿の基準 `482f19b88` との差 (下の「story 未反映の着地」) は
  前稿が明記した (本稿は継承する)。B-8 / K2 対照口 / B-5 の記述には論文ストーリーの版を出所として使わない。
- `docs/paper-story/README.md` の stale 注記 (2026-09-20 時点 3 件): B-7 材料稿の図 10 の着地、
  **B-7 の限定付き充足 (D2174 項 3)**、K2 3 巡の図 12 の着地。方法節は数値・図を転載しないので直接の影響は
  ないが、B-7 の状態語は同版 §8 (「要件充足へは昇格させない」) でなく D2174 項 3 で書く。同注記に無い着地
  (凍結 v2 g1 の発効 D2180、pin 前進 [T-2304]) は下の「実走・契約・未了の境界」節の「story 未反映の着地」で扱う (前稿から継承)。
- D2150 項 1 と `output/insights/2026-09-20/t2304-pin-advance/README.md`: pin 前進は承認済みかつ実施済み
  (main `482f19b88`)。前進が動かす identity の層と動かさない層、旧系列が固定 checkout から走ることを同 README
  §1・§4 から引く。前進は探索・軸採用の解禁を含まない (D2134 項 9、D2159 項 8・9)。
- `docs/phase3.md`「kickoff の最小スコープ」「現行 Phase 3 must と発火条件」「後続段」: 有効な編集契約と
  段ごとの実装・実走の射程を引く。冒頭の古い日付の要約だけで現在の全状態を決めない。
- `docs/phase3-main-experiment.md`: `output/s1-freeze/known_axes_freeze.json` の source sha256 として
  凍結されており、確定値の追記は `FreezeError` になる (entry 1702)。検証相の確定値は D2160・insight・
  results 稿に日付付きで置かれ、同文書への追記は未履行の繰延べである。
- **B-8 (2026-09-21 版で追加):** 規則の正本は事前登録 v1 本文 (`docs/b8-final-candidate-longrun-verify-preregistration.md`、
  raw sha256 `6ccb18c7…`、発効 commit `624c84986`)。登録の作成は D2175、対象・定義・試走の段階認可は D2186 項 1、
  runner v5 と発効束 draft は D2190、発効と本走の承認は D2194 項 1、発効の形と実施手順は D2202。実施の件数・日時・
  request・判定は結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md` と発効記録
  `output/insights/2026-09-21/t2807-b8-effective/README.md` (entry 1791) から引く。論文ストーリーの版と、同日の
  結果・要旨・限界の草稿 (entry 1801) は出所にしない。
- **K2 の同 job stock 対照口:** 実装 = D2183 (entry 1746)、初投入の不成立 = D2187 (entry 1754、
  `output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §0)、pair mode への修復 = D2205 (entry 1795、
  `output/insights/2026-09-21/t2795-pair-repair/README.md` §0)、再投入の認可 = D2211 項 1、pair の成立と 4 巡目 = entry 1823
  (`output/insights/2026-09-22/t2795-k2-pair-resubmit/README.md`)。裁定の本文を実走済みの証拠にしない。
- **B-5:** 事前登録 v1 = D2158、部品の段階実装と上限付き試走の認可 = D2172 項 4、試走の完走 = entry 1779、本走の段階認可 =
  D2200 項 1、Tier0 = D2215、親運用 = D2216、walltime = D2217、投入経路 = D2221、発効束 draft = D2222、本走の認可 = D2227 項 2、
  block 1 stage 1 の投入・中断と 6 比較の判定不能・費用案 = entry 1866 (insight `output/insights/2026-09-26/t2797-b5-cost-options/README.md` §2・§3・§7)、
  LLM 親の週次上限 = F1050。発効 commit `6fce61d6e` は採用時点の main の祖先でない (親 wave が `git merge-base --is-ancestor` で実測)。
- **2026-09-26 版で追加した正本:** 論文ストーリー `docs/paper-story/2026-09-26.md` (§0・§2 第 3 幕・§6・§8) を入力とし、数値・判定・状態は
  各行が引く D 本文・worklog entry・insight から写した。関数単位の軸 = D2214 (条件付き採用)・D2226 (段階 C)・D2234 (段階 D)・D2240 (既知最良との小比較)・
  D2243 項 1 (段階 E へ、未実装)。TPC-C 段 1 = D2224・D2225・D2230・D2232・D2238・D2244。比較基盤 = D2220・D2233・D2248。事前登録と実行器 = D2223・D2228・
  D2231・D2245・D2241。検出期待表 = D2239・D2246・entry 1855。pin C = D2236。trace 保全 = D2233 項 4・D2247。K2 の pair の成立 = entry 1823。
  **ComSys 原稿・旧草稿は出所にしない。**

## 主要記述とコードの対応 (前稿から継承。前稿が main `482f19b88` で再照合した行)

コードの参照はリポジトリ相対パスと関数名で示す。本文番号は methods.md の節番号である。前稿が前々稿の行のうち
`482f19b88` で変わった点を「区分と上限」に書いた。本稿はこの表を再照合していない。

| 本文 | 記述 | 実装アンカー | 区分と上限 |
|---|---|---|---|
| §1–2 | planner/coder/critic の分担、セッションによる反復駆動 | `orchestrator/campaign/p3_s4_loop.py` モジュール説明、`PlannerProposal`、`CoderProposal`、`planner_context_payload`、`drive_iteration` | 実装済み。関数は提案を受け取り、LLM 自体は起動しない。プロジェクト全体の無人化ではない |
| §1–2 | 導入済みの hole に限定したコード生成 | 同 `render_hole`、`quarantine`、`_run_one_iteration_resolved`、`orchestrator/campaign/backoff_hole_grammar.py` | 実装済み。backoff は値と一致する単一数値リテラルの一文。コード出力形式と非列挙空間の探索は同義でない |
| §2 | 骨格・stock 枝の保存、ホスト作用と軸文法の検査 | 同 `quarantine` → `orchestrator/campaign/diff_quarantine.py` `DiffQuarantine.validate`、`orchestrator/campaign/coder_effect_gate.py` `scan_host_effects`、軸文法 | 実装済み。字句検査は有限の規則。任意の外部作用・意味逸脱を完全に封じるとは書かない |
| §2 | 提案値と実コードの帰属を一致させる | 同 `assert_value_literal_consistent`、`_check_attribution_before_quarantine`、genome の構築 | 実装済み。値の対応を確認する範囲であり、一般的な意味等価証明ではない |
| §2 | patch の適用・評価・復元とソースの識別 | 同 `_run_one_iteration_resolved` → `patchharness.applied` → `loop.run_campaign`、`orchestrator/campaign/pipeline.py` `_prepare_evaluation_core`、`orchestrator/campaign/source_digest.py` `src_token`、`resolve_evidence`、`canonical_source_preimage_bytes` | 実装済み。pre-image は `-dD` で有効枝の `#define` / `#undef` を含む (D2108、2026-09-17)。指令と include の相対位置・`push_macro` / `pop_macro` は識別しない (D2120 項 7)。過去の測定を現在の差分だけで無効化しない |
| §2 | 拒否と重複提案を成功から区別 | `p3_s4_loop.py` `record_diff_reject`、`_resolve_duplicate`、`_run_one_iteration_resolved` | 実装済み。重複は保存済み証拠の再利用。毎回再測定したとは書かない。`dry-pass` は検疫のみ |
| §3 | 空履歴・異常終了・証拠欠落・検証赤は採用しない | `pipeline.py` `_execute_verification_repetition` → `verify_trace_dir_with_capability`、`_prepare_evaluation_core`、`orchestrator/verifier/core.py` `verify_trace_dir`、`report.py` `_anomaly_to_dict` | 実装済み。検証赤は循環・依存辺を含む構造化 `verify` 診断付きで abort。`verify_trace_dir` は protocol の証明面 (`assess_protocol_proof_surfaces`) を要求し、無ければ certified を返さない。指定された履歴と検証意味論の範囲に限る |
| §3 | 全検証構成・全反復の合格を要求 | 同 `CorrectnessWorkload`、`s2_correctness_workload`、`performance_correctness_workload`、`_prepare_evaluation_core` 内の pass/repetition 走査 | 実装済み。`legacy+s2` と `legacy+performance` は別の opt-in。全 caller で性能相当検証が既定とは書かない |
| §3 | 構造化反例と生存性・検疫拒否を critic へ提示 | `p3_s4_loop.py` `make_critic_digest` → `orchestrator/critic/digest.py` `load_rejections`、`load_liveness_rejections`、`render_rejections` | 実装済み (前稿は 3 関数を `p3_s4_loop.py` に帰属させていたが、所在は `orchestrator/critic/digest.py`)。`reflux=False` は赤い診断節を要約から除くだけで検証は継続。因果的な改善効果は未証明 |
| §3 | 状態保存と停止判定 | 同 `save_loop_state`、`load_loop_state`、`project_whiteboard`、`check_stop`、`drive_iteration` | 実装済み。予算・小変更の連続・逆方向推奨で止める。統計的最適性の判定ではない |
| §4 | trace 有効/無効の別ビルド・別実行 | `pipeline.py` `_prepare_evaluation_core` 内の `_build_one(trace=True/False)`、`_execute_verification_repetition`、`_run_bench` | 実装済み。buildcache/source_digest に観測者効果の検査を委譲。`TRACE` の実行時分岐化は許可しない |
| §4 | 測定の排他・反復・不安定性を記録 | 同 `_run_bench` → `bench_lock`、`orchestrator/calibrator/runner.py` `competing_bench_pids`、`measure_point`、`orchestrator/calibrator/stability.py` `remeasure_until_stable` | 実装済み。`unstable` は残り得る。全 measured COMMIT が安定・有意な勝者とは限らない |
| §5 | bench-first は opt-in、明白な劣位だけを未認証棄却 | 同 `ScreeningConfig`、`_prepare_evaluation_core` の `active_screening` 分岐 | 実装済み。下記の閾値と例外条件を持つ。段 4 LLM loop の通常評価順を変更するものではない |
| §5 | verify 後だけ COMMIT、測定値と認証を分離 | 同 `evaluate`、`_commit_prepared` | 実装済み。`do_bench=False` の COMMIT は `fitness_tps=None`。COMMIT の存在だけで性能選択可能とは言えない |
| §5 | 保存済み証拠を用途に応じて受理 | `orchestrator/campaign/artifact_admission.py` `require_admitted_campaign`、`require_persisted_certified_commit`、`CampaignReadPurpose` | 実装済み。`HISTORICAL_RAW` と `CERTIFIED_ACCEPTANCE` は異なる view。履歴読み取りは認証への昇格ではない |
| §6 | descriptor から固定候補を一つ指名 | `orchestrator/campaign/s8b_selector_input.py` `build_selector_payload`、`load_catalog`、`s8b_selector_output.py` `parse_selector_output` | 実装済み。固定候補の一つと理由を受理する部品。任意コード生成でも最終比較判定でもない |
| §6 | 正式評価が要求する証拠を照合 | `orchestrator/campaign/s8b_oracle_report.py` `_assess_window`、`_assess_campaign`、`build_observations` | 実装済みの評価部品。trial の検証・測定記録と登録を照合する。oracle 実走は未達で、全正式実験の完走証拠にはしない |
| §6 | 証拠があれば新規候補、なければ stock/tie を正直に返す | `docs/phase3.md` 冒頭「各 run の正直な出力契約」 | 系全体の契約。`p3_s4_loop.py` 単体による汎用最終選択の実装とは書かない。前提欠落は有効な tie でない |
| §6 | 材料レポートと説明を区別 | `orchestrator/campaign/layer3_report.py` モジュール説明、`build_report`、`render`、`_mechanism_view` | 記録の射影は実装済み。通常出力は `certifying_input=false`。機序仮説層 (v3) は K2 2 巡目で初適用され `mechanism_hypotheses` は critic 帰属記録の決定論射影 (D2143)。前稿の「空の予約区画・未実装」は 2026-09-18 に変わった。機序の証拠ではない |

## 09-10 以後の機構 — 実装済みの範囲と、各実験で実際に使った範囲

本文の該当節と、実装アンカー、使用した走行 (worklog entry / attempt) を分けて示す。「使用」欄は本稿が
参照する走行を示す。未掲載だけを未使用の根拠とせず、未投入・未使用は各行に明記する。

| 本文 | 機構 | 実装アンカー (main `482f19b88`。2026-09-21 版で追加・更新した行は `36fb14a3d`) | 使用した走行 | 実装済みだが未使用・上限 |
|---|---|---|---|---|
| §5 | A-1 sized の非認証 lane と 1 attempt 認可の投入経路 | `orchestrator/campaign/paper_story_a1_paired.py` `run_submit`、`_v3_barrier_before_bench`、`_run_complete_v3`、`positional_statistics`、`_classify_difference`、`CLASSIFICATION_RULES`；policy `paper_story_a1_paired.v3-sized.json` (`formal=false`、`promotion_prohibited=true`、`result_authority=sized-preregistered-descriptive-only`)；job body `tools/pegasus/paper_story_a1_paired.sh` | attempt-0001 (2026-09-18、entry 1636、job `4939`〜`4941`)：3 workload とも完走、分類は `resolved-above-floor`、6 arm の verifier anomaly 0 (`legacy` 条件)。descriptive 出力であり「A-1 の値」ではない | pilot 系 (`v3-pilot.json`) と sized 系は別 policy。分類語は事前登録 README (`resolved-beyond-floor` 等) と実装 (`resolved-above-floor` / `bounded-below-floor`) で表記が違い述語は同値 (entry 1636 の観察) |
| §5 | A-1 の再投入 gate と認可 record | 同 `_assert_no_prior_v3_bench_start`、`V3_SIZED_RERUN_AUTHORIZATIONS` (定数 1 件)、`_exact_v3_rerun_authorization`、`run_authorize_rerun` (subcommand `authorize-rerun`、schema `paper-story-a1-paired-rerun-authorization/v1`)、`_exact_materialization_destination` (公開先は兄弟 dir) | gate の拒否は attempt-0002 の実投入で確定 (2026-09-19、entry 1687、D2156、qsub 前 rc 2、副作用なし)。認可 record 機構は 2026-09-20 に着地 (entry 1736、D2178) | **2026-09-26 版の更新:** record を使った投入は attempt-0002 の 1 件 (2026-09-20、[T-2792]、entry 1755、3 workload とも完走・`resolved-above-floor`、非認証 lane のまま)。2 attempt は並記するだけでプールした推定量・再現判定を作らない (D2194 項 6)。3 本目の投入は採用時点までの entry に無い。record は署名でなく、「性能値を見た後の選択」を防ぐ装置でもない (D2178) |
| §5 | A-2 / A-6 certification の受領証束縛 | `orchestrator/campaign/paper_story_a2_certification.py` `preregister_attempt`、`record_submission_receipt`、`record_completion_receipt`、`record_acquisition_receipt`、`finalize_raw_manifest`、`_cell_source_binding_status`、`_require_cell_src_token_role`、`_parse_condition_gate_admissions`、`collect_results` (outer status)、`materialize`；policy `paper_story_a2_certification.v2.json`、`paper_story_a6_certification.v2.json`；性能条件側の検証 fan-out `_validate_verify_fanout_hosts` → `orchestrator/campaign/verify_fanout_worker.py` | A-2 attempt `t2364-20260907b` (2026-09-07、`observed-positive`、4 cell certified、`source_binding_status=bound`)、A-6 attempt `a6-20260908b` (2026-09-08、`reject`、2 cell certified)。いずれも 1 node で走った | policy の `scheduler.nodes` は 5 へ実装済み (entry 1686) だが A-2 / A-6 の新 attempt は無い (別途 nodes=5 の probe `t2489-20260918a` が fan-out を実走したが、outer status を作らず A-2 の attempt に数えない)。成果物の `compile_out_evidence_scope` / `independent_observation_limits` は自己申告。条件関門については admission record (`admitted` / `use_class` / `unestablished_meaning_macros` / `record_ids`) が残り、参照先の supply-effectuation / runtime-meaning record の本体は残らない。correctness 側の実 argv は独立に記録されない (`workload_argv_observation`) |
| §5 | certification 経路の descriptive 利用 (同一候補 fixed 5 µs の 3 workload 同時期測定) | 同 module の closed set に足した study `paper-story-b7-fixed5-regression` (`paper_story_b7_fixed5_regression.v2.json`、nodes 5)、submitter `tools/pegasus/submit_paper_story_a2_certification.sh` | attempt `b7f5-20260919a` (2026-09-19、entry 1705、request `10807`〜`10809`、6 cell certified、outer `reject`)。稿の床値判定 (read-heavy だけ退行) はコード外 | B-7 は D2174 項 3 で「単一 attempt・descriptive・非認証・反復間安定性は未判定」の限定付き充足。反復 attempt は認可されていない |
| §6 | B-10 待ち方 grid の事前登録と driver | `docs/b10-backoff-shape-preregistration.md`、`orchestrator/campaign/b10_backoff_shape_sweep.py` `holm_adjust`、`cell_effects`、`_shape_differences`、`_write_reports`、`ReportAnalyzerIdentity`；job body `tools/pegasus/b10_backoff_shape_campaign.sh`、`submit_b10_backoff_shape.sh` | report phase `978195.nqsv` (実行 2026-09-05、記録と D1678「現行 report で閉じる」の裁定は 2026-09-07)。単独 results 稿は entry 1737 | `official_certification` は `false`。判定が及ぶのは登録した 1 つの対比だけ |
| §6 | B-10 静的右 tail の事前登録と driver | `docs/b10-backoff-static-tail-preregistration.md` (2026-09-19 末尾追記 = 第 2 cohort の地位)、`docs/b10-backoff-static-tail-submission.md`、`orchestrator/campaign/b10_backoff_static_tail_formal.py` `analyze_interval`、`analyze_cohort`、`materialize_report`；投入 `tools/pegasus/submit_b10_backoff_grid.sh` | cohort 1 (2026-09-15、`not-observed`)、cohort 2 (2026-09-19、entry 1690、同 verdict、D2157)。正しさは `legacy` 条件の別走行で各 120 記録 | 2 cohort の統合 verdict・プール推定は無い。帯 901〜998 µs は未測 (D2027)。性能は未認証 |
| §3 | 採用候補 2 genome の検証相 | **リポジトリ内に runner は無い。** 判定器 `python3 -m orchestrator.verifier` (`orchestrator/verifier/cli.py` → `core.verify_trace_dir`)、identity は `source_digest.resolve_evidence`、extime 選択は `orchestrator/campaign/s1_verify_extime_calibration.py` `choose_extime` を runner が流用 | 校正 6 job + 本走 12 job (2026-09-19〜20、entry 1702、D2160)。判定集合 30 verify / 候補 (本走 24 + 校正完走 6) で anomaly 0、校正 10 s の未完走 2 件 / 候補は `indeterminate` として開示 | runner (Codex author 作、v1 1301 行 / v2 1384 行) は job dir に保全され repo に入っていない (insight `verify-phase-adopted-backoff/README.md` §4.3)。S-1 事前登録本文への確定値追記は凍結束縛で未履行 |
| §3 | B-8 最終候補の長時間・独立反復 trace 検証 (**2026-09-21 版で追加**、main `36fb14a3d` で照合) | 規則 = `docs/b8-final-candidate-longrun-verify-preregistration.md` (v1、発効 commit `624c84986`)；発効束 JSON `output/insights/2026-09-21/t2807-b8-effective/verbatim/b8-effective-bundle.json` (schema `b8-effective-bundle/v1`、sha256 `059536a7…`)；**runner v5 はリポジトリ外** (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2807-b8-prerun/probe/verify_phase_runner.py`、2103 行、sha256 `4ff6652a…`。B-8 で使った操作は `prerun` / `calibrate` / `verify` / `summarize`、未完走の枠のための `verify --resume` と `reverify` は発生 0)；判定器 `python3 -m orchestrator.verifier` (module 9 file の sha256 を発効束に固定)；案 A の build は template patch `patches/silo-backoff-trigger-gating-variant.patch` | 校正 3 job (`14640`〜`14642.nqsv`、2026-09-21 08:45〜09:11 JST) と本走 6 job (`14686`〜`14691.nqsv`、09:17〜10:13 JST)、Pegasus gen_S (結果稿 §3、発効記録 §3〜§5、entry 1791。手順は D2202)。判定集合は本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠 (3 workload × extime 6 s / 10 s、各 1 回) の 30 枠で、`summarize` の 3 値判定は `pass`。校正の未完走・bench 失敗・規約不適合は 0 件、再検証・再開・再投入は 0 回 | runner は repo に入っていない (D95)。runner の bundle 検査 (`validate_bundle`) は `status` と承認情報を見ない (発効記録 §1.1) — 未発効の draft で走らせない防止は、tracked path への固定と投入直前の sha256 照合という手順による (D2202)。seed 値は記録しない。1 cohort だけ。性能値を含まない |
| §3 | verifier の容量 (packed 配列) | `orchestrator/verifier/dsg.py` `_PackedVersions`、`_PackedProducer`、`DSG._build_compact_packed`、`_edge_worker`；`core.py` `verify_trace_dir` | 計算ノードの compare (2026-09-20、entry 1744、D2181): 10 s trace 2 件が完走し、旧版と `result_to_dict` が byte 同一 | 検証相 (entry 1702) はこの変更**前**の verifier で走った。story 2026-09-20 版には未反映 |
| §2 | K2 型付き critic 診断 | `p3_s4_loop.py` `k2_critic_diagnosis_from_bytes`、`_validate_k2_critic_diagnosis`、`planner_context_payload(k2_critic_diagnosis=...)` (K2・非 B-4・reflux on を要求)、`k2_next_generation_inputs` (両 role へ同一診断を組み込む) | 3 巡目 (2026-09-19、entry 1691、job `10761.nqsv`)：critic-2 逐語から 6 field を組み立て planner-4 / coder-4 へ届け、1 評価が certified | 実 consumer は登録 Claude role への親の inline 送付 (D2155)。「届いた」と「効いた」は別。3 巡とも legacy critic で B-4 ablation には非適格 |
| §2 | K2 同 job stock 対照口と pair mode (**2026-09-21 版で更新**、main `36fb14a3d` で照合) | `p3_s4_loop.py` `_run_stock_control_resolved` (keyword `authorization_session`)、`main` の pair mode 分岐 (`--run-iteration` と `--stock-control` の併用、`--isolate-worktree` 必須。`--stock-control` 単独は B-5 の slot 起動で従来どおり)、stock 経路限定の `capability_resolver`；`orchestrator/campaign/loop.py` `authorization_session`、`_AuthorizationSession`、`_authorize_measurement` / `run_campaign` の keyword-only 引数 `authorization_session`；job body `tools/pegasus/p3_s4_loop_pegasus.sh` (`IZANAGI_S4_STOCK_CONTROL=1` は driver 1 起動の pair で、`IZANAGI_S4_PROPOSAL_PATH` を要求する) | 修復前の 2 process 形の初投入 1 job (`13339.nqsv`、2026-09-20、entry 1754、D2187。pin 前進後の superproject `6a3e15809` から、CCBench を driver の PIN `511c9538` へ checkout して投入)：候補 10 の再評価は certified、stock は `campaign_claim.acquire_claim` の `ClaimError` で build の前に停止し、`src_token == STOCK` は未確認で **pair 不成立**。pair mode (entry 1795、D2205) の実機投入は **0 件** | 成功条件 = certified かつ `src_token == STOCK`。claim leaf (`campaign_claim.py`) の bytes と one-shot 性は不変。**2026-09-26 版の更新:** D2211 項 1 の認可で pair mode の再投入 1 job (`16269.nqsv`、2026-09-22) が成立し (候補 10 と stock がともに certified、stock の `src_token` は stock)、4 巡目の 1 job (`16312.nqsv`) も候補と同 job の stock がともに certified (entry 1823。CCBench は driver の PIN `511c9538` へ checkout)。同 job の比は記述値で、改善・優劣・診断の効果の証拠ではない |
| §3 | MoCC の trace-hook (X / P 計装) | `patches/instr-mocc-lock-coverage.patch` (計装 template 版 `instr-mocc-lock-coverage-temperature.patch`)、`orchestrator/campaign/s3_mocc_lock_coverage.py`、`mocc_trace_pair.py` (pair receipt `mocc-trace-pair-receipt/v2`)、`mocc_g2_discriminator.py`、`mocc_g2_repro_ledger.py`；job body `tools/pegasus/mocc_trace_pilot.sh` | pilot 対 (2026-08-26、`accepted`)、G2 観測 (i)〜(iii) (2026-09-18〜19、[T-2774] / [T-2779] / [T-2780])、機械実証 wave 1 (entry 1666、D2147) / wave 2 (entry 1701、D2159) の stock 走 | X / P 計装は 2026-09-23 まで CCBench pin の tree に無く patch で当てた (旧 pin `511c9538` について D2083、`e9e477ca` でも patch のまま)。**2026-09-26 版の更新:** pin は C (`68106660`、gitlink を `6d198ca8a` の `git ls-files -s` で確認、`pin.CURRENT_PIN = "6810666"`) へ進み、C の source が計装を持つ (D2236)。旧来の「pin + 計装 patch」の経路は C では計装 patch が当たらず走らないので、検出期待表の MoCC 行は壊し patch を C に単独で当てた (D2246)。G2 の観測 (i)〜(iii) は旧 pin 上の記録。全 leg `official_certification=false`。G2 の根因は未同定 |
| §3 | MoCC の軽量 witness | hook commit W `5b02546f` (submodule branch `izanagi-t1943-mocc-g2-witlight`、上流未公開)。**izanagi 側の module ではなく CCBench 側の変更** | 4 arm × 60 走 (2026-09-19〜20、entry 1696)：on 0/60・0/60、off 1/60・1/60、discriminator 未発火 | main の pin に含まれない。非 certifying。観測者効果の除去は言えない |
| §1 | MoCC 温度述語 template と機械実証 | `patches/mocc-temperature-predicate-variant.patch`、`orchestrator/campaign/axis_mocc_temperature.py` (`PROOF_PIN = e9e477ca`、探索用 `PIN = pin.CURRENT_PIN` の参照式は不変で、指す commit は前進に追随)、`s3_mocc_template_proof.py` `compute_checks`、`quarantine_controls`、`instrumentation_preservation`；`s3_mocc_mutation_proof.py` | wave 2 `11161.nqsv` (2026-09-20、entry 1701、30 check all_pass)、wave 1 `5096.nqsv` (entry 1666) | 探索・正式な軸採用は未解禁 (D2134 項 9、wave 2 の緑は認可を与えない)。**2026-09-26 版の更新:** pin が C へ進んだ後も `axis_mocc_temperature.py` は変えず、`PROOF_PIN`・template・proof は `e9e477ca` に束縛したまま、探索用 `PIN = pin.CURRENT_PIN` は C を指す (consumer は wrong-oid の負例 1 箇所だけ、D2236 項 1)。前進は探索の解禁を含まない |
| §4 | 床値 pair protocol v3 (B-4 の `floor`) | `orchestrator/campaign/floor_pair_driver.py` (`SPEC_SCHEMA = floor-pair-spec/v3`、`run_window`、`finalize_floor`、`GainDifference`)、凍結 spec 3 本 `output/env/pegasus/floor-pair/t2288-f1/`；job body `tools/pegasus/floor_pair_campaign.sh`、submitter `submit_floor_pair.sh` | w1 3 job `10711`〜`10713.nqsv` (2026-09-19〜20、entry 1693)：3 窓とも `complete`、各 62 標本 | w2・finalize・集約・採用・事前登録 §5 記入は無い。driver は自ら「spec が結果前に凍結されたことを証明しない (freeze receipt は無い)」と宣言する |
| §4 | 条件関門の意味 witness の拡張 | `orchestrator/campaign/condition_meaning_gate.py` `evaluate_define_supply_effectuation`、`evaluate_define_runtime_meaning`、`declare_define_runtime_meaning`、`MeaningWitnessDeclaration` | 関門族自体は A-2 / A-6 / 同一候補 3 workload 測定 / A-1 attempt-0001 の各走行が通過 (検証相は identity 束縛だけで関門を通していない)。`#ifdef` 形と非一意 directive の観測 (D2182、entry 1745) は 2026-09-20 着地 | story 2026-09-20 版には未反映。関門は「供給されたか」「同じ意味を持つか」を独立に見るが、実行到達性までは閉じない (D955) |

## 09-22 以後の機構 (本稿で追加、全行を main `6d198ca8a` で照合)

| 本文 | 機構 | 実装アンカー | 使用した走行 | 実装済みだが未使用・上限 |
|---|---|---|---|---|
| §1・§3 | ccbench pin C | gitlink `external/ccbench` = `68106660686232781bca3be792a750d3e19d7a8a`、`orchestrator/campaign/pin.py` `CURRENT_PIN = "6810666"`・`CCBENCH_FULL_SHA` (D2236、entry 1850) | 検出期待表の MoCC 行 (entry 1864)、MoCC の較正と差し込み (entry 1867) | 前進の範囲は D2150 項 1 の ①④⑦。`p3_s4_loop.PIN` は `511c9538` のまま (D1936 項 1、F1051)。探索・軸採用の解禁でも MoCC の certified 系列でもない。C-1 の性能比較 0 件 |
| §2 | 関数単位の軸の受理契約と骨格 | `orchestrator/campaign/silo_policy_grammar.py` `validate_policy` (型付きの構文検査)、`silo_policy_compile.py` `check_policy_body`・`compile_policy` (単独 TU の `-Werror` compile)・`run_ubsan_harness`、骨格 api `silo_function_policy_api.hh`、手書き方策 `silo_function_policy_hand/`、機構変異 `patches/broken-silo-policy-*.patch` | 段階 C の診断走と焦点試験・機構変異 (entry 1830、D2226) | 診断 build は NON_ADMISSIBLE で `pipeline.evaluate` を通さず certified 候補と称さない (D2226 項 5)。安全の主張は D2214 項 2 の条件付き |
| §2 | 型付き有限 IR と偵察・小比較 | `orchestrator/campaign/silo_policy_ir.py` (式木 `Const`・`Reason`・`Attempt`・`StateRef`・`Compare`・`Select`・`Min`・`Max` ほか)、`silo_policy_recon.py` `run` (phase `initial` / `compare` ほか)・`aggregate`・`compare_aggregate`・`_cases` (compare の 6 方策と job 番号 mod 6 の巡回)・`_backoff_fixed_define` (静的 10 µs の実効 define 検査) | 段階 D の初走 8 job + 再測 (entry 1846、D2234)、小比較 8 job (21389〜21396.nqsv、entry 1856、D2240) | 3% 線は未較正の探索的な目印、再測なし、多重選択の補正なし。後段へ渡すのは段階 D の `projection.json` の二値と射程文だけ (手順書 §3-D)。段階 E の driver・role は未実装 (D2243 項 1 は裁定) |
| §2 | 5 手法の比較基盤 (S1) | `orchestrator/campaign/t2849_comparison_harness.py` `run_series`・`run_block_controls`、`t2849_generators.py` `random_value`・`sweep_order`・`gp_posterior`・`expected_improvement`・`BOGenerator` ほか、`p3_s4_loop.py` の `--reference-genome` (比較基盤の slot に限る)、巡 tool `tools/t2849_llm_round.py` (D2233) | [T-2850] 試走 block 1 の 6 job (21512〜21517、entry 1863。3 系列が欠測) | 試走は block 2・3 をユーザー指示で止めた。手法間の比較は無い |
| §2・§4 | MoCC の差し込み | `p3_s4_loop.py` `--protocol {silo,mocc}` (既定 silo)、protocol が mocc のときだけ campaign pin を C の literal にする分岐、job body の env `IZANAGI_S4_T2849_PROTOCOL`、意味検査の翻訳単位の切替 (D2248) | pin C での MoCC の認定較正 3 件 (rr5・rr50・rr95、records 1,000,000)、計算ノードの生死確認 (系列 1 本の 5 slot と block 対照 1 slot が certified、entry 1867) | 疎通の生死確認であって比較ではない。K0 LLM の MoCC 経路は計算ノードで未走行。第 2 プロトコルでの疎通 (20〜40 候補 × 3 workload) は未 |
| §3 | TPC-C 段 1 の trace v3 の読みと存在契約 | `orchestrator/verifier/model.py` (`Integrity.existence_violations`・`existence_violation_details`、`clean()` が件数 0 を要求)、`dsg.py` `_existence_rows`・`_check_existence`、`core.py` `result_to_dict_v3` (D2224・D2232) | Silo の実 TPC-C trace 1 本 (36,156 取引) の公開 API での判定と違反注入の拒否 (entry 1843) | 契約は Silo の版付けに裏付けた段 1 に限り、段 2 へ広げない。v2 (YCSB) では存在検査を走らせない |
| §3 | pipeline の TPC-C 受理 | `orchestrator/campaign/pipeline.py` `_run_trace` (`tpcc_` かつ 57:43 の 4 flag の文字列一致だけ trace、判定器の後に v3 を要求) と v3 の構造化出力の配線 (D2238) | 実 TPC-C trace (Silo) と実 stdout を executor に通した判定と、存在違反・末尾欠落の写しの拒否 (entry 1852) | production の build (buildcache) は `ycsb_<protocol>.exe` だけで campaign の TPC-C 評価の配線は無い。現 pin の tpcc 実行体は v2 で v3 要求に拒否される。trace の取引種別は pipeline で検査しない |
| §3 | TPC-C の CCBench 側候補と規律 1 の証拠 | CCBench の local branch (repo 外、未 push を含む): `izanagi-tpcc-v3-trace` (C1・C2、人間が push 済み、D2235 項 1)、`izanagi-tpcc-v3-mocc` (C1'・C3、D2230)、`izanagi-tpcc-v3-silo-mocc` (C → C1' → C3 → C2'、未 push、D2244)。D297 の検査器 `tools/check_trace0_preprocess_identity.py` | 結合確認 1 走 (29455.nqsv、Elapse 243 秒、entry 1862) | D297 の検査器は C → C2' を `include/tpcc.hh` の header 差分で拒否 (rc=1)。受理方式は 4 択でユーザー裁定待ち。pin・gitlink は不変 |
| §3 | 検出期待表の壊し build と発火診断 | `orchestrator/campaign/s2_verify_calibration.py` `_broken_build_and_verify`、patch `patches/broken-silo-*.patch`・`control-silo-*.patch` (新規 14 本)・`broken-silo-sort-nonswo.patch`・`broken-silo-trigger-misattr.patch`・`broken-mocc-*.patch` (既存 4 本 + `broken-mocc-skip-canonical-restore.patch`)・`control-mocc-negated-temperature-predicate.patch`。起動器は repo 外 (D2239 項 5、D2246 項 1) | silo 15 行 (pin `e9e477ca`、entry 1854)、V07 1 job (entry 1855)、MoCC 34 cell 4 job (pin C、entry 1864) | 各 cell 1 回の有限の走。発火診断は判定に使わない。検出力の網羅的な証明ではない。si の行は採用時点で未走 |
| §3 | trace 保全口の inventory | `pipeline.py` の env `IZANAGI_TRACE_ARCHIVE_ROOT` 分岐、inventory の `verifier_argv`・`repo_head`・`ccbench_pin` / `ccbench_pin_declared`・`patch_sha256`・`tracked_diff_sha256`・`verifier_module_sha256`、git 起動 helper `_archive_git` (D2233 項 4、D2247) | 生成器のある 17 図の描き直し (entry 1865) は保全口と別の作業 (login で描き直し、値の差 0) | opt-in。論文根拠の実験の job body で有効にするのは残り。保全の失敗は評価結果を置き換えない |
| §5 | B-5 の Tier0 と本走の投入経路 | `orchestrator/campaign/b5_generator_contrast.py` `_b5_tier0_build_inputs`・`_run_b5_tier0_smoke`・`SeriesLedger`、report `b5_generator_contrast_report.py`、launcher `tools/pegasus/b5_contrast_launch.py`、巡 tool `tools/b5_llm_round.py` (D2215・D2221) | 本走 block 1 stage 1 の 12 job (2026-09-23 21:53 JST 投入、Elapse 計 126,426 s、entry 1866) | 現行 cohort `b5-registered-v1` は 6 比較すべて判定不能 (欠測)。続行形はユーザー裁定待ち。発効 commit は main に未着地 |
| §6 | 転移の実行器と解析器 | `orchestrator/campaign/t2851_transfer_runner.py` `freeze_candidates`・`activation_allowed`・`run_job`・`verify_candidate`・`verification_status`、`t2851_transfer_analysis.py` (D2241) | 錨 wh-base だけの生死確認 4 回 (4 回目で検証が certified、entry 1857) | 留保 cell は 0 走。測定は未発効。TPC-C の検証は認定経路の接続まで indeterminate ([T-2866]) |

## screening の具体的な読み分け

`ScreeningConfig` の基準 throughput を T₀、between-run floor を f とすると、bench-first の遅さによる棄却
条件は T < T₀(1 − kf) であり、k は 1.5 以上である。これだけでは棄却せず、`unstable` でないこと、abort 率が
得られていること、基準 abort 率に係数を掛けた値を超えないことも要求する。古い基準点なら screening を
無効にして verify-first に戻る。この閾値は「候補が優れている」ことを認定する閾値ではない。

## 記録・経路の読み分け

| 記録・経路 | 読めること | 読めないこと |
|---|---|---|
| 性能だけの探索・診断 | その条件で得た raw な観測 | 検証済み fitness、正式選択、headline |
| bench-first の検証前 `BENCH_DONE` | 性能標本が取得された | 検証通過 |
| `screen-slower-than-floor` で abort | 保守的スクリーニングで棄却された | 正しさ違反が検出された、certified な劣位が確定した |
| 全 verify 後の測定付き COMMIT | 指定検証を通し性能を記録した | すべての consumer で正式適格、安定性・優越性が確定した |
| 探索 namespace の certified outcome | 当該探索で検証を通った | official namespace の正式認証成果物になった |
| `HISTORICAL_RAW` による履歴読み取り | 記録当時の事実を用途限定で読む | 現行の certified 判定へ再ラベルする |
| certification の cell `correctness=certified` | 当該 workload・当該 build bytes で legacy 1 回 + 性能条件 5 回の trace 検証を通った (workload の束縛は campaign lock と pipeline constructor による) | 性能の認証、要求構成が build されたこと (それは `source_binding_status`)、翻訳単位全体の意味一致、correctness 側の実 argv の独立記録 (`workload_argv_observation` = 未記録) |
| certification の outer `observed-positive` / `reject` | protocol の status (論理積) | 研究の成功・失敗、有意差、再現性 (`a4_noise_floor_status=open`) |
| A-1 sized の `resolved-above-floor` | 登録済み解析で区間が床の外にある (向きは平均の符号) | 「A-1 の値」、A-1 の充足、formal 化、反復間の安定性 (lane は `formal=false`) |
| 検証相の `pass` (判定集合で anomaly 0) | 操作的事実 | 1−εⁿ の確率主張、B-8 の取得、既存 certified 記録の昇格 |
| B-8 の `pass` (runner v5 の 3 値判定、**2026-09-21 版で追加**) | 発効した事前登録 v1 の規則の下、本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠の判定集合 30 枠に失格に当たる verify が無く、本走 24 枠が pass の条件を満たした (規則の機械適用の出力) | 研究の成功宣告 (D12)、serializable であることの証明・保証・信頼度、乱数列の独立性の検証、S-1 当時のソース・バイナリの再検証、S-1 (iv 付属) の充足、検証相 (案 B) との比較、性能、別 cohort での再現 |
| B-10 の `not-observed` / cohort 2 の同 verdict | 事前登録の述語で表現可能域まで飽和を観測しなかった (各 cohort について) | 飽和しない、2 cohort で有意、再現精度 |
| MoCC の G2 観測 (witness on / off) | 非 certifying の観測記録 | 根因、観測者効果の実証、不在 (0 件)、同等性 (非有意) |
| K2 3 巡目の certified 1 評価 | 診断が届き 1 評価が certified だった | 診断が効いた、改善、候補間の certified 選択 |
| K2 同 job pair の初投入 (`13339.nqsv`、D2187、**2026-09-21 版で追加**) | 候補 10 の再評価 1 件が certified だった | pair の成立、同 job の stock 対照、stock の失格・非 STOCK 判定、改善・退行・再現性 |
| K2 pair mode の結合検査の緑 (D2205) | 1 process・1 回の認可と claim の所有期間で候補 → stock を評価する経路が、結合検査で通る (build・trace・bench・checkout・condition gate などは stub) | 実機での pair の成立 (それは entry 1823 の実走が示す) |
| K2 同 job pair の再投入と 4 巡目 (entry 1823、**2026-09-26 版で追加**) | 同じ job で候補と stock がともに certified、stock の `src_token` は stock。同 job の比は配線 1 点の記述値 | 改善、候補間の優劣 (4 巡目と pair の候補は別 job)、診断の効果、B-6 の充足 |
| 関数単位の軸の段階 D の二値 true (D2234、**同**) | 固定 16 点が同 job の退化点 abort0 に 3% 超を示し別 job で再現した | 既知最良を超える地形の有無、全 IR の地形 |
| 小比較の最良参照比 (D2240、**同**) | 同 job の参照 3 本 (静的 10 µs が全 8 job で最良) に対し、16 点中 3 点が 6〜7% 上回った (探索的・1 回・再測なし・多重選択の補正なし) | 統計的な優位、B-1 の成立、別 workload・全 IR・LLM×C++ への一般化、10 µs 以外の静的値との比較 |
| pipeline での TPC-C 段 1 の判定 (D2238、**同**) | Silo の実 trace 1 本が executor で直列化可能と判定され、違反注入・末尾欠落の写しは拒否された | TPC-C の合成候補の認定・評価、TPC-C の性能、段 2、本文の定義での certified |
| 検出期待表の「盲点として certified」・「停止」(D2239・D2246、**同**) | 変異が挙動を変えその取引が commit した履歴を判定器が受理した / run が timeout した | 判定器の欠陥、deadlock、検出力の網羅的な証明 |
| B-5 の「判定不能 (欠測)」(entry 1866、**同**) | report の規則で 6 比較すべてに欠測があり判定できない | LLM と random / sweep の優劣・同等性、性能の結果 |
| MoCC の 5 slot certified (D2248、**同**) | 差し込んだ経路が計算ノードで疎通した | MoCC での比較・既知最良との比較 |

## 実走・契約・未了の境界

本稿の静的照合は、新しい測定を実施したという記録ではない。`docs/phase3.md`「後続段」の実績を、現在の
pin による新試行の完了や一般的な性能優越へ移さない。8c の bounded MVP も、段 4 の責任分担を遡って
無人化しない。

`docs/phase3-main-experiment.md` の検証相、非 LLM 対照、系列単位の標本設計、floor、多重比較は評価契約
として読む。D52 の S、縮小後の S' と workload 特化の前向き評価を混ぜず、旧 headline が不成立となったことを、
方法節で成功へ言い換えない。

**B-8 と B-5 は別の登録・別の段階にある (2026-09-26 版で更新、main `6d198ca8a` で照合)。** B-8
(`docs/b8-final-candidate-longrun-verify-preregistration.md`、D2175) の事前登録 v1 は 2026-09-21 に発効し
(D2194 項 1、発効 commit `624c84986`)、repo 外の runner v5 (D2190) で校正・本走・3 値判定まで済んだ (結果稿 §3、
発効記録 §3〜§5、entry 1791。手順は D2202。上の表の B-8 行)。B-5 (`docs/b5-generator-contrast-preregistration.md`、D2158) は、
上限付き試走の完走 (entry 1779) と段階認可 (D2200 項 1) の後、発効束の draft (D2222) を経て第 32 回の裁定で本走が認可された
(D2227 項 2)。本走 wave は block 1 stage 1 の 12 job を 2026-09-23 に投入した後に止まり、現行 cohort は 6 比較すべて判定不能 (欠測) で、
続行形 (v1 を閉じて v2 で登録し直す前提の 4 択) はユーザー裁定待ちである (entry 1866、F1050)。**B-5 の発効 commit は main の祖先でない
branch にあり、本走 wave の記録は main に着地していない。** 着地しているのは entry 1866 と D2243 の索引外の記述である。

**関数単位の軸・TPC-C・比較基盤・事前登録の境界 (2026-09-26 版で追加)。** 段階 E は D2243 項 1 で裁定されたが実装は採用時点で無い。
TPC-C は段 1 の判定器と pipeline の受理まで (上の表)、campaign の評価・性能・段 2 は無い。比較基盤は S1 の実装と MoCC の疎通まで、
試走は発効後に block 1 で中断し、転移は実行器まで (測定は未発効)。試走の費用削減案のうち検証の同時化を採る判断は、ユーザーの委任を
受けた親裁定として repo 外の job 領域にだけ記録され、正典 (entry 1863 の次の一手) では「ユーザーの確認」を要する択のままである。

B-4 は D1936 項 8・9 と D2016 により記述統計限定で、適格な赤 precursor は 0 件 ([T-2632]) のまま
`design_not_feasible` である。実装の限界は前稿のまま残る — 記録の writer は create-only
(`orchestrator/campaign/p3_b4_raw_record_producer.py` の `O_EXCL` 作成)、材料 report の §7.1 の 4 分類は未実効
(`p3_b4_material_report.py` の `section_7_1_four_classifications_operationalized: False`)、launcher は単一
`--arm` まで (`p3_b4_launcher.py`)。記述統計への限定は機械の受理集合を変更せず (D2016)、正式な certified 選択への
接続も未完である (D1408)。床値 pair の w1 完走も K2 の stock 対照口の追加と修復も、この限界を解消しない。

**前稿 (2026-09-20 版) が記録した、story 2026-09-20 版に未反映の着地 (基準 `482f19b88` までに main へ入った実装・発効。
本稿は再照合せず前稿のまま継承する):** B-10 freeze-tree
pin の更新と凍結 v2 g1 chain の取り込み (entry 1716)、A-1 認可 record (entry 1736、D2178)、凍結 v2 g1 の
承認 A と active pointer X を AI が作り発効させたこと (entry 1742、D2180。同版 §2 (c) / §6 / §8 の「未発効」は
この時点で古い。official 経路の launch validation の既存不整合 2 件は未達のまま)、verifier の packed 配列
(entry 1744、D2181)、意味 witness の `#ifdef` / 非一意 directive 対応 (entry 1745、D2182)、K2 の stock 対照口
(entry 1746、D2183)、**CCBench pin の前進 `511c9538` → `e9e477ca`** ([T-2304]、main `482f19b88`。記録は
`output/insights/2026-09-20/t2304-pin-advance/README.md`。gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` を同一 commit で
更新し、build admission の policy epoch が移ったため現行 policy 束縛の golden が追随した。較正 record・凍結
protocol・比較 policy・歴史 golden は据え置き)。発効と pin 前進を除きいずれも実装であって新しい測定・判定では
なく、発効も oracle 実走の開始ではない。**pin 前進の帰結として、新 main では旧 policy で admission された
binary / lock を live に消費できず、`p3_s4_loop.py` の独立 full OID (`511c9538`) は新 main の submodule と不一致で
fail-closed、`resolve_current_floor_protocol()` も新 gitlink で fail-closed になる。稼働中・登録済みの系列 (K2 の巡、
A-1 sized、凍結 v2 g1 の launch、B-4 床値) は前進前の superproject と対応 submodule の固定 checkout から走り、
新 main からの再開・再投入は系列ごとの整合 (新登録・identity・ドライバの pin・後継 protocol・admission) が
要る (同 README §4)。** 前稿は、その照合時点で稼働中だった兄弟 wave (A-1 attempt-0002 の投入など) の結果を数えなかった。

**前稿 (2026-09-21 版) が採用時点 `36fb14a3d` で揃えた着地:** B-8 の発効と 3 値判定 `pass`、K2 の同 job pair の初投入の不成立 (D2187) と
pair mode への修復 (D2205)、B-5 の上限付き試走の完走と本走の段階認可。**本稿 (2026-09-26 版) が採用時点 `6d198ca8a` で揃えた着地:** 上の
「09-22 以後の機構」の表の全行、K2 の pair の成立 (entry 1823)、A-1 attempt-0002 の投入と完走 (entry 1755)、B-5 本走の認可・中断・判定不能
(D2227 項 2、entry 1866)、pin C (D2236)、B-4 の carrier (D2213)。表に載せない運用側の着地 (受入・land の道具ほか) は方法節の対象外で照合していない。

「拒否診断を返す実装がある」から「そのフィードバックによる改善効果を実証した」へ飛躍しない。同様に、
「認可 record の機構がある」から「A-1 の 2 本目が投入された」へ、「stock 対照口がある」「pair mode の結合検査が緑」
から「pair が成立した」「同 job の stock 対照が取れた」へ、「packed 配列で 10 s trace が完走した」「B-8 の本走が
extime 10 s で完走した」から「検証相を 10 s で取り直した」「判定器が改善した」へ、「B-8 が `pass`」から
「最終候補が serializable であることが示された」「S-1 の付属規則 (iv) が充足された」へ飛躍しない。**2026-09-26 版で足した分:**
「小比較で 3 点が静的 10 µs を上回った」から「関数単位の合成が既知最良を超えた」「B-1 が成立した」へ、「pipeline が TPC-C の trace を受理した」から
「TPC-C の候補を認定・評価した」へ、「MoCC の 5 slot が certified」から「MoCC で比較した」へ、「pin が C へ進んだ」から「探索が解禁された」
「比較 harness も C で走る」へ、「B-5 の 6 比較が判定不能」から「LLM が勝てなかった」へ、「17 図を描き直して値が一致」から「測り直して
再現した」へ、飛躍しない。

## 本文照合の確認点

**本稿で足した確認点 (2026-09-26 版):**

- 「09-22 以後の機構」の表の module・関数・patch・gitlink・`CURRENT_PIN` を採用時点 `6d198ca8a` の作業木で `ls` / `grep` / `git ls-files -s` で確かめた。
  CCBench 側の branch (repo 外) は D 本文と entry の記述に拠り、本稿では checkout していない。
- 本文の certified の定義 (YCSB の point read / write に限る) を広げず、TPC-C の trace の判定は「判定器が直列化可能と判定した」と書いた (F1049)。
- 認可・裁定 (D2227 項 2、D2243 項 1、D2235 項 7) と実施記録 (entry 1856・1866・1863) を分け、B-5 の発効 commit が main に無いことを書いた。
- gitlink の pin と driver の campaign pin を分けた (F1051)。
- 稼働中で採用時点に未着地の作業 (関数単位の軸の段階 E、試走の検証の同時化の実装、検出期待表の si の行ほか) は書かない。
- 前稿の継承部分の相対リンクのうち、同 dir の README を指していたものは前稿の README へ張り替えた (複製で新しい README へ解決するため)。

**前稿で足した確認点 (2026-09-21 版、継承):**

- B-8 の方法の各文を、事前登録本文の節 (§0・§3.2・§4.1・§4.2・§5・§6.1〜§6.4・§7・§12) と D2186 項 1・D2190・D2202 の
  項へ当てた。実施の日時・request・件数・判定は結果稿 §3 と発効記録 §3〜§5 から写した。
- 件数は「本走 24 枠 (独立 8 反復 × 3 workload・extime 10 s) + 校正の完走 6 枠 (3 workload × extime 6 s / 10 s、各 1 回)」
  の形で 1 文に並べ、判定集合 30 枠の全体を本走の条件へ帰属させない。
- 校正の未完走 (運用上の `indeterminate`、verdict を持たず再検証しない) と、判定器が完走して返す `indeterminate` verdict
  (失格側、D2190 項 3) を区別した。
- K2 は D2187 (修復前の 2 process 形の初投入の不成立) と D2205 (pair mode への修復、実機未投入) を別の段落・別の行にし、
  修復の緑を対照の成立と書かない。pair mode の実装アンカーは main `36fb14a3d` の `loop.py`・`p3_s4_loop.py`・job body で
  確かめた。D2205 以後に pair の再投入を認可した決定は decisions に無い。
- B-5 は D2172 項 4 (段階実装・試走の認可)、entry 1779 (試走の完走、主標本外)、D2200 項 1 (段階認可、本走の認可ではない)
  で書いた。D2200 以後に B-5 の本走を認可した決定は decisions に無い (D2206 は「発効束の完成は AI 手番で進行中」と記録)。
- 継承部分で「本稿の時点」と書いていた箇所 (methods §1 の非 Silo の性能比較、§5 の A-1 認可 record、本表の A-1 行、
  境界節の兄弟 wave の文) は、中身を再照合せず「前稿の照合時点 (`482f19b88`)」へ表記だけを直した。
- 段 6 の独立レビュー ([前稿 README](../../2026-09-21/paper-methods-ja/README.md) §4) の should-fix 4 件 (K2 pair の初投入は CCBench を driver の旧 PIN へ checkout して
  走ったこと、bench 失敗は校正・本走を問わず pass を妨げること、`pass` の出所を実施記録にすること、継承段落のリンク先) と
  nit 8 件を反映した。

**前稿 (2026-09-20 版) の確認点 (継承):**

親が生成→検疫→検証→測定→記録の呼出しを追い、前稿の確認点 (数値リテラル一つの backoff を任意コード合成と
読ませない、診断還流 off を検証 off と取り違えない、raw 観測・探索 certified・正式適格を分ける、COMMIT と
最終勝者を同一視しない) に加え、次を本文へ反映した。certified の定義を story §6 の 2 文に揃える。
certification の outer status の判定順を `collect_results` の分岐順どおりに書く。A-1 の分類 3 値と lane の
2 field を policy と `CLASSIFICATION_RULES` から写す。検証相の runner が repo 外であることを insight §4.3 で
確認する。verify fan-out の node 数を policy 3 本の `scheduler.nodes` (5) と取得済み attempt の実測 (1 node)
で書き分ける。段 6 の独立レビュー (read-only、[前稿 README](../../2026-09-20/paper-methods-ja/README.md) §5) の must-fix 4 件 (K2 stock 対照 =
内蔵の適応 backoff、admission record と元 record の区別、B-4 の実装限界 3 点の復記、pin 前進の承認状態) と
should-fix 3 件を反映し、その後に取り込んだ pin 前進 ([T-2304]) を pin に触れる行へ再照合した。本文と表の
「実装済み」は静的確認であり、本 wave の受入テストとは別の根拠である。
