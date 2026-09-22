# 段 6 裁定 2 巡目 — [T-2857] (2026-09-22 21:0x JST、親 = Claude manager)

入力: 焦点走 f3 (18048.nqsv、8 failed / 4773 passed / 8 skipped、log = job dir `focus-3.log`)、修正前 coverage (18034.nqsv、
`coverage-pre1.json`: `RuntimeError: condition gate rejected SILO_POLICY_VARIANT`)、原因調査 (read-only 子、要旨は下の G1)。
fix-1 の F1〜F8 が閉じたこと: f2 の赤 8 件は f3 で全件消えた。

| # | 出所 | 内容 | 判定 | 扱い |
|---|---|---|---|---|
| G1 | coverage-pre1 | driver の gate が軸 flag `SILO_POLICY_VARIANT` の gate にも case の別 macro (norw では `IZANAGI_BREAK_NOREAD_VALIDATION=1`) を CXX flags の companion として強制する。軸 ON の norw patch は骨格の `#if SILO_POLICY_VARIANT` 1 site (read_tid の要因記録) を `#if IZANAGI_BREAK_NOREAD_VALIDATION` の `#else` に包むので、要求・既定の両前処理からその site が消え、観測 requested (14,14) / default (0,14) が期待 (15,15) / (0,15) と一致せず `compile-time-branch-selection-mismatch` で red になる (condition_meaning_gate.py の `_assert_compile_time_branch_selection`)。既存 driver (`s3_lock_coverage.py`・`s8a_trigger_coverage.py`) は 1 gate = 1 macro で companion を混ぜない | real | fix。1 gate = 1 macro にし、軸 flag の gate には companion を混ぜない。他の gate も、宣言した site が実 source で見えるために要る場合を除き companion を混ぜない。gate の検査は変えない |
| G2 | f3 赤 6 件 (`[IZANAGI_SILO_POLICY_PROBE]`・`[IZANAGI_BREAK_SILO_POLICY]` の `compile-command-invalid`) | この 2 macro の DefineSpec が軸 flag を companion (`("SILO_POLICY_VARIANT", "1")`) として CXX flags で供給する。F2 で fixture の universal definition が `SILO_POLICY_VARIANT=0` を出すようになり、compile command に同名 define が 0 と 1 で並ぶ。実機でも universal definition の `SILO_POLICY_VARIANT=1` と重なる | real | fix。2 つの DefineSpec から companion を外す (cache 経路の前提 flag は configure 引数で与える。既存の `IZANAGI_BREAK_TRIGGER_MISATTR` が `BACKOFF_TRIGGER_GATING` に対してとる形)。本 wave が足した test の期待値 (companion の期待) を追随 |
| G3 | f3 赤 1 件 (`test_production_build_sinks_include_certify_calibration_script`) | F1 で driver の build sink の行 (本 wave が pin した 348) が動いた | real | fix。本 wave が足した pin を新しい行へ追随 (既存 pin は動かさない) |
| G4 | f3 赤 1 件 (`test_coverage_reuses_controls_and_separates_prefix_exits`) | driver の TRACE=0 確認の経路で `_owner_command` の結果に `command` key が無い (`KeyError: 'command'`、silo_policy_coverage.py:580) | real | fix。compile_commands の行の `arguments` / `command` の両形を扱う |
| G5 | 相談 A・調査 | driver の gate 拒否の例外文が supply / meaning の状態と理由 code を捨てている | real | fix。既存 `s3_lock_coverage.py` の拒否文と同じ形で載せる |

変異の事前登録: 追加なし (G1〜G5 は M-GATE-DOM と既存の閉集合 test の範囲)。M-GATE-DOM の置換 anchor は fix-2 統合後に固定する。
