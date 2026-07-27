# [T-140] 段 2 プラン + 段 3 敵対相談の逐語 (凍結、2026-07-28)

親の裁定・要約は `../2026-07-28_t140-datastructure-axis-package.md` が正本。ここは逐語のみ。

| ファイル | 役 | レンズ | sha256 (凍結時) |
|---|---|---|---|
| `plan-datastructure-axis.md` | 段 2 プラン起草 | — | `b22e4f1191f1628eb6e85c9f88d4519945f8bbbf4bed086e452fb014a9334849` |
| `review-a-correctness-boundary.md` | 段 3 敵対相談 | 正しさ境界・信頼境界・恒真化 | `6b9a253fc5272ec131cea283a4d0f6365243970f6cc4780d2af942f8b60a5086` |
| `review-b-axis-efficacy.md` | 段 3 敵対相談 | 軸の実効性・科学的価値・リーク制御 | `3ac841a83935545063cabc33273f614a06c9ac4a8c0818fb89023607705e8df7` |

実行環境は 3 本とも `codex exec -m gpt-5.6-sol -c model_reasoning_effort="max" -s read-only`
(`DW-O01`)。いずれも静的検査のみで pytest を走らせていない (`DW-O05`) — **3 本の「緑」の記述は
存在せず、テスト結果として読んではならない**。defang は施していない (検出語 gate は clean)。

## リーク制御の注意 (必読)

**これらの逐語には具体的な container 戦略名・設計候補が含まれる。**
`docs/axis-onboarding.md` §5 と D45 (文書地雷) に従い、**coder / planner の入力へ射影しては
ならない**。射影してよいのは軸の生死の二値と中立な API 契約だけである。

現時点で coder へ届いた事実はなく、実測された勝ち点も存在しない (本 wave は性能を測っていない)。
将来この軸を再開する場合は、戦略名・source・順位を隔離成果物へ移してから E/F へ進むこと
(段 3 レンズ B の所見 B-6)。
