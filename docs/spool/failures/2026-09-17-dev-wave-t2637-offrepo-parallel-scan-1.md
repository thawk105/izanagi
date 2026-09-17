---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-t2637-offrepo-parallel-scan
seq: 1
---

## 再発

### F3

- **再発: 2026-09-17** — 到達不能監査の並列化 wave で、親が自分の計測系列を自分で重ねた。D958 の形の
  独立走 (new16-7、fixture × 実根、16 worker) と、失敗の帰属用の onerror probe (同じ探索根を 16 worker で走査)
  の待ち手の鍵を「直前の走の `.done`」(`fixture-old-4.done`) にしたため、probe が new16-7 の走行中 (09:28:46〜09:34:14)
  に 09:29:05 から同時に走り、両方の所要 (327.0 秒 / 319 秒) を汚した。他 session の外乱ではなく親自身の producer が
  原因で、単独性の確認 (`ps` で同じ探索根を叩く自 process 0 件) を投入前に行わなかった。new16-7 は値と理由を残して
  無効にし、単独の代替走 (new16-8) を取った。恒久対応: 同じ資源 (探索根・repo・node) を叩く計測を chain するときの
  鍵は**系列の終端 file** (`series-<name>.done`) にし、直前の走の `.done` にしない。投入直前に
  `ps -eo pid,args | grep "[a]udit_dangling_commits.*--offrepo-root"` で自 process を数える (memory
  `measurement-chains-key-on-series-end`)。正本 = `output/insights/2026-09-17/t2637-offrepo-parallel-scan/README.md`
  の実測表。
