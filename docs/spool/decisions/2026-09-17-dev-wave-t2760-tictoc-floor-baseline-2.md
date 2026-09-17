---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2760-tictoc-floor-baseline
seq: 2
---

## {{D:tictoc-floor-baseline-cmake-default}}. between-run floor の tictoc stock baseline は現行 pin の CMake cache 既定とし、認定較正と同じ genome に揃え、既定との一致を source へ束縛する

**決定:** `orchestrator/campaign/between_run_floor.py` の `BASELINES["tictoc"]` は
`tictoc|BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,PREEMPTIVE_ABORTS=1,TIMESTAMP_HISTORY=1`
とする。これは現行 CCBench pin `511c9538` の `external/ccbench/cmake/Options.cmake` の cache 既定であり、
mocc 登録 (2026-09-01) と同じく「CMake 既定 = stock」の形をとる。`TICTOC_SPACE` の点 (no-wait は (1,0)、D1418) で、
D2083 が文書登録した accepted な tictoc 認定較正 record 2 件 (rr50 / rr95) の `genome` と同一である。
根拠のうち「CMake 既定との一致」は test が `Options.cmake` の `set(CCBENCH_<AXIS> <v> CACHE …)` を読んで
束縛し、pin が進んで既定が変われば赤になる。silo の baseline (BACK_OFF=0、p2_2 の歴史的比較構成) は据え置き、
既定との一致 test の対象にしない。

この登録は D2114 項 4 の準備であり、測定の開通ではない。D1373 の関門 (`_protocol_source_has_trace_hook_evidence_only`)
は 1 byte も変えず、現行 pin では `--protocol tictoc` は引数解析を通った後に build 前で拒否される (受理集合不変)。
between-run floor の実測には hook 移植と pin 再承認 (D2083 項 5、D1603) が別途要る。

**理由:**
- 層 3 report は floor の `genome` から protocol だけを取り、(protocol, records, threads, workload) で within-run と
  between-run を照合する (`orchestrator/campaign/layer3_report.py` の `_floor_protocol_and_basis` / `_calibration_floors`)。
  つまり 2 種の floor が別の stock で測られていても機械的には対になり、整合は登録側で保つしかない。tictoc の
  認定較正 (within-run) は既に CMake 既定 genome で accepted であり、between-run 側を同じ genome にするのが
  最小の整合である。
- D1373 が関門を許可リストでなく source の事実へ束縛したのと同じ理由で、baseline の根拠も comment の主張に
  留めず現行 checkout の `Options.cmake` へ束縛する。pin 前進時に「既定が変わったのに登録が古い」状態を
  赤で検出でき、規律 7 の「同一性だけを理由に無効化」ではなく値の意味を検査する。
- 「根拠つき」の形は既存登録と揃える: code 内は短い出典 comment、詳細は wave の insight。mocc の根拠も
  T-2115 の段 2 plan にしか無く、code 側の形はこれで同形になる。

**却下した選択肢:**
- silo と同じく `BACK_OFF=0` で high-abort を狙う — silo の値は p2_2 の比較構成に由来する歴史的選択で、
  tictoc の認定較正は既定 (BACK_OFF=1) で取得済み。別 genome にすると floor 対が割れる。
- 認定較正 record の `genome` 文字列を test の期待値にする — `output/` の data file へ test を結合し、
  record の改版・再配置で赤になる。source (Options.cmake) への束縛で足りる。
- `BASELINES` を genome 空間の既定値から導出する一般化 — 本題外。認定 launcher も軸表を独立に持つ (D1863)。
- cicada も同時に登録する — 認定較正が無く、D2114 項 4 の起票外。
