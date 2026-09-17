## 変更の要約 (file:line)

編集は `orchestrator/tests/test_ccbench_spawn_sites.py` のみ。commit は作成していません。

- 1225行: 例外名・組込み catcher と前提コメント。
- 1580行: module の import・ClassDef 情報収集。
- 1610行: check の3要素化、scope ごとの stack 初期化。
- 1728行: `_injected_check_unswallowed`。
- 1835行: R0 の記録制限。
- 1981行: Try の位置別 stack 管理。
- 2302行: `and unswallowed`。
- 3043行以降: synthetic 19例と production pin。

## 規則の実装 (R0〜R4 と裁定の対応)

| 規則 | 実装 |
|---|---|
| R0 | `call is returned_evidence_call` の場合だけ `(lineno, result_name, unswallowed)` を記録 |
| R1 | body・handler・orelse を push、`finally` で必ず pop。当該 finalbody は積まず、scope ごとに空へ初期化 |
| R2 | 全 stack の TryStar と finalbody の Return／Break／Continue を変換停止より先に検査 |
| R3 | MAYBE→DEFINITE→NONE の優先順位、tuple 集約、再束縛、handler の脱出・末尾 Raise、bare／変換の追跡を実装 |
| R4 | 既存一致条件へ bool を AND。限定保証と未検査範囲をコメント化 |

脱出走査は自前の再帰走査で、FunctionDef／AsyncFunctionDef／ClassDef／Lambda に入りません。前提の追加 assert、alias chain、campaign 専用判定の変更はありません。

## 追加した test (nodeid と期待値)

以下の nodeid はすべて `orchestrator/tests/test_ccbench_spawn_sites.py::` が接頭辞です。

`test_define_sink_cross_product_t2491_accepts_injected_reraise[ID]`:

- `p1-no-try`
- `p2-bare-reraise`
- `p3-conversion`
- `p4-s1-handlers`
- `p5-outer-reraise`
- `p6-handler-position`
- `p7-raise-as-name`

各例で sink 集合の完全一致、`Counter({"covered": 1})`、`failures == []` を要求します。

`test_define_sink_cross_product_t2491_rejects_injected_swallow[ID]`:

- `n1-error-pass`
- `n2-bare-pass`
- `n3-exception-return`
- `n4-conditional-raise`
- `n5-unreachable-raise`
- `n6-finally-return`
- `n7-unknown-handler`
- `n8-lambda`
- `n9-system-exit`
- `n10-try-star`
- `n11-outer-swallow`
- `n12-local-rebinding`

各例で sink 集合の完全一致、`Counter({"failure-reachable": 1})`、`[("BACKOFF_FIXED", sink, "reachable")]` を要求します。n10 は Python 3.11 未満では skip します。

`test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered` は、指定4 sink に `Counter({"covered": len(patch_sources)})` を要求します。

## 実走結果 (nodeid・件数、または「実装済み・未実走」と理由)

**実装済み・未実走。** 次を実行しましたが、テスト子プロセスは起動していません。

```text
python3 tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py
```

非帰属エラー本文:

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
[Pegasus dispatch] receipt を /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/output/pegasus-dispatch/9811ee213d312adb3701ad04286787f8/receipt.json へ保存しました (child rc=16)
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

実走 node 数は **0**。静的に数えた対象は **67 node（追加20）** です。AST 構文確認、ASCII parameter ID 確認、`git diff --check` は通りました。

台帳 exact／live sink 数、process inventory exact、calibration call-site 数、T2155 の分類・行番号 pin、T2520 の台帳除去検査を洗い出しました。全ファイル走に含めましたが、いずれも未実走です。親の全走・変異走を代替しません。

## production 4 check の当て直し

| sink → check | 規則の適用 |
|---|---|
| n_pilot 997 → 1018 | 1017-try の S1DriverError が DEFINITE。PilotError への変換で停止 |
| s8b driver 1788 → 1801 | 1730-try の WAL tuple は MAYBE bare、S1DriverError は DEFINITE 変換。1660 の handler 追跡前に停止 |
| s1 1208 → 1218 | 1204-try: WAL は MAYBE bare、子 class は NONE、DriverError は DEFINITE bare。1151-try に脱出 finalbody なし |
| s1 1288 → 1295 | 1279-try の WAL／DriverError を通り、1204→1151 を同様に追跡 |

既存 `_potentially_bound_names` による静的確認で、`run_role`／`run_block`／`build_binaries` と `{DriverError, S1DriverError, _SortSwoOracleRejected}` の束縛名交差はすべて空でした。global／nonlocal との交差も空です。

helper の明示 raise 8箇所はすべて `DriverError(...)`。これは前提確認であり、新しい gate にはしていません。

## 波及の静的列挙

- `returned_evidence_checks` の変更箇所は宣言1610行・書込み1842行・読取り2303行の3箇所。
- Try 分岐の変更は `_PythonGateFlow` が解析する全 scope に及びます。既存の flow 入出力・継続判定は維持しています。
- consumer は閉包検査、T2155 分類、T2520 台帳除去、新 production pin。floor の既存 injected sink にも判定は及びますが、繰延べ台帳は不変です。
- `_GateFlowState.returned_evidence_names`、`_campaign_checked_root`、共有 fixture、既存 test 全件は AST 比較で不変でした。
- 所有外の n_pilot test は、親が M1 の production 変異を実行する際の consumer です。本実装から production への実行時変更はありません。

## 変異 matrix の anchor (M0〜M7、old/new 文字列、期待 node)

以下は Python 文字列リテラルです。`\n` は LF、末尾 LF を含みます。全 old が対象ファイル内で **1箇所**に一致することを確認しました。変異実走はしていません。

M1 以外の対象は編集した test file です。

**M0 — 等価コメント。期待赤なし。**

```python
old = '        if matching_checks:\n            # Explicit helper rejection E is reraised by its first catcher;\n'
new = '        if matching_checks:\n            # Explicit helper rejection E is reraised by the first catcher;\n'
```

**M1 — `orchestrator/campaign/s8b_oracle_n_pilot.py`。**

```python
old = '            except S1DriverError as exc:\n                raise PilotError(f"build condition evidence rejected: {exc}") from exc\n'
new = '            except S1DriverError:\n                pass\n'
```

期待赤は裁定の7 node:

- `test_s8b_oracle_n_pilot.py::test_injected_build_fn_without_condition_records_is_rejected`
- `test_s8b_oracle_n_pilot.py::test_build_binaries_uses_binding_flags_and_prepared_records_independently`
- `test_s8b_oracle_n_pilot.py::test_r33_successor_protocol_document_loads_from_repository`（冗長 gate）
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member`
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly`
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal`
- `test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered`

いずれもパス接頭辞は `orchestrator/tests/` です。

**M2 — bool 恒真化。**

```python
old = '                self.returned_evidence_checks.setdefault(scope, []).append(\n                    (call.lineno, result_name, self._injected_check_unswallowed(scope))\n                )\n'
new = '                self.returned_evidence_checks.setdefault(scope, []).append(\n                    (call.lineno, result_name, True)\n                )\n'
```

期待赤: 新負例の **n8 以外**。n8 は R0 で記録されないため、この変異だけでは赤になりません。n10 は対応 Python でのみ対象です。

**M3 — bare handler を NONE に変更。期待赤: `n2-bare-pass`。**

```python
old = '            if exception_type is None:\n                return "definite"\n'
new = '            if exception_type is None:\n                return "none"\n'
```

**M4 — 末尾 Raise を内部の Raise へ緩和。期待赤: `n4-conditional-raise`。**

```python
old = '                if not handler.body or not isinstance(handler.body[-1], ast.Raise):\n                    return False\n                raised = handler.body[-1].exc\n'
new = '                raises = [item for item in region_nodes(handler.body) if isinstance(item, ast.Raise)]\n                if not raises:\n                    return False\n                raised = raises[-1].exc\n'
```

n5 は先行する `has_escape(handler.body)` が拒否するため、この変異だけでは赤になりません。

**M5 — finally 脱出検査を除去。期待赤: `n6-finally-return`。**

```python
old = '        if any(has_escape(node.finalbody) for node, _ in self.injected_try_stack):\n            return False\n'
new = '        if False:\n            return False\n'
```

**M6 — 文の値に限る記録制限を除去。期待赤: `n8-lambda`。**

```python
old = '            if (\n                call is returned_evidence_call\n                and name.endswith("require_returned_condition_evidence")\n            ):\n'
new = '            if (\n                name.endswith("require_returned_condition_evidence")\n            ):\n'
```

**M7 — 変換先 ClassDef 制限を除去。期待赤: `n9-system-exit`。**

```python
old = '                    elif name in self.module_class_counts:\n                        if kind == "definite":\n'
new = '                    elif True:\n                        if kind == "definite":\n'
```

M2〜M7 の短縮 ID はすべて `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2491_rejects_injected_swallow[ID]` を指します。期待赤集合の確定には親の probe が必要です。

## 総括

指定1ファイルに R0〜R4、synthetic 19例、production pin を実装しました。**dispatch 障害により未実走で、closed ではありません。** 親への引継ぎ事項は全走、Python 3.11 以降での n10、M2／M4 の期待集合補正と変異 probe です。