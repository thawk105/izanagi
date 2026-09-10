静的検査のみであり、pytest は実行していない。

# 所見 1: hold の書込み前失敗は診断だけ残して fail-open になる

判定 (real/refuted): real

根拠 (file:line):

- `_latch_orphan_hold` は `OSError` を `qdel["hold_error"]` と stderr に記録するだけで `None` を返す。`os.open` が EACCES、ENOSPC、EROFS などで inode 作成前に失敗した場合、hold は存在しない。`tools/pegasus/dispatch_compute.py:1056-1068`
- `claim_cleanup_once` の `finally` は `_latch_orphan_hold` の戻り値を検査せず、失敗後も元の cleanup 結果を返す。`tools/pegasus/dispatch_compute.py:1551-1574`
- harness の独立停止条件は「timeout」または「hold path が存在する」だけで、receipt の `qdel.hold_error` や `job_may_remain=True` を読まない。`tools/mutation_harness.py:247-287`
- したがって非 timeout の dispatch rc=16 では hold 不在のまま `finally` が復元側へ進める。`tools/mutation_harness.py:1783-1793`, `tools/mutation_harness.py:1837-1867`
- 新設テストも「診断が入る」「hold が存在しない」までしか確認せず、復元・後続投入が止まることを検査しない。`orchestrator/tests/test_pegasus_dispatch_compute.py:2343-2369`

成果物影響 1 行: `job_may_remain=True` の invocation 後に変異 source が復元され、後刻 job が読む bytes と mutation ledger／proof の対応が壊れる。

推奨対処: hold 作成失敗を receipt 診断で終わらせず、harness が当該 attempt の receipt／sidecarにある `job_may_remain=True` または `hold_error` を独立に検出して `OrphanHoldStop` にする。より強い境界として、qsub 前の durable unresolved claim を作り、書けなければ qsub 自体を開始しない。

# 所見 2: `qsub_result_unknown` はメモリ上だけで、signal／SIGKILL に耐久しない

判定 (real/refuted): real

根拠 (file:line):

- `qsub_result_unknown=True` は qsub 直前の Python bool 代入にすぎず、durable record ではない。`tools/pegasus/dispatch_compute.py:1596-1611`
- hold は outer exception に到達した後、request discovery が完了してから初めて作られる。`tools/pegasus/dispatch_compute.py:1900-1934`
- `_discover_request_id` は `_run(qstat)` の例外だけを捕捉し、その後の `_capture(result)` は try の外にある。最初の signal で qsub 経路から unwind した後、ここで再度 SIGINT／SIGTERM が入ると `_SignalAbort` が再送出され、hold 作成へ到達しない。`tools/pegasus/dispatch_compute.py:906-925`
- 外側の `dispatch` はその例外を setup failure receipt に畳むだけで、orphan hold は作らない。`tools/pegasus/dispatch_compute.py:2032-2066`
- SIGKILL は exception handler 全体を迂回する。mutation harness の timeout fallback はその利用時だけ有効で、直接 dispatch や provenance dispatch を救わない。
- 新設テストは qsub 呼出しそのものが `_SignalAbort` を投げ、続く discovery が正常完了する一経路だけを固定している。`orchestrator/tests/test_pegasus_dispatch_compute.py:2415-2443`

成果物影響 1 行: scheduler が qsub を受理した後でも hold 不在で終了でき、次回投入・source 復元・worktree 廃棄が未観測 job と並行して進む。

推奨対処: qsub 前に create-only の unresolved claim を永続化し、観測済み rc≠0 または対象束縛された終端証拠でのみ解決する。少なくとも discovery と hold 作成中は signal を pending 化し、hold を先に作ってから request ID を補助情報として収集する。

# 所見 3: `_apply_mutation` の `finally` は本体例外を握り潰す

判定 (real/refuted): real

根拠 (file:line):

- 本体で特別扱いされるのは `SignalAbort` だけで、通常の `HarnessError`、`RuntimeError`、I/O例外は active exception のまま `finally` に入る。`tools/mutation_harness.py:1833-1836`
- その時点で hold があれば `pending_stop` を新設し、`raise pending_stop` するため、本体例外は呼出し側から見える主例外ではなくなる。`tools/mutation_harness.py:1837-1864`
- さらに `_assert_only_expected_dirt`、`_assert_head`、変異 bytes 再読が失敗すると、その検査例外が本体例外を置換する。`tools/mutation_harness.py:1842-1850`
- `main` は `OrphanHoldStop` のみを停止 ledger 化するが、その schema に元例外の型・文言・trace はない。`tools/mutation_harness.py:2363-2393`, `tools/mutation_harness.py:2715-2724`

成果物影響 1 行: orphan-stop ledger から実際の runner／harness 故障原因が消え、変異結果を再現・監査するための診断鎖が欠落する。

推奨対処: `except BaseException as exc` で元例外を保持し、`OrphanHoldStop` の構造化 fieldへ型・文言を保存した上で `raise stop from exc` とする。`finally` 内の検証失敗も元例外と併記し、置換しない。

# 所見 4: receipt 署名そのものの return 網羅性には欠落がない

判定 (real/refuted): refuted

根拠 (file:line):

- `_fresh_qstat_gated_qdel` は初期値を `job_may_remain=True` とする。request ID 不明、clock 例外を含む早期 return もこの値を維持する。`tools/pegasus/dispatch_compute.py:1154-1199`
- `denied` の全経路は明示的に `True` を再設定するため、request 不在、terminal conflict、permission、RUN／UNKNOWN、予算切れも hold 対象になる。`tools/pegasus/dispatch_compute.py:1206-1237`, `tools/pegasus/dispatch_compute.py:1243-1314`
- qdel 経路は rc=0 の場合だけ `False`、非ゼロまたは例外なら `True` になる。`tools/pegasus/dispatch_compute.py:1316-1347`
- `claim_cleanup_once` の初期 record も `True` であり、helper が例外送出しても `finally` が同じ mutable recordを署名する。`tools/pegasus/dispatch_compute.py:1539-1574`
- qsub 結果未観測経路も明示的に `True` を設定する。`tools/pegasus/dispatch_compute.py:1921-1934`

成果物影響 1 行: 正常に生成・処理できた receipt について、`job_may_remain=True` を署名分類から漏らして成果物を受理する経路は見つからない。

推奨対処: 単純署名は維持する。所見1・2のように「署名へ到達しない」「署名後に永続化できない」境界を別途塞ぐ。

# 所見 5: 新設テストには恒真または層間配線を証明しない gate が残る

判定 (real/refuted): real

根拠 (file:line):

- 次は helper を直接呼ぶだけなので、production call siteから署名・latch呼出しを削除しても緑のままになる。
  - `test_orphan_hold_signature_uses_only_literal_job_may_remain`
  - `test_orphan_hold_signature_rejects_false_missing_and_non_bool`
  - `test_request_absent_and_terminal_history_receipts_latch_hold`
  - `test_orphan_hold_record_is_create_only`
  - `test_orphan_hold_write_error_is_recorded_and_not_reported_as_success`
  - `orchestrator/tests/test_pegasus_dispatch_compute.py:2251-2369`
- 特に write-error test は `hold_error` と stderr という診断文字列、hold 不在だけを assertし、後続 source 復元や scheduler 起動を検査しない。`orchestrator/tests/test_pegasus_dispatch_compute.py:2343-2369`
- 次の正例は意図的な受理集合 pin だが、対応する拒否 gate を削除しても緑になる。
  - `test_observed_nonzero_qsub_does_not_latch_orphan_hold`
  - `test_dispatch_non_timeout_parse_error_is_not_an_orphan_condition`
  - `test_no_hold_keeps_positive_teardown_paths_between_observation_points`
  - `test_dispatch_cleanup_without_hold_keeps_existing_positive_behavior`
- consumer testの多くは hold を fixture 自身で作るため、実 producer を削除しても緑になる。signal testは `orchestrator/tests/test_mutation_harness.py:942-968`、worktreeの fake harnessは `orchestrator/tests/test_mutation_worktree.py:151-154`、acceptance testは `orchestrator/tests/test_check_acceptance_reds.py:1721-1749` と `:1770-1801` で直接作成している。
- qsub 未観測テストは通常 signal 1 回だけで、所見2の再 signal、SIGKILL、hold writer失敗を殺さない。`orchestrator/tests/test_pegasus_dispatch_compute.py:2415-2443`

成果物影響 1 行: 新設テストが全緑でも、実 producerが hold を残せず consumerが sourceを復元する false-openを mutation matrixが検出できない。

推奨対処: 実 dispatchからharness／worktreeまで通す焦点テストを追加し、`os.open` の作成前 EACCES、discovery中の再 signal、dispatcher強制終了を注入する。assert対象は診断ではなく「変異 bytes保持」「次 runner 0回」「container存在」「非終端 stop ledger」にする。

# 所見 6: F47・通常完走・local・非 timeout PARSE_ERROR の受理集合は静的には維持される

判定 (real/refuted): refuted

根拠 (file:line):

- F47 は orphan hold より先に検査され、既存文言と優先順位を維持する。`tools/pegasus/dispatch_compute.py:1448-1462`
- 通常完走は `claim_cleanup_once` を呼ばず、receipt 永続化後に `active=False` として従来の child rcを返す。`tools/pegasus/dispatch_compute.py:1854-1899`
- harness の orphan 判定は `runner_mode != "dispatch"` なら即座に不成立で、worktree側の検査も dispatch modeに限定される。`tools/mutation_harness.py:247-258`, `tools/mutation_worktree.py:1150-1153`
- 非 timeout の `PARSE_ERROR` は orphan条件にならず、`finally` が従来どおり `_restore_targets` を呼ぶ。`tools/mutation_harness.py:1783-1804`, `tools/mutation_harness.py:1837-1867`

成果物影響 1 行: clean rootでの通常成果物、local mutation結果、従来の非 timeout PARSE_ERROR停止について、意図しない受理集合変更は静的には確認できない。

推奨対処: 実測緑とは扱わず、親の再走でこの4正例を固定する。既知の1赤は次所見のfixture隔離で解消する。

# 所見 7: 判明済み赤を別 rootへ隔離する案は期待値緩和ではない

判定 (real/refuted): refuted

根拠 (file:line):

- 当該テストは `trusted` と `untrusted` という独立したdeadline事例を、同じ `tmp_path / "dispatch"` に連続投入している。`orchestrator/tests/test_pegasus_dispatch_compute.py:2564-2602`
- 1回目は terminal evidenceなしの timeoutとなるため、現在の契約では hold が残り、2回目を投入前に拒否するのが正しい。拒否点は `tools/pegasus/dispatch_compute.py:1453-1462`
- assert対象は各schedulerの elapsed、state、qstat回数、qdel不実行であり、root共有そのものではない。`orchestrator/tests/test_pegasus_dispatch_compute.py:2604-2619`
- したがって `_dispatch(tmp_path / "trusted", ...)` と `_dispatch(tmp_path / "untrusted", ...)` のように入力だけを隔離し、assertを一行も変えない修正は、比較対象を独立fixtureへ戻すものである。
- repo内の直接 `DC.dispatch`／`_dispatch` 呼出しを静的探索した結果、同一root複数dispatchは他に2件あった。
  - `test_m6_qstat_success_without_request_skips_qdel_and_create_only_latches` は2回目を止めること自体が目的。`orchestrator/tests/test_pegasus_dispatch_compute.py:1724-1758`
  - `test_f47_latch_precedes_orphan_hold_and_hold_remains_independent` はF47除去後も同じholdで止まることが目的。`orchestrator/tests/test_pegasus_dispatch_compute.py:2392-2412`
- `test_python_dont_write_bytecode_env_is_projected_into_tests_request` も2回dispatchするが、既に別rootである。`orchestrator/tests/test_pegasus_dispatch_compute.py:2805-2843`

成果物影響 1 行: root隔離によりdeadline parserの既存期待値を維持しつつ、orphan holdによる正しい投入拒否を誤回帰として扱わずに済む。

推奨対処: 親案どおり2事例を別rootへ分ける。同一root拒否の保証は既存の上記2テスト、とくにF47を除去して再試行する後者へ担わせる。

# 所見 8: 既存 hold の path・symlink・部分書込み検査は fail-closed

判定 (real/refuted): refuted

根拠 (file:line):

- dispatch、harness、worktree、acceptance cleanupはいずれも `os.lstat` を使い、正常fileだけでなくdirectory・symlink・壊れたJSONも存在扱い、`OSError` も成立側へ倒す。`tools/pegasus/dispatch_compute.py:985-995`, `tools/mutation_harness.py:169-176`, `tools/mutation_worktree.py:616-626`, `tools/check_acceptance_reds.py:383-393`
- hold writerは `O_CREAT | O_EXCL` で先にinodeを作り、後続のJSON書込みやfsyncに失敗してもunlinkしない。したがって作成後の部分書込みは次回検査でholdとして扱われる。`tools/pegasus/dispatch_compute.py:372-384`
- dispatchのcustom output rootは使用前にresolveされる。`tools/pegasus/dispatch_compute.py:1417-1424`

成果物影響 1 行: 既にpathが作られた後の破損・読取不能・symlinkでは安全でない成果物受理は起きず、過剰停止側に倒れる。

推奨対処: この存在判定は維持する。broken symlink、directory、EACCES、書込み途中fileを明示テストし、inode作成前の失敗だけは所見1のdurable claim境界で塞ぐ。

## 総括

最重は、hold writerがinode作成前に失敗すると診断だけで終わり、harnessが非 timeout経路でsourceを復元できる点である。  
次に、`qsub_result_unknown` が非永続boolであり、SIGKILLやdiscovery中の再 signalではhold作成前に終了できる。  
`_apply_mutation` の `finally` は安全停止自体は優先するが、元の実行例外を停止ledgerから消してしまう。  
receiptの `job_may_remain` 署名、既存holdのlstat検査、F47／通常／local／PARSE_ERRORの受理集合には静的な欠落を認めなかった。  
既知の1赤を別rootへ隔離する案は期待値緩和ではなく、独立したdeadline事例から新しいlatch状態を分離する正当なfixture修正である。