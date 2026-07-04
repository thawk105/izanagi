# YCSB 7 プロトコル stock baseline (2026-06-19 凍結)

**worklog 2026-06-19 エントリから昇格した凍結記録** (2026-07-05。可変状態ではなく実測履歴なので追記しない)。
Phase 1 完了時点の確定 calibration (env=linux-baremetal) で取得した stock baseline。**CV<1.5%**。

| protocol | throughput (tps) |
|---|---|
| tictoc | 1.05M |
| silo | 902K |
| mocc | 661K |
| cicada | 605K |
| si | 351K |
| ermia | 327K |
| oze | 81 (病理、下記) |

- **oze の病理:** 81 tps / CV 53%。skew0.9 では thread=1 でも 244 tps、thread48 で abort 99% の livelock。
  uniform は 122K tps で正常。機構 = read ごとの依存グラフ DFS (`is_invisible_dfs`) が密競合グラフで爆発。
  詳細は `output/insights/2026-06-19_oze-skew-pathology.md` (この 1 件のみ当時 insight 化済み)。
- **用途と限界:** Phase 3 主実験 headline 2 (クロスプロトコル stock 最良) の**初期比較の参考値**。
  採否判定には使わない — headline 2 の実行時は protocol 別 calibration + between-run floor の対象別再実測が
  前提 (phase3.md 後続段 6 の前提タスク (b)。floor の流用禁止は同 統計計画の節)。
