---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2708-fixture-config-h-gap
seq: 3
---

## 再発

### F351

- **再発: 2026-09-17** — 発火面が変わった。受入の正規 consumer ではなく、**計算ノードで走らせる使い捨て probe** (Codex author が書き、repo 外へ退避) が held module `test_s8b_oracle_driver.py` の fixture builder を pytest 外から `import` し、`GrowthTestHoldBypassRefused` (`node_id: test_s8b_oracle_driver.py::*`) で 6 秒 rc=1 になり generic dispatch 1 本を空費した。段 2 plan (「静的には pytest 外から直接呼べる」) と段 3 の 2 レンズ (import 副作用を temp 検査・xdist・conftest まで検算した) の 3 者がいずれも末尾の `enforce_held_functions(..., plain_runner="none")` を見落とし、親も memory の「pytest session を要する probe」を held module と結びつけずに読んだ。解除 env はユーザー明示専用なので使わず、probe の内側で `pytest.main([held module, "--collect-only", "-q", "-p", "no:cacheprovider", "-k", <不一致名>])` を呼び `pytest_sessionstart` hook で完全修飾名を import して `sys.modules` に残す形へ fix 子が直した (`-k` で items を空にし `pytest_collection_finish` の receipt memo prewarm を避ける。hold session 2.2 秒、rc=5)。held module の helper を外から使う probe / harness は、設計段で module 末尾の guard binding の有無を必ず見る。一次資料は `output/insights/2026-09-17/t2708-fixture-config-h-gap/README.md` §7 と同 dir `run1-result.json`。
