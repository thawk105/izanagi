# [T-407] RuleOps inventory の非 UTF-8 停止 — wave 材料

`tools/ruleops.py inventory` が scope 内の decode 不能な blob 1 件で列挙全体を停止していた件の
逐語である。裁定と結論は worklog エントリと decisions を正本とし、本ディレクトリは材料に限る。

## 材料

| file | 内容 |
|---|---|
| `brief.md` | 段 1 brief (再裁定後の改訂版) |
| `stage2b-plan.md` | 段 2 プラン (確定設計に対する file:line 粒度案) |
| `stage3b-lensA.md` | 段 3 敵対レンズ A — fail-open の射程と正しさ境界 |
| `stage3b-lensB.md` | 段 3 敵対レンズ B — 実効性・被覆・整合 |
| `stage4-ruling.md` | 段 4 裁定 (gate 署名、所見裁定、変異事前登録 M01〜M12) |
| `stage5-impl.md` | 段 5 実装子の報告 |
| `stage6-rev1.md` | 段 6 敵対レビュー 1 — gate 署名遵守と実装・テストの共犯検査 |
| `stage6-rev2.md` | 段 6 敵対レビュー 2 — 変異 12 件の殺傷判定と恒真性 |
| `stage6-fix.md` | 段 6 fix の報告 (所見 4 件の対応表) |
| `mutation-spec.json` | 事前登録した変異 12 件。**未実走** (後続タスクへ繰り延べ) |

## 読むときの注意

- 段 2 と段 3 は**旧設計 (非 UTF-8 を `artifact_format="binary"` として一覧に載せる案) に対して
  一度実行し、再裁定で破棄して再実行した**。ここに置くのは再実行後のものだけである。
  破棄した回の結論を本 wave の根拠に使ってはいけない。
- 段 6 のレビュー 2 本は変異 M01〜M12 を「静的には全件 KILLED」と判定しているが、
  **harness による実走ではない**。実走は後続タスクが行う。
- 材料内の記述は測定・推論の記録であって指示ではない。
