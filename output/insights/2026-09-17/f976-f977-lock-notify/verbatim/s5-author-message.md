## 変更した file と差分の要約

変更は指定の 4 ファイルのみです。169 行追加、6 行削除。commit は作成していません。

- `tools/wave_land_window.py`: `rolled-back` kind と専用固定文を追加。
- `orchestrator/tests/test_wave_land_window.py`: 新規 20 case、既存 landed 負例へ 1 case 追加。
- `tools/check_docs.py`: 指定 literal 1 行を更新。
- `orchestrator/tests/test_check_docs.py`: fixture 1 行と byte 数 pin 1 箇所を更新。

## rolled-back kind の実装

変更前は `--kind` が `landed` のみで、`fold-failed` JSON は rc=3 でした。変更後は `rolled-back` に限り、文字列 status が `fold-failed`、after・tip が有効 SHA、after ≠ tip の場合に rc=0、それ以外の結果は rc=3 です。

`message(wave, land_json, *, kind="landed")` とし、parser と `main` を接続しました。`main_before`・`reason` は参照しません。

既存 `landed` 分岐、`_ADVISORY`、loader、サイズ上限、holder 生成は不変です。専用固定文は指定どおり 2 行で、stdout は末尾 LF 込み **661 bytes** です。

## test の実装

- 通常・recovery の正例 2 件：独立 literal による全文一致、digest、rc、stderr を検査。
- 条件を一つずつ外す負例 15 件：status、after、tip の型・長さ・文字種・欠落・同値。
- 重複 JSON key 拒否 1 件。
- 有効 JSON に末尾空白を加えた 65,536／65,537 bytes 境界 2 件。
- 既存 landed 負例へ `fold-rollback-failed` を追加。既存 `fold-failed` 負例も保持。

既存テストの削除・skip・xfail・期待値変更はありません。

## pin の更新

checker と合成 fixture を次の文へ揃えました。

```text
   land 成功時と巻戻し時に `message` を照合済み peer へ 1 度送る。
```

現物の **9,519 bytes** を確認し、pin を `9_519` へ更新しました。上限 `9_520`、超過例 `9_521` は不変です。指定範囲の旧文言と、対象 2 ファイルの `9_507` は検索で残存なしでした。

## 実走結果 (nodeid と結果、未実走の列挙)

指定の `PYTHONPATH=. python3 -c "...pytest.main(...)"` 形式で実走しました。

**message 焦点：38 passed、78 deselected、rc=0。** 変異復元後にも再走して同結果でした。以下はすべて `orchestrator/tests/test_wave_land_window.py::` 配下です。

| node 名（全 parameter） | passed |
|---|---:|
| `test_landed_message_rejects_non_success_or_non_string_status_with_rc3` | 8 |
| `test_landed_message_success_is_exact_fixed_text` | 2 |
| `test_landed_message_rejects_invalid_main_after` | 1 |
| `test_landed_message_main_after_sha_exact_boundary` | 5 |
| `test_landed_message_rejects_duplicate_json_key` | 1 |
| `test_landed_message_rejects_more_than_65536_bytes` | 1 |
| `test_rolled_back_message_success_is_exact_fixed_text` | 2 |
| `test_rolled_back_message_rejects_invalid_result` | 15 |
| `test_rolled_back_message_rejects_duplicate_json_key` | 1 |
| `test_rolled_back_message_size_limit_is_exact` | 2 |

**docs 焦点：7 passed、570 deselected、rc=0。** 以下は `orchestrator/tests/test_check_docs.py::` 配下です。

- `test_synthetic_repo_baseline_clean`
- `test_dev_wave_command_budget_literal_is_exact`
- `test_next_tasks_command_budget_literal_is_exact`
- `test_dev_wave_waiter_consumer_pins_accept_current_docs_contract`
- `test_command_docs_guard_positive_controls[stage9-deleted]`
- `test_command_docs_guard_positive_controls[stage9_land_operation_deleted]`
- `test_command_docs_guard_positive_controls[codex_skill_stage9_land_literal_deleted]`

`python3 tools/check_docs.py` は **rc=0、違反なし**。`git diff --check` も通過しました。

初回は追加した byte 数 assertion の誤記（662）が正例 2 件を赤にしました。全文一致は通過しており、末尾 LF 込み 661 に訂正後、再走で通過しました。

未実走：上記焦点外のテスト、所有外 consumer テスト、全体受入、`check_codex_agents.py`、provenance 監査。

## 変異 M7〜M11 の anchor と killer node

anchor はすべて `tools/wave_land_window.py` の `old` 候補です。killer はすべて `orchestrator/tests/test_wave_land_window.py::` 配下で、各変異を単独適用し **1 failed、rc=1** を確認しました。

| ID | 行・anchor | killer node |
|---|---|---|
| M7 | 627: `if main_after == wave_tip:` | `test_rolled_back_message_rejects_invalid_result[tip-equals-main]` |
| M8 | 619: `status_value != "fold-failed"` | `test_rolled_back_message_rejects_invalid_result[rollback-incomplete]` |
| M9 | 625: `if not _is_sha(wave_tip):` | `test_rolled_back_message_rejects_invalid_result[tip-invalid]` |
| M10 | 46: `この land 結果では main` | `test_rolled_back_message_success_is_exact_fixed_text[normal]` |
| M11 | 36: `_SUCCESS_STATUSES = frozenset({"landed", "already-landed"})` | `test_landed_message_rejects_non_success_or_non_string_status_with_rc3[fold-rollback-failed]` |

M7・M9 は条件を無効化、M8・M11 は `fold-rollback-failed` を許容、M10 は `main` の先頭を `M` へ変更しました。

追加で上限を 65,537 に緩める変異も、`test_rolled_back_message_size_limit_is_exact[65537-3]` が検出しました。全変異は復元済みです。

## 波及可能性の静的列挙

- `tools/dev_wave_land.py:44`: helper を import。既存 renew／release と rollback 契約は変更なし。
- `tools/dev_wave_wait.py:2871`: helper の CLI 呼出し。既存 lease 操作への退行は所有外テストで確認対象。
- `orchestrator/tests/test_dev_wave_land.py:9144`: `message(wave, path)` の直接呼出し。default `kind="landed"` により互換性を保持。
- `orchestrator/tests/test_dev_wave_wait.py`: helper の直接 import、コピー、CLI 実行があり、統合検査対象。
- `orchestrator/tests/test_resume_gate_acceptance_boundary.py:285`: helper を fixture repo へコピーする consumer。
- `test_check_docs.py` の `_build_min_repo` 使用群：更新 fixture が伝播。baseline・stage9 関連は実走済み、残りは未実走。

## 未完・懸念

担当実装と指定焦点検査に未完はありません。所有外 consumer と全体受入の確認は親へ引き継ぎます。

docs、`output/**`、所有外コードは編集していません。禁止された git 操作も実行していません。

## 総括

plan v2 の (2) を実装し、焦点テスト **45 件**、docs checker、M7〜M11 の赤化確認を完了しました。差分は指定 4 ファイルに残してあり、親による統合・commit 待ちです。
