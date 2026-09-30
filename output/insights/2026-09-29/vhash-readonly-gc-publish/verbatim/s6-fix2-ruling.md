# 段 6 fix2 裁定 — md_22 [T-2911] (2026-09-30 00:2x JST)

焦点走 2 (commit 1fad6942b、44 file、36421.nqsv、00:12〜00:15 JST): **1 failed, 5144 passed, 8 skipped**。焦点走 1 の赤 10 件はすべて緑。
残る赤 1 件: `orchestrator/tests/test_ccbench_spawn_sites.py::test_define_sink_cross_product_t2520_certify_entry_removal` (3633 行)。
`before[target] == Counter({"deferred": 14, "proven-unreachable": 55})` に対し実測 `proven-unreachable: 58`。
帰属: 本 wave が patch 由来の define を 3 件 (IZANAGI_CICADA_RO_GCFLAG・_COUNT・IZANAGI_CICADA_ROGC_WORKLOAD) 足したため、t2187 probe の sink から到達不能な macro が 55 → 58 に増えた。fix1 で更新した 69→72 (supply)・45→48 (CXX flags) と同じ性質の件数 pin の取り残し。先例 (deferred 14) は変わらない。

- **FB-8:** 同 test の `proven-unreachable` の期待を 58 に直す (deferred 14 は変えない)。同じ test file と `test_condition_meaning_gate.py` の中に、patch 由来 define の総数から派生する件数 pin で本 wave の 3 件追加を反映していないものが他に無いかを静的に洗い、あれば同じ規則で直して全件報告する。先例 macro に固有の件数は変えない。
- 単位 A への fix は無し。
