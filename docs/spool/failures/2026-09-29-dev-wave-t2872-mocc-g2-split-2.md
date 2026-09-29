---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-t2872-mocc-g2-split
seq: 2
---

## 再発

### F139

- **再発: 2026-09-29** — [T-2872] の MOCC 診断 runner (job dir、Codex author) が計算ノードの smoke で 3 回止まった: (1) MOCC の `transaction.cc` も WORKLOADS 4 実行体へ compile されるので `compile_commands.json` の行が 4 本あり、1 本前提の行選択で停止、(2) macro off の前処理一致を `-E` の出力 (`#if` で飛ばした行を空行で埋める) で比べて必ず不一致、(3) probe の追加コードの符号付き/なし比較が CCBench の `-Wall -Wextra -Werror` で停止。(1) は同日 [T-2875] の再発と同じ形。親の login 簡易試験 (include を除いた `g++-11 -E -P`) は (2) を見逃した。段 5 の author prompt に「全 case の外部との交点を既存 driver と CCBench に照合した表を作らせる」を入れていなかった。smoke は 1 回 28〜34 秒で実害は時間だけ (4 回目で完走)。恒久対応は F139 のまま。記録 = `output/insights/2026-09-29/t2872-mocc-g2-split/README.md` §8。
