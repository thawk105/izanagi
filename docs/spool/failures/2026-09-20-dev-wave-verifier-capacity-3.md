---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-20
wave: dev-wave-verifier-capacity
seq: 3
---

## 新規

### {{F:broken-pool-hangs-when-sigterm-ignored}}. 壊れた ProcessPoolExecutor が SIGTERM 無視環境の計算ノードで停滞し、直列性検査が hard timeout に達した [手順漏れ] [計測汚染]

- 事象: trace-enabled 10 s 走 (write-heavy 8.3M commit) の直列性検査で、edge worker 1 本が OOM kill された後、残 15 worker が state S のまま 2400 s 以上停滞し、親 process は `executor.shutdown(wait=True)` から戻らず hard timeout (前 wave 3600 s、本 wave の再現 2700 s) に達した。前 wave (D2160 項 4) はこれを「worker 側の停滞」とだけ記録し、原因を確定していなかった。
- 根本原因: `concurrent.futures` の管理 thread は壊れた pool の worker を `Process.terminate()` (SIGTERM) で殺そうとするが、Pegasus の job 配下 (`dispatch_compute.py --task generic`) では子 process が SIGTERM を無視する (別 wave [T-2778] の実測と同じ環境事実) ため殺せず、`join` で永久に待つ。worker が結果 pipe を待って眠るので CPU も進まず、親の rusage だけを見ると「親 CPU が少ない」= 原因不明に見える。上流の記憶量増大 (copy-on-write) は {{D:verifier-packed-producer-array-workers}} 項 1。
- 恒久対応: `orchestrator/verifier/parse.py` の `_kill_pool_workers` (SIGKILL) を parse / edge の pool 破綻経路で `shutdown` の前に呼び、部分結果・Future・executor の参照を解放してから全件を逐次再計算する ({{D:verifier-packed-producer-array-workers}} 項 3)。`orchestrator/tests/test_verifier.py::test_capacity_broken_pool_terminates_workers_and_falls_back` / `::test_capacity_parse_broken_pool_terminates_workers` が SIGTERM 無視 + worker `os._exit` の条件で 120 s 以内の復帰 (fix 前は timeout) を固定する。
- 再発検知: 計算ノードの profile probe (`/proc/<pid>/stat` の state と `/proc/vmstat` の `oom_kill` の時系列、job dir `run/profile/wh10/samples.jsonl`) で「oom_kill 増分 + 残 worker の S 状態 + node 使用量不変」の 3 点が揃えば同型。dispatch 下で `Popen.terminate()` に頼る終端処理は同じ穴を持つ。
