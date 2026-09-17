## 変更の要約 (file:line)

編集は [orchestrator/tests/test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py) のみ。commit は作成していません。

| 行 | 変更 |
|---|---|
| 1751 | R3b：字句的親関数・全種類の引数を局所束縛集合へ追加 |
| 1805 | R3c：as 名が handler body で再束縛される場合を拒否 |
| 1813 | R3a：変換先の ClassDef 件数・module／局所再束縛を検査 |
| 2329 | 保証限界コメントを補足 |
| 3125、3265、3298 | p8、n14、n13／n15〜n17 を追加 |

既存テスト本体・既存 parameter の source／期待値／id は、修正前 HEAD との AST 比較で不変です。

## R3a〜R3c と comment の実装

- **R3a:** 変換先は `module_class_counts[name] == 1`、`module_assignments` に不在、`local_names` に不在の全条件を要求します。不成立なら変換として受理しません。
- **R3b:** `_lexical_scopes(scope)` の `<module>` 以外について、body の `_potentially_bound_names`、posonlyargs／args／kwonlyargs／vararg／kwarg を集約し、`global_nonlocal_names` と合わせました。
- **R3c:** `raise <as名>` は、その名前が `_potentially_bound_names(tuple(handler.body))` に含まれない場合だけ bare 扱いにします。
- **comment:** 型名・as 名の束縛検査の範囲、finalbody 内 check の未追跡、変換後の外側処理、MAYBE の未変換経路、with／guard／結果名再束縛、Python 3.10 での TryStar 未実走を明記しました。

## 追加した test (nodeid と期待値、各 1 理由の根拠)

nodeid の共通接頭辞は `orchestrator/tests/test_ccbench_spawn_sites.py::` です。以下の略記を使います。

```text
A = test_define_sink_cross_product_t2491_accepts_injected_reraise
S = test_define_sink_cross_product_t2491_rejects_injected_swallow
R = test_define_sink_cross_product_t2491_rejects_injected_rebinding
```

| nodeid | sink 行 | 期待値・単一理由 |
|---|---:|---|
| `A[p8-known-child-handler]` | 8 | covered。n7 と同じ handler 列で、module ClassDef の ChildError は NONE |
| `R[n13-local-rebound-conversion]` | 7 | reachable。局所再束縛した X は MAYBE なので変換を拒否 |
| `S[n14-try-star-reraise]` | 6 | reachable。bare 再送出自体は適法で、TryStar 規則だけが拒否 |
| `R[n15-module-rebound-conversion]` | 8 | reachable。module 再代入された PilotErr を変換先として受理しない |
| `R[n16-argument-rebound-handler]` | 7 | reachable。引数 ChildError を NONE として読み飛ばさない |
| `R[n17-rebound-as-name]` | 7 | reachable。再束縛された exc の送出を bare と認めない |

正例は `Counter({"covered": 1})` と `failures == []`、負例は `Counter({"failure-reachable": 1})` と `[("BACKOFF_FIXED", sink, "reachable")]` を要求します。全例で sink 集合も完全一致を要求します。

n14 の skipif は既存 n10 と同一です。n13・n15〜n17 は独立した parametrize に置き、既存負例グループの source 構成を保持しました。

## 実走結果 (nodeid・件数、または「実装済み・未実走」と理由)

**実装済み・未実走。実走 nodeid はなし、実走件数は0です。**

指定コマンドを実行しました。

```text
python3 tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py
```

非帰属エラー本文：

```text
警告: 受入形でない走行です。この結果を受入全走として扱わないでください。
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
IZANAGI_DISPATCH_OUTCOME_V1 {"child_rc":null,"child_started":false,"kind":"infra","reason":"dispatch-error"}
IZANAGI_TASK_RUN_DIAGNOSTIC_V1 recording-unavailable:dispatch-no-child
```

receipt は `output/pegasus-dispatch/df582903882f65b3adae236054ed48cb/receipt.json`。終了コード16で、テスト子プロセスは起動していません。

静的確認では **73 node（従来67＋今回6）**。AST 構文解析、追加 parameter ID の ASCII 形式、既存テスト不変性、`git diff --check` は通りました。

制約 meta-test として、以下を確認しました。期待値は変更していません。

- process inventory exact、patch define registry 一致。
- deferred 台帳 exact・全 entry の live sink 対応。
- T2155 の分類件数・行番号 pin。
- T2520 の台帳除去前後の件数・他 sink 不変。
- production 4 sink の行番号 pin。
- calibration の call-site 数、bounded launch inventory。

波及先は `_PythonGateFlow` の injected 判定を消費する閉包検査、T2155、T2520、production pin、既存 floor injected sink です。検索範囲 `orchestrator/`・`tools/` では解析 helper の所有外 caller は見つかりませんでした。共有 fixture、campaign 専用状態計算、production は変更していません。所有外の n_pilot テスト3件は M1 の consumer です。

## production 4 check の当て直し

指定集合 `{DriverError, S1DriverError, _SortSwoOracleRejected, PilotError, OracleDriverError}` と束縛名の交差を production AST で確認しました。

| check | 対象関数 | 全種類の引数 | 関数 body の Name Store | module Assign／AnnAssign |
|---|---|---|---|---|
| s1:1218 | `run_role` | 空 | 空 | 空 |
| s1:1295 | `run_role` | 空 | 空 | 空 |
| s8b_oracle_driver:1801 | `run_block` | 空 | 空 | 空 |
| n_pilot:1018 | `build_binaries` | 空 | 空 | 空 |

4件とも対象関数は module 直下で、字句的親関数はありません。各行の helper Call も AST で確認しました。

静的追跡では、s1 の2件は従来の bare 再送出経路、s8b は OracleDriverError、n_pilot は PilotError への変換経路を維持します。**covered 維持は静的判断であり、今回の実走確認ではありません。**

## 変異 matrix の anchor (M0〜M13、old/new 文字列、期待 node)

全 old は修正後の実 bytes と照合し、対象ファイル内で **各1箇所**でした。全置換結果の AST 構文解析も通りました。変異自体は未実走で、以下は期待赤集合の予測です。

M1 以外の対象は `orchestrator/tests/test_ccbench_spawn_sites.py` です。

**M0 — 2326行。期待赤なし、SURVIVED。**

```python
old = '        if matching_checks:\n            # Explicit helper rejection E is reraised by its first catcher;\n'
new = '        if matching_checks:\n            # Explicit helper rejection E is reraised by the first catcher;\n'
```

**M1 — `orchestrator/campaign/s8b_oracle_n_pilot.py`:1028。期待赤7 node。**

```python
old = '            except S1DriverError as exc:\n                raise PilotError(f"build condition evidence rejected: {exc}") from exc\n'
new = '            except S1DriverError:\n                pass\n'
```

以下はいずれも `orchestrator/tests/` 配下です。

```text
test_s8b_oracle_n_pilot.py::test_injected_build_fn_without_condition_records_is_rejected
test_s8b_oracle_n_pilot.py::test_build_binaries_uses_binding_flags_and_prepared_records_independently
test_s8b_oracle_n_pilot.py::test_r33_successor_protocol_document_loads_from_repository
test_ccbench_spawn_sites.py::test_define_sink_cross_product_has_no_unreviewed_ungated_member
test_ccbench_spawn_sites.py::test_define_sink_cross_product_classifies_t2155_production_sinks_exactly
test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal
test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2491_injected_production_sinks_stay_covered
```

r33 は冗長 digest gate です。

**M2 — 1857行。期待赤：n8 以外の全負例。n10／n14 は Python 3.11 以降のみ。**

```python
old = '                self.returned_evidence_checks.setdefault(scope, []).append(\n                    (call.lineno, result_name, self._injected_check_unswallowed(scope))\n                )\n'
new = '                self.returned_evidence_checks.setdefault(scope, []).append(\n                    (call.lineno, result_name, True)\n                )\n'
```

対象は S の n1〜n7・n9〜n12・n14 と、R の n13・n15〜n17。3.10 では予測14件、3.11以降では16件です。

**M3 — 1768行。期待赤：`S[n2-bare-pass]`。**

```python
old = '            if exception_type is None:\n                return "definite"\n'
new = '            if exception_type is None:\n                return "none"\n'
```

**M4 — 1802行。期待赤：`S[n4-conditional-raise]` のみ。**

```python
old = '                if not handler.body or not isinstance(handler.body[-1], ast.Raise):\n                    return False\n                raised = handler.body[-1].exc\n'
new = '                raises = [item for item in region_nodes(handler.body) if isinstance(item, ast.Raise)]\n                if not raises:\n                    return False\n                raised = raises[-1].exc\n'
```

n5 は先行する脱出検査で拒否され続けます。

**M5 — 1748行。期待赤：`S[n6-finally-return]`。**

```python
old = '        if any(has_escape(node.finalbody) for node, _ in self.injected_try_stack):\n            return False\n'
new = '        if False:\n            return False\n'
```

**M6 — 1850行。期待赤：`S[n8-lambda]`。**

```python
old = '            if (\n                call is returned_evidence_call\n                and name.endswith("require_returned_condition_evidence")\n            ):\n'
new = '            if (\n                name.endswith("require_returned_condition_evidence")\n            ):\n'
```

**M7 — 1813行。期待赤：`S[n9-system-exit]`。**

```python
old = '                    elif (\n                        self.module_class_counts[name] == 1\n                        and name not in self.module_assignments\n                        and name not in local_names\n                    ):\n'
new = '                    elif (\n                        True\n                        and name not in self.module_assignments\n                        and name not in local_names\n                    ):\n'
```

**M8 — 1790行。期待赤：`S[n7-unknown-handler]`。**

```python
old = '                return "none"\n            return "maybe"\n\n        for node, position in reversed(self.injected_try_stack):\n'
new = '                return "none"\n            return "none"\n\n        for node, position in reversed(self.injected_try_stack):\n'
```

**M9 — 1793行。期待赤：`S[n11-outer-swallow]`。**

```python
old = '        for node, position in reversed(self.injected_try_stack):\n            if position != "body":\n'
new = '        for node, position in reversed(self.injected_try_stack[-1:]):\n            if position != "body":\n'
```

**M10 — 1800行。期待赤：`S[n5-unreachable-raise]`。**

```python
old = '                if has_escape(handler.body):\n                    return False\n'
new = '                if False:\n                    return False\n'
```

**M11 — 1778行。期待赤：`R[n13-local-rebound-conversion]` と `R[n16-argument-rebound-handler]` の両方。**

```python
old = '            if name in local_names or name in self.module_assignments:\n                return "maybe"\n'
new = '            if name in self.module_assignments:\n                return "maybe"\n'
```

n13 は X が DEFINITE に変わり PilotErr への変換を受理、n16 は ChildError が NONE に変わり Pass を読み飛ばすため、両方が赤になる予測です。n12 は末尾 Pass により拒否され続けます。

**M12 — 1813行。期待赤：`R[n15-module-rebound-conversion]`。**

```python
old = '                    elif (\n                        self.module_class_counts[name] == 1\n                        and name not in self.module_assignments\n                        and name not in local_names\n                    ):\n'
new = '                    elif (\n                        self.module_class_counts[name] == 1\n                        and name not in local_names\n                    ):\n'
```

**M13 — 1805行。期待赤：`R[n17-rebound-as-name]`。**

```python
old = '                bare = raised is None or (\n                    isinstance(raised, ast.Name) and raised.id == handler.name\n                    and handler.name not in _potentially_bound_names(tuple(handler.body))\n                )\n'
new = '                bare = raised is None or (\n                    isinstance(raised, ast.Name) and raised.id == handler.name\n                )\n'
```

## 総括

指定1ファイルに R3a〜R3c、保証限界コメント、追加6例を実装しました。既存期待値は不変、commit は未作成です。

**dispatch 障害によりテスト・変異は未実走です。** 親への引継ぎは73 node の全ファイル走、Python 3.11以降での TryStar 検証、M0〜M13 の変異走と予測集合の照合です。