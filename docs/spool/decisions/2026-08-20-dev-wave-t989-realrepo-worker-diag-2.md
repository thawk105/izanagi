---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t989-realrepo-worker-diag
seq: 2
---

## {{D:t989-worker-span-diagnostic-closed}}. real-repo group 受入 wall 帰属調査を打ち切る

**決定:** worker_id/nodeid/start/finish の一時診断は実装・敵対レビュー・変異matrix
(4/4 KILLED) まで完走させ技術的健全性を確認した上で revert し、real-repo group の
受入 wall への帰属をこれ以上定量化する投資は行わない。D258・D358 の「排他機構の
変更では受入は速くならない」という結論を維持する。

**理由:**
- 診断を実際に全テストスイートへ適用しようとしたところ、`tools/pegasus/dispatch_compute.py`
  の `"tests"` task 用 `env_allowlist` が閉じた集合 (D103 決定5「任意 command 化は
  しない」に基づく意図的設計) であり、新規診断用 env var が計算ノードへ dispatch
  される qsub job の環境に伝播しないと判明した。この allowlist は 20 以上の並行
  稼働セッションが共有する dispatch のセキュリティ境界であり、一時診断のためだけに
  拡張するのは対象の重さと不釣り合いである。
- 診断が測定する worker span (occupied interval の union) は、対象を除外した場合の
  wall 短縮量を意味する**因果的指標ではない**。real-repo group が wall の大半を
  占有していても、他 worker の作業が同じ時間を埋めていれば除外効果はゼロになり
  得る。測定に成功していたとしても、この指標だけからは D358 を覆す根拠を得られない。
- D258 (2026-08-10)・D358 (2026-08-13)・2026-08-19 wave (n=1 測定の統計的限界)・
  本 wave (測定基盤の壁と worker span の非因果性) の4波にわたる独立した調査が、
  いずれも同じ結論へ収束した。

**再訪条件 (両方成立して初めて着手を検討する):**
- `tools/pegasus/dispatch_compute.py` の env allowlist 拡張が、本件と独立の別用途
  によって既に正当化されていること。
- worker span 相当の観測から因果的な wall 短縮効果を推定する方法論 (実際に対象を
  除外した A/B 比較、複数 run のペア比較等) が用意されていること。単発の occupied
  span 観測では原理的に不十分。

**却下した選択肢:**
- `tools/pegasus/dispatch_compute.py` の env allowlist へ診断用 env var を追加して
  measurement を強行する — 共有セキュリティ境界の拡張が一時診断単独の価値に対して
  不釣り合いに重い。
- 診断コードをそのまま残し「いつか測定する」余地を保つ — 規律5 (段階導入・盛らない)
  に反し、使われない可能性が高いコードを test infra に恒久化することになる。
