---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t472-canonical-predicate-consumers
seq: 1
title: [T-472] freeze 由来 gate_predicate の 2 consumer に正準述語 membership を足した — 起票の前提は誤りで受理集合は既に閉じており、純増は consumer-local 防御層と検出力 (コード + docs、branch worktree-dev-wave-t472-canonical-predicate-consumers)
---

## 本文

- **起票の前提が誤っていた (段 1 前提実測)。** worklog (193) の [T-472] は
  「この 2 consumer には旧 blacklist しか掛かっていない」と書いたが、親の実測では
  [T-428] の membership は `p3_s4_loop.quarantine` の marker 分岐から**既に推移的に効いていた**。
  `TRIGGER_MARKER_ID` は `axis_trigger_gating.MARKER_ID` の別名で、2 consumer はどちらも
  この marker で quarantine を呼ぶ。凍結 6 述語 (mask 8/31/4/31/8/31) も全て正準で、
  [T-428] の land は s1 driver を壊していない。**受理集合は着手前から閉じていた。**
- したがって本 wave の成果は受理集合の縮小ではなく、**consumer-local な防御層と、
  それを固定するテストの検出力**である。追加した 2 gate は
  **現行凍結値では発火しない regression sentinel** であり、「初回閉包」ではない
  (段 6 レンズ A の指摘を採用して命名を是正した)。
- **親の段 1 brief も一部誤っていた。** brief は「未 pin なので変えれば赤ゼロで開く」と書いたが、
  共有 quarantine の 32 受理と非正準拒否は `test_p3_s4_loop.py` が既に pin していた。
  真の未 pin は (a) consumer-local 層の不在、(b) 校正側の marker 結線、
  (c) 凍結 6 セルが述語としては 3 種類しかないこと。段 4 で訂正した。
- **段 4 の変異事前登録に 4 件の誤りがあり、段 6 レンズ B が走らせる前に検出した。**
  M2 の期待 node 不足、M5 の登録 node が存在しない path 由来の**偽 kill**、
  M6/M7 の期待集合が shared 層 2 node を落としていたこと、
  M3/M4 が「検査を省く」変異では正例を赤にしないこと。是正後は 7/7 が node 集合完全一致で KILLED。
  是正しなければ harness は全て `MISMATCH` にしていた。
- **`DW-M03` に従い M1 は kill に合算しない。** direct consumer gate を消しても共有 quarantine が
  同じ入力を拒否するため受理集合は不変で、変わるのは拒否位置と診断だけである
  (診断感度 pin として別枠に記録)。実効 semantic kill は M2〜M7 の 6 件。
- 段 3 / 段 6 で real と裁定した **scope 外所見 4 件**は実装せず裁定パッケージへ回した
  (U-1 strip 同値による identity 多重化、U-2 `configuration` 別名の silent fall-through、
  U-3 freeze 生成層の semantic membership 欠落、U-4 `sort_best.comparator` の権威集合不在)。
  正本 = `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7。
- **実装しないと裁定した所見 2 件**: `ident_all` 固有テスト (共通枝のため等価変異で区別できない)、
  S8b の実 `prepare_cell` 正例 (実 build 費用が大きく、未検証という制限を insight に明記)。
- **`DW-M08` の対照走行で純増検出力を実測した。** 追加 7 テストを除外した集合へ同じ M1〜M7 を
  走らせると、M1〜M4 は **SURVIVED** (consumer-local 層の退行は wave 以前のテストでは
  1 件も検出できなかった)、M6/M7 は shared 層 2 node だけの KILLED に縮んだ。7/7 期待一致。
- 対照走行は Pegasus queue 混雑で dispatch rc=16 に当たって 1 度 fail-closed 停止し、
  untracked な insight による clean-tree 拒否でもう 1 度停止した。いずれも harness の防壁が
  正しく発火したもので、tree は毎回復元されている。記録 commit 後に走り直して完走した。
- **段 8 の dev-wave 改善候補 2 件は、いずれも既存正本で被覆済みのため不採用とした。**
  (a) 「起票の前提を覆す新事実が出たとき止めるか narrow するか」は `DW-S01` が
  「brief に出して段 4 で再裁定する」と既に規定していた。(b) 「親の受入を login ノードで
  直接走らせない」は `CLAUDE.md` が環境専用 runbook へ委譲済みで、`DW-O18` へ書くと
  横断 docs へのマシン密結合と重複になる。

## 次の一手差分

### 完了

- [T-472] 2 consumer に consumer-local な正準述語 membership を足し、32 正準述語の受理・
  凍結 6 occurrence の受理・固定文言での非正準拒否・両層 composition をテストで固定した。
  変異 7/7 KILLED (node 集合完全一致)、受入全走 5974 passed / 19 skipped。
  起票の前提が誤っていたこと、保証が regression sentinel であることを insight へ記録した。
  scope 外 real 所見 4 件は {{T:t472-scope-out-rulings}} へ分離した。
  remaining: none
  base: 7c6de5ff743e9612e1766dd104592d667b7ca7642f610591ef6e1c62154a0820

### 新規

- {{T:t472-scope-out-rulings}} **P1・ユーザー裁定待ち**: [T-472] の段 3 / 段 6 で real と裁定した
  scope 外所見 4 件。U-1 = `is_canonical_predicate` の `strip()` 同値により
  外周空白付き述語が受理され、畳まずに materialize されるため同じ mask から複数の
  `src_token` / `variant_id` を作れる (推奨: materialize 前に正準 bytes へ畳む)。
  U-2 = `prepare_cell` の `configuration` dispatch に拒否 `else` がなく、別名・未知構成は
  述語検査も quarantine も飛ばして flags-only cell を yield する (推奨: 既知 6 構成の allowlist)。
  U-3 = `s1_known_axes_freeze` の生成・検証層に semantic membership がなく、
  両 provenance が連動 drift すれば非正準 freeze を生成できる (推奨: 次回 refreeze 前の別 T)。
  U-4 = `sort_best.comparator` に閉じた権威集合がない (推奨: 独立起票)。
  正本 = `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7
