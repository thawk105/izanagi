---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t2589-consumer-real-artifact-repair
seq: 3
---

## supersede 追記

- F909 **supersede: 2026-09-14** — 恒久対応が指す負例 `test_shared_noncanonical_toolchain_digest_is_rejected` は撤去した。守っていた「腕内で canonical digest を再計算して記録値と照合する層」自体が producer の証拠を取り違えた等式で、回収成果物では恒偽だったためである ({{D:t1998-consumer-artifact-truth}})。**本項の一般の教訓 (片側だけを変える負例は対称な層に mask される) は有効なままである。** 腕間 digest 一致の負例 `test_toolchain_record_digest_drift_is_rejected` は残し、変異 M3 で KILLED を実測した。経緯は `output/insights/2026-09-14_t2589-consumer-real-artifact-repair/README.md`。
