# 変異走行の注記 — [T-2265] 反実仮想 ITT

probe 走行 (`mutation-probe-spec.json` / `mutation-probe-report.json`) と本走
(`mutation-spec.json` / `mutation-main-report.json`) の 2 段で行った。事前登録は段 4 裁定 §5。

## probe 走行の結果と erratum

baseline PASSED。**10 変異すべてで赤が出た。生存した変異は 1 件もない。**
KILLED 4 / MISMATCH 6。**MISMATCH はすべて「親が予測した赤の node 集合が実際と違った」型であり、
ゲートに歯が無い型ではない。**

| 変異 | 予測と実際のずれ |
| --- | --- |
| M13 (TOST に 95% の値を使う) | 予測 2 node に対し実際は 3 node。`test_equivalence_uses_log_1p03_margin_not_literal_point03` も同じ定数から合成データの振幅を作るので連鎖して赤くなる |
| M11 (cluster 不足を受理) | 予測した `test_public_analysis_...` は赤にならず、`test_missing_arm_and_zero_commit_...` と `test_only_final_assignment_...` が赤くなった |
| M9 (最後の更新を落とさない) | 予測 1 node に対し実際は 4 node |
| M3 (明示 seed を policy 2 へ渡さない) | 予測 2 node のうち `test_step_policy_seed_accepts_...` は赤にならず、`test_genome_for_policy_cell_supplies_real_build_define` だけが赤くなった |
| M4 (policy 0/1 へも seed を漏らす) | 予測した node と別の node (`test_genome_for_policy_cell_...`) が赤くなった |
| M2 (seed の書式検査を外す) | 予測 5 param のうち `[hex]` だけ赤にならなかった (下記) |

**M2 の `[hex]` は真の等価変異である。** 入力 `0x1` は、書式の正規表現を外しても Python の
`int()` 自体が 16 進表記の文字列を受け付けないため、変異後も正しく拒否される。残る 4 param
(`negative` / `plus` / `underscore` / `non-ascii`) は正規表現が無いと通ってしまうので赤くなる。
**したがって M2 の検出そのものは成立している。**

## 途中で止まった 2 回とその原因

1. **1 回目 (probe、1 回目の投入):** 期待 node 名が pytest の収集結果に実在せず preflight で停止した。
   対象テストは 6 通りの入力で parametrize されており、収集時の node id には `[overflow]` のような
   接尾辞が付く。名前を実体へ合わせて解決した。
   **このとき親の生存確認が別 session の変異走行に一致していたため、止まっているのに
   「実行中」と誤って報告した。** `pgrep` を worktree / spec path で一意化する義務 (DW-M05) を
   守っていなかったことが原因である。
2. **2 回目 (probe、M10 の実行中):** 計算ノードへの投入が rc=16 (infra) で失敗し、
   harness が fail-closed で停止した。D612 の opt-in 上書き (queue 待ち 3600 秒 / 猶予 600 秒) を
   与えて `--resume` で再開し、M10 以降を完走させた。**M10 は再開後に KILLED になった。**

## 冗長 gate の扱い

本走の変異は解析 module と driver の中だけを触り、driver の行数を変える変異は含めていない。
そのため `test_ccbench_spawn_sites.py` の deferred gate 台帳 (行番号で sink を照合する層) は
本走の赤に現れない。実装 fix の側では、同台帳の行番号を実体へ追随させている。

## 本走

probe で観測した完全集合を `expected_nodes` へ登録し直して回した。結果は
`mutation-main-report.json` を正本とする。
