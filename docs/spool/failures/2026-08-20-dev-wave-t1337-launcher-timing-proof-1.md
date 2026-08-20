---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: dev-wave-t1337-launcher-timing-proof
seq: 1
---

## 再発

### F357

- **再発: 2026-08-20** — `trial_registry.py` / `p3_autonomous_workload_trial.py` /
  `s8c_preregistration_evidence.py` を編集した状態で13ファイル consumer test 一括走を投入し、
  19 failed + 34 errors を観測した。理由行はほぼ全て `contract-loader-drift` だった。
  統合 commit 後に同じ範囲を再走したところ 1531 passed / 0 failed へ解消し、実装差分由来の
  赤は0件だった。判定手順 (赤の理由行に `contract-loader-drift` があれば commit してから
  再走する) は既載のとおりで機能した。

### F290

- **再発: 2026-08-20** — `tools/check_ai_provenance.py` の `KNOWN_PROVENANCE_VIOLATIONS`
  registry へ known-violation エントリを1件追加する fix 指示に、検査コマンドとして
  監査ツール本体の実行だけを書き、対になる meta-test file
  (`orchestrator/tests/test_check_ai_provenance.py`) を名指ししなかった。子はツール本体の
  rc=0 を確認して完了報告したが、受入全走 (attempt 1) で
  `test_known_violation_ledger_matches_literal_entries` が赤になり、受入を1回余分に消費した
  (attempt 2 で解消、`verdict=non-attributable-only` で受入成立)。恒久対応・再発検知は
  既載のとおり (台帳・定数表を編集させる指示には対になる meta-test file を必ず名指しする) で、
  今回は指示作成時にこの既知パターンを見落とした。
