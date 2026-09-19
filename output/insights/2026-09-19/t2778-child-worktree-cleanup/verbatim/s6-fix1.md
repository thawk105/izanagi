## 総括

**修正を反映しましたが、既存submodule正例とA2の衝突を検出したため、指定どおり停止しました。** 差分は所有4ファイルに残しています。commitは作成していません。

`test_remove_child_checks_initialized_submodule[clean]` はprimary module storeを作らないため、A2の検査でrc20／`backup-precheck`となります。既存期待値は撤去成功です。検査の緩和・期待値変更・fixture変更は行っていません。

所見ごとの反映箇所です（行番号は現在の作業木）。

| 所見 | 対応・file行範囲 |
|---|---|
| A1 | 変換属性・autocrlf拒否。`tools/dev_wave_cleanup.py:239–243,1562–1581`、テスト`:309–317` |
| A2 | primary storeのpin確認。実装`:1584–1622`、テスト`:414–443`。上記衝突で検証停止 |
| A3/B3 | stdin待ちによる終了。テスト`:238–251` |
| A4/B1 | literal更新。`tools/check_docs.py:628–635`、`orchestrator/tests/test_check_docs.py:189–196` |
| A5/B8 | main進行時のpartial負例追加。テスト`:356–375`。既存binding負例は不変 |
| A6 | tmpへfsync→link→unlink→directory fsync。実装`:1843–1847` |
| A7/B4 | manifest形式・信頼境界・argvをdocstringへ記載。実装`:2–15` |
| A8 | 正例を`main(argv)`経由に変更。テスト`:171–229` |
| B2 | `committed.patch`とreceipt集合を追加。実装`:251–256,1673–1747`、テスト`:213–219,446–461` |
| B5 | 未使用allowlist項目を削除。実装`:239–243` |
| B6 | submodule status取得を各階層1回へ。実装`:1584–1622` |

テストの行番号は、表内で省略したものもすべて `orchestrator/tests/test_dev_wave_cleanup.py` です。

**直接呼出し結果：7件PASS、1件FAIL。pytestは未実走です。**

以下は同ファイルのnode名です。

| 新設・変更node | 直接呼出し |
|---|---|
| `test_remove_child_rejects_clean_filter`（新設） | PASS |
| `test_remove_child_main_advance_during_removal_is_partial`（新設） | PASS |
| `test_remove_child_archives_dirty_integrated_author_and_keeps_branch`（変更） | PASS |
| `test_remove_child_rejects_live_process_cwd`（変更） | PASS |
| `test_remove_child_detached_ancestry_and_empty_backup`（変更） | PASS |
| `test_remove_child_checks_initialized_submodule[local-only-pin]`（parameter追加） | 未呼出し |
| 同`[clean]`（既存） | FAIL：primary storeにpinなし |

変更していない`test_remove_child_admin_binding_change_is_partial`と`test_remove_child_already_clean_with_receipt`も直接呼出しPASSです。残るsubmodule parameter、変異による赤化確認、正式harnessは停止により未実施です。

DW-O28の両literalは改訂ファイルと**byte一致・各996 bytes**を確認しました。byte assertは`:9487`と`:9685`の2箇所とも996のままです。`check_docs`は**rc1、期待されたDW-O28 exact契約不一致の1件のみ**。`git diff --check`はrc0でした。

静的な波及先は、receipt再読取り、子撤去正例・detached正例、共有submodule fixture、docsのsynthetic契約テストです。変更helperの所有外Python callerは検索範囲で見つかりませんでした。`test_pytest_collection_config.py`と`orchestrator/test_selection_contract.py`は既存ファイルpath・既存nodeを参照しており、今回の追加による参照変更はありません。これらのmeta-testも未実走です。