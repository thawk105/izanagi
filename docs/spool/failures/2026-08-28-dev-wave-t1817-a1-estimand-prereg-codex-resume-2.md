---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-28
wave: dev-wave-t1817-a1-estimand-prereg-codex-resume
seq: 2
---

## 再発

### F185

- **再発: 2026-08-28** — final mutationの180秒timeoutをdispatch queue / Pre-runningだけで超え、
  M03 sourceを変異したままrequest `954432.nqsv` のorphan-holdへ到達した。job実行のTIMEOUTとは
  読まず、request不在確認後に復旧して完走した。

### F453

- **再発: 2026-08-28** — repo内root holdとrequest holdを削除してresumeしたが、job-dir側
  `mutation-ledger-final.json.orphan-stop.json`を最初の復旧で見落とし、resumeがrc=125で即停止した。
  source clean / HEADとrequest不在を再照合し、3 sidecar全てを除去して再開した。
