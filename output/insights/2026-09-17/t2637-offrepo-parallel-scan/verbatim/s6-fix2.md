## 変更一覧

- [tools/audit_dangling_commits.py:910](tools/audit_dangling_commits.py:910)：`_process_offrepo_iteration` の key を `(walk_key, 候補列内の位置)` に変更。869 行の `_OffrepoKeys` 型も更新。merge・ordered 再構築は既存処理で同じ key を使用。
- [test_audit_dangling_commits.py:1338](orchestrator/tests/test_audit_dangling_commits.py:1338)：`preserves_failure_counts` に読めない directory 5 個を設定。入れ子 root を含む期待 failures は `(5 + 1) × 2 = 12`。root 実行時は権限依存の検査だけ省略。
- [同ファイル:1408](orchestrator/tests/test_audit_dangling_commits.py:1408)：`preserves_first_seen` に Barrier で処理順を固定した hardlink fixture を追加。同一 worker の後順→前順処理、代表 path、OID 順 `[A, B]` を直接検査。
- [同ファイル:1574](orchestrator/tests/test_audit_dangling_commits.py:1574)：`propagates_worker_exception` に 300 ms 遅延する worker を追加。再送出時の完了 flag と thread 数復元を検査。

## 実走結果

指定コマンドを実走し、最終版は **155 passed（8.67 秒）**。非 root 実行のため権限依存の検査も通過しました。

反実仮想はメモリ上だけに適用し、各 1 件、計 4 件すべて赤化しました。

| 対象 | 反実仮想 | 検出結果 |
|---|---|---|
| A1 / B11 | tie-break を無効化 | OID 順が `[B, A]` |
| A2 / B10 | worker の onerror 計数を最大 1 回に制限 | failures が `4`、期待 `12` |
| A3 / M5 | 局所比較だけ `<` → `>` | 代表が `b/other.py` |
| B9 | join を除去 | 再送出時の完了 flag が False |

`git diff --check` 通過。AST 比較で変更関数が指定範囲内であることも確認しました。

## 変異 matrix への影響

M5 の比較行自体は不変です。967 行（局所）・1105 行（merge）の old はともに：

```python
if group_key not in keys or key < keys[group_key]:
```

key の形が変わったため、局所側の現在の old 3 行は：

```python
                key = (key_prefix + ((0, filename),), position)
                group_key = (candidate.object_id, identity)
                if group_key not in keys or key < keys[group_key]:
```

今回は局所側だけの比較反転で赤化を確認しました。

## 総括

指定の nit 4 件を修正・検証済みです。変更は対象 2 file のみで、指定外の既存テスト期待値、設計、受理集合、報告行は変更していません。git add / commit、実根走査は行っていません。
