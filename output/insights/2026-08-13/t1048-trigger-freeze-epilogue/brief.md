# [T-1048] 段 1 brief — trigger-gating 凍結領域を post-END の `if (izanagi_gate_pass)` まで拡大

2026-08-13 17:2x JST / branch `worktree-dev-wave-t1048-trigger-freeze-epilogue` (base = main 48b2caab)。

## 確定済みユーザー裁定

第 10 回 #5 = **(b)**。凍結領域を post-END の `if (izanagi_gate_pass)` まで広げて R2 (block 外での
`izanagi_gate_pass` 再代入) を閉じる。**C++ 字句解析器は再建しない。R1 (コメント化・raw string の囮) は
閉じず残存限界として明記。** 正本 = `output/insights/2026-08-13_t897-trigger-admission/README.md` RP-2。
控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-rulings10-15rulings.md` #5。

## scope

`build_admission._require_materialized_trigger_axis_predicate` の受理言語へ、END 行末の**直後に隣接する**
post-END epilogue の逐語一致を足す。受理集合は狭くなるだけで、広がる変更は一切入れない (規律 2)。

## 実アンカー

| 面 | アンカー |
|---|---|
| 軸定数 | `orchestrator/campaign/axis_trigger_gating.py:27-50` (`FROZEN_TEMPLATE_HOLE_BYTES` / `FROZEN_TEMPLATE_BLOCK_BYTES`) |
| gate 実装 | `orchestrator/campaign/build_admission.py:169-199` (`_require_materialized_trigger_axis_predicate`)、`:68` (`_TRIGGER_SKELETON_TOKENS`) |
| 骨格の現物 | `patches/silo-backoff-trigger-gating-variant.patch:106-111` (END 行 + epilogue 5 行) |
| patch 整合テスト | `orchestrator/tests/test_build_admission.py:554-562` (`test_frozen_trigger_block_matches_template_patch_bytes`) |
| 波及 fixture | `test_build_admission.py` / `test_campaign.py:5371` / `test_s8a_trigger_sweep.py` / `test_s1_direct_comparison.py` / `test_p3_s4_loop_trigger_gating.py` / `test_p3_exploration_namespace.py` / `test_p3_autonomous_workload_trial.py` |

epilogue の逐語 bytes (patch から実測、末尾空白なし・LF):
`#if BACKOFF_TRIGGER_GATING\n  if (izanagi_gate_pass) {\n    Backoff::backoff(FLAGS_clocks_per_us);\n  }\n#endif\n`

## 既存被覆と純増検出力 (機構名でなく性質で検索した)

「EVOLVE-BLOCK hole の外の bytes 改変を拒む」性質を持つ既存機構は `diff_quarantine` 1 本
(`OUTSIDE_REGION`)。掛かるのは**実装文字列を挿入する候補 materialization 経路だけ**で、呼び手は
`p3_s4_loop*` / `pipeline` / `s8a_trigger_coverage` / `auditor_gate` / `materializer_admission`。
build gateway 側 (`derive_build_admission` / `require_build_admission`) は現在 BEGIN..END の block bytes
しか見ず、**END の直後 1 byte も見ていない**。
→ **純増検出力 = quarantine を経由しない build 経路 (S8b oracle / S8b floor / S-1 extime calibration、
および候補挿入を伴わない pristine / characterization build) で、END 直後の epilogue の改変・削除・
挿入・gap 挿入を admission が拒否できるようになること。**

## 不変条件

- `patches/silo-backoff-trigger-gating-variant.patch` を 1 byte も変えない (canary provenance
  `output/insights/2026-07-13_s6-canary-rename-provenance.json` と上記整合テストが依存)。
- `FROZEN_TEMPLATE_BLOCK_BYTES` / `FROZEN_TEMPLATE_HOLE_BYTES` と受理 hole 32 通りは不変。
- C++ 字句解析器・BOM/NUL/decode 検査を再建しない (T-897 段 6 が両方向の誤りを実証済み)。
- `FROZEN_MANIFEST` (23 件) に本 wave の対象 path は無い — 実測済み、pin 閉包の再発行は不要。
- 過剰拒否を作らない: `instr-...-tally.patch` / `broken-silo-trigger-misattr.patch` は
  `izanagi_gate_pass` にも END 行にも触らない (実測済み)。`s6_canary_rename` の匿名化 source は
  marker も token も rename されるため gate に到達しない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) 凍結は epilogue 側だけでよい。** hole は mask 0..31 のすべてが `izanagi_gate_pass = <述語>;` の
  無条件代入 (`orchestrator/tests/reflux_ir_expected_goldens.py:25-56` で実測)。よって BEGIN より手前の
  再代入は hole が必ず上書きし、R2 が効くのは [END, gated if] の区間だけ。prologue
  (`bool izanagi_gate_pass = true;` 宣言) の凍結は不要。
- **(P2) 隣接性は exact adjacency で要求する。** END 行末の直後から epilogue bytes が始まること。
  gap を許すと挿入が通るので「どこかに epilogue がある」では足りない。
- **(P3) 適用条件は現行の三分岐を維持。** marker 不在 + skeleton token 存在 = reject、
  marker 不在 + token 不在 = pass (stock)、marker 存在 = block 検査 + epilogue 検査。
- **(P4) epilogue の後続空行は凍結領域に含めない。** `#endif\n` までで R2 は閉じる。
- **(P5) R1 は閉じない。** `#define izanagi_gate_pass` 等の前処理器による迂回も R1 と同族の残存限界として
  insight と実装 docstring に明記する。

## 成果物影響 (DW-G05)

実装しなければ、block 外で `izanagi_gate_pass` を再代入した materialized source が admission を通り、
report は mask M を主張しつつ実バイナリは全要因 backoff (= stock 相当) で走る。S8b oracle / floor の
測定値、S-1 direct comparison の帰属、certified 選択の proof chain がそのまま偽になる。

## 分割方針

軽量版は採らない (受理集合が変わる = DW-C00 の敵対検証子を省かない条件)。段 2 plan 1 本、段 3 敵対相談 2 本
(レンズ = 過剰拒否 / 迂回経路)、段 5 実装子 1 本、段 6 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。
受入は計算ノード (worklog (541) の実績 = 10748 passed / 147 秒)。
