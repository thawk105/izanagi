---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2327-s1-sort-contract-binding
seq: 3
---

## 再発

### F39

- **再発: 2026-09-08** — s1 materializer の bytes を変える wave ([T-2327]) で、materializer 全体 sha256 の literal
  (`orchestrator/tests/test_s8b_oracle_manifest.py`) は旧 hash 値の値検索で拾って更新したが、**その literal を含む
  golden bytes (`PIN_GATE_SPEC_RAW`) の sha256 を pin する 2 段目の定数 (`PIN_GATE_SPEC_SHA256`)** を落とした。
  1 段目の値検索は 2 段目に原理的に掛からず、author prompt の「他の literal は触らない」がそれを固定した。
  検出は親の焦点走 1 回目 (2 赤、land 前、実害なし)。恒久対応は F39 から変更しない。運用として、
  全体 hash の literal を更新したら、**その literal を含む bytes を hash する定数**まで同 file を追って列挙し、
  実装子の prompt で「派生 pin の再計算」を明示する。
