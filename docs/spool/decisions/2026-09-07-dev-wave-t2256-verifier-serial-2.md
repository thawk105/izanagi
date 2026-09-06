---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2256-verifier-serial
seq: 2
---

## {{D:verifier-serial-merge-concat-and-run-update}}. 直列性検査の親側の辺結合は「task 順の連結 + source ごとの run を set.update で投入」に限り、dense 配列 SCC と鍵の大域 id は実測で退ける

**決定:** 親に残る直列部のうち、辺の結合だけを次の 2 つで縮める。(1) 子の結果を task 番号順に連結する (task ごとの ordinal 範囲が互いに素で単調であることに依存し、完全性は件数と task 番号集合の一致で検査、欠ければ並列結果を全部捨てて逐次へ戻る)。(2) 子は source の初出順に宛先を run へ群化して 3 本の array で返し、親は `set.update(array slice)` で投入する (set への挿入列は旧の逐次 add と同じ順)。SCC の dense 配列化と鍵の大域 id は採用しない。

**理由:**
- 68 万 txn・並列度 16 の同系列比較で、(1)+(2) は総 18.22 → 12.60 s、辺構築 11.42 → 6.17 s、判定 (`result_to_dict` の sha256) は全 trace・全並列度で旧新一致。(2) 単独の効果は P1 だけの木との交互比較で 14.37 → 12.99 s (3 走とも速い)。
- dense 配列 Tarjan は txid → dense index の登録 pass が O(E) の dict lookup を足し、SCC 3.15 → 5.65 s に悪化した。
- 鍵の大域 id は read-only の鍵にも id を振るため親が全 read を走査し、producer 構築 0.94 → 2.98 s に悪化した (子の decode を親へ移しただけ)。winner 再生の fast path は 0.53 → 0.50 s で n=3 の採用根拠にならない。
- 判定の意味論に触れない改善だけを採り、部分結果の採用・完全性検査の緩和は行わない (規律 2)。

**却下した選択肢:**
- `heapq.merge` による大域 ordinal 順の合流 (旧) — O(E log P) で、task 範囲の単調性を使えば連結で同じ列になる。
- dense 配列 Tarjan — 上記の実測で遅い。登録 pass を持たない形が出てくるまで再提案しない。
- 鍵の大域 id (親で read を走査する形) — 上記の実測で遅い。writer を持つ鍵だけに id を振り、writer の無い鍵を sentinel として子が扱う形は別 wave の候補として残す。
- 並列度 16 の既定を変える — 記憶量が根拠 (D1553)。本 wave の Pss 実測は 680k read-heavy / 16w に限れば旧比 −8% だが、P1 単独比では +4〜5%、並列度 1 と write-heavy では増えており、下方外挿の根拠にしない。
