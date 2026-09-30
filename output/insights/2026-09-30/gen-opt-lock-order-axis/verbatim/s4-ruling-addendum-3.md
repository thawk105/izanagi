# 段 4 追補裁定 3 — screening driver の条件既定値表への SILO_ORDER_VARIANT の追記 (2026-09-30)

発端: 受入全走 attempt 2 (tip 562fec6d1、claimed main 213d411c6、1 failed / 28,423 passed / 74 skipped) の赤 1 件
`orchestrator/tests/test_screening_driver.py::test_screening_condition_requests_cover_exact_define_specs`。
同 test は `screening_driver._CONDITION_DEFAULTS` の macro 集合が `condition_meaning_gate.DEFINE_SPECS` と一致することを要求する。

帰属: 自分起因。段 4 で許可した「SILO_ORDER_VARIANT を条件意味 gate の supply domain へ登録する」ことの consumer (`orchestrator/campaign/screening_driver.py` の `_CONDITION_DEFAULTS`) を、段 1〜6 の consumer 列挙と焦点走の file 集合から落としていた (焦点走に test_screening_driver.py を含めていなかった)。受入全走の他の consumer (`DEFINE_SPECS` を読む backoff_sweep・s1_direct_comparison・silo_ladder_rung1・t2228 probe と各 test) は緑。

許可する変更: `orchestrator/campaign/screening_driver.py` の `_CONDITION_DEFAULTS` に `"SILO_ORDER_VARIANT": 0` を 1 行追記する (inert 値。`SILO_POLICY_VARIANT` の隣)。既存 test の期待値は変えない (この test は追記で緑になる設計)。

受理・拒否の含意: screening driver が組む条件要求に SILO_ORDER_VARIANT=0 (stock と同一の前処理結果) が加わるだけで、既存の macro の既定値・要求は変わらない。通る正例: `test_screening_condition_requests_cover_exact_define_specs` が緑になる。
