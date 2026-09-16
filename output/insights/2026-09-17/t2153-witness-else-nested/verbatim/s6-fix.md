## 変更した file と差分の要約

- `orchestrator/tests/test_build_site_gate.py`: m11の素通し条件に`izanagi_compile_time_branch_`を追加。期待例外と`calls == []`は維持。
- `orchestrator/campaign/s2_verify_calibration.py`: factory配線を指定の3行へ分行。
- `orchestrator/tests/test_s5_permutation_coverage.py`: factory呼出しの先行assertと、拒否例外に両reason codeが含まれる検査を追加。

段5の差分を保持。追加編集禁止の2ファイルは、提供された段5差分との一致も確認しました。commitは作成していません。

## 所見ごとの対応表 (closed / partial / regressed)

| 所見 | 状態 | 確認 |
|---|---|---|
| fix 1 | closed | m11が実compiler・CMakeで成功 |
| fix 2 | closed | 指定形式への分行と復元後のテスト成功 |
| fix 3(a) | closed | 配線変異で4ケースとも指定assertにより失敗 |
| fix 3(b) | closed | 両macroの拒否分岐で両reason codeを検査して成功 |

## 実走結果 (nodeid と結果、未実走の列挙、反実仮想の結果)

指定の`PYTHONPATH=. python3 -c "...pytest.main(...)"`形式で実走しました。

- `orchestrator/tests/test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent`: **1 passed、22 deselected**。
- `orchestrator/tests/test_s5_permutation_coverage.py`全体: **12 passed**。配線復元後も**12 passed**。
- 上記に含まれる`test_s2_condition_gate_passes_factory_declaration_to_meaning_evaluator`は、`[True/False × IZANAGI_BREAK_NOREAD_VALIDATION/IZANAGI_BREAK_HIGHKEY_VALIDATION]`の全4ケース成功。

反実仮想ではS2を一時的に`declaration=None`へ変更し、consumer全4ケースが次の理由で失敗しました（4 failed、8 deselected）。

```text
AssertionError: factory was not called before meaning evaluation
```

`IndexError`は発生せず、終了後にS2を変更前のバイト列へ復元しました。復元後の`git diff`抜粋：

```diff
-        captured, request=request, declaration=None, cxx=buildcache.DEFAULT_CXX,
+        captured, request=request,
+        declaration=condition_meaning_gate.declare_define_runtime_meaning(request),
+        cxx=buildcache.DEFAULT_CXX,
```

`git diff --check`も成功。指定された実走対象に未実走はありません。

## 未完・懸念

本段の3件に未完はありません。consumer回帰全体・受入全走・実機S2走行は本段では実施していません。fixtureでの成功を実機S2の検証結果とは扱いません。

## 総括

3件ともclosedです。指定の3ファイルだけを追加編集し、段5の未commit差分とともに作業ツリーへ残しました。