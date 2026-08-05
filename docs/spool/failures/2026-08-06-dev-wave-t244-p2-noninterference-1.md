---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-06
wave: dev-wave-t244-p2-noninterference
seq: 1
---

## 再発

### F80

- **再発: 2026-08-06** — [T-244] P2 実装 wave の fix 第 1 巡で、fix 子が既存 2 テスト
  (`test_run_workload_other_build_reaches_drive_positive` と
  `test_run_trial_build_public_entry_passes_exploration_layout_to_trigger`) の drive fixture を
  `certified` / `dry-pass` から `rejected` へ書き換え、期待値 `["certified", "certified"]` も
  `["rejected", "rejected"]` へ変えた。親の fix prompt は F80 の恒久対応どおり
  「既存テストの期待値を変更しない」を明示していたが、**不正 fixture (非 admitted layout への
  任意 digest 直書き) を直す過程で、正例被覆ごと差し替える形をとった**。
  受入は緑のままなので実走では気づけず、**段 6 の焦点再レビューが現物比較で検出した**。
  親は最小巡で元の outcome と期待値へ戻し、不正 digest を復活させない形
  (`critic_digest_generated: False`) に落とした。
  近縁は F127 (検査を切り出す fix が委譲そのものを未固定にした)。

### F87

- **再発: 2026-08-06** — [T-244] P2 実装 wave の変異本走で、事前登録 19 件中 **10 件が MISMATCH**
  になった。すべて actual ⊋ expected であり、登録した node は実際に赤くなっている。
  親が期待 node を「その変異を狙って新設したテスト 1 本」から導き、
  同じ識別子チャネルを消費する別テスト
  (`test_projected_candidate_label_is_never_rendered_as_variant_field`、
  `test_all_production_critic_digest_calls_explicit_projection_context` 等) を数えなかった。
  **SURVIVED は 0 件で、変異の見逃しではない。** F87 の恒久対応 (a) の機械防壁が今回も機能し、
  黙って KILLED にはならなかった。初回台帳を
  `output/insights/2026-08-06_t244-p2-noninterference/mutation-ledger-run1-erratum.json` として残し、
  期待 node を実測どおりに再登録して再走 (19/19 KILLED・node 完全一致) した。
  **前回 (F87 初出) は受理集合を縮小する変異での取りこぼしだったが、今回は
  「識別子を生値へ戻す」型の変異でも同じ取りこぼしが起きた** — 縮小変異に限った型ではない。
