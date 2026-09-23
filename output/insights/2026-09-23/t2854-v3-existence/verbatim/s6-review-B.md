### B1 — nit：撤去した印の名前が試験に残存

根拠：`orchestrator/tests/test_verifier.py:3897`。

`rg` で `orchestrator/`・`tools/` を検索した結果、`assert not hasattr(ig, "v3_existence_unverified")` が唯一の残存でした。旧 note の文言は残っていません。削除確認の意図は分かりますが、旧名への依存を毎回の fixture 検査に残す必要はありません。

修正案：この1行を削除する。production の field・設定・clean 条件・不要 import は既に撤去されています。

成果物への影響：放置しても certified・受理集合は変わりません。

### B2 — nit：経路比較 helper が同じ DSG を二度構築

根拠：`orchestrator/tests/test_verifier.py:3448–3449`。

辺比較と integrity 比較で、それぞれ `DSG(txns)` を構築しています。今回追加した後者により、同じ入力の辺構築と存在検査が余分に一度走ります。裁定が要求する経路比較を減らさず削れる重複です。

修正案：`graph = DSG(txns)` を一度だけ作り、両 assertion で共有する。

成果物への影響：放置しても certified・受理集合は変わらず、試験の処理量だけ増えます。

### B3 — nit：読みの照合で不要な空コンテナを毎回生成

根拠：`orchestrator/verifier/dsg.py:423`。

`histories.get(obj, {}).get(version, (None, set()))[1] == {"D"}` は、検索が成功する場合もデフォルト引数の空 dict・空 set と比較用 set を生成します。非 genesis 読みの件数分だけ発生する、局所的に削れる割当です。

修正案：履歴と版の取得を分け、欠落時は `None` を使う。曖昧 object は既に除外済みなので、取得した ops の `"D" in ops` で判定できます。新しい抽象や索引は不要です。

成果物への影響：放置しても certified・受理集合は変わりません。実行時間への寄与は未計測です。

## 総括

- **GO：このレビュー範囲では must-fix なし。** 上記3件は局所的な整理です。
- production 127行、試験198行、新規 test 6本は、差分・commit・author 報告が一致し、裁定上限内です。
- 6種類の違反、v3 限定の入口、出力欄、notes は裁定に対応しています。単位5の配線や不要な汎用化は見当たりません。
- 旧印の production 撤去は完了。core の `is_v3`・`TxnV3` import も消え、dsg の `TxnV3` は使用中です。
- notes は既存の「件数・種別集計・先頭5件」の形式と整合し、コメントにも初期集合の独立検証という過大主張はありません。
- 追加処理は W/R 各1走査、object 内の版 sort、違反詳細 sort。履歴保持は O(W)、詳細は O(違反数) で、メモリ増加はありますが過大と断定する実測はありません。
- 外部 probe は両 worker 設定で certified=true。時間は合計17.9秒で、提示された変更前合計11.8秒より約52%増です。高速化とは評価できず、増分すべてを存在検査に帰属できる比較条件も未確認です。
- author の「未 commit・親 probe 未完了」は報告時点の記述として扱いました。本レビューではテスト・変異を実行しておらず、R8 全達成の判定はしていません。