# [T-2795] K2 手動 loop の同 job pair launcher と B-5 §10 の K2 共有部品 (較正動作点 CLI、exact correctness opt-in) を実装した

`authority: none` / `default_effect: no-state-change`

**種別:** 実装 (driver `p3_s4_loop.py`・job body `p3_s4_loop_pegasus.sh`・test 5 file、Codex author + fix 2 巡) と記録 (job body README の節、本 insight)。
**新規測定はゼロ** (実 compiler での stock の STOCK 成立・pair 測定は land 後の別 wave)。

- 日付: 2026-09-20 (JST)
- wave: `dev-wave-t2795-pair-launcher`、branch `worktree-dev-wave-t2795-pair-launcher`
- 起点 local main: `371674ea685ecb11e08dbcc31d4bf4f2bed0b20b`
- 依頼: `verbatim/T-2795-origin.md` (ユーザー、dev-wave 引数の逐語)。裁定 = D2172 項 3 (i) (同 job pair launcher を Codex author の別 wave で実装) と
  項 4 (α) (§10 部品を K2 共有部品から段階実装、本走は未認可)。内容 (1) 同 job pair → (2) 較正動作点 CLI → (3) exact correctness 経路の順。
  pair 投入 (候補 10 + stock)・4 巡目 (iv)・B-5 試走 (β) は land 後の別 wave。「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化は scope 外」。

## 0. この wave が主張すること・しないこと

**主張する。**

1. **driver に stock 対照の独立口 `--stock-control` が付き、同 campaign (同 identity・同 WAL) で適応 backoff stock (silo、`BACK_OFF=1`、
   `BACKOFF_FIXED=-1`) を 1 本、planner / coder / 検疫 / whiteboard / checkpoint に触れずに `run_campaign` → `pipeline.evaluate` へ通す。** §1・§2。
2. **job body は `IZANAGI_S4_STOCK_CONTROL=1` で候補 (proposal / fixture) の後に同 allocation・同 prebuild receipt・同 K2 manifest / 宣言値で stock を
   1 回起動し、候補 rc を捕捉して候補非零優先で集約する。既定 (env 不在 / `0`) は現行と同じ 1 起動で argv は bytes 不変。** §2。
3. **stock の成功 (`outcome=certified-stock`、rc 0) は certified かつ source が STOCK (variant id = `variant_id(genome)` かつ BUILD_START の
   `src_token == STOCK`) のときだけ。非 STOCK の certified は `non-stock-source`、terminal 既存は `skipped` (復元しない)、いずれも rc 1。**
   stock 用 condition gate は A-1 paired と同型 (`stock_comparison=True`、`STOCK_ADAPTIVE_BRANCH`、別の pinned-clean stock root)。§2。
4. **較正動作点 CLI (`--calibrated-perf --perf-workload {write-heavy,balanced,read-heavy}`) が p2_2 の較正定数 (1M / 48 / 3 s / 5 reps) と
   3 workload + `ycsb_max_ope="10"` から PerfConfig を組み、opt-in 時だけ search_config に `records / threads / perf_workload / extime / reps` を焼く。
   `--verify-performance` (較正必須) は `search_config["verify"] = legacy+performance` を焼き、既存の `loop._closed_verify_workloads` →
   `performance_correctness_workload(perf)` → `evaluate(extra_correctness=)` に接続する。指定なしの identity は変更前の preimage bytes と一致。** §2。
5. **規律 2 は保存: legacy 既定 pass は残り、anomaly (初回 / 最終 repetition) で bench に進まず COMMIT しない (TV の実 verifier test)。
   pipeline.py / loop.py / ident.py / build_admission.py は変更なし。** §2・§4。
6. **変異 matrix (等価対照 1 + 負例 17) と受入全走の結果は §5・§6。**

**主張しない。**

- **pair が成立した (同 job で候補と stock の両方が測れた) とは言わない。** 本 wave は結線だけで、1 job も投入していない。pair 成立は両 attempt の
  WAL outcome で判定し、driver rc・campaign id・stdout の `p3 S4 pair:` 行から判定しない (候補 CLI は提案 reject でも rc 0 を返す)。
- **実 compiler で stock の source が STOCK token に解決すること (inert) は未測定。** b10 / A-1 paired に実装と検査の先例があるが、S4 の
  template・compiler・gate での成立ログは無い。成立しなければ pair wave はその走を対照成立と認定しない (裁定 Q4)。
- **stock の admission class は `machine-generated` (generator `backoff-sweep`) であり `stock-baseline` ではない。** `derive_build_admission` の
  stock-baseline 分岐が `source.ccbench_commit == CURRENT_PIN` (短縮 `511c953`) の exact 比較で、S4 の full `PIN` では入らないため、既存 driver
  (backoff_extended_sweep 等) と同じ `capability_resolver` で generator receipt を発行して admission した。source の STOCK 性は
  `src_token` で保証され、class 名は admission の経路を表す。pin 比較の正規化は admission gate (規律 2 の防壁側) の変更なので本 wave では行わず、
  §7 の裁定パッケージ候補に置く。
- **B-5 §5.4 の系列開始 stock (初回 planner 前の stock → `current_perf`)、block stock、§5.3 の session 品質契約 (品質欠測の分類)、§5.5 の
  残余引数・seed・verifier 版の発効束は作っていない。** 候補後の stock は D2172 項 3 の K2 同 job 対照の結線であり、§5.4 の順序は逆。
- **較正・verify の driver opt-in は job body に配線していない** (B-5 試走 (β) wave の launcher 設計で足す)。B-5 本走は未認可のまま。
- **exact correctness の「記録」は campaign.lock の identity preimage (search_config) からの決定論的な復元であり、実 argv・binary・toolchain の
  独立 receipt ではない。** §5.5 全体が成立したとは言わない。
- `--v` 略記は `--verify-performance` 追加で曖昧になる (`--va` / `--val` は従来どおり)。使用箇所は無い。既定 argv・identity の不変とは別の狭い互換差。
- 3 巡目の記録 (候補のみ、identity `409e13f8…`) は保持し、pair の結果は別の実行証拠として追記する (D2172 項 3)。identity の維持は約束しない。

## 1. 置いたもの

| file | 内容 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py` (Codex author + fix1、commit `c6eb77597`) | `--stock-control` と排他 (run-iteration / 明示 value / emit-planner-context / no-build / coder-role / b4-reflux-ablation / allow-coder-derived-build と排他、isolate-worktree 必須)、`_run_stock_control_resolved` (genome → `layout.ensure` → `ensure_resumable_attempts` → applied TEMPLATE_PATCH → stock 形 condition gate → `run_campaign(..., capability_resolver=)` → 成功条件 → digest 再生成)、`_require_condition_gate(..., stock_root=)` の stock 形、`_stock_capability_resolver` (STOCK evidence だけ `attest_generator_output`)、`_refresh_critic_digest` (fixture 経路の既存処理を抽出)、`calibrated_perf(name)`、`--calibrated-perf` / `--perf-workload` / `--verify-performance` と identity の焼き込み、`perf = default_perf()` の差し替え。`default_cfg` / `default_perf` / `_assert_coder_value_domain` / `_resolve_duplicate` は bytes 不変。+250/−13 行 |
| `tools/pegasus/p3_s4_loop_pegasus.sh` (同上) | `IZANAGI_S4_STOCK_CONTROL` (未設定 / `0` off、`1` on、他・設定済み空値 rc=2)、`stock_identity_argv` (manifest + 任意宣言値、coder-role なし)、候補 rc 捕捉、stock step、rc 集約。+32/−2 行 |
| `orchestrator/tests/test_p3_s4_loop.py` (author + fix1 + fix2、commit `c6eb77597` / `46cc32feb`) | 新 test 22 関数 (stock 経路 / 較正 CLI / verify opt-in / identity / gate / resolver / rc 契約、§2)。既存 test の期待値は不変 |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py` (author、`c6eb77597`) | 逐語 pin 7 個 + mutation 対、driver 呼出し箇所数 2 → 3、stage-order、実 shell helper の履歴化 (argv 履歴・rc・compute-result)、実 shell test 4 本 + static test 1 本 |
| `orchestrator/tests/test_pipeline_verify_result_retention.py` (author、`c6eb77597`) | 実 `pipeline.evaluate` + 実 verifier で legacy → performance `reps` 回、anomaly (初回 / 最終) の bench 前停止、legacy 赤、numactl exact の 5 test |
| `orchestrator/tests/test_p3_exploration_namespace.py`、`orchestrator/tests/test_p3_b4_wiring_probe.py` (fix2、`46cc32feb`) | 静的 inventory pin の更新: p3_s4_loop の `ast_layout_calls` 10 → 11、`ast_run_campaign_calls` 1 → 2 (runtime は 1)、静的 import 閉包 47 → 49 (`p2_2` + `genome`。`source_digest` は旧閉包に既在)。由来 comment 付き |
| `tools/pegasus/README.md` (親 docs、`46cc32feb`) | 同 job pair の節、fence (1 個) に `IZANAGI_S4_STOCK_CONTROL`、「manifest・宣言値は proposal 分岐だけ」を coder-role のみに限定、driver opt-in は job body 未配線の注記 |
| `docs/spool/worklog/…`、`docs/spool/decisions/…` | worklog fragment (T-2795 / T-2797 / T-1872 / T-2632 の更新)、decisions fragment (設計判断) |
| 本 insight | 記録と逐語 (`verbatim/`) |

触っていない: `pipeline.py`、`loop.py`、`ident.py`、`source_digest.py`、`build_admission.py`、`condition_meaning_gate.py`、`p2_2.py`、事前登録
(`docs/b5-generator-contrast-preregistration.md`、凍結)、phase doc、paper-story。

## 2. 契約 (段 4 裁定 §2 + 追補 1、段 6 で確定)

- **stock の口:** `p3_s4_loop --stock-control --isolate-worktree --fetchcontent-prebuild-receipt R [--knowledge-manifest M --knowledge-classification C --knowledge-de-novo-claim false] [--calibrated-perf --perf-workload W [--verify-performance]]`。
  `--allow-coder-derived-build` は渡さない (stock の build は coder 由来でない。build context は `build_run_context(generator_id=BACKOFF_SWEEP)`、
  policy は coder authority に依存しないので identity は候補と同じ)。
- **同 campaign:** identity preimage (spec_content / ccbench_commit / search_tag / search_config / trial) に genome も `--stock-control` も入らない。
  K2 manifest の SHA / level と admission policy は search_config で束縛されるので、job body は stock にも同じ manifest / 宣言値を渡す
  (knowledge receipt は同 bytes なら既存を受理)。critic identity projection は `src_token` で stock label を付ける (class 名ではない)。
- **stock 形 condition gate:** `BACKOFF_FIXED == -1` で `stock_root` 必須、`capture_define_inputs(source_root, stock_root=)`、
  `make_define_request(..., requested_value=-1, default_value=-1, stock_comparison=True)`、`MeaningCase(-1, None, expected_selected_branch=STOCK_ADAPTIVE_BRANCH)`。
  stock_root = `external/ccbench` (`assert_pinned_clean` 済み。`--isolate-worktree` 下で評価 tree と別)。候補の呼出し `_require_condition_gate(sub, genome)` は逐語不変。
- **admission:** `_stock_capability_resolver(build_context)` は `evidence.src_token == STOCK` のとき `attest_generator_output(..., generator_input_sha256=sha256("p3-s4-loop-stock-control/v1|" + genome_sha256))`、
  それ以外は None → pipeline が admission-error で abort (fail-closed)。
- **outcome:** `certified-stock` (rc 0) / `aborted` / `non-stock-source` / `skipped` / `identity-skipped` (rc 1)。stdout は
  `=== 段 4 stock control (stock_root=..., isolate_worktree=True) ===`、`  outcome=... variant=... fitness_tps=... verdict=...`、`  campaign dir: ...`。
  stock 後に `s4_loop_digest.txt` を admitted view から再生成 (checkpoint / whiteboard は不変)。
- **job body:** `case "${IZANAGI_S4_STOCK_CONTROL-0}"` (設定済み空値も拒否)、`candidate_rc=0; stock_rc=0`、候補の既存呼出し末尾に ` || candidate_rc=$?`、
  stock: `"$PY" -B -m orchestrator.campaign.p3_s4_loop --isolate-worktree --fetchcontent-prebuild-receipt "$prebuild_receipt" "${stock_identity_argv[@]}" --stock-control || stock_rc=$?`、
  `echo "p3 S4 pair: candidate_rc=... stock_rc=..."`、候補非零優先で exit。`set -Eeuo pipefail`・EXIT trap・compute-result schema は不変。
- **較正 CLI:** `calibrated_perf(name) = PerfConfig(records=p2_2.RECORDS, threads=p2_2.THREADS, workload={**dict(p2_2.WORKLOADS)[name], "ycsb_max_ope": S2_FLAGS["ycsb_max_ope"]}, extime=p2_2.EXTIME, reps=p2_2.REPS)`。
  2 口同時必須、verify は較正必須。identity key は `perf_workload` (既存 `workload` key は他 driver で token 文字列 / name 付き dict の別意味、D75)。
  correctness は legacy 1 回 + performance `perf.reps` (5) 回 (§5.5 は回数を定めない)。記録先 = campaign.lock preimage。

## 3. 段 2〜3 の所見と裁定

段 2 plan (codex read-only、6 分): pipeline.py / loop.py は変更不要、`--stock-control` 独立口 + 新関数、terminal 復元の二層化、較正 2 口、verify opt-in、
Q1〜Q4。段 3 consult 2 本 (sol / luna、各 4〜5 分): **must-fix 3 件 (すべて real・採用)** = A-M1 非 STOCK の certified を stock 成功に含めない、
A-M2 候補用 condition gate は stock の意味 (適応枝) を検査しない → A-1 paired 形 + `--isolate-worktree` 必須、B-M1 TJ の driver 呼出し箇所数 2 → 3 と
fixture fragment。should 8 件採用 (anomaly 最終 rep の負例、campaign.lock 復元 test、rc と測定成功の区別、terminal 復元の二層化を削る (skip = 非成功)、
変異 6 の kill は実 shell test へ、TJ helper の履歴化、TV は bench 到達可能で、README は置換)。削った要素: terminal 復元の二層化、較正・verify の
job body env 配線 (β へ)、inert を証明しない token/projection test。P1 (同 campaign) 支持、P2 条件付き、P3 支持 (key 名 `perf_workload`)、P4 条件付き
(lock 永続化 test)、P5 条件付き (rc 0 初期化・集約)、P6 支持。裁定全文 = `verbatim/s4-adjudication.md`。

段 5 author (27 分) は 5 file を実装し TJ 107 / TV 11 / TL 548 passed、1 failed で**未了を正直に報告**: stock source の admission が
`derive_build_admission` の stock-baseline 条件 (full / short PIN 不一致) で admission-error になる。追補 1 (`verbatim/s4-addendum-1.md`) で stock 経路限定の
`capability_resolver` を裁定し、fix1 (8 分) で完成 (TL 550 passed、M16 / M17 追加)。

## 4. 段 6 レビューと fix2

- review A (正しさ境界・identity・admission・WAL): **must-fix 0 / should 1 (stock gate の赤 → 拒否伝播の負例) / GO**。規律 2・admission の fail-closed・
  同 campaign・既定 identity・stock gate・exact correctness・LoopState 不変・job body の各境界を現物で確認 (`verbatim/s6-review-A.md`)。
- review B (既定挙動不変・過剰・削除・test の実効・変異帰属): **must-fix 0 / should 2 (既定候補 main の preimage 比較、layout ID の観測) / nit 2 / GO**。
  hunk 分類で既定経路の変更なし、削除裁定の要素は残っていない、新 test の層と変異 M0〜M17 の kill 予測、報告件数の照合 (TL 509 → 550、TJ 82 → 107、TV 6 → 11)
  (`verbatim/s6-review-B.md`)。
- 親の焦点走 1 (計算ノード request 12619.nqsv、15 file、129 秒): **1741 passed / 2 failed / 1 skipped**。2 failed は本差分に帰属する静的 inventory pin
  (`test_p3_exploration_namespace` の layout 呼出し数、`test_p3_b4_wiring_probe` の閉包 module 数)。T-2746 の先例どおり pin を由来 comment 付きで更新 (fix2)。
- fix2 (test のみ、9 分): A-S1 / B-S1 / B-S2 / B-N1 closed、pin 2 件更新 (閉包差の実測 = `p2_2` + `genome`、指示の `source_digest` は旧閉包に既在と訂正)。
  TL 553 passed。焦点再レビュー 1 本 = §4.1。
- 統合 commit: `c6eb77597` (実装 + test)、`46cc32feb` (fix2 + README)。

### 4.1 焦点再レビュー (fix2)

codex read-only 1 本 (`verbatim/s6-focus.md`): **A-S1 / B-S1 / B-S2 / B-N1 / 焦点走 red 1 / red 2 の 6 所見すべて closed、must-fix 0、GO。**
確認点 = A-S1 は `_REAL_CONDITION_GATE` を戻し、production の `_issue_arm_record()` が発行する赤 record で実 `require_condition_gate_family` を通し、
evidence 書出し (`IZANAGI_S4_EVIDENCE_ROOT`) と `run_campaign` 未到達 (`calls == []`) を検査。B-S1 は新 option なしの候補 main で identity 確定後の
cfg を捕捉 (固定定数は不変)。TL の case 数は 550 + 2 + 1 = 553 で fix2 の報告と整合。AST 再集計 = layout 11 / run_campaign 2 (追加は stock 分岐と
`_run_stock_control_resolved`、いずれも build_context 束縛)。閉包差 = `p2_2` と (p2_2 経由の) `genome`、`source_digest` は `pipeline` 経由で旧閉包に既在。
fix2 報告の残存失敗 `test_source_and_test_are_the_only_non_output_worktree_changes` は子の dirty 作業木由来で clean な統合 commit では成立しない
(焦点走 2b で確認)。新規 nit C-N1 = README の digest 再生成の条件省略 → 親が「stock が skip でなく WAL record が存在するとき admitted view から
再生成」に直した。閉包差分と fence の自動再集計は子の hook 拒否で静的照合に留まる。

## 5. 変異 matrix (事前登録 → probe → 本走)

事前登録 = 裁定 §3 (M0〜M15) + 追補 1 (M16 / M17)。spec 生成器 `make_mutation_spec.py` (job dir) が統合 commit 2 の現物から exact old / new を組み、
18 anchor がすべて一意であることを検査した。独立 clone (D1009、main = `46cc32feb`) で `tools/mutation_worktree.py --runner-mode dispatch`、
runner = `run_tests.py --force-dispatch` × 3 test file (TL / TJ / TV)。

**probe (全件 SURVIVED 登録で観測 node を集める走、spec sha256 `082d3f36…`、`verbatim/mutation-spec-probe.json` / `verbatim/mutation-probe-out.json`):**
baseline PASSED (rc 0、37.6 秒)。**M0 SURVIVED (等価対照)、M1〜M17 は全件で失敗 node を観測 (probe 形なので MISMATCH 17)**。各変異の観測 node 数と主担当 node:

| # | 変異 (位置) | 観測 node 数 | 主担当 node (裁定 §3 / 追補 1 の予定) |
|---|---|---:|---|
| M1 | stock genome `BACKOFF_FIXED` −1 → 1 | 2 | `test_stock_control_reaches_campaign_under_applied_template` (+ 同 manifest identity test) |
| M2 | stock genome `BACK_OFF` 1 → 0 | 1 | 同上 |
| M3 | stock 関数の末尾で checkpoint を保存 | 5 | `test_stock_control_does_not_touch_loop_state[False/True]` (+ skipped ×2、digest) |
| M4 | stock + `--run-iteration` の排他を外す | 1 | `test_stock_control_cli_rejects_conflicting_modes[extra0-run-iteration]` |
| M5 | 負値で attribution を skip | 1 | `test_fixture_value_minus_one_remains_rejected` |
| M6 | job body の stock 起動から identity argv を落とす | 56 | `test_pair_job_runs_candidate_then_stock[k2]` (+ TJ static contract / fragment pin の連鎖) |
| M7 | stock 成功条件から STOCK 判定を外す | 2 | `test_stock_control_rejects_non_stock_certified_source[False/True]` |
| M8 | 較正 opt-in で records / threads を identity に焼かない | 5 | `test_calibrated_cli_binds_effective_perf_before_layout[True/False]` (+ candidate 版 ×2、lock 復元) |
| M9 | 指定なしでも identity key を足す | 2 | `test_default_cli_preserves_preimage_bytes` (+ stock reaches campaign) |
| M10 | stock gate を候補宣言 (`stock_comparison=False`) に | 1 | `test_stock_condition_gate_declares_adaptive_branch[-1]` |
| M11 | job body の stock env 既定 on | 61 | `test_default_job_invokes_driver_once[None-fixture]` (+ TJ static contract の連鎖) |
| M12 | proposal 末尾の候補 rc 捕捉を外す | 56 | `test_pair_job_runs_stock_after_candidate_failure[rcs0-7-proposal]` (+ 連鎖) |
| M13 | 最終分岐を stock rc だけに | 58 | `test_pair_job_runs_stock_after_candidate_failure[rcs0-7-proposal/fixture]` (+ 連鎖) |
| M14 | `--verify-performance` で verify key を焼かない | 3 | `test_verify_opt_in_reaches_real_loop_evaluate_options[True]` (+ 較正 identity、lock 復元) |
| M15 | pipeline の repetition loop を初回 pass で打ち切る | 74 | TV `test_performance_anomaly_at_last_repetition_aborts_before_bench` (+ TV 2 本、TL 71 本 = rep 数を観測する既存 test の連鎖) |
| M16 | resolver が非 STOCK evidence にも receipt を返す | 1 | `test_stock_resolver_refuses_non_stock_evidence` |
| M17 | stock 経路が resolver を渡さない | 2 | `test_stock_digest_refresh_keeps_checkpoint` (+ stock reaches campaign) |

主担当 node はすべて観測集合に含まれる (裁定 §3 / 追補 1 の予定と一致)。job body の 4 変異 (M6 / M11 / M12 / M13) は TJ の static contract
(mutation 対 test) が「1 static failure」を要求するため、変異が入った job body に対して parametrize 全件が連鎖して赤になる — これは static inventory pin
の性質で、kill 理由 (実 shell test の主担当 node) とは別枠。M15 の TL 71 本は rep 数を観測する既存 test の連鎖で、TV の最終 rep 負例が主担当。
`DW-M08` に従い、final は観測集合を**完全集合**として登録し、完全一致だけを KILLED とする。

**final (完全集合登録、spec sha256 `a75f29a4…`、`verbatim/mutation-spec-final.json` / `verbatim/mutation-final-out.json`):** **baseline PASSED (rc 0、42.5 秒)、M0 SURVIVED、M1〜M17 = 17/17 KILLED (期待 node 完全一致、MISMATCH 0、TIMEOUT 0)。** 各変異の所要 37〜1036 秒 (中央値 46 秒、M10 は queue 混雑で 1036 秒)、合計 2215 秒。実走は 15:12〜15:55 JST、独立 clone の HEAD `46cc32feb`、results JSON の sha256 = probe `64309c42…` / final `5005b5ea…` (要約 JSON が束縛)。M15 は pipeline.py (本 wave で変更していない production) への変異で、TV の最終 repetition 負例が新設 test として検出する (test 強化の層。旧 TV 6 件は通過することを author が報告)。

## 6. 受入全走・検査

- 焦点走 1 (統合 commit `c6eb77597`、計算ノード request 12619.nqsv、129 秒、15 file = 変更 3 + consumer 10 + メタ 2): **1741 passed / 2 failed / 1 skipped**
  (`verbatim/focus-post-fix1.log`)。2 failed = 静的 inventory pin (§4)。焦点走 2b (統合 commit `46cc32feb`、request 12681.nqsv、117 秒、同 15 file):
  **1746 passed / 1 skipped / 0 failed** (`verbatim/focus-post-fix2b.log`)。焦点走 2 (14:21 JST) は provenance 監査の dispatch と同 worktree で
  並行投入して orphan hold (rc=16、走行ゼロ) — DW-O26 の直列違反、監査終端後に 2b で再投入。
- `python3 tools/check_docs.py` 違反なし (3 回)、`git diff --check` rc=0、provenance range 監査 (`371674ea6..HEAD`、2 commit) 違反なし。
- 三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`、記録 commit 前): holdout hit は rr80 / rr20 各 4 件で、いずれも既存の凍結
  artifact (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/*`、`output/s8b-freeze-candidates/holdout_freeze.v2.g1.json`)。
  **本 wave の変更 file (12 path) は hit に含まれない** (rr50 の一般 hit 231 件は fig5〜8 の provenance 等と同じ従来からの一般 hit)。
- **final**: 記録 commit の tip で clean tree から `tools/dev_wave_wait.py acceptance` (3 shard) を門番 loop (他 wave の leader ≤ 1 ∧ load ≤ 60、jitter)
  から 1 回投入する。結果は本 README には書かず (受入は記録の後)、受領証 (`acceptance-receipt-final-<n>.json`、job dir) と land の記録が持つ。
  child-green でなければ land しない。

## 7. 言ってよいこと・言ってはいけないこと・次の一手

- 言ってよい: §0 の「主張する」。言ってはいけない: §0 の「主張しない」。
- 次の一手 (別 wave、いずれも認可済みまたは裁定済み):
  - **pair 投入 (D2172 項 3 (i)):** fresh submit-tree + fresh layout で候補 10 + stock を 1 job (`IZANAGI_S4_STOCK_CONTROL=1`)。3 巡目の記録に pair 結果を追記。
    最初に実 compiler での STOCK 成立 (stock の `outcome=certified-stock`、admission receipt の source `src_token`) を確認し、成立しなければ対照成立と認定しない。
  - **4 巡目 (項 3 (iv)):** 新規生成 1 回 + 同 job stock 対照 1 本 (1 job、再投入なし)。
  - **B-5 試走 (β) (項 4):** 較正・verify opt-in の job body 配線 (launcher 設計) と 1 workload・3 arm × 1 系列・60 論理 session 以下。verifier wall の実測を残す。
- 裁定パッケージ候補 (実装せず): `build_admission.derive_build_admission` の stock-baseline 分岐が full PIN と短縮 `CURRENT_PIN` を exact 比較する点
  (S4 の stock は machine-generated class で admission される)。正規化は admission gate の変更なのでユーザー裁定。
- 設計メモ (scope 外、DW-G04): stock 先行 (planner 前) の順序選択 env、block stock の配置、実 argv の独立 receipt。

## 8. 一次資料

- 依頼・brief・裁定・追補: `verbatim/T-2795-origin.md`、`verbatim/brief.md`、`verbatim/s4-adjudication.md`、`verbatim/s4-addendum-1.md`
- 設計メモ 項 6 (K2 round 3): `verbatim/design-memo-item6.md` (= `output/insights/2026-09-19/k2-loop-round3/reviews/s2-plan.md` 項 6)
- codex 入出力: `verbatim/s2-plan{-prompt,}.md`、`verbatim/s3-consult-{A,B}{-prompt,}.md`、`verbatim/s5-author{-prompt,}.md`、`verbatim/s6-fix1{-prompt,}.md`、
  `verbatim/s6-review-{A,B}{-prompt,}.md`、`verbatim/s6-fix2{-prompt,}.md`、`verbatim/s6-focus{-prompt,}.md`
- 走: `verbatim/focus-post-fix1.log`、`verbatim/focus-post-fix2b.log` (行末空白の可逆正規化、`verbatim/NORMALIZATION.md`)、`verbatim/mutation-spec-{probe,final}.json`、`verbatim/mutation-{probe,final}-out.json` (results JSON の sha256 束縛の要約)
- job dir (repo 外): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2795-pair-launcher/` (HANDOFF.md、launcher、受入 log)
