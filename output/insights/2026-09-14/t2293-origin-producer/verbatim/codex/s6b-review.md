## 総括

`57eeaad54` の静的レビューでは、blocker / must-fix は検出しませんでした。nit は duration 台帳の未登録 1 件です。pytest・収集・baseline 再計算は実行していません。

以下、`A` は `orchestrator/campaign/p3_autonomous_workload_trial.py`、`T` は `orchestrator/tests/test_p3_autonomous_workload_trial.py` を指します。

## 削除 field の参照残り

production・test・tools・実行可能資材を検索し、削除 field を通常実行で参照する残骸は見つかりませんでした。

残っている削除 field 指定は、すべて `TypeError` を期待する新規 negative test です。

| 参照 | 箇所 | 判定 |
|---|---|---|
| `evidence_path=` | `T:11498` | `T:11497` の `pytest.raises(TypeError)` 内 |
| `evidence_root=` | `T:11507` | `T:11506` の `pytest.raises(TypeError)` 内 |
| `result_record_bytes=` | `T:11509` | `T:11508` の `pytest.raises(TypeError)` 内 |

`orchestrator/campaign/reflux_origin_topology.py:411` の `material.evidence_path` は削除対象ではありません。同ファイル `:126` の `MemberRecoveryMaterial` に属し、`:132` に field が残っています。

`A:1936` と `A:1937` は formal consumer の引数であり、削除された producer field の参照ではありません。

## 共有 fixture・helper への波及

`_origin_public_inputs` の直接利用は次の 10 test 関数です。各行は関数定義位置です。

| test 関数（すべて `T`） | 行 | 静的判定 |
|---|---:|---|
| `test_registered_slot_is_reserved_before_first_performance_observation` | 8996 | 予約・envelope・観測の順序検査に削除 field 依存なし |
| `test_origin_public_path_preserves_capability_identity_and_projects_terminal` | 11042 | runtime 配下の物理証拠・envelope・terminal 照合と整合 |
| `test_origin_client_omission_is_typed_preflight_before_production_resolution` | 11196 | client 欠落の preflight 拒否に影響なし |
| `test_origin_producer_arm_must_match_issued_capability_and_closed_arm_set` | 11222 | `enforcement_arm` の置換・拒否条件に影響なし |
| `test_origin_arguments_are_all_or_none_before_artifact_creation` | 11259 | 引数対の検査に影響なし |
| `test_origin_request_rejects_unregistered_exploratory_admission` | 11279 | admission 拒否に影響なし |
| `test_origin_public_result_distinguishes_partial_from_completed` | 11304 | completion wrapper が証拠を保存・封印するため収集可能 |
| `test_origin_envelope_create_failure_is_preflight_and_pre_observation` | 11324 | 証拠収集前の envelope 書込み失敗を検査 |
| `test_origin_post_lifecycle_observation_failure_returns_reported_partial` | 11371 | 観測開始失敗の partial 分岐に削除 field 依存なし |
| `test_origin_runtime_collects_only_producer_owned_evidence` | 11461 | materialize・seal 後に変異し、本体の収集を検査する構造 |

間接利用は `orchestrator/tests/test_reflux_originless_compatibility.py:1252` の `test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set` です。同ファイル `:1261` → `_origin_enabled_bundle` → `:134` の順で helper を呼びます。もう一つの test（`:1239`）は origin helper を使いません。

共有 helper の連鎖は `T:10935`、`:10992`、`:11006`、`:11009`。`T:10693` で導出 path に保存した raw bytes を返し、`:11013` で同じ bytes を封印へ渡してから `:11016` で completion を呼びます。今回の保存先変更による参照切れは検出しませんでした。

## originless 経路の不変

変更された処理へ入る入口は origin 有無で分岐しています。

- `A:4872` で runtime は `None`、`:4875` の origin request がある場合だけ prepare。
- `A:4941` の origin 分岐内だけで envelope を導出。
- `A:3842` の origin 分岐内だけで証拠を収集。

したがって、この差分から originless の report bytes・材料レポート・試行台帳・受理集合を変える実行経路は見つかりませんでした。互換 test は `orchestrator/tests/test_reflux_originless_compatibility.py:1258` で省略指定、`:1260` で明示 `None`、`:1264` と `:1265` で比較します。実際の bytes 一致は未実測です。

## 凍結 artifact への影響

baseline entry の再計算・更新を必要とする依存変更は検出しませんでした。

`orchestrator/tests/test_reflux_origin_fixture_builder.py:25` の固定対象は 7 builder で、`:112` がそれぞれの出力 digest・長さを照合します。今回変更した supervisor helper は対象に含まれません。

`orchestrator/tests/reflux_origin_fixture_builder.py:572` の fixture path は既に `origin/batch/query.json` 形式です。今回の変更は `T:10693` の runtime 向け materialization にあり、凍結 builder の出力生成には入りません。`reflux_origin_fixture_baseline.json:19` の recovery envelope entry を含め、変更理由はありません。

## meta-test と受入台帳

次の検査を確認しました。

| 検査 | 根拠 | 今回の影響 |
|---|---|---|
| pytest 収集設定 | `orchestrator/tests/test_pytest_collection_config.py:175` | 設定キー・testpaths を検査。既存ファイルへの関数追加は対象外 |
| plain runner 被覆 | `orchestrator/tests/test_plain_runner_coverage.py:60` | ファイル単位。`T:11454` の `pytest.main` が再収集するため、その後に追加した関数も対象になる |
| duration schema・件数整合 | `orchestrator/tests/test_update_acceptance_duration_ledger.py:306` | 台帳内部の整合を検査。全 test の登録義務ではない |
| suite node 集合固定 | 同ファイル `:329`、`:364` | 固定対象に今回の test ファイルは含まれない |
| 実収集との台帳被覆 | `orchestrator/tests/test_acceptance_schedule_order.py:660`、`:712` | 全収集の **90% 以上**が必要 |

新設 2 関数は parameter 展開で **9＋14＝23 ケース**です。`orchestrator/tests/acceptance_duration_ledger.json` に両 test の entry はありません。

**個々の新規 test 全件を登録せよ、という検査は見つかりませんでした。** 要求は全収集に対する 90% 被覆です。未登録分はその分母を増やします。全収集を実行していないため、追加後も閾値以上かは断定しません。

## import と schema 互換

循環 import の新設は検出しませんでした。`A:43` は以前から formal consumer を import し、その consumer は `orchestrator/campaign/reflux_formal_consumer.py:46` で result evidence を import しています。今回の `A:48` より前に存在する依存です。`reflux_result_evidence.py:25` から始まる import 節に supervisor への逆 import はありません。

path は `A:1350` と `orchestrator/campaign/reflux_result_evidence.py:966` が同じ形式です。token 検査も同じ関数を使用します。

- topology の相対 path 制約：`orchestrator/campaign/reflux_origin_topology.py:116`
- member path の相異制約：同 `:371`
- 導出 envelope の保存・digest 計算：`A:4967`、`:4974`
- consumer の disk bytes・digest・canonical envelope 照合：`orchestrator/campaign/reflux_formal_consumer.py:407`、`:411`、`:415`

path 値が変われば envelope digest も変わりますが、新規 envelope から計算して照合する連鎖に古い固定値は見つかりませんでした。

## blocker / must-fix / nit の一覧

- **blocker：0 件**
- **must-fix：0 件**
- **nit：新規 23 ケースの duration 未登録。** 根拠：`T:11461`、`T:11586`、`orchestrator/tests/test_acceptance_schedule_order.py:712`。放置すると台帳被覆率が下がり、未知 duration の実行順計算を受けるが、certified 選択・材料レポート・試行台帳の値や受理集合が変わる根拠はない。

## 判定 (採用可 / 要 fix / 差し戻し)

**採用可。** レンズ B の静的読解で採用を止める不整合は検出しませんでした。テスト成功・全収集の duration 被覆率は未確認です。