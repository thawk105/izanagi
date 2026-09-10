# レンズ B（回帰と波及）レビュー

結論は **must-fix 0、should-fix 0、nit 2** です。現行の成果物値・受理集合・参照を変える回帰は静的には見つかりませんでした。

## 所見

[severity: nit] [攻撃シナリオ] 実装は互換だが、テストは `REGISTRY` の反復順序と `lookup()` の完全な例外 message を固定していない。`set(ec.REGISTRY)` は順序を捨て、未知入力テストは例外型しか確認しないため、将来同じ key set の並べ替えや文言変更が入っても検出できない。[根拠 `orchestrator/tests/test_env_contract.py:281-289,359-363,559-565`; `orchestrator/campaign/env_contract.py:375-382`] [提案] `list(ec.REGISTRY) == ["linux-baremetal", "pegasus"]`、`sorted(ec.REGISTRY)`、未知 tag と非 hashable 入力の完全な `str(exc)` を追加で pin する。

[severity: nit] [攻撃シナリオ] s8c の `lookup` 反射依存は active gate ではない。`_evaluate_c12()` は environment AST の `lookup` FunctionDef と workload supervisor の reachable call `lookup` を要求するが、C12 は `machine_checkable: false` であり、通常 dispatch は `_evaluate_undefined()` に入り当該述語を実行しない。さらに call 条件の対象は `env_contract.py` 自身ではなく workload supervisor で、現行 `p3_autonomous_workload_trial.py` には `lookup` call がない。今回 `lookup` FunctionDef は温存されているため回帰ではないが、「s8c test が削除を機械的に止める」とは数えられない。[根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:575-595,621-627,699-707`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:430-486`; `orchestrator/tests/test_s8c_preregistration_predicates.py:98-130,379-385`; `orchestrator/campaign/p3_autonomous_workload_trial.py:37-123,1685-1913`] [提案] この wave では scope を広げず、温存理由を「凍結 evidence contract の参照互換」と表現する。active 防壁化は別 wave で直接 AST test を置くか、裁定後に C12 を machine-checkable 化する。

## `lookup()` / `REGISTRY` の後方互換

| 観点 | 静的確認 |
|---|---|
| 値型 | `REGISTRY` の値は引き続き exact `ExecutionEnvironmentContract`。wrapper は返らない。 |
| 同一性 | `REGISTRY[tag] is GENERATIONS[tag][-1].contract` かつ `lookup(tag)` はその同じ object を返す。`orchestrator/campaign/env_contract.py:341-344,375-378` |
| 内容 | 両 env の全 field と contract hash は変更前と同一。`orchestrator/campaign/env_contract.py:236-275`; `orchestrator/tests/test_env_contract.py:68-75,1003-1032` |
| 型 | `REGISTRY` は引き続き `MappingProxyType`。`orchestrator/campaign/env_contract.py:341-344` |
| 反復順序 | 変更前後とも `linux-baremetal`、`pegasus`。新しい内包表記は `GENERATIONS.items()` の同じ挿入順を保存する。 |
| `sorted(REGISTRY)` | 前後とも `["linux-baremetal", "pegasus"]`。 |
| 例外 | `lookup()` 本体は変更されておらず、未知・非 hashable key は同じ `EnvContractError` と完全に同じ message。`orchestrator/campaign/env_contract.py:375-382`; `0324d627^:orchestrator/campaign/env_contract.py:202-209` |

production 21 call はすべて差分対象外で、consumer の型期待とも整合しています。

- `tools/pegasus/probes/t419_probe_causality.py:3396`
- `orchestrator/qualification/t126_driver.py:496,868`
- `orchestrator/campaign/s8b_floor_campaign.py:313,412,1874,2755`
- `orchestrator/campaign/s8b_oracle_driver.py:762`
- `orchestrator/campaign/s8b_oracle_report.py:1202`
- `orchestrator/campaign/s8b_ratified_freeze.py:960,1803,2287,2880`
- `orchestrator/campaign/silo_ladder_rung1.py:1936,3534,3752,4433`
- `orchestrator/campaign/pipeline.py:535`
- `orchestrator/campaign/loop.py:72`
- `orchestrator/campaign/pegasus_floor_scoping.py:75`
- `orchestrator/campaign/p3_s4_loop_trigger_gating.py:95,324`

production に `REGISTRY` の直接 reader はありません。直接反復するのは `test_env_contract.py:590,708,741,810,814` で、値 object と順序はいずれも維持されています。

## 初期化・leaf 性・scope・受理集合

`validate_generations(GENERATIONS)` は import 時に実行されますが、現行二列はいずれも exact tuple、g1、key/env 一致、hash 非重複、長さ 1 なので、静的には `EnvContractError` 分岐へ入りません。将来の不正 g2 で全 importer を import 失敗させる挙動は、裁定された bootstrap fuse そのものです。`orchestrator/campaign/env_contract.py:278-340`

leaf 性も維持されています。追加 import は stdlib の `typing.Mapping` だけで、campaign 内 import はありません。`orchestrator/campaign/env_contract.py:19-27`

scope 外の `CurrentContract`、`HistoricalContract`、consumer 移行、`lookup()` 削除、activation/receipt 実装はありません。`activation record / activation receipt` は拒否理由の文字列とそのテストにだけ現れ、実体・発行・台帳書込みは追加されていません。`orchestrator/campaign/env_contract.py:314-318`; `orchestrator/tests/test_env_contract.py:469-483`

受理集合も次のとおりです。

- `lookup()` の dict-key 等価性を含む成功入力、未知入力、例外型・message は前後同一。
- `load_verified_calibration()` は未変更。`mode=none` は引き続き grandfathered SHA だけを受理します。`orchestrator/campaign/env_attestation.py:799-873`
- generic successor が新 path/SHA を許しても loader は拒否する非対称性が固定されています。`orchestrator/tests/test_env_contract.py:712-725`
- `ExecutionEnvironmentContract` と `_canonical_obj()` は無変更なので、`dataclasses.replace(ec.lookup(...))` は引き続き raw contract を返します。

## 回帰する可能性のある既存テスト

**静的に回帰が予測される既存テストは 0 件**です。機序は以下です。

- `test_buildcache_v2.py:35-39,129-140` は変更されていない raw contract class を直接生成する。
- `test_execution_guard.py:34-35` の fixture は従来どおり raw contract を返す。
- `test_s8b_floor_campaign.py:620-628,1399-1407` の synthetic contract と `dataclasses.replace()` は wrapper 化されていない。
- `test_p3_s4_loop_trigger_gating.py:334-348,476-481,510-526` の `_lookup is env_contract.lookup` と raw contract replacement は維持される。
- `test_s8b_oracle_driver.py:2295-2300,2369-2381` の `env_contract is ec.lookup(...)` は、繰返し lookup が同じ `REGISTRY` value object を返すため維持される。
- s8c の現行 snapshot は C12 を `EVIDENCE_UNDEFINED` と期待しており、今回 evaluator・contract・workload supervisor は変更されていない。

## 最初に赤くなる候補

全走で赤が出た場合の局在候補であり、失敗を予測しているものではありません。

1. `orchestrator/tests/test_env_contract.py:325-363,486-538,559-565` — 新世代列、resolver、identity、MappingProxy を直接検査する。
2. `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:334-348,476-481,656-670` — import 時の function identity と contract object identity に最も強く依存する。
3. `orchestrator/tests/test_s8b_oracle_driver.py:2295-2300,2369-2381` — lookup の返り値 object を `is` で検査する。

pytest は実走しておらず、緑とは判定していません。

## 総括

- must-fix / should-fix は 0。既存 consumer の値・型・同一性・受理集合を変える経路は見つからない。
- 最も重い所見は、反復順序と完全な例外 message がテストで未固定な点だが、現行実装自体は互換。
- 次点は、s8c の反射述語が dormant であり active 防壁ではない点。今回の `lookup` 温存は成立している。
- scope 外機能の実装、consumer 移行、leaf 性破壊はない。
- レンズ B としては、上記 nit を記録したうえで親の計算ノード受入全走へ進める状態。