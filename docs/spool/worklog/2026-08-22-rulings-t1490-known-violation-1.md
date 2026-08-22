---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: rulings-t1490-known-violation
seq: 1
title: [T-1490] known-violation 台帳登録の裁定を記録し、既に対応済みと確認した (docsのみ、branch worktree-rulings-t1490-known-violation)
---

## 本文

- `/rulings all 説明付き` の索引で提示した T-1490 (commit `09ce607b` に AI 関与を示す
  trailer が一切無く、全履歴 provenance 監査で `missing-ai-agent` として検出される件) に
  ついて、ユーザーが rulings の推奨案 (known-violation 台帳登録) をそのまま採用する裁定を
  下した (2026-08-22)。却下したのは `AI-Agent-Waiver` trailer による個別承認 (D105) —
  waiver は commit 時点で本人が付ける仕組みであり、確定済み過去 commit への後付けは
  履歴書き換えを要するため不適合と判断した。
- 本 fragment を commit する直前の自己検証として `python3 tools/check_ai_provenance.py`
  (全履歴監査) を実行したところ、commit `09ce607b` は**既に**
  `KNOWN_PROVENANCE_VIOLATIONS` へ kind=`missing-ai-agent` として登録済みで、
  rc=0・新規違反なし (`known-violations=44`) と判明した。登録した commit は `89ab8093`
  (`fix(provenance): external/ccbench gitlinkのユーザー直接commitをknown-violation
  登録する`、2026-08-21、T-1458 wave)。rulings でユーザーへ報告した時点
  (worklog entry 825、2026-08-22) ではこの登録がまだ main に取り込まれておらず
  新規違反として観測されていたが、並行していた別セッション (T-1458) が同じ対応を
  独立に完了し、その後 main へ着地していた。
- 採用した方針 (known-violation 登録) は既に実現済みであり、追加の実装 wave は不要。
  T-1490 はこの記録をもって完了とする。

## 次の一手差分

### 完了

- [T-1490] ユーザーは推奨案 (known-violation 台帳登録) を採用する裁定を下した。検証の
  結果、対象 commit `09ce607b` は既に別セッション (T-1458、commit `89ab8093`、
  2026-08-21) が `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS` へ
  kind=`missing-ai-agent` として登録済みであり、全履歴監査は rc=0・新規違反なしを返す。
  追加実装は不要。
  remaining: none
  base: fcc4710ddcffc3ba583f114d3c0dc9061b9d6c410cd2c1a2663268ed194d4a1e
