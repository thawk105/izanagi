---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-vhash-hot-block-microbench
seq: 2
---

## {{D:vhash-hot-block-microbench-standalone}}. VHash の hot block 配置の微小計測は CCBench を改変せず、tools/ の独立 C++ と driver に置く

**決定:** VHash 論文の H1 (少数版の記述子の局所化) を確かめる 1 キー版選択の微小計測は、`tools/vhash_microbench/` の依存なし C++20 単一 TU (`hot_block_bench.cc`) と Python 3.9 互換の driver (`run_hot_block.py`) に置き、作図は `tools/plotting/plot_vhash_hot_block.py` に置く。CCBench の gitlink と中身、`patches/` には触れない。build は CCBench に揃え (計算ノードの g++-12、`-O3 -DNDEBUG -std=c++20 -Wall -Wextra -Werror`、ISA は `-march=native` でなく明示 flag = CCBench の microbench の慣行)、計算ノードへは `tools/pegasus/dispatch_compute.py --task generic` で 1 shard = 1 job として投げる。生出力は schema `izanagi-vhash-hot-block-microbench/v2` の JSON で、作図器はこの契約だけを受理する。一次資料は `output/insights/2026-09-29/vhash-hot-block-microbench/README.md`。

**理由:**
- D16 / D18 / D20 は **CCBench の改変** の行き先を分類する決定であり、CCBench のコードを 1 行も使わない独立の微小計測はその分類の対象外である。
- CCBench の `microbench/` (既定 OFF) へ patch で足す案は、gflags / glog / FetchContent を含む configure と CCBench の上流 CI 規約 (clang-format) を負うのに、得るのは同じ compiler・同じ flag だけである。
- `orchestrator/campaign/` に driver を置くと、本番の起動箇所・build 箇所の台帳テスト (`orchestrator/tests/test_ccbench_spawn_sites.py` の走査対象) に掛かる。`tools/vhash_microbench/` はその走査の外である。

**却下した選択肢:**
- CCBench の `microbench/` へ inert patch で足す — 上記のとおり負担だけが増える。
- `orchestrator/campaign/` に置く — 本番 campaign の台帳に研究用の微小計測が混ざる。
- 受入所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) へ新 test を登録する — 被覆率 gate (0.90) は未登録でも割らず、land の競合循環を避けるため登録しない。
