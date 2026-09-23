# 既知結果の検索 (親、2026-09-23 JST、worktree HEAD = local main cadaf3805)

cwd = /work/1/SFC/tanab/izanagi/.claude/worktrees/t2851-tpcc-heldout-prereg。git 管理下の file だけを見る。

## 1. TPC-C の実行時引数の名前

command: `git grep -l -E "tpcc_(num_wh|perc_payment|perc_order_status|perc_delivery|perc_stock_level|interactive_ms)" -- output docs orchestrator tools`

出力 (8 file):
```
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/README.md
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/B0-tpcc-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/D1-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/M1-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/M2-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/M3-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/M4-run.json
output/insights/2026-09-22/t2854-tpcc-ccbench-v3/evidence/compute-2/mutation-results.json
```

## 2. 上の記録で使われた倉庫数・thread 数・extime

command: `git grep -h -o -E "tpcc_num_wh[^,\" ]*|thread_num[= ][0-9]+|extime[= ][0-9]+" -- output/insights/2026-09-22/t2854-tpcc-ccbench-v3 | sort | uniq -c`

出力:
```
      1 extime 1
     14 extime=1
     14 thread_num=2
     12 tpcc_num_wh=1
```

## 3. binary 名の出現

command: `git grep -l -E "tpcc_(silo|mocc)" -- output | wc -l` → 116。
dir 別 (`... | cut -d/ -f1-3 | sort | uniq -c | sort -rn`): output/s6-rounds/frozen 62、output/insights/2026-09-22 21、output/insights/2026-09-16 9、
output/s6-rounds/runs 6、output/env/pegasus 4、output/s6-rounds/scores 3、output/s6-rounds/anon 2、他 1 件ずつ 9 file。
文脈の標本 (`git grep -h -o -E ".{60}tpcc_(silo|mocc).{60}" -- output/s6-rounds/frozen output/env/pegasus | sort | uniq -c | sort -rn | head -5`):
全て `CMakeFiles/tpcc_silo.exe.dir/...` 等の compile 行 (build log)。
`output/s6-rounds` 以外の 42 file (`git grep -c -E "tpcc_(silo|mocc)" -- output ':!output/s6-rounds'`) の内訳: env/pegasus の compile_commands.json 4、
t2630 の obs-*.json 9 と t1994・t2625 の qualification JSON 2 と t2708 の projected JSON 1 (標本は compile 行)、2026-06-19・07-10・07-13・07-28・08-11 の
5 file (source path の参照・レビュー文、`git grep -n` で全行を読んだ)、v1 の known-scan 1、[T-2854] の 2 insight 20 (構造検査・前処理・設計の記録)。
t2630・qualification・t2708 の JSON は標本だけを見ており、全行は読んでいない。`output/s6-rounds` 配下の 74 file (frozen 62・runs 6・scores 3・anon 2・
audit-sheet 1) は frozen の標本 (compile 行) だけを見た。合計 74 + 42 = 116。

## 4. throughput の記述

command: `git grep -n -i -E "tpcc.{0,80}(tps|throughput)" -- output docs | wc -l` → 0 (同じ行に限る検索で、別の行・別 file の数値は拾わない)。
command: `git grep -l -F "throughput[tps]" -- output/insights/2026-09-22/t2854-tpcc-ccbench-v3` → 8 file (B0-tpcc-run.json、B0-ycsb-run.json、D1-run.json、
M1〜M4-run.json、mutation-results.json)。B0-tpcc-run.json の stdout 抜粋に `commit_counts_: 36156`、`abort_rate: 0.0819`、`maxrss: 507200 kB`、
`throughput[tps]: 36156`、`actual_extime: 1` がある (TRACE=1 の構造検査、BACK_OFF 1)。

## 射程

未追跡の file、別の worktree、job dir (`/work/1/SFC/tanab/dev-wave-jobs/` 配下)、campaign の作業領域、repo 外は見ていない。
