## 所見ごとの対応表 (closed / partial / regressed)

closed は修正完了を示し、実走成功を意味しません。

| 所見 | 状態 | 対応 |
|---|---|---|
| RB-1 / F-1 | closed | seedへ文字列接尾辞を追加し、改変前後のbytes不一致をassert |
| RA-2・RB-4 / F-2 | closed | 例外文言の書換え分岐を削除。新規負例のmatchを指定文言へ変更 |
| RB-3 / F-3 | closed | 「解決した protocol hash」へ実装・新規負例を更新 |
| RA-1 / F-4 | closed | record bytesとの冗長比較を削除。commit OID比較は維持 |
| RB-2 | closed（親の記録対象） | closure除外assertを独立の検出力に数えない |
| RA-3・RB-4・RB-5 | partial（親担当） | M3の診断差分類・M5の登録外分類に従い、変異実走は未実施 |

## 変更点 (file:line)

- `orchestrator/campaign/s8b_holdout_freeze.py:1394`：例外を直接包み、冗長比較を削除。
- 同ファイル`:1480`：hash不一致の診断文言を変更。
- `orchestrator/tests/test_s8b_holdout_freeze.py:1879`：新規hash負例のmatchを変更。
- 同ファイル`:1895`：seed改変、bytes不一致assert、resolver拒否のmatchを修正。

今回の編集は上記2ファイルのみ。既存fixture差分は維持し、docs編集・commitはしていません。

## 実走した検査と結果

- **AST parse：成功（rc=0）**。編集2ファイルを確認。
- **構造検査：成功（rc=0）**。`FLOOR_PROTOCOL_REL`代入1件、`_run_git`・`_run_git_bytes`・`_run_git_z`の定義とsubprocess起動各1件、必須3呼出し各1件を確認。
- **既存期待値保全：成功（rc=0）**。HEADに存在するテスト・helper全131関数のASTが不変。
- **`git diff --check`：成功（rc=0）**。
- **指定焦点走：未実走（rc=16）**。`tools/run_tests.py`経由で試行したが、`qstat -Q preflight rc=1`で停止。`child_started=false`、実走nodeidなし・0件。全体走・変異走も未実施。

runnerが所有外の `output/pegasus-dispatch/a734296f7007e7ae934e843be9a1463b/receipt.json` を自動生成しました。

## 総括

**F-1〜F-4は実装済み・未実走です。** 静的検査は成功し、既存テストの期待値は維持しています。親側で焦点走・回帰確認・変異評価を完了する必要があります。