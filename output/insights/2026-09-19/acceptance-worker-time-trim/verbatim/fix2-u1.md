## 所見別の対応表

| 所見 | 対応・根拠 |
|---|---|
| A2 | **closed（実装修正）**。`test_s8b_ratified_freeze.py:62,1005,1015`：session 分離を key に移し、深さ制限を撤去。`mutation`・`baseline` 配置が採用されることを直接確認。性能回復は未実測。 |

## 変更面

所有ファイル `orchestrator/tests/test_s8b_ratified_freeze.py` のみ、6行追加・8行削除。

- import 時に process token を生成。
- key に `TESTRUNUID or process token` を使用。
- 最寄りの適格な `pytest-N` を深さによらず採用。
- 新正例は変更なし。git add／git commit は未実行。

## 直接呼出しの検証結果

**DIRECT_CALL_PASS**

- 指定 (a)(b)(c)：採用。(d) tempfile：`None`。
- 私設 session の `seed`／`copy`／`rebuilt`：採用。
- UID 未設定・異なる値で digest が分離。空文字は token に fallback。
- 同じ UID では token が異なっても同じ digest。fork 子の token 継承も確認。

**AST_PASS**：test 関数64本。base `657e1e5a7` の既存63本は完全不変。HEAD 比では新正例を含む64本すべて不変。

両ファイルの `py_compile`、`git diff --check` も成功。

## 未実走・未確認

pytest、builder 本体、copy／refresh・残骸回復、変異検証、A/B 性能測定は未実走です。416秒からの回復は親の計算ノード検証待ちです。新正例の未登録 tracked 入力読取りは残ります。

## 総括

A2 の修正と直接検証を完了しました。
深い配置の memo 採用と session key 分離を確認しました。
既存期待値・新正例は不変です。性能回復は未確認です。