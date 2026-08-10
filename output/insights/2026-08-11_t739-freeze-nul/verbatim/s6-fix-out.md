指定の 2 件をテストファイルだけで修正しました。production の既存差分には触れていません。

## 総括

1. 変更したファイルと関数

- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t739-freeze-nul/orchestrator/tests/test_s8c_preregistration_core.py)
  - `_contract_path_cases`: import 時の件数 assert を削除
  - `_contract_with_interior_path_nul`: required / consumer path の中間へ NUL を挿入する独立 fixture helper を追加
  - `test_contract_path_inventory_has_expected_count`: 38 件の drift 検査を独立テスト化
  - `test_evidence_contract_hash_rejects_nul_at_interior_position`: 中間 NUL の 2 case を追加
- `orchestrator/campaign/s8c_preregistration.py` は変更していません。表示される変更は段 5 からの既存差分です。
- docs、契約 JSON、freeze record は未変更です。

2. 追加・変更した nodeid

追加:

- `orchestrator/tests/test_s8c_preregistration_core.py::test_contract_path_inventory_has_expected_count`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_interior_position[required]`
- `orchestrator/tests/test_s8c_preregistration_core.py::test_evidence_contract_hash_rejects_nul_at_interior_position[consumer]`

既存 38 case の parametrize と id/nodeid は変更していません。

中間 NUL テストは、NUL で終わらないことと、NUL の後ろに文字が続くことを自身で assert します。reason、message、NUL 非漏洩も exact 検査します。

3. 実走した command と結果

対象範囲: `test_s8c_preregistration_core.py` 全 nodeid。

```text
python3 tools/run_tests.py orchestrator/tests/test_s8c_preregistration_core.py -q -rf
```

結果: `rc=16`。`qstat -Q preflight rc=1` による Pegasus dispatch infrastructure failure で、pytest は起動・collection されていません。passed/failed 数は取得不能です。

非テスト検査:

```text
python3 -c 'import ast, pathlib; ast.parse(pathlib.Path("orchestrator/tests/test_s8c_preregistration_core.py").read_text())'
git diff --check -- orchestrator/tests/test_s8c_preregistration_core.py
```

いずれも `rc=0` です。

4. 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| R2: 中間 NUL の検出力不足 | closed | required / consumer の中間 NUL 2 case を追加 |
| 採用 nit: import 時の件数 assert | closed | 独立 nodeid へ移動。38 件から drift すれば同テストが赤になる |
| regressed | なし | 既存期待値・38 case の id・production は未変更 |

5. 未実走事項

pytest は dispatch preflight 障害により未実走です。テストを弱めず、直接 pytest を起動する迂回も行っていません。親環境で同じ `tools/run_tests.py` コマンドの再実行が必要です。
