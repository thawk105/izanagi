---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1841-proposal-causal-binding
seq: 2
---

## 再発

### F161

- **再発: 2026-08-27** — 受理集合を縮小する wave で正例を段 4 に登録していたが、
  その正例が gate の**発火する側**しか覆っていなかった。gate 冒頭の早期 return
  (対象外の入力をそのまま通す枝) は、それ自体が受理を保つ機構でありながら無検査だった。
  早期 return を潰す変異は「正当な継続を恒久拒否する」退行を作るのに、
  段 3 と段 6 の敵対レビュー 4 本を含め全テストが緑のまま生存した。変異走行だけが暴いた。
  恒久対応は `orchestrator/tests/test_p3_s4_loop.py::test_b4_nonempty_admitted_history_allows_valid_continuation`
  と、変異事前登録の `MUT-T1841-M2-GATE-APPLIES-TO-EVERY-STATE`
  (`output/insights/2026-08-27_t1841-bootstrap-history-gate-mutation-ledger.json`)。
  再発検知の拡張: 受理集合を縮小する wave の正例は、新しい拒否条件が成立する側だけでなく、
  **gate が早期 return して対象外とする側**も覆う。
