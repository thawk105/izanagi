## 変更の要約

`orchestrator/campaign/buildcache.py` の docstring の該当箇所のみ修正しました。

変更前（逐語）:
```text
    新 pin ``e9e477ca1b55348ab4530de0b1cf663ce4555290`` も CMake 3.25.0 の bnode019 / pegasus02 で両 check が成功 (2026-09-20 T-2304、3.22.1 は未確認)。
```

変更後（逐語）:
```text
    新 pin ``e9e477ca1b55348ab4530de0b1cf663ce4555290`` も CMake 3.25.0 (計算ノード bnode019、build 込み) と
    3.22.1 (login pegasus02、configure のみ) で同形を実測し両 check が成功した (2026-09-20 T-2304)。
```

## 実走結果

- `python3 -m py_compile orchestrator/campaign/buildcache.py`: 成功（終了コード0）。
- `git diff --check`: 成功（終了コード0）。

## 総括

CMake 3.22.1 の確認済み実測を反映しました。差分は指定1ファイルの docstring のみです。禁止された Git 操作は実行していません。