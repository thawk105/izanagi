# 段 5 実装報告 — [T-1328]

## 変更した file

| file | 変更行の要約 |
|---|---|
| [certify_calibration.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/tools/pegasus/certify_calibration.sh:907) | 候補全滅による停止を削除。selection・symlink は候補成功時のみ生成。最終 PATH で canonical probe を実行し、unavailable 時だけ receipt 引数を追加。 |
| [cli.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/calibrator/cli.py:162) | receipt 引数・保存・canonical 判定を追加。capability と calibrate に同じ判定値を伝播。host／notes に測定条件を記録。登録条件は変更なし。 |
| [sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/calibrator/sweep.py:170) | `use_perf=True` を追加。False のみ runner に伝播。sweep を保持し、no-perf は noise 遷移前に `saturation=None` で返す。 |
| [runner.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/calibrator/runner.py:1256) | counter 必須検査だけを `if use_perf:` 内へ移動。throughput・maxrss・rep 失敗処理は維持。 |
| [test_calibrator_certify.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/tests/test_calibrator_certify.py:379) | `_invoke` に任意の subprocess fixture を追加。実 CLI → sweep → measure_point → run_once の正負例を追加。 |
| [test_pegasus_calibration_workload.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/tests/test_pegasus_calibration_workload.py:633) | production shell の選択・probe・argv 生成を実行する 4 条件を追加。 |
| [test_official_perf_closure.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1328-impl/orchestrator/tests/test_official_perf_closure.py:44) | CLI・sweep を登録し、runner guard の期待条件を更新。 |

変更禁止の 7 file は差分なし。docs・既存テスト期待値の変更、commit・push は行っていません。

## 実走した nodeid と結果

**最終実走：289 件緑、所有外の既存テスト 4 件赤。**

実行方法は `PYTHONPATH=.` 付きの既存自走 harness、および既存テスト関数を呼ぶ自走 harness です。通常の `tools/run_tests.py` は qstat 事前確認で **rc=16・子未起動**。直接の `python3 -m pytest` は hook に拒否されました。

以下のパスはすべて `orchestrator/tests/` 起点です。`::*` は当該 file 全件を実走した範囲です。

| 緑の実走範囲 | 件数 |
|---|---:|
| `test_calibrator_certify.py::*` | 86 |
| `test_calibrator.py::*` | 69 |
| `test_holdout_observation.py::*` | 108 |
| `test_official_perf_closure.py::*` | 7 |
| `test_plain_runner_coverage.py::*` | 3 |

新規 nodeid はすべて緑です。

- `test_calibrator_certify.py::test_cli_no_perf_preserves_all_sweep_reps[20,50,80]`：各 parameter を実走。
- `test_calibrator_certify.py::test_cli_no_perf_fatal_stops_at_bad_rep[maxrss,throughput,rc]`：各 parameter を実走。
- `test_calibrator_certify.py::test_cli_perf_probe_error_stops_before_calibrate`
- `test_pegasus_calibration_workload.py::test_certify_perf_preflight_argv[unavailable,probe_error,selected,literal_available]`：各 parameter を実走。

追加で実走した緑の nodeid：

- `test_pegasus_calibration_workload.py::test_calibration_shell_scripts_parse`
- `test_pegasus_calibration_workload.py::test_calibrator_uses_smoke_checked_interpreter_selected_before_call`
- `test_pegasus_calibration_workload.py::test_default_silo_build_and_calibrate_argv_match_offline_contract`
- `test_pegasus_calibration_workload.py::test_certify_final_calibrate_binary_matches_built_binary[silo,mocc,tictoc]`
- `test_pegasus_tools.py::test_certify_calibrate_timeout_argv_cannot_self_match_ycsb_probe`
- `test_pegasus_tools.py::test_exec_calibrate_execs_valid_argv`
- `test_env_contract.py::test_v2_modules_have_no_env_literals_outside_registry`
- `test_env_contract.py::test_calibration_verify_is_in_v2_env_neutral_module_closure`
- `test_env_contract.py::test_legacy_calibration_allowlist_is_exact_and_closed`
- `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`：被覆 **22,988 / 24,040＝95.624%**。

**赤：`test_pegasus_tools.py` の次の 4 nodeid。変更せず残しています。**

| nodeid の関数名 | 原因 |
|---|---|
| `test_certify_perf_stage_is_policy_driven_fail_closed_and_precedes_calibrate` | 今回削除する候補全滅時の `write_failure` 行を要求する旧期待値。 |
| `test_perf_stage_all_candidates_failed_writes_perf_failure` | 抽出 fixture に `CALIBRATE_PYTHON` がなく、未定義変数で停止。 |
| `test_perf_stage_rejects_not_supported_smoke_output` | 同上。 |
| `test_calibrate_failure_survives_err_trap_and_writes_job_result` | 抽出 fixture に `USE_PERF` がなく、未定義変数で停止。 |

新規テスト開発中の赤は、予約量・argv 名・JSON 構造など fixture／assertion の誤りを修正し、最終実走で解消済みです。`git diff --check` も通過しました。

**未実走：** repository 全 suite、wrapper 全体の認証 job、計算ノードでの性能測定、M1〜M10／M-POS の変異実走。

## 受理・拒否挙動の変化

- **変更前：** policy 候補全滅で測定前に rc=2。
- **変更後・canonical unavailable：** sweep の全 rep を実行して throughput を保存。counter は null、noise は未実行、`saturation=None`。既存品質判定で **rejected・rc=1・未登録**。
- **変更後・候補全滅＋literal perf available：** perf 有り経路へ進めるため、既存品質条件を満たせば新たに accepted になり得ます。
- **旧 smoke 成功＋canonical probe 不成功：** 従来 accepted になり得た入力が rejected／失敗になる限界は残ります。
- `probe_error` は失敗のままです。maxrss・throughput 欠損と rep 非ゼロ終了は、該当 rep の理由と停止位置を確認しました。

認証 predicate・登録条件・rc の意味は変更していません。

## shell テストの主張範囲

**argv 生成と分岐の到達に限定しました。**

実 production 断片と canonical probe を使い、選択後 PATH、probe_error の保存、selection 不在、perf 有り argv の完全一致を確認しました。`exec_calibrate.py → os.execv` と job 終端は新規 shell テストの範囲外です。

Python 側は実経路を通しています。noise 遷移は実関数へ委譲する観測 wrapper で、holdout 側の拒否より前に記録します。

## 波及可能性の静的列挙

- **共有 fixture：** `_invoke` の既存 nm／sha256sum 応答は維持。追加の benchmark 応答は明示指定時だけ使用します。
- **所有外 shell consumer test：** 上記 4 件の旧期待値／不足変数への対応が残ります。
- **CLI・sweep caller：** receipt 未指定は従来の perf=True。perf 有り時に追加の `use_perf` keyword は渡しません。
- **holdout capability：** rr20／rr80 の perf mode が変更対象。実経路の両正例と既存 108 件で確認しました。
- **成果物 consumer：** `collect_receipt.py` は整数 rc と staging manifest を扱うため、rc=1・追加 receipt を回収可能。`env_contract.py` の accepted／registered 要求は維持され、no-perf 成果物は正式較正に使えません。
- **閉包・制約 meta-test：** perf inventory、環境 literal 制約、自走 harness 被覆、所要台帳被覆を実走しました。

## 裁定と食い違った事実

production 契約の相違はありません。

ただし、裁定で具体化されていなかった所有外の既存テスト 4 件の赤が判明しました。また、既存 `_invoke` の acquisition receipt は 1 点分の予約量なので、新規の 3 点 sweep fixture には対応する予約量が必要でした。

## 総括

実装と対象検証は完了しましたが、所有外の既存テスト 4 件が赤のため全体を closed とは申告しません。  
no-perf の測定継続・throughput 保存を確認し、認証は rejected・未登録を維持しています。  
認定較正取得の回復や予約費用の解消は達成範囲に含みません。  
docs・commit・push は未実施です。