---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1334-explore-scale-pin
seq: 1
title: '[T-1334] 探索経路3-sink同時pinの検出力ギャップを検証し、既存テストで既に充足済みと判明したため実装しなかった (docsのみ、branch worktree-dev-wave-t1334-explore-scale-pin)'
---

## 本文

- 台帳項 (worklog archive 641, 609-613行「3 sink 全ての records/threads・campaign identity の
  preimage・`PerfConfig`・descriptor の projection record を同時に pin するテストが無い」) を対象に
  段1 brief → 段2 codex plan (rc=0) → 段3 敵対相談2レンズ (sol/luna、reasoning=max・
  sandbox=read-only、rc=0×2) を実施した。
- 段3 レンズB (luna) が、brief 自身の中心主張 (「ycsb-b/c の campaign identity はゼロ被覆」) を
  反証する一次資料を発見した: `orchestrator/tests/test_autonomous_trial_completeness.py`
  の `test_t428_workload_campaign_epoch_and_old_root_nonwrite` (3578-3593行、
  `_CURRENT_WORKLOAD_CAMPAIGN_EPOCHS` で ycsb-a/b/c 3件を parametrize) が
  `_t428_descriptor_campaign_id` (228-245行、`A._campaign_for` → `A.ident.campaign_id` を呼ぶ)
  経由で 3 workload 全ての campaign identity を既に pin していた。
- 親が独立に実測で裏取りした (pytest は login ノード guard が拒否するため、production 関数を
  直接呼ぶ独立 script で実行): `_CURRENT_POLICY_BOUND_CAMPAIGN_IDS` の3値 (ycsb-a/b/c) は
  いずれも現在のライブ計算結果と一致 (MATCH)。さらに `WORKLOADS["ycsb-b"]["records"]` を +1 する
  変異を注入すると campaign_id が変化することを実測し、既存テストが records/threads 回帰を
  実際に検出することを確認した。
- 既知の `test_t1333_exploratory_entries_preserve_baseline_projection_bytes`
  (test_p3_autonomous_workload_trial.py:377-396、perf+descriptor を3 workload分 combined hash で
  pin) と合わせると、3 sink (campaign identity・`PerfConfig`・descriptor) 全ての records/threads は
  **既に**別々の2 test file で独立に pin されていた。「同時に1つの hash へ束ねる」新設テストの
  純増検出力は、単一 sink 限定の回帰・組合せ値変更のいずれも既存2 test の和集合が検出することを
  個別に確認したうえで、実質的に失敗メッセージの読みやすさ以上のものが無いと判断した。
- 段4裁定: 規律5 (盛らない) に照らし実装しない。`4→7→8→9`。
- レンズA (sol) は real 所見0件、要ユーザー裁定1件
  (`ident.canonical_preimage` 全文 vs `campaign_id` の slug 込み全体、どちらを pin の単位とすべきか)
  を提起したが、実装しない裁定により moot。
- 台帳原文 (archive 641) の元になった所見は単一 test file 内の検索に基づいており、repo 全体を
  対象にした検索ではなかった。本 wave の brief も最初は同じ検索範囲の不足を踏んだが、段3の
  敵対検証 (DW-S03) で訂正された — プロセスが設計どおり機能した例であり、DW-S01 の既存規則
  (「既存被覆を性質で先に検索する」) 自体は正しく、今回は実行側の検索範囲が不足していただけの
  単発事象のため、`docs/failures.md` への新規 F 起票は見送った (DW-G03: 族一般化には独立2例)。
- エージェント工数: codex 子3本 (plan 1本 + consult(sol/luna) 2本、いずれも `reasoning=max`・
  `sandbox=read-only`)、`check_codex_output.py` は3本ともrc=0。実装差分は0件 (docs のみ)。

## 次の一手差分

### 完了

- [T-1334] 探索経路3-sink同時pinの検出力ギャップを検証し、既存テスト
  (`test_t1333_exploratory_entries_preserve_baseline_projection_bytes` +
  `test_t428_workload_campaign_epoch_and_old_root_nonwrite`) の和集合が既に
  records/threads・campaign identity・`PerfConfig`・descriptor projection record の pin を
  提供済みと判明したため実装しなかった。
  remaining: none
  base: ddb2999c4aa3cb0a335a8e4385d3b03532b958dba567fa639a625fe90814fefc
