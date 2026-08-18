# 所見

### A-01 空の canonical container が validator を素通りする

深刻度: should-fix  
file:line: `orchestrator/campaign/s8c_preregistration.py:819, 862-864`  
再現できる入力: `{}`
  
`{}` は `json-empty-container` として `UNFILLED` になり、`FILLED` の場合だけ実行される validator に届かず、`root-keys` も出ない。裁定 E が「UNFILLED は制約対象外」と明示するなら仕様境界だが、8b の exact schema を全 canonical JSON に要求するなら素通しである。未修正時は、空 object を置いた変更が repo の受理集合に残る。現行の `UNFILLED` 判定では直ちに発効・台帳化はしないが、将来の consumer 変更時に未検証値が発効入力へ流れる。

非空の `FILLED` 値については、bool、入れ子、重複 key、全角・半角、NFC 非正規形、指数表記、各範囲分岐とも静的には素通ししない。`sd_max=-0.0` は受理され、`delta_min=-0.0` は `delta-min-range` になる。`ActivationReport` と digest の変更もない。

# 恒真性の評価

`orchestrator/tests/test_s8c_preregistration_invariant.py:597` の `test_living_doc_section5_value_violations_are_empty` は、当該欄が `未記入` である限り validator を呼ばないため、validator 呼び出し削除、各分岐の弱体化、違反 tuple の常時空化では緑のままである。

検出できるのは、生きた doc の値が非 `UNFILLED` になる変更、または実際に violation が発生する変更だけである。`{}` のような canonical empty container への変更すら `UNFILLED` のまま検出しない。これは恒真に近い保護であり、should-fix。

`_parse_filled_section5_value` の再 parse が失敗する条件は、現行の分類と同じ code span・strict JSON 検査を通った `FILLED` 値からは到達不能である。仮に到達すれば例外で parse を止めるため fail-closed になる。

# 単一理由性の評価

`test_section5_iteration_contrast_reports_all_value_violations` (`orchestrator/tests/test_s8c_preregistration_core.py:1414`) は、次の4軸を同時に壊す過剰決定 fixture である。

再現できる入力: `{"H1":{"delta_min":1,"direction":"on-minus-off","n":true,"sd_max":0,"unit":" "},"H2":{"delta_min":0,"direction":[],"n":2,"sd_max":0,"unit":"ops_per_second"}}`

`H1.n`、`H1.unit`、`H2.delta_min`、`H2.direction` が同時に違反する。集約動作のテストとしては妥当だが、単一変異の kill 根拠や台帳には使えない。未修正時は本番の受理集合は変わらず、mutation ledger の原因帰属だけが過大・不明確になる。

# 総括

非空の `FILLED` canonical JSON に対する指定制約の fail-open は見つからない。  
唯一の境界反例は `UNFILLED` 扱いされる空 container である。  
`sd_max=-0.0` 受理と `delta_min=-0.0` 拒否は仕様どおりである。  
生きた doc テストは validator の実効性を単独では保証しない。  
pytest は実走せず、以上は静的レビューのみである。