# t139-probe — [T-139] 劣化梯子の生死 probe (task-scoped、非 calibration)

**この namespace は task-scoped な使い捨て probe の置き場であり、`output/env/<env-tag>/` の
calibration / profile (環境の物差し) ではない。** ここの throughput は DW-G01 の生死確認
(方向の go/no-go シグナル) 専用の**未較正・受理不能 (non-acceptance) 値**である —
性能比較・headline・calibration・floor のいずれの入力にもしない。

- `t139_probe_gap.sh` — PBS ジョブ (投入したのと同一 bytes)
- `t139-probe-degradation.patch` — probe patch (候補 A/B、裸マクロ)
- `0_873583.nqsv/` — job 873583 の全成果物 (summary.tsv、run ログ、witness、PBS 会計、
  manifest.json = post-hoc provenance)

設計・裁定の正本 = `output/insights/2026-07-29_t139-silo-degradation-ladder-design.md`。
