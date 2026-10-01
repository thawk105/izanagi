# 段 A の軸 (競合度順の施錠) を探索ループへつなぐ — 小モデル結果の関門・要求つき判定器・反例の返却 ([T-2888]・[T-2946]、gen-opt md_20、2026-09-30〜10-01)

authority: none
default_effect: no-state-change

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20.txt` と `common-5.txt` (repo の外。逐語の写しは job dir `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/`)。
- wave: `dev-wave-md20-lock-order-loop` (branch `worktree-dev-wave-md20-lock-order-loop`)。着手時 local main `908741c6f`、開始 gate rc=0 (`verbatim/startup-gate.log`)。
- 前提の一次資料: 段 A の軸 `output/insights/2026-09-30/gen-opt-lock-order-axis/README.md` (md_13)、判定器の意味の版 2 `output/insights/2026-09-30/gen-opt-gate-verifier/README.md` (md_14、D2321)、関門の設計 `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` §4.4・§7 (U5)、段 A の候補 `output/insights/2026-09-29/gen-opt-stage-a-candidate/README.md` §4・§5。
- 段の記録: `verbatim/` (brief・段 2 plan・段 3 相談 2 本・段 4 裁定と追補・段 6 レビュー 2 本・段 6 裁定 2 本と追補・焦点再レビュー)。

---

## 0. 結論

- gen-opt の段 A の軸に、**候補 → 検疫・文法・単独 compile (order_gate) → 仕様 digest ごとの小モデル結果の関門 (build 前) → 要求つき判定器 → 閉じた history 行 → 次の coder 入力** の 1 周をつなぐ driver `orchestrator/campaign/p3_s4_loop_lock_order.py` ができた。生成器対照の部品 (`p3_s4_loop_policy.py` ほか) は 1 byte も変えず、import して部品を使う。
- 判定器の capability 経路 (`verify_trace_dir_with_capability`) と pipeline (`run_campaign` → `evaluate` → 各検証反復 → build 出口の再照合) に `require_gate_witness` を通した。Silo で `SILO_ORDER_VARIANT≠0` の genome は caller に依らず要求つきになる。要求時の D5 は **build 時に捕えた source snapshot の text** で評価し、disk を読まない ([T-2946]、D2321 の「driver 接続と同時に行う」義務)。要求なしの既存呼出しは keyword も snapshot の field も出さない。
- 小モデル結果の受け口 `cc-model-result/1` (最小の閉じた形) と関門 `orchestrator/campaign/silo_lock_order_model_gate.py` を足した。期待する仕様 digest・登録場面は結果 file からでなく軸の定数 (既定は未登録) から取り、**未登録なら全候補を build 前に拒否**する。反例は `tools/cc_model_checker/schema.py` の `validate_counterexample` を通したものだけを、閉じた field で history 行へ返す ([T-2888])。
- **生死確認 (計算ノード 1 job、起動器・fixture 付き):** 名前つき対照 (版が新しいほど先に施錠) を driver の関数経路で通した。本番の登録簿のままでは `model-unregistered` で build 0 回・拒否行。fixture の小モデル結果を明示して通すと、U1 + Silo 修正 + 骨格の trace build で **2 workload とも D1・D2 の違反 0・D5 pass・要求 true・意味の版 2・serializable・certified、history 行 certified**。Silo 修正を外すと **D2b 違反で indeterminate、history 行は `verifier-not-certified` と違反件数**を返した。
- **これは配線の確認であり certified の主張ではない。** 小モデル結果は fixture、build は起動器の直 build (pipeline の source 証拠と build 受理を経ない)、pin は C のまま。gen-opt の候補の certified は、pin 前進 (md_15) と小モデル本体 (md_19) の着地後に pipeline 経由で取り直す。

## 1. 何を作ったか

| file | 中身 |
|---|---|
| `orchestrator/verifier/core.py`・`model.py` | capability 版に `require_gate_witness` (keyword、既定 False)。要求時だけ D5 証拠束 (`include/ycsb.hh`・`cc/silo/transaction.cc`・`cc/silo/ycsb_silo.cc` の text と include 解決の真偽) を snapshot に捕え、`_gate_d5_sources` で評価。述語は md_14 の `_gate_d5` と同じ (MEANING_VERSION は 2 のまま)。disk 版は CLI 用に残した |
| `orchestrator/campaign/source_digest.py` | 実効要求の純粋関数 `effective_gate_witness_requirement` (明示 or Silo の `SILO_ORDER_VARIANT≠0`)。snapshot の serialize は要求時だけ `gate_d5_sources` を足す (要求なしの JSON は従前と byte 同一、deserialize は未知 field・欠落・型違いを拒否) |
| `orchestrator/campaign/loop.py`・`pipeline.py`・`buildcache.py` | `run_campaign(..., require_gate_witness=False)` → `evaluate` → `_prepare_evaluation_core` → 全検証反復 (local concurrent を含む) → build 出口の再照合 (新規 build・cache hit) まで要求を運ぶ。要求つきの反復だけ `verify_payload` (WAL の verify_done) に `gate_witness` 節を載せる。fan-out (backoff 専用) は変えない |
| `orchestrator/campaign/layer3_schema.json` | `verifications.items` に optional の閉じた `gate_witness` を足した (D828: `schema_version`・`required` は据え置き、D829: view で消さない) |
| `orchestrator/campaign/silo_lock_order_model_gate.py` | `cc-model-result/1` の読込と照合 (§2) |
| `orchestrator/campaign/axis_silo_lock_order.py` | 登録簿の定数 `MODEL_SPECIFICATION_DIGEST`・`MODEL_SCENARIOS`・`MODEL_VOCABULARY` (すべて None = 未登録) |
| `orchestrator/campaign/p3_s4_loop_lock_order.py` | driver (§3) |
| `orchestrator/campaign/materializer_admission.py` | 新 driver の CLI を coder 権限の発行元として 1 項目登録 (既存 5 軸と同型、段 4 追補裁定 1) |
| test | 新規 `test_verifier_capability_gate_witness.py`・`test_pipeline_gate_witness.py`・`test_silo_lock_order_model_gate.py`・`test_p3_s4_loop_lock_order.py` (自走 harness 付き)。既存 test は inventory の実数の追記 (`test_p3_exploration_namespace.py`・`test_campaign.py` の certified-writer inventory・`test_p3_build_authority_cli.py`) と、層 3 の閉包 test の条件つき key の分類 (段 6 追補裁定 1) だけ |

production の追加は判定器・pipeline 側が約 130 行、関門・driver 側が約 575 行 (段 4 裁定の上限 350・600 行の内)。

## 2. 小モデル結果の受け口 (`cc-model-result/1`、md_19 が合わせる最小の形)

- top = {`schema`, `axis`, `specification_digest`, `scenarios`}。scenario = {`scenario_id`, `complete`, `stop_reason` (`exhausted`・`max_states`・`max_seconds`)、`explored_configurations`, `witness_reached` (bool か null), `counterexamples`}。重複 key・NaN・余分 field・場面の重複を拒否。上限: 場面 4,096、反例は結果全体で 64。
- 反例は `validate_counterexample` (`cc-model-counterexample/1`) を通し、外側の digest・scenario_id と一致させる。登録簿に語彙があれば `vocabulary=` で渡す。
- 照合 (build 前、別々の拒否コード): 未登録 `model-unregistered`、欠落 `model-result-missing`、schema 不正 `model-result-invalid`、axis/digest 不一致 `model-digest-mismatch`、登録場面の欠落 `model-scenario-missing`、未完了 (complete 偽か stop_reason ≠ exhausted) `model-incomplete`、構成数の不一致 `model-coverage-mismatch`、witness 未到達 `model-witness-missing`、反例あり `model-counterexample`。
- **期待 digest を結果 file から取らない** (自己申告は恒真)。登録外の場面の存在は拒否しないが、**反例はどの場面で出ても拒否**する (段 6 裁定 1 で B1 を refuted: 拒否は安全側)。
- 結果 file が実際の checker の実行から来たことの束縛 (再生・生成元) はこの受け口では検査しない。本番の登録 (定数に digest と場面を書く判断) が、その束縛を確かめる点になる (§6)。

## 3. driver (`p3_s4_loop_lock_order.py`)

- 順序: 閉じた proposal の intake (axis `silo-lock-order-policy`、重複 key 禁止、名前つき対照は origin `initial`) → `order_gate(write=False)` → 小モデル関門 (本番の登録簿だけを使い、差し替え引数を持たない。拒否は history に 1 行書き build しない) → 骨格 patch と `order_gate(write=True)` → `run_campaign(..., require_gate_witness=True)` (方策軸と別の campaign identity) → 当該 build attempt の verify_done 記録を WAL から全件読み、**全件の gate 節が required・版 ≥ 2・D5 pass で、かつ campaign が certified** のときだけ certified 行 → `lock_order_history.jsonl`。skip された variant は certified にしない。
- history 行の閉じた key: `schema, iteration, axis, proposal_digest, variant_id, outcome, reject_code, model_specification_digest, model_evidence_kind (registered・fixture・unregistered), model_scenario_ids, counterexamples, verifier_digest, measurement_campaign_id`。反例は 1 行 2 件まで、`scenario_id`・`judgment_id`・`rule_ids` だけ。gate 違反は 8 計数 (unreachable・D1a・D1b1・D1b2・D1c・D2a・D2b_i・D2b_ii) と D5 状態。例外本文・自由文は載せない。
- `--emit-coder-input` は軸の仕様の所在と閉じた `self_history` を出す。**LLM の coder role (agents・manifest・adapter・`codex_roles/policy.py` の axis 固定) と coder 向け接続仕様はこの wave に無い** (段 4 裁定 P5)。名前つき対照を proposal として通せば 1 周は成立する。

## 4. 生死確認 (計算ノード、fixture 付きの配線確認)

起動器は repo の外 (`/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_20-lock-order-loop/launcher/launch_md20_liveness.py`、Codex author、sha256 `53be38d7…`、説明と事前登録した期待は `evidence/launcher-README.txt`)。計算ノード側で node-local の TMPDIR を作る wrapper (`live-node.sh`、親) から呼ぶ。repo の driver・関門・判定器を import して、同じ関数を通す。workload は md_14 と同じ (200 record・zipf 0.9・rratio 50・1 取引 5 操作・4 thread・1 秒、RMW あり / なし)。

| job | request | 計算ノード | Elapse | 結果 |
|---|---|---|---:|---|
| live-1 | 40117.nqsv | bnode005 | 5 s | preflight で停止「node-local TMPDIR required」。dispatch の job 環境に TMPDIR が無かった (build 前、損失なし)。起動器は変えず、wrapper で node-local の dir を TMPDIR に渡す形にした (`evidence/live-1-result.json`) |
| live-2 | 40121.nqsv | bnode058 | 160 s (起動器の計測 155.6 s) | 下表 (`evidence/live-2-result.json`) |

木は wave の `c33afae78` (fix 1 の後。fix 2 は層 3 の schema と test だけで、起動器が通る経路は同じ)。

| 条件 | 中身 | 小モデル関門 | commit / abort | 判定 (要求つき) | history 行 |
|---|---|---|---|---|---|
| M | 名前つき対照、本番の登録簿 (未登録) | `model-unregistered` | build 0 回 | — | rejected `model-unregistered`、evidence `unregistered` |
| X | U1 `dcb9a41f3` + Silo 修正 + 骨格 + 対照 | fixture で合格 | RMW あり 194,803 / 8,447、なし 228,386 / 9,698 | 両方 D1・D2 違反 0、D5 pass、required true、版 2、**serializable・certified** | **certified**、evidence `fixture` |
| S | U1 + 骨格 + 対照 (Silo 修正なし) | fixture で合格 | RMW あり 194,978 / 8,068、なし 227,656 / 9,903 | D2b (i)/(ii) = 31,498 / 15,125 (RMW あり)、1,565 / 17,643 (なし)、他 0、D5 pass → indeterminate | rejected `verifier-not-certified`、gate 計数つき |

- patch は `git apply` で fuzz なし (Silo 修正は offset 4、骨格は offset 4〜66 行)。trace build は各 5 s、1 run + 判定は 27〜31 s。
- 判定経路は `verify_trace_dir(require_gate_witness=True, _proof_source_snapshot=<build 前に捕えた snapshot>)`。直 build には pipeline の `SourceEvidence`・`BuildAdmission` が無いので capability を作らず、理由 (`not-issued`) を記録した (捏造しない)。
- S の D2b の違反は、md_14 の条件 S (修正前の Silo) と同じ型 (取引内で自分の書きを読まない / 2 度目の書きが据わらない) で、判定器が要求つきで理由を構造化して返し、driver の投影が拒否コードと件数を次の入力へ載せることの実例になっている。

## 5. test と検証

焦点走 (計算ノード、`tools/run_tests.py --force-dispatch`、変更 test + consumer test + inventory 4 群):

| 回 | request | commit | file 数 | 結果 | Elapse (pytest の所要) |
|---|---|---|---:|---|---:|
| f1 | 40044.nqsv | `61aaf3714` (段 5 統合) | 38 | 10 failed / 3,860 passed / 5 skipped | 182 s (176 s) |
| f2 | 40108.nqsv | `c33afae78` (fix 1) | 39 | 1 failed / 3,900 passed / 5 skipped | 182 s (177 s) |
| f3 | 40135.nqsv | `8631dee79` (fix 2) | 41 | **4,055 passed / 11 skipped** | 268 s (262 s) |

- f1 の赤 10 件: 新 test の組み立て 8 件 (実装子は sandbox から試験を走らせられず、全件未実走で出していた)、perf 閉包へ不要な行を足した 1 件、`run_campaign` の末尾 2 引数を固定する既存 test に対し新 keyword を末尾に置いた 1 件。すべて自分起因で、既存 test の期待値は変えずに直した。
- f2 の赤 1 件: `test_layer3_report.py::test_verification_producer_keys_and_schema_closure`。verify_payload の全 key を層 3 schema が知っていることを要求する閉包 test で、fix 1 の `gate_witness` に反応した。schema に optional property を足し、閉包 test に条件つき key の分類を足すことを追補裁定で許した (その 1 test の 2 点だけ)。
- skip は f3 で 11 件 (足した file の分)。内訳は特定していない。
- 全史の provenance 監査: 段 5 統合後 rc=0 (13,833 件、新規違反なし)。

### 5.1 変異検査 (事前登録 M1〜M12 = 段 4、M13〜M15 = 段 6、`mutation/`)

対象 commit `8631dee79` を main に固定した独立 clone (D1009) に `tools/mutation_harness.py` を当て、runner (新 test 4 file) を計算ノードへ dispatch した。期待 node は全件 SURVIVED 期待の dispatch probe で観測した完全集合 (DW-M08)。

| 走 | request | Elapse | 結果 |
|---|---|---:|---|
| probe | 40144.nqsv | 5 s | 親が完全 SHA を誤転記し「commit 解決に失敗」で停止 (`mutation/erratum-1.md`) |
| probe2 | 40151.nqsv | 328 s | 基準走 緑 (38 passed)、M0 SURVIVED、負の 15 本すべて赤 (`mutation/out-probe2.json`) |
| probe3 | 40202.nqsv | 128 s | 狙い直した M13b の観測 (`mutation/out-probe3.json`) |
| **本走** | 40203.nqsv | 316 s | **KILLED 15 / SURVIVED 1 (M0)、16 本すべて期待と完全一致、基準走 緑** (`mutation/out-final.json`、spec `mutation/spec-final.json` sha256 `57f28273…`) |

| id | 変異 | owner の証拠 (drift を受けない赤) |
|---|---|---|
| M1 | pipeline の flag 由来の強制を外す | `test_m1_flag_forces_required_evaluate` |
| M2 | loop が evaluate へ要求を渡さない | **なし** (赤は drift の test_m2 だけ。§ erratum) |
| M3 | capability が要求を verify へ渡さない | `test_m3_required_capability_rejects_absent_gate_file` ほか |
| M4 | 要求時の D5 を disk から読む | `test_m4_required_d5_uses_snapshot_not_disk` |
| M5 | 要求なしでも証拠束を serialize | `test_m5_unrequested_snapshot_legacy_bytes` |
| M6〜M10 | 関門の未登録・digest の自己申告・stop_reason・場面欠落・反例を受理 | 各 `test_m6`〜`test_m10` |
| M11 | 反例の投影に余分な field | `test_m11_counterexample_projection_has_exact_keys` |
| M12 | certified 行が required を見ない | `test_m12_required_false_cannot_certify` ほか |
| M13b | build 出口の再照合が要求を渡さない | `test_m13_build_exit_rechecks_required_snapshot_for_fresh_and_hit` |
| M14 | 要求つき反復の payload に gate 節を載せない | `test_required_repetition_reaches_capability` |
| M15 | driver が verify_done 記録の 1 件目だけを見る | `test_m15_second_verify_record_required_false_rejects` ほか |

- **drift による赤:** `test_m2_explicit_requirement_passes_run_campaign` は `run_campaign` 起動時の contract-loader の照合 (閉包 file の disk bytes = HEAD blob) を通るので、閉包 file (loop.py・pipeline.py・buildcache.py・判定器ほか) への変異では内容と無関係に赤になる。完全集合には含めて登録したが、owner の証拠には数えない (先例: T-2253)。
- **M2 は owner の証拠が無い。** loop.py は閉包の中で、注入方式ではその運搬だけを赤にする test を置けない。gen-opt の genome (`SILO_ORDER_VARIANT≠0`) では pipeline 側の強制 (M1、owner あり) が独立に効くので、loop の運搬が落ちても要求は外れない。
- **M13 は狙いが外れていた** (置換位置が `build_v2` の中で、test の経路で使われない)。出口の再照合 (`_recheck_source_evidence`) へ狙い直した M13b を登録した。`build_v2` の経路を要求つきで通す test は無い (落としても出口で fail-closed に止まる)。
- 単一理由性は、段 6 のレビュー 2 本の静的点検と、本走の観測集合 (各変異の赤が owner test + drift の test_m2 に限られる) で確かめた。

## 6. 段の経過と裁定

- 段 2 plan (条件付き GO)、段 3 相談 A (NO-GO: 小モデル結果の自己申告、終端済み variant の skip、fan-out は backoff 専用)・B (条件付き GO: fixture が certified へ流れうる、schema の作り込み過ぎ)。段 4 裁定で受け口を最小の形にし、期待 digest を独立の登録簿に置き、fixture の登録簿は関門関数の単体でだけ渡せる形にした。
- 段 5: 実装子 2 本が試験を走らせようとして rc=16 で途中停止した (子の sandbox では `tools/run_tests.py` も pytest も走らない既知の制約を prompt に書き漏らした、親の誤り)。継続子に「未実走で完成させる」と明記して出し直した。
- 段 6: レビュー A (NO-GO) の real 所見 2 件 — **要求つき build が出口の再照合で必ず不一致になる** (buildcache が要求を知らず、証拠束つき snapshot と食い違う) と、**成功時の検証結果が driver に届かない** (pipeline が反復ごとに `verify_result` を捨てる) — を fix 1 で直した (buildcache に要求を渡す、WAL の verify_done に gate 節を載せ driver が全件を照合する)。レビュー B の所見は B1 を refuted、B2・B3・B5 を採用。
- 焦点再レビュー (NO-GO) の新規所見は段 6 裁定 2 で次のとおり裁いた: local 並列検証の受信側が gate 節入りの payload を拒否する (N1) と WAL 記録数の期待反復数との照合 (N2) は backlog (新 driver は並列検証を使わない・拒否は fail-closed、記録の欠落は WAL 破損時だけ)、層 3 schema の counts が追加 key を拒む (N3) は nit。

## 7. 限界

- **生死確認は fixture 付きの配線確認である。** 小モデル結果は `sha256:fff…` の fixture、build は起動器の直 build、pin は C。capability 経路 (source 証拠・build 受理の束縛) は test で確かめただけで、実 build では通していない。pipeline 経由の 1 周は、U1 と Silo 修正を含む pin (md_15) と、`source_digest.ALLOWLIST` に U1 の header を含まない問題が解けるまで通らない。
- **小モデル結果の真偽は検査しない。** 受け口は形・digest・完了・被覆・反例を登録簿と照合するが、結果が実際の checker の実行から来たこと (再生) は md_19 と本番登録の判断の責務。登録簿は未登録のままなので、今の driver は全候補を拒否する。
- **並べ替えを使った取引の数を数える計数 build は無い** (段 4 裁定 P6)。段 A の効果評価の前に要る。
- **LLM の coder role と接続仕様は無い** (P5)。名前つき対照を proposal として 1 周させただけで、LLM が出した候補の評価ではない。
- local 並列検証 (`verify_performance_concurrent`) を要求つきで使うと、受信側が gate 節を拒否して検証を確定できない (N1、fail-closed)。driver は WAL の記録数を期待反復数と照合しない (N2)。
- 判定器 (core.py・model.py) の bytes が変わったので、変更前に作った campaign lock は land 後の main から読むと D442 の drift になる (md_14 と同じ帰結。生成器対照の本走は submit checkout なので影響しない)。
- 生死確認は各構成 1 回・小規模 (200 record・4 thread・1 秒)。

## 8. 何を確かめ、何を確かめていないか

**確かめたこと (実走・実物):** §4 の全数値 (`evidence/live-2-result.json`)。§5 の焦点走 3 回の件数 (job dir の `focus-f1.log`〜`focus-f3.log`)。§5.1 の変異 16 本の本走が事前登録と完全一致 (`mutation/out-final.json`)。patch の当たり方 (offset のみ)。全史 provenance rc=0。

**計算ノードの所要 (この wave の job 合計):** 焦点走 182 + 182 + 268 s、生死確認 5 + 160 s、変異 5 + 328 + 128 + 316 s ≈ 1,574 s ≈ 0.44 node 時間 (受入の全走は land 用で別)。

**確かめていないこと:** 受入の全走 (land の直前に行う)。pipeline 経由の要求つき判定の実 build。md_19 の実物の結果の受理。LLM の候補。並列検証経路。

## 9. 次の一手

- **[T-2888] の残り:** (1) md_19 (小モデル本体) の着地後、`axis_silo_lock_order.py` の登録簿に仕様 digest・登録場面 (期待構成数・witness の要否)・語彙を書き、実物の結果で関門を通す。結果 file が実際の checker の実行から来たこと (再生か生成元の束縛) を登録の判断点で確かめる。受け口の形が md_19 の実物と合わなければ、受け口を最小の差分で合わせる。(2) LLM の coder role (agents・manifest・adapter・`codex_roles/policy.py` の axis 固定・`projection_guard` の contract) と coder 向け接続仕様。(3) 要求つきで local 並列検証を使うなら受信側の key 集合 (N1)、本評価の前に WAL の verify_done 記録数と期待反復数の照合 (N2)。
- **[T-2896] (段 A の試し) の前提:** 済み = [T-2884] (判定器 版 2)・[T-2886] (軸の入口)・[T-2887] (小モデル部品)・[T-2946] (要求つき判定の配線、本 wave)。残り = U1 と Silo 修正を含む pin への前進 ([T-2854]・[T-2917]、md_15。前進後に骨格 patch の当て直しと pipeline 経由の certified の取り直し)、この軸の小モデルの結果 (md_19、3 取引の層を含む) の本番登録、[T-2888] の残り (1)(2)、計数 build (並べ替えを使った取引の数)。
- **[T-2896] の計算の見積り:** 単価は段 A 候補 §6.1 の pair job 1 本 0.206〜0.220 node 時間 (方策軸の実測)。名前つき対照 1 本 × workload 3 点 = 3 本 ≈ 0.62〜0.66、LLM の候補 2 本を足して 9 本 ≈ 1.85〜1.98 node 時間。小モデルの 3 取引の層を計算ノードで流すなら仮定付きで約 1.6 が加わり、合計 2 node 時間を超える → 投入前に land 調整役へ相談する (common-5 §4)。要求つき判定 (D1・D2 の照合) の追加の所要は、本 wave の生死確認で 1 run 20 万取引規模の判定が 11〜12 s だった (小規模の実測で、本評価の規模では未測定)。1 本 5 分目安への分割は、pair job を workload × 反復で割って組む (pair を 1 job に入れる原則は保つ)。
