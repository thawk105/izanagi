## 変更面

指定どおり、2ファイルに10行を追加しました。逐語diffは以下です。

```diff
diff --git a/orchestrator/qualification/contract.py b/orchestrator/qualification/contract.py
index 6c1451b10..47fe1b3af 100644
--- a/orchestrator/qualification/contract.py
+++ b/orchestrator/qualification/contract.py
@@ -73,6 +73,9 @@ REQUIRED_CODE_IDENTITY_PATHS = frozenset({
     "orchestrator/calibrator/schema_v2.py",
     "orchestrator/calibrator/tsc.py",
     "orchestrator/verifier/core.py",
+    "orchestrator/verifier/dsg.py",
+    "orchestrator/verifier/model.py",
+    "orchestrator/verifier/parse.py",
     "tools/pegasus/policy.json",
 })
 REQUIRED_SCRIPT_IDENTITY_PATHS = frozenset({
diff --git a/orchestrator/tests/test_t126_pegasus_tools.py b/orchestrator/tests/test_t126_pegasus_tools.py
index 181235206..501337e8e 100644
--- a/orchestrator/tests/test_t126_pegasus_tools.py
+++ b/orchestrator/tests/test_t126_pegasus_tools.py
@@ -1524,6 +1524,13 @@ def test_required_code_identity_closes_activation_receipt_imports_without_record
     }
 
 
+def test_required_code_identity_includes_verifier_core_dsg_model_parse():
+    assert "orchestrator/verifier/core.py" in REQUIRED_CODE_IDENTITY_PATHS
+    assert "orchestrator/verifier/dsg.py" in REQUIRED_CODE_IDENTITY_PATHS
+    assert "orchestrator/verifier/model.py" in REQUIRED_CODE_IDENTITY_PATHS
+    assert "orchestrator/verifier/parse.py" in REQUIRED_CODE_IDENTITY_PATHS
+
+
 def test_series_preimage_exact_code_identity_set_tracks_activation_closure(
     tmp_path,
 ):
```

## 検査

`python3 -B`で実測しました。

- 集合件数：`CODE_COUNT=40`、scriptとの和集合：`UNION_COUNT=43`。両方assert成功。
- 新テストの直接呼出し：`DIRECT_CALL_PASS`。
- test module属性をdsg.pyなしのfrozensetへ一時差し替え：`AssertionError`を確認し、`DID_RAISE`。属性は復元済み。
- pytestによる新テスト・既存consumer testの検証：**実装済み・未実走**。焦点走・変異matrix・受入全走は実行していません。

`git diff --stat`：

```text
 orchestrator/qualification/contract.py        | 3 +++
 orchestrator/tests/test_t126_pegasus_tools.py | 7 +++++++
 2 files changed, 10 insertions(+)
```

`git status --porcelain`：

```text
 M orchestrator/qualification/contract.py
 M orchestrator/tests/test_t126_pegasus_tools.py
```

所有2ファイル以外に差分はありません。

## 波及の静的列挙

- `t126_driver._identity_files()`は定数から列挙するため、新3ファイルを個別hashとdisk/blob照合の対象にします。`submission.prepare()`の取得経路にも反映されます。
- `series_identity()`のexact集合は37件から40件へ置換され、`identity.verify_recorded_series_identity()`とcollectorにも波及します。旧37-key成果物は現行検証で不受理になりますが、歴史記録のbytes・当時の判定は変更していません。
- 共有fixture `_attempt()`と`test_t126_qualification_contract.py`の集合由来fixtureは自動追随します。tracked path検査は43 nodeへ増えます。`test_t419_probe_causality.py`の既存部分集合検査は変更不要です。
- **B1照合：確認済み・修正不要。** submit scriptの7 path列挙、`submission.py`の入口、`t126_qualification.sh`のsource-stage evidence生成はidentity全集合の複製ではありません。docs参照5箇所も全集合の複製ではなく、編集していません。
- **B2照合：静的確認済み。** driver testの`_prologue_value()`は3-keyの部分fixtureです。`_dependency()`の定義はpegasus tools test側にあり、依存repoを作ります。いずれも変更していません。driver testの実走確認は親に残ります。
- `contract.py`は自身のidentityとcampaign loader閉包にも含まれるため、統合commit後の整合確認が必要です。verifierのtrace判定、schema、hash domain、検証ロジック、campaign閉包は変更していません。

## 総括

plan v2の1・2を逐語どおり実装しました。指定の直接検査3項目は成功しました。禁止されたGit操作、docs編集、pytest・`tools/run_tests.py`起動は行っていません。commitと実走検証は親へ引き継ぎます。