# [T-1488] rr80/rr20 calibration 登録 wave — 変異 matrix と合成監査の逐語

authority: none
default_effect: no-state-change

wave: dev-wave-t1488-rr80-rr20-calibration / 2026-08-23 / anchor `4e74a8b5`

段 4 が事前登録した「fix 後、変異 matrix で所見1・2 の kill 確認を行う」を実施した記録である。
この wave は実装差分が非ゼロ (1424 insertions) のため、`DW-S04` の変異 matrix 免除
(「実装しない」裁定かつ実装差分ゼロ) に当たらない。

## 変異 matrix

anchor commit `4e74a8b56cec9ab8037401d1636be2bdb127d8ac` の使い捨て worktree
(`tools/mutation_worktree.py --runner-mode dispatch --detached`)。
runner は `tools/run_tests.py --force-dispatch orchestrator/tests/test_holdout_observation.py
-rf -p no:cacheprovider`。

| ID | 区分 | 変異 | 結果 | 期待赤 node (完全集合) |
|---|---|---|---|---|
| M1 | negative | `transition_to_noise` の未消費 sweep guard を `if False:` で無効化 | KILLED | `test_calibration_capability_rejects_noise_transition_with_unconsumed_sweep` |
| M2 | positive | 同 guard から `len(state.sweep_records) < 3` の early-stop 救済を外し、fix2 の過剰拒否へ戻す | KILLED | `test_calibration_capability_allows_noise_transition_after_three_sweep_points` |
| M3 | negative | `runner.run_once` が gateway の返す正規化済み `numactl` / `extra_env` を捨て、呼び手の生値で spawn する | KILLED | `test_calibration_gateway_reuses_normalized_runtime_values_for_spawn` |

**3/3 KILLED、MISMATCH 0、SURVIVED 0。baseline は rc=0 / 27.097 秒。**

M1 と M3 は段 6 敵対レビュー (reviewB) の所見2・所見1 が指摘した bypass そのものであり、
fix がその受理集合の穴を実際に塞いだことを示す。M2 は逆向きの正例で、fix3 が入れた
early-stop 救済を外すと**正当な計測経路が止まる**ことを示す — `DW-M01` の
「受理集合を縮小する wave では、承認外の過剰拒否を検出する正例も登録する」に当たる。
M1 と M2 は同じ 3 行を別方向へ変異させる対であり、guard が両側から拘束されていることを示す。

## probe を先に回した理由と結果

`DW-M07` は「KILLED 期待で期待 node が空の spec は起動前に中止する」ため、
まず全件 SURVIVED 期待の probe を回して観測 node を集めた
(`verbatim/mutation-spec-probe.json`、`verbatim/mutation-ledger-probe.json`)。

probe の結果は 3 件とも MISMATCH (SURVIVED 期待に対して実際は kill された) で、
観測 node は 3 変異とも**ちょうど 1 node** だった。この実測を完全集合として本走の spec を
再登録した (`DW-M08` の「期待 node は完全集合」)。
T-1222 の先例と違い、親が事前に挙げた node 集合と probe の実測が一致したため、
再登録による集合の拡大は起きていない。

## 合成監査 (段 9 の local main 取り込み)

`verbatim/s9-merge-composition-audit.md` は、local main `c301c4fd` を取り込む merge に対する
read-only の Codex 合成監査 (gpt-5.6-sol / xhigh) の逐語である。自動 merge は競合ゼロだったが、
競合の不在は合成の正しさを意味しないため規律6 に従って独立監査にかけた。判定は安全、
危険と判定した点はゼロ。両親が触った実装面 path は
`orchestrator/tests/test_ccbench_spawn_sites.py` の 1 件だけで、合成結果は両親のどちらとも
異なる (単純な和集合) ため、provenance checker が Codex `role=author` を要求する形になっていた。

監査が未検証として残した 3 点 (pytest 実走、Pegasus 実機実行、issuer visitor 自身が明記する
動的経路) のうち前 2 者は親が実測した。動的経路の非検査は段 2c/段 4 の確定方針どおり scope 外である。

## 手元 artifact の所在

段 1〜6 の brief・プラン・敵対所見・裁定・fix 報告・実機投入証跡は repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1488-rr80-rr20-calibration/` に保全されている。
