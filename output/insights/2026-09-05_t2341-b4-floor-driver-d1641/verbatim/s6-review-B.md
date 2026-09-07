# blocker

## 所見 1 — median の有限性を検査せず、正当な有限 rep から床値生成が停止する

(a) [実測] `_measurement_payload_complete` は各 rep の有限性だけを検査し、median を検査しない。偶数 rep の `_median` は `(a + b) / 2` なので、`sys.float_info.max` 2 件では各値が有限でも median が `inf` になる。実式でも `each_finite=True / median_finite=False` を確認した。

(b) [実測] `orchestrator/campaign/floor_pair_driver.py:1606-1674`、`:2411-2417`、`:2643-2653`。

(c) [実測] 放置すると、全 role が有限な同値の最大 float を返す標本でも、期待される `D=0` の生成ではなく `not_generated_missing_samples` となり、床値の受理集合を不当に縮める。

(d) [推測] 偶数 median を `lower + (upper - lower) / 2` などの overflow-safe な式にし、`_measurement_payload_complete` と `_status_from_records` で role-aware median の有限性・符号も明示検査する。全 role が最大有限 float 2 件を返す実 `run_window` 正例を追加し、`generated / upper=0` を固定する。この回帰用変異も M1〜M20 外として追加する。

(e) [実測] plan v2 3、6、8、12(j)。既存 M1〜M20 に直接対応する変異なし。

# must-fix

## 所見 2 — M15 の入力は terminal count が先に拒否し、因果 gate の証拠にならない

(a) [実測] `test_not_run_sample_dropped_without_prior_failure_is_rejected` は、原因なし `not_run_sample_dropped` と同時に terminal の `dropped_sample_count` を 1 へ改変する。M15 の因果検査だけを外しても、再導出された dropped key は 0 のため terminal exact 検査が拒否する。regex 不一致で node 自体は赤になるが、因果 gate を殺した証拠ではない。

(b) [実測] `orchestrator/tests/test_floor_pair_driver.py:2142-2175`、`orchestrator/campaign/floor_pair_driver.py:2276-2279`、`:2395-2406`。

(c) [実測] 放置してもこの fixture の床値は生成されないため受理集合は変わらず、M15 だけが実効 gate であるという変異台帳の参照が誤る。

(d) [推測] terminal を再導出値 `dropped_sample_count=0 / complete_sample_count=0` に合わせ、`_validate_window_artifact` を直接呼んで因果エラーだけを期待する。現状の M15 は DW-M03 により証拠から外す。

(e) [実測] plan v2 5(a)(c)、12(h)、M15。

## 所見 3 — 境界 fixture は数式を正しく固定するが、変異帰属が過剰決定されている

(a) [実測] 7 構成の分母・閾値・局所性は正しい。一方、5 境界を一つの parameterized test にまとめ、status、campaign summary、drop 因果、derivation を同じ node で検査しているため単一理由ではない。

(b) [実測] helper は `orchestrator/tests/test_floor_pair_driver.py:1347-1466`、境界 node は `:1966-2033`、局所性は `:2036-2055`、empty stratum は `:2107-2139`。

|構成|固定しているもの|静的判定|
|---|---|---|
|59/2|unique dropped 2、分母 59、5% 未満の生成|[実測] M6 の正例。ただし summary・因果・derive も同時検査|
|59/3|分母 59、5% 超過|[実測] M8。summary count も同時検査|
|40/2|exact 5% を受理する比較演算|[実測] M7。empty-stratum 正例も同じ境界を再観測|
|177/8|3 pair 合算分母 177 の正例|[実測] M10。鳩の巣原理により pair 分母なら必ずどこかが 3/59 以上|
|177/9|177 分母の負例|[実測] M8 と分母の逆向き確認|
|2 window|2/20 と 0/20 を全体 2/40 に希釈しない|[実測] M9 の campaign 局所性|
|20 pair × 1|全体 exact 5% でも 1 stratum が空|[実測] M12。threshold より empty を選ぶ理由を固定|

(c) [推測] 放置すると変異本走で M3〜M11 の複数 node が同時に赤となり、どの gate が床値または受理集合を守ったかを単独帰属できない。

(d) [推測] gate の status だけを検査する小さい node と、summary exact、因果、derivation の各 node を分割する。特に M11 は、最後の role の post-probe だけを competing にして3 roleすべてに完備 throughputを残し、その標本を混ぜると upper が変わる専用 fixtureにする。現行 `test_production_adapter_artifact_finalizes_from_raw_medians` は drop が 0 なので、段4表の M11 候補 node にはならない。

(e) [実測] plan v2 7〜9、12(c)〜(f)(m)、M3〜M12。

### M1〜M20 の静的帰属

[実測] node の存在と入力形は現物から確認した。[推測] pytest・変異 probe 未実走のため、「追加で赤になる node」は制御フローからの静的予測である。

|M|殺す node|帰属判定|
|---|---|---|
|M1|`test_d1641_failure_policy_is_the_only_accepted_wire_policy[policy-all_planned_samples_required/v1]`|単独|
|M2|同 `[max_dropped_fraction-1/19]`|単独|
|M3|`test_measure_exception_still_runs_post_probe_and_closes_remaining_plan`|campaign helper 利用 node にも波及|
|M4|同上|drop を持つ campaign node 全般へ波及|
|M5|同上|campaign summary の exact 因果 assertion にも波及|
|M6|campaign 境界 `[59-1-2-generated]`|他の dropped-count assertion にも波及|
|M7|campaign 境界 `[40-1-2-generated]`|empty-stratum node も exact 5% を観測|
|M8|campaign境界 59/3、177/9|window-local、threshold-priority node にも波及|
|M9|`test_campaign_threshold_is_local_to_each_window_not_global_sum`|単独|
|M10|campaign境界 177/8|empty-stratum node も pair 分母で赤|
|M11|生成側 59/2、40/2、177/8 と `test_dropped_summary_includes_complete_role_before_failure`|過剰決定。段4候補 node は無効|
|M12|`test_exact_five_percent_with_empty_stratum_is_not_generated`|単独。下流も床値生成を止めるが status が変わる|
|M13|`test_finalizer_revalidates_complete_header_and_terminal_contract` の terminal count 3 case|各 field case は単独|
|M14|`test_mutation_07_status_only_rewrite_is_rejected_by_payload_derivation`|単独|
|M15|`test_not_run_sample_dropped_without_prior_failure_is_rejected`|terminal gate と冗長。証拠から外す候補|
|M16|`test_candidate_zero_is_complete_and_contributes_gain_minus_one`|単独|
|M17|`test_reference_zero_and_negative_values_are_fatal_protocol_violations[values_by_role0]`|単独|
|M18|`test_mutation_05_real_trace_inspection_call_rejects_before_probe_and_measure` と `test_outside_window_is_fatal_and_not_counted_as_dropped`|登録自体が2 statusを束ねるため2 node|
|M19|`test_production_adapter_artifact_finalizes_from_raw_medians`|単独|
|M20|`test_module_docstring_names_limits_and_unrecorded_env_failure_is_not_a_status`|単独|

## 所見 4 — 既存の「measure exception 後も post-probe」を検査する pin が消えている

(a) [実測] 同名 test は measure exception を一度も起こさず、最初の pre-probe competing を検査する test に置換された。旧 `failed_measure_point` と `probes == [0, 1]` が削除され、supersede 許可6種に含まれない「例外後の post-probe」保証が失われた。

(b) [実測] `orchestrator/tests/test_floor_pair_driver.py:1514-1570`。実装上の post-probe は `orchestrator/campaign/floor_pair_driver.py:1836-1840`。

(c) [推測] 放置すると、measure exception 後の post-probe を削除・短絡する回帰が緑になり、raw artifact の probe 参照が失われる。現仕様では標本自体は drop されるため床値の数値は直ちには変わらない。

(d) [推測] 現 test を pre-probe drop の名前へ変更し、別 node で最初の measurement を例外化して、post-probe 実行、`measure_failed`、同標本だけの skip、次標本継続を固定する。

(e) [実測] plan v2 11、12(b)、M3〜M5。

## 所見 5 — droppable status 6種のうち3種が実経路 test に到達していない

(a) [実測] 実 `run_window` で生成されるのは `pre_probe_competing`、`measure_failed`、`measure_incomplete`。`pre_probe_indeterminate`、`post_probe_competing`、`post_probe_indeterminate` は test source に期待 status がなく、finalizer の対応分岐にも到達しない。さらに pre-probe competing と measure_incomplete の test は finalize まで通さない。

(b) [実測] pre competing は `orchestrator/tests/test_floor_pair_driver.py:1526-1567`、measure failed は helper `:1432-1447`、measure incomplete は `:2323-2352`。未到達の production 分岐は `orchestrator/campaign/floor_pair_driver.py:2199-2213`。

(c) [推測] 放置すると、これらを fatal または complete に誤分類する回帰や、finalizer が実 driver の artifact を拒否する回帰が緑となり、dropped count、campaign 合否、床値が変わりうる。

(d) [推測] pre/post × competing/indeterminate を実 probe callback で発生させ、各 artifact を finalize する parameterized test を追加する。M11 専用 fixtureには最後の role の post-probe competing を利用できる。

(e) [実測] plan v2 4、5、12(b)(h)(i)、M3〜M5、M11、M14。

# nit

## 所見 6 — 3 meta-test は `measure_point` の exact call shape を検査していない

(a) [実測] `test_ccbench_spawn_sites.py` は subprocess site、`test_official_perf_closure.py` は perf predicate、`test_plain_runner_coverage.py` は test file の自走 harness を走査する。位置引数4個と keyword集合を exact に検査するのは `test_mutation_12_production_adapter_passes_all_runner_arguments_and_sinks` である。

(b) [実測] `orchestrator/tests/test_ccbench_spawn_sites.py:358-370`、`test_official_perf_closure.py:479-543`、`test_plain_runner_coverage.py:35-74`、`test_floor_pair_driver.py:1080-1139`、production call `floor_pair_driver.py:1406-1424`。

(c) [実測] 現物は1 call、位置引数4、keyword 13個で exact 一致しており、床値・受理集合への影響はない。報告上の consumer の説明だけが不正確である。

(d) [推測] 完了報告を「2 meta-test が production source inventory、plain-runner meta-test が自走 collection、call shape は driver test が exact 検査」と訂正する。

(e) [実測] plan v2 11、収集検査5・6。M番号なし。

# 確認済み事項

- [実測] 差分の全削除行を確認した。所見4を除き、削除は schema/policy、role-aware 完備性、droppable の global stop、旧 terminal、旧 status 判定という supersede 許可範囲に収まる。
- [実測] HMAC 実装 `floor_pair_driver.py:1219-1297` は不変で、golden 更新は schema/spec hash 更新による順序変更だけである。sample block、role集合、schedule index の pin は追加されている。
- [実測] `test_finalizer_revalidates...` の既存6 parameter は `test_floor_pair_driver.py:1896-1901` に残り、terminal count 3 parameterだけが追加された。
- [実測] `REQUIRED_FIELD_PATHS` は69から70へ増え、静的評価で70件すべて一意だった。追加は `test_floor_pair_driver.py:522`。
- [実測] `_valid_document` の新 field は `test_floor_pair_driver.py:283-288` にあり、同 file の手書き failure-policy fixture は他にないため、旧40 nodeの早期連鎖赤は静的には解消している。
- [実測] top-level test function は62、parameter展開の静的見込みは161 node。parameter tupleと明示IDに重複はない。
- [実測] `test_floor_pair_driver.py:2510-2511` の `pytest.main([__file__])` により、自走 harnessと通常pytestの双方が同じtestを収集する。
- [実測] metamorphic test `:2178-2214` は spec、probe、drop keyを同じにし、`values_by_role` だけを変更している。
- [実測] production sourceの subprocess callは従来どおり `_git_show_head`、`_git_head`、`_run_probe` の3件で、CCBench inventoryと一致する。`measure_point` は1件、位置引数4、keyword 13件で直接testとも一致する。
- [実測] `git diff --check` は異常なし。pytestは制約どおり実走していない。

# 裁定パッケージ候補

## 所見 7 — plan v2 を超える record/probe exact closure が追加されている

(a) [実測] `_SESSION_RECORD_FIELDS` による全field exact closure、probeの `stdout/stderr/returncode` 型検査、measured recordの `binary_sha256` 再照合が追加された。plan v2 5が名指しする status・competitors・error・throughput・rep・因果・terminal countより広い。

(b) [実測] `orchestrator/campaign/floor_pair_driver.py:2082-2109`、`:2113-2139`、`:2149-2150`、`:2185-2187`。

(c) [推測] 通常のdriver生成物の床値は変わらないが、同じstatus意味を持つ追加field付きartifactもfinalizerが拒否するため、artifact受理集合を無裁定で狭める。

(d) [推測] DW-G05により、親がplan v2 5の「exact payload」に含むと明示追認するか、status再導出に不要なfield closureと型検査を削る。少なくともscope追加として記録する。

(e) [実測] plan v2 5。M1〜M20には未登録。

## 総括
- [実測] blocker 1件、must-fix 4件、nit 1件。pytest/変異probeは未実走。
|変異|観測 node|
|---|---|
|M1|`test_d1641_failure_policy...[policy-all_planned_samples_required/v1]`|
|M2|`test_d1641_failure_policy...[max_dropped_fraction-1/19]`|
|M3|`test_measure_exception_still_runs_post_probe_and_closes_remaining_plan`ほか|
|M4|同 node ほか campaign drop nodes|
|M5|同 node ほか summary exact nodes|
|M6|`test_campaign_drop_fraction...[59-1-2-generated]`ほか|
|M7|同 `[40-1-2-generated]`、empty-stratum|
|M8|同 59/3・177/9、window-local、threshold-priority|
|M9|`test_campaign_threshold_is_local_to_each_window_not_global_sum`|
|M10|campaign 177/8、empty-stratum|
|M11|campaign生成3 case、`test_dropped_summary_includes_complete_role_before_failure`|
|M12|`test_exact_five_percent_with_empty_stratum_is_not_generated`|
|M13|`test_finalizer_revalidates...` terminal count 3 case|
|M14|`test_mutation_07_status_only_rewrite_is_rejected_by_payload_derivation`|
|M15|冗長。DW-M03で証拠から外す候補|
|M16|`test_candidate_zero_is_complete_and_contributes_gain_minus_one`|
|M17|`test_reference_zero_and_negative_values...[values_by_role0]`|
|M18|binary-binding test、outside-window test|
|M19|`test_production_adapter_artifact_finalizes_from_raw_medians`|
|M20|`test_module_docstring_names_limits_and_unrecorded_env_failure_is_not_a_status`|
- [実測] 供給されていない変異番号: なし。ただしM15は冗長、median有限性の回帰変異は未登録。