## 変更内容

| file | 差分行数 | 内容 |
|---|---:|---|
| [core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/core.py) | +94 / −73 | D5 の関数名を修正。到達可能性、D1、D2 を分割し、2 回目以降の外部読みと Q の thid 不一致を扱うよう変更 |
| [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/tests/test_verifier_gate_witness.py) | +49 / −1 | U1 と同じ emitter 名の source、D2a・B5・Q thid・CLI 欠落と読取不能のテストを追加 |

他の所有ファイルは変更していません。

## 裁定 1 の各行への対応

1. D5 の関数名と正例 source：`core.py:39`、テストファイルの `_source` と `test_gate_real_u1_emitter_names_d5_pass`
2. 2 回目以降の D2a：`core.py` の `_gate_d2`、`test_gate_second_external_read_wrong_stamp`
3. V と W、thread 集合の明示検査：`core.py` の `_gate_require_v_matches_w` と `_gate_reachability`。**位置付き notes を含む完了確認は未了**
4. Q の thid 不一致：`core.py` の D1(c) 分岐、`test_gate_q_thread_mismatch_is_d1c`
5. B5 型：`test_gate_b5_later_reader_disagrees_with_stored_stamp`
6. CLI rc：`test_gate_required_partial_thread_cli_rc`、`test_gate_required_unreadable_cli_rc`
7. 関数分割：`core.py` の `_gate_reachability`、`_gate_d1`、`_gate_d2`
8. 変異位置表：**未完成**

## 変異 M1〜M15 の位置と対応 test

停止時点で file:line と単一理由性を確定できていません。変異の実走もしていません。対応 test の割当は次のとおりです。

| 変異 | 対応 test | 外す式の位置 |
|---|---|---|
| M1 | `test_gate_b2_unregistered_write_m1` | 未確定 |
| M2 | `test_gate_b1_missing_initial_read_m2_m15` | 未確定 |
| M3 | `test_gate_trace_read_without_q_key_m3` | 未確定 |
| M4 | `test_gate_q_frame_m4` | 未確定 |
| M5 | `test_gate_b4_wrong_version_payload_m5` | 未確定 |
| M6 | `test_gate_genesis_wrong_payload_m6` | 未確定 |
| M7 | `test_gate_b6_stale_own_read_m7` | 未確定 |
| M8 | `test_gate_last_write_wins_m8` | 未確定 |
| M9 | `test_gate_v_missing_m9` | 未確定 |
| M10 | `test_gate_missing_thread_m10` | 未確定 |
| M11 | `test_gate_required_absent_m11_cli_rc` | 未確定 |
| M12 | `test_gate_b7_emitter_missing_m12` | 未確定 |
| M13 | `test_gate_invalid_filename_m13` | 未確定 |
| M14 | `test_gate_legacy_parse_m14` | 未確定 |
| M15 | `test_gate_b1_missing_initial_read_m2_m15` | 未確定 |

## 自己確認

`python3 -m py_compile`（production 5 file と対象 test file）と `git diff --check` は rc=0 でした。pytest は起動していません。

pytest を使わない自前の 5 ケース確認は **rc=1** で最初のケースで停止しました。D5 は `pass`、gate 到達不能と D1/D2 違反は 0 でしたが、CLI rc の期待 0 に対して実際は 3 でした。確認用の最小 source では `proof_surfaces` がすべて `evidence-absent` と判定されています。これ以上のケースは実走していません。指示に従い、この失敗時点で作業を止めました。

## 所有外への波及

所有外の caller として `campaign/pipeline.py`、`t2851_transfer_runner.py`、`silo_ladder_rung1.py`、`reflux_result_evidence.py`、`p3_s4_loop_policy.py`、共有 fixture と既存 consumer test に静的な波及があります。いずれも編集していません。閉包系 test を含む既存 test は未実走です。

## 総括

修正は作業ツリーに残っていますが、裁定 1 の受入確認と M1〜M15 の位置・単一理由性の記録は未完了です。自前確認の rc=1 を解消していないため、合格とは報告しません。