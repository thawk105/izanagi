## 依頼 1

### 12 行と現行 driver の対応

|D1641 の凍結行|判定|現物との対応|
|---|---|---|
|1. 対象 driver と軸|**不一致**|`FloorPairSpec` に driver kind / axis field がない (`floor_pair_driver.py:220-235`)。top-level schema にも存在せず (`:1105-1111`)、`protocol` 等は unknown field として拒否される (`test_floor_pair_driver.py:539-556`)。cell/artifact 名へ人手で埋め込めるだけで、選定結果との束縛はない。親が数えた「他 10 行」は、この行を落としており、欠測以外は本来 11 行ある。|
|2. 実行 site = gen_S|**一致**（正しい frozen spec が前提）|`environment.site` を受理 (`:602-618`)し、実行時に evidence 付き live site と exact 比較する (`:1437-1453`)。parser 自体は `OTHER` も受理するため、D1641 の値は spec 起草時に `PEGASUS_COMPUTE` へ固定する必要がある。|
|3. env_tag の機械導出|**一致**|`_machine_env_tag_for_site` が resolver から導出 (`:1404-1434`)し、spec 値と live 値を照合する (`:1448-1452`)。|
|4. 校正済み PerfConfig|**不一致**（部分実装）|校正 artifact は hash / HEAD 束縛され、accepted、records、threads、workload、clocks を照合する (`:994-1060`)。一方、`extime`、`reps`、`ycsb_max_ope` は spec から自由に受ける (`:685-705`)だけで calibrator 出力との照合がない。calibrator の `CalibrationResult` 自体にもこれらの field はない (`orchestrator/calibrator/model.py:195-210`)。|
|5. 3 workload × contention セル集合|**一致**（凍結 spec のレビューが前提）|cells と perf_config を strict parse (`floor_pair_driver.py:685-725`)し、全 pair / window / closed stratum の参照閉包を検査する (`:932-960`)。ただし「3 workload」や §5 の集合との一致は driver が検査しない。|
|6. 共通参照点と対照対|**不一致**（D1641 の逐語解釈）|候補 2 側の artifact byte identity は強制される (`:741-767`)。3 role は sample ごとに連続し、role 順を HMAC で無作為化する (`:1203-1253`)。しかし candidate 2 件と reference はいずれも別 `PlannedSession` であり、「参照点は対ごとに同一セッション内で測る」を満たさない。連続していることは同一セッションではない。|
|7. probe → 測定 → probe → journal|**不一致**（部分実装）|前後 probe と測定の順は `:1697-1750`、session record は `:1751-1773`。create-only JSONL は journal 相当の記録になるが、D1641 が名指す s8b floor campaign journal との統合はない。親 brief 自身も `s1-brief.md:48-49` でこれを scope 外としている。|
|8. n=59、2 campaign、24h 分離|**一致**（値の凍結に依存）|`sample_count`、campaign ID、窓を表現でき、campaign ID 一意と窓非重複を検査する (`floor_pair_driver.py:779-835`)。ただし n=59、exact 2 campaign、24h gap は強制しない。同一 campaign の値は `(window,pair)` stratum に留まり (`:2062-2119`)、最後に stratum 上限を最大合成する。独立機会数という field はなく、独立性自体を証明しない (`:14`, `:66`)。|
|9. 標本最大値の片側許容限界|**一致**|許す関数 ID を閉じ (`:847-880`)、`sample_max/v1` を適用する (`:1309-1340`)。|
|10. 全セル × 2 窓の最大|**一致**|`closed_strata` と全 planned `(window,pair)` を exact 一致させ (`:951-960`)、各 stratum と全 stratum の最大を取る (`:2105-2122`)。|
|11. create-only JSON と名前の 5 要素|**不一致**（機械保証なし）|create-only は `_ExclusiveWriter` (`:1456-1484`) で満たす。だが `artifact_relpath` は任意の canonical relative path (`:779-827`)、summary も同様 (`:905-919`)。env_tag・protocol・threads・workload・campaign の含有検査がなく、protocol field 自体もない。正しい spec 値を人手で凍結すれば実成果物名は適合できるが、driver の保証にはならない。|
|12. 欠測規則と upper ≥ 1|**不一致**|upper ≥ 1 を丸めない部分は一致 (`:2158-2165`)。欠測は旧 policy だけを受理 (`:56`, `:883-902`)、最初の失敗後に全 window を停止 (`:1834-1853`)、1 件でも非 complete なら全体を不採用 (`:1997-2004`)する。ここが S-C の明確な変更対象。|

したがって「唯一の実差は欠測規則」は**不一致**である。S-C として即実装できる差は欠測規則だが、少なくとも行 1、4、6、7、11 には別の機械保証不足がある。特に行 6 は正しい spec を書くだけでは解消しない。

### provisional 裁定

- **P1:** 条件付きで採用する。ただし「理由だけが古い」は不正確で、D1641 第 4 項の事実記述と「新設する」という実行指示の双方が裁定日時点で古かった。追記 fragment には、既存 driver が 2026-09-02 に存在したことと、本 wave が新設でなく差分適合であることを明記する。測定前に適合を完了させる、という認可境界は維持できるので再裁定までは不要。
- **P2:** `base` 固定では全域規則にならない。`sort` と `trigger` だけが合格した場合に不合格の `base` を選んでしまう。合格集合から固定優先順 `base → sort → trigger` の最初を選ぶ、と修正する。
- **P3:** **旧 policy は残さず、新 policy 1 値だけを受理する。** 推奨 ID は `d1641-drop-and-count-max-5pct/v1`。旧 policy を許すことは安全側の過剰棄却ではあるが、D1641 が凍結した欠測手続きと campaign 間の比較可能性を spec 選択で変更できるため、裁定からの逸脱に当たる。
- **P4:** 採用する。「標本」は `(window_id, pair_id, sample_index)` の 3 role 組。`make_measurement_plan` は sample を外側、role を内側で列挙するため 3 role は連続する (`:1218-1253`)。1 role が失敗した後の残り role は `not_run_after_fail_closed`、`error="sample_dropped"` とし、次 sample は実行する。
- 分母は window 内の unique planned sample 数、すなわち `window.sample_count * len(window.pair_ids)`。pair 合算でよい。exact 5% は採用、超過だけ不採用なので `Fraction(dropped, planned) > Fraction(1, 20)`、同値な整数式は `dropped * 20 > planned` で正しい。
- `binary_binding_failed` は測定値を持たない binding 欠測、`outside_window` は凍結時間窓違反による欠測なので、いずれも dropped sample に数える。`not_run_after_fail_closed` は同じ sample を重複加算しない。window 開始前の live environment mismatch は campaign 自体を開始拒否する現行 fail-closed を維持する。
- 残り role を走らせる案は、採用不能と確定した sample に追加測定を行うだけで、完全性を回復しない。予定外実行面も増えるため不採用とする。

### 値を小さくする除外の禁止

現行経路は、probe 状態、例外、完全性だけから session status を作る (`_run_planned_session`:1640-1774)。`_measurement_complete` は reps、returncode、timestamp、有限正 throughput を検査する (`:1547-1601`)。有限正の検査は値を見るが、D の大小による選別ではなく、D1641 が明記する非有限・欠測の validity 判定である。

S-C では、sample を落とす判断を `status != "complete"` だけから作り、`compute_gain_difference` より前に確定させること。`_status_from_records` と `_derive_strata` が difference、median、最大値を見て dropped 判定を変える経路を作らなければ、driver 内に低い値だけを残す選択経路はない。

### summary consumer と schema

次の静的検索で production consumer は 0 件だった。

`git grep -n -E 'floor-pair-summary/v1|floor-pair-summary-json/v1|SUMMARY_SCHEMA' -- '*.py' ':!orchestrator/campaign/floor_pair_driver.py' ':!orchestrator/tests/test_floor_pair_driver.py'`

test 側には JSON を読む箇所が `test_floor_pair_driver.py:1631` と `:1759` にあるが、現状 schema 値は検査していない。summary の形は変わるため `SUMMARY_SCHEMA` は `floor-pair-summary/v2` へ上げる。さらに failure policy の input shape と window terminal shape も変わるため、`SPEC_SCHEMA` と `WINDOW_SCHEMA` も v2 にする。plan の wire shape と JSON serialization format ID は変わらないので `PLAN_SCHEMA`、`WINDOW_FORMAT_ID`、`SUMMARY_FORMAT_ID` は据え置く。

### 実アンカー表の検査

|親のアンカー|判定|
|---|---|
|production の主要アンカー|一致。`:56`, `:205`, `:883`, `:1619`, `:1640`, `:1777`, `:1997`, `:2055`, `:2126`, `:51`, `:62` は現物どおり。|
|failed 分岐 `:1851-1863`|不一致。状態分岐は `:1834-1850`、record write は `:1851-1852`、terminal は `:1853-1862`。|
|`_ExclusiveWriter :1462`|不一致。class 定義は `:1456`、`:1462` は `os.open` 実行行。|
|test アンカー|一致。`:431`, `:505`, `:860`, `:1287`, `:1323`, `:1617`, `:1693`, `:1743`。|
|§5 対象 item `:171-195`|不一致。対象 driver の item は `:171-191`。`:192-199` は赤 precursor の item。|
|配線 probe `_DRIVER_MODULES :63`|不一致。dict は `p3_b4_wiring_probe.py:70-74`。`:63` は別の module path entry。|
|probe の他アンカー|一致。`:48`, `:1796`, `:2022`。|
|§5 consumer と dispatch|一致。`p3_b4_admission_record.py:77`, `:114`、`dispatch_compute.py:154`, `:1318`, `:1625`。|

なお source 上は 42 個の `def test_...` があり、既存 mutation ledger は parameter 展開後 140 tests を記録している。親 brief の「51 test」はどちらの数え方とも一致しない。

## 依頼 2

### production 変更面と規模

変更対象は次のとおり。

- 定数: `SPEC_SCHEMA:48`、`WINDOW_SCHEMA:50`、`SUMMARY_SCHEMA:51`、`FAILURE_POLICY_ID:56`、`NOT_PROVEN:62-69`。`MAX_DROPPED_FRACTION = Fraction(1, 20)` と wire 値定数を追加。
- dataclass: `FailurePolicy:205-210`。
- 関数: `_parse_failure_policy:883-902`、`_not_run_record:1619-1637`、`run_window:1777-1870`、`_validate_window_artifact:1899-1985`、`_status_from_records:1997-2052`、`_derive_strata:2055-2123`、`finalize_floor:2126-2196`。
- 新規 helper: sample key、dropped sample 集計、campaign drop report、summary 用 dropped record 射影の 3、4 関数。

推測による見積もりは production が追加 95〜125 行、変更 25〜40 行、削除 10〜20 行。test は追加 130〜180 行、変更 30〜50 行、削除 15〜30 行。合計 net はおよそ +180〜+255 行。

### 赤になる既存 test

fixture を同時更新した後にも直接赤になる既存 node は 3 件。

1. `test_mutation_11_hmac_rank_has_multiple_pair_sample_golden_order` (`:949`): spec field/schema の変更で `spec_sha256` が変わり、HMAC golden 順も変わる。HMAC アルゴリズムと sample 内 3 role の連続性は維持して期待列だけ更新する。
2. `test_measure_exception_still_runs_post_probe_and_closes_remaining_plan` (`:1323`): window 全体停止という期待が supersede される。
3. `test_mutation_07_one_noncomplete_session_makes_whole_floor_missing` (`:1693`): 1 欠測即不採用という pin が D1641 により supersede される。

`_valid_document:185-293` に新しい failure policy field を足さず production parser だけ変更すると、valid fixture を通る 40 collected nodes が早期 `FloorPairSpecError` で赤になる。該当 group は以下。

- `test_tracked_calibration_declared_sha_mismatch...`
- `test_mutation_04...` 3 cases、`test_mutation_14...`、`test_mutation_15...`、`test_calibration_none...`
- `test_build_receipt_uses...`、`test_build_receipt_binary_sha_and_trace...` 2 cases
- `test_mutation_19...`、`test_mutation_11...`、`test_mutation_12...`
- `test_login_and_suspect...` 2 cases、`test_mutation_17...`、`test_live_site...`
- `test_run_window...`、`test_measure_exception...`、`test_mutation_05...`、`test_mutation_06...`
- `test_mutation_10...`、`test_runtime_head...`、`test_output_open...`
- `test_production_adapter_artifact_finalizes...`
- `test_finalizer_revalidates...` 6 cases、`test_mutation_18...`、`test_mutation_07...`
- `test_nonfinite_measurement...`、`test_mutation_08...`、`test_mutations_09_and_13...`
- `test_finalizer_rejects_duplicate...`、`test_summary_is_exclusive_create`
- `test_cli_execute_window...`、`test_validate_only...`

これは独立した仕様赤ではなく、fixture 更新漏れによる連鎖赤である。

特記された既存 node の扱いは以下。

- `:505 test_every_schema_field_is_required`: 現状のままでも他 field 欠落で例外になるため赤にはならないが、`failure_policy.max_dropped_fraction` case を追加しないと新 field の required 性を pin できない。
- `:431` docstring test: `NOT_PROVEN` と module docstring の両方へ同じ文言を足せば変更なしで緑。supersede しない。
- `:1617` finalize test: 現状の assertion は subset なので緑のままだが、summary v2、zero dropped、campaign counts を追加確認する。
- `:1655` terminal test: complete campaign は引き続き緑。terminal の dropped count 改変 case を追加する。
- `:1715` nonfinite test: status は維持される。sample-local skip と dropped count の assertion を追加してよい。

supersede してよい pin は、旧 policy ID、最初の失敗後に window 全体を `not_run` にする挙動、1 欠測で floor 全体を消す挙動、旧 summary/window/spec schema version、spec hash 変更前の HMAC golden 列だけ。

supersede してはならない pin は、create-only (`:1472`, `:1515`, `:1810`)、HEAD/blob/source 三者束縛 (`:571`, `:873`, `:1500`)、固定 probe argv (`:860`)、upper ≥ 1 の非丸め (`:1743`)、live site/env 判定 (`:1116-1232`, `:1406`)、production adapter の非差込性 (`:1764`)、plan/session 順と ID/count の exact 検証 (`:1677`, `:1788`)。

### test の追加・更新数

既存 6 test function を更新する。

- `:505`: 新 policy field の required 性。
- `:949`: 新 spec hash に対する golden 順。ただし sample 内連続性も明示 assertion。
- `:1323`: 失敗 sample の残り role だけを飛ばし、次 sample が走ること。
- `:1617`: summary v2、zero-drop campaign report。
- `:1655`: forged terminal dropped count を reject する parameter。
- `:1693`: 1/20 exact 境界で生成し、dropped 全 role を summary へ載せる正例へ置換。

新規 3 test function、parameter 展開後 4 node を追加する。

1. legacy policy ID と `"max_dropped_fraction" != "1/20"` の 2 負例。正例は全 valid fixture が担う。
2. 2/20 dropped で `not_generated_dropped_fraction_exceeded`、upper/floor が null になる負例。正例は更新後 `:1693` の 1/20。
3. campaign 全体は 5% 以下だが、ある closed stratum の残存 sample が 0 のとき `not_generated_empty_stratum` となる負例。正例は `:1617` の全 stratum 非空。

これで、parser、sample-local 継続、5% 境界、empty stratum、terminal integrity、summary audit の各面に正負の対ができる。

S-C 単独なら 1 実装子、所有 2 file、1 commit、fix 3 巡以内に収まる。行 1、4、6、7、11 の追加適合まで同じ commit に入れるなら収まらず、scope を分けるべきである。

## 依頼 3

### 1. policy と parser

1. `floor_pair_driver.py:20-35` に `from fractions import Fraction` を追加する。
2. `:48-56` を次へ変更する。

   - `SPEC_SCHEMA = "floor-pair-spec/v2"`
   - `WINDOW_SCHEMA = "floor-pair-window/v2"`
   - `SUMMARY_SCHEMA = "floor-pair-summary/v2"`
   - `FAILURE_POLICY_ID = "d1641-drop-and-count-max-5pct/v1"`
   - `MAX_DROPPED_FRACTION = Fraction(1, 20)`
   - `MAX_DROPPED_FRACTION_WIRE = "1/20"`

3. `FailurePolicy:205-210` に `max_dropped_fraction: Fraction` を必須 field として追加する。
4. `_parse_failure_policy:883-902` の exact keys を `policy`, `retry_count`, `require_all_reps`, `max_dropped_fraction` にする。JSON 値は exact string `"1/20"` だけを受け、内部値には `MAX_DROPPED_FRACTION` を格納する。
5. legacy ID と新旧両受理はしない。`retry_count=0` と `require_all_reps=true` も現状どおり固定する。failure semantics に spec 自由度を一つも残さない。時間窓、output path、probe timeout のような outcome 非依存の運用値は既存 spec 自由度のままでよい。

### 2. run_window

1. `make_measurement_plan:1203-1253` は変更しない。sample ごとに 3 role が連続する現行構造を利用するが、実装は連続性だけに依存せず、`(window_id,pair_id,sample_index)` key の set で dropped 状態を持つ。
2. `_not_run_record:1619-1637` は status を `not_run_after_fail_closed` のまま維持し、`error` を exact `"sample_dropped"` にする。
3. `run_window:1834-1852` の window-global `failed` を `dropped_sample_keys` へ置換する。

   - key が既に dropped なら `_not_run_record`。
   - 未 drop なら `_run_planned_session`。
   - status が non-complete ならその key を set に追加。
   - key が変わった次 sample は通常実行。

4. terminal (`:1853-1862`) は artifact の記録完了を示す `status="complete"` とし、次を exact field として追加する。

   - `planned_sample_count`
   - `dropped_sample_count`
   - `complete_sample_count`

   `WindowRunResult.status` も artifact が terminal まで閉じた場合は `"complete"`。欠測の意味は count で表す。
5. `_validate_window_artifact:1899-1985` で session records から unique dropped keys を再計算し、terminal の 3 count と exact 一致させる。terminal 自己申告だけを信用しない。

### 3. finalize と summary

1. `_status_from_records:1997-2052` は non-complete record を即全体 failure にしない。complete record だけ現行の reps、finite、returncode、observation、timestamp 検査を通し、non-complete record の throughput を drop 判定に使わない。
2. 新 helper で plan の sample keys と records を照合し、次を作る。

   - window/campaign ごとの `planned_sample_count`
   - unique `dropped_sample_count`
   - exact fraction の numerator / denominator
   - `max_dropped_fraction = "1/20"`
   - `admissible = Fraction(dropped, planned) <= Fraction(1, 20)`

3. どれかの campaign が超過した場合の status は `not_generated_dropped_fraction_exceeded`。`upper` と `candidate_floor` は null。
4. `_derive_strata:2055-2123` は 3 role のどれかが non-complete の sample 全体を、median や D を計算する前に skip する。残った sample のみを `strata_values` へ入れる。
5. 5% 以下でも残存 sample が 0 の closed stratum があれば、status は `not_generated_empty_stratum`。空列を `max()` へ渡さない。threshold 超過と empty stratum が同時なら、D1641 の直接条件である `not_generated_dropped_fraction_exceeded` を優先する。
6. `finalize_floor:2134-2183` の summary に次を追加する。

   - `campaigns`: 各 window の campaign ID、planned、dropped、fraction、threshold、admissible。
   - `dropped_sample_count`: 全 campaign の unique dropped sample 合計。
   - `dropped_record_count`: `dropped` の件数。
   - `dropped`: dropped sample に属する 3 role 全件の `{window_id,pair_id,sample_index,role,status,error}`。

   失敗より前に complete だった role も、sample 全体が捨てられた事実を示すため `dropped` に含める。その record の `status="complete"`、`error=null` も保持する。

### 4. NOT_PROVEN

module docstring `:9-16` と `NOT_PROVEN:62-69` に同一の 1 行を追加する。

> 落ちた標本による残存標本数の減少を許容限界の被覆確率へ補正せず、残存標本で 95% 被覆を保つことを証明しない。

これは n=59 から欠測を許す以上必要な限定であり、欠測を隠す記述にしない。

### 5. 変異事前登録候補

|変異の意味|殺す期待 node|
|---|---|
|legacy policy ID も受理する|新規 policy negative test|
|`max_dropped_fraction` の exact `"1/20"` 検査を外す|新規 policy negative test|
|失敗後も同じ sample の残り role を実行する|更新 `test_measure_exception...`|
|sample-local set を window-global failed flag に戻す|更新 `test_measure_exception...`|
|3 non-complete role を 3 dropped samples と数える|更新 `test_mutation_07...`|
|比較を `>` から `>=` にして exact 5% も落とす|更新 `test_mutation_07...`|
|5% 超過 gate を外す|新規 above-five-percent test|
|dropped sample を `_derive_strata` に混ぜる|更新 `test_mutation_07...`|
|empty stratum gate を外す|新規 empty-stratum test|
|terminal count の再計算照合を外す|`test_finalizer_revalidates...` の追加 parameter|
|summary の dropped から complete 済み role を除く|更新 `test_mutation_07...` の exact dropped assertion|
|summary schema を v1 のままにする|更新 `test_production_adapter_artifact_finalizes...`|
|新しい proof limitation を片側だけから除く|既存 docstring test `:431`|

### 6. 親担当 docs の検査

現案は §5.1 (i) の必要項目を概ね含むが、次を直す必要がある。

1. **配置:** `#### 5.1.2` を現行 `## 6` の直前、すなわち現在の `docs/phase3-b4-reflux-ablation-preregistration.md:542` に置く。`対象 driver` item の直後 `:192` に H4 を置くと、残りの §5.1 field bullets が 5.1.2 配下へ入ってしまう。`:171-191` には「詳細は §5.1.2」と参照だけ足す。
2. この配置なら `p3_b4_analysis_prereg_consumer.py:301-345` が hash 対象にする 5.1.1 bytes の直後が新 H4 境界となる。既存 bytes を動かさず境界へ挿入すれば `:404-407` の raw / semantic hash を変えない。
3. 候補は driver 名だけでなく、次の exact driver-axis 対として先に固定する。

   - `base = silo-backoff-magnitude`
   - `sort = silo-writeset-sort`
   - `trigger = silo-backoff-trigger-gating`

   `_DRIVER_MODULES` (`p3_b4_wiring_probe.py:70-74`) と `B4_PROJECTION_DRIVER_KINDS` (`p3_b4_admission_record.py:91-95`) がともに exact 3 で一致しなければ開始しない。

4. exact command は driver ごとに次の形へ展開して 3 本を逐語固定する。

   `python3 tools/pegasus/dispatch_compute.py --task generic -- python3 -m orchestrator.campaign.p3_b4_wiring_probe --driver base --evidence-set-id t2341-eligibility`

   `sort`、`trigger` も同形。generic argv が `--` を除いて shell=False で child argv になることは `dispatch_compute.py:4482-4489`, `:1623-1636` と一致する。

5. command 前提として、§5.1.2 の commit が HEAD の祖先であること、3 target と sidecar が全て不存在であること、3 command を同じ source HEAD から投入することを明記する。生成後は evidence の `source.repository_head` が freeze commit を含むことを検査する。
6. 合格述語を `status != "not_measured"` ではなく、次の conjunction にする。

   - sidecar が exact `<64 lower hex><two spaces><driver>.json\n` で JSON bytes の SHA-256 と一致。
   - `run.driver` と `run.axis` が凍結対と exact 一致。
   - `run.evidence_set_id == "t2341-eligibility"`。
   - `run.argv` が凍結した probe argv と exact 一致。
   - `result.passed is true`。
   - `result.pass_rule == "all-four-checks-and-zero-interdiction-or-protected-root-violations"`。
   - `checks.campaign_identity.site_projected_cfg.status == "measured"`。
   - 同 `site == PEGASUS_COMPUTE`。
   - 4 checks、interdiction、protected root の閉じた条件が evidence schema と一致。

7. 選択規則は「全 3 候補を判定後、合格集合から固定優先順 `base, sort, trigger` の最初を選ぶ」。0 件なら値セルを変更せず `design_not_feasible` を記録する。infra rc=16 は 0 件扱いでなく、procedure 未完了として停止する。candidate check failure と infra failure を混同しない。
8. D1266 の役割定義は現行 `:174-176` で満たす。§5.1.2 でも記入者 = レビュー者 = `thawk105` と、その reviewer が独立検査者ではないことを参照する。
9. (ii) の先走りをコード自体は防がない。freeze commit の ancestry と evidence `source.repository_head` の照合が、同じ slug の pre-freeze evidence 再利用を拒否する手続きになる。ただし削除後の再実行歴までは証明しない、と過大主張を避ける。
10. §5 の値セルは選択結果だけでなく、3 候補すべての JSON path と SHA-256 を束縛する。選択した `base.json` だけでは、複数合格時の決定を再計算できない。

提示例の文字列は `_RESERVED_SENTINEL_RE` (`p3_b4_admission_record.py:114-118`) に掛からない。`_EXPECTATION_ROW_RE` (`:103-113`) は label が `model snapshot / prompt hash / projection hash` の行だけへ適用され (`:674-676`)、対象 driver 行には適用されない。

ただし `p3_b4_admission_record.py:602-688` は対象 driver セルを意味解析せず、非空かつ sentinel なしとだけ判定する。新しい §5.1.2 は読まない。`p3_b4_analysis_prereg_consumer.py:301-345` も 5.1.1 だけを読み、§5 表と 5.1.2 は読まない。したがって親は「consumer が evidence path/hash や選択規則を検証する」と書いてはならない。

対象 driver 行だけを埋めても、現在は残る 8 value cell に `未記入` が含まれるため admission は閉じたままである。親 brief の「他 9 行が未記入」は不正確で、n 行は既に記入済みである。

推奨する値セル形式は次の形。

`base (silo-backoff-magnitude); evidence_set=t2341-eligibility; base.json sha256=<64hex>; sort.json sha256=<64hex>; trigger.json sha256=<64hex>; 記入者 = レビュー者 = thawk105 (D1266、D1638)`

path root は §5.1.2 に exact 固定し、各 sidecar も tracked にする。この形も sentinel regex と expectation row regex の問題を起こさない。

## 依頼 4

1. **「同一セッション」の意味**

   - A: 現行の `(window,pair,sample_index)` 3-role block を D1641 の「同一セッション」と解釈する。
   - B: candidate と reference を一つの低水準 session 呼出しへ再設計する。
   - **推奨: B。** 現行コード自身が各 role を `PlannedSession` と呼ぶため、A は逐語と衝突する。A を採るなら D1641 に用語訂正の追記が必要。

2. **残る 4 行の機械保証**

   - A: target/axis、PerfConfig 全項目、journal、成果物名は frozen spec の人手レビュー責任とする。
   - B: schema と validator を別 wave で拡張し、測定前に機械検査する。
   - **推奨: B。** 本 S-C commit へ混ぜず、D1641 測定開始前の follow-up とする。少なくとも「欠測だけ直せば D1641 完全適合」とは記録しない。

## 総括

- 判定: S-C の欠測案 P3/P4 は修正後に実装可能。ただし「唯一の実差」は不一致。
- 直接赤になる既存 test は 3 node。fixture 更新漏れなら 40 collected nodes が連鎖赤。
- 更新 6 test function、新規 3 function / 4 collected nodesを見込む。
- 推測変更量: production net +75〜+105 行、test net +100〜+165 行。
- 欠測 scope だけなら 1 実装子、1 commit、fix 3 巡以内で分割不要。
- 裁定パッケージ候補は 2 件あり、共通参照点の同一セッション解釈と、残る機械保証の扱い。