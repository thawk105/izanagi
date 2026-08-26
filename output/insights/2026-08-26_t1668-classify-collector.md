# [T-1668] 出力前分類の起動器と scheduler accounting collector — 実測と変異台帳

wave: `dev-wave-t1668-classify-collector`
base: `9463bcbc`、実装 commit: `adf4aec6`
作成日: 2026-08-26

D843 の残余のうち、決定文が名指しした 2 つ (信頼側の起動器と収集器) を 1 変更単位で作った
wave の一次資料。裁定の全文は同 wave の `s4-adjudication.md` (erratum 1〜3 を含む)。

---

## 1. scheduler 側の証拠源の実測

### 1.1 会計エピローグ (`<script>.e<ID>`) — exit status は無い

`output/env/pegasus/smoke/0:867861.nqsv/smoke_probe.sh.e867861` の逐語:

```
============================================================
Request ID:             867861.nqsv
Request Name:           smoke_probe.sh
Queue:                  gen_S@nqsv
Number of Jobs:         1
User Name:              tanab
Group Name:             SFC
Created Request Time:   Sun Jul 19 00:53:37 2026
Started Request Time:   Sun Jul 19 00:53:45 2026
Ended Request Time:     Sun Jul 19 00:53:50 2026
Resources Information:
  Elapse:               9S
  Remaining Elapse:     591S
============================================================
```

2026-08-26 の本番 job (`948792.nqsv` / `949031.nqsv` / `949456.nqsv`) でも同形式を再確認した。
`orchestrator/campaign/silo_ladder_rung1.py` の
`validate_nqsv_accounting_epilogue` の docstring も
「NQSV は scheduler 側の exit status を会計エピローグへ出力しない」と明記している。

**射程の限定:** 上記は「観測した正常系エピローグには exit status が無かった」までを支持する。
node 障害・cancel・scheduler 版差を含む一般則ではない。

### 1.2 `qstat -J -f <request>` — `Exit Code` と `Execution Host` が在る

`output/insights/2026-08-03_t361-t362-cluster-probes/evidence/20260815T165532Z-203e1b799097dbd0/attempts/t361-flock/20260815T165533Z-t361-flock-a2-976fc6bbfdbb5894/work/controller/raw/00010-lifecycle-qstat-attempt-1.stdout.raw`
の逐語 (先頭 block):

```
Request ID: 912550.nqsv
    Batch Job Number = 0
    Execution Job ID = (none)
    User  Name = tanab
    User  ID   = 31609
    Group ID   = 30410
    Job Server Number = 3
    Job Server Name = JobServer0003
    Execution Host = bnode003
    Exit Code = 1100
  Resources Information:
    Memory    = 0.000000B
    Assigned Sockets = 0
    CPU Time  = 0.000000S
    Accumulated CPU Time = 0.000000S
    Remaining CPU Time = UNLIMITED
    Virtual Memory = 0.000000B
```

argv の正本は同 probe driver の `run_probes.py:1680`
(`["qstat", "-J", "-f", request_id]`)。

2026-08-26 に稼働中の本番 job `949456.nqsv` へ同 argv を実行し、
`Execution Host = bnode001` と `Exit Code = (none)` が返ることを再確認した。

**これは job 自身が書けない login 側の surface である。** D510 決定 4 の言う
「性能出力の外側の証拠」に当たる。収集器の証拠源をここに置いた。

### 1.3 `qstat -f` (request 単位) の状態 field

`output/env/pegasus/smoke/0:867861.nqsv/qstat_job.stdout` の逐語 (抜粋):

```
    Current State           = Running
    Previous State          = Pre-running
    State Transition Time   = Sun Jul 19 00:53:45 2026
    State Transition Reason = PRERUN_SUCCESS
```

`orchestrator/scheduler_nqsv.py` の parser が正規化する語彙は
`QUE` / `RUN` / `HLD` / `END` の 4 値だが、**これは parser の出力の閉集合であって
qstat プロトコル全体の語彙ではない。** `Previous State` と
`State Transition Reason` は parser の対象外である。

---

## 2. `Exit Code` の実測値域と、対応表が未確立であること

repo 全体を絞り込みなしで数えた (`grep -rh "Exit Code" output/`)。

| 値 | 件数 |
|---|---|
| `(none)` | 263 |
| `1100` | 4 |
| `F` | 3 |
| `9` | 2 |
| `A` | 1 |

すべて T-361 / T-362 の cluster probe が意図的に作った条件の観測である。

**どの値が `node_failure` を意味し、どの値が `scheduler_external_interruption` を
意味するかを裏付ける資料は repo に無い。** `9` は SIGKILL を思わせるが、D740 は
walltime kill と SIGKILL の自己申告を明示的に閉集合から除いており、
scheduler が報告した `9` がそのどちらでないと言える根拠は無い。

`DW-O13` は「field の実在では足りない。その field が実環境で取りうる値を実測し、
要求する値が到達可能か確かめてから述語を採用する。到達不能なら採用せず、
測った値域を裁定へ書く」と定める。**したがって収集器の規則表は exact に空のまま land した。**

帰結として、**本 wave の時点で収集器が正当に発行できる受領証は 0 件である。**
`_FLOOR_RECOVERY_AUTHORITIES` も空のまま維持した。成果物でこれを誇張しない。

---

## 3. 床値 campaign の配線が成立しない理由

段 6 の敵対レビュー 2 本が独立に指摘し、親が現物で確認した。

- `orchestrator/campaign/s8b_attempt_profile.py:395`
  `S8B_RETRYABLE_FAILURE_REASONS: frozenset[str] = frozenset()` — 空。
- 同 file の `TransitionPolicy` は `require_previous_terminal=True`、
  `forbid_retry_after_observation=True`、
  `require_terminal_reason_equals_classification=True`。
- `attempt_registry_core.py:1085-1119` は `attempt_ordinal > 0` の開始を
  「直前 ordinal の terminal が `retryable-failure`」か「検証済み recovery」でだけ許す。

順に辿ると:

1. terminal の理由は classification の理由と一致しなければならない。
   統計的に無効になった session の pre-output 分類理由は `None` である。
2. `retryable_failure_reasons` が空なので `retryable-failure` terminal を作れない。
3. `attempt_ordinal > 0` は terminal 経路から永久に開かない。
4. recovery 経路も §2 のとおり発火しない。

**床値 campaign の通常の測り直しが台帳の slot をひとつも取れない。**
床値 protocol は cell ごとの測り直し枠を前提に組まれているため、
稀な経路の破れではなく運用そのものが成立しない。

この不整合は D880 の却下理由に「registry の空 `retryable_failure_reasons` との不整合は
既知で、別裁定へ回す」と明記されている。解消には受理集合を広げるしかないため、
本 wave は配線を取り下げ、起動器を未接続のまま land した。

---

## 4. 変異 matrix (逐語)

harness: `tools/mutation_harness.py`、`--runner-mode dispatch`、`--detached`。
対象 test file 5 本、baseline は **rc=0 / 233 passed / failed_nodes=[]**。

### 4.1 probe 走 (全件 SURVIVED 期待。観測 node の収集)

spec sha256 `5241f88292e6c51243adaed815c53ae1f01cb41f7766a21087397d4e9ded33fc`。

| 変異 | 結果 |
|---|---|
| MUT-T1668-SEAL-ORDER | MISMATCH (赤 4 node) |
| MUT-T1668-OBS-AFTER-PREOUT | **SURVIVED** |
| MUT-T1668-REQUEST-ID-BINDING | MISMATCH (赤 1 node) |
| MUT-T1668-RECEIPT-IDENTITY | MISMATCH (赤 3 node) |
| MUT-T1668-AUTHORITY-LITERAL | MISMATCH (赤 1 node) |
| MUT-T1668-AUTHORITIES-EMPTY | MISMATCH (赤 1 node) |
| MUT-T1668-DEFERRED-LEAK | MISMATCH (赤 1 node) |

### 4.2 SURVIVED の erratum — 等価変異と再照準

`MUT-T1668-OBS-AFTER-PREOUT` の初回 replacement は関数の**型注釈だけ**
(`failure: ClassifiedFailure` → `ClassifiedAttempt`) を書き換えていた。
Python の注釈は実行時に強制されないため挙動を変えておらず、**等価変異**だった
(`DW-M04` に従い mutated 内容を確認して判定)。

再照準先は実行時判定
`state = _require_handle(failure, ClassifiedFailure)`
(`orchestrator/campaign/s8b_attempt_registry.py:1592`) の第 2 引数。

### 4.3 本走 (期待 node は probe の実測から作成)

spec sha256 `9e23257972eb022d06f47db6981b8b13b5f4a2aafafc0e7c4294728fa17a9edb`。
baseline は **rc=0 / failed_nodes=[]**。

| 変異 | 結果 | kill した node |
|---|---|---|
| MUT-T1668-SEAL-ORDER | **KILLED** | `test_s8b_floor_attempt_launcher.py::test_mut_t1668_seal_order_and_reason_precedence_use_recorder_fake[no-pre-output-reason]` / `[post-probe-precedes-launch-failure]` / `[launch-failure]`、`::test_open_error_still_observes_and_terminalizes_after_classification` |
| MUT-T1668-OBS-AFTER-PREOUT | 赤 (再照準版) | `test_s8b_attempt_registry.py::test_failure_observation_without_classification_remains_rejected` / `::test_failure_observation_cannot_be_recorded_twice` / `::test_mut_t1668_obs_after_preout_digests_actual_output` / `::test_failure_observation_after_terminal_remains_rejected` / `::test_failure_observation_after_recovery_remains_rejected` |
| MUT-T1668-REQUEST-ID-BINDING | **KILLED** | `test_s8b_scheduler_accounting.py::test_bound_request_cannot_be_constructed_from_a_raw_string` |
| MUT-T1668-RECEIPT-IDENTITY | **KILLED** | `test_s8b_scheduler_accounting.py::test_receipt_issuance_requires_typed_shared_root_capability` / `::test_mut_t1668_receipt_identity_includes_target_start_event_hash`、`test_s8b_holdout_admission.py::test_registry_recovery_of_retry_attempt_selects_that_attempt_as_trigger` |
| MUT-T1668-AUTHORITY-LITERAL | **KILLED** | `test_s8b_scheduler_accounting.py::test_mut_t1668_authority_literal_requires_independent_pin` |
| MUT-T1668-AUTHORITIES-EMPTY | **KILLED** | `test_s8b_holdout_admission.py::test_registry_recovery_authority_is_empty_and_fail_closed` |
| MUT-T1668-DEFERRED-LEAK | **KILLED** | `test_calibrator_deferred_output.py::test_capture_seals_raw_readers_perf_open_and_sinks_until_open` |

KILLED の 6 件は期待 node 集合と**完全一致**した (`DW-M08`)。
**登録した 7 件すべてが固有のテストに撃たれ、他層に mask されたものは無い。**

### 4.4 取り下げた変異 (初回登録を消さない記録)

- `MUT-T1668-RECOVERY-AFTER-OBS` / `MUT-T1668-RECOVERY-REPLAY` — 段 3 sol 所見 1 を
  real と裁定して登録したが、当該挙動は設計どおりの受理と判明したため取り下げた (erratum 1)。
- `MUT-T1668-FENCING` — core replay (`attempt_registry_core.py:1317`) に mask されると
  段 5 の実装子が判定し、単一理由へ帰属できないため登録しなかった。
- `MUT-T1668-SESSION-BYTES` — 撃つ対象 (床値 campaign の seam) を erratum 2 で
  取り下げたため消滅した。

---

## 5. 焦点走の記録 (すべて dispatch 実走)

| 時点 | 対象 | 結果 |
|---|---|---|
| 基準 (実装差分ゼロ) | 3 file | 625 passed / 1 failed (非帰属) |
| 単位 A・B 統合後 | 16 file | failed=2 (非帰属のみ) / errors=0 |
| 単位 C 統合後 | 6 file | 170 passed / 0 failed |
| 単位 F 統合後 | 2 file | 150 passed / 0 failed、rc=0 |
| 単位 D 統合後 | 11 file | 827 passed / 2 failed (1 件は本 wave 帰属) |
| fix1 後 | 2 file | 574 passed / 1 failed (非帰属のみ) |
| fix2 後 | 19 file | 1761 passed / 7 failed (5 件が本 wave 帰属) |
| **fix3 後 (最終)** | **21 file** | **1938 passed / 2 failed / 12 skipped、赤は非帰属のみ** |

非帰属の赤 2 件はいずれも
`assert "runs" in ignored_prefixes`
(`test_s8b_floor_campaign.py` と `test_s8b_oracle_driver.py`)。
`output/runs/` を作るのは `test_codex_worker_launch.py` の副作用であり、
fresh worktree の焦点走では作られない。実装差分ゼロの基準走でも再現する。
