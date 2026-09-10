---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-astra-medium
seq: 1
---

## 再発

### F941

- **再発: 2026-09-10** — Codex worker のモデル変更は専用branchで受入22463 passedまで終えたが、
  landのrc=11と他sessionの処理中dirtyを見て、再試行を続けず終了した。
  DW-O23はstale/busyを再試行するのに、Skill末尾とcommand終端のrace後再起動記述を優先した。
  ユーザーが「なぜmain landまでしないの？」「自己改善よろしく」と指摘した。
  `.agents/skills/dev-wave/SKILL.md`、`.claude/commands/dev-wave.md`、DW-S09の再試行・停止を
  DW-O23へ統一し、同節に処理中dirtyを非接触で待って再照合する区別を統合した。
  正しさ検査やpostcondition failureの停止、他session所有物の保護は維持する。
  これはpromptの不整合是正であり機械的な再発不能保証ではない。
