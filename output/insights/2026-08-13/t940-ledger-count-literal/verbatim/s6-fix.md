## 総括

指定どおり [test_check_ai_provenance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t940-ledger-count/orchestrator/tests/test_check_ai_provenance.py:1448) に 1 行だけ追加しました。production・docs は未変更、commit も未作成です。**実装済み・pytest 未実走**です。

### `git diff` 逐語

```diff
diff --git a/orchestrator/tests/test_check_ai_provenance.py b/orchestrator/tests/test_check_ai_provenance.py
index a2aba829..8e603699 100644
--- a/orchestrator/tests/test_check_ai_provenance.py
+++ b/orchestrator/tests/test_check_ai_provenance.py
@@ -1445,6 +1445,7 @@ def test_known_violation_ledger_matches_literal_entries():
         ("c96803854911dd989954c20d0955ad423e7d1207", "missing-codex-author", dw8c_ruling, dw8c_retry_note, ""),
         ("8ceebcdbe40fac27cb2a1fbd7a1b1e016894bd0e", "missing-codex-author", t316_ruling, t316_note, ""),
     )
+    assert len(provenance.KNOWN_PROVENANCE_VIOLATIONS) == len(expected)
     assert observed == expected
     assert len({row[0] for row in expected}) == len(expected)
     assert provenance._LEDGER_FINDING_KINDS == frozenset({
```

### `git diff --stat`

```text
 orchestrator/tests/test_check_ai_provenance.py | 1 +
 1 file changed, 1 insertion(+)
```

`git diff --numstat` は `1 0`、`git status --short` は対象ファイルの `M` だけです。

### 静的検査

- `python3 -m py_compile orchestrator/tests/test_check_ai_provenance.py`: rc=0
- AST parse: OK
- `git diff --check`: rc=0
- AST 上の assert 順序:
  - 1448: 動的件数一致
  - 1449: 内容完全一致
  - 1450: `expected` の SHA 一意性

### 受理・拒否挙動

| 入力 | 結果 |
|---|---|
| (1) 未承認 entry を production だけへ追加 | 1448 行が最初に赤。独立評価なら 1449 行も不一致 |
| (2) 既存 entry の note を1文字変更 | 1448 行は通り、1449 行が赤 |
| (3) `len()` は39、反復は38件の容器 | 1448 行が赤。隠された反復結果では1449行は通る |
| (4) 承認済み entry を production と `expected` の双方へ同期追加 | 1448〜1450行すべて通り、緑になるべき入力 |

### 所有外への波及可能性

- caller: テスト名の参照は定義箇所だけで、直接 caller はありません。pytest collection のみです。
- 共有 fixture: 対象テストは引数なしで、`expected` も関数ローカルです。共有 fixture への波及はありません。
- consumer test:
  - 同じ台帳を直接読む `test_production_registry_notes_satisfy_descriptive_contract` と `test_unregistered_malformed_finding_remains_rc1_with_production_registry` が存在しますが、今回のローカル assert 追加には依存しません。
  - 台帳を monkeypatch する registry schema、stale finding、stdout、forward-correction、waiver 系テストも関数単位で隔離されています。
  - 隣接する real-commit 検査は固定 SHA 表を独立に持ち、今回の件数 assert からは呼ばれません。

pytest は実行しておらず、テストを「緑」または要件を `closed` とは申告しません。