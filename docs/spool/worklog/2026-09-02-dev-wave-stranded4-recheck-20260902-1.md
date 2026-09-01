---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-stranded4-recheck-20260902
seq: 1
title: 取り残し branch 4 本の回収依頼を 3 度目として base main で独立に再判定し、22 path 全ての blob が main に実在すると確定して取り込み 0 件で閉じた (docs のみ、branch worktree-dev-wave-stranded4-recheck-20260902、実装面の差分ゼロにつき変異 matrix は DW-S04 の免除)
---

## 本文

ユーザー起票。「作業木も担当セッションも無い取り残し branch 4 本の成果を回収して land する」。
**取り込みは 0 件で閉じた。** 4 本とも内容は既に main にある。

- **依頼が挙げた commit 数 (6 / 3 / 2 / 1) は「main に無い commit の数」であって未着地量ではない。**
  依頼自身が三点 diff を根拠にしないよう指示していたが、commit 数も同じ性質を持つ。
  `worktree-dev-wave-t1933-reconciliation` は他 2 本の tip を祖先に持ち、
  `git merge-base --is-ancestor` が両方とも真を返す。下 2 本は独立の回収対象ではない。
- **着地判定は fork 点からの file 閉包を 1 path ずつ blob OID で照合して行った。** 閉包は
  19 / 8 / 9 / 1 path、distinct 22 path。branch 側の blob を main の全 blob 索引 13,440 件と
  突き合わせ、**main のどこにも無い blob は 2 件だけ**だった。その 2 件はいずれも fold が
  消費して削除した spool fragment であり、content_sha256 が `docs/spool/FOLDED.md` の receipt と
  一致し、本文は canonical 側に逐語で実在する (D1260 と、F606 の 2026-08-28 再発文)。
  **fragment の不在は消失ではなく fold 済みの正常形である。**
- **取り込まない理由は「既に在る」だけではない。3 つとも退行になる。** (1) `6f5de08ce` の
  insight README を入れると main の後継 `d1b9a2a75` が前身 `c778863e1` へ退行する
  (main 側にだけ fresh 再構成の provenance がある)。(2) fold 済み fragment を戻すと
  同一本文の D / F が二重採番される。(3) `df20d3631` の逐語 land は D1149 で決着済みの
  裁定待ちを live state へ戻し、かつ断片が持つ `[T-1273]` への更新操作は同 ID が active でないため
  fold が `transition-target` で拒否する。
- **実装面はゼロだった。** T-080 process-memo grouping の追加 `2ffb32a0e` と撤去 `1bafd884a` は
  対象 2 file について差し引きゼロで、fork 点からの file 閉包に test file が 1 本も現れない。
- **同じ結論は 2026-08-29 (1094) と 2026-09-01 (1129) が既に下していた。本 wave はそれを引用せず
  base main `cab0a265f` で独立に再導出し、一致を確認した。これで 3 度目である。** 1129 の base
  `24014bdb2` から main は先へ進んでいるが、判定は変わらなかった。
- **3 度繰り返す理由は、4 本が ref のまま残っていることにある。** ref だけを見る棚卸しは
  「main に無い commit を持つ branch」として毎回これらを拾い、着地済みかどうかは blob 照合まで
  進まないと分からない。処遇 (削除するか、着地済みと分かる印を付けるか) はユーザーの判断に属する。
- branch の削除はユーザー指示に従い 0 件。4 本とも ref のまま残した。

## 次の一手差分

### 新規

- {{T:stranded4-branch-disposition}} **P2・ユーザー裁定待ち**: 着地済みと 3 度確定した
  取り残し branch 4 本 (`worktree-dev-wave-t1933-reconciliation`、
  `worktree-dev-wave-acceptance-fastest`、`worktree-dev-wave-t1933-acceptance-longest-node`、
  `worktree-dw-c01-websearch-ruling-20260827`) の処遇を決める。ref を残す限り、ref だけを見る
  棚卸しは毎回これらを回収候補として挙げ、blob 照合まで進んで初めて 0 件と分かる。
  削除は D の裁定ではなくユーザー指示でだけ行う規律のため、ここでは選択肢の提示に留める。
