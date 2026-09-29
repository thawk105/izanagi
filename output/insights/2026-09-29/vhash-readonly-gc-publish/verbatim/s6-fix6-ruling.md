# 段 6 fix6 裁定 — md_22 [T-2911] (2026-09-30 01:4x JST)

焦点走 4 (commit 981f2f63d、44 file、36732.nqsv、01:36〜01:41 JST): **1 failed, 5160 passed, 8 skipped**。
赤: `orchestrator/tests/test_ccbench_spawn_sites.py::test_ro_gc_publish_build_sink_uses_complete_condition_gate_family` (3608 行)、`KeyError: _BuildSink(relative_path='orchestrator/campaign/vhash_ro_gc_publish.py', scope='<module>._build_variant', lineno=197, kind='direct-cmake-target')`。
帰属: 本 wave。fix3 で足した test が新 driver の build sink を行番号 197 で名指ししていたが、fix5 で `verify_acceptance` に行が増え、同じ sink の行番号が変わった (981f2f63d で `"--build"` を持つ `cmake --build` 呼び出しは 216 行、関数定義は 195 行)。この test file は先例の sink も行番号の literal で固定する書き方 (s1 1281・s8b 1781)。

- **FB-12:** 同 test の sink の行番号を 981f2f63d の実物に合わせる (sink の行番号が何を指すかは同じ file の `_production_build_sources` / `_benchmark_build_sinks` の定義で確かめる)。期待する分類 (covered 4・proven-unreachable 68) は変えない。他の test の期待値は変えない。
