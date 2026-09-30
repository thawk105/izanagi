# 段 6 fix4 裁定 — md_22 [T-2911] (2026-09-30 00:5x JST)

smoke2 (commit 3fa41955a、36592.nqsv、bnode001、job Elapse 148 s、raw `raw/smoke2.json`): rc=1。
- 依存物 build 3 本 (primary 22.0 s・trace 11.5 s・vlife 11.5 s) の後、gate を通って build 4 本 (default-stock 14.4 s、default-variant 17.7 s、smoke-trace 18.0 s、smoke-vlife 25.9 s) が成功 (fix3 で smoke1 の停止は解消)。
- 実規模の対 (S95-wait10msR-gc10、48 worker、1M 件、3 s): stock wall 3.8 s・variant 3.7 s、実現 ro 試行率 0.95001 / 0.95001、長い ro 試行 300 / 300、variant の COUNT は ro commit 25,719,558・flag 立て 12,709。
- trace 木の短走 (4 worker、200 件、1 s): ro commit 626,864・flag 立て 370・長い ro 100。
- **停止:** vlife 木の短走が `ERROR: unknown command line flag 'izanagi_long_kind'` で rc=1。
帰属: 本 wave の driver。`_flags` は vlife build に `izanagi_ronly_pct=-1` と `izanagi_long_kind=0` を渡すが、vlife patch の `izanagi_long_kind` は `IZANAGI_CICADA_LONGTX` の内側でだけ定義される (instr-cicada-version-lifetime.patch 196-211 行)。本 wave の build は LONGTX を立てない (長い ro は workload patch で作る、段 4 裁定)。`izanagi_ronly_pct` は VLIFE の内側なので渡せる。

- **FB-10:** vlife build への flag から `izanagi_long_kind` を外す (`izanagi_ronly_pct=-1` と `worker1_insert_delay_rphase_us=0` は残す)。measure と smoke の両方の経路。vlife の long 系の書換えが無効であることは、LONGTX を立てないこと自体で保たれる (macro 既定 0)。build の macro に LONGTX が無いことと flags に `izanagi_long_kind` が無いことが対応していることを test で検査する。
- 既存テストの期待値は変えない。
