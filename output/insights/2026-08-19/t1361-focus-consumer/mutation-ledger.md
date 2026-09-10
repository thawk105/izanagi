# 変異台帳 (T-1361, 手動変異、DW-M05 の「独自 harness は同等の検査を備えると段4で事前登録する」に基づく)

baseline (無変異): `orchestrator/tests/test_check_docs.py` — 472 passed, 3 skipped
(既知の growth-hold、`test_check_docs.py::test_real_repo_clean` 等)、0 failed。

対象は `tools/check_docs.py` の今回の新規4hunk。各変異は DW-O19 の一時変異手順
(Edit → `python3 tools/run_tests.py orchestrator/tests/test_check_docs.py -q` →
`git diff --stat` で単一 hunk であることを確認 → `git checkout -- tools/check_docs.py` +
`git apply --include=tools/check_docs.py <baseline patch>` で復元) で実測した。
`tools/mutation_harness.py` (dispatch 経由) は本 wave では未使用 — 本走で必要な
Pegasus dispatch は、codex 子の pytest 実走 (段5/段6 全試行) がすべて `qstat -Q`
preflight rc=1 / `qlogin` socket 拒否で失敗する状況が観測されており、同じ infrastructure
不調を踏む蓋然性が高いため、DW-M05 の許容に従い親が直接手動変異で代替した。

## M1 — `REQUIRED_REFERENCE_SECTIONS["docs/dev-wave/operations.md"]` から union `{"DW-O26"}` を落とす

- 変異: union 演算を外し、`_OPERATION_NUMBERS` 由来の内包表記だけに戻す。
- 結果: **KILLED**。単独理由の直接証拠は
  `test_operation_contract_pins_exact_section_set`
  (`check_docs.REQUIRED_REFERENCE_SECTIONS[operations] == expected | {"DW-O26"}` の
  直接比較で red)。
- 冗長gate (DW-M03): `_build_min_repo()` が production 定数を直接参照して共有 baseline
  fixture を構築するため、この定数の変更は同 fixture を使う 273 件の無関係テスト
  (例: `test_provenance_dispatch_table_structure_is_exact` の全 parametrize、provenance
  とは無関係) も同時に red 化する (実測: 274 failed)。根本原因は 1 箇所 (この union) で
  あり、273 件は fixture 共有による過剰決定と判定し、単独変異の証拠 (expected_nodes) から
  除外する (DW-M03 「過剰決定なら…冗長gateと明記して単独変異の証拠から外す」)。

## M2 — `CONDITION_DISPATCH_CONTRACT["18"]` の上書きから `DW-O26` を落とす (`DW-O18` 単独に戻す)

- 変異: `_pairs(_OPERATIONS, "DW-O18", "DW-O26")` → `_pairs(_OPERATIONS, "DW-O18")`。
- 結果: **KILLED**。単独理由の直接証拠は同じ
  `test_operation_contract_pins_exact_section_set`
  (`check_docs.CONDITION_DISPATCH_CONTRACT["18"] == {(operations,"DW-O18"),(operations,"DW-O26")}`
  の直接比較で red)。
- 冗長gate: M1 と同じ機構で 273 件が同時に red (実測)。同じ理由で単独変異の証拠から除外。

## M3 — `DEV_WAVE_DW_O26_SECTION_LITERAL` の本文を1箇所変更する (「取り逃す」→「見逃す」)

- 変異: 定数文字列の末尾付近を1語変更。
- 結果: **KILLED**。単独理由の直接証拠は
  `test_normative_exact_section_contract_is_handwritten_and_complete`
  (`check_docs.DEV_WAVE_DW_O26_SECTION_LITERAL == _SYNTHETIC_DW_O26_SECTION` の直接比較で
  red)。
- 冗長gate: `_build_min_repo()` の共有 baseline fixture が本定数を使って DW-O26 節本文を
  描画するため、M1/M2 と同型の理由で 273 件が同時に red (実測)。同じ理由で除外。

## M4 — `DEV_WAVE_EXACT_VISIBLE_SECTIONS` から DW-O26 の登録行を削る

- 変異: `("docs/dev-wave/operations.md", "DW-O26 — ...")` → `DEV_WAVE_DW_O26_SECTION_LITERAL`
  の1エントリを削除。
- 結果: **KILLED、単独理由・冗長gateなし。** 実測で赤化したのは次の5件のみ
  (完全集合、DW-M08):
  - `test_normative_exact_section_contract_is_handwritten_and_complete`
  - `test_normative_exact_section_pins_reject_raw_html_inside_pinned_sections`
  - `test_command_docs_guard_positive_controls[o26_section_deleted]`
  - `test_command_docs_guard_positive_controls[o26_contract_weakened]`
  - `test_command_docs_guard_positive_controls[o26_heading_only]`
- この定数は `_build_min_repo()` の fixture 描画には使われず (節は常に描画される)、
  check_docs.py 側の「この節を exact pin 検査するか」という判定だけに使われるため、
  baseline fixture の内容と乖離せず、cascade が起きない。M1〜M3 との違いの根本原因。

## 総括

baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0。M1〜M3 は `_build_min_repo()` が
production 定数を直接参照する本ファイルの構造上、共有 fixture 経由の過剰決定
(273〜274件) を伴う。単独理由の証拠はいずれも直接の等価 assert 1件に明確に帰属できる
ため、DW-M01 の要求 (「無効化時の赤理由が一つに絞れることをコードで確認する」) は
「直接証拠の特定」という形で満たしたと判断し、過剰決定分は登録から除外した。
この判定パターン (production 定数の直接参照による fixture cascade) は
`docs/dev-wave/mutation.md` の `DW-M01`/`DW-M03` へ一般化して追記する価値があると
考えるが、L2 予算が満杯のため段8では記録のみに留めユーザー裁定へ返す。
