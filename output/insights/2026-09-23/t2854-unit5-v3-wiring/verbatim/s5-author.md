## 変更前の受理・拒否挙動

`_run_trace` は名前が `ycsb_` で始まる binary だけを受理し、TPC-C を含むその他は trace 実行前に拒否していました。CLI JSON、pipeline の拒否診断、capability digest は旧 `result_to_dict` 射影を使い、v3 の表・取引種別・存在詳細を出力していませんでした。

## 変更内容 (file ごと、追加削除行数)

| file | 追加 / 削除 | 内容 |
|---|---:|---|
| [core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/verifier/core.py:284) | 1 / 1 | capability digest を v3 射影へ変更。既存の 3 種の `pop` は維持し、存在詳細は残した |
| [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/verifier/cli.py:90) | 3 / 3 | `--json` を v3 射影へ変更 |
| [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/campaign/pipeline.py:434) | 19 / 5 | `ycsb_` と、4 flag が文字列で `43/0/0/0` に一致する `tpcc_` を受理。TPC-C の verifier 結果に v3 を要求し、拒否診断を v3 射影へ変更 |
| [test_verifier.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/tests/test_verifier.py:4040) | 123 / 0 | 下記 3 試験 |
| [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u5/orchestrator/tests/test_campaign.py:7481) | 97 / 0 | 下記 2 試験 |

変更は指定された 5 ファイルのみです。production の追加削除は計 32 行、試験は 220 行、新規 test 関数は 5 本で、いずれも上限内です。

## 試験 (関数名と中身、実走結果)

- `test_v3_cli_json_wiring_and_v2_bytes`：v3 cycle の表・取引種別、存在違反の件数・詳細、v2 の旧 JSON bytes 一致。
- `test_v3_capability_digest_binds_anomaly_and_existence`：v3 の表・取引種別・存在詳細を digest に束縛し、v2 の旧射影 digest と照合。
- `test_v3_district_lost_update_and_serial_control`：District 表 1 の lost update に ww・rw と cycle が出ること、および直列対照の認定。
- `test_tpcc_stage1_run_trace_allowlist`：実 `_run_trace` と fake executable で 57:43、payment=44、delivery 欠落、`"043"`、既存 `ycsb_`、その他の拒否を確認。
- `test_tpcc_executor_v3_v2_existence_and_witness`：実 verifier で v3 正例、v2 拒否、存在違反診断、完全な末尾 frame・最大 txid・thread file の欠落を確認。末尾 frame の変異 control は framing・orphan・存在違反が 0 で、note が witness 不一致だけであることを検査。

**pytest は未実走で、緑とは報告しません。** `tools/run_tests.py` による追加試験および meta-test の実行は、`qstat -Q` 事前確認の失敗で子試験が起動せず `rc=16` でした。直接の pytest は Pegasus ログインノードの PreToolUse hook が拒否しました。`py_compile` と `git diff --check` は通過しています。

## 波及の静的列挙

CLI の利用入口は `verify.py` と `verifier.__main__`、pipeline 診断の consumer は `critic/digest.py`、capability digest の consumer は `verifier/commit_receipt.py` です。共有 fixture の `campaign.lock` は `verifier/__init__.py` の hash に依存するため、同ファイルは編集していません。関連 consumer test は `test_t1286_commit_receipt.py`、既存の `test_verifier.py`・`test_campaign.py` です。

新規 test の収集・件数に関係する `conftest.py` の収集 hook、`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`、`test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed` を確認しました。後二者の実走は上記 dispatch 障害で未完了です。YCSB 専用の `silo_ladder_rung1.py` と `reflux_result_evidence.py` の旧射影 caller、TPC-C binary の build・選択経路は今回の編集対象外です。

## 変異の照準表

| 変異 | production の位置 | 殺す試験 | 赤の帰属 |
|---|---|---|---|
| M1 | `cli.py:90` | `test_v3_cli_json_wiring_and_v2_bytes` | JSON の構造化項目 |
| M2 | `pipeline.py:670` | `test_tpcc_executor_v3_v2_existence_and_witness` | 存在詳細の診断 assertion |
| M3 | `core.py:284` | `test_v3_capability_digest_binds_anomaly_and_existence` | v3 digest |
| M4 | `core.py:284–287` | 同上 | 存在詳細を含む digest |
| M5 | `pipeline.py:437` | `test_tpcc_stage1_run_trace_allowlist` | payment=44 の受理集合 |
| M6 | `pipeline.py:439` | 同上 | delivery 欠落の受理集合 |
| M7 | `pipeline.py:437–440` | 同上 | `"043"` の文字列比較 |
| M8 | `pipeline.py:639–645` | `test_tpcc_executor_v3_v2_existence_and_witness` | v2 trace の拒否理由 |
| M9 | `pipeline.py:442` | 既存 `test_run_trace_parses_commit_witness_from_stdout` | `ycsb_` の受理 |
| M10 | `pipeline.py:435–443` | `test_tpcc_stage1_run_trace_allowlist` | 57:43 の受理。executor の seam は検出に数えない |
| M11 | verifier の reason 表射影 `core.py:215` | `test_v3_district_lost_update_and_serial_control` | 表 1 の assertion。ただし既存 v3 試験も赤になり得るため、単一理由性は成立せず登録から外す対象 |

M5〜M7・M9・M10 は fake executable を使う実 `_run_trace` で受理集合を直接検査します。M8 の v2 入力は verifier 自体では認定可能な形にしてあり、追加した v3 要求へ帰属します。M11 を除き、表中の assertion は対象の射影または条件を直接照合します。

## 裁定からの逸脱と理由

実装内容・規模上限からの逸脱はありません。実走だけはキュー事前確認の障害とログインノードの hook 拒否で完了できませんでした。現 pin の TPC-C producer が v3 emitter・計数修正済みであることや、production `evaluate` が TPC-C binary を build・選択することは、この差分では証明していません。

## 総括

指定 5 ファイルに v3 射影と TPC-C 段 1 の受理条件を実装しました。
`ycsb_` の既存受理と、条件外 binary の拒否は維持しています。
TPC-C は 4 flag、v3、既存 verifier の正しさ条件を満たす場合にだけ認定へ進みます。
v2 の JSON bytes・digest を守る試験と、v3 の構造化出力を束縛する試験を追加しました。
構文検査と差分検査は通過しました。
pytest と meta-test は dispatch 障害により未実走です。