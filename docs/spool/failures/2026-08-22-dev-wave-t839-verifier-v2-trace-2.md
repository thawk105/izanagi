---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t839-verifier-v2-trace
seq: 2
---

## 再発

### F23

- **再発: 2026-08-22** — `docs/dev-wave/operations.md` DW-O01 の起動定型
  (`nohup setsid bash -c '<cmd>; echo $? > <log>.done'`) が F23 の恒久対応
  (`< /dev/null` を明示) を反映しないまま残っており、codex consult 子が
  「Reading additional input from stdin...」で無言停止 (.done 未生成) する事故を実測した。
  DW-O01 の定型へ `< /dev/null` を明記して閉じる。
