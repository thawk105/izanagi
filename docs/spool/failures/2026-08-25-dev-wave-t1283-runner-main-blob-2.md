---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1283-runner-main-blob
seq: 2
---

## 再発

### F57

- **再発: 2026-08-25** — dev-wave-t1283-runner-main-blob の焦点走で
  `test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean` が再び落ちた。
  本文は 2026-08-24 の再発項と逐語一致で、`orchestrator/campaign/execution_guard.py` の
  `CertifiedWriterAuthorizationError`「Pegasus compute では receipt state 内で一意な required
  authorization_contract だけを受理する」。当 wave の差分は campaign 層にも当該テストにも触れていない。
  **前回の再発項が残した「引き金は file 集合 (xdist の同居関係)」という読み方は、今回の実測では
  成立しない。** 当該 nodeid を**単独で**投入した走行 (1 件だけの収集) でも同じ本文で落ちた。
  差分の有無でも変わらず、実装前後の 2 回の焦点走で同一である。共通しているのは計算ノードで
  走ったことだけで、`_site_policy.current_site() == PEGASUS_COMPUTE` の枝でのみ発火する条件は
  ソース上も一致する。すなわち観測されているのは file 集合依存ではなく **site 依存の決定的な赤**
  である可能性が高い。login node では重量ガードが pytest の直接起動を拒むため、当 wave では
  対照の緑を取れていない。所有は引き続き [T-1079]。
- 影響範囲: この機体の計算ノードで走る焦点走・変異 baseline。変異 baseline は
  `--deselect` で外して緑を確保した (DW-C01 の既定手順)。
