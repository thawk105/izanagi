---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-t2884-gate-verifier
seq: 3
---

## 再発

### F109

- **再発: 2026-09-30** — 判定器の D5 (emitter の証拠面) の include 検査が `#include "ycsb.hh"` しか受けない正規表現で、test の fixture も実物と違うその簡略形を書いていたため、段 5・6 の test (200 件緑) と review 2 本・焦点再レビューが通した。実物の `cc/silo/ycsb_silo.cc` は `#include "../../include/ycsb.hh"` で、計算ノードの生死確認 (Silo 修正あり) で D1・D2 が 0 件なのに D5 が不成立になり certified にならなかった (向きは偽の赤)。include の path を `cc/silo/` から解決して `include/ycsb.hh` と同じ file のときだけ成立にし、fixture を実物の形にして別 file へ解決する負例を足した (`orchestrator/verifier/core.py` の `_gate_d5`、`orchestrator/tests/test_verifier_gate_witness.py::test_gate_wrong_include_target_d5_fails`)。再発検知は同 test と変異 M12、および実物の source で走る生死確認 (`output/insights/2026-09-30/gen-opt-gate-verifier/README.md` §4.3)。
