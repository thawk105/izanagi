## 変更の要約

指定2ファイルのみ変更（15行追加）。

- launcherを指定の4値で `local-ok` 登録。
- class／entry／evidenceの固定表へ各1項追加。
- 既存期待値は変更なし。禁止されたGit操作は未実行。

## 実走結果

- 指定の絞り込み：**89 passed、395 deselected**（6.62秒）。
- `test_hooks.py` 全件：**482 passed、1 failed、1 skipped**（19.06秒）。
- JSON読み込み、`git diff --check`：成功。

以下のnodeidは通過（接頭辞：`orchestrator/tests/test_hooks.py::`）。

- `test_bash_pegasus_registry_schema_and_fixed_classes`
- `test_bash_pegasus_execution_inventory_is_synchronized`

[全484件のnodeid・結果一覧](/tmp/t2797-unit-fix1-test-hooks-nodeids.txt)

## 未了・懸念

- `test_t2146_authority_hardlink_alias_is_denied_in_both_guards`：sandbox外の `/work/1/SFC/tanab/.izanagi-t2146-hardlink` への一時ディレクトリ作成が読み取り専用制限で失敗。
- `test_real_submodule_payload_edit`：既存条件によるskip（`backoff.hh` のEVOLVE-BLOCK marker不在）。skipの追加・変更なし。

## 総括

実装と対象89件の検証は完了。全件も実走しましたが、環境制約による失敗1件と既存条件によるskip1件が残っています。