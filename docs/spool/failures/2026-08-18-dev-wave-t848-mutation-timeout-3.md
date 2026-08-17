---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t848-mutation-timeout
seq: 3
---

## 再発

### F109

- **再発: 2026-08-18** — 変異 harness の走行束縛テストで、fixture が判定器の読む値
  (`request.json` の `environment` に載る nonce) を**自分で書いて**いた。実 producer は
  `tools/run_tests.py` から dispatch へ環境を渡す連鎖だが、fixture はその連鎖を一度も通さない。
  そのため carrier が将来壊れてもテストは緑のまま残る。段 6 の焦点再レビューが摘出し、
  親は連鎖の各段 (harness が nonce を置く → run_tests は同変数に触れない →
  `_dispatch_environment()` が素通しする → dispatch の env allowlist に実在する →
  `request.json` に載る) を実コードで確認して**挙動側は成立**と裁定した。
  連鎖を pin するテストの新設は本 wave の scope 外として後続タスクへ送った。
