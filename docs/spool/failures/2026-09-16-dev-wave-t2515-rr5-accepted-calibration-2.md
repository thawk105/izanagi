---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2515-rr5-accepted-calibration
seq: 2
---

## 再発

### F348

- **再発: 2026-09-16** — 向きが逆の同型。段 2 plan 子と段 3 レンズ B が、`attempts/*/calibration.md` を
  固定集合と完全一致で比較する `test_env_attestation.py::test_probe_output_v1_corpus_is_exact_and_replays_all_physical_copies`
  の本文だけを読み、「新しい attempt を 1 件足すと赤になるので実装子が要る」と独立に判定した。
  実際には同 node は `orchestrator/tests/growth_test_holds.py:300` に
  `hold_axis=output_artifacts` で登録済みで、実走は `1 skipped` になる。親が実走して反証し、
  不要な実装子と変異 matrix を立てずに済んだ。F348 は「保留 node を期待赤に選ぶ」= 赤になると
  思った node が走らない型で、本件は「走らない node を根拠に作業を増やす」型である。
  **どちらも根は同じ — テストの実在と実行は別問題で、子は `_HOLD_ROWS` を見ない。**
  親の brief も「赤の予測は hold 台帳を見てから書け」と指示していなかった。
  ただし hold による skip は整合性の確認ではない。本 wave は投入前から 6 件あったコーパス乖離と
  増分 1 件を `output/insights/2026-09-16/t2515-rr5-calibration/README.md` §7 に記録した。
