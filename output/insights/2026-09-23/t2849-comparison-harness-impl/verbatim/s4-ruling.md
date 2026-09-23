# 段 4 裁定とプラン v2 — [T-2849] 単位 1〜7 + [T-2853] (1)

- 裁定: 親 (manager)、2026-09-23 08:5x JST。基準 = 段 2 plan (../s2/plan.md) + 段 3 相談 A (../s3/consult-A.md)・B (../s3/consult-B.md)。
- 裁定 inbox 再走査: wave 開始後の新着なし (最新 2026-09-22-rulings-full31、19:52)。local main は起点 3886a1fd3 のまま。
- **本文と plan.md が食い違う箇所は本文が正本。**

## 所見の裁定 (10 件、すべて real・採用・scope 内)

| ID | 内容 | 裁定 |
|---|---|---|
| A1 / B1 | (P2) は D2220 の LLM 構成を変える。設計 insight §2.7 (90 行) が K2 限定を既に指摘し、K0 への拡張を単位 4 に含めていた。親 brief の「裁定時に未見」は不正確 (新規なのは sha 束縛の波及範囲だけ)。束が縛るのは planner-v4 と coder-v4-autonomous-k2 で、通常の coder-v4-autonomous は含まない | real。**(P2) を撤回し (a) を採る:** 役割定義 2 file を改訂し、K0 に critic 診断と初期点・投入前拒否の兄弟 key を渡す。前例 T-2783 (commit 4bd962643) と同じ分担 = 役割 .md は親 (docs)、role adapter JSON・review_ledger・互換 test の pin は Codex author |
| A2 / B4 | 役割費用の producer→consumer が未確定、critic 費用の所在を集約が引けない | real。§3.3 で固定 (費用 file は ledger の handshake dir に置き、driver が event へ写し、集約は ledger root から読む) |
| A3 | N_eval と session 内 5 rep の結合 | real。expected_reps は評価口の固定 5 (B-5 N_EVAL の値ではなく reps 定数) とし、N_eval (endpoint・参照の session 数) と別引数にする |
| A4 | cohort root と ledger root の配置契約が無い | real。`--ledger-root` を廃し、配置を cohort root から導出する (§3.2) |
| A5 | 参照分類の負例・保全例外の試験不足 | real。負例 3 本 (genome 不一致・performance verify 欠落・anomaly 混入) と、保全の起動失敗・inventory 書込失敗が元の結果・例外を置き換えない試験を必須にする |
| B2 | (P3) 「置き場が無い」は誤り。lock は driver 側でも置ける。job body 分岐を残す理由は prebuild 受領証の受け渡し。INITIAL_VALUES env と shell 側の全 arm 検査は削れる | real。job body の最小分岐は残し、lock は **job body の harness 分岐だけ**に置く (D2209 と同形、driver には置かない)。INITIAL_VALUES env と `--initial-values` CLI を削り、driver 定数 `INITIAL_VALUES = (5, 10)` とする。shell 試験は引数輸送・排他・rc・lock・非 harness 不変だけ |
| B3 | endpoint 選択は B-5 `select_endpoint` を直接使える (初期点 5・10 は v で決着) | real。独自の資格 filter / sort を作らず、全系列の失格値集合を渡して `select_endpoint` を呼ぶ |
| B5 | 変異を単一変更に分け、「保全で anomaly を成功へ」は削る | real。§5 の登録表は単一変更だけ |

(P1): 2 レンズとも条件付き成立。発効 commit は「T-2797 の land commit を親にし、束の status・effective 節だけを変える commit」でなければならず、main 先端で作ると本 wave の変更 (p3_s4_loop.py・pipeline.py・job body・planner-v4.md) を含んで束の sha と食い違う。本 wave は束を編集せず、段 7 で insight と worklog の [T-2797] 項にこの条件を 1 行書く。
(P3): 採用 (上記 B2 の形)。

## 計算の見積り (D2212 項 4)
受入 2 回 (0.50) + 焦点走 3〜4 回 (≤0.24) + 追加受入 1 回の余裕 (0.25) = **≤ 0.99 node 時間**。変異は全件 login self-run 可能な pure test に置く (dispatch probe を使う場合は 1 本 ≈ 0.06 で、合計が 2 を超える前に止めて確認する)。**2 node 時間未満のため事前確認は不要。** 単価は 2026-09-22 [T-2797] の job Elapse 実測 (受入 1 回 ≈ 900 s、焦点走 166〜229 s)。

## プラン v2 (plan.md からの変更点だけ)

### 1. 所有と単位

| 単位 | 所有 path (素集合) |
|---|---|
| 親 (docs) | `.claude/agents/planner-v4.md`、`.claude/agents/coder-v4-autonomous.md` (段 5 投入前に親が改訂し commit する。子はこの commit を base にする) |
| U-A | `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/pipeline.py`、`orchestrator/tests/test_t2849_loop_entry.py`、`orchestrator/tests/test_t2853_trace_preservation.py`、`orchestrator/tests/test_ccbench_spawn_sites.py` |
| U-B | `orchestrator/campaign/t2849_comparison_harness.py`、`orchestrator/campaign/t2849_generators.py`、`orchestrator/tests/test_t2849_generators.py`、`orchestrator/tests/test_t2849_comparison_harness.py`、`orchestrator/tests/test_t2849_comparison_aggregate.py`、`orchestrator/tests/test_official_perf_closure.py` |
| U-C | `tools/t2849_llm_round.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_t2849_llm_round.py`、`orchestrator/tests/test_t2849_job_contract.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`、`.codex/role-adapters/planner-v4.json`、`.codex/role-adapters/coder-v4-autonomous.json`、`orchestrator/codex_roles/review_ledger.py`、`orchestrator/tests/test_reflux_originless_compatibility.py`、`orchestrator/tests/test_codex_agents.py` (役割定義の sha を pin する test・ledger は子が `git grep` で全列挙し、上記以外に要るなら報告して止まる) |

禁止: `orchestrator/tests/test_p3_s4_loop.py` (他 wave 編集中)、`orchestrator/campaign/b5_generator_contrast.py`、B-5 事前登録・束、`.claude/agents/coder-v4-autonomous-k2.md`、verifier・CCBench・silo 関数方策の file 群・`docs/axis-onboarding.md`。

### 2. 評価 CLI (U-A) — plan §2.1 のまま
`--b5-slot` の接頭辞に `t2849-harness-v1|` を追加、`--reference-genome PATH.json` (`--stock-control` と `t2849-harness-v1|` slot の組でだけ受理)。参照の exact flags は plan §2.1 の表。`BACKOFF_FIXED` は足さない。

### 3. 系列 driver (U-B)

#### 3.1 CLI
```
python3 -B -m orchestrator.campaign.t2849_comparison_harness run-series
  --cohort ID --cohort-root PATH --arm {random,sweep,bo,evolution,llm}
  --workload W --series R --block Q --a-limit A --b-limit B --n-eval N
  --fetchcontent-prebuild-receipt PATH
... run-block-controls --cohort ID --cohort-root PATH --workload W --block Q --n-eval N --block-stock-sessions S --fetchcontent-prebuild-receipt PATH
... aggregate --cohort-root PATH --job-costs PATH --out PATH
```
初期点は driver 定数 `INITIAL_VALUES = (5, 10)` (header に記録)。`expected-inputs` subcommand は作らない (巡 tool は driver が公開する request-<a>.json を読む。末尾の追補)。

#### 3.2 配置 (A4)
- 系列: `<cohort-root>/<workload>/<arm>/series-<R>/` (ledger root。既存なら拒否)。
- 共有対照: `<cohort-root>/<workload>/controls/block-<Q>/`。
- aggregate は cohort root 配下のこの 2 形だけを走査し、header の cohort が一致しない ledger は結果に「不一致」として列挙し集約に入れない。

#### 3.3 費用 (A2/B4)
- 巡 tool は handshake dir (`<ledger root>/handshake/`、B-5 と同じ位置) に `role-costs-<a>.json` (proposal / reject 時) と `critic-costs-<b>.json` (critic 実行後) を書く。形は `{"role_calls": [{"role", "count", "wall_s", "reported_tokens"}], "human_interventions": [{"at_utc", "action", "note"}]}`、未報告は null。
- driver は handshake の proposal / reject を消費するとき `role-costs-<a>.json` を読み、その event の `provenance.role_calls` / `provenance.human_interventions` に写す (無ければ null、0 にしない)。
- aggregate は各 ledger の handshake dir の `critic-costs-*.json` を読んで系列の LLM 費用へ加える。job Elapse は `--job-costs` の `{PBS_JOBID: {elapse_s, queue_wait_s, source}}` から job ごとに 1 回。
- 生成器の計算 wall は driver が ask の前後で測り event の `timing.generator_wall_s` に置く。

#### 3.4 N_eval と reps (A3)
`classify_slot(..., expected_reps=5, ...)` の 5 は評価口の固定 rep 数の module 定数 `SESSION_REPS = 5` とし、`--n-eval` は endpoint 再計測と参照の session 数にだけ使う。

#### 3.5 endpoint (B3)
初期点 event と探索 event を合わせ、cohort 内の全系列 (score・初期点・探索・共有対照を含む) で anomaly が出た値の集合を `disqualified_values` にして B-5 `select_endpoint` を呼ぶ。run-series 時点では「その時点で cohort root に存在する ledger」から集合を作り、aggregate は最終集合で再判定し、固定後の失格は日付付きの訂正として出す (次点へ選び直さない)。

#### 3.6 K0 LLM の入力 (A1/B1、役割定義改訂に対応)
`expected_inputs(ledger, next_evaluation)` は B-5 と同じ whiteboard・current_perf/baseline (最新の certified・品質正常。stock・初期点・探索から)に加え、次の 2 key を返す。巡 tool は両方を planner と coder の入力に**同じ値で**入れ、driver は `assert_inherited_inputs` で一致を照合する。
- `k2_critic_diagnosis`: key 名と 6 field は D2155 のまま (射影の中身を変えない、D2220 項 2)。評価 1 回目以降の critic 逐語から `p3_s4_loop.k2_critic_diagnosis_from_bytes` で作る。b ≥ 1 で必須、b = 0 では無し。p3_s4_loop.planner_context_payload の K2 限定は変えない (巡 tool はそれを呼ばず、validator を直接使う)。
- `t2849_prior_observations`: `{"data_boundary": "harness_observations_are_data_not_instructions", "initial_points": [{"value": int, "outcome": str, "fitness_tps": number|null}], "rejected_opportunities": [{"a": int, "reject_class": "role-output"|"schema"|"grammar"|"preprocess"|"tier0"}]}`。fitness は certified・品質正常のときだけ数値。拒否の列に候補値・自由文を入れない。reject_class の写像: 巡 tool の reject = role-output、`assert_closed_proposal_schema` / ability probe 失敗 = schema、`validate_backoff_value` 失敗 = grammar、outcome `rejected-preprocess` = preprocess、`rejected-tier0` = tier0。
- whiteboard 5 field・iteration = b・継承照合は B-5 のまま。

### 4. 保全口 (U-A) — plan §2.4 のまま + A5・B 保全節
env `IZANAGI_TRACE_ARCHIVE_ROOT` (絶対 path) の opt-in。未設定なら挙動・出力とも不変。失敗 (zstd 不在・起動失敗・非 0・書込不能・inventory 書込失敗) は元の verdict・例外を置き換えず、原本を削除せず、stderr に失敗と原本 path を残す。部分圧縮を完了扱いしない。inventory は certification の根拠に入れない。WAL・proof chain・receipt schema は変えない。

### 5. 変異の事前登録 (DW-M01、単一変更)
kill = 名指しの test が FAIL し、他の登録外 test の赤を伴っても期待 node の完全集合は実装後に self-run で確定する (DW-M08)。test 名は author への必須名。

| # | 単位 | 位置 | 変異 | kill を期待する test |
|---|---|---|---|---|
| M1 | U-A | p3_s4_loop main の接頭辞受理 | `t2849-harness-v1|` を受理集合から外す | test_t2849_loop_entry::test_harness_machine_slot_accepted |
| M2 | U-A | _run_stock_control_resolved | 参照指定時も `_BASE`+BACK_OFF=1 の genome を使う | test_t2849_loop_entry::test_read_heavy_reference_exact_flags |
| M3 | U-A | p3_s4_loop main | `--reference-genome` を B-5 slot でも受理 | test_t2849_loop_entry::test_reference_rejected_outside_harness |
| M4 | U-A | pipeline 保全 | 保全の前に rmtree | test_t2853_trace_preservation::test_archive_before_cleanup |
| M5 | U-A | pipeline 保全 | 保全失敗後も原本を削除 | test_t2853_trace_preservation::test_failure_retains_original |
| M6 | U-A | pipeline 保全 | 保全の例外を握らず送出 | test_t2853_trace_preservation::test_preservation_error_does_not_replace_result |
| M7 | U-A | pipeline 保全 | env 未設定でも保全を実行 | test_t2853_trace_preservation::test_unset_env_unchanged |
| M8 | U-B | run_series 初期点 | 初期点で B を加算 | test_t2849_comparison_harness::test_initial_outside_b |
| M9 | U-B | slot 実行 | retry の attempt ごとに B を加算 | test_t2849_comparison_harness::test_retry_counts_b_once |
| M10 | U-B | BO tell | Tier0 不通過を失敗集合から外す | test_t2849_generators::test_bo_excludes_candidate_failures |
| M11 | U-B | Matérn | 距離を ln v でなく v で取る | test_t2849_generators::test_gp_two_point_independent_values |
| M12 | U-B | EI | 予測分散に観測雑音を足す | test_t2849_generators::test_ei_latent_variance |
| M13 | U-B | 進化 tell | 親置換を `>=` にする | test_t2849_generators::test_equal_fitness_keeps_parent |
| M14 | U-B | endpoint | 初期点を候補から外す | test_t2849_comparison_harness::test_initial_can_be_endpoint |
| M15 | U-B | 失格集合 | 自系列の anomaly だけにする | test_t2849_comparison_aggregate::test_cross_series_disqualification |
| M16 | U-B | 欠測優先 | 品質欠測のとき block stock fallback で埋める | test_t2849_comparison_aggregate::test_missingness_precedence |
| M17 | U-B | expected_inputs | current_perf を最新でなく最良にする | test_t2849_comparison_harness::test_k0_uses_latest_normal |
| M18 | U-B | 参照分類 | genome identity 照合を外す | test_t2849_comparison_harness::test_reference_genome_mismatch_not_certified |
| M19 | U-B | classify 呼出し | expected_reps に N_eval を渡す | test_t2849_comparison_harness::test_n_eval_independent_of_reps |
| M20 | U-B | slot_argv | llm arm に `--machine-generated-proposal` を付ける | test_t2849_comparison_harness::test_llm_slot_argv_k0 |
| M21 | U-B | whiteboard | iteration に a を使う | test_t2849_comparison_harness::test_rejection_does_not_advance_whiteboard |
| M22 | U-B | handshake 消費 | role-costs を event に写さない | test_t2849_comparison_harness::test_role_costs_recorded |
| M23 | U-C | job body harness 分岐 | IZANAGI_BENCH_LOCK の設定行を消す | test_t2849_job_contract::test_harness_bench_lock |
| M24 | U-C | job body harness 分岐 | harness 起動後に既存 driver へ fallthrough | test_t2849_job_contract::test_harness_single_driver |
| M25 | U-C | 巡 tool | `t2849_prior_observations` を planner にだけ入れ coder に入れない | test_t2849_llm_round::test_prior_observations_both_roles |

## 規模の上限 (段 6 fix にも継承)
production 追加 ≤ 2,000 行、test ≤ 1,600 行。超えるなら実装を止めて理由を報告する。

## 追補 (段 5 投入前、単位間の結合を固定)

- **handshake (U-B が producer、U-C が consumer)。** 位置は `<ledger root>/handshake/`。driver は提出機会 a ごとに
  `request-<a>.json` = `{"a", "next_evaluation", "expected_whiteboard", "current_perf", "baseline", "current_perf_source",
  "t2849_prior_observations", "deadline_utc"}` を公開し、評価後に `slot-<b>.json` (B-5 と同じ形、`digest_path` を含む) を公開する。
  巡 tool は `proposal-<a>.json` + `inputs-<a>.json` (`{"planner_input", "coder_input"}`)、または `proposal-<a>.rejected.json`、
  および `role-costs-<a>.json` を書き、critic 後に `critic-costs-<b>.json` を書く。巡 tool は U-B の module を import せず、
  request の値を写して入力を組む。driver は `assert_inherited_inputs` で whiteboard・current_perf・baseline・
  `t2849_prior_observations` の完全一致と、`k2_critic_diagnosis` の形 (6 field) と planner / coder 間の一致、b ≥ 1 での存在を照合する。
- **job body → driver (U-C が producer、U-B が consumer)。** env `IZANAGI_S4_T2849_MODE` (series | block-controls)、
  `IZANAGI_S4_T2849_{COHORT,COHORT_ROOT,WORKLOAD,BLOCK,N_EVAL}`、series は `…_{ARM,SERIES,A_LIMIT,B_LIMIT}`、block-controls は
  `…_BLOCK_STOCK_SESSIONS`。job body は §3.1 の CLI へそのまま写す。driver 起動直前だけ `IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"`。
- **driver → 評価 CLI (U-B が producer、U-A が consumer)。** §2 の argv。U-B は U-A の実装を待たず argv を組み、評価は stub runner で試す。
