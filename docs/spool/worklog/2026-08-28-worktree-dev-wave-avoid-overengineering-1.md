---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-avoid-overengineering
seq: 1
title: Claude/Codex の next-tasks・dev-wave・rulingsへ過剰追加抑制規則を統合した (docs-only、branch worktree-dev-wave-avoid-overengineering、変異matrix免除)
---

## 本文

- ユーザー直接指示「過剰実装・過剰ガードレールは避ける」を、Claude/Codex 双方の next-tasks・dev-wave・rulings へ反映した。
- repo 内は `docs/dev-wave/core.md` の既存 `DW-G05` と `.claude/commands/rulings.md` の2箇所だけを変更した。Codex dev-wave / rulings Skill は共通 dispatcher 委譲で到達するため重複追記しなかった。
- repo 外 personal 定義 `/home/SFC/tanab/.claude/commands/next-tasks.md` と `/home/SFC/tanab/.agents/skills/next-tasks/SKILL.md` へ意味等価の候補除外規則を適用した。personal 変更は Izanagi commit に含まれない。
- 段2 plan 1本、段3相談2本、段6レビュー2本、焦点再レビュー3巡を実行した。局所修正の誤除外、主目的機能の脱落、必要性の自己申告通過、ユーザー要求範囲、予算縮約による既存義務の意味落ちを修正した。
- checker・スコア・台帳・新しい G 節・文書予算は増やさず、dev-wave core は変更前と同じ byte 数、rulings は変更前より小さく収めた。
- 実装面差分ゼロの docs-only wave なので変異 matrix を免除した。関連 test は `orchestrator/tests/test_check_docs.py` 571 passed / 3 skipped、`check_docs`・`check_codex_agents`・Codex Skill validator は緑。
- 一次資料は `output/insights/2026-08-28_avoid-overengineering-rules/`。最終受入全走は本記録 commit 後の tip で行うため、この entry に未実施値を書かない。

## 次の一手差分
