# [T-2867] 段 6 裁定 2 (親、2026-09-29 16:2x JST)

入力: fix 1 統合 commit `98a1e894f` の焦点走 `focus-2.log` (5 件赤) と `focus-b4.log` (wiring probe を commit 後に単独再走 → 65 passed、赤は未 commit の新 file を数えたもので実装に帰属しない)。

| G | 赤 | 判定 | 直し (子 X、所有 = 段 5 の X と同じ + なし) |
|---|---|---|---|
| G1 | 既存 `test_p3_s4_loop_policy.py::test_record_reject_cli_uses_coder_only_input_without_build_opt_in` (期待 `only coder`、実際 `invalid preview proposal fields`) | real — 対照でない経路の拒否文言を変えた。既存の受理・拒否と文言を変えない | 対照でない経路 (`--contrast-ledger` 無し) の `load_proposal_file` の拒否文言を基点と同じにする。対照の経路だけ `{coder, auditor}` を受ける |
| G2 | 新 `test_contrast_unit_rejects_changed_proposal_before_slot_start` (`AttributeError: 'object' object has no attribute 'policy'`) | real — テストの誤り | 実体の build context を使うか、driver の既存 seam に合わせてテストを直す (sha256 不一致で rc=2 と `slot-start` 無しを確かめる本体は変えない) |
| G3 | `test_p3_exploration_namespace.py::test_driver_ast_supplements_runtime_namespace_gate[p3_s4_loop_policy]` (AST の run_campaign 呼出し 3 対 契約 2) と `test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` (合計 25 対 24) | real — 静的 10 µs の経路が 3 つ目の `run_campaign` 呼出し箇所を足した。閉じた inventory の期待値は変えない | ref-fixed10 を既存の呼出し箇所に載せる: `run_stock_control` に「静的 10 µs」用の最小の引数 (genome の BACKOFF_FIXED=10 と `patches/silo-backoff-fixed.patch` の適用・既存の条件 gate の呼出し) を足し、`measure_slot` はそれを呼ぶ。driver の `run_campaign` 呼出しを基点どおり 2 個に戻し、段 5 で変えた `test_campaign.py` の 2 か所 (`p3_s4_loop_policy.py` の数 3) を基点の値 (2) に戻す |
