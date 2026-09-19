## 総括

指定の 2 ファイルだけを変更しました（計 3 行追加・18 行削除）。

- `test_s8b_holdout_freeze.py`：2383–2384 行の重複 `True` と対応 id を除去。残存 row / ids は **2 / 2**。
- `test_p3_s4_loop.py`：旧3238–3247 行の指定関数と空行、指定4 row と対応 ids を除去。区切りコメントを保持。残存 row / ids は **5 / 5**、順序対応も確認済み。
- test 名集合：108→108、289→288。差分は `test_value_literal_consistency_accepts_match` の削除1件のみ、追加なし。
- `grep -rn`：所有 path 外の一致は `acceptance_duration_ledger.json` の8行のみ。他ファイルの参照なし。台帳は未編集。
- 両ファイルの構文確認、AST による指定外変更なしの確認、`git diff --check` は成功。
- **実装済み・pytest 未実走**。git add / commit は未実行。