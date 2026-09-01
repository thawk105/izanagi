---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2122-prereg-executable-evidence
seq: 2
---

## 再発

### F24

- **再発: 2026-09-02** — 段 6 レビュー B の待ち手 (`tools/dev_wave_wait.py producer`) が
  producer 生存中に **exit 0 かつ出力ゼロ**で戻った。`.done` も成果物も不在で、
  `pgrep` で codex 子 (launcher と exec の 2 process) の生存と artifact の増加を確認して
  張り直したところ、子は正常に完走した。恒久対応 (`.done` の exit code と producer 生死で
  判定し、待ち手の rc も通知も信じない) がそのまま効き実害はゼロ。**追加事実は無く、
  2026-08-23 の「段 6 レビュー B の待ち手」と同一の形である。**
