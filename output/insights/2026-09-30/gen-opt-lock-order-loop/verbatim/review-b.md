## 総括

**条件付き GO。** 単位 1 の production 追加約 101 行、単位 2 の約 523 行は、裁定の上限 350／600 行以内です。必須の拒否条件と正例は静的には概ね揃っています。ただし、登録外場面の反例で候補を拒否する点は裁定と食い違うため、局所修正が必要です。テスト・build の実走結果は未確認です。

## 所見

1. **must-fix — 登録外場面の反例が全候補を拒否する。** [silo_lock_order_model_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/silo_lock_order_model_gate.py:115) は全場面の反例を集め、141 行で一律に `model-counterexample` とします。裁定は登録外場面を「記録だけ」として拒否しない指定です。**放置時:** 登録場面がすべて合格しても、追加場面の反例だけで build と certified 選択集合が減ります。**修正:** 反例の拒否判定を登録場面に限り、登録外場面の ID と反例は上限内で履歴に投影する。追加場面に反例がある正例 test を足す。

2. **should-fix — flag 強制式が二箇所にある。** [loop.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/loop.py:828) と [pipeline.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/pipeline.py:1746) が同じ実効要求を別々に計算します。前者は先行する source capture、後者は直接 `evaluate` する caller に必要で、単純な片方の削除では足りません。**放置時:** 式がずれると、D5 snapshot 欠落による過剰拒否、または要求漏れによる certified 受理集合の拡大が起こり得ます。**修正:** 小さな共通の純粋関数に式を一本化し、二つの呼出し位置は維持する。

3. **should-fix — 版 ≥2 の判定を、版 2 固有の計数 key 集合が狭める。** [p3_s4_loop_lock_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_lock_order.py:150) は `counts` の key 完全一致を certified 条件にしています。**放置時:** 後続の意味の版で計数が追加されると、required・D5 pass・certified の結果も `gate-witness-invalid` になり、裁定の「版 ≥2」より受理集合が狭まります。**修正:** 現行 8 項の存在と値を検査してその 8 項だけ投影する。追加 key を持つ正例を試す。

4. **nit — 履歴の再読込検査は生成側の関係を保証しない。** [p3_s4_loop_lock_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/campaign/p3_s4_loop_lock_order.py:225) は `verifier_digest=None` でも通すため、`outcome=certified`、`model_evidence_kind=fixture` の行を coder 入力に載せられます。**放置時:** 手で変えられた台帳が coder の自己履歴に誤った certified 参照として現れます。**修正:** `certified` 行について model evidence、reject code、verifier digest の関係だけ追加検査する。台帳全体の汎用 schema 層は不要です。

5. **nit — M5 の bytes 試験は比較対象を現行出力から組み立てている。** [test_verifier_capability_gate_witness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-md20-lock-order-loop/orchestrator/tests/test_verifier_capability_gate_witness.py:72) の期待値は `body["normalized_sources"]` を再利用します。**放置時:** その field 自体の旧版からの変化は検知できず、「既存 bytes と同一」という試験の根拠が弱くなります。**修正:** 既存 fixture の固定 bytes と比較する。現状の `gate_d5_sources` 不在検査は残せます。

裁定外の大きな停止制御や対照運用一式の移植は見当たりません。CLI 権限登録と inventory の追加は、実在する各 1 call site に対応しています。

## 変異 M1〜M12 の単一理由性

| 変異 | 外す一か所と赤になる test | 別層による遮り |
|---|---|---|
| M1 | `pipeline.py:1746` の flag 強制 → `test_m1_flag_forces_required_evaluate` | flag=1・明示なしで直接 evaluate。loop は通らない。 |
| M2 | `loop.py:980` の evaluate keyword → `test_m2_explicit_requirement_passes_run_campaign` | flag=0 なので pipeline 強制は遮らない。source capture 側の独立 assert もある。 |
| M3 | `core.py:652` の verify への転送 → `test_m3_required_capability_rejects_absent_gate_file` | capability を直接呼び、gate file 欠落で required の効果を観測する。 |
| M4 | `core.py:301` を disk D5 に戻す → `test_m4_required_d5_uses_snapshot_not_disk` | snapshot と disk を反対の状態にした直接判定で、再 capture は遮らない。 |
| M5 | `source_digest.py:157` の省略条件 → `test_m5_unrequested_snapshot_legacy_bytes` | 他層は遮らない。ただし上記の期待 bytes の弱さがある。 |
| M6 | `silo_lock_order_model_gate.py:78` の未登録拒否 → `test_m6_unregistered_registry_rejected` | 結果は正常形なので schema が先に遮らない。 |
| M7 | 同 `:128` の digest 照合 → `test_m7_result_digest_cannot_supply_expectation` | 別 digest も形式上は有効。 |
| M8 | 同 `:134` の stop_reason 照合 → `test_m8_complete_max_states_is_incomplete` | `complete=True` で他の完了条件は満たす。 |
| M9 | 同 `:130` の登録場面欠落照合 → `test_m9_required_scenario_missing` | 空配列は schema 上有効。 |
| M10 | 同 `:141` の反例拒否 → `test_m10_counterexample_rejected` | 反例は validate を通る形。 |
| M11 | `p3_s4_loop_lock_order.py:117` の反例投影に余分 field → `test_m11_counterexample_projection_has_exact_keys` | validate 済み dataclass を直接渡し、入口 schema に遮られない。 |
| M12 | 同 `:163` の required 照合 → `test_m12_required_false_cannot_certify` | synthetic verify 結果の他の certified 条件は真。 |

これは静的な単一理由性の点検であり、変異 test の実走結果ではありません。

## 裁定との食い違い

- **登録外場面は記録だけ**という裁定に対し、実装はその反例でも拒否します（所見 1）。
- **意味の版 ≥2**という裁定に対し、計数 key の完全一致が将来版を拒否し得ます（所見 3）。
- 裁定の正例・禁止は単体 test で概ね覆われています。追加が必要なのは、登録外場面に反例がある正例と、追加計数 key を持つ版 ≥2 の正例です。