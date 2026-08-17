## 総括

G1 / G2 / G4 を実装しました。pytest は指示どおり実行していないため、すべて `partial（実装済み・未実走）` とします。G3 には触れていません。

| 項目 | 状態 | 根拠 |
|---|---|---|
| G1 | `partial` | module-scope fixture で snapshot を5箇所へ共有。archive 対象を実際の evidence ref 閉包へ限定 |
| G2 | `partial` | literal dead branch と終端文後を除外し、C09 負例3件と未知条件の正例を追加 |
| G4 | `partial` | `_attributes` を削除し、削除後の全件検索で識別子0件 |
 
G1 は snapshot 生成を5回から1回、archive 展開を `139 × 5 = 695 files` から `57 files` へ削減しました。残る57件は契約、宣言 evidence、評価器が実際に読んだ中継 module の閉包です。これ以上減らすと現行評価で参照された blob を欠くため、検出力を保ったままでは削減できません。共有する tree を使う5テストはいずれも読み取り専用で、変異漏れはありません。

G2 の追加負例は [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1202-t1197-cross-module-reach/orchestrator/tests/test_s8c_preregistration_predicates.py:1229) の3 parameterです。

- `if-true-else`: 定数真の `else` 内 call を殺す
- `while-false-body`: 定数偽 loop の body 内 call を殺す
- `after-return`: 無条件 `return` 後の call を殺す

各ケースは C09 の terminal-undefined baseline から対象 call 1件だけを dead 位置へ移し、`layer3-producer-unreachable` の単一理由を期待します。未知条件の両枝を残す正例も追加しました。`raise` / `continue` / `break` 後を含む8形の直接 AST 診断も成功しています。

静的確認結果:

- 12条件の status / reason: 指定表と12/12完全一致
- snapshot archive 対象: 57 files
- 静的評価可能な `.replace()`: 48式、no-op 0件
- `_attributes`: 削除前は定義1・参照0、削除後は production/test 合計0件
- 保護対象のC12テスト2本: bytes hash不変
- `ast.parse`: 対象3ファイルすべて成功
- `git diff --check`: 成功
- 変更ファイル: 許可範囲内の2ファイルのみ
- pytest: 未実走。親の計算ノード実測待ち