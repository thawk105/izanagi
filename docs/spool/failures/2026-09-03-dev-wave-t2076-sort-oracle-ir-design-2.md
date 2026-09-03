---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-03
wave: dev-wave-t2076-sort-oracle-ir-design
seq: 2
---

## 新規

### {{F:parent-share-of-must-fix-never-executed}}. 親担当と分割した must-fix が実行されないまま wave が 完了 で閉じた [手順漏れ]

- 事象: [T-2145] の段 6 裁定は F4 (現役 docstring / docs が旧「動的反例 gate」を名乗る) を
  real・must-fix とし、`orchestrator/campaign/p3_s4_loop_sort.py:47` と
  `orchestrator/campaign/s6_sort_sweep.py:28` を fix 子へ、
  `docs/phase3-s5-sort-runbook.md:190` を「親が段 7 で書く」分として分割した
  (`output/insights/2026-09-02_t2145-sort-oracle-ir/s6-review-adjudication.md:49-55`)。
  **fix 子担当の 2 docstring は着地し、親担当の docs だけが着地しなかった。**
  それでも同 wave は worklog entry 1214 で [T-2145] を完了として記録し、次の一手からも消した。
  結果として local main の現役 runbook は、受理言語を閉じた IR へ縮めた新しい実験を、
  旧 raw C++ 実験の proof chain (有限 corpus 上の反例探索・compile 失敗は候補 `REJECT`) で
  説明し続けた。検出は翌日の後続 wave の段 3 敵対レンズで、実害は誤記述の滞留に留まった。
- 根本原因: 分割は段 6 裁定文 (insight) に書かれ、実行は段 7 で行われるが、**両者を突き合わせる
  工程が無い。** 子担当分は成果物 (patch) が来なければ親が気づくのに対し、親担当分は
  「親が後で書く」という宣言だけが残り、書かなくても検査は 1 つも赤くならない。
  `DW-O12` は裁定予定を worklog へ写すことを禁じていたが、**裁定した親担当分を実行したかの
  照合**までは求めていなかった。F262 (逐語から台帳へ写すとき件数が落ちた) とは別型である —
  本件は転記ではなく実行の欠落で、F262 の件数照合を行っても検出できない。
- 恒久対応: `docs/dev-wave/operations.md` の `DW-O12` へ
  「親担当と分割した裁定項目は段 7 前に着地差分と突き合わせる」を追記した。
- 再発検知: 段 7 前の目視照合。機械化は未実装で、裁定文の分割記法が定型でないため
  lint 化には形式の固定が要る (F262 と同じ制約)。

## 再発

### F655

- **再発: 2026-09-03** — 共有 checkout ではなく**別 worktree** を指す `cd` を、worktree 隔離に
  入る前の session で 1 度実行した。この向きの逸脱は guard に掛からず黙って通り、以後の
  相対 path 読みが**古い別 checkout** を指した。`docs/archive/` の一覧が古い版のものになり、
  実在する file を「無い」と誤認した。復帰は元 path への `cd` だけで足りた。

## supersede 追記

- F655 **supersede: 2026-09-03** — 「症状は即座かつ明確」は共有 checkout 向きの逸脱に限る。隔離前の session が別 worktree へ逸れる向きは拒否されず、誤った読み取りとして静かに現れる。
