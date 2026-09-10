# 段 4 裁定と plan v2

## 所見裁定

- safety F1: real・scope 内・採用。next-tasks の選定規則変更は依頼本体なので、scope 外を母集合収集・既存優先順位・件数配分へ狭めた。
- safety F2 / minimality F1: real・scope 内・採用。追加必要性は自己申告でなく、対象機構と不足を挙げて確認する文にする。
- safety F3: real・scope 内・採用。非弱化対象を既存安全規律、ユーザー明示要求、現在の受入要件まで揃える。
- safety F4/F5: refuted。rulings の全件索引と既存安全規律の不変は文案で維持できる。
- minimality F2: real・scope 内・採用。byte/address 予算は増やさず、赤なら文面を縮める。whole-file pin が実在し意味上必要な場合だけ最小更新する。
- minimality F3: real・scope 内・採用。next-tasks は候補除外だけを担い、一般規則を各投げ文へ複製しない。
- minimality F4: real・scope 内・採用。rulings は新しい裁定を作らず、既存の裁定待ちを全件索引した上で過剰案の不採用を推奨する。
- minimality F5/F6: refuted。新 G 節・入口重複・personal 定義の repo 化は行わない。

## plan v2

1. `docs/dev-wave/core.md` の既存 `DW-G05` へ、追加実装・追加防壁を scope/must-fix に入れる必要条件を統合する。
2. `.claude/commands/rulings.md` の既存 `## 作法` へ、全件索引を維持したまま過剰案の不採用を推奨する条件を一つ追加する。
3. personal Claude/Codex next-tasks の各 `## 選定規則` へ、過剰追加候補を除外する意味等価な短文を一つずつ追加する。
4. `.claude/commands/dev-wave.md`、`.agents/skills/dev-wave/SKILL.md`、`.agents/skills/rulings/SKILL.md`、`docs/skill-self-improvement.md` は既存委譲で効くため変更しない。
5. checker、スコア、台帳、新節、出力投げ文への一般規則複製、byte/address 予算増を行わない。

## 禁止署名と通る正例

- 禁止署名: 仮想リスクまたは将来可能性だけを根拠に、framework・一般化・互換層・gate・検査・台帳を追加する。
- 通る正例: 現在の受入で false green を再現し、既存機構と局所修正ではその受理を止められない対象機構・不足を示した上で、その穴だけを閉じる最小 gate を追加する。

## 変異事前登録

- 実装面差分ゼロの docs-only wave なので `DW-S04` に従い変異 matrix を免除する。受入全走は免除しない。
