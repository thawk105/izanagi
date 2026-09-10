1. レンズ1所見1（二重代入）

- file:line: `orchestrator/tests/test_coder_effect_gate.py:149-167`
- real/refuted: **refuted**
- must-fix/nit: **nit**

`ast.walk(tree)` で `ast.Assign` と `ast.AnnAssign` を全走査し、対象を発見するたび `assignments` に追加しています。直接代入が2件あれば `len(assignments) == 2` となり、`test_coder_effect_gate.py:164` の assert が発火します。

2. レンズ1所見2（別名迂回）

- file:line: `orchestrator/tests/test_coder_effect_gate.py:168-172`
- real/refuted: **refuted**
- must-fix/nit: **nit**

RHS に `_SOURCE`、`DENY_TABLE`、`dict`、`map` などの `ast.Name` が現れると、`node.id != "frozenset"` により `test_coder_effect_gate.py:170-172` の assert が失敗します。`frozenset(_SOURCE)` の形でも `_SOURCE` の走査時に拒否されます。属性参照は `:173-174`、間接呼び出しは `:183-189` で拒否されます。

3. allowlist の新規欠陥

- file:line: `orchestrator/tests/test_coder_effect_gate.py:69-98, 168-195`
- real/refuted: **refuted**
- must-fix/nit: **nit**

現行定義の RHS は `ast.Dict`、`ast.Tuple`、直接の `frozenset` 呼び出し、文字列 `ast.Constant`、`ast.Load` のみで、allowlist に適合します。`ast.Set`、`ast.List`、comprehension、属性、非文字列定数などは `:192-195` の最終 `pytest.fail` に到達するため、意図せず通過しません。

4. 既存155件への非破壊性

- file:line: `s6-fix-output.md:1-6`; `test_coder_effect_gate.py:112-143, 198-205`; `focus-run-2.log:42`
- real/refuted: **refuted**
- must-fix/nit: **nit**

fixの変更範囲はAST guard関数内部のみと報告されており、意味的probe・総数チェック・既存一意性検査は残っています。焦点走は `155 passed` です。なおログ自身が受入全走ではないと警告しているため、ここでは焦点走の証拠としてのみ扱います。

5. 段4裁定・M6境界

- file:line: `s4-ruling.md:60-75`; `test_coder_effect_gate.py:135-143`
- real/refuted: **refuted**（旧来の2点M6に対する指摘は、更新済み3点M6で解消）
- must-fix/nit: **nit**

M1〜M5は、production側だけ識別子を削ると frozen semantic probe が該当識別子を検査して失敗するためKILLEDです。M6は productionの`fork`、frozen literalの`fork`、総数`96→95`を同時変更した場合だけprobeとsanity checkをともに通過し、裁定どおりSURVIVEDになります。

## 総括

変異matrixへ進めてよいか: **はい**。  
レンズ1の二重代入・別名迂回はいずれも閉じています。  
allowlistは現行定義を受理し、`ast.Set`/`ast.List`等を拒否します。  
M1〜M5はKILLED、M6は3点協調時のみSURVIVEDです。