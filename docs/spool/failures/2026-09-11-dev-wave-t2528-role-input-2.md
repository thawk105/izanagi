---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-11
wave: dev-wave-t2528-role-input
seq: 2
---

## 再発

### F43

- **再発: 2026-09-11** — T-2528のfix子は必須の総括見出しを欠き、CLI rc=0でもlauncherがf43_fragmentとして未受理にした。親は別のread-only focus子に未受理差分を独立監査させて採用した。既存の検収経路を使用し、新しい防壁は追加しない。原報告と検証記録は `output/insights/2026-09-11/t2528-role-input/README.md`。

### F433

- **再発: 2026-09-11** — T-2528で親がplanner source hashの追随だけを指定し、trigger-gating側の固定baseline 7箇所を落とした。単独走job991683の1FAILで検出し、D95 authorが両roleの固定hashだけを追随。修正後2 passed、既存helper・比較集合・assertionを維持した。検証記録は `output/insights/2026-09-11/t2528-role-input/README.md`。
