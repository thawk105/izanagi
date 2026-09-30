# 段 4 追補裁定 4 — main 側で新設された site 数合計 pin への SILO_ORDER_VARIANT の加算 (2026-09-30)

発端: 合成 merge c495d42bf 後の焦点走 f3 (09c12874a、19 file、1 failed / 1,831 passed / 5 skipped) の赤 1 件
`orchestrator/tests/test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`
の `assert sum(G._CONDITIONAL_BRANCH_SITE_COUNTS.values()) == 277` (実数 291)。

帰属: この合計 pin は main 側 (vhash-interval-gc) が新設したもので、wave 側の親には無い。合成後の `_CONDITIONAL_BRANCH_SITE_COUNTS`
には wave 側の `SILO_ORDER_VARIANT: 14` が入るので、合計は 277 + 14 = 291 になる。段 4 で許可した SILO_ORDER_VARIANT の登録
(site 14) に従属する期待値で、実装の誤りではない。

許可する変更: 同 test の `== 277` を `== 291` にする 1 行だけ。他の期待値は変えない。

受理・拒否の含意: 登録簿の内容は変わらず、合計の記述が合成後の実数に追随するだけ。通る正例: 同 test が緑になる。
