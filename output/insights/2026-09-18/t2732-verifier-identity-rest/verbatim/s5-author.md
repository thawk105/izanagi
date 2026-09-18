## 変更面

`orchestrator/qualification/contract.py`:

```diff
diff --git a/orchestrator/qualification/contract.py b/orchestrator/qualification/contract.py
index 47fe1b3af..d5b5dbe52 100644
--- a/orchestrator/qualification/contract.py
+++ b/orchestrator/qualification/contract.py
@@ -76,6 +76,9 @@ REQUIRED_CODE_IDENTITY_PATHS = frozenset({
     "orchestrator/verifier/dsg.py",
     "orchestrator/verifier/model.py",
     "orchestrator/verifier/parse.py",
+    "orchestrator/verifier/__init__.py",
+    "orchestrator/verifier/commit_receipt.py",
+    "orchestrator/verifier/report.py",
     "tools/pegasus/policy.json",
 })
 REQUIRED_SCRIPT_IDENTITY_PATHS = frozenset({
```

`orchestrator/tests/test_t126_pegasus_tools.py`:

```diff
diff --git a/orchestrator/tests/test_t126_pegasus_tools.py b/orchestrator/tests/test_t126_pegasus_tools.py
index 501337e8e..a0b9f7115 100644
--- a/orchestrator/tests/test_t126_pegasus_tools.py
+++ b/orchestrator/tests/test_t126_pegasus_tools.py
@@ -1531,6 +1531,12 @@ def test_required_code_identity_includes_verifier_core_dsg_model_parse():
     assert "orchestrator/verifier/parse.py" in REQUIRED_CODE_IDENTITY_PATHS


+def test_required_code_identity_includes_verifier_init_report_commit_receipt():
+    assert "orchestrator/verifier/__init__.py" in REQUIRED_CODE_IDENTITY_PATHS
+    assert "orchestrator/verifier/report.py" in REQUIRED_CODE_IDENTITY_PATHS
+    assert "orchestrator/verifier/commit_receipt.py" in REQUIRED_CODE_IDENTITY_PATHS
+
+
 def test_series_preimage_exact_code_identity_set_tracks_activation_closure(
     tmp_path,
 ):
```

## 検査

- `python3 -B` による import: code 集合 **43**、script との和集合 **46**。両値を assert で確認。
- 新 test の直接呼出し: **DIRECT_CALL_PASS**。
- test module 側の集合から `report.py` を一時除外した直接呼出し: `AssertionError` を確認、**DID_RAISE**。属性は復元済み、file 変更なし。
- 初回の test module import は補助 module の検索パス不足で失敗。`orchestrator/tests` をプロセス内の `sys.path` に追加して再実行し、上記結果を確認。
- `grep -Fxc` による追加行の完全一致数: `__init__.py` **1**、`commit_receipt.py` **1**、`report.py` **1**。
- pytest による焦点走・変異 harness・受入全走: **実装済み・未実走**。指定に従い pytest と `tools/run_tests.py` は起動していない。

`git diff --stat`:

```text
 orchestrator/qualification/contract.py        | 3 +++
 orchestrator/tests/test_t126_pegasus_tools.py | 6 ++++++
 2 files changed, 9 insertions(+)
```

`git status --porcelain`:

```text
 M orchestrator/qualification/contract.py
 M orchestrator/tests/test_t126_pegasus_tools.py
```

所有 2 file 以外の差分なし。

## 波及の静的列挙

- **直接 consumer:** `t126_driver.py:372` の `_identity_files()` が集合に追随し、追加 3 file も個別 hash と disk/HEAD blob 照合の対象になる。`identity.py:140` の和集合比較は 46 path に追随する。
- **受理形:** `series_identity()` の exact set 比較により、code key 集合は 43-key 形へ置換される。旧 40-key 形は `series identity code_identity required set mismatch` で拒否される。検証ロジック・schema・hash domain は変更していない。この受理・拒否は静的確認であり、今回の直接呼出し検査の対象外。
- **B1 の間接 consumer:** `collector.py:358/473/1168/1487/1515` と `artifacts.py:1291` は契約関数を経由して追随する。B1 の「6 file・24 行」は変更前の production/test における直接出現の棚卸しであり、間接 consumer 全体の件数ではない。歴史記録は変更していない。
- **B3 の共有 fixture:** `_attempt` は相対 path ごとに親 directory を作り、汎用内容を書き込み、fixture commit の blob から hash を取得する。追加 3 path は既存処理に追随し、basename の重複も衝突しない。fixture の追加修正は不要。
- **consumer test:** 既存の exact set 比較、`test_t126_qualification_contract.py:76` の集合由来 fixture、tracked path の parametrized test は集合に追随する。tracked path は静的には 46 ケースになる。`test_t419_probe_causality.py:42` の部分集合 assert と既存 verifier 4 file 包含 test は変更不要。
- **loader 閉包:** `contract.py` は既存の loader 閉包 member。実 repo の live binding を取得する経路では未 commit の bytes 差分が drift として拒否される。焦点走 4 file の成功は今回未実測。
- **script・verifier:** submit/job script の固定 path 列挙は required code 集合全体の複製ではなく、今回の追加に伴う変更は不要。verifier の個別束縛は tracked 9 file 中 4 → 7 file。s4 の経路棚卸しどおり、集合外の `__main__.py` / `cli.py` は追加していない。

## 総括

plan v2 の 1・2 を逐語どおり実装した。差分は所有 2 file の 9 行追加のみ。指定の件数・直接呼出し・反実仮想・anchor 検査を確認済み。commit、stage、stash、branch 変更、docs 編集は行っていない。