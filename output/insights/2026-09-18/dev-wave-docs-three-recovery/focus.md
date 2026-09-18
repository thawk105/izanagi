| 所見 | 判定 | 根拠 file:line | 成果物への影響 | 重要度 |
|---|---|---|---|---|
| 1：検出時点を「受入全走後、land lock内で初めて」と断定 | **closed** | `docs/spool/worklog/README.md:63–65`で未反映のmain側変化に限定し、dry-runで検出できる条件を明記。`docs/spool/worklog/2026-09-18-dev-wave-t2129-spool-carry-wording-1.md:7`も「場合がある」に限定。同`:39–41`で旧依頼引用を保持したまま訂正を補足。 | 検出時点の誤った一般化は解消。歴史記録と現行の説明を区別できる。 | must-fix（解消済み） |

静的に確認した実装経路は `tools/spool_fold.py:3693`（dry-runでも`plan_fold`）→ `:2491` → `:1893` → `:1830`（`transition-target`）。入力は作業木のworklog（`:2394`）で、先行fragmentの処理結果が次のactive集合へ渡る（`:2483–2491`）。修正文言はこの挙動と整合する。

`git diff HEAD`は指定の文書2本のみ。spool実装・裁定内容の変更はない。追加のmust-fix／should／nitなし。

## 総括

**GO — T-2129のmust-fix 1はclosed。**

未検証範囲：fold・dry-runの実行、pytest、受入全走、land時の挙動、provenance監査、T-2440・T-2669の再監査。今回の判断は指定範囲の静的照合のみ。編集・commit・テスト・再帰起動は行っていない。