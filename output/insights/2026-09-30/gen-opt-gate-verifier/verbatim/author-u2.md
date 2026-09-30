## 変更前の受理・拒否の挙動

gate file のない trace は、既存の trace 健全性検査・巡回検出・X/P/I 証拠面で判定し、gate 記録は要求も照合もしません。既存の `result_to_dict` / `result_to_dict_v3` に `gate_witness` 節はありません。

## 変更内容 (file ごと、追加行数)

**実装は途中段階です。テスト本体を起動できなかったため、完了・合格とは扱えません。** 変更は未 commit の作業ツリーに残しています。

| file | 追加行数 | 内容 |
|---|---:|---|
| [parse.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/parse.py:51) | 72 | gate 名、Q/V、刻印の解析 |
| [model.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/model.py:443) | 22 | 意味版 2、計数、`clean()` |
| [core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/core.py:43) | 203 | compact 経路の照合、D5 |
| [report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/report.py:96) | 24 | gate 有効時の結果節 |
| [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/cli.py:38) | 5 | `--require-gate-witness` |
| [test_verifier_gate_witness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/tests/test_verifier_gate_witness.py:1) | 196 | 手製履歴のテスト案。**未実走** |

新しい fixture directory と inventory・ledger の更新は未実施です。

## 照合の実装 (関数名 file:line、擬似コードとの対応)

`_gate_paths` と `_gate_row` が名前・書式を読み、[`_check_gate`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/core.py:71) が compact 列と Q/V を照合します。producer 刻印と未解決の外部読みを保持し、D1・D2 の計数を到達可能性の確認後に反映する構成です。[`verify_trace_dir`](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2884-u2/orchestrator/verifier/core.py:219) が presence／要求で起動します。

D5 の照合対象名は `GATE_EMITTER_CALLS` の一か所に置き、既定値を `izanagi_trace::emit_steps(`、`izanagi_trace::emit_stored(`、`izanagi_trace::gate_note_commit(` としました。U1 最終形との突き合わせは未実施です。**既知の未解決点:** Q の thread 値不一致を現在は到達不能に分類しており、裁定の D1(c) 分類との確認・修正が必要です。

## test と変異の対応表 (M1〜M15 → test 名、自己確認の結果)

| 変異 | 対応するテスト案 |
|---|---|
| M1 | `test_gate_b2_unregistered_write_m1` |
| M2 | `test_gate_b1_missing_initial_read_m2_m15` |
| M3 | `test_gate_trace_read_without_q_key_m3` |
| M4 | `test_gate_q_frame_m4` |
| M5 | `test_gate_b4_wrong_version_payload_m5` |
| M6 | `test_gate_genesis_wrong_payload_m6` |
| M7 | `test_gate_b6_stale_own_read_m7` |
| M8 | `test_gate_last_write_wins_m8` |
| M9 | `test_gate_v_missing_m9` |
| M10 | `test_gate_missing_thread_m10` |
| M11 | `test_gate_required_absent_m11_cli_rc` |
| M12 | `test_gate_b7_emitter_missing_m12` |
| M13 | `test_gate_invalid_filename_m13` |
| M14 | `test_gate_legacy_parse_m14` |
| M15 | `test_gate_b1_missing_initial_read_m2_m15` |

**M1〜M15 の写しでの変異実走、kill 判定、単一理由性の自己確認はすべて未実施です。** 対応表はテスト名の割当であり、結果ではありません。

## 性能の測定

200k 取引の所要・peak RSS は未測定です。ログインノードで性能測定を直接起動していません。

## 実走した test (nodeid・範囲・rc)

**実走した pytest nodeid はありません。** `tools/run_tests.py orchestrator/tests/test_verifier_gate_witness.py -q`、`-n 1`、`--collect-only -q` はいずれも **rc=16、child 未起動**でした。ログインノードの予約台帳を安全に更新できず dispatch が選ばれ、`qstat -Q` preflight が rc=1 で失敗しました。

`py_compile`（変更した production 5 file と新 test file）および `git diff --check` は rc=0 でした。これらをテストの緑とは数えません。

## 所有外への波及と未実走

静的に見つかった投影 consumer は `campaign/pipeline.py`、`t2851_transfer_runner.py`、`silo_ladder_rung1.py`、`reflux_result_evidence.py`、`p3_s4_loop_policy.py` です。指定された既存 verifier test、D442 閉包 test、meta-test、`check_codex_agents.py`、`check_docs.py`、provenance 監査は未実走です。既存 fixture・test・所有外 production file は編集していません。

## 総括

**要求された U2 の受入条件は未達です。** テスト基盤が child を起動できない事実を確認した時点で、推測による合格判断と変異・性能測定を止めました。作業ツリーには実装途中の差分が残っています。