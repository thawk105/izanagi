## 総括

T-2515回収のD95 Codex authorとして、指定4 fileに局所合成を実施した。`rratio`の受理集合は、投入wrapperとjob bodyの両方でexact `{5, 20, 50, 80, 95}`に揃えた。条件関門は既存のsmoke済み`CALIBRATE_PYTHON`選定を関門より前へ移し、argv先頭だけを`"$CALIBRATE_PYTHON"`へ変更した。macro、meaning、timeout 300秒、siloだけが呼ぶ条件は変えていない。

T-2535のoffline staging、pristine verifier用の独立interpreter選定、5個のFetchContent引数、productionの`run_condition_gate`実起動観測は維持した。T-2536の軸名関連testは変更していない。BACKOFF撤去、fixture共有化、receipt schema拡張、patch materialize、新規測定は取り込んでいない。

## 変更内容

- `tools/pegasus/submit_certify.sh`: usage、exact比較、拒否文言を5値に拡張。protocol関門とoffline staging precheckは不変。
- `tools/pegasus/certify_calibration.sh`: job側exact比較を5値に拡張し、既存の`CALIBRATE_PYTHON`選定ブロックをNM記録後へ前倒し。後段のperf shimと最終`CALIBRATE_PATH`は維持。
- `orchestrator/tests/test_pegasus_calibration_workload.py`: 両shellのexact受理集合を抽出比較、job bodyの5正例と6非canonical負例を実起動、submitterの5正例でpre-submit・receipt・qsub exportの実体を検査。8負例はclean repo・三者staging済み・dry-runで、baselineはrc=2かつ投入成果物なしとした。関門harnessは記録用python3.10と裸`python3`のpoison stubを分離し、`CALIBRATE_PYTHON`に記録用絶対pathを渡す。
- `orchestrator/tests/test_pegasus_tools.py`: interpreter選定ブロックと後段PATH shimを別抽出して連結。toolchain fragmentの終端をinterpreter選定前へ狭めた。

## 実走とchecker

- `PYTHONPATH=orchestrator python3 tools/run_tests.py -q orchestrator/tests/test_pegasus_calibration_workload.py orchestrator/tests/test_pegasus_tools.py`
  - rc=16。runnerが計算ノードdispatchを選び、`qstat -Q preflight rc=1`でdispatch infrastructure failure。`child_started=false`でpytest子は未起動。receiptは`output/pegasus-dispatch/bc2b6c55bcdd6f6aefbbf602a4cee1f8/receipt.json`。
- 次の8 test selectorを同じ`tools/run_tests.py`へ渡して再試行: `test_submitter_exposes_only_the_calibration_whitelist`、`test_job_rechecks_the_submission_workload_and_records_it`、`test_condition_gate_uses_smoke_checked_interpreter_selected_before_call`、`test_submitter_rejects_an_unregistered_ratio_before_side_effects`、`test_submit_dry_run_passes_scheduler_file_paths_to_qsub`、`test_certify_calibrator_resolves_and_shims_versioned_interpreter`、`test_certify_calibrator_interpreter_resolution_fails_closed`、`test_certify_records_real_cmake_and_fixed_nm_identity`。
  - rc=16。同じ`qstat -Q preflight rc=1`で、`child_started=false`。receiptは`output/pegasus-dispatch/ebd2bffc70456946497bc57a7de494aa/receipt.json`。
- `python3 tools/check_codex_agents.py`: rc=0。
- `python3 tools/check_docs.py`: rc=0、違反なし。
- `git diff --check`: rc=0。指定4 fileのU+0300〜U+036F走査は検出0。

pytestは一度も起動できていないため、greenやclosedは報告しない。状態は「実装済み・未実走」である。

## 静的波及確認

所有4 fileを起点とするconsumer閉包は、所有中の2 test fileを含めて次の7 fileと確認した。親の全走対象と一致する。

- `orchestrator/tests/test_pegasus_calibration_workload.py`
- `orchestrator/tests/test_pegasus_tools.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_pegasus_floor_tools.py`
- `orchestrator/tests/test_hooks.py`
- `orchestrator/tests/test_check_docs.py`

新設testは`test_condition_gate_uses_smoke_checked_interpreter_selected_before_call`の1本。test改名はない。制約meta-testとしてacceptance duration ledgerのconsumerとadd-only更新制約を調べ、今回の2 test fileは凍結suite prefixに含まれないことを確認した。ledgerは所有外であり、未実走でduration実測もないため編集していない。

## 親への引継ぎ

- 親が先行変更した`tools/pegasus/README.md`は編集・復元していない。
- commit、git add、merge、cherry-pickは実施していない。
- queueまたはdispatch preflightが復旧後、親は上記7 fileの全走と事前登録8変異を現合成差分上で取得する必要がある。M8は新しい実起動consumerを含む失敗node完全集合をprobeから生成する。
- accepted calibrationは未取得で、性能測定も新規起動していない。
