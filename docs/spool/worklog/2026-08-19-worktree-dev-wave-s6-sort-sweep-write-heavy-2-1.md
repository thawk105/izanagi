---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: worktree-dev-wave-s6-sort-sweep-write-heavy-2
seq: 1
title: s6_sort_sweep write-heavy/balanced 偵察 sweep 再実行の依頼は stale premise と判明し、D46/D47/D328 に照らし実装しないと裁定した (docs のみ、branch worktree-dev-wave-s6-sort-sweep-write-heavy-2 + sibling wave dev-wave-s6-sort-sweep-balanced2)
---

## 本文

- 2つの並行 /dev-wave command (`s6_sort_sweep.py` write-heavy 担当・balanced 担当) が
  同時刻に起票された。両方とも「`--report` が『provenance がまだ無い』と返したので本走が必要」
  という同一の前提で、計算ノードへの sweep dispatch 直前まで準備が進んでいた。
- write-heavy 側セッションの段1 brief 前提実測 (DW-S01) で、この前提が誤りと判明した。
  「provenance がまだ無い」は pin drift (旧 `d706650` → 現行 `511c953`、[T-816] 手順4、
  commit `fb5e74a1`、2026-08-12) による campaign identity の変化が原因であり、未計測の証拠では
  ない。write-heavy/balanced とも旧 pin での certified provenance が git 追跡済みで既に存在する
  (commit `ffa383f4`)。
- さらに、このタスク自体 (段6前提タスク (i)、D44) は D46 (2026-07-10) で write-heavy/balanced
  双方を含め 32 本走 + 6 再測点で完走・certified・「sort 軸に floor 超地形は見当たらない」と
  結論済みであり、後継決定 8a (2026-07-12 完了、D47 決定5ほか) で sort 軸自体が放棄され
  trigger-gating 軸へ差し替え済みと確認した。8a 由来軸すら「低競合動作点の単独再ホストはしない」
  と裁定されており (2026-07-14)、現在の主経路 (8b/8c) はいずれも sort 軸を参照しない。
- balanced 側セッションが cross-session message を受けて独立に同じ一次資料 (`git log`・
  `pin.py`・D46 本文) を確認し、同じ結論に達した。両セッションで裁定 inbox
  (`/work/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-19-s6-sort-sweep-balanced-writeheavy-pin-drift-stale.md`、
  repo 外) へ選択肢 a/b/c を提示し、ユーザーへ返した。
- ユーザーは推奨案 (b: stale premise として docs のみの carry closure で終える) をそのまま
  裁定した。D328 (2026-08-12、「凍結チェーン検証はしばらく保留」) が同じ [T-816] pin bump との
  衝突を契機に成立しており、「pin 前進が機構を赤にするなら束縛が主張に要るかを先に問う」という
  基準に本件がほぼ該当することも裁定の後押しとなった。
- 重複を避けるため、balanced/write-heavy 両 workload の記録は本 fragment 1 本へ統合する
  (write-heavy 側セッションが代表)。balanced 側セッションは worktree を畳んで追随せず終了した。
  write-heavy 側の詳細分析一次資料 = `docs/handoff/2026-08-19-s6-sort-sweep-write-heavy.md`
  (本 branch の commit `245125d9`)。balanced 側の独立検証一次資料 = 上記 rulings-inbox エントリ。

## 次の一手差分

### 新規

- {{T:dw-s01-decision-provenance-depth}} **P3・新規**: `DW-S01` の前提実測は「引用した
  decision の結論」までしか明示的に要求していないが、「decision が属するタスク台帳自身の
  完了マーク」と「その後の派生決定が premise を上書きしていないか」まで辿る必要があるケースが
  実在した (本件: D46/D47/8a)。`docs/dev-wave/core.md` の `DW-S01` 等へ明文化する候補。
  core/operations/workers.md の3層予算は満杯のため、本 wave では reference 節への統合を
  試みずユーザー裁定へ返す。
