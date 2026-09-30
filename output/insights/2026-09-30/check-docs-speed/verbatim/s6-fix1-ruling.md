# fix 第 1 巡の裁定 (親、2026-09-30 JST)

根拠: 焦点走 r1 (wave 木に impl-r1.patch 適用、計算ノード): 1 failed, 678 passed, 3 skipped。赤は
`orchestrator/tests/test_growth_test_holds_contract.py::test_every_held_module_has_exact_top_level_guard_binding` の 1 件だけ
(test_check_docs.py の追加 test が `enforce_held_functions(...)` 呼出しと `if __name__ == "__main__":` guard の後ろにあり、
契約「call must follow every top-level test definition」「call must precede the __main__ guard」に反する)。
レビュー A (s6/out-rev-a.md) と B (s6/out-rev-b.md) に判定ロジックの must-fix はない。

## fix 項目

- F1 (must-fix、既知欠陥): 追加した test 群と参照実装 helper (`_speed_reference_raw_slice`、`_speed_reference_visible_lines`、
  `test_speed_*` 全部) を、`_run()` 定義の後・`from orchestrator.tests.growth_test_holds import enforce_held_functions` の import 行の**前**へ移す。
  中身は変えない。`enforce_held_functions(...)` 呼出しが全 top-level test 定義より後、`__main__` guard より前になること。
  既存 `_run()` 手動 runner が新 test を拾う場合、parametrize 付き test の扱いで壊れないことを確認する (既存 parametrize test と同じ扱いなら可)。
- F2 (レビュー A1 / B2、採用): `_newline_positions` の lru_cache を `main()` の `finally` で `_newline_positions.cache_clear()` し、
  cache の寿命を読取 cache と同じ 1 回の main() に揃える (呼出し側 `_READ_TEXT_CACHE.reset` と同じ finally 内)。maxsize=4 は維持。
- F3 (レビュー B1、採用): `_ArchiveWorklog.entry_ids` (全 entry 分) を、archive 境界の sink に使う**先頭 entry の本文 ID だけ**の保持に変える
  (例: フィールド `first_entry_ids: list[str]`、既定値を持たせる必要がなければ `field` import を消す)。archive 内遷移は従来どおりループ内の局所 list を使う。
  所見の文言・順序・sink の取り違えがないこと (変異 M4 が引き続き T4 で赤になること)。

## 不採用

- レビュー A2 (T4 の断片 assert): 不採用。判定全文の一致は repo 外 probe E1/E2 (旧版との stdout 全文比較) で示す。T4 は M3/M4 の検出用。
- レビュー A3 / B3 (所要): 焦点走 r1 で test_check_docs を含む 682 node が 14.6 s (xdist) で完了。追加 test の個別所要は親が段 7 で記録する。

## 実走してほしいもの

子の環境で pytest を直接起動できない場合は、`python3 -c` / 直接関数呼出しで追加 test 関数を呼ぶ確認と、
`test_growth_test_holds_contract.py` の当該 test 関数を直接呼ぶ確認を行い、「pytest 未実走」と明記する。親が計算ノードで再走する。
