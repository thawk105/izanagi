---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2440-rulings-entry-f897-f888
seq: 1
title: [T-2440] /rulings 入口の収集 §1 に「carry 鎖を archive まで解決した実体本文へ走査語を当てる」を明記し (F888 再発の是正)、F897 の出力規則は D1868 で入口へ着地済みと照合して Codex 側鏡像の旧規則 1 句だけを同期した — 予算 5,623 の中で 5,623 bytes、意味等価な縮約 3 か所、安全義務の削除 0 (docs のみ、branch worktree-dev-wave-t2440-rulings-entry-f897-f888、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2440] (P2、entry 1364、F897 / F888) .claude/commands/rulings.md を直す: (1) 入口の出力規則 (F897)、
  (2) 収集 §1 に『carry 鎖を docs/archive/ まで解決した実体本文へ走査語を当てる』を明記 (F888 再発の是正)。入口の byte 予算
  5,623 (現在 5,621) の中で 2 件を同時に直し、予算の引き上げは独立審査対象なので行わない。docs/skill-self-improvement.md の
  command 入口の編集条件に従う。稼働 rulings-all-20260918 は spool fragment のみで同 file に触れていない (起動時に再確認)。
  着手直前の local main から fresh worktree。本題の 2 件だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **閉じた。** 対象 file は 5,621 → 5,623 bytes (上限 5,623、最長行 96 chars / 上限 180)。予算は上げていない。
- **(1) は起票後に別 wave で着地していた (F35 型の照合)。** F897 の是正「`all` は索引と推奨」は D1868 (2026-09-09、
  entry 1407、commit fbf245894) で入口へ入っており、第 17〜22 回は「推奨通りで」で裁定が成立している。依頼文の (1) は
  entry 1364 の起票文の写しで、着地済みの事実を反映していなかった。残余は Codex 側鏡像 `.agents/skills/rulings/SKILL.md`
  項 3 が「`all` は全件索引のみ」と旧規則のまま (8b7135c4f の同期でも残った) だった点だけで、同項を「`all` は索引と推奨」へ
  直した (2,982 → 2,979 bytes、上限 3,000)。入口の出力規則そのものは本 wave で 1 byte も変えていない。
- **(2) は収集 §1 に 1 句で入れた:** 「索引確定前に carry 鎖を archive まで解決した実体本文を `裁定` `決` `判断` `ユーザー` で
  (…) 総ざらいし」。表記は起点 entry 1364 の裁定逐語と F888 再発追記の是正方針 (「archive まで解決した実体本文へ当てる」) に合わせ、
  同 file 作法節の「worklog・archive・decisions・roadmap」と同じ bare `archive` にした。第 20・21 回 (entry 1596 / 1617) は
  既に carry 鎖を実体まで解決してから抽出しており、明記は現に行われている手順の固定である。
- **予算内に収めた縮約 3 か所 (いずれも意味等価、安全義務の削除 0):** (a) 収集冒頭「carry stub は実体へ統合し重複計上しない」→
  「carry stub は重複計上しない」(実体への解決は §1 の新句が明示するため重複を落とした)。(b) 収集 §2「`docs/decisions.md` /
  `docs/failures.md` の同語検索」→「decisions・failures の同語検索」(同 file の作法節・§2 後半と同じ bare 表記、対象台帳は同じ)。
  (c) 出力「N / M」→「N/M」(空白 2 byte)。check_docs の pin (`$ARGUMENTS` 1 回、Codex Skill の literal 列) には触れていない。
- 検査: `tools/check_docs.py` 違反なし、`tools/check_codex_agents.py` OK、`spool_fold.py --dry-run`、`git diff --check`、
  provenance 監査。受入全走は land 前に 1 回 (結果は land の受領証)。
- 軽量版 (docs-only)。段 2・3 は省略、実装子なし。段 6 相当として read-only codex レビュー 1 本 (`gpt-6-astra`、
  model call 10、stop_reason completed、`check_codex_output.py` OK) を回した — **GO: must-fix 0、should 0、nit 1**。
  縮約 3 か所とも意味等価 (§2〜§6 の収集源に carry stub 書式の独立行は 0 件、bare 名の参照先は一意、空白 2 byte)、
  安全義務の削除・弱化 0 (編集前後の対照表 7 行、command の 7〜9・20〜30・35〜64 行は区間ごとに完全一致)、
  bare `archive` は一意 (作法節・spool README の移動先)、P1 (F897 は D1868 / commit fbf245894 で着地済み、入口に推奨なしを
  許す読みは残らない) と scope 適合 (Skill の旧句同期は (1) の残余) を支持。予算・pin (`>` 判定で上限と等しい 5,623 は通る、
  `$ARGUMENTS` 1 回、Skill literal 12/12 残存)・fragment の事実命題 (D1868・entry 1407・第 17〜21 回・第 20/21 回の実体収集・
  bytes) と failures の supersede 文法 2/2 も独立計数で一致。nit 1 (本 fragment の参照名「F888 恒久対応」→ 該当句は F888 の
  再発追記にある) は親が現物 (F888 の 11 行目が D1756、26 行目が再発追記の是正方針) で裏取りして採用し、本文を直した。
  dev-wave 改善候補 0 (段 8 は無言通過)。

## 次の一手差分

### 完了

- [T-2440] `/rulings` 入口の是正を閉じた: (2) 収集 §1 に「carry 鎖を archive まで解決した実体本文へ走査語を当てる」を明記
  (F888 再発の是正、5,623 bytes / 上限 5,623)。(1) F897 の出力規則は D1868 (entry 1407) で入口へ着地済みと照合し、残余の
  Codex 側鏡像 SKILL.md 項 3 の旧規則 1 句だけを同期した。予算は上げていない。
  remaining: none
  base: 373970238e899633194a4653555af15a4d888a871fa429db81aa0cb57b3e2e11
