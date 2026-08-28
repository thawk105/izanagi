---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: worktree-dev-wave-t2068-a2-partial-raw
seq: 3
---

## 再発

### F166

- **再発: 2026-08-28** — `--runner-mode dispatch`へ`--force-dispatch`を付けず、baseline test rc=0をreceipt表示0件のPARSE_ERRORとして停止した。DW-M07の既存recipeを読み直して別out/spec履歴のattemptで再走し、最終8/8 KILLEDを得た。
