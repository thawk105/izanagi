## 実装した物

- `tools/plotting/plot_a2_certification.py`: study exact 2件、A-6 pin、`6 × N` 閉包、request／時刻の一意検査、`2 × N` axes、A-6 caption・注記・caption_source 束縛を実装しました。A-6 は2段1列、figsize `(8.0, 7.6)` です。
- `orchestrator/tests/test_plot_a2_certification.py`: 許可された exact pin を拡張し、A-6 実寸 fixture、正常系・拒否系・実データ・着地検査を追加しました。既存の期待値と self-run harness は維持しています。
- `load_measurements` に study、current-full provenance に study を追加しました。legacy provenance のキー集合は既存契約を維持しています。
- A-2 の caption／artist は fig5・6・7 の landed closure で互換性を確認しました。

## 実走した検査

| 対象 | 結果 |
|---|---|
| `test_plot_a2_certification.py` 全111 node | **110 passed / 1 failed / 0 skipped** |
| `test_plain_runner_coverage.py` 全3 node | **3 passed / 0 failed / 0 skipped** |
| 下記の収集契約3 node（直接呼出し） | **DIRECT_CALL_PASS × 3** |
| 編集2ファイルの `py_compile`、`git diff --check` | rc=0 |

直接呼出しした nodeid は `orchestrator/tests/test_pytest_collection_config.py::` に続く以下です。

- `test_repo_pytest_ini_has_no_addopts_and_pins_testpaths`
- `test_permanent_exclusion_table_has_no_other_verifier_or_oracle_tests`
- `test_ini_testpaths_and_runner_default_target_point_at_the_same_tree`

A-6 実データ CLI は **rc=0**。成果物は次の3件です。

- `probe-fig11/fig11_a6_certification_reject.png`
- `probe-fig11/fig11_a6_certification_reject.pdf`
- `probe-fig11/fig11_a6_certification_reject.provenance.json`

provenance と稿の照合結果：

| 項目 | 一致した値 |
|---|---|
| median（stock / adopted） | `10088796` / `9505248` |
| effect rr95 | `-0.057841193339621455` |
| abort率（stock / adopted） | `0.1547` / `0.145` |
| correctness | 両cell certified、legacy 1回・performance条件5回、pass |
| caption_source SHA-256 | `34a968428f867ce26479abe37320946b6eb8149007244dfe1d18a18446633850` |

caption は指定の固定文5件と限定を含み、禁止語を含みません。fig5・6・7 および scratch fig11 の `validate_repo_closure` はすべて通過しました。A-2 実 root の median `[2438295, 3987794, 3756230, 4297929]` も certification と一致しました。

## 未実走・期待赤

唯一の失敗は
`orchestrator/tests/test_plot_a2_certification.py::test_landed_fig11_repo_closure_and_caption_when_present`
です。**未着地のため赤**であり、skip／xfail 化していません。

正式な変異 harness、親の受入検査は未実走です。編集用の複合 Python コマンド1件は guard の解析で拒否され、編集は `apply_patch` で完了しました。検査コマンドの拒否はありません。

## 受理・拒否の含意

改修前の A-6 入力は repository-owned pin 表に無いため拒否されていました。

改修後は A-2／A-6 の current-full と既存 A-2 legacy を受理し、第3 study、A-6 legacy、workload 0件、hash・閉包・一意性の不整合を拒否します。

正例として、実 attempt `a6-20260908b` が検証・作図・3成果物の出力まで通過しました。

## 所有外への波及

所有外の編集はありません。最終 status は指定2ファイルの変更と untracked `probe-fig11/` のみです。

Python caller／共有 fixture／consumer の参照検索では所有外の直接依存は見つかりませんでした。self-run coverage と収集契約を確認済みです。既存図の consumer は landed closure で確認しました。親による fig11 bundle と README の着地が必要です。

## 変異事前登録への対応

以下は対応する検出 node です。正式な変異走の結果ではありません。接頭辞はすべて `orchestrator/tests/test_plot_a2_certification.py::` です。

| id | 対応test |
|---|---|
| m0 | docstring の等価変異。SURVIVED想定、対象nodeなし |
| m1 | `test_a6_pin_drift_is_rejected`、既存 `test_m11_whitespace_changed_certification_fails_cli_with_zero_outputs` |
| m2 | `test_a6_fixture_loads_as_current_full_with_six_file_closure`、`test_a6_rejects_six_file_closure_underflow_and_overflow` |
| m3 | `test_a6_provenance_tracks_caption_source_with_current_sha` |
| m4 | `test_layout_rejects_wrong_axes_count` |
| m5 | `test_a6_caption_contains_fixed_literals` |
| m6 | `test_unknown_study_is_rejected` |
| m7 | `test_current_rejects_duplicate_workload_requests[request_id]`／`[created_utc]` |
| m8 | `test_landed_fig11_rejects_all_missing_outputs` |
| m9 | `test_a2_current_full_caption_is_unchanged_for_landed_fig6` |

m6 は producer にも未知studyの拒否層があります。生成器の検査を除去しても別理由で拒否されるため、受理挙動としての単一理由性はありません。正式変異走では再照準が必要です。

## 総括

実装済み：生成器・テスト、A-6実データ3成果物、A-2互換確認。
検査結果：110 passed、未着地による期待赤1件、skipなし。
未実走：正式変異 harness・親の受入検査。
親への依頼：scratch退避、fig11とREADMEの着地、変異・受入検査、commit。