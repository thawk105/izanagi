# 段 1 brief — 過剰実装・過剰ガードレール抑制

- scope: Claude/Codex 双方の next-tasks・dev-wave・rulings が、必要性を証明できない追加実装・追加防壁を提案、採用、裁定推奨しないための判断規則を追加する。
- 実アンカー: repo 内 `.claude/commands/dev-wave.md`、`.agents/skills/dev-wave/SKILL.md`、`.claude/commands/rulings.md`、`.agents/skills/rulings/SKILL.md`。
- 実アンカー: repo 外 personal 定義 `/home/SFC/tanab/.claude/commands/next-tasks.md`、`/home/SFC/tanab/.agents/skills/next-tasks/SKILL.md`。
- 共通正本候補: dev-wave は両入口が読む `docs/dev-wave/core.md`。rulings は Codex Skill が委譲する `.claude/commands/rulings.md`。
- 確定済みユーザー裁定: 「過剰実装・過剰ガードレールは避ける」を六つの利用面すべてへ効かせる。
- 既存被覆: `CLAUDE.md` 絶対規律5、`DW-G01`〜`DW-G05`、D605、phase3 見送り台帳は、根拠なしの一般化・hardening を既に抑制する。
- 不変条件: 絶対規律2/3、実在する正しさ欠陥、明示されたユーザー要求、現在の受入に必要な防壁を「過剰」として削らない。
- 不変条件: 新しい framework・一般化・互換層・gate・検査・台帳を、仮想リスクや将来の可能性だけで追加しない。
- 不変条件: 既存機構の再利用または局所修正で足りる場合は、それより広い仕組みを提案・実装しない。
- 成果物影響: 規則が無いと next-tasks が低価値 hardening を選び、dev-wave がレビュー所見から scope を膨張させ、rulings が仮想リスクをユーザー判断へ昇格させうる。
- 成果物: 各面に一度だけ効く短い規則と、重複のない委譲。現行 docs budget/address lint の上限は変更しない。
- scope 外: 自動スコア、複雑度計測、新しい guardrail checker、過去 task の再分類、既存安全規律の撤去。
- scope 外: next-tasks の母集合収集・既存優先順位・件数配分、dev-wave の9段構成、rulings の収集順・交差相談の変更。
- (P1) dev-wave は `docs/dev-wave/core.md` に一つの G 節を追加して両入口から参照するのが最小であり、両入口へ同文を複製しない。親の provisional 裁定であり攻撃対象。
- (P2) rulings は共通 dispatcher の作法にだけ追加し、Codex Skill は既存委譲で効かせる。親の provisional 裁定であり攻撃対象。
- (P3) next-tasks は共通 repo 正本が無いため、Claude/Codex personal 定義へ意味等価の短文を各一箇所追加する。親の provisional 裁定であり攻撃対象。
- 分割方針: docs-only 変更で実装面差分ゼロ。親が編集し、read-only Codex plan と敵対相談で過剰規則化・責務重複・安全規律弱化を攻撃する。
- 受入: `git diff --check`、`tools/check_docs.py`、`tools/check_codex_agents.py`、対象 Codex Skill の `quick_validate.py`、関連 docs/skill tests、受入全走。
