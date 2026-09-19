## 所見別の対応表

行番号は `orchestrator/tests/test_s8b_ratified_freeze.py`。

| 所見 | 対応 | 箇所 |
|---|---|---|
| A1/B1 | closed：新正例に sealed-process decorator を追加 | :1387 |
| A2 | closed：標準配置だけを採用し、key に session UID を追加 | :1003、:1018 |
| B3 | closed：4回構築、blob取得を削除、g1/topology を直接比較 | :1388 |
| B6 | closed：`sizes`・`copied_files`・`copied_bytes` を削除 | :1061 |

closed は修正完了を示し、pytest 成功を意味しません。

## 変更面

所有ファイル1本のみ、12行追加・12行削除。`key`・`status`・`source_paths` は維持。`git add` / `git commit` は実行していません。

## 直接呼出しの検証結果

**DIRECT_CALL_PASS**

- 標準 xdist／非 xdist 配置：期待する memo 親を採用。
- 外側祖先を持つ custom basetemp／tempfile 配置：`None`。
- 深すぎる配置・不正worker名・session自身：`None`。
- 新正例と同じ tempfile 配置：`pytest-of-*` 祖先がなく、確実に迂回。
- UID 未設定時は空文字。異なる UID で digest が変化。

**AST_PASS**：test 数は64本。base `657e1e5a7` および修正前HEADと比較し、既存63本の本体・decorator・parametrize・signature は不変。新正例の builder 呼出しは4回。

両 freeze/verify ファイルの `py_compile`、`git diff --check` も成功しました。

## 未実走・未確認

pytest、builder本体、copy/refresh・残骸回復の再実走、変異検証、A/B は未実施です。実走は親の計算ノード検証に委ねます。

新正例には、登録簿に未登録の tracked 入力読取りが残ります。走行中に入力が変わらない前提です。

## 総括

指定4所見の修正を完了しました。
配置判定・UID分離・構文・既存63本のAST不変性を確認しました。
pytest の成功は未確認です。