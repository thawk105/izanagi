---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1115-env-bytecode-check
seq: 2
---

## 再発

### F43

- **再発: 2026-08-20** — 段6 の軽量 fix子 (1行追加だけの修正) 2回とも、親が「変更した
  file:line を明記するだけでよい」と簡潔な報告を求めたところ、報告が499/494 bytes で
  500 bytes 下限に届かず `tools/check_codex_output.py` に不受理にされた
  (`codex_exit_code=0`, `accepted=false`, `validator_rc=1`)。2026-08-18 再発と同型
  (「2〜5行で書け」で500 bytes未達)。作業自体は `attempt-0001.output.md` に正しく
  書かれており親が fallback で読んで採った。2026-07-28/2026-08-18裁定 (`DW-O01` への
  prose 追記は見送り、恒久対応はテスト・機械検査優先) を踏襲し、今回も reference
  編集はしない。
