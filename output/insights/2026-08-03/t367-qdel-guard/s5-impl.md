実装を完了しました。編集は指定された 2 ファイルだけです。テスト、`py_compile`、git 操作は一切実行しておらず、緑は主張しません。

## 変更箇所

- [dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:37)

  - cleanup 予算・gate regex/policy: 37, 123–130
  - gate 専用状態正規化/parser: 243–314
  - `_best_effort_qdel()`: 972–999
  - `_fresh_qstat_gated_qdel()`: 1002–1165
  - 残存警告: 1168–1187
  - `_dispatch_impl()` と4 callsite: 1208–1743
  - `dispatch()` の予算引数伝播: 1746–1839

- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:28)

  - fake scheduler拡張・明示 END 既定列: 28–198
  - parser/gate/retry/予算/TOCTOU/meta-test: 810–1078
  - 既存 qdel テストの裁定準拠更新: 1184–1415
  - HLD・qdel失敗/例外: 1479–1551
  - discovery不明・malformed ID: 1598–1646
  - RUN/UNKNOWN/非ゼロの明示 gate state: 1680–1900

## 裁定11項目との対応

| # | 実装 |
|---|---|
| 1 | `_fresh_qstat_gated_qdel()` を新設し、4 production callsiteを集約。primitive callerはhelper内1箇所のみ |
| 2 | ID一意性、対象block、state field一意性、両stateの整合を要求するtarget-bound parserを追加。`_scheduler_state()`は不変 |
| 3 | `[A-Za-z0-9][A-Za-z0-9._-]*`を正規化後に検査。不正IDでは対象qstat/qdelを発行せず、`--`も未導入 |
| 4 | `_classify_qstat_response()=="transient"`だけ最大3回再試行。permission・不在・RUN・END・UNKNOWNは即拒否 |
| 5 | 既定90秒のcleanup予算と`qdel.cleanup_elapsed_s`を追加。既存30秒command timeoutは不変 |
| 6 | terminal END観測後のQUE/HLDを`terminal-history-conflict`で拒否 |
| 7 | 判定tryとqdel primitiveを分離。`attempted`は起動要求を表し、qdel後のclock例外でも結果を維持するテストを追加 |
| 8 | qdel非ゼロ・例外時に`job_may_remain=true`と人間向け残存警告 |
| 9 | gate到達時は常に`cleanup_policy="fresh-qstat-gate/v1"`と`gate` objectを記録。schemaはv2据え置き |
| 10 | 非atomicなsnapshot保証に限定するdocstringと、QUE後RUN遷移のcharacterization testを追加 |
| 11 | AST meta-testで`_best_effort_qdel`のproduction callerを新helperだけに固定 |

scope外と裁定された孤児job lifecycle、discovery同定強化、receipt v3昇格は実装していません。

## 受理集合の差

変更前は4 cleanup経路で、permission、request不在、RUN、END、UNKNOWN、qstat非ゼロでもrequest IDがあればqdelを要求していました。

変更後に受理するのは、fresh qstatが次をすべて満たす場合だけです。

- rc=0
- 対象IDが一意
- 対象blockの状態が一意かつ矛盾なし
- 正規化状態がQUEまたはHLD
- terminal END履歴との矛盾なし
- cleanup予算内

STGはQUEへ正規化されます。qstat→qdelは非atomicなので、QUE snapshot後にRUNへ移る残余リスクは意図的に保証外です。

## 未実測と親が走らせる範囲

**pytest、構文確認、scheduler commandは走らせていません。**

親はまず全nodeidを実測してください。

```text
python3 tools/run_tests.py orchestrator/tests/test_pegasus_dispatch_compute.py -q
```

重点nodeidは以下です。

- `::test_fresh_qstat_gate_accepts_que_hld_and_stg_snapshots`
- `::test_target_bound_gate_rejects_malformed_or_conflicting_state`
- `::test_fresh_qstat_gate_retries_only_bounded_transient_errors`
- `::test_fresh_qstat_gate_cleanup_budget_stops_retry_and_records_elapsed`
- `::test_allowed_qdel_failure_records_job_may_remain_and_warns`
- `::test_missing_compute_marker_latches_only_after_visible_job_terminates`
- `::test_qdel_result_is_not_overwritten_by_post_qdel_gate_clock_exception`
- `::test_best_effort_qdel_production_caller_is_only_fresh_gate`

意図的に赤くするテストはありません。既存assertの削除・skip・弱体化もありません。

## 所有外への波及可能性

- `tools/run_tests.py` と `tools/check_ai_provenance.py` が`dispatch()`をproduction利用します。両者は整数rcを消費し、追加引数は既定値のため呼出形は維持されます。
- `tools/mutation_harness.py`はdispatcher path/source identityを扱うため、変更後は旧mutation ledgerをresumeできません。
- `tools/check_docs.py`と関連テストはdispatcherの`TASKS`をAST解析します。`TASKS`自体は未変更です。
- `qdel` objectのrepo内consumerは対象テスト以外には静的に見つかりませんでした。
- shared `_Scheduler`の既定状態列にgate用の明示`EXT`を追加しました。正常終了経路では余剰stateは消費されません。
- 新設・改名したテスト名を拘束する実行可能なrepo-wide meta-testやexact-vocabulary検査は見つかりませんでした。一方、過去の`output/` insightとstage3レビューには旧overall-timeout nodeidが残っています。歴史記録かつ編集禁止範囲なので変更していません。

## 総括

fresh qstatの対象ID・状態を厳密に束縛し、取消可能snapshotだけをqdelへ通すfail-closed gateへ4経路を集約しました。receipt証拠、bounded retry、90秒予算、END履歴矛盾、qdel失敗警告、TOCTOU限定、caller閉包まで実装済みです。実測は未実施で、親による対象ファイル全走が必要です。