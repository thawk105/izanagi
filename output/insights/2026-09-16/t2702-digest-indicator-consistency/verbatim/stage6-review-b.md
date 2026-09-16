## 所見

静的レビュー。pytest・変異注入は未実走。以下の行番号は実装後の現物。変異の期待 node は、baseline が成功し、対象の値の断言まで到達する場合を示す。

1. **real — M6 の赤化範囲は plan の「平均テストの direct のみ」より広い。**

   **根拠:** `runner.py:1300` の direct 側を旧選択へ戻すと、`test_calibrator.py:497` の `.4` が `.6`、`:548` の片側欠損時の `None` が `.6`、`:562` の `(.4,17M,300)` が `(.6,14M,300)` になる。したがって平均・欠損・偶奇の **3 direct node** が赤。deferred 側は `runner.py:1072` の helper 呼出しが残るため、この変異では緑。

   **成果物への影響:** 平均テストだけを期待 node に固定すると、正当な追加検出を変異台帳で期待外として扱う。

   **推奨: nit。** probe 後の正式 spec は後掲の3 nodeで固定する。現時点の probe 用空配列を完成済み期待値とは扱わない。

2. **refuted — M1〜M5 を新規 fixture が検出できないという懸念。ただし node 内の後続ケースは独立実走されない。**

   **根拠:**
   - M1/M2: `test_calibrator.py:491–510` の中央二反復は abort `.2/.6`、latency `20M/14M`。上側採用なら `.6/14M` となり、期待 `.4/17M` と異なる。
   - M3: `:539–549` は各指標について `(None,x)`、`(x,None)`、`(None,None)`、`(0,x)` を置く。欠損行と counts fallback は `:470–474` で省かれる。残る側の採用は最初の abort ケースで `.6 != None`。
   - M4: `:523–524` の全同値 `[200,200,200]` では、現行は実行 index 0、変異は index 1。`(wall,maxrss,abort,latency)` が `(1,100,.1,10)` から `(2,200,.2,20)` となり、`:529` で赤。
   - M5: `:555–562` の要求5・有効4は変異後 `(.6,14M,300)`。`:563–569` の要求4・有効3は、変異後に下側二反復を平均して約 `(.15,15,200)`。**両ケースとも個別に評価すれば赤**だが、実走は最初の assert で停止する。
   - M5 の `len(rep_results)` は一般には要求 reps と同一ではない。例外で除外された反復は `runner.py:1197` 以降の `continue` により入らない。今回の fixture は `strict_returncode=False` なので rc=7 でも解析され、throughput 行の欠損によって無効になる（`:706`、`test_calibrator.py:480`）。この fixture では登録意図どおりの偶奇になる。

   **成果物への影響:** 対象回帰は検出できるが、単一 node の失敗から全ケース・両指標をそれぞれ実測したとは記録できない。

   **推奨: nit。** 現状の検出力は十分。M3 の両指標、M5 の両方向まで独立した実測証拠を求める場合はケースも node 化する。

3. **refuted（現物）／未実測（将来変更）— monotonic fixture と単位なし maxrss は現在成立する。**

   **根拠:** `runner.py:656,688` に各 rep の `time.monotonic()` が計2回ある。`measure_point` の時刻記録は `time.time_ns()`、`open_measurement_point`（`:958`）は monotonic を追加呼出ししない。fixture は `settle_first=False`、subprocess は iterator stub なので、`test_calibrator.py:478` の ticks はちょうど `2×reps` 個、wall は `1,2,…` 秒になる。

   `runner.py:45–48` は `_num("300")` を整数化する。`benchparse.py:41–52` は先頭 token を `float` 化するため、単位なし `"300"` は **300 kB** として保持される。

   将来、追加の monotonic 計測・settle・実 subprocess の timeout 待機をこの patch 範囲に入れると、ticks のずれや枯渇で集約とは無関係に赤化する。また patch は共有 `time` module の属性を変えるため、依存先の呼出しも対象になる。

   **成果物への影響:** 現在の値は正しい。将来の計時変更による失敗を集約変異の検出として台帳へ誤計上する可能性はある。

   **推奨: nit。** 現状修正不要。失敗原因は値の assert と `StopIteration` を区別する。

4. **refuted — 自走 harness の現行 node 名と meta-test 要求の不一致。**

   **根拠:** `test_calibrator.py:1354` の `__main__` 内に `_run(` があり、`test_plain_runner_coverage.py:27–39` の signal 判定を満たす。4つの decorator は `args[1]=["direct","deferred"]`、`ids` も同じ文字列（`test_calibrator.py:489,514,534,553`）。`:1323–1329` の展開結果は pytest の `[direct]`／`[deferred]` と一致する。

   ただし harness は `ids=` 自体を読んでいない。将来 ids を値と異なる名前にした場合や `pytest.param`、複数引数へ拡張した場合の互換性はない。deferred stub も `text=False` に対して str を返すが、現行 `_decode_captured_output`（`runner.py:165`）が受理するため集約には到達する。bytes decode の検証にはならない。

   **成果物への影響:** 現在の9 nodeの識別は一致する。将来の decorator 拡張では pytest と自走報告の参照 node がずれ得る。

   **推奨: nit。** 現行用途では修正不要。

5. **refuted — critic の既存期待値変更の逸脱・legacy fixture との不一致。**

   **根拠:** `author1.patch` の既存テスト変更は、plan-v2 §4 が指定した4箇所に一致する。現物は `test_critic.py:667,683–684,730–733,804–807`。legacy fixture（`:776–782`）の値は throughput `123.0`、abort `.2`、LLC `.3`、IPC `1.2` で、明示辞書と一致する。除外されるのは latency `456.0` のみ。

   新規テスト（`:810–834`）は射影・軸・ヘッダ・WAL残存・方向辞書を固定値で確認する。M7 は新規だけでなく、この既存4 nodeも赤化する。`HIGHER_IS_BETTER` を変更しない M7 でも、射影 key の不一致で先に検出できる。

   **成果物への影響:** latency を通常 digest から外し、WAL の5指標を維持するという予定の変更だけが期待値に反映されている。

   **推奨: nit。** 修正不要。作者時点の admission 失敗は対象 assert の成功証拠ではなく、親の統合後実走で確認する。

6. **refuted（特定した固定期待値の破損）／未実測（受入全走）— 周辺テストに今回の意味変更だけで必ず赤となる箇所は見つからない。**

   **根拠:**

   | 対象 | 静的照合 |
   |---|---|
   | `test_calibrator_deferred_output.py` | `:197–207` の2 repsは同じ出力、throughputs は `[1000,1000]`。平均化と旧選択を区別しない。 |
   | `test_between_run_floor.py` | `:762–779` は throughput と abort `.2` を持つ固定 stub。runner の再集約を通らない。 |
   | `test_pegasus_floor_scoping.py` | `:81–85` の測定 stub が同値 throughputs と abort `.125` を返す。 |
   | `test_campaign.py` | bench の `ScriptedPoint.leading_indicators`（`:5826–5830`）は固定値。WAL5 keyの期待（`:6707`）は維持される。screening matrix（`:7807–7838`）も集約済み abort を注入するため、新しい集約の境界影響は検証しない。 |
   | `test_p3_s4_loop.py` | digest bytes 比較の期待値は `:3823` で現行 `render_text(build_digest(...))` から生成する。旧5列の literal golden ではない。 |
   | online digest | 独立した `test_online_digest*.py` は見つからない。実際の対象は `test_guided.py:90–162` と `test_critic.py:851–880`。genome数・admission表示を確認し、旧列を固定しない。 |
   | `test_p3_b4_closed_critic.py` | `:1678` は送信した本文の hash、`:2232–2249` は現行生成本文との比較。列削除に追随する。 |
   | backoff report | `test_backoff_sweep_report*.py` は見つからない。`test_backoff_consumers.py:135–145` は `load_workload` を stub 化し、throughput/abort/IPC を供給する。 |
   | `test_s8b_*` | `test_s8b_floor_campaign.py:9513–9555`、`test_s8b_oracle_driver.py:6291–6299` の実 runner 経路は固定の指標出力を使用する。その他の多数の経路は5 repsの測定 stub。今回の異値偶数集約を固定する反例は確認できない。 |

   **成果物への影響:** 周辺テストが緑でも、今後の偶数測定における abort の変更や screening 到達集合の変更まで不変とは証明しない。

   **推奨: scope 外。** screening の追加テストは親裁定どおり本件へ追加しない。上表は静的見込みであり、受入全走の代替にはしない。

7. **refuted — anchor の多重一致・M6 の両経路置換・M8 の集約値非等価。**

   **根拠:** JSON の各 `old` を現物文字列で照合した結果、**全8件が各1回一致**した。

   | 変異 | 一致位置 |
   |---|---|
   | M1 | `runner.py:818` |
   | M2 | `runner.py:820` |
   | M3 | `runner.py:818` |
   | M4 | `runner.py:810` |
   | M5 | `runner.py:812` |
   | M6 | `runner.py:1300` |
   | M7 | `digest.py:65` |
   | M8 | `runner.py:805` |

   M6 は `point.` を含み、deferred の `pt.`（`:1072`）には一致しない。M8 は内部の tuple list に対して、同じ順序・同じ要素参照の list を直ちに生成するため集約値は等価。

   ただし **ソース bytes は等価ではない**。作者報告の `contract-loader-drift` のような HEAD 束縛が変異実走でも発生するかは未実測。M8 の値等価性から、ソース認証を含む全 suite の無条件 SURVIVED までは導けない。

   `mutation-spec-probe.json:17–18` 等の空 expected_nodes／SURVIVED は、指定どおり probe 用と理解する。M1〜M7の正式期待値ではない。

   **成果物への影響:** ソース束縛拒否を集約の検出力として数えると、変異台帳の感度証拠が過大になる。

   **推奨: nit。** 親の実走では対象 assert による赤と admission 拒否を分離し、M8を正例として確認する。

## 変異ごとの期待 node

以下は値の断言に由来する赤の完全列挙。admission・環境失敗は含めない。

**M1**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_average_central_indicators[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_average_central_indicators[deferred]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[deferred]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[deferred]
```

**M2**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_average_central_indicators[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_average_central_indicators[deferred]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[deferred]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[deferred]
```

**M3**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[deferred]
```

**M4**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_odd_reps_preserve_legacy_values[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_odd_reps_preserve_legacy_values[deferred]
```

**M5**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[deferred]
```

**M6**

```text
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_average_central_indicators[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_even_reps_none_indicator_is_none[direct]
orchestrator/tests/test_calibrator.py::test_measure_point_parity_uses_valid_reps_not_requested[direct]
```

**M7**

```text
orchestrator/tests/test_critic.py::test_load_sorts_by_throughput_and_marginal_back_off
orchestrator/tests/test_critic.py::test_no_wait_axis_is_categorical_LT
orchestrator/tests/test_critic.py::test_load_workload_uses_committed_retry_attempt_only
orchestrator/tests/test_critic.py::test_load_workload_preserves_legacy_commit_without_build_attempt_id
orchestrator/tests/test_critic.py::test_digest_omits_latency_from_projection_table_and_axes
```

**M8**

```text
[]
```

## 総括

GO — レンズBの静的レビューでは must-fix なし。
M1〜M7の検出経路は成立し、M6は3つの direct node が赤になる。
M5の両ケースは反例になるが、実走では同一 node の最初の失敗で止まる。
M8は集約値について等価。ソース束縛拒否を変異検出として計上しないこと。
焦点走・変異 matrix・受入全走は未実測で、親による確認が残る。
