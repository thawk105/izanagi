## 所見対応表 (closed/partial/regressed)

|所見|判定|対応|
|---|---|---|
|must-fix 1|partial — 実装済み・未実走|spec 間の出力 path 非共有 gate を削除|
|must-fix 2|partial — 未作成|公開経路の正例・負例は未追加。要求された負例に契約との矛盾あり|
|nit 1|partial — 実装済み・未実走|到達不能な空層分岐を削除|

closed と判定した所見はありません。

## 変更した関数

`orchestrator/campaign/p3_b4_floor_artifact_issuer.py` の2関数のみ変更しました。

- `_load_expected_specs`: `aggregate_output_reuse_error` の検査を削除。
- `_validate_aggregate_summary_coverage`: `retain_count == 0` 分岐を削除。

空層分岐は、先行する非空 `values` 検査、実標本との対応検査、閉じた層集合との一致を通過した後では到達不能です。

## 追加した正例と負例

追加なし。既存テスト・fixture・decorator・期待値は変更していません。

## 受理集合の変更 (前と後)

|入力|前|後（静的判断）|
|---|---|---|
|異なる spec が window 出力 path を共有し、他の条件を満たす|拒否|受理可能|
|各 spec 内の出力 path 重複|拒否|拒否を維持|
|summary path 重複・期待 spec 対応欠落・window 閉包不一致|拒否|拒否を維持|
|空層|先行検査で拒否|同じ先行検査で拒否|

v1・CLI は変更していません。

## 実走結果 (nodeid と範囲)

試行した exact command:

```bash
PYTHONPATH=. python3 -m pytest orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q
```

PreToolUse hook の `guard_bash` が、Pegasus ログインノードでの pytest 直接実行を拒否しました。診断は計算ノードでの実行を要求しています。

対象範囲は issuer テストファイル全体。**実走 nodeid は0件、未実走です。**

## 波及の静的列挙

- 集約発行と v2 loader の再構成が、変更した2関数を使用します。
- material report の resolver → loader → evaluator 経路、および JSON・Markdown の床値射影に受理範囲の変更が届きます。consumer test は未実走です。
- 共有 helper の `_write_inputs`・`_valid_document`、report の `immutable_publication` は未変更です。
- レビュー B が挙げた raw-record producer・producer-auth experiment の report consumer にも間接波及し得ます。当該ファイルは射影外のため直接確認していません。
- テスト追加なし。duration ledger・group 登録も未変更です。

## 未実走・未完了

must-fix 2 は未完了です。

「期待 spec 列と summary を同時に1組落とす」場合、残る期待列と入力の閉包が一致すれば、追補 (b)(f) と段4裁定には拒否条件がありません。発行時なら有効な縮小集合になり、成果物改変時も全体を再構成して外側 pin を更新した場合は、明記された採用責任の境界です。この負例を成立させる追加 gate は実装していません。

公開経路用の実体較正 fixture も未作成です。既存 helper は較正 payload が `{}` で検証を置換しているため、そのままでは迂回禁止の正例になりません。材料レポートへの到達も未確認です。

## 総括

2つの不要な検査を削除しましたが、実走できていません。  
公開経路テストは未作成で、段6完了とは判定しません。  
docs・所有外ファイルの編集、`git add`、commit は行っていません。