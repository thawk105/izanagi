# 段 4 裁定 — [T-2265] 反実仮想対照

親が段 3 の 2 本 (sol v2 = 命題の健全性 / luna v2 = 閉包と歯) を real / refuted、採用 / 不採用、
scope 内 / 外へ裁定した結果である。plan v2 をこの裁定で上書きした版が plan v3 (= 実装子への指示) となる。

## 0. 本 wave が主張してよいこと (最重要。README・insight・worklog へ逐語で書く)

**本 wave は「機序に答えた」とは書かない。** 書けるのは次だけである。

> 事前登録された反実仮想試験を次 wave で走らせるために必要な、compile-time の腕・診断記録・
> 投入経路・登録簿を着地させた。**測定はしていない。** 得られる腕がどの命題に答え、
> どの命題には答えないかは §1 に書いたとおりである。

## 1. real と裁定した所見 (採用。実装へ反映する)

### R1 (sol B1, real, 採用) 固定 seed は交換可能でない → seed を option 化する
1 本の seed に固定すると割当が更新番号の決定関数になり、走行を跨いで同じ更新番号は同じ処置になる。
**実装対応:** seed を `CCBENCH_BACKOFF_STEP_POLICY_SEED` として CMake option 化する (既定 =
`0x9E3779B97F4A7C15` の 10 進表記)。**次 wave が独立 seed を複数使えるようにするのが本 wave の責務**で、
seed の選び方・本数・事前登録は次 wave。

### R2 (sol B3, real, 採用) 処置後選択を避ける材料を今のうちに記録する
`inversion_realized` での層別は処置の後で選ぶ操作なので偏る。**割当の前に決まる量**を記録しなければ
次 wave は不偏な副解析すらできない。
**実装対応:** trace v2 に **`both_actions_feasible`** を追加する。**割当を適用する前**に、推奨差分と
その符号反転の**両方**が clamp を受けずに適用可能かを pre-state から判定した値とする。
これで trace は 4 項目増える (`recommended_delta_sign` / `assigned_invert` / `inversion_realized` /
`both_actions_feasible`)。

### R3 (sol B2, real, 採用するが実装は次 wave) 推定量は方向的中率ではない
的中率の差は処置効果の推定量ではない。**ただし推定量を今 wave で作らない。** 結果を見る前に
事前登録すべきものを先に凍結せずに実装すると、誤った推定量が焼き付く。
**実装対応:** `_directional_success` の既存の意味は変えず、v2 では割当別の内訳を
**記述統計として**足すだけにする。README に「これは反実仮想の推定量ではない。次 wave が
事前登録する ITT が推定量である」と逐語で書く。

### R4 (sol B4, real, 次 wave へ持ち越し) 等価域・検出力・除外規則は新規事前登録が要る
旧事前登録 (±3%、7 腕、run 単位) は更新単位の ITT を覆わない。**次 wave の最初の成果物は
新規事前登録**であり、seed 一覧・主推定量・層・除外規則・停止規則・目標検出力を結果を見る前に凍結する。
本 wave では「次の一手」に起票するだけ。

### R5 (sol must-fix, real, 採用) 「受理域を緩めない」という言い方を撤回する
正しさゲート (認証の 2 cell exact 契約) は 1 byte も変えない。診断入力言語の受理集合は
**exact literal 1 本ぶんの制御された拡張**である。brief・README・worklog でこの言い方に統一する。
(`gate-input-measurement.md` は訂正済み)

### R6 (sol must-fix, real, 採用) 旧事前登録が新実験を覆うように見える provenance を作らない
**実装対応:** 反実仮想 literal で走った artifact には `counterfactual_preregistration: "pending"` を
記録する。旧 `prereg_sha256` は driver 契約の同一性としてそのまま記録してよいが、
**それが実験の事前登録であるかのように見せない。** gate は足さない (記録だけ)。

### R7 (luna B1, real, 採用) `assigned_invert` の宣言が無い
plan v2 は `izanagi_backoff_trace_assigned_invert` を代入・参照するのに宣言していない。
trace=1 の 12 構成が compile 不能。**実装対応:** trace local 群に宣言と初期化を置く。

### R8 (luna B2, real, 採用) 割当 bit と実際の一歩の対応に歯が無い
記録する bit は正しいまま反転条件を `== 0` にする変異が全テストを通る。
**実装対応:** policy=2 で **assigned=0 の更新は推奨方向へ、assigned=1 の更新は逆方向へ**動いたことを、
安全な pre-state (clamp に触れない) で**両方**逐語検査するテストを必須にする。
LCG 系列 pin だけを policy=2 の歯にしない。

### R9 (luna B3, real, 採用) schema を v3 へ上げる
A+B+C の stack で作った artifact が旧 A+B と同じ schema 名を持つのは provenance の欠陥。
**実装対応:** patch stack に C を含む走行の schema を **v3** へ上げる (A+B 導入時に v2 へ上げた前例に従う)。

### R10 (luna must-fix, real, 採用) C++ の出力と Python の parser を結合試験する
遷移 driver は実 stdout を捨てているので、field 名・順序・版が食い違っても両側が緑になる。
**実装対応:** TRACE=1 で compile した driver を実行し、**実 stdout をそのまま `_parse_backoff_trace` へ
食わせる**結合テストを 1 本置く。合成文字列テストはこれを代替しない。

### R11 (luna must-fix, real, 採用) 2 層 exact literal の逐語同一性を直接検査する
**実装対応:** `COUNTERFACTUAL_TRACE_CELLS_TEXT.replace(",", "+") == COUNTERFACTUAL_TRACE_CELLS_RAW`
(PBS から読んだ現物) を 1 本のテストで比較する。既存 literal についても同型を置く。

### R12 (luna must-fix, real, 採用) CMake 配線の歯は静的検査 1 本しかない
consumer test は `Genome.flags` を見るだけで CMake を通らない。**冗長性を主張しない。**
**実装対応:** 静的検査を「cache 既定値 0 の行」「`ccbench_universal_definitions` 内の行」の
**2 本に分け**、後者は**関数の内側にあること**まで見る (行を関数外へ移す変異を殺す)。
変異台帳では「CMake 配線の歯は静的検査のみ。実 CMake configure は通していない」と明記する。

### R13 (luna must-fix, real, 採用) 変異台帳の冗長 gate 分類を作り直す
plan v2 の冗長性主張は過大。**確実に冗長なのは** clamp / ceiling 縮小を同時に赤にする 2 件と、
登録簿欠落に対する exact 集合 + 件数 pin の組だけ。Python 側と PBS 側は別 site なので冗長でない。
**無歯として指摘された 2 件**(「LCG を gradient=0 / 推奨差分 0 / clamp 時に進めない」変異、
「trace=0 の policy 1/2 だけ診断名を残す」変異) は**歯を作る**: 前者は LCG が全更新で進むことを
特殊入力で検査、後者は preprocess 検査を policy 3 値すべてに要求する。

### R14 (親の独立発見 + luna must-fix, real, 採用) 図生成器の既存経路を壊さない
`expected_stack` を A+B+C へ**無条件に**変えると、既存 A+B 証拠の再生成が拒否される。
**実装対応:** A+B と A+B+C の**両方**を versioned に受理する。
**scope 境界:** 新 cell と新 event 項目を図が理解する改修は**次 wave** (図の作業は本 wave の scope 外)。

### R15 (親の実測, real, 採用) 単位の順序制約
`test_condition_meaning_gate.py:254` は各 DefineSpec の patch 現物を読む。**patch C の file が
存在しないと登録簿側が赤になる。** よって実装は 2 巡: 先に単位 A (patch C + 遷移テスト)、
その後に単位 B (driver/PBS) と単位 C (登録簿 + 既存 pin + 図生成器) を並列。

## 2. refuted / 不採用と裁定した所見

- **「policy=1 は D1515 の直接確認にならない」(sol) — real だが不採用ではなく §0 で処理。**
  policy=1 を落とさない。性能ビルドで測れる唯一の腕であり、逆方策の総効果という別の命題に答える。
  D1515 の再訪条件を満たすのは policy=2 + 新規事前登録 + 独立 seed の試験 (次 wave) である。
- **「12 field の receipt 波及はゼロ」(luna nit) — real。** 説明を「認証 receipt まで守られる」から
  「payload と journal の 2 面に届く」へ直すだけ。実装変更なし。
- **推定量 (ITT) の実装 — scope 外。** R3 のとおり次 wave の事前登録が先。
- **図が新 cell を理解する改修 — scope 外** (R14)。
- **反実仮想 cell の直列性認証 — scope 外。** 次 wave の前提として「次の一手」へ起票。

## 3. 変異事前登録 (DW-M01。実装前に確定。段 6 で走らせる)

| ID | 変異 (1 site) | 期待して赤になる test node (完全集合) | 備考 |
|---|---|---|---|
| M1 | patch C の `#if BACKOFF_STEP_POLICY` を `#ifdef` | `test_patch_c_uses_numeric_if_and_adds_no_include` + `test_policy_zero_matches_patch_b_transitions_exactly` | **冗長 gate** |
| M2 | cache 既定値 0 → 1 | `test_patch_c_cmake_cache_default_is_zero` | 単独 |
| M3 | `ccbench_universal_definitions` の行を関数外へ移す | `test_patch_c_universal_definition_is_inside_the_function` | 単独 |
| M4 | 反転式を `before + (proposed - before)` | `test_policy_one_reverses_safe_positive_and_negative_recommendations` | 単独 |
| M5 | 反転を clamp の後ろへ移動 | `test_inversion_is_applied_before_clamp` | 単独 |
| M6 | 反転点を `#if BACKOFF_STEP_ADAPT` の内側へ移動 | `test_policy_inversion_is_shared_by_all_step_ceiling_combinations` | 単独 |
| M7 | policy=2 の反転条件を `== 0` へ | `test_policy_two_assigned_zero_follows_recommendation` + `test_policy_two_assigned_one_reverses_recommendation` | **R8 の歯。冗長 gate** |
| M8 | LCG の加数を変える | `test_policy_two_assignment_sequence_is_exact` | 単独 |
| M9 | LCG を gradient=0 / 推奨差分 0 / clamp 時に進めない | `test_policy_two_lcg_advances_on_every_update` | **R13 で新設する歯** |
| M10 | `recommended_delta_sign` を `gradient_sign` の別名にする | `test_trace_v2_records_parity_recommendation_not_gradient_alias` | 単独 |
| M11 | `inversion_realized` を符号だけで決める (大きさを見ない) | `test_inversion_realized_is_one_only_for_unclamped_exact_inverse` | 単独 |
| M12 | `both_actions_feasible` を割当の**後**で計算する | `test_both_actions_feasible_is_computed_before_assignment` | **R2 の歯** |
| M13 | trace の版を v=2 のまま field を 1 つ落とす | `test_parse_backoff_trace_accepts_v1_and_exact_v2` | 単独 |
| M14 | C++ 側の field 名を 1 つ変える | `test_emitter_stdout_parses_with_the_real_parser` | **R10 の歯 (結合)** |
| M15 | `parse_cells` から 12 field 受理を削除 | `test_parse_cells_accepts_legacy_dynamic_and_policy_forms` | 単独 |
| M16 | `_validate_grid_contract` の tuple から `step_policy` を削除 | `test_grid_distinguishes_policy_builds` | 単独 |
| M17 | `_cell_from_document` の key 存在検査を削除 | `test_cell_document_round_trip_requires_policy_key_presence_to_match_format` | 単独 |
| M18 | Python 側 exact 述語から 2 本目 literal を削除 | `test_backoff_trace_contract_accepts_only_two_exact_cell_literals` | 単独 (PBS 側とは別 site) |
| M19 | PBS 側 literal を 1 文字変える | `test_two_layer_trace_literals_are_byte_identical` | **R11 の歯** |
| M20 | PBS の `colon_text -eq 10` を戻す | `test_pbs_marks_eleven_and_twelve_fields_extended` | 単独 |
| M21 | patch stack から C を削除 | `test_patch_stack_identity_is_exact_ordered_a_b_c` | 単独 |
| M22 | schema を v2 のままにする | `test_counterfactual_stack_artifacts_use_schema_v3` | **R9 の歯** |
| M23 | `_DEFINE_SPECS` から新 define を削除 | exact 集合 pin + 件数 pin + consumer | **冗長 gate (3 層)** |
| M24 | 図生成器の `expected_stack` を A+B+C だけにする | `test_plot_accepts_both_ab_and_abc_stacks` | **R14 の歯** |
| M25 | 等価変異 (C 内の comment 1 行の文言変更) | — (SURVIVED 期待の正例) | 正例 |

冗長 gate (M1 / M7 / M23) は単独変異の独立証拠に数えない (DW-M03)。

## 4. 単位分割と順序 (R15)

- **単位 A (先行)**: `patches/cicada-adaptive-counterfactual.patch`、
  `orchestrator/tests/test_dynamic_backoff_transitions.py`
- **単位 B (A の後、C と並列)**: `tools/pegasus/probes/t2187_adaptive_const_probe.py`、
  同 `.pbs`、`orchestrator/tests/test_t2187_adaptive_const_probe.py`
- **単位 C (A の後、B と並列)**: `orchestrator/campaign/condition_meaning_gate.py`、
  `orchestrator/campaign/screening_driver.py`、`orchestrator/tests/test_condition_meaning_gate.py`、
  `tools/plotting/plot_dynamic_backoff.py`、`orchestrator/tests/test_plot_dynamic_backoff.py`
- `patches/README.md` は親が最後に書く。
