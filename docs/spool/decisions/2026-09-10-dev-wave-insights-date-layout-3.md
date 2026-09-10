---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-10
wave: dev-wave-insights-date-layout
seq: 3
---

## {{D:recoverable-failures}}. 修正可能な検査失敗は自律復旧し、人間へ再開を要求しない

**ユーザー指示:** AI自身が進められる状況で止まらず、手取り足取りの再開指示を要求しない。自己改善プロンプトも修正する。

**決定:** fail-closedは未受理のまま次段へ進むことを止める。原因調査・許可範囲の修正・再検証は続ける。
正式停止は人間の裁定/権限が必要な場合、承認前提を覆す新事実、許可範囲で復旧不能な場合に限る。
未受理workerの残差分は未完了として次のauthorが独立監査し、元の失敗記録を保持する。
検査器の弱体化、権限拡大、未監査差分の採用は認めない。

**実装:** `docs/dev-wave/core.md` のDW-STOPと `docs/dev-wave/operations.md` のDW-O01/O02へ統合した。
読取ログもNFC対象と明示し、非NFC fixtureは原文を変えずASCII escape表示する。既存の文字範囲禁止も維持する。
予算上限・段構成・実装担当の権限は変更しない。
