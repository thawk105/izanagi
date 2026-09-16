## 変更一覧

変更先は sandbox 内の `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2723-impl`。指定された親 worktree の対象 6 ファイルと変更前の一致を確認して実装した。

以下の略記を用いる。

- A: `orchestrator/campaign/p3_b4_admission_record.py`
- F: `orchestrator/campaign/p3_b4_floor_artifact_issuer.py`
- R: `orchestrator/campaign/p3_b4_material_report.py`
- AT / FT / RT: 各 module に対応する `orchestrator/tests/test_*.py`

| file:line | 変更 |
|---|---|
| A:27 | 完全 admission 検査と floor 読取の共有範囲を docstring に明記 |
| A:604 | `_parse_section5_fixed_table_source_cells` を抽出。normalized 値・strip 済み raw 値・strip 前 label を返す |
| A:663 | `_assert_section5_source_cell_has_nonempty_value_and_no_reserved_sentinel` を抽出 |
| A:688 | 既存 admission 関数から両 helper を呼ぶ |
| F:74 | 共有 helper と例外型を import |
| F:1476 | `_floor_cell` を共有 parser・exact label・責任者述語へ接続 |
| F:1506 | resolver の docstring 更新、strip 後 raw sentinel 比較 |
| R:5 | module docstring のみ更新 |
| AT:1173 | raw / normalized を区別する test 1 関数追加 |
| FT:188 | `_preregistration` を完全表 builder の wrapper に変更 |
| FT:680、737、783 | 指定された既存 test 3 件を更新 |
| FT:799 | 新規 test 用補助関数 |
| FT:826 | 新規 test 12 関数・14 node を追加 |
| RT:137、1001、1110 | fixture 書込み 3 箇所を wrapper 経由に変更 |

`main()`、loader、material report の実装コード、禁止対象ファイルは変更していない。`git add`・commit は未実施。

## 実走結果

指定コマンドで各ファイルの全テストを実走した。

| 対象・範囲 | passed | failed |
|---|---:|---:|
| FT 全 node（自走 `_run`） | 93 | 0 |
| AT 全 test 関数（自走 `__main__`） | 30 | 0 |
| RT 全 node（指定の `pytest.main` 呼出し） | 50 | 0 |
| **合計** | **173** | **0** |

FT 初回は 92 passed / 1 failed。後述の schema 負例修正後、全 93 node を再実走して成功した。RT は 275.57 秒で完了した。

追加分の実走 nodeid は以下。`FT::` / `AT::` は上記ファイルパスへの略記で、すべて passed。

```text
FT::test_resolver_real_preregistration_is_absent
FT::test_resolver_ignores_pin_outside_section5
FT::test_resolver_rejects_missing_floor_despite_outside_pin
FT::test_resolver_rejects_unrecorded_owner_before_loading_pin
FT::test_resolver_rejects_missing_owner_row
FT::test_resolver_ignores_blocked_section5_decoys[fence]
FT::test_resolver_ignores_blocked_section5_decoys[comment]
FT::test_preregistration_floor_label_matches_admission_label
FT::test_resolver_preserves_raw_floor_pin
FT::test_resolver_keeps_exact_floor_label[padded]
FT::test_resolver_keeps_exact_floor_label[fullwidth]
FT::test_resolver_rejects_unknown_label_at_fixed_row_count
FT::test_resolver_preserves_encoding_error
FT::test_resolver_rejects_nfkc_only_absent_sentinel
AT::test_section5_parser_preserves_raw_and_normalized_values
```

既存の重要 node も実走済み。

```text
FT::test_resolver_exact_sentinel_is_the_only_absence
FT::test_resolver_rejects_duplicate_floor_rows
FT::test_m05_m06_resolver_fails_closed_without_absence_fallback[missing]
FT::test_m05_m06_resolver_fails_closed_without_absence_fallback[hash]
FT::test_m05_m06_resolver_fails_closed_without_absence_fallback[schema]
FT::test_aggregate_public_issue_load_and_preregistration_pin
AT::test_section5_expectation_row_rejects_nfkc_only_ascii_grammar_matches
RT::test_m8_absent_authority_public_bytes_match_pre_change_golden
RT::test_aggregate_authoritative_floor_reaches_public_material_report
RT::test_present_floor_projects_required_verbatim_non_guarantees
RT::test_m7_non_sentinel_resolver_failure_never_falls_back_or_calls_evaluator
RT::test_cli_clean_subprocess_runs_twice_and_refuses_overwrite
```

FT:1679 の `_run` は pytest で全 node を収集するため変更不要だった。`git diff --check` も成功。

変異 probe、本体以外の consumer 回帰、親の `tools/run_tests.py` 統合走は未実走。

## 期待値変更

既存 test の期待値変更は裁定の次の 3 件に限定した。

1. FT:680：padded sentinel 2 例を None 期待へ変更。`TBD` / `artifact_path=x` は grammar error のまま。
2. FT:783：完全表の別 label を floor label に置換して重複を作り、`preregistration_floor_row_error` を検証。
3. FT:737：m05/m06 の code を `missing → path_error`、`hash → artifact_hash_mismatch`、`schema → artifact_schema_error` に固定。

**実走で判明した fixture 補正:** schema 負例の従来値 `p3-b4-authoritative-floor/v2` は現行 aggregate schema として有効であり、aggregate の形状検査で `schema_error` になった。FT:759 の入力を未対応の `v999` に変更し、指定どおり `artifact_schema_error` を検証した。期待値の緩和や loader の変更はしていない。

AT・RT の既存期待値、固定 golden、揮発 hash の期待値は変更していない。

## 波及可能性

`grep -rn --include='*.py'` と `rg` による静的確認結果。

| 起点 | caller・consumer |
|---|---|
| `_floor_cell` | F:1523 の resolver のみ |
| resolver | R:216、RT:1006・1062、FT:688・695・701・727・772・791・810・829・1506 |
| `PREREGISTRATION_FLOOR_LABEL` | F 内の exact 比較・raw 値取得、FT の wrapper・文書加工・独立 literal pin |
| admission 完全検査関数 | A:822 の verifier、AT の既存直接検査群 |
| `_section5_document` の外部 import | FT:189 の wrapper のみ |
| `_preregistration` の外部 import | RT:137・1001・1110 |
| `_write_floor_preregistration` | RT:864 の m9 四状態、RT:1061 の non-guarantees 正例 |

間接波及として、closed critic（`:56・104・646`）、launcher（`:28`）、raw record producer（`:995`）が admission またはその bytes に依存する。admission の変更で projection closure hash が変わる。

関連 consumer test は `test_p3_b4_closed_critic.py`、`test_p3_b4_launcher.py`、`test_p3_b4_raw_record_producer.py`、`test_ccbench_spawn_sites.py:173`。これらは今回未実走で、親の統合検証対象となる。

## 受理集合の自己申告

実装による変化は裁定 §3 の列挙内に収まると判断する。

- 拒否→受理：floor 値セルの外周空白除去、真正 §5 外の同 prefix 行の無視。
- 受理→拒否：共有 parser の全条件、floor label の strip 前 exact 一致、既存責任者述語、セル中の ASCII `|`。
- 不変：sentinel は strip 後 raw の `未記入` のみ。pin grammar と loader 引数も raw。他欄の sentinel と expectation 宣言は floor 経路では検査しない。

admission parser は追加した label 保存を除いて元の処理と文字列一致を確認した。expectation 検査部分も一致し、述語は `continue → return` の抽出のみ。例外 message・`from exc`・検査順を維持した。

F423 型の見出し decoy と、他欄未記入でも有効 pin が present になる既存仕様は残る。完全 admission の成立は主張しない。

## 変異 matrix の対象行と予想 killer

以下は予想。失敗集合の完全一致は親の probe で確定する。

| ID | 対象 file:line | 予想 killer node |
|---|---|---|
| M0 | A:27 docstring | 等価対照、SURVIVED 予想 |
| M1 | F:1476 `_floor_cell` | FT::test_resolver_ignores_pin_outside_section5、missing-floor / missing-owner / unknown-label、decoy 両 node |
| M2 | F:1496 責任者述語呼出し | FT::test_resolver_rejects_unrecorded_owner_before_loading_pin |
| M3 | A:658 label 集合一致 | FT::test_resolver_rejects_unknown_label_at_fixed_row_count |
| M4 | A:650 `cell.strip()` | FT::test_resolver_exact_sentinel_is_the_only_absence、FT::test_resolver_preserves_raw_floor_pin |
| M5 | A:656 raw 値保存 | AT::test_section5_parser_preserves_raw_and_normalized_values、AT::test_section5_expectation_row_rejects_nfkc_only_ascii_grammar_matches、FT::test_resolver_preserves_raw_floor_pin |
| M6 | A:619・626・632 fence 除外 | FT::test_resolver_ignores_blocked_section5_decoys[fence] |
| M7 | A:620・627・633 comment 除外 | FT::test_resolver_ignores_blocked_section5_decoys[comment] |
| M8 | F:1526 raw pin fullmatch／後続 path 取得 | FT::test_resolver_preserves_raw_floor_pin |
| M9 | F:1489 strip 前 label 比較 | FT::test_resolver_keeps_exact_floor_label[padded]、同 `[fullwidth]` |
| M10 | F:1524 sentinel 比較 | FT::test_resolver_rejects_nfkc_only_absent_sentinel |
| M11 | F:1494 責任者だけを選ぶ箇所 | FT::test_resolver_real_preregistration_is_absent、RT の実文書使用正例 |

M6 / M7 は既存 admission の fence / comment test も killer になりうるため、専属性を主張しない。

## 総括

§5 固定表解析と責任者述語への接続を実装し、指定 3 ファイルで **173 passed / 0 failed** を確認した。変更は指定 6 ファイルのみ。

親に残る作業は統合後の consumer・受入走、変異 probe と本走、docs 更新・commit。現段階では wave 全体の closed は主張しない。
