# silo_ladder_rung1 — rung 1 ability-probe characterization (task-scoped)

**この namespace は劣化梯子 rung 1 (D18 第 4 類 subtype `evaluation_role=ability_probe`) の
characterization 専用であり、環境の物差し (calibration / floor) ではない。** ここの throughput は
ability-probe の受理証拠 — 性能比較 headline・calibration・floor・RF のいずれの入力にもしない。

- `silo_ladder_rung1.json` — committed 実証 JSON (all_pass。pytest
  `orchestrator/tests/test_silo_ladder_rung1_evidence.py` が現物へ再束縛)
- `job-staging/0_873917.nqsv/raw-bundle-attempt-1/` — raw evidence bundle (sha256 相互参照鎖。
  bundle のみ tracked、job-staging のその他は gitignore の作業領域)
- 駆動・設計・実測の正本 = `orchestrator/campaign/silo_ladder_rung1.py` と
  `output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md`
