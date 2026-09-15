## 現物で数えた行番号

- `main` 内の `run_campaign(...)`: **8661行**
- `build_cells.invoke_build` 内の `build_fn(...)`: **4708行**（変更不要）

ソースとASTで確認し、2表の pin が8661で一致することも確認しました。

## 変更した差分

対象: `orchestrator/tests/test_ccbench_spawn_sites.py`

```diff
@@ 945行
-        8659,
+        8661,
@@ 2721行
-            "wave t2027", "campaign", "<module>.main", 8659,
+            "wave t2027", "campaign", "<module>.main", 8661,
```

変更がこの数値2箇所だけであることを確認しました。

## 実走した検査

静的検査と `git diff --check` は成功。

指定の4 nodeid は `tools/run_tests.py` 経由で起動を試みましたが、`qstat -Q preflight rc=1` により **rc=16、child_started=false**。テスト本体は未実走です。親の受入全走を代替しません。

## 波及可能性の静的列挙

- 所有外 caller: 本番コードへの変更なし。`orchestrator` 内の検索では対象テスト台帳への外部参照は未発見。
- 共有 fixture: 変更なし。既存 `monkeypatch` の契約も不変。
- consumer test: 同ファイルの台帳照合・分類・未審査検出・entry removal が更新値を参照します。assert・分類条件は不変です。

## 総括

**実装済み・未実走**。commit・push はしていません。

最後の操作で [fix-spawn-sites.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2596-impl/fix-spawn-sites.patch) を出力しました。出力元差分で確認した内容は **22行、空ではなく、対象テストファイル1つのみ**です。