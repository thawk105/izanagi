---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t1934-acceptance-residual
seq: 2
---

## 再発

### F333

- **再発: 2026-08-28** — T-1934の段7でcommitとfull-history provenanceを同じ短い前景commandへ繋ぎ、dispatch親だけを打ち切ってrequest `953513.nqsv`とorphan holdを残した。qdelせず終端を待ち、child未起動のqueue-wait-timeoutとsource clean/HEAD不変を確認した。holdは回復処理が解除し、監査は単独commandで再走して新規違反なしを得た。既存恒久対応に修正すべき新事実はない。
