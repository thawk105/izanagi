---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-15
wave: dev-wave-t2607-t316-gate-tree
seq: 1
title: [T-2607] t316 の条件関門と build 木を patch 済みの使い捨て木へ揃え、実経路で S6 を go まで到達させた (コード + docs、branch worktree-dev-wave-t2607-t316-gate-tree、変異 matrix = baseline PASSED・7/7 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザーは 3 件を同一欠陥として 1 wave で扱い、解消案を実測で決めてから実装するよう指示した。
  **この指示のうち「実測で決める」は前提が成立しなかった。** 「関門ごと落とす」案の不成立は
  D1625 (ユーザー裁定) と `verdict_s6` の現行契約による帰結であって、どんな測定値が出ても
  変わらない。段 2 のプランと段 3 の 2 レンズが独立に同じ結論へ達したため、親は実測を
  択一の決定ではなく採用案の到達確認へ回した。この順序変更は段 4 の裁定に明記してある。
- D1994 と D1864 は「直し方は定めない・扱いはユーザー裁定へ返す」としていた。本 wave の起動引数が
  それを上書きしたのは「誰が決めるか」だけで、却下済みの 3 案 (未使用変数だけの削除 /
  関門にだけ patch 木を渡す / stderr 判定の緩和) は却下のまま扱った。
- 親の暫定裁定 3 件のうち 2 件が子に反証された。詳細と訂正は
  `output/insights/2026-09-15/t2607-t316-gate-tree/README.md` の「段 3・段 6 が親を訂正した点」。
- 段 5 の実装子は dispatch の preflight (`qstat -Q` rc=1) が一過性に落ちたため pytest を
  1 度も起動できず、実走はすべて親が担った。段 6 の fix 子 2 本も、実 bwrap を要する node が
  子の sandbox で `NETLINK_ROUTE socket: Operation not permitted` になるため検証できず、
  計算ノードでの確認は親が行った。
- 設計判断は {{D:t316-gate-tree-alignment}}、実走で見つけた置き場の欠陥は {{F:sandbox-tmp-mask-checkout}}。

## 次の一手差分

### 完了

- [T-2505] 修正後の t316 実経路 (request `0:999027.nqsv`、Elapse 98 秒) で supply 腕が
  `stock-inert-preprocess-root-location-only` / comparison `stock-inert-root-location-only` の
  緑に到達し、family admission は admitted=true、S6 は go
  (`S6_SANDBOX_BUILD_SUCCEEDED`) になった。受領証は
  `output/env/pegasus/t316-sandbox-backend/0:999027.nqsv/receipt.json`。
  remaining: none
  base: 238e05bc08083df8e1d4551b93ef8706b80f7857a7ee3b5568830dff817099b2
- [T-2519] 既存機構で inert 要求が stock 同等の緑へ到達するかは、**2 つの driver で到達すると
  確定した**。`backoff_sweep` の driver 段は 2026-09-07 に bnode039 で
  (`output/insights/2026-09-07_t2228-driver-gate-liveness/README.md`)、t316 は 2026-09-15 に
  本 wave で到達した。D1936 項17 が名指さなかった「既存機構」は、緑に到達した既知の 2 経路で
  尽きている。**D1856 の繰延べはこの項では解除せず、そのまま維持する。**
  remaining: none
  base: 6cc6dcf811f8aa99deb2d7b9c6bcb1e20ce1890aa6fda44cb4c895e68ea4b96a
- [T-2607] 不一致の解消は {{D:t316-gate-tree-alignment}} で決め、実装して実測まで閉じた。
  採ったのは A-2 と同型の「patch を当てた使い捨て木を関門と両 build で共有する」形であり、
  CCBench が参照しない 3 変数の除去を同時に行った。後者が無いと patch を当てても両アームで
  未使用変数警告が出るため赤は解けない。
  remaining: none
  base: c8f6895809bb97ac65a47013ecd0d741f6b5bf0724af30dfbf20d071efdedf52

### 新規

- {{T:t316-gate-cache-residue}} **P2・新規**: t316 の条件関門の緑が、永続 third-party cache に
  残っている masstree の生成物 (`config.h`、`libkohler_masstree_json.a`) に依存している状態を
  解消するか決める。関門は configure と preprocess はするが生成の custom command を走らせないので、
  cache を掃除すると preprocess が通らなくなる。緑に到達した既知の 2 例 (A-2 と `backoff_sweep`
  driver 段) はどちらも `prepare_masstree_fetchcontent` で準備した base を使い、永続 cache を
  直指ししていない。t316 だけが直指しする。
  成果物影響 = 放置すると、cache を掃除した時点で t316 の S6 が
  `S6_CONDITION_GATE_UNPROVEN` へ戻り、この driver の成果物が supply effectuation の機械証拠を失う。
