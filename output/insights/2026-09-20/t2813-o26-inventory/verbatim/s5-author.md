## 変更の要約

変更前の実測はrc=1、DW-O26の「節全体が exact 契約と不一致」1件でした。

- `tools/check_docs.py`: DW-O26 literal本文だけ更新（+8/-8行）。
- `orchestrator/tests/test_check_docs.py`: 独立literal、bytes期待値979→998、旧本文依存のM8を更新（+10/-11行）。目安超過はM8追随分です。

exact登録・単節予算1,000・拒否結果の期待値は不変です。docsは変更していません。

## byte 一致の確認

repo内の一時scriptで実測し、終了後に削除しました。

| 対象 | UTF-8 bytes | operations.md内の出現数 |
|---|---:|---:|
| docs DW-O26節 | 998 | 1 |
| production literal | 998 | 1 |
| 合成fixture | 998 | 1 |

正本fileとdocsのbyte一致、`literal == fixture == docs`、NFC、末尾改行1つを確認しました。attack文字列「静的レビューが見落とした破れを」は各本文に1回です。

## 既存 test 追随の有無

追加依存が1件ありました。

`test_non_attributable_landing_contract_mutations_have_one_finding[M8]` の削除対象を、新本文の「変更 test file は受入前に単独走で確認する。」へ更新しました。変更成立のassertと単一違反の期待値は維持しています。

その他の旧本文断片への依存はありませんでした。`o26_contract_weakened` のattack文字列は不変です。

## 実走結果

指定の `pytest.main(...)` 方式で実行しました。

| 対象 | 結果 | rc |
|---|---|---:|
| 指定焦点集合＋M8を含む変異集合 | 36 passed、1 skipped、546 deselected | 0 |
| `orchestrator/tests/test_check_docs.py` 全583件 | 580 passed、3 skipped（316.20秒） | 0 |
| 制約meta-test | 4 passed | 0 |
| `python3 tools/check_docs.py` | 最終行 `check_docs: 違反なし` | 0 |
| `git diff --check` | 問題なし | 0 |

焦点走のnodeidは以下です。共通prefixは `orchestrator/tests/test_check_docs.py::`、括弧内は実行parameterの列挙です。

```text
test_dev_wave_layer_budget_contract_is_literal
test_dev_wave_layer_budget_rejects_plus_one[l1, l1_5, l2_section]
test_operation_contract_pins_exact_section_set
test_dev_wave_dispatch_route_rejects_separator_in_normative_candidate[\u2028, \u2029]
test_normative_exact_section_contract_is_handwritten_and_complete
test_dw_o18_exact_section_pin_accepts_synthetic_fixture
test_dw_o26_exact_section_pin_accepts_synthetic_fixture
test_non_attributable_landing_contract_mutations_have_one_finding[M1–M8, M10–M12]
test_dw_o28_exact_section_pin_accepts_synthetic_fixture
test_normative_exact_section_pins_reject_raw_html_inside_pinned_sections
test_dw_o20_points_to_dw_c01_and_drops_legacy_submodule_command
test_dw_c01_is_immediately_before_dw_stop
test_command_docs_guard_positive_controls[
  stage6_o25_deleted, condition_18_o18_deleted, condition_18_o26_deleted,
  o25_contract_weakened, o25_before_o01,
  o26_section_deleted, o26_heading_only, o26_contract_weakened,
  o28_section_deleted, o28_heading_only, o28_contract_weakened
]
```

meta-testの実走nodeid：

```text
orchestrator/tests/test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted
orchestrator/tests/test_plain_runner_coverage.py::test_allowlist_has_no_stale_or_self_runnable_entries
orchestrator/tests/test_plain_runner_coverage.py::test_this_metatest_is_itself_self_runnable
orchestrator/tests/test_growth_test_holds_contract.py::test_every_held_module_has_exact_top_level_guard_binding
```

既存growth holdによる未実走nodeidは、同じ `test_check_docs.py::` 配下の次の3件です。焦点走のskipは最後の1件です。

```text
test_real_repo_clean
test_dev_wave_model_pins_accept_current_docs_contract
test_normative_exact_section_pins_accept_real_repo
```

## 波及

指定の `orchestrator/ tools/ hooks/ .codex/ .agents/` を検索した結果、対象symbolの所有外参照元はありませんでした。

参照は `check_docs.py` のexact登録と、`test_check_docs.py` の合成repo生成・独立literal比較・bytes検証・正例検証に限定されています。`docs/failures.md` 等の逐語引用は歴史記録として未変更です。

## 未了・懸念

既存holdの3件はpassedに数えていません。実repo検査は別途実行して違反なしでした。親の全走・段6変異検証は本実走で代替しません。

## 総括

実装・指定検証は完了しました。差分は指定2ファイルだけで、working treeに残しています。commit・stageは行っていません。