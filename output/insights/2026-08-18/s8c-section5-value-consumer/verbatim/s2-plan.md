# プラン

前提: 行番号は現 checkout のもの。pytest、`run_tests.py`、Web 検索は実行していない。以下は静的検査に基づく段 2 案である。

## 1. 編集アンカー

- `orchestrator/campaign/s8c_preregistration.py:19-33`
  - `math` と必要な型だけを追加する。
- `orchestrator/campaign/s8c_preregistration.py:117`
  - 対象欄名、root key 集合、block key 集合、`_SECTION5_VALUE_VALIDATORS` の exact table を追加する。
- `orchestrator/campaign/s8c_preregistration.py:759`
  - `_parse_section5` から欄名を渡す。
  - 現在の `status, reason = _classify_section5_value(cells[1])` を、`field_name=name` 付きに変える。
  - 対象欄名が table から消えた場合は `section5-validator-field-missing` で fail-closed にする。
- `orchestrator/campaign/s8c_preregistration.py:806`
  - signature を `def _classify_section5_value(raw_value: str, *, field_name: str)` に変更する。
  - placeholder、非 code span、JSON、canonical 比較、`null`、空文字、空 container の既存順序は維持する。
  - 対象欄の canonical かつ非空 container だけを validator table へ渡す。
- `orchestrator/campaign/s8c_preregistration.py:806-835`
  - exact object schema、型、有限性、符号、`unit`、`direction` を検査し、違反時は `INVALID` と固有 reason code を返す。
- `orchestrator/campaign/s8c_preregistration.py:134-138`
  - `FieldStatus` は変更しない。
- `orchestrator/campaign/s8c_preregistration.py:231-245`
  - `ActivationReport` は変更しない。既存の `section5_findings` と `effective` が新 reason/status を運ぶ。
- `orchestrator/campaign/s8c_preregistration.py:1727-1758`
  - `all_filled` と conjunction は変更しない。ここが `INVALID` を `effective=False` へ伝播させる既存 consumer である。
- `orchestrator/tests/test_s8c_preregistration_core.py:53-68`
  - `_markdown(filled=True)` の対象欄だけを canonical な正例へ差し替える。他の 8 欄は従来の `` `{"v":1}` `` を維持する。
- `orchestrator/tests/test_s8c_preregistration_core.py:1221` 付近
  - §5 の正例・負例・reason code・production entrypoint テストを追加する。
- `orchestrator/tests/test_s8c_preregistration_core.py:109-116`
  - `_init_repo` の構造は変更しない。
- `orchestrator/tests/test_s8c_preregistration_invariant.py:31-41`
  - 新規 test file は作らないため `WAVE_REQUIRED_PATHS` は変更不要。validator key の meta-test は既存 core test file に置く。

signature 変更時の直接呼び出しは静的検索で次のとおり。

- production の直接 call は `orchestrator/campaign/s8c_preregistration.py:799` の 1 箇所だけ。
- `_parse_section5` の直接 call は同 file `:894` の 1 箇所だけ。
- 既存テストから `_classify_section5_value` / `_parse_section5` を直接呼ぶ箇所は 0 件。
- 間接的な production 経路は `parse_preregistration_at:1035-1042`、履歴検証 `:1479`、`_activation_report_at:1661-1680`、`prepare_revision:1882-1885`、公開 `activation_report_at:1777-1782` である。
- `output/insights/...:115` は過去説明であり実行 callsite ではない。

## 2. 受理形と reason_code

P1 は採用する。root は exact 2 key `H1` / `H2`、各 block は exact 5 key とする。

P2 は概ね採用するが、巨大な整数の扱いが未規定である。

- `n`: `type(value) is int` かつ `>= 2`。`bool`、float、Decimal、int subclass は拒否。
- `delta_min`: exact built-in `int` または `float`、有限、正。
- `sd_max`: exact built-in `int` または `float`、有限、非負。
- `unit` / `direction`: exact `str`、`.strip()` 後が空でない。
- H1/H2 間の unit/direction 一致は要求しない。P2 が明示的に要求していない意味制約を追加しない。
- `{}`、`[]`、`null`、空文字列は既存規約どおり `UNFILLED` を維持する。対象欄でも、既存の空 container 分岐より後ろに validator を置く。非空の list、非空の dict、欠落 block は `INVALID`。

推奨する reason code は次のとおり。

- root: `section5-params-root-type`, `section5-params-root-keys`
- block: `section5-params-block-type`, `section5-params-block-keys`
- n: `section5-params-n-type`, `section5-params-n-range`
- delta: `section5-params-delta-min-type`, `section5-params-delta-min-nonfinite`, `section5-params-delta-min-range`, `section5-params-delta-min-negative-zero`
- sd: `section5-params-sd-max-type`, `section5-params-sd-max-nonfinite`, `section5-params-sd-max-range`, `section5-params-sd-max-negative-zero`
- 文字列: `section5-params-unit-type`, `section5-params-unit-empty`, `section5-params-direction-type`, `section5-params-direction-empty`
- 入れ子 code span: `section5-code-span-nesting`
- 対象欄消失: `section5-validator-field-missing`

既存の JSON 構文・canonical 失敗理由 (`invalid-json`, `noncanonical-json` など) は維持する。canonical 比較を schema 検査より先に置く。

正例は次の literal を使う。

`{"H1":{"delta_min":1,"direction":"on-minus-off","n":2,"sd_max":0,"unit":"ops_per_second"},"H2":{"delta_min":1,"direction":"on-minus-off","n":2,"sd_max":0,"unit":"ops_per_second"}}`

key 順は root、block とも昇順である。

巨大な int については択一が必要である。

- P2 の字面を守る案: exact int は数学的に有限なので、float 化せず比較し、巨大でも受理する。
- fail-closed を強める案: `float(value)` が `OverflowError` または非有限になる int を `section5-params-number-unrepresentable` で拒否する。

後者は P2 にない上限を追加するため、段 4 の裁定なしには採用しない。

## 3. 既存挙動を緩めない証明

現在の分岐順は次のままにする。

`placeholder / 非 code span / ambiguous span / invalid JSON / noncanonical / null / 空文字 / 空 container`  
→ 既存の `UNFILLED` または `INVALID`  
→ canonical かつ非空の値だけ対象 validator  
→ validator 成功時だけ `FILLED`

したがって、新 validator の後ろにある `FILLED` は、既に現行コードで `FILLED` になっている入力だけに到達する。現行 `UNFILLED` / `INVALID` を validator が `FILLED` に戻す分岐は作らない。

対象 validator が違反を返した場合は必ず `FieldStatus.INVALID` とする。`_activation_report_at:1727-1728` の `all_filled` は全 finding が `FILLED` であることを要求し、`:1753-1758` の conjunction が `effective=False` にする。

対象欄名が欠落して parser が `PreregistrationError` を出した場合も、`:1680-1682` が contract を捨て、空 findings により `effective=False` へ倒す。

## 4. fail-open 経路の棚卸し

- 欄名不一致  
  `_SECTION5_VALUE_VALIDATORS.get(name)` の未登録を成功扱いにしない。対象欄名が findings に現れなければ `section5-validator-field-missing` を送出する。現行 doc の欄名集合に table key があることを meta-test で固定する。

- root が dict でない  
  `type(value) is not dict` を使う。非空 list、数値、文字列、bool は `section5-params-root-type`。

- bool が int として通る  
  `type(n) is int` とし、`isinstance(n, int)` を使わない。`true` / `false` は `section5-params-n-type`。

- NaN / Infinity  
  `_strict_json` の `parse_constant` 拒否と `_canonical_bytes(... allow_nan=False)` を維持する。`NaN`、`Infinity`、`1e309` は `FILLED` へ到達させない。float 検査でも `math.isfinite` を必須にする。

- `-0.0`  
  `value == 0.0` だけでは不十分なので、`math.copysign(1.0, value) < 0` を明示する。`sd_max=-0.0` を `>= 0` だけで通さない。

- 非常に大きい int  
  `math.isfinite(huge_int)` や無防備な `float(huge_int)` は使わない。P2 の字面を採るなら exact int 分岐で比較し、float 化の例外が発生する実装を置かない。representable policy を採る場合は `OverflowError` / `ValueError` を捕捉して `INVALID` にする。

- Decimal 由来  
  `type(value) in (int, float)` または各 field の exact type 検査を使い、`numbers.Number` や広い `isinstance` を使わない。将来 parser が `parse_float=Decimal` になっても `INVALID`。

- code span の入れ子  
  現行の同一 delimiter 検査に加え、対象欄の code span content 内に backtick run が残っていれば `section5-code-span-nesting`。二重 delimiter 内の単一 delimiter を通さない。

- key 欠落・未知 key・欠落 block  
  `set(value) == {"H1","H2"}`、各 block も `set(block) == {"delta_min","direction","n","sd_max","unit"}` を exact に検査する。検査順を H1、H2、固定 field 順にして reason を決定論的にする。

## 5. 既存テストへの波及

意図した受理集合の縮小に伴う fixture 更新は `_markdown` の 1 箇所だけである。次の 16 箇所は `_init_repo(filled=True)` を通るため、helper の値更新の影響を受ける。

- `test_s8c_preregistration_core.py:1864` `_effective_fixture`
- `:2004` `test_matching_decider_version_preserves_activation_conjunction`
- `:2021` `test_mismatched_decider_version_is_not_effective`
- `:2039` `test_legacy_v1_tip_is_readable_but_not_effective`
- `:2061` `test_invalid_running_decider_version_cannot_activate`
- `:2082` `test_valid_hostile_str_subclass_cannot_fake_decider_version_match`
- `:2097` `test_activation_report_digest_binds_decider_and_projection_fields`
- `:2125` `test_every_non_satisfied_status_keeps_effective_false`
- `:2144` `test_effective_requires_all_twelve`
- `:2165` `test_activation_report_records_all_module_blob_hashes_at_commit`
- `:2192` `test_projection_blob_must_match_live_module`
- `:2214` `test_projection_file_read_failure_is_error`
- `:2236` `test_projection_import_failure_is_error`
- `:2269` `test_private_conjunction_helper_reads_commit_blob_not_dirty_worktree`
- `:2298` `test_non_json_cli_reports_decider_reason`
- `:2312` `test_effective_preregistration_cannot_be_constructed_or_dataclass_replaced`

これらの `effective is True`、`effective is False`、全 finding `FILLED`、predicate 状態、decider reason の期待値は触ってはいけない。正例を有効値へ更新すれば、元のテスト意図はそのまま成立する。

次も変更しない。

- `test_section5_placeholder_and_arbitrary_nonempty_are_not_filled:1221`
- `test_section5_json_semantic_empty_values_are_unfilled:1244`
- `test_current_evidence_contract_hash_is_frozen:1158`
- `test_existing_g1_record_pins_are_unchanged:1164`
- 現行 doc の 9 欄名、field hash、condition hash の期待値
- `WAVE_REQUIRED_PATHS:31-41` と machine contract の期待集合

`DECIDER_VERSION` を v4 にする strict 案を採る場合だけ、`:2016` の v3 期待値と最新 generation の期待値が変わる。これは fixture 更新ではなく scope 拡張である。

## 6. 新テストの一覧

すべて valid base literal から 1 軸だけ変え、status と reason code を同時に assert する。

- `test_section5_h1_h2_canonical_value_is_filled`
  - 正例の受理。validator を常時 reject する変異を殺す。
- `test_section5_invalid_value_reaches_production_parse_and_report`
  - `parse_preregistration_at` と `activation_report_at` から到達し、`INVALID` と `effective=False` を確認する。
- `test_section5_invalid_value_forces_non_effective_with_satisfied_predicates`
  - `_activation_report_at_for_test` で全 predicate を SATISFIED にしても invalid finding が発効を止めることを確認する。
- `test_section5_target_field_missing_is_fail_closed`
  - 対象欄名を 1 文字だけ変更し、`section5-validator-field-missing` を確認する。
- `test_section5_validator_key_matches_current_document_field_name`
  - validator table key が実 doc の `section5_field_names` に存在することを確認する。
- `test_section5_h1_h2_root_must_be_object`
  - 非空 list を root にする。root type 検査の欠落を殺す。
- `test_section5_h1_h2_requires_exact_top_level_keys`
  - `H2` 欠落だけを変える。key set 検査を殺す。
- `test_section5_h1_h2_block_must_be_object`
  - H1 block を非空 list にする。block type 検査を殺す。
- `test_section5_h1_h2_block_requires_exact_keys`
  - `unit` だけを欠落させる。block key set 検査を殺す。
- `test_section5_h1_h2_n_rejects_bool`
  - `n=2` から `n=true` だけを変更する。bool-as-int を殺す。
- `test_section5_h1_h2_n_requires_integer`
  - `n=2` から `n=2.0` だけを変更する。exact int 検査を殺す。
- `test_section5_h1_h2_n_requires_two_or_more`
  - `n=2` から `n=1` だけを変更する。下限検査を殺す。
- `test_section5_h1_h2_delta_min_requires_number`
  - `delta_min=1` から `"1"` だけを変更する。数値型検査を殺す。
- `test_section5_h1_h2_delta_min_rejects_nonfinite`
  - `delta_min=1` から `1e309` だけを変更する。非有限値の通過を殺す。
- `test_section5_h1_h2_delta_min_requires_positive`
  - `delta_min=1` から `0` だけを変更する。正値検査を殺す。
- `test_section5_h1_h2_delta_min_rejects_negative_zero`
  - `delta_min=1` から `-0.0` だけを変更する。符号 bit 無視を殺す。
- `test_section5_h1_h2_sd_max_requires_number`
  - `sd_max=0` から `"0"` だけを変更する。数値型検査を殺す。
- `test_section5_h1_h2_sd_max_rejects_nonfinite`
  - `sd_max=0` から `1e309` だけを変更する。非有限値の通過を殺す。
- `test_section5_h1_h2_sd_max_requires_nonnegative`
  - `sd_max=0` から `-1` だけを変更する。非負検査を殺す。
- `test_section5_h1_h2_sd_max_rejects_negative_zero`
  - `sd_max=0` から `-0.0` だけを変更する。`-0.0 >= 0` の穴を殺す。
- `test_section5_h1_h2_unit_requires_string`
  - `unit` を数値にする。文字列型検査を殺す。
- `test_section5_h1_h2_unit_rejects_blank`
  - `unit` を `"   "` にする。空白だけの通過を殺す。
- `test_section5_h1_h2_direction_requires_string`
  - `direction` を list にする。文字列型検査を殺す。
- `test_section5_h1_h2_direction_rejects_blank`
  - `direction` を `""` ではなく空白文字列にする。空白だけの通過を殺す。
- `test_section5_h1_h2_rejects_noncanonical_key_order`
  - 値は妥当なまま key 順だけを逆転し、`noncanonical-json` を確認する。
- `test_section5_h1_h2_rejects_nested_code_span`
  - 二重 code span 内へ単一 backtick を 1 個だけ入れる。
- `test_section5_h1_h2_rejects_decimal_derived_number`
  - validator helper に `Decimal("1")` を渡し、JSON number として受けないことを確認する。
- `test_section5_h1_h2_large_integer_conversion_failure_is_invalid`
  - strict 案でのみ追加する。`float` 化不能な巨大 int を `INVALID` に倒す。

`{}`、`[]`、`null`、空文字列の既存 `UNFILLED` は、今回の新しい負例にはしない。既存規約を変えないためである。

## 7. 変異候補

以下は実装後に段 4 で事前登録する候補であり、実走結果ではない。

- M1  
  old 逐語: `status, reason = _classify_section5_value(cells[1])`  
  期待赤: `test_section5_invalid_value_reaches_production_parse_and_report`

- M2  
  old 逐語: `return FieldStatus.FILLED, "canonical-json"`  
  期待赤: `test_section5_h1_h2_root_must_be_object`

- M3  
  old 逐語: `if not isinstance(n, int):`  
  期待赤: `test_section5_h1_h2_n_rejects_bool`

- M4  
  old 逐語: `if type(value) is not dict:`  
  期待赤: `test_section5_h1_h2_requires_exact_top_level_keys`

- M5  
  old 逐語: `if not math.isfinite(value):` を削除する  
  期待赤: `test_section5_h1_h2_delta_min_rejects_nonfinite`

- M6  
  old 逐語: `or (value == 0.0 and math.copysign(1.0, value) < 0)` を削除する  
  期待赤: `test_section5_h1_h2_sd_max_rejects_negative_zero`

- M7  
  old 逐語: `if "`" in content: return FieldStatus.INVALID, "section5-code-span-nesting"` を削除する  
  期待赤: `test_section5_h1_h2_rejects_nested_code_span`

- M8  
  old 逐語: 対象欄欠落時の `raise PreregistrationError("section5-validator-field-missing", ...)` を削除する  
  期待赤: `test_section5_target_field_missing_is_fail_closed`

- M9  
  old 逐語: `all_filled = bool(findings) and any(item.status is FieldStatus.FILLED for item in findings)`  
  期待赤: `test_section5_invalid_value_forces_non_effective_with_satisfied_predicates`

- M10  
  old 逐語: `_SECTION5_VALUE_VALIDATORS = {}`  
  期待赤: `test_section5_validator_key_matches_current_document_field_name`、`test_section5_invalid_value_reaches_production_parse_and_report`

## 8. scope 外の確認

docs の本文は既に、`docs/phase3-8c-preregistration.md:159-163`、`:231-239` と `docs/phase3-8c-preregistration.md:270-287` で今回の制約と validator 到達性を規定している。従って、本文、§5 の実値、evidence contract JSON、machine-checkable の反転は変更せずに実装できる。

ただし、別の停止候補がある。

- `docs/phase3-8c-preregistration.md:294-297` は、受理集合または拒否理由を変える判定器変更に `DECIDER_VERSION` bump と新 generation record を要求する。
- `orchestrator/campaign/s8c_preregistration.py:15` は `DECIDER_VERSION` が受理意味を代表すると定義し、現在は `:50` の `s8c-decider/v3`。
- 最新 `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g7.json` も v3 を束縛している。
- 今回は canonical JSON のうち `FILLED` として受理する集合を狭めるため、厳密には generation record を 1 byte も変えずに docs 契約を満たせない。

段 4 の択一は次のどちらかである。

1. 厳密遵守: v4 への bump と次世代 generation record を scope に追加する。
2. scope 維持: 今回は既存規範の実装欠落を埋めるだけであり、D458 の版 bump 対象外とするユーザー裁定を明示する。

2 を無裁定で選んで v3 のまま実装するのは停止候補であり、推奨しない。

## 総括

採るべき実装は、既存の空値・canonical・code span 判定の後段に対象欄専用の exact validator table を置く構成である。  
最大の危険は、受理集合を狭める変更と `DECIDER_VERSION` / generation record の凍結契約が衝突している点である。  
巨大 int の representability と H1/H2 の unit/direction 一致も、P2 の未規定部分として残る。  
親は段 4 で「v4 + generation record を許すか」「既存 v3 を維持する明示裁定を出すか」を先に決めるべきである。