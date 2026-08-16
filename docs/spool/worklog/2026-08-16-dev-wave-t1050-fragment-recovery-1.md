---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1050-fragment-recovery
seq: 1
title: 取り残し branch 3 本を内容で再判定し、真の未着地 1 本だけを回収した — 依頼が根拠にした差分量は着地済みの branch でも大きく出る指標だった (docs のみ、branch worktree-dev-wave-t1050-fragment-recovery)
---

## 本文

- **依頼の前提を段 1 の実測が覆したため、wave を docs-only へ縮小して段 5・6 を飛ばした。**
  依頼は 3 本のうち 2 本を実装面 (checker 886 行、`hooks/guard_bash.py` 889 行) の取り残しとし、
  Codex author (D95) を要求していた。実測では両方とも既に main へ着地しており、着地する実装面は
  1 行も無い。`DW-C00` の既定軽量版で子ゼロ、`4→7→8→9` と裁定した。
- **`worktree-dev-wave-known-red-octopus` (`05279797`) は回収しない。** `git cherry main` の
  非 merge 3 commit が全て `-`。`docs/archive/worklog-phase3-0813-539-540.md` に
  「land を推さない」の明示裁定が既にあり、理由は後続 v2 (`8d645ee4`) が実環境欠陥を修正済みで
  旧版の再 land が退行になること。main に `tools/check_acceptance_reds.py` が実在する。
- **`worktree-dev-wave-t1025-impl` (`87223966`) は回収しない。** branch 名では裁定が出ず、
  タスク ID `T-1025` で追って初めて着地が判明した (`docs/archive/worklog-phase3-0816-569-570.md`)。
  着地 commit は `4f47bc74` で `git merge-base --is-ancestor 4f47bc74 main` が rc=0。
  着地版は台帳の 6 形に加えて実測同族と `dd` の非対称まで閉じた上位互換で、期待表 135 件・
  変異 8/8 KILLED・反転検査 `WIDENED=0` を伴う。branch が足す 11 関数
  (`_sed_read_only` 〜 `_argument_hits_protected`) は全て main に実在し、branch 側はテスト 0 行。
  **branch 名の grep だけでは見つからない裁定があり、タスク ID での再検索が判定を反転させた。**
- **`worktree-dev-wave-t1050-s8b-admission` (`9bd0b270`) だけが真の未着地。** F222 再発の
  failures fragment 22 行。識別できる逐語 (`1,006,920` / `877 秒`) が `docs/failures.md` と
  `docs/archive/` の双方で 0 件であることを以て、path でなく内容で未着地と判定した。
  未 land branch の merge は land の fold 形状検査に掛かるため cherry-pick で回収した。
- **依頼が根拠にした `git diff --stat main...<branch>` は未着地量の指標ではない。** 三点記法は
  merge-base から branch tip までの branch 側全作業を出すため、既に着地した branch でも大きな
  insertions を返す。実際 (1) は 2,246 insertions を示しながら `git cherry` では全 commit が `-`
  だった。この誤読は F270 の 3 例目 (新規 F を採らず再発) として記録した。
- 3 本とも branch は削除していない (ユーザー指示が無いため)。
- 受入は実測前に欄を作らない。結果は本エントリの land 前に追記する。

## 次の一手差分

### 新規

- {{T:stranded-branch-landing-lint}} **P2・新規**: 取り残し branch の着地判定を機械検査にする可否を
  裁定する。F270 の恒久対応は「lint 化の可否は裁定へ返す」で止まっており、本 wave が独立 3 例目
  (代理指標は順に path 実在 / lease 混雑の推定 / 三点 diff の差分量)。`DW-G03` の
  「族一般化には独立 2 例」は既に満たしている。判定材料は `git cherry` の patch-id、
  branch 名に加えたタスク ID での台帳・archive 検索、内容逐語の照合の 3 点で、
  いずれも機械化できる。実装面のため Codex author が要る。
