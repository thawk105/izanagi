## blocker

[実測] なし。

## must-fix

### 所見 1 — M15 fixture は terminal gate の冗長性を除いたが、因果 gate 単独の証拠にはなっていない

- (a) [実測] F3 に従い terminal は planned 1 / dropped 0 / complete 0 へ直っています。しかし test は `finalize_floor` 全体を呼ぶため、M15 の先行原因検査を外しても正常終了しません。`not_run_sample_dropped` は drop key に数えられず、空の throughput を持つ標本が derivation に入り、`_median([])` の添字参照へ進みます。
- (b) [実測] fixture は `orchestrator/tests/test_floor_pair_driver.py:2429`、terminal 修正は `:2458`、対象 gate は `orchestrator/campaign/floor_pair_driver.py:2296`。後続経路は同 file `:2470`、`:2572`、`:2587`、空列を扱えない median は `:2431`、`IndexError` を捕捉しない箇所は `:2670` です。
- (c) [推測] 放置して M15 を適用しても malformed artifact は床値へ入らず、summary 発行前の `IndexError` で停止します。したがって床値・受理集合は現在も広がりませんが、M15 を殺した理由が因果 gate ではなく下流 crash になります。
- (d) [推測] `pytest.raises(..., match="先行失敗")` の対象を `finalize_floor` から `F._validate_window_artifact(spec=spec, plan=plan, window=spec.windows[0])` へ変えてください。gate を外した変異では validator が返るため、因果 gate だけを観測できます。
- (e) [実測] F3 / M15。F3 は未閉です。

## nit

### 所見 2 — production 差分には F1・F2 外の動作等価な書換えが1箇所ある

- (a) [実測] `_audit_session_causality` の `setdefault` が明示初期化へ置換されています。F1・F2 の数値修正ではありません。
- (b) [実測] `orchestrator/campaign/floor_pair_driver.py:2279`。fix patch の該当差分は `s6-fix.patch:94`、これを要求する既存 source test は `orchestrator/tests/test_floor_pair_driver.py:2784` です。
- (c) [実測] 空のローカル辞書に対する同値変換なので、床値・受理集合は変わりません。
- (d) [推測] code は戻さず、段7で「既存 source invariant を緑へ戻すための動作等価な例外」として production 局所修正契約への例外を記録すれば十分です。
- (e) [実測] 規模契約。F番号・M番号なし。

## F1〜F6 の閉包

- [実測] **F1 閉。** `_median` は `low + (high - low) / 2.0` です。到達値は有限非負なので差・加算とも overflow せず、median 内に有限性検査は追加されていません。`orchestrator/campaign/floor_pair_driver.py:2431`。実 `run_window` 正例は `orchestrator/tests/test_floor_pair_driver.py:2013` で、全 role の全 rep を `sys.float_info.max` とし、complete 3件、generated、upper/candidate_floor 0を固定しています。
- [実測] **F2 閉。** helper は exact `int` / `float` 以外も含めて返値を持ち、符号判定 `value < 0` は `float(value)` より前です。変換例外も捕捉します。`floor_pair_driver.py:1319`。正負の `10**400` は `test_floor_pair_driver.py:2030` で実 `run_window` と `finalize_floor` の双方を通ります。
- [実測] **F3 未。** terminal の dropped 0 修正自体は完了しましたが、所見1のとおり M15 fixture は下流 crash にも依存します。
- [実測] **F4 閉。** 5境界の期待 tuple は `test_floor_pair_driver.py:2157` に同値で移され、status/upper node は `:2170`、summary/因果/derivation node は `:2194` に分割されています。M11 fixture は `:2323` で全3 roleに throughputを残し、drop対象 D=0.75、残存 max=0.25、upper=0.25を固定しています。
- [実測] **F5 閉。** `test_measure_exception_runs_post_probe_drops_remaining_roles_and_continues` は probe→measure例外→probe、`measure_failed`、同標本だけのskip、次標本3 role完備を固定しています。`test_floor_pair_driver.py:1573`。
- [実測] **F6 閉。** `test_droppable_probe_statuses_run_and_finalize` は pre/post × competing/indeterminate の4 parameterを実 probe callbackから発生させ、`run_window` の後に `finalize_floor` を呼び、1/21 dropで generatedを固定しています。`test_floor_pair_driver.py:1636`。

## test 削除行の全件検査

[実測] fix patch の test 側削除10行を全件確認しました。

- [実測] `s6-fix.patch:129` は旧名から pre-probe用名への改名だけで、node本体の削除ではありません。
- [実測] `:354`〜`:360` の5期待 tupleは `:343`〜`:349` の `_CAMPAIGN_BOUNDARY_CASES` へ同値移動しています。
- [実測] `:399` の負例 `upper is None` は、`:369` の generatedとの双方向一致へ移され、正例側も検査する強化になっています。
- [実測] `:485` は F3 が要求した forged terminal の `dropped_sample_count=1` の除去です。期待例外の反転や緩和ではありません。
- [実測] skip追加、test node削除、期待statusの反転、受理条件の緩和はありません。

## regression 面

- [実測] create-only は `floor_pair_driver.py:1513`、HEAD/blob/source三者束縛は `:1125`、`:1182`、`:1971`、固定 probe argv は `:64` と `:1563` のままです。
- [実測] upper 1以上の非丸めは `:2680`、live site/env は `:1494`、production adapter非差込は `run_window` の固定 signature `:1947` に残っています。
- [実測] plan exact は `:1308`、session ID/count/order exact は `:2365`、fatal 3種は `:102`〜`:114` と `:2027`〜`:2030` に残っています。
- [実測] `_SESSION_RECORD_FIELDS` exact閉包、probe payload、`binary_sha256` 再照合は `:2100`〜`:2207` に残り、fixによる緩和はありません。
- [実測] `runner.measure_point` の production callは `:1418` の1件だけで、位置引数4個、keyword 13個です。fix hunkはこの呼出しを変更していません。
- [実測] `git diff --check` と両所有fileのAST parseは成功しました。pytestは制約どおり実走していません。

## M1〜M22 の観測 node

|M|観測 node|静的帰属|
|---|---|---|
|M1|[実測] `test_d1641_failure_policy_is_the_only_accepted_wire_policy[policy-...]` (`:561`)|[推測] 単独|
|M2|[実測] 同 `[max_dropped_fraction-1/19]`|[推測] 単独|
|M3|[実測] `test_measure_exception_runs_post_probe_drops_remaining_roles_and_continues` (`:1573`)|[推測] 複数のcall数/statusでもkillするため過剰決定|
|M4|[実測] 同 nodeおよび `test_pre_probe_drop_closes_sample_and_continues_next_sample` (`:1514`)|[推測] 過剰決定|
|M5|[実測] 同2 nodeのerror/cause exact|[推測] 登録変異自体が2変更を束ね、過剰決定|
|M6|[実測] campaign境界 `(59,1,2)` (`:2170`)|[推測] status nodeは単独。summary nodeもkillする|
|M7|[実測] campaign境界 `(40,1,2)`|[推測] status nodeは単独。empty-stratum nodeも観測|
|M8|[実測] campaign境界 `(59,1,3)`、`(59,3,9)`|[推測] 2負例と局所性/優先順でもkillし、過剰決定|
|M9|[実測] `test_campaign_threshold_is_local_to_each_window_not_global_sum` (`:2252`)|[推測] 単独|
|M10|[実測] campaign境界 `(59,3,8)`|[推測] primaryは単独。empty-stratum nodeも観測|
|M11|[実測] `test_mutation_11_post_probe_drop_excludes_high_difference_sample` (`:2323`)|[推測] 有効だが、retained件数・値集合・upperの複数理由で過剰決定|
|M12|[実測] `test_exact_five_percent_with_empty_stratum_is_not_generated` (`:2394`)|[推測] 単独|
|M13|[実測] `test_finalizer_revalidates_complete_header_and_terminal_contract` のterminal 3 case (`:2098`)|[推測] 各case単独|
|M14|[実測] `test_mutation_07_status_only_rewrite_is_rejected_by_payload_derivation` (`:2136`)|[推測] 単独|
|M15|[実測] `test_not_run_sample_dropped_without_prior_failure_is_rejected` (`:2429`)|[推測] 冗長terminal gateは解消したが、下流 `IndexError` と過剰決定。所見1|
|M16|[実測] `test_candidate_zero_is_complete_and_contributes_gain_minus_one` (`:2503`)|[推測] 単独入力。複数の結果assertあり|
|M17|[実測] `test_reference_zero_and_negative_values_are_fatal_protocol_violations` のreference-zero case (`:2545`)|[推測] 単独|
|M18|[実測] binary node (`:1693`) と outside-window node (`:2586`)|[推測] 登録された2 fatal armに各1 node。冗長なし|
|M19|[実測] `test_production_adapter_artifact_finalizes_from_raw_medians` (`:1962`)|[推測] schema assertionで単独|
|M20|[実測] `test_module_docstring_names_limits_and_unrecorded_env_failure_is_not_a_status` (`:454`)|[推測] 片側除去を直接観測|
|M21|[実測] `test_mutation_21_max_finite_even_medians_generate_zero_upper` (`:2013`)|[推測] 単独|
|M22|[実測] `test_mutation_22_large_exact_int_is_total_in_run_and_artifact_rederivation` の正負2 case (`:2050`)|[推測] 両caseともrun側で先にkillするため変異証拠としては過剰決定。現行経路のfinalize検査自体は実行される|

## 規模

- [実測] fix patch numstatは production `+40/-15`、test `+296/-10` で、追加行目安の上限内です。
- [実測] 新 helperはF2のtotal変換だけで、互換層や一般化APIはありません。medianの追加guardは変換失敗用であり、禁止されたmedian有限性検査ではありません。
- [実測] F1/F2外のproduction変更は所見2の動作等価な明示初期化だけです。余分な受理gateは追加されていません。

## 総括

- [実測] F1=閉、F2=閉、F3=未、F4=閉、F5=閉、F6=閉。
- [実測] blocker 0件、must-fix 1件、nit 1件。
- [実測] 緩んだ regression 面: なし。`measure_point` call shapeも不変。
- [実測] 冗長な事前validatorにより無効なnode: なし。
- [推測] M15のみ下流crashとの過剰決定が残る。
- [実測] M1→`test_d1641_failure_policy...[policy]`; M2→同`[fraction]`。
- [実測] M3→`test_measure_exception_runs_post_probe...`; M4→同/pre-probe node。
- [実測] M5→同2 node; M6→campaign 59/2。
- [実測] M7→campaign 40/2; M8→campaign 59/3・177/9。
- [実測] M9→`test_campaign_threshold_is_local...`; M10→campaign 177/8。
- [実測] M11→`test_mutation_11_post_probe_drop...`; M12→empty-stratum node。
- [実測] M13→terminal count cases; M14→status-only rewrite node。
- [実測] M15→先行失敗なしnode、過剰決定; M16→candidate-zero node。
- [実測] M17→reference-zero node; M18→binary/outside-window nodes。
- [実測] M19→production adapter summary node; M20→docstring/NOT_PROVEN node。
- [実測] M21→max-finite median node; M22→large-int正負2 node、過剰決定。