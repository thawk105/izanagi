## 必須 assertion の被覆表

静的確認では、裁定「設計 v2」6 の必須 assertion に未被覆はありません。

| 必須 assertion | 固定する test と assertion |
|---|---|
| 負例の 12 件、全 `ERROR`、exact reason、空 evidence、`effective=False` | `test_evaluator_exception_remains_fail_closed`、`test_s8c_cli_entrypoints.py:391-407`。特に件数 `:402`、status `:403`、evidence `:404,406`、reason `:405`、effective `:407` |
| plain/sibling report の `_jsonable` と digest が一致 | 同 test `:394-400`。値は fixture 内で `_jsonable` と `_activation_report_digest` を別々に取得している `:220-240` |
| normalize 側の 3 field | `test_evaluator_exception_reason_names_real_normalizer_failure`、`test_s8c_cli_entrypoints.py:410-419`。単体でも `test_default_registry_normalizer_exception_remains_fail_closed`、`test_s8c_preregistration_core.py:2634-2649` |
| evaluator 側 `RuntimeError` の 3 field | `test_default_registry_evaluator_runtime_error_is_structured`、`test_s8c_preregistration_core.py:2670-2685` |
| detail 非漏出 | `test_preregistration_exception_detail_is_not_copied_to_diagnostics`、`test_s8c_preregistration_core.py:2688-2706`。exact reason `:2699-2705`、detail 非包含 `:2706` |
| reason 欠落・非文字列・path・長過ぎ・hostile 属性の total 性と sentinel | `test_invalid_preregistration_reasons_use_bounded_sentinel_without_leaking`、入力 `test_s8c_preregistration_core.py:2709-2726`、12 件 fallback `:2737`、sentinel `:2738-2741`、非漏出 `:2742-2744` |
| hostile・非文字列・不正文字・長過ぎの exception type | `test_invalid_exception_type_uses_bounded_sentinel_without_leaking`、`test_s8c_preregistration_core.py:2747-2775` |
| 正常系の空診断 | `test_default_registry_success_has_no_diagnostics`、`test_s8c_preregistration_core.py:2778-2786`。full report 経路は `test_test_registry_success_has_no_diagnostics`、`:2830-2840` |
| 正常 CLI の空 stderr | `test_cli_entrypoint_matches_library_report`、`test_s8c_cli_entrypoints.py:309-388`、exact 空文字 `:388` |
| CLI の path/module、JSON/text、stdout bytes、終了値、stderr 1 JSON、traceback/path 非包含 | `test_evaluator_exception_cli_preserves_stdout_and_emits_one_diagnostic`、parameter `test_s8c_cli_entrypoints.py:422-429`、assertion `:460-467` |
| test-registry の evaluator/normalize 例外で非空診断 | `test_test_registry_exceptions_always_return_diagnostics`、`test_s8c_preregistration_core.py:2789-2827` |
| 既存 3 dataclass の field 集合 | `test_activation_and_predicate_report_field_sets_are_unchanged`、`test_s8c_preregistration_core.py:2595-2621` |
| sibling API に `registry` が無い | `test_production_entrypoints_do_not_accept_registry_injection`、`test_s8c_preregistration_core.py:3007-3012` |

## fixture が機構を通るか

CLI e2e fixture は目的の実機構へ到達します。

- temporary repo へ core・projection・contract をコピーし、11 件 evaluator を配置しています。`test_s8c_cli_entrypoints.py:155-172`
- それらを同じ temporary repo で commit し、core/evaluator/projection の各 commit blob と live bytes の一致を assertion しています。`:174-203`
- oracle subprocess は `cwd=repo_root` かつ閉じた環境で temporary repo の package を import します。`:207-262`
- CLI の module 形式も `cwd=repo_root`、path 形式は temporary repo の core file を直接起動します。`:438-458`
- path 起動では core が package root を `sys.path` へ追加し、同じ module object を正式名へ登録するため、evaluator が import する `core.PredicateResult` と `__main__` 側の型 identity も一致します。`s8c_preregistration.py:36-41`
- production 経路は core blob 照合 `s8c_preregistration.py:2005-2015`、`_default_registry_module` の live import と evaluator blob 照合 `:1837-1869`、projection blob 照合 `:1872-1907` を通り、最後に `_default_registry_results` へ到達します。`:2016-2034`
- evaluator は 11 件を返すため、実体の `_normalize_predicate_results` が `predicate-result-type` を送出します。`:1918-1948`

単体側も `_default_registry_results`、`_normalize_predicate_results`、診断 helper を stub していません。module 引数または test-registry の正規注入 seam に evaluator double を渡し、それ以降は実体を通しています。

例外は `test_non_json_cli_reports_decider_reason` です。`test_s8c_preregistration_core.py:3034-3038` で sibling API を `(report, ())` に stub しているため、この test 自体は診断機構を通りません。固定しているのは許可された seam 追随後の終了値と `decider_version` stdout 行だけです。`:3039-3043`

## 事前登録変異の検出可否 (M1〜M3・D1〜D8)

| ID | 判定 | 落ちる test/assertion |
|---|---|---|
| M1 | 検出する | `test_evaluator_exception_remains_fail_closed` の status assertion、`test_s8c_cli_entrypoints.py:403`。単体 helper の `test_s8c_preregistration_core.py:520` も落ちる |
| M2 | 検出する | 同 CLI test の exact reason assertion、`test_s8c_cli_entrypoints.py:405`。単体 helperでは `test_s8c_preregistration_core.py:521` |
| M3 | 検出する | raw 11 件が返るため同 CLI test の件数 `test_s8c_cli_entrypoints.py:402`、または単体 helper の `test_s8c_preregistration_core.py:518` |
| D1 | 検出する | `test_default_registry_normalizer_exception_remains_fail_closed` の診断 tuple equality、`test_s8c_preregistration_core.py:2643-2649` |
| D2 | 検出する | `test_default_registry_evaluator_runtime_error_is_structured` の exact 3 field、`test_s8c_preregistration_core.py:2679-2685` |
| D3 | 検出する | detail test の exact reason `test_s8c_preregistration_core.py:2699-2705`。`str(exc)` がそのまま入れば非漏出 assertion `:2706` も落ちる |
| D4 | 検出する | normalize literal へ統一すれば evaluator test `:2679-2685`、evaluator literal へ統一すれば normalizer test `:2643-2649` |
| D5 | 検出する | production 正常経路は CLI oracle の `diagnostics == ()`、`test_s8c_cli_entrypoints.py:282-285`。test-registry 側なら `test_s8c_preregistration_core.py:2840` |
| D6 | 検出する | `test_test_registry_exceptions_always_return_diagnostics` の exact 非空 tuple、`test_s8c_preregistration_core.py:2825-2827` |
| D7 | 検出する | stdout への混入、separator、改行のいずれも exact bytes assertion `test_s8c_cli_entrypoints.py:463` が落ちる |
| D8 | 検出する | `_HostileReason` または `_HostileType` で `SystemExit` が helper 外へ漏れ、`test_invalid_preregistration_reasons_use_bounded_sentinel_without_leaking` または `test_invalid_exception_type_uses_bounded_sentinel_without_leaking` が assertion 到達前に ERROR になる。これは assertion failure ではなく未処理例外による node failure |

登録済み 11 変異はすべて静的に検出可能です。

## 新しい生存変異

指定された 2 test file の現行入力では、次の変異が assertion を満たしたまま生存します。

| 変異 | file:line と内容 | 生存理由 |
|---|---|---|
| S1、totality 破壊 | `s8c_preregistration.py:1927` の `except Exception` を `except RuntimeError` に狭める | evaluator 直送 fixture がすべて `RuntimeError` またはその subclass。`ValueError` 等が未投入 |
| S2、totality 破壊 | `s8c_preregistration.py:1939` の normalize 側も `except RuntimeError` に狭める | 現在の normalize 負例は `PreregistrationError` と `RuntimeError` だけ。遅延 iterable の `TypeError` 等が未投入 |
| S3、診断無効化 | `s8c_preregistration.py:2337` で `callsite == "_normalize_predicate_results"` の診断だけ stderr に出す | real-process CLI 負例は normalize 側だけ。evaluator 側 CLI 診断を消しても単体 test は CLI を通らない |
| S4、虚偽診断 | `s8c_preregistration.py:1816` の `<= 128` を `< 128` にする | valid な 128 文字 reason が無く、短い正常値と 129 文字の異常値しかない |
| S5、虚偽診断 | `s8c_preregistration.py:1801` の exception type 長さ判定も `< 128` にする | 同じく 128 文字ちょうどの valid type がない |
| S6、安全性低下 | `s8c_preregistration.py:68` の reason charset に `_` を追加する | 不正文字 test は slash の path だけで、`fixture_reason` のような単一不正文字を固定していない |

- 所見 1 (深刻度: must-fix): evaluator と normalize の捕捉対象が `RuntimeError` family に狭まる変異 S1/S2を殺せません。`ValueError` を直接送出する evaluator と、materialize 中に `TypeError` を送出する遅延 iterableについて、12 件の exact fallback と診断を確認する assertion が不足しています。  
  放置時の成果物影響: 対象例外では fail-closed report 自体が返らず、certified 選択と台帳への参照値を「拒否」として生成できなくなります。

- 所見 2 (深刻度: must-fix): real-process CLI が evaluator 側 callsite を一度も通らないため、S3の選択的な診断無効化が生存します。live evaluator が `RuntimeError` を直接送出する CLI fixture と、exact evaluator-side stderr assertion が不足しています。  
  放置時の成果物影響: 受理集合と report 値は同じでも、evaluator 直送例外の診断成果物が消え、拒否理由への参照が欠落します。

- 所見 3 (深刻度: must-fix): 長さ上限の inclusive 境界と reason charset の拒否境界が固定されておらず、S4〜S6が生存します。128 文字ちょうどを exact 値として受理する assertion、129 文字を sentinel にする assertion、および underscore 等を sentinel にする assertion が必要です。  
  放置時の成果物影響: certified 選択と report digest は不変でも、診断成果物の値が正しい reason/type から sentinel へ変わるか、不許可の外部文字列が診断へ混入します。

## 偽緑の経路

- temporary path は期待値へ焼き込まれておらず、むしろ stderr 非包含を `test_s8c_cli_entrypoints.py:467` で確認しています。
- 時刻依存値はありません。
- temporary commit hash は動的ですが、通常 CLI test は実引数の commit と出力を `:383` で照合しています。
- malformed fixture は「現行 hash literal」を差し込まず、現行 bytes を temporary repo に commitして blob/live 一致を作っています。これは `_default_registry_module` を越えるために必要な構成です。対象 4 ファイルは現在 commit `134e5926d` と一致しています。
- malformed stdout の期待値は plain API の report から `test_s8c_cli_entrypoints.py:223-250` で構築する自己参照型です。そのため歴史的な stdout golden ではありません。ただし CLI formatter は別実装で再構築され、exact bytes `:463`、plain/sibling report と digest `:397-400` が別途固定されるため、D7 は検出します。
- `all()` は前段の件数 assertionにより空集合ではありません。CLI 負例は `:402`、単体 helper は `test_s8c_preregistration_core.py:518` で 12 件を先に固定しています。
- totality test は結果と sentinel まで検査しており、「例外が出ないだけ」の test ではありません。

## 既存テストの弱体化

commit 差分で、既存 assertion の変更・反転・緩和・skip・削除はありません。

既存行の実質変更は次の 2 件です。

- 正常 oracle が sibling API を呼ぶようになり、空診断と従来 API report との equality を純増しています。`test_s8c_cli_entrypoints.py:282-286`
- 裁定で許可された `test_non_json_cli_reports_decider_reason` の monkeypatch seam だけを sibling API と `(report, ())` へ追随しています。stdout と終了値の期待は維持されています。`test_s8c_preregistration_core.py:3034-3043`

`s8c_preregistration_evidence.py` は commit で変更されていません。

## 新規 test node の副作用

- 新規 test file はありません。既存 2 test file への追記だけです。
- CLI 側は 6 node、core 側は 18 node、合計 24 node の純増です。
- fixture 自体は node を増やしません。
- core file 末尾の自走入口 `raise SystemExit(pytest.main([__file__]))` は `test_s8c_preregistration_core.py:3701-3702`。既存 CLI file の形式 `test_s8c_cli_entrypoints.py:470-471` と一致し、pytest collection node にはなりません。
- file 一覧を増やしていないため file-list 前提への構造的影響はありません。受入所要台帳や外部 meta-test の実体は必読射影に含まれないため、その実走結果は確認していません。

## scope 外の所見

所見なし。

## 総括

静的レビュー結果は blocker 0、must-fix 3、nit 0 です。必須 assertion と事前登録 M1〜M3・D1〜D8 はすべて検出可能で、CLI fixture も live import・blob 照合・実 normalizer を通ります。

ただし、登録外の生存変異が 6 件あり、特に非 `RuntimeError` の fail-closed totalityと evaluator-side CLI 診断が未固定です。したがって、現時点ではテスト感度について受理せず、所見 1〜3を must-fix と判定します。pytest は実走しておらず、実走結果を緑とは扱っていません。