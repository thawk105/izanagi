# 日本語方法節の実装対応メモ (2026-09-20 版)

対象本文は [方法節草稿](methods.md)。照合対象は local main `482f19b88` (2026-09-20) のコードと指定文書で
ある (起草時の基準は `fec4a8187`。その後に着地した [T-2304] の CCBench pin 前進 `511c9538` → `e9e477ca` を
取り込み、pin に触れる記述を再照合した)。本資料のための新規 CC 合成・性能測定は行っていない。以下の「実装済み」は記載した関数・経路が現行
main に存在し、その挙動が本文の記述に対応することを指し、その機能を使った正式実験の完走を含まない。
「使用」は、その機構を実際に使った attempt・走行を worklog entry または insight で名指しできることを指す。
本資料は新しい論文シリーズ、実験登録、判定器ではない。前稿 (2026-09-10 版、entry 1430) は置き換えず、
本稿は別稿である。

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
  (2026-09-20 07:04 JST) から導出されており、本稿の基準 `482f19b88` との差 (下の「story 未反映の着地」) は
  本稿が明記する。
- `docs/paper-story/README.md` の stale 注記 (2026-09-20 時点 3 件): B-7 材料稿の図 10 の着地、
  **B-7 の限定付き充足 (D2174 項 3)**、K2 3 巡の図 12 の着地。方法節は数値・図を転載しないので直接の影響は
  ないが、B-7 の状態語は同版 §8 (「要件充足へは昇格させない」) でなく D2174 項 3 で書く。同注記に無い着地
  (凍結 v2 g1 の発効 D2180、pin 前進 [T-2304]) は本稿末尾の「story 未反映の着地」で扱う。
- D2150 項 1 と `output/insights/2026-09-20/t2304-pin-advance/README.md`: pin 前進は承認済みかつ実施済み
  (main `482f19b88`)。前進が動かす identity の層と動かさない層、旧系列が固定 checkout から走ることを同 README
  §1・§4 から引く。前進は探索・軸採用の解禁を含まない (D2134 項 9、D2159 項 8・9)。
- `docs/phase3.md`「kickoff の最小スコープ」「現行 Phase 3 must と発火条件」「後続段」: 有効な編集契約と
  段ごとの実装・実走の射程を引く。冒頭の古い日付の要約だけで現在の全状態を決めない。
- `docs/phase3-main-experiment.md`: `output/s1-freeze/known_axes_freeze.json` の source sha256 として
  凍結されており、確定値の追記は `FreezeError` になる (entry 1702)。検証相の確定値は D2160・insight・
  results 稿に日付付きで置かれ、同文書への追記は未履行の繰延べである。

## 主要記述とコードの対応 (前稿から継承し現行 main で再照合した行)

コードの参照はリポジトリ相対パスと関数名で示す。本文番号は methods.md の節番号である。前稿の行のうち
現行 main で変わった点は「区分と上限」に書く。

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

| 本文 | 機構 | 実装アンカー (main `482f19b88`) | 使用した走行 | 実装済みだが未使用・上限 |
|---|---|---|---|---|
| §5 | A-1 sized の非認証 lane と 1 attempt 認可の投入経路 | `orchestrator/campaign/paper_story_a1_paired.py` `run_submit`、`_v3_barrier_before_bench`、`_run_complete_v3`、`positional_statistics`、`_classify_difference`、`CLASSIFICATION_RULES`；policy `paper_story_a1_paired.v3-sized.json` (`formal=false`、`promotion_prohibited=true`、`result_authority=sized-preregistered-descriptive-only`)；job body `tools/pegasus/paper_story_a1_paired.sh` | attempt-0001 (2026-09-18、entry 1636、job `4939`〜`4941`)：3 workload とも完走、分類は `resolved-above-floor`、6 arm の verifier anomaly 0 (`legacy` 条件)。descriptive 出力であり「A-1 の値」ではない | pilot 系 (`v3-pilot.json`) と sized 系は別 policy。分類語は事前登録 README (`resolved-beyond-floor` 等) と実装 (`resolved-above-floor` / `bounded-below-floor`) で表記が違い述語は同値 (entry 1636 の観察) |
| §5 | A-1 の再投入 gate と認可 record | 同 `_assert_no_prior_v3_bench_start`、`V3_SIZED_RERUN_AUTHORIZATIONS` (定数 1 件)、`_exact_v3_rerun_authorization`、`run_authorize_rerun` (subcommand `authorize-rerun`、schema `paper-story-a1-paired-rerun-authorization/v1`)、`_exact_materialization_destination` (公開先は兄弟 dir) | gate の拒否は attempt-0002 の実投入で確定 (2026-09-19、entry 1687、D2156、qsub 前 rc 2、副作用なし)。認可 record 機構は 2026-09-20 に着地 (entry 1736、D2178) | **record を使った投入は本稿の時点で 0 件** (投入は別 wave の手番)。record は署名でなく、「性能値を見た後の選択」を防ぐ装置でもない (D2178) |
| §5 | A-2 / A-6 certification の受領証束縛 | `orchestrator/campaign/paper_story_a2_certification.py` `preregister_attempt`、`record_submission_receipt`、`record_completion_receipt`、`record_acquisition_receipt`、`finalize_raw_manifest`、`_cell_source_binding_status`、`_require_cell_src_token_role`、`_parse_condition_gate_admissions`、`collect_results` (outer status)、`materialize`；policy `paper_story_a2_certification.v2.json`、`paper_story_a6_certification.v2.json`；性能条件側の検証 fan-out `_validate_verify_fanout_hosts` → `orchestrator/campaign/verify_fanout_worker.py` | A-2 attempt `t2364-20260907b` (2026-09-07、`observed-positive`、4 cell certified、`source_binding_status=bound`)、A-6 attempt `a6-20260908b` (2026-09-08、`reject`、2 cell certified)。いずれも 1 node で走った | policy の `scheduler.nodes` は 5 へ実装済み (entry 1686) だが A-2 / A-6 の新 attempt は無い (別途 nodes=5 の probe `t2489-20260918a` が fan-out を実走したが、outer status を作らず A-2 の attempt に数えない)。成果物の `compile_out_evidence_scope` / `independent_observation_limits` は自己申告。条件関門については admission record (`admitted` / `use_class` / `unestablished_meaning_macros` / `record_ids`) が残り、参照先の supply-effectuation / runtime-meaning record の本体は残らない。correctness 側の実 argv は独立に記録されない (`workload_argv_observation`) |
| §5 | certification 経路の descriptive 利用 (同一候補 fixed 5 µs の 3 workload 同時期測定) | 同 module の closed set に足した study `paper-story-b7-fixed5-regression` (`paper_story_b7_fixed5_regression.v2.json`、nodes 5)、submitter `tools/pegasus/submit_paper_story_a2_certification.sh` | attempt `b7f5-20260919a` (2026-09-19、entry 1705、request `10807`〜`10809`、6 cell certified、outer `reject`)。稿の床値判定 (read-heavy だけ退行) はコード外 | B-7 は D2174 項 3 で「単一 attempt・descriptive・非認証・反復間安定性は未判定」の限定付き充足。反復 attempt は認可されていない |
| §6 | B-10 待ち方 grid の事前登録と driver | `docs/b10-backoff-shape-preregistration.md`、`orchestrator/campaign/b10_backoff_shape_sweep.py` `holm_adjust`、`cell_effects`、`_shape_differences`、`_write_reports`、`ReportAnalyzerIdentity`；job body `tools/pegasus/b10_backoff_shape_campaign.sh`、`submit_b10_backoff_shape.sh` | report phase `978195.nqsv` (実行 2026-09-05、記録と D1678「現行 report で閉じる」の裁定は 2026-09-07)。単独 results 稿は entry 1737 | `official_certification` は `false`。判定が及ぶのは登録した 1 つの対比だけ |
| §6 | B-10 静的右 tail の事前登録と driver | `docs/b10-backoff-static-tail-preregistration.md` (2026-09-19 末尾追記 = 第 2 cohort の地位)、`docs/b10-backoff-static-tail-submission.md`、`orchestrator/campaign/b10_backoff_static_tail_formal.py` `analyze_interval`、`analyze_cohort`、`materialize_report`；投入 `tools/pegasus/submit_b10_backoff_grid.sh` | cohort 1 (2026-09-15、`not-observed`)、cohort 2 (2026-09-19、entry 1690、同 verdict、D2157)。正しさは `legacy` 条件の別走行で各 120 記録 | 2 cohort の統合 verdict・プール推定は無い。帯 901〜998 µs は未測 (D2027)。性能は未認証 |
| §3 | 採用候補 2 genome の検証相 | **リポジトリ内に runner は無い。** 判定器 `python3 -m orchestrator.verifier` (`orchestrator/verifier/cli.py` → `core.verify_trace_dir`)、identity は `source_digest.resolve_evidence`、extime 選択は `orchestrator/campaign/s1_verify_extime_calibration.py` `choose_extime` を runner が流用 | 校正 6 job + 本走 12 job (2026-09-19〜20、entry 1702、D2160)。判定集合 30 verify / 候補 (本走 24 + 校正完走 6) で anomaly 0、校正 10 s の未完走 2 件 / 候補は `indeterminate` として開示 | runner (Codex author 作、v1 1301 行 / v2 1384 行) は job dir に保全され repo に入っていない (insight `verify-phase-adopted-backoff/README.md` §4.3)。S-1 事前登録本文への確定値追記は凍結束縛で未履行 |
| §3 | verifier の容量 (packed 配列) | `orchestrator/verifier/dsg.py` `_PackedVersions`、`_PackedProducer`、`DSG._build_compact_packed`、`_edge_worker`；`core.py` `verify_trace_dir` | 計算ノードの compare (2026-09-20、entry 1744、D2181): 10 s trace 2 件が完走し、旧版と `result_to_dict` が byte 同一 | 検証相 (entry 1702) はこの変更**前**の verifier で走った。story 2026-09-20 版には未反映 |
| §2 | K2 型付き critic 診断 | `p3_s4_loop.py` `k2_critic_diagnosis_from_bytes`、`_validate_k2_critic_diagnosis`、`planner_context_payload(k2_critic_diagnosis=...)` (K2・非 B-4・reflux on を要求)、`k2_next_generation_inputs` (両 role へ同一診断を組み込む) | 3 巡目 (2026-09-19、entry 1691、job `10761.nqsv`)：critic-2 逐語から 6 field を組み立て planner-4 / coder-4 へ届け、1 評価が certified | 実 consumer は登録 Claude role への親の inline 送付 (D2155)。「届いた」と「効いた」は別。3 巡とも legacy critic で B-4 ablation には非適格 |
| §2 | K2 同 job stock 対照口 | `p3_s4_loop.py` `_run_stock_control_resolved`、CLI `--stock-control` (`--isolate-worktree` 必須、他 mode と排他)、stock 経路限定の `capability_resolver`；job body `tools/pegasus/p3_s4_loop_pegasus.sh` の stock step | **0 件** (entry 1746、D2183: 結線のみ) | 成功条件 = certified かつ `src_token == STOCK`。pair の成立は両 attempt の WAL outcome で判定。story 2026-09-20 版には未反映 |
| §3 | MoCC の trace-hook (X / P 計装) | `patches/instr-mocc-lock-coverage.patch` (計装 template 版 `instr-mocc-lock-coverage-temperature.patch`)、`orchestrator/campaign/s3_mocc_lock_coverage.py`、`mocc_trace_pair.py` (pair receipt `mocc-trace-pair-receipt/v2`)、`mocc_g2_discriminator.py`、`mocc_g2_repro_ledger.py`；job body `tools/pegasus/mocc_trace_pilot.sh` | pilot 対 (2026-08-26、`accepted`)、G2 観測 (i)〜(iii) (2026-09-18〜19、[T-2774] / [T-2779] / [T-2780])、機械実証 wave 1 (entry 1666、D2147) / wave 2 (entry 1701、D2159) の stock 走 | X / P 計装は CCBench pin の tree に無く patch で当てる (旧 pin `511c9538` について D2083、前進後の `e9e477ca` でも patch のまま)。G2 の witness (`IZANAGI_MOCC_G2_WITNESS`、`#if TRACE` 内) は `e9e477ca` に含まれる。全 leg `official_certification=false`。G2 の根因は未同定 |
| §3 | MoCC の軽量 witness | hook commit W `5b02546f` (submodule branch `izanagi-t1943-mocc-g2-witlight`、上流未公開)。**izanagi 側の module ではなく CCBench 側の変更** | 4 arm × 60 走 (2026-09-19〜20、entry 1696)：on 0/60・0/60、off 1/60・1/60、discriminator 未発火 | main の pin に含まれない。非 certifying。観測者効果の除去は言えない |
| §1 | MoCC 温度述語 template と機械実証 | `patches/mocc-temperature-predicate-variant.patch`、`orchestrator/campaign/axis_mocc_temperature.py` (`PROOF_PIN = e9e477ca`、探索用 `PIN = pin.CURRENT_PIN` の参照式は不変で、指す commit は前進に追随)、`s3_mocc_template_proof.py` `compute_checks`、`quarantine_controls`、`instrumentation_preservation`；`s3_mocc_mutation_proof.py` | wave 2 `11161.nqsv` (2026-09-20、entry 1701、30 check all_pass)、wave 1 `5096.nqsv` (entry 1666) | 探索・正式な軸採用は未解禁 (D2134 項 9、wave 2 の緑は認可を与えない)。pin 前進は D2150 項 1 で承認済みで、2026-09-20 に [T-2304] が実施した (main `482f19b88` の gitlink・`CCBENCH_FULL_SHA`・`CURRENT_PIN` = `e9e477ca`。探索用 `PIN = pin.CURRENT_PIN` はこれに追随し、`PROOF_PIN` と同じ commit を指す)。前進は探索の解禁を含まない |
| §4 | 床値 pair protocol v3 (B-4 の `floor`) | `orchestrator/campaign/floor_pair_driver.py` (`SPEC_SCHEMA = floor-pair-spec/v3`、`run_window`、`finalize_floor`、`GainDifference`)、凍結 spec 3 本 `output/env/pegasus/floor-pair/t2288-f1/`；job body `tools/pegasus/floor_pair_campaign.sh`、submitter `submit_floor_pair.sh` | w1 3 job `10711`〜`10713.nqsv` (2026-09-19〜20、entry 1693)：3 窓とも `complete`、各 62 標本 | w2・finalize・集約・採用・事前登録 §5 記入は無い。driver は自ら「spec が結果前に凍結されたことを証明しない (freeze receipt は無い)」と宣言する |
| §4 | 条件関門の意味 witness の拡張 | `orchestrator/campaign/condition_meaning_gate.py` `evaluate_define_supply_effectuation`、`evaluate_define_runtime_meaning`、`declare_define_runtime_meaning`、`MeaningWitnessDeclaration` | 関門族自体は A-2 / A-6 / 同一候補 3 workload 測定 / A-1 attempt-0001 の各走行が通過 (検証相は identity 束縛だけで関門を通していない)。`#ifdef` 形と非一意 directive の観測 (D2182、entry 1745) は 2026-09-20 着地 | story 2026-09-20 版には未反映。関門は「供給されたか」「同じ意味を持つか」を独立に見るが、実行到達性までは閉じない (D955) |

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
| B-10 の `not-observed` / cohort 2 の同 verdict | 事前登録の述語で表現可能域まで飽和を観測しなかった (各 cohort について) | 飽和しない、2 cohort で有意、再現精度 |
| MoCC の G2 観測 (witness on / off) | 非 certifying の観測記録 | 根因、観測者効果の実証、不在 (0 件)、同等性 (非有意) |
| K2 3 巡目の certified 1 評価 | 診断が届き 1 評価が certified だった | 診断が効いた、改善、候補間の certified 選択 |

## 実走・契約・未了の境界

本稿の静的照合は、新しい測定を実施したという記録ではない。`docs/phase3.md`「後続段」の実績を、現在の
pin による新試行の完了や一般的な性能優越へ移さない。8c の bounded MVP も、段 4 の責任分担を遡って
無人化しない。

`docs/phase3-main-experiment.md` の検証相、非 LLM 対照、系列単位の標本設計、floor、多重比較は評価契約
として読む。D52 の S、縮小後の S' と workload 特化の前向き評価を混ぜず、旧 headline が不成立となったことを、
方法節で成功へ言い換えない。B-5 (`docs/b5-generator-contrast-preregistration.md`、D2158) と B-8
(`docs/b8-final-candidate-longrun-verify-preregistration.md`、D2175) の事前登録 v1 は未発効で、対応する
runner・生成器は実装されていない。

B-4 は D1936 項 8・9 と D2016 により記述統計限定で、適格な赤 precursor は 0 件 ([T-2632]) のまま
`design_not_feasible` である。実装の限界は前稿のまま残る — 記録の writer は create-only
(`orchestrator/campaign/p3_b4_raw_record_producer.py` の `O_EXCL` 作成)、材料 report の §7.1 の 4 分類は未実効
(`p3_b4_material_report.py` の `section_7_1_four_classifications_operationalized: False`)、launcher は単一
`--arm` まで (`p3_b4_launcher.py`)。記述統計への限定は機械の受理集合を変更せず (D2016)、正式な certified 選択への
接続も未完である (D1408)。床値 pair の w1 完走も K2 の stock 対照口の追加も、この限界を解消しない。

**story 2026-09-20 版に未反映の着地 (基準 `482f19b88` までに main へ入った実装・発効):** B-10 freeze-tree
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
要る (同 README §4)。** 本稿は稼働中の兄弟 wave (A-1 attempt-0002 の投入など) の結果を数えない。

「拒否診断を返す実装がある」から「そのフィードバックによる改善効果を実証した」へ飛躍しない。同様に、
「認可 record の機構がある」から「A-1 の 2 本目が投入された」へ、「stock 対照口がある」から「pair が
成立した」へ、「packed 配列で 10 s trace が完走した」から「検証相を 10 s で取り直した」へ飛躍しない。

## 本文照合の確認点

親が生成→検疫→検証→測定→記録の呼出しを追い、前稿の確認点 (数値リテラル一つの backoff を任意コード合成と
読ませない、診断還流 off を検証 off と取り違えない、raw 観測・探索 certified・正式適格を分ける、COMMIT と
最終勝者を同一視しない) に加え、次を本文へ反映した。certified の定義を story §6 の 2 文に揃える。
certification の outer status の判定順を `collect_results` の分岐順どおりに書く。A-1 の分類 3 値と lane の
2 field を policy と `CLASSIFICATION_RULES` から写す。検証相の runner が repo 外であることを insight §4.3 で
確認する。verify fan-out の node 数を policy 3 本の `scheduler.nodes` (5) と取得済み attempt の実測 (1 node)
で書き分ける。段 6 の独立レビュー (read-only、[README](README.md) §5) の must-fix 4 件 (K2 stock 対照 =
内蔵の適応 backoff、admission record と元 record の区別、B-4 の実装限界 3 点の復記、pin 前進の承認状態) と
should-fix 3 件を反映し、その後に取り込んだ pin 前進 ([T-2304]) を pin に触れる行へ再照合した。本文と表の
「実装済み」は静的確認であり、本 wave の受入テストとは別の根拠である。
