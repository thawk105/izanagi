## 現状の構造

- [floor_pair_driver.py:2-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2) は、1 pair-sample を `candidate_1`、`candidate_2`、共通 `reference` の独立した 3 session と説明している。`SPEC_SCHEMA`、`WINDOW_SCHEMA`、`SUMMARY_SCHEMA` は v2、`PLAN_SCHEMA` は v1、`_ROLES` はこの 3 role 固定である。[floor_pair_driver.py:51-114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:51)

- spec 束縛では、`PairConfig.sides` を exact 2 件の `candidate_1/2` とし、両 side が同じ candidate artifact ID を使い、reference artifact ID とは異なることを検査する。[floor_pair_driver.py:189-200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:189) [floor_pair_driver.py:752-800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:752) `statistics` は reducer、stratum upper、closed strata、final combiner の 4 項だけで、reference 数と D の式は束縛していない。[floor_pair_driver.py:220-225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:220) [floor_pair_driver.py:871-904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:871)

- checkout 束縛は、spec、calibration、build receipt の HEAD tracked byte 一致、artifact の宣言 SHA-256 と実体の一致、calibration と各 cell の一致を検査する。[floor_pair_driver.py:968-1203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:968)

- `make_measurement_plan` は pair-sample 順を HMAC rank で決めた後、同じ pair-sample の 3 role も HMAC rank で並べ、role ごとに `PlannedSession` を 1 件作る。したがって 1 pair-sample は 3 session であり、reference は 1 sessionだけである。[floor_pair_driver.py:262-282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:262) [floor_pair_driver.py:1231-1305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1231)

- `_measure_with_runner` は caller から測定 callable を受けず、固定の `runner.measure_point` を直接 1 回呼ぶ。低水準関数が binary を 1 個しか受けないため、現状の `PlannedSession` 1 件は binary 1 個に対応する。[floor_pair_driver.py:1400-1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1400) [runner.py:1057-1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/calibrator/runner.py:1057)

- `_run_planned_session` は、その role の binary 1 個について SHA-256 と trace symbol を再検査し、`pre_probe → measure_point → post_probe` を実行して flat な session record を作る。[floor_pair_driver.py:1783-1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1783) `run_window` は 3 session を順に実行し、droppable failure が出た pair-sample の残り role を `not_run_sample_dropped` にする。[floor_pair_driver.py:1947-2071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1947)

- finalizer は raw header、3 session の順序・metadata・status・payload、失敗因果を plan から再導出し、3 status が全て `complete` の pair-sample だけを残す。[floor_pair_driver.py:2100-2428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2100) 残った標本では 3 role の median を取り、単一の reference median を両 gain の分母にして D を算出する。[floor_pair_driver.py:1349-1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1349) [floor_pair_driver.py:2554-2625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2554)

- `finalize_floor` は campaign 単位の exact な 5% 会計、空 stratum、`upper >= 1` を fail-closed に処理し、create-only summary へ `candidate_floor` と `NOT_PROVEN` を出す。[floor_pair_driver.py:2445-2722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2445)

## 変更プラン

- [floor_pair_driver.py:2-19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2) の説明を、「1 pair-sample は独立した 2 side session、各 side session は単一の pre/post probe 区間内で candidate と reference を各 1 回測る」に変更する。D は `gain_i = median(candidate_i) / median(reference_i) - 1`、`D = abs(gain_1 - gain_2)` と明記する。既存の `NOT_PROVEN` 8 項は残し、少なくとも「同一 session は driver の probe 区間であり、2 回の `measure_point` が同一 process または原子的実行であることは証明しない」「区間途中だけ存在した競合を前後 probe が必ず検出することは証明しない」を追加する。[floor_pair_driver.py:67-76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:67)

- [floor_pair_driver.py:51-114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:51) で次を変更する。

  - `SPEC_SCHEMA`: `floor-pair-spec/v2` → `floor-pair-spec/v3`
  - `PLAN_SCHEMA`: `floor-pair-plan/v1` → `floor-pair-plan/v2`
  - `WINDOW_SCHEMA`: `floor-pair-window/v2` → `floor-pair-window/v3`
  - `SUMMARY_SCHEMA`: `floor-pair-summary/v2` → `floor-pair-summary/v3`
  - JSON と JSONL の符号化方式は変わらないため、`WINDOW_FORMAT_ID` と `SUMMARY_FORMAT_ID` は v1 のままにする。
  - `_ROLES` を削除し、`_SIDE_IDS = ("candidate_1", "candidate_2")` と `_MEASUREMENT_ROLES = ("candidate", "reference")` に分ける。
  - `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE = 2` と、wire 上の exact 文字列 `DIFFERENCE_FORMULA = "D=abs((median(candidate_1)/median(reference_1)-1)-(median(candidate_2)/median(reference_2)-1))"` を定数化する。
  - `COMPETING_PROBE_ARGV`、status 集合、`MAX_DROPPED_FRACTION` は変更しない。

- [floor_pair_driver.py:220-305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:220) の dataclass を次の形にする。

  - `StatisticsConfig` に `reference_measurements_per_pair_sample: int` と `difference_formula: str` を追加する。
  - `PlannedMeasurement` を新設し、`measurement_id`、`role`、`artifact_id`、`order_index` を必須 field とする。
  - `PlannedSession` の `role` と `artifact_id` を `side_id` と `measurements: tuple[PlannedMeasurement, ...]` に置き換える。1 session の `measurements` は exact 2 件である。
  - `MeasurementRequest` と `MeasurementResult` の識別子を `session_id` から `measurement_id` に変更し、candidate/reference の結果を曖昧なく照合できるようにする。
  - `GainDifference` の出力 field は維持する。

- [floor_pair_driver.py:752-800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:752) の pair parser は、exact 2 side、side ID、同一 candidate artifact、reference との artifact 分離を維持し、ID 比較には `_SIDE_IDS` を使う。

- [floor_pair_driver.py:871-904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:871) の `_parse_statistics` は key 集合へ新しい 2 field を追加し、reference 数が exact int の `2`、D の式が `DIFFERENCE_FORMULA` と exact 一致しなければ `FloorPairSpecError` にする。fallback、別名、式 registry、spec 側の自由選択は設けない。

- [floor_pair_driver.py:1231-1305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1231) の `make_measurement_plan` は以下の canonical plan を作る。

  - pair-sample の HMAC 順は維持する。
  - 各 pair-sample の `candidate_1/2` side session 順を、用途ラベル `"side-session"` と side ID を含む HMAC rank で事前固定する。
  - 各 side session 内の `candidate/reference` 順も、用途ラベル `"in-session-measurement"`、side ID、measurement role を含む別の HMAC rank で固定する。
  - side session ID は `window.pair.sNNNNNN.side_id`、measurement ID はその末尾へ `.candidate` または `.reference` を付ける。
  - candidate measurement は当該 side の candidate artifact、reference measurement は pair の reference artifactへ固定する。
  - 各 pair-sample が exact 2 session、exact 4 measurement、うち reference が exact 2 件であることを構築時にも検査する。
  - nested dataclass 全体を plan hash の入力に含める。`_assert_plan_exact` による run/finalize 前の再生成比較は維持する。[floor_pair_driver.py:1308-1316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1308)

- [floor_pair_driver.py:1349-1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1349) の `compute_gain_difference` を、4 つの keyword-only 引数 `candidate_1_tps`、`reference_1_tps`、`candidate_2_tps`、`reference_2_tps` を取る関数へ変更する。candidate は有限非負、各 reference は有限正を要求し、二つの分母を別々に使う。upper statistic の閉じた registry は変更しない。

- [floor_pair_driver.py:1400-1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1400) の `_measure_with_runner` は識別子名だけ追随させ、`runner.measure_point` を直接呼ぶ唯一の production adapter のままにする。`measure_fn`、adapter object、spec field、dataclass field、CLI optionなど、測定実体を差し替える seam は追加しない。

- [floor_pair_driver.py:1604-1716](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1604) の payload 検査は `_MEASUREMENT_ROLES` を受け、candidate の有限非負と reference の有限正を個々の nested measurement に適用する。raw record が名乗る role ではなく、canonical plan の `PlannedMeasurement.role` を権威とする。

- [floor_pair_driver.py:1719-1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1719) の record 生成と `_run_planned_session` を作り直す。

  - session record は flat な `role`、`artifact_id`、throughput 群、`binary_sha256` を持たず、`side_id` と plan 順の nested `measurements` を持つ。各 nested record は measurement ID、role、artifact ID、order index、binary SHA-256、throughput、returncode、observation、timestamp、error を保持する。
  - candidate/reference の両 binary を canonical plan から解決し、各々について宣言 SHA-256 と trace symbol 不在を検査する。
  - pre-probe を 1 回実行し、clear の場合だけ nested plan 順に `_measure_with_runner` を 2 回直接呼び、最後に post-probe を 1 回実行する。
  - 1 回目の測定が失敗、不完備、または protocol violation なら 2 回目を受理目的で続行せず、未実行 suffix を raw payload 上で明示し、post-probe は実行する。
  - session が `complete` になるのは両 measurement が exact 完備で、両 probe が clear の場合だけとする。
  - `not_run_sample_dropped` と `not_run_after_fail_closed` は side session 単位にする。nested measurement の欠落を complete と解釈しない。

- [floor_pair_driver.py:1947-2071](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:1947) の `run_window` は public signature を変えず、1 pair-sample の 2 side session を順に実行する。どちらか一方が droppable なら pair-sample 全体を 1 件として落とし、未実行の他 side を `not_run_sample_dropped` にする。header には nested `planned_sessions` に加え、`planned_measurement_count`、`measurements_per_session=2`、`reference_measurements_per_pair_sample=2`、`difference_formula` を入れる。probe callable と clock callable の既存 seam は維持するが、measurement callable は追加しない。

- [floor_pair_driver.py:2100-2428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2100) の artifact validator と因果 audit は、次を raw payload から再導出する。

  - session 順、side ID、nested measurement 順・ID・role・artifact・SHA-256 が canonical plan と exact 一致する。
  - attempted measurement は plan の prefix であり、complete session は exact 2 件を持つ。欠落、追加、重複、順序交換は拒否する。
  - pair-sample 完了条件は二つの side session がともに complete であること。
  - droppable cause 前の side は complete を許し、cause 後の side は `not_run_sample_dropped` だけを許す。
  - terminal の planned/recorded session 数は pair-sample あたり 2 として再計算し、measurement 数も header と照合する。

- [floor_pair_driver.py:2445-2625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2445) の status、drop 会計、導出を nested session へ合わせる。5% の分母は従来どおり pair-sample 数であり、session 数や measurement 数へ変えない。`_derive_strata` は side ID ごとに candidate/reference median を取り、二つの side-specific reference を keyword 引数で `compute_gain_difference` へ渡す。summary の標本内訳は、例えば `session_medians = {"candidate_1": {"candidate": c1, "reference": r1}, "candidate_2": {"candidate": c2, "reference": r2}}` とし、どの分母を使ったかを残す。

- [floor_pair_driver.py:2628-2722](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2628) の summary に、凍結した reference 数と D の式を含む `statistics` を出す。`candidate_floor`、`upper`、status 語彙、`upper >= 1` の非生成、create-only 書き込み、全 `NOT_PROVEN` の出力は維持する。CLI の mode と引数は変えない。[floor_pair_driver.py:2740-2771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/campaign/floor_pair_driver.py:2740)

- この設計は driver 自身に新しい `subprocess` 起動点を増やさず、既存の `_git_head`、`_git_show_head`、`_run_probe` の各 1 点を維持する。また `use_perf=False` の predicate も変えないため、固定台帳側の編集は不要とする。

## (P1) への評価

- **(P1-a): 採る。** scope 内の低水準 API は binary 1 個しか受けないため、1 side session を「1 pre-probe、candidate/reference の固定された 2 回の直接 `measure_point` 呼び出し、1 post-probe」からなる区間として実装する。`capture_measure_point` も binary 1 個しか受けず、これへ替えても一呼び出し二 binary にはならない。pair-sample 全体では独立した side session が 2 件となる。

- **(P1-b): 採る。** reference measurement point は pair-sample あたり exact 2 件、各 side session に 1 件とする。同じ reference artifact を使うが、raw 値 `r1` と `r2` は別測定である。`D = abs((c1/r1-1) - (c2/r2-1))` により、各 gain の候補と参照が同じ probe 区間に収まり、走行間ドリフトを別 session の分母へ持ち越さない。

- **(P1-c): 採る。** session 内の candidate/reference 順を HMAC rank で事前固定する。加えて、D1641 の「独立した 2 session の順序も事前に無作為化」を失わないため、`candidate_1/2` side session の順にも別 domain label の HMAC rank を適用する。両階層を plan hash と raw header に束縛する。

- **(P1-d): 対案がある。** `SPEC_SCHEMA v3` と `SUMMARY_SCHEMA v3` は採るが、それだけでは旧 plan と旧 raw window が新しい意味で読めてしまう。nested session plan の構造変更に合わせ `PLAN_SCHEMA v2`、raw record 構造変更に合わせ `WINDOW_SCHEMA v3` も上げる。encoding の `WINDOW_FORMAT_ID` と `SUMMARY_FORMAT_ID`、failure policy、randomization algorithm ID は意味が変わらないため据え置く。

- **(P1-e): 採る。** `statistics.reference_measurements_per_pair_sample = 2` と `statistics.difference_formula = DIFFERENCE_FORMULA` を必須 exact field にし、loader で定数一致を要求する。さらに canonical plan の件数検査、window header、summary へ同じ値を投影し、spec hashだけに隠れた凍結にしない。

## 壊れるテストの棚卸し

- 共通 fixture では、[_valid_document:185-294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:185) に統計 2 fieldを追加し、[PUBLIC_DATACLASSES:420-443](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:420) に `PlannedMeasurement` を加える。[REQUIRED_FIELD_PATHS:469-526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:469) へ凍結 2 field を加え、欠落時の拒否を既存 parametrized test に引き継がせる。

- role 値を呼び出し順へ割り当てる [_run_campaign_shape:1386-1466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1386)、[_run_production:1884-1926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1884)、[_run_multi_pair_sample_production:1929-1959](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1929) は作り直す。flatten した canonical `(session, measurement)` 順と実際の binary pathを照合し、値は `(side_id, measurement_role)` で与える。引き続き `F.runner.measure_point` の test monkeypatchを使い、production 引数へ callable を増やさない。

- [test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1002) は**作り直す**。4 pair-sampleから 8 side session、16 nested measurement が生成される golden order とし、各 sample の side set、各 session の role set、連番、ID 一意性、seed 変更時の順序変更を検査する。

- [test_gain_difference_uses_one_common_reference_and_registry_is_closed:1052](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1052) は**作り直す**。名前も「two side-specific references」に変え、`r1 != r2` の数値例で四入力の式を検査する。upper statistic registry の閉包検査は同じテスト内に残す。

- [test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks:1080](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1080) は `MeasurementRequest.measurement_id` への追随だけ**作り直す**。runner 引数、sink、固定 `require_all_reps` 等の検査内容は維持する。

- [test_run_window_orders_pre_measure_post_and_records_all_sessions:1469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1469) は**作り直す**。各 side session が `probe → measure → measure → probe`、1 sample が 2 session、raw が header、2 session、terminal になることを検査する。両 `measure` の binary path と順序を plan に照合する。

- [test_pre_probe_drop_closes_sample_and_continues_next_sample:1514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1514) と [test_measure_exception_runs_post_probe_drops_remaining_roles_and_continues:1573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1573) は**作り直す**。失敗 side session と未実行 side session の 2 record、失敗後も post-probe が来ること、次 sample の 4 measurement が実行されることを検査する。

- [test_droppable_probe_statuses_run_and_finalize:1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1645) は**作り直す**。落ちた sample を `expected_status + not_run_sample_dropped`、残る 20 sample を 40 complete side session として検査する。

- [test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure:1693](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1693) は**作り直す**。candidate と reference の各 binary を対象に parametrized 化し、いずれの trace 混入も probe・測定前または少なくとも測定前に fatal となり、残り side session が未実行になることを検査する。

- [test_production_adapter_artifact_finalizes_from_raw_medians:1962](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:1962) は**作り直す**。summary v3、二つの nested side median、reference 数、D 式、異なる `r1/r2` から再計算された gain と D を検査する。

- [test_mutation_21_max_finite_even_medians_generate_zero_upper:2013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2013) と [test_mutation_22_large_exact_int_is_total_in_run_and_artifact_rederivation:2050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2050) は**作り直す**。`_ROLES` を使わず 4 measurement 値を指定し、raw status は 2 side session 分に更新する。

- [test_finalizer_revalidates_complete_header_and_terminal_contract:2098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2098) は**作り直す**。新しい measurement count、reference count、D 式の改変も拒否ケースに加える。

- [test_mutation_18_recorded_multiple_pair_sample_order_must_match_plan:2120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2120) は**作り直す**。8 session の順序を照合し、session 交換に加えて nested candidate/reference の交換も拒否する。

- [test_mutation_07_status_only_rewrite_is_rejected_by_payload_derivation:2136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2136) は fixture 入力を四測定形へ**作り直す**。status-only 改変を payload 再導出で拒否する性質は維持する。

- [test_campaign_drop_fraction_uses_exact_campaign_boundary_and_pair_sum:2170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2170)、[test_campaign_threshold_is_local_to_each_window_not_global_sum:2252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2252)、[test_exact_five_percent_with_empty_stratum_is_not_generated:2394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2394)、[test_threshold_status_precedes_empty_stratum_status:2415](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2415) は、共通 helper の変更後は**そのまま通る**構成にする。これらは session 数ではなく pair-sample 数による 5% 境界を検査している。

- [test_campaign_boundary_summary_causality_and_derivation_are_exact:2194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2194) は**作り直す**。落ちた sample ごとの raw summary record 数を 3 から 2 にし、cause ID を role suffix ではなく side session ID で照合する。

- [test_dropped_summary_includes_complete_role_before_failure:2274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2274) は**作り直し、改名する**。第 1 side session の candidate/reference がともに complete、その後の第 2 side session 内で失敗した場合、dropped summary が `complete side + failed side` の 2 record を含むことを検査する。

- [test_mutation_11_post_probe_drop_excludes_high_difference_sample:2323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2323) は**作り直す**。二つの side-specific reference で高 D を作り、第 2 side session の post-probe failure により sample 全体が導出から除外されることを検査する。

- [test_not_run_sample_dropped_without_prior_failure_is_rejected:2429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2429) は**作り直す**。flat throughput field の消去ではなく nested `measurements` を non-run 形に改変し、先行 cause がないことを拒否させる。

- [test_drop_selection_is_invariant_under_complete_throughput_changes:2467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2467) は四測定値の fixtureへ**作り直す**。drop 選択が値に依存しない性質は維持する。

- [test_candidate_zero_is_complete_and_contributes_gain_minus_one:2506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2506) は**作り直す**。片 side の candidate を 0、同じ side の reference を正にし、nested median と gain を検査する。

- [test_reference_zero_and_negative_values_are_fatal_protocol_violations:2548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2548) は**作り直す**。各 side の reference zero と candidate negative を `(side_id, role)` で指定し、internal order に依存せず fatal となることを検査する。

- [test_outside_window_is_fatal_and_not_counted_as_dropped:2589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2589) と [test_nonfinite_measurement_is_recorded_incomplete_not_serialized_as_nan:2612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2612) は**作り直す**。status 列を 2 side session 分にし、非有限値は nested measurement 内で `null` へ正規化されることを検査する。

- [test_mutation_08_upper_at_or_above_one_is_preserved_and_not_clamped:2644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2644) は四測定式へ**作り直す**。二つの reference を使って `D >= 1` を作り、非 clamp を維持する。

- [test_mutations_09_and_13_forged_production_named_high_measure_is_rejected:2665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2665) は**そのまま通る**形を維持する。これは `measure_fn` injection seam が存在しないことを直接守る中核テストである。

- [test_finalizer_rejects_duplicate_session_id_even_when_set_matches:2689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2689) は**作り直す**。2 件へ複製 1 件を足すため terminal の forged count は 3 とし、nested measurement ID の重複拒否ケースも追加する。

- [test_summary_is_exclusive_create:2711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2711) は共通 production helper 更新後は**そのまま通る**。create-only の性質は session 形に依存しない。

- [test_cli_execute_window_selects_the_named_production_adapter:2728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b4-paired-session-driver/orchestrator/tests/test_floor_pair_driver.py:2728) は fake result の `session_count` を 2 にして**作り直す**。`measure_fn` が kwargs にないこと、production probe と clock が選ばれることは維持する。

- **消すテストは 0 件。** 「単一共通 reference」や「3 role」の旧主張は、それぞれ二つの side-specific reference、2 side session の検査へ改名して作り直すため、守っていた閉包、順序、失敗因果、raw 再導出の各性質を失わない。

## 規律 2 の攻撃面

- **測定実体の差し替え:** 2 binary を回す loop に `measure_fn` を渡せるようにすると、両側へ同値を返して D を 0 にできる。`run_window` と `_run_planned_session` の signature に測定 callable を置かず、固定 `_measure_with_runner → runner.measure_point` の直接経路だけにする。既存の forged `measure_fn` 拒否テストを残し、各呼び出しの binary path が canonical plan と一致するテストを追加する。

- **reference の共有または省略:** 旧共通 reference を再利用したり、片 side の reference を省くと比が session 境界を跨ぐ。spec の exact 数 2、plan の exact 2 reference、各 side session の exact candidate/reference set、raw nested payload、summary の四 median を全段で照合する。

- **role と artifact の交換:** raw 側の自己申告 role を信用すると、candidate binary を reference として受理できる。role→artifact 対応は canonical plan からのみ導出し、両 binary の宣言 SHA-256 と trace symbol を測定前に検査し、raw の role、artifact ID、SHA-256 を plan と exact 比較する。

- **probe 区間の分割:** candidate と reference ごとに probe 対を作ると、再び別 session になる。side session record に pre/post を各 1 件だけ持たせ、その間の nested measurement が exact 2 件である構造と、`probe → measure → measure → probe` の順序テストで固定する。

- **片側だけの complete 化:** 1 measurement の欠落、例外、非有限値を session complete と扱うと D を都合よく小さくできる。attempted measurement は canonical prefix、complete は exact 2 件、pair-sample complete は exact 2 side session とし、status は raw payloadから再導出する。

- **HMAC domain の混同:** side session 順と session 内順が同じ label や不十分な field を使うと、意図しない相関や plan 衝突が生じる。二つの用途ラベル、side ID、spec schema、spec hash、window、pair、sample indexを rank 入力へ入れ、nested plan 全体を plan hash に含める。

- **D 式の drift:** parser が任意式 ID を受けたり、実装が再び単一分母を使うと凍結が空文化する。wire formula は exact 定数一致だけを受理し、計算関数は四つの keyword-only 値を取らせ、`r1 != r2` のテストで単一分母への変異を赤にする。式の selectable registry は作らない。

- **drop 会計の分母変更:** record が 3 role から 2 session、4 measurement へ変わる際、session 数や measurement 数を分母にすると 5% gate が緩む。drop key を従来どおり `(window_id, pair_id, sample_index)` に固定し、campaign の planned sample 数で `Fraction` を計算する。59 件境界と複数 pair/window のテストを維持する。

- **旧 schema の意味混入:** 同じ schema で record 構造と `candidate_floor` の意味だけ変えると、旧成果物を新成果物として読める。spec、plan、window、summary の意味が変わる各 schema を上げ、header と finalizer の exact 再検査で版の混在を拒否する。

- **D=0 自体の禁止はしない:** 実測で同じ gain になることは正当なので、0 を下限で丸めたり拒否したりしない。塞ぐ対象は D=0 へ偽装できる測定 seam、reference 省略、binary 交換、partial payload であり、正当な 0 は従来どおり受理する。

## 総括

- 1 pair-sample を、candidate/reference を同じ probe 区間で測る 2 side sessionへ変更する。
- reference は exact 2 件、D は二つの side-specific reference を使う式として spec に凍結する。
- production 測定 callable の injection seam は追加せず、固定 runner 経路を維持する。
- spec、plan、window、summary の意味変更に対応して各 schema を上げ、raw から全構造を再導出する。
- 書き込みと pytest 実走は行っておらず、本プランは指定資料に対する静的検査結果である。