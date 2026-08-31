---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-01
wave: worktree-dev-wave-stranded4-recheck-20260901
seq: 1
title: 取り残し branch 4 本を base main で再判定し、3 経路すべてで着地済みと確定して取り込み 0 件で閉じた (docs のみ、branch worktree-dev-wave-stranded4-recheck-20260901、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。「main へ未着地のまま残っている branch 4 本を回収する」。**取り込みは 0 件で閉じた。**
一次資料は `output/insights/2026-09-01_stranded4-branch-recovery/`。

- **依頼の前提 (4 本が未着地) を段 1 前の実測が覆した。** 4 本とも内容は既に main にある。
  同じ判定は 2026-08-29 の wave (archive エントリ 1094) が下していたが、本 wave はその結論を
  引用せず base main `24014bdb2` で独立に再導出して一致を確認した。
- **着地判定の経路は 3 つあり、本件では 3 つとも実際に使われていた。** (1) canonical へ fold し
  `docs/spool/FOLDED.md` に content_sha256 の受領証が残る、(2) archive worklog へ別文言で吸収され
  受領証にも canonical の逐語にも一致が出ない、(3) insight の `sources/` へ原文 blob として保存され
  canonical にも受領証にも現れない。**1 経路だけを見た判定は 4 本とも「未着地」と誤る。**
  経路 3 は本 wave が 2 度目の往復の末に見つけた。
- **未着地量は fork 点からの file 閉包で測った。** commit が触る file だけを数えると、競合解消で
  内容を入れた merge を取りこぼす。`git diff --name-only $(git merge-base main <branch>) <branch>` で
  19 / 8 / 9 / 1 file を得て、distinct 22 path を 1 本ずつ blob 照合した。三点 diff の
  file 数・行数は根拠に使っていない。
- **実装面はゼロだった。** T-080 process-memo grouping の追加 `2ffb32a0e` と撤去 `1bafd884a` は
  対象 2 file について差し引きゼロで、fork 点からの file 閉包に test file が 1 本も現れない。
- **取り込まない理由は「既に在る」だけではない。** `6f5de08ce` の insight README を取り込むと
  main 側の後継 `d1b9a2a75` が前身 `c778863e1` へ退行する。4 branch の merge は、エントリ 1081 が
  「source tip・旧 merge・実装・撤去・停止 tip を非祖先のまま保つ」と記録した意図を崩す。
  `df20d3631` の逐語 land は D1149 で決着済みの裁定待ちを live state へ戻し、かつ断片が持つ
  `[T-1273]` への更新操作は同 ID が active でないため fold が `transition-target` で拒否する。
- **file 閉包 22 path のうち、main のどの path にも無いのは 2 blob だけだった。**
  停止した reconciliation の spool 断片 `bee4d47fd` と、その insight README `c778863e1`。
  エントリ 1081・1094 の先例に従い原文のまま insight の `sources/` へ保存した。
  **廃案となった手順の記録であって正本ではない**と明記し、記述にある merge commit
  `60c758a86` `8b677a197` が main の祖先でないことを添えた。`docs/spool/` の外に置くため
  fold の入力にはならない。
- branch の削除はユーザー指示に従い 0 件。4 本とも ref のまま残した。

## 次の一手差分
