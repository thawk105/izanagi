## 実装した内容

[acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2591-impl/orchestrator/tests/acceptance_duration_ledger.json:3) の指定値だけを `79.0` → `4.8` に変更しました。

## 実走結果

`orchestrator/tests/test_update_acceptance_duration_ledger.py` 全24件を指定の直接実行方式で実走。**24 passed、rc=0**。

## 総括

変更を逆置換すると編集前の全バイトと一致することを確認しました。JSON比較でもschema・全キーの並び順・他nodeの値が不変、`nodeid_count` と実件数がともに `23110` と確認済みです。

他ファイルの編集・commitはしていません。