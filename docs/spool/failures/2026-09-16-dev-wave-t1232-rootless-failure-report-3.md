---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t1232-rootless-failure-report
seq: 3
---

## 再発

### F29

- **再発: 2026-09-16** — [T-1232] wave。段 1 brief で 2 つの前提を、命題と違う対象から導いた。
  (1) producer が failure-only report を実際に publish する例として
  `orchestrator/tests/test_p3_autonomous_workload_trial.py` の
  `test_registered_formal_noncertifying_build_crash_is_indeterminate` を挙げたが、このテストは
  `assert_autonomous_trial_completeness`・`assert_autonomous_trial_execution_digest_chain`・
  `layer3_report.render` (admitted を返す fake)・`assert_campaign_layer3_chain` をすべて monkeypatch で
  無効化しており、**実出力の証人にならなかった**。(2)「root を省くと失われるのは path identity 束縛だけ」と
  結論したが、読んだのは `assert_campaign_layer3_chain` の失敗 cell 区間だけで、その手前で走る
  `verify_s8c_cross_binding` の build population 要件を含めていなかった。実際には campaign identity を持つ
  失敗 cell は **root を与えても** cross-binding が落とす。いずれも読解自体は正確で、
  **読解対象が命題と違っていた。** 検出は段 2 の codex plan で、段 3 の敵対レンズ 2 本も独立に同じ 2 点を
  指摘し、親が現物で裏取りして段 4 裁定で訂正した。brief は実測 1〜6 を「source 読解であって実走ではない」と
  明記していたが、**テストを証拠に挙げるときにその検証機構が無効化されていないかを確かめる手順**は
  書いていなかった。恒久対応は既存のまま (再発検知行どおりレンズに攻めさせる経路が機能した)。
  逐語は `output/insights/2026-09-16/t1232-rootless-failure-report/verbatim/s4-ruling.md` §2。
