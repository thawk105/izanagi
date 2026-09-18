## 対応表

J=`tools/pegasus/floor_pair_campaign.sh`、S=`tools/pegasus/submit_floor_pair.sh`、T=`orchestrator/tests/test_floor_pair_job_contract.py`。closed は実装・自走 harness での確認を指します。

| 所見 | 状態 | 変更箇所 |
|---|---|---|
| F1 | closed | T:31：exec 前の子で TERM/HUP/INT を SIG_DFL・UNBLOCK |
| F2 | closed | J:189：JOB_RC を DRIVER_RC に固定。T:395：signal 観測後 rc=0 の正例追加 |
| F3 | closed | J:39、S:29：3 prefix 全件 unset。T:79：消去・PBS_JOBID 保持・固定 PATH を観測 |
| F4 | closed | T:74：両 script の `bash -n` |
| F5 | closed | T:346：元 bytes に復元後、chmod 0600 |
| F6 | closed | J:209、S:257：main 化。T:228・270：順序／途中拒否。T:454：finalize HEAD 不一致。T:322・465：静的検査の限定を明記 |

F3 は既存の文字列期待値を維持するため、名指し unset も残しています。既存ケースの期待値の反転・緩和・削除はありません。

## 実走

| command | rc | 結果 |
|---|---:|---|
| `python3 orchestrator/tests/test_floor_pair_job_contract.py` | 0 | **22 passed / 0 failed、約1.95秒** |
| `python3 tools/run_tests.py orchestrator/tests/test_floor_pair_job_contract.py orchestrator/tests/test_hooks.py orchestrator/tests/test_plain_runner_coverage.py -q -rf --force-dispatch` | 16 | **未実走**。`qstat -Q preflight rc=1`、child 未起動 |
| `git diff --check` | 0 | 問題なし |

自走 harness の PASS 関数に対応する nodeid は、接頭辞 `orchestrator/tests/test_floor_pair_job_contract.py::` と以下の名前を結合した **22 件**です（pytest 自体は未実走）。

```text
test_checkout_and_input_binding
test_child_rc_collection
test_clean_environment
test_driver_argv
test_dry_run_has_no_execution
test_evidence_and_receipts
test_finalize_preflight_requires_terminal
test_frozen_spec_pins
test_gate_order_and_calls
test_hostname_gate
test_job_main_gate_order_and_calls
test_no_build_or_output_replacement
test_pbs_and_walltime_binding
test_registry_entries
test_scratch_name_normalizes_colon
test_scripts_parse
test_submitter_argument_set
test_submitter_head_consistency_preflight
test_submitter_main_gate_order_and_calls
test_walltime_values
test_window_gate_boundaries
test_window_id_and_fields
```

## 変異の exact old (fix 後)

以下は読取済みソースと検索結果による静的照合です。各対象ファイル内で一意です。追加の Python 一括 count 検査は hook 拒否で未実行です。

| ID | 対象・行 | fix 後の exact old |
|---|---|---|
| M0 | J:202 | `# Window admission is checked again after scratch preparation.` |
| M1 | registry:76 | 下記の2行 |
| M2 | S:102 | `SPEC_SHA256=990e3a6feb176ccf863315fde6e2afce43b7fc16053f50a1080641dde2570619` |
| M3 | J:54 | `now + duration <= not_after` |
| M4 | J:141 | `[[ "$label" =~ ^bnode[0-9]+$ ]]` に続く下記の拒否句を含む command 全体 |
| M5 | J:162 | `--execute-window "$FP_WINDOW_ID"` |
| M6 | runbook:516 | 下記の表行 |
| M7 | J:194 | `require_compute_hostname "$HOST_OBSERVED"` |
| M8 | S:226 | `if (( DRY_RUN )); then` |
| M9 | J:153 | `${PBS_JOBID//:/_}` |
| M10 | S:173 | `if header.get("loaded_head") != head: refuse("loaded_head_mismatch")` |

M1（単独の class 文字列では一意にならないため、entry 名を含める）:

```text
    "tools/pegasus/floor_pair_campaign.sh": {
      "class": "dispatch-required",
```

M4:

```bash
[[ "$label" =~ ^bnode[0-9]+$ ]] || fail 4 site compute_node_required
```

M6:

```text
| `tools/pegasus/floor_pair_campaign.sh` | `dispatch-required` | `static job-body classification` |
```

M7 は引き続き `admit_and_run()` 内、M8 は `submit_or_dry_run()` 内です。main 化で両者の文言・一意性は変わらず、既存の抽出実行 test も維持されています。変異投入・殺傷観測は今回行っていません。

## 総括

F1〜F6 を所有する3ファイルに実装し、自走 harness は22件すべて通過しました。  
計算ノードでの3ファイル検査は dispatch 障害により未実走で、再実行が必要です。  
commit は作成していません。実 driver・実 job/submitter 全体の実行もありません。

追加の exact old 一括照合は、PreToolUse `guard_bash` が対象を dispatch-required 実行体と判定して実行前に拒否しました。迂回せず、上表は静的照合結果として報告しています。