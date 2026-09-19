---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2778-child-worktree-cleanup-4
seq: 1
title: T-2778 の remove-child の reflog 判定に「任意の local branch が保持」を加え、段 9 の dogfood を閉じる (コード、branch worktree-dev-wave-t2778-child-worktree-cleanup-4)
---

## 本文

- entry 1706 (D2163) → wave-2 → wave-3 の続き、同一 session。wave-3 の land (main 65fe36a94) 後の段 9 で実子木 `.codex/worktrees/t2778-author` の
  `remove-child` が phase `integration`「HEAD reflog history is unreachable from main and retained branch」で rc=20 (wave-3 木は removed。
  backup-precheck の 2 件は wave-2/3 で解消済み)。原因は DW-S05-A の手順どおり同じ author 木で fix1〜fix6 の branch を切り替えてきたことで、
  HEAD reflog に各 fix branch の tip が残り、manifest の branch (main tip から切った最新 fix branch) からも main からも到達しない。それぞれの
  local branch が保持しており喪失ではない (tool は子 branch を削除しない)。1706 時点の規則「main ∨ manifest の branch」は、この手順に従う実子木を
  必ず拒否する (親が reflog 全 sha の branch 包含を事前実測: 15 sha 全てが local branch に含まれる)。
- 裁定 (親): reflog sha は「main ∨ manifest の branch ∨ 任意の local branch (`git branch --contains`) から到達」で受理し、どの branch にも無い sha
  (reset で捨てた commit) は引き続き拒否 (削除範囲外に在るかの原理、A2/fix6 と同じ)。Codex author が実装し正例
  `test_remove_child_reflog_retained_by_other_branch` を足した。変異 1 件で裏取り。受入・land・撤去結果は専用 handoff と insight §6.5 に記録する。
- 段 9 の実子木 dogfood は 3 巡続けて tmp fixture に無い実環境の差 (submodule の gitattributes、入れ子 module の clone 既定 branch、同一木の
  branch 切替) を出した。tool の受理述語は「削除範囲外 (main・local branch・primary module store) に在るか」に統一された。

## 次の一手差分
