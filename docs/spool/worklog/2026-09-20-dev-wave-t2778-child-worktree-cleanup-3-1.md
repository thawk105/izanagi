---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2778-child-worktree-cleanup-3
seq: 1
title: T-2778 の remove-child の submodule reflog 判定に primary store の実在を加え、段 9 の dogfood を閉じる (コード、branch worktree-dev-wave-t2778-child-worktree-cleanup-3)
---

## 本文

- entry 1706 (D2163) → wave-2 (submodule の変換検査を superproject 限定に) の続き、同一 session。wave-2 の land (main c13914d44) 後の段 9 で
  実子木 `.codex/worktrees/t2778-author` の `remove-child` が今度は rc=20 `backup-precheck`「submodule reflog is unreachable from gitlink pin」
  (wave-2 木は removed)。原因は入れ子 submodule (ccbench → shirakami → googletest) の googletest module の HEAD reflog に clone 直後の既定 branch tip
  (`4267679b`、「checkout: moving from <既定> to <pin>」の old 側) が残り pin の祖先でないこと。この sha は上流と primary の同 path の module store に
  実在し、子の store を消しても失われない。A3-iii の「reflog 全 commit が pin から到達」は clone の既定 branch tip で必ず偽陽性になり、
  wave-2 時点でも実子木を撤去できなかった。
- 裁定 (親): reflog sha は「pin から到達 ∨ primary の同 path の module store に実在」で受理し、どちらでもない sha (子の store にしか無い local commit) は
  引き続き拒否 (A2 と同じ「削除範囲外に在るか」の原理)。Codex author が実装し fixture に `[default-branch-reflog]` (source の既定 branch が pin より先) を足した。
  変異 1 件 (store 実在の分岐を外す = 同 parameter 赤) で裏取り。受入・land・子木と wave-3 木の撤去結果は専用 handoff と insight §6.3 に記録する。
- 学び: tmp fixture の submodule は「pin を直接 clone」していたので clone 既定 branch の reflog が入らず、実子木 (GitHub から clone した入れ子 module)
  でしか出ない。段 9 の実子木 dogfood を完了判定に置いた効果が 2 巡続けて出た。

## 次の一手差分
