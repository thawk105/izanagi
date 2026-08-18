## 実測

pytest と実装変更は行っていない。静的 AST と bounded `_ReachabilityExplorer` の read-only replay で確認した。

- `_reachable_calls` は `_functions` の top-level 定義だけを対象に、同一 module 内の名前・属性呼出しを間接追跡する。深さ制限はなく、cycle は `reached` で停止する (`s8c_preregistration_evidence.py:291-309,407-424`)。
- C12 の `read_binding` / `check_reservation` は `reservation.py` の top-level 定義 (`reservation.py:159,218`) と、`p3` の `run_trial` から到達する呼出し名が必要。配置は `run_trial` 本体、またはそこから直接呼ぶ top-level helper とする。
- C12 の環境経路は既に成立している。`p3:3825 -> run_trial -> _finish_trial:2472 -> _run_workload:3153 -> _drive_s8c_generation:1472 -> trigger.drive_iteration:640 -> loop.run_campaign:168 -> loop._authorize_measurement:109` を replay した結果、`env_contract.lookup` と `execution_guard.attest_and_build_receipt` はともに `graph.calls` に入った。環境 lookup の別経路も `p3:2811 -> trigger._admit_env_contract:325-331 -> _lookup` で成立する。`_declared_call` は target path が `contract.evidence_paths` に含まれることと graph 上の exact target を見るだけ (`s8c_preregistration_evidence.py:1474-1477,1903-1912`)。
- 現在の C12 未達は allocation gate に限定される。`_evaluate_c12` は allocation 判定を環境判定より先に返す (`s8c_preregistration_evidence.py:1765-1778`)。
- `is_reservation_required` は `IsolationPolicy.single_process` だけを返す (`reservation.py:273-277`)。Pegasus は `single_process=True`、Linux は `False` (`env_contract.py:253-267,292-307`)。したがって P5 は「予約不要なら読まない」を採る。
- `read_binding` は次の8 keyを必須とする (`reservation.py:120-175`)。`IZANAGI_RESERVATION_JOB_ID`, `REQUESTED_S`, `SCHEDULER_STARTED_EPOCH`, `DEADLINE_EPOCH`, `HOST`, `BOOT_ID`, `SCRIPT_SHA256`, `NONCE`。さらに `check_reservation` は `PBS_JOBID` を読む (`reservation.py:218-239`)。
- job不一致、boot不一致、残時間不足はすべて `ReservationError` (`reservation.py:237-257`)。成功時だけ `ReservationCheck` を返す (`reservation.py:262-270`)。`required_s` は正整数、`safety_margin_s` は非負整数 (`reservation.py:202-215`)。8bの既存呼出しは safety margin 0 (`s8b_oracle_driver.py:85,918-930`)。p3では `required_s=max_wall_s`, `safety_margin_s=0` とする。
- C04 の既存 lifecycle 記録先は `output/s8c-trial-registry/lifecycle.jsonl` (`trial_registry.py:47-51`)。`record_trial_terminal(..., terminal_status="indeterminate")` は既存 v1 row として report/journal hash を null にする (`trial_registry.py:1959-1983`)。新台帳形式は不要。
- `run_trial` の二つの `except BaseException` は `p3_autonomous_workload_trial.py:3524-3535,3630-3641`。現在は `_record_indeterminate_terminal` を呼び、再送出する。`_run_workload` 自体は `finally` 後に result を返すだけ (`p3_autonomous_workload_trial.py:3202-3209`)。`p3:3235` は workload catch ではなく、indeterminate terminal append の失敗を捕捉する箇所。通常の `Exception` は `_finish_trial:2473-2506` で supervisor-error/partial に変換されるため、この既存挙動は保つ。
- `record_trial_start_once` は既に start row の重複を atomic に拒否する (`trial_registry.py:1866-1870`)。`TrialLifecycleToken` と capability state は既存構造 (`trial_registry.py:198-226`)。
- C11 は成立。runtime test `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_two_generation_critic_feedback_precedes_next_planner` が、世代1の critic 後に世代2 planner payloadへ `critic_feedback.source_generation == 1` が入ることを assert している (`test_p3_autonomous_workload_trial.py:3313-3377`)。追加テストも production変更も不要。
- M1: 支持。`SATISFIABLE_CONDITION_IDS` は空集合 (`s8c_preregistration_evidence.py:1815-1818`)、機械判定が `SATISFIED` なら `ERROR` に変換される (`s8c_preregistration_evidence.py:1924-1932`)。
- M2: 支持。C11の cap、3境界の validator、critic projection は `p3_autonomous_workload_trial.py:126,395,2801,2906,3296,3772` に存在し、上記runtime testもある。
- M3: 支持。ただし「guard呼出しがp3本文にない」は不十分な観測。guardは `loop.py:92-120,168-170` 経由で到達済み。未実装なのは reservation consumer。
- M4: 支持。ただし `:3235` の説明は反証。そこは workload catch ではない。新設対象は `mark_experiment_indeterminate` と registry側の `forbid_trial_restart` / `reject_started_trial`。
- M5: 支持。freeze record は契約・規範 hashだけで production bytes 名を持たない (`output/s8c-preregistration/condition-freeze/condition-freeze.v1.g7.json:1`)。再凍結不要。
- M6: 反証。指定3面に加え、同じ predicate test内の `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer` (`test_s8c_preregistration_predicates.py:196-220`) も実装後に赤くなる。
- P1: 支持。C11は no-op、既存runtime被覆あり。
- P2: 支持。p3側で job/boot/deadline 判定を再実装せず `check_reservation` を呼ぶ。
- P3: 支持。既存 lifecycle terminal row を再利用する。
- P4: 支持。reservation preflight は current `run_trial` preflight帯 (`p3_autonomous_workload_trial.py:3292-3443`) に置き、lifecycle start・run_root・campaign launchより前にする。
- P5: 支持。Linuxの既存完走テストは予約keyを持たず、無条件読込は受理集合を狭める。Pegasus用の `test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers` (`test_claude_transport.py:1588-1645`) も `PBS_JOBID` 以外の予約keyを持たないため、valid reservation fixtureを追加する対象になる。

`grep -rln` で source/test/docs 全体を検索し、各該当 file を `grep -n` で再確認した。C04/C12の現在statusを消費する箇所は predicate test と invariant testだけで、他の `reservation` 呼出し (`t126_driver.py:951-952`, `s8b_oracle_driver.py:922-928` など) は独立consumerだった。

## プラン

1. `orchestrator/campaign/trial_registry.py:216-226,1810-1902`

   - 既存 `_TrialLifecycleCapabilityState` に `started_once` と `restart_forbidden` を追加する。`TrialLifecycleToken`自体は immutable identityなので変更しない。
   - `record_trial_start_once` で `started_once=True` を初期化する。
   - `reject_started_trial(*, trial_id, repository_root, lifecycle_path=DEFAULT_LIFECYCLE_PATH) -> None` を追加する。既存 `_locked_lifecycle_update` と `_load_lifecycle_rows` を使い、start rowがあれば `TrialRegistryError`。追加rowは書かない。
   - `forbid_trial_restart(token: TrialLifecycleToken) -> None` を追加し、既存 capability state の `restart_forbidden=True` を先に固定する。永続的な拒否は既存 start rowと `terminal_status="indeterminate"` rowで表現する。

2. `orchestrator/campaign/p3_autonomous_workload_trial.py:367-390,3292-3443`

   - sealedな `_RunEnvironmentAdmission` を追加し、`site`, `contract`, `reservation_binding`, `reservation_check`を保持する。
   - `run_trial` の validator、site opt-in、authority検査後、`run_root.mkdir` と `record_trial_start_once` より前に環境契約を一度解決する。
   - `contract.isolation_policy` が予約不要なら即 returnし、`read_binding(os.environ)` を呼ばない。
   - 必要時だけ `read_binding(os.environ)` と `check_reservation(binding, required_s=max_wall_s, safety_margin_s=0, environ=os.environ)` を実行する。
   - `trigger._current_site` と `_admit_env_contract` をここで一度だけ呼び、sealed admissionを `_finish_trial` / `_run_workload`へ渡す。既存 `p2` の site call 二重化を避ける。

3. `orchestrator/campaign/p3_autonomous_workload_trial.py:2344-2472,2747-2825`

   - `_finish_trial(..., execution_admission=None)` と `_run_workload(..., execution_admission=None)` に内部引数を追加する。
   - sealed admissionがある場合は既存の `trigger._current_site` / `_admit_env_contract` を再実行せず、同じ contractを `_prepare_campaign_identity` と `_drive_s8c_generation`へ渡す。
   - guardの権威は既存 `loop._authorize_measurement` (`loop.py:92-120`) に残し、p3側で attestation判定を複製しない。

4. `orchestrator/campaign/p3_autonomous_workload_trial.py:3212-3241,3524-3641`

   - `_record_indeterminate_terminal` を包む `mark_experiment_indeterminate(token, *, cause, remaining_cells, origin_terminal_projection=None)` を追加する。
   - helper内で先に `trial_registry.forbid_trial_restart(token)`、次に既存 `_record_indeterminate_terminal` を呼ぶ。
   - `run_trial:3526` と `run_trial:3632` の呼出しを新helperへ置換し、helper完了後に元の例外を再送出する。
   - `_finish_trial:2473` の通常 `Exception -> partial` 経路は変更しない。C04対象は未捕捉 `BaseException` crashである。

5. `orchestrator/tests/test_s8c_preregistration_predicates.py:139-220`

   - `test_current_repository_gap_reason_snapshot_requires_cross_wave_review` の C04/C12を、`EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable`へ反転。
   - `test_current_repository_c12_registry_reports_unwired_allocation_consumer`も同じ終端へ反転。
   - `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer`は `_c12_allocation_binding_verdict(...) is None` を assertする形へ反転。
   - synthetic absence tests (`:1260-1526,1998-2027`) の拒否理由は変更しない。

6. `orchestrator/tests/test_s8c_preregistration_invariant.py:43-122,321-329`

   集合差分は正確に次の3 tupleだけ。

   `MACHINE_CONTRACT_FUNCTION_CHECKS` へ追加:

   - `("C04", "orchestrator/campaign/p3_autonomous_workload_trial.py", "mark_experiment_indeterminate")`
   - `("C04", "orchestrator/campaign/trial_registry.py", "forbid_trial_restart")`
   - `("C04", "orchestrator/campaign/trial_registry.py", "reject_started_trial")`

   `MACHINE_CONTRACT_FUNCTION_EXCLUSIONS` から同じ3 tupleを削除する。C12の `reservation.read_binding` / `reservation.check_reservation` は引き続き `non-identifier-token` (`:113-120`) で、分類差分はない。

## テスト

実測はしていないため、以下は新設・変更nodeid案。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_run_trial_reservation_rejects_live_binding_mismatch[job-id-mismatch]`
  - `PBS_JOBID`だけを変更し、`ReservationError`を捕捉する。
  - 検出する実装ミス: `check_reservation`を呼ばない、bindingのjobだけを比較する、例外を握り潰す。

- `...::test_run_trial_reservation_rejects_live_binding_mismatch[boot-id-mismatch]`
  - bindingのbootだけを変更し、拒否とlaunch未実行をassertする。
  - 検出する実装ミス: boot照合の省略、job照合だけの実装。

- `...::test_run_trial_reservation_rejects_live_binding_mismatch[insufficient-remaining-time]`
  - deadlineを `required_s + safety_margin_s` 未満にし、拒否とprovider/campaign未起動をassertする。
  - 検出する実装ミス: `required_s=0`、deadline無視、残時間不足の例外隠蔽。

- `...::test_run_trial_does_not_read_reservation_for_linux_isolation`
  - `read_binding`をfail-fast monkeypatchし、Linux/OTHERの既存fixture runが完走することをassertする。
  - 検出する実装ミス: `is_reservation_required`を無視した無条件読込。

- `...::test_formal_crash_marks_experiment_indeterminate_and_forbids_rerun`
  - start後に `BaseException` を注入し、元例外の再送出、lifecycle terminal rowの `indeterminate`、reportのpartial化なし、別run_rootでの再起動拒否をassertする。
  - 検出する実装ミス: crashをpartial成功相当に変換、markをraise後に置く、restart guardを呼ばない。

- `orchestrator/tests/test_trial_registry.py::test_reject_started_trial_blocks_existing_lifecycle_start`
  - 既存start rowを検出し、ledger bytesが不変のまま拒否することをassertする。
  - 検出する実装ミス: preflightが常に通る、別pathを読む、registryを変更する。

- `orchestrator/tests/test_trial_registry.py::test_forbid_trial_restart_preserves_existing_lifecycle_record`
  - `forbid_trial_restart`後に新形式rowを追加せず、既存start/indeterminate terminal構造で再起動不可となることをassertする。

既存被覆との差分は、leafの `test_check_reservation_rejects_each_negative_core[...]` (`test_reservation.py:140-155`) が判定器単体しか見ていないのに対し、上記3件はp3 consumerのlaunch前支配性を検出する点にある。C04では既存の `test_formal_post_start_io_failure_records_indeterminate_and_stays_consumed` (`test_p3_autonomous_workload_trial.py:5743-5772`) を維持し、通常の `Exception -> partial` は `test_supervisor_error_still_writes_partial_terminal_report` として退行させない。

C11は既存の `test_two_generation_critic_feedback_precedes_next_planner` が世代Nのprojectionを世代N+1 planner入力へ結び付けているため、純増テストなし。

## 危険

- `reject_started_trial` はfail-fastであり、同時起動の最終防壁は既存 `record_trial_start_once` のatomic checkとして残す。
- lifecycle JSONのexact key集合 (`trial_registry.py:76-88,1646-1689`) は変更しない。新しい `started_once` / `restart_forbidden` JSON形式を作ると既存履歴検証を壊す。
- `_finish_trial` の `Exception` catchまでindeterminate化すると、既存のpartial受理集合が変わる。C04の対象は `BaseException` crashに限定する。
- Pegasusの既存fixtureは予約key不足であり、条件付き読込でも拒否対象。`test_p2_flag_on_run_trial_admits_compute_wrapper_with_real_providers` はvalid binding fixtureを追加する必要がある。
- p3は別wave `worktree-dev-wave-t1333-t1310-workload-profile` と同じファイルを編集する。C09/C10 waveはpredicate snapshot/invariant testと衝突するため、land直前に行番号と集合を再確認する。
- 判定器は変更対象外。nested function、dead branch、test-only decoyで静的到達を満たす実装は、既存 negative control (`test_s8c_preregistration_predicates.py:1271-1526`) で拒否される。

## 総括

C11はproduction変更不要で、runtime被覆も存在する。  
C12はenv/guard到達済みで、追加対象はreservation consumerだけである。  
予約不要時は読まず、Pegasusだけ3拒否を実際に発火させる。  
C04は既存lifecycle ledgerを再利用し、crashをindeterminateかつ再起動不可にする。  
M6はpredicate内の追加tripwireも反転対象として扱う。