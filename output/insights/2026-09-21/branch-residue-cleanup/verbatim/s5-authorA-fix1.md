## 変更前の挙動 / 変更後の挙動

bundle 省略条件を「reflog 全 commit が main 祖先」から「子 HEAD が main 祖先」へ変更しました。`integration_basis` は従来の判定を維持しています。

## file:line の変更一覧

- [tools/dev_wave_cleanup.py:18](tools/dev_wave_cleanup.py:18): HEAD が main 祖先なら bundle 不要と追記。
- [同:1851](tools/dev_wave_cleanup.py:1851): `_ancestor(args.main, proof.head, proof.main_tip)` で作成要否を判定。
- [同:1935](tools/dev_wave_cleanup.py:1935): 省略理由を `child HEAD is a main ancestor` に変更。
- [orchestrator/tests/test_dev_wave_cleanup.py:345](orchestrator/tests/test_dev_wave_cleanup.py:345): 既存 reflog テストに指定の assertion 3件を追加。既存ケースで覆うため新設なし。

## テスト実走結果

**実装済み・未実走。実走0件、緑の nodeid なし。**

直接 pytest を試行しましたが、起動前に拒否されました。構文解析と `git diff --check` は成功しています。

## 波及の静的確認

受理集合の2関数と wave `_delete_branch` は AST 比較で変更なし。既存 assertion の反転・緩和・削除、新設・改名 node はありません。

## 総括

所有2ファイルだけを修正しました。commit・branch 操作・push はしていません。  
仕様衝突への修正は完了していますが、実行時の検証が残っています。

自動実行審査（PreToolUse `guard_bash`）が pytest の直接起動を拒否しました。理由は Pegasus ログインノードでの pytest 実行禁止です。