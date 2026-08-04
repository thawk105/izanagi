---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-04
wave: dev-wave-t399-t400-signal-mitigation
seq: 2
---

## {{D:probe-evidence-three-way-split}}. probe 証拠の admissibility を単一連言から 3 分離 (split-v2) へ移す

**決定:** T-361/T-362 系 probe controller (`output/insights/2026-08-03_t361-t362-cluster-probes/
driver/run_probes.py`) の attempt 判定を、単一の `admissible = all(validity)` から
`observation_valid` (probe が有効に観測した) / `attempt_safe` (attempt の結末が安全だった) /
`accounting_available` + `accounting_integrity_valid` + `termination_cause_consistent`
(会計証拠の有無・完全性・因果整合) の 3 分離 (`evaluation_model = "split-v2"`) へ移す。
authoritative 選出は `observation_valid かつ terminal_proven` だけで行い、
危険側の観測 (`attempt_safe=false`) も authoritative になれる。危険結論は閉じた
`unsafe_reason` (cleanup_order_invalid / post_restore_canary_mismatch 等) からだけ導出し、
費用・qdel・artifact hygiene の失敗を危険結論に混ぜない。legacy 記録は
`evaluation_model` key 欠落だけを legacy と認め、`admissible:true` の既存 authority のみ維持、
`admissible:false` は再認定せず、明示 null・未知値は拒否する。stale session の無い
completed / terminal-unproven request は、保存 raw (qsub/qwait receipt) の再検証を通過した
場合だけ終端実証へ移行できる。

**理由:**
- 旧連言は「観測の有効性」「結末の安全性」「会計記録の有無」を混同し、SIGKILL で cleanup が
  走らないという**本命の危険観測そのもの**が `admissible:false` になって authoritative に
  なれなかった (worklog (149) の実測、[T-400])。危険側の観測が構造的に記録不能な判定器は、
  fail-closed ではなく fail-blind である。
- racct の反映遅延 (欠測) は観測の欠陥ではないが、request 束縛の混線・件数過剰・因果矛盾は
  観測の欠陥である。「外してよいのは欠測だけ」という線引きを field 分離で機械化した。

**却下した選択肢:**
- 会計項を丸ごと evidence 側へ移す (親の当初案) — 敵対レンズが「束縛・因果検査まで消える」と
  実証し、integrity / cause を観測 gate に残す 3 分解へ改めた。
- 2 field 分離 (観測/安全のみ) — 会計の欠測が観測無効へ倒れる旧問題が残るため 3 系へ拡張した。
- 判定緩和による leg 進行の回復 — 必要なのは保存 raw を再検証する閉じた migration 経路であり、
  受理集合を広げる緩和ではない。
