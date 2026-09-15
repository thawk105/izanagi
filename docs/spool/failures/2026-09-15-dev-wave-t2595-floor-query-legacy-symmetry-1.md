---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-15
wave: dev-wave-t2595-floor-query-legacy-symmetry
seq: 1
---

## 再発

### F591

- **再発: 2026-09-15** — [T-2595] の段 1 brief が、`DW-G05` の成果物影響を「欠陥地点へ至る経路が
  実在すること」だけで書いた。段 3 の敵対 2 本が独立に否定し、親が現物で検算した。同じ呼び手
  `_Runner.run()` は `_retry_round` を呼ぶ手前で round の全 retry start に `_replay_cut6_start` を
  掛け、その先の `_assert_retry_start_authorized_locked` が同じ混在履歴を先に拒否する。consume は
  測定 callback より前に走る。さらに production には registry recovery 行を書く呼び手が無い
  (`record_attempt_recovery` の非テスト参照は内部委譲のみ)。閉じた非対称は実在するが、
  **現時点の production からは到達しない**。前回は実装後に段 6 が検出したのに対し、今回は F591 の
  恒久対応である段 3 / 段 6 の実効性レンズが実装前に検出した。経路の実在は到達性を含意しない、
  という同じ誤りである。
