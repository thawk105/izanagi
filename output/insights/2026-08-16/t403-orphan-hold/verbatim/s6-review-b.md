静的検査のみ。pytest は実行せず、親の実測結果を前提とした。

# 所見 1: hold 書込み失敗を層 2 が独立に塞げていない

判定 (real/refuted): real

根拠 (file:line):

- dispatcher は hold 作成失敗時、`qdel.hold_error` を記録して file を作らずに戻る。[dispatch_compute.py:1061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1061)
- その後 receipt は保存され、通常の infra rc=16 として終了する。[dispatch_compute.py:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1953)
- harness の独立判定は `timed_out is True` または hold file の存在だけであり、`hold_error`、`job_may_remain`、dispatch rc=16 を見ない。[mutation_harness.py:247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:247)
- 非 timeout かつ hold 不在なら mutation は通常の `PARSE_ERROR` 処理へ進み、finally で source を復元する。[mutation_harness.py:1783](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1783)、[mutation_harness.py:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1837)
- 新設テストは `_latch_orphan_hold` 単体の書込み失敗しか検査せず、dispatcher → harness の波及を通していない。[test_pegasus_dispatch_compute.py:2343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2343)

成果物影響 1 行: hold storage が壊れたときに変異 source が復元され、孤児 job が読む bytes と mutation ledger の対応が壊れるため、裁定 L1.4/A-4 の保証が成立しない。

推奨対処: dispatch result へ権威ある `job_may_remain`／`hold_error` を渡し、harness は非 timeout でもそれを孤児条件として停止する。書込み失敗を dispatcher から `_apply_mutation` まで通す統合テストと事前登録変異を追加する。

# 所見 2: 新設テストの検出力と事前登録には穴がある

判定 (real/refuted): real

根拠 (file:line):

主な行削除と、新設テストの対応は次のとおり。

| 削除・破壊する実装 | 赤くなる新設テスト |
|---|---|
| 署名 `job_may_remain is True` [dispatch_compute.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1001) | `test_orphan_hold_signature_uses_only_literal_job_may_remain`、`test_request_absent_and_terminal_history_receipts_latch_hold`、`test_orphan_hold_record_is_create_only`、`test_orphan_hold_write_error_is_recorded_and_not_reported_as_success`、`test_qsub_result_unobserved_discovers_and_holds_without_qdel` |
| create-only 書込み [dispatch_compute.py:1056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1056) | record create-only、request-absent/history、qsub-result-unobserved |
| `hold_error` 記録 [dispatch_compute.py:1061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1061) | `test_orphan_hold_write_error_is_recorded_and_not_reported_as_success` |
| 投入前 gate [dispatch_compute.py:1453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1453) | `test_existing_orphan_hold_blocks_before_any_scheduler_command`、`test_f47_latch_precedes_orphan_hold_and_hold_remains_independent` |
| qsub 前の unknown 武装 [dispatch_compute.py:1597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1597) と例外処理 [dispatch_compute.py:1906](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1906) | `test_qsub_result_unobserved_discovers_and_holds_without_qdel` |
| qsub 非0観測後の unknown 解除 [dispatch_compute.py:1617](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1617) | `test_observed_nonzero_qsub_does_not_latch_orphan_hold` |
| timeout 条件、停止、復元見送り [mutation_harness.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:261)、[mutation_harness.py:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1837) | `test_dispatch_timeout_latches_hold_preserves_bytes_stops_next_and_writes_stop` |
| signal 中の finally gate [mutation_harness.py:1837](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1837) | `test_signal_unwind_with_hold_marks_restore_skipped_and_preserves_mutation` |
| collection/baseline の投入前 gate [mutation_harness.py:1269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1269)、[mutation_harness.py:1642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1642) | `test_preexisting_hold_blocks_collection_and_baseline_runner_start` の両 parameter |
| teardown gate [mutation_worktree.py:945](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:945) | `test_orphan_hold_always_blocks_should_teardown...` の3件、`test_orphan_hold_preserves_container...` の2件 |
| fallback gate [mutation_worktree.py:1206](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1206) | `test_plan_only_exception_fallback_preserves_orphan_hold_container...` |
| dispatch artifact 保全 [check_acceptance_reds.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:396) | `test_dispatch_cleanup_preserves_everything_when_orphan_hold_exists` |
| probe worktree 保全 [check_acceptance_reds.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:833) | `test_probe_cleanup_runs_no_command_or_rmdir_when_orphan_hold_exists` |

削除変異を1本も kill しない正例専用テストは次の4つである。

- `test_orphan_hold_signature_rejects_false_missing_and_non_bool`
- `test_dispatch_non_timeout_parse_error_is_not_an_orphan_condition`
- `test_no_hold_keeps_positive_teardown_paths_between_observation_points`
- `test_dispatch_cleanup_without_hold_keeps_existing_positive_behavior`

これらは過剰拒否を検出する価値はあるが、M1〜M9 の行削除検出力には数えられない。

また、次の実装行は10変異では殺せない。

- cleanup から latch を実際に呼ぶ `finally`。[dispatch_compute.py:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1567) これを削除しても direct helper test と qsub-unknown の別呼出しは緑のままである。
- 4箇所の `lstat` OSError → hold 成立 branch。例: [dispatch_compute.py:993](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:993)、[mutation_worktree.py:624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:624)、[check_acceptance_reds.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:391)。新設テストは通常 file と不在だけで、判定不能を注入しない。
- hold payload の `schema_version`、`job_name`、`submission_dir`、大半の recovery field。[dispatch_compute.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1026)
- acceptance の `_cleanup_dispatch_artifacts` gate。テストはあるが、M9 は `_cleanup_probe` だけである。
- harness の collection/baseline の「runner 終了後に新たに立った hold」と hold 書込み失敗経路。

成果物影響 1 行: 登録済み10変異を全て KILLED にしても、cleanup caller の切断や判定不能 fail-open により孤児 source を復元・削除できる。

推奨対処: M10として cleanup caller から `_latch_orphan_hold` を削除、M11として各 consumer の `lstat` OSError を不在扱い、M12として dispatcher hold write failure を追加する。P1は下記のように producer／harness／worktree／acceptanceへ分割する。

# 所見 3: gate 先取り後の期待 node は多くが1件では足りない

判定 (real/refuted): real

根拠 (file:line):

静的に導ける完全集合は次のとおり。parameterized case は別 node と数える必要がある。

| 変異 | 期待される失敗 node | gate由来1件で十分か |
|---|---|---|
| M1 | signature true 6件、request/history 2件、create-only、write-error、qsub-unobserved | 不十分 |
| M2 | existing-hold gate、F47 priority の2件 | 不十分 |
| M3 | qsub-result-unobserved 1件 | 十分 |
| M4 | dispatch-timeout、signal-unwind の2件 | 不十分 |
| M5 | dispatch-timeout 1件 | 十分 |
| M6 | dispatch-timeout 1件。ただし変異の具体形で stop-ledger assertion と next-run assertionのどちらが先に壊れるかが変わる | 現状1件 |
| M7 | `_should_teardown` の3 parameter＋wrapper integration の2 parameter、合計5件 | 不十分 |
| M8 | plan-only fallback 1件 | 十分 |
| M9 | probe cleanup 1件 | 現状は十分 |
| P1 | 単一変異として定義不能 | 不十分 |

P1は `_orphan_hold_required`、dispatch の `_orphan_hold_present`、harness の `_path_present_fail_closed`、worktree と acceptance の `_orphan_hold_present` という独立した5判定面を「全」としている。例えば worktree の正例テストは `_should_teardown(orphan_hold=False)` を直接呼ぶだけで、実際の detector を常時成立へ変えた場合の単一理由性を証明しない。[test_mutation_worktree.py:532](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_worktree.py:532)

成果物影響 1 行: gate由来1件だけを expected node にすると、実際には複数 node が落ちて `MISMATCH` となり、正しい安全機構を mutation proof が誤って失格にする。

推奨対処: P1をP1a〜P1eへ分割し、各 detector に hold 不在の実呼出し正例を置く。M1、M2、M4、M7は baseline 修正後の JUnit から全 parameter nodeid を再導出する。

# 所見 4: 現在の焦点 test は新 gate による自己汚染で land 不能

判定 (real/refuted): real

根拠 (file:line):

- `test_nonzero_qstat_run_stdout_does_not_restart_deadline` は同じ `tmp_path/output/pegasus-dispatch` に対して2回 `_dispatch` する。[test_pegasus_dispatch_compute.py:2564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2564)、[test_pegasus_dispatch_compute.py:2590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2590)
- 1回目は UNKNOWN cleanup により `job_may_remain=True` となって hold を作り、2回目は scheduler より前に拒否される。[dispatch_compute.py:1300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1300)、[dispatch_compute.py:1453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1453)
- 親の実測した唯一の赤と一致する。

成果物影響 1 行: 焦点 suite が baseline で赤いため mutation harness と最終受入を開始できず、現差分はそのまま land できない。

推奨対処: gateを緩めず、2つの比較 subcase に別 `output_root` を与える。人工 hold を削除して続行するより、独立 root の方が本番の create-only 契約を汚さない。

# 所見 5: stop ledger と案内された resume command が非互換

判定 (real/refuted): real

根拠 (file:line):

- orphan stop 時は通常 ledger v4を `partial_ledger` に包み、同じ `--out` を `izanagi-dev-wave-mutation-orphan-stop/v1` で上書きする。[mutation_harness.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2363)
- worktree は保全時に必ず `--resume` command を表示する。[mutation_worktree.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1044)
- しかし resume loader は exact な通常 ledger field 集合と `schema=izanagi-dev-wave-mutation/v4` を要求し、stop schemaや `partial_ledger` を受理しない。[mutation_harness.py:2152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2152)
- timeout hold は `job_name=None` とし、request recovery が失敗すれば `request_id` と `submission_dir` も `None` になる。[mutation_harness.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:207) 新設テスト自身が `request=None` を使うが、hold payload の識別力を検査しない。[test_mutation_harness.py:857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:857)

成果物影響 1 行: ユーザーが job 終端確認・source 復元・hold削除を正しく行っても、表示された resume command は ledger schema mismatch で rc=2になり、保全した campaign を再開できない。

推奨対処: stop recordを `--out.orphan-stop.json` の別 fileへ出して通常 partial ledgerを維持するか、resume loaderに `partial_ledger` の厳格な unwrap契約を実装する。また exact request IDが無い場合の探索手順と、resume可能になる前提をstderrへ明示する。

# 所見 6: 列挙された consumer の schema・rc 互換性は保たれている

判定 (real/refuted): refuted

根拠 (file:line):

- `mutation_fanout.py` は shard rc=2を nonterminal とし、mergeせず rc=16で停止する。[mutation_fanout.py:1692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:1692)
- `mutation_fanout_contract.py` は wrapper/child rcが `{0,1}` 以外なら拒否し、orphan-stop schemaを terminal ledgerとして受理しない。[mutation_fanout_contract.py:1288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout_contract.py:1288)
- `dev_wave_wait.py` は acceptance child rcが0/1以外なら拒否し、red checker rc=2も拒否する。[dev_wave_wait.py:3116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/dev_wave_wait.py:3116)、[dev_wave_wait.py:2740](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/dev_wave_wait.py:2740)
- `dev_wave_land.py` は権威ある acceptance receiptで checker rc=0を要求するため、停止 runは landされない。[dev_wave_land.py:601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/dev_wave_land.py:601)
- `run_tests.py` と `check_ai_provenance.py` は dispatcher rc=16をそのまま返す。[run_tests.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/run_tests.py:940)、[check_ai_provenance.py:1767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_ai_provenance.py:1767)
- `floor_liveness.py` は変更されていない qstat parserだけを使用し、`queue_state.py` は `DEFAULT_QUEUE` だけをimportする。[floor_liveness.py:340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/campaign/floor_liveness.py:340)、[queue_state.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/campaign/queue_state.py:38)
- productionで dispatch rootを走査・削除する箇所は、harness inventory、fan-out orphan evidence scan、worktree evidence移動、acceptanceの2 cleanupである。新 fileは inventoryではdirectoryでないため数えられず、fan-outでは`receipt-fallback-*`でないためreceipt扱いされない。[mutation_harness.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1440)、[mutation_fanout.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:1014)

成果物影響 1 行: 新 schemaを既存 terminal ledgerやreceiptとして誤受理する経路はなく、停止成果物はmerge・acceptance・landへ流入しない。

推奨対処: 現在の厳格拒否は維持する。ただし次所見の運用可視性は別途補う。

# 所見 7: fan-out では hold 理由と回復用 ID が上位へ十分に出ない

判定 (real/refuted): real

根拠 (file:line):

- fan-out のdispatch root走査はsubmission directoryとreceiptだけを読み、`orphan-hold.json`を無視する。[mutation_fanout.py:1014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:1014)
- holdにはreceipt保存失敗時にも使える `request_id`、`job_name`、`submission_dir` がある。[dispatch_compute.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1026)
- nonterminal shardの上位 failureは一般的な `"nonterminal shard rc"` で、top-level stderrへ orphan理由を出さない。[mutation_fanout.py:1720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:1720)
- driver reportはpreserved containerを列挙するが、hold pathや理由は含めない。[mutation_fanout.py:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:1386)

成果物影響 1 行: fan-outは安全に停止するが、operatorがlauncher logとcontainer内部を掘らない限り orphan-hold と対象requestを特定できず、復旧が長期停滞する。

推奨対処: holdを取消権威にはせず、read-only診断としてdriver reportへ `shard_id`、hold path、request ID、submission dir、hold_errorを転記し、top-level stderrにも要約する。

# 所見 8: repo scanには掛からないが、受入中のholdは受入全体を止めてprobeを残す

判定 (real/refuted): refuted

根拠 (file:line):

- `output/pegasus-dispatch/` 全体がignoreされる。[.gitignore:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/.gitignore:26) `git check-ignore`でも新pathがこの規則に一致する。
- `ruleops.py` のoutput scanは `output/insights/**` に限定され、`check_docs.py`もliving docsとinsightsを対象にする。[ruleops.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/ruleops.py:72)、[check_docs.py:1332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_docs.py:1332)
- 通常のuntracked検出はignored fileを含まないため、run_tests/provenance/landのclean gateを直接赤くしない。
- 受入全走自身でholdが立てば child rc=16となりwaiterが拒否する。非帰属赤probe中ならdispatch artifactとprobe worktreeの両方が保全され、checker rc=2となる。[check_acceptance_reds.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:396)、[check_acceptance_reds.py:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/check_acceptance_reds.py:833)
- waiterは通常失敗時にleaseをreleaseする。[dev_wave_wait.py:2402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/dev_wave_wait.py:2402)

成果物影響 1 行: holdはrepo scanを汚さない一方、受入receiptは発行されず、保存されたprobe worktreeを人手処理するまでlandできないという意図したfail-closedになる。

推奨対処: scan除外を追加する必要はない。受入失敗時にprobe pathとhold pathがacceptance logに残ることを統合テストで固定する。

# 所見 9: runbook更新が必要

判定 (real/refuted): real

根拠 (file:line):

- 現行runbookはdispatch receiptとrc=16を説明するが、orphan hold、source復元停止、container保全、解除順序を記載していない。[pegasus-runbook.md:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/docs/pegasus-runbook.md:1315)
- mutation harnessの現行節はrunner argvだけである。[pegasus-runbook.md:1081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/docs/pegasus-runbook.md:1081)

書くべき運用事実:

- §7.0: `output/pegasus-dispatch/orphan-hold.json` はcreate-only latchでありlockではないこと、F47が表示上先行すること、成立時はscheduler command 0本でrc=16となること。
- §7.3: 受入全走またはred probeでholdが立つとreceiptが発行されず、probe worktreeとdispatch evidenceが残ること、leaseとprobe cleanupは別であること。
- §7.4: dispatch timeout／既存holdでharness rc=2、mutation sourceを残すこと、stop ledgerの場所、復旧順序、現状のresume可否。
- §7.5: fan-outではholdはshard checkout単位で、兄弟shardは完了まで走るがmergeしないこと、driver reportのpreserved containerを確認すること。
- §8: `qstat`で対象を確認 → 必要なら人手対処 → source復元 → clean/HEAD確認 → hold削除、の順序。手動qdelはF47も武装すること。
- §8または§7冒頭: 保護範囲は`dispatch_compute`経由のtests/provenanceとmutation/acceptance consumerに限り、直接submit scripts、`patchharness.py`、local runner、共有lifecycle lockはscope外であること。

内部helper名、payloadの全field一覧、テスト名はrunbookへ書かなくてよい。

成果物影響 1 行: 運用正本が無いままでは安全な停止後に誤ったhold削除、無効なresume、F47との二重ラッチ見落としが起きる。

推奨対処: 段7で上記各節を更新する。ただし所見1と5はdocsだけでは解消しないため、コード修正後の実挙動を正本化する。

# 所見 10: false positiveの頻度と停止範囲は裁定内だが、回復不能化は裁定外

判定 (real/refuted): refuted

根拠 (file:line):

- 通常完走はcleanup/latchを呼ばずchild rcを返すため、正常完走だけならhold発生率は0である。[dispatch_compute.py:1878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1878)
- qdelは非0または例外なら無条件に`job_may_remain=True`となるため、QUE/HLD観測直後に自然終了してqdelが「対象なし」を返す競合ではfalse positiveとなる。[dispatch_compute.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1107)
- dispatch-mode timeoutはqsub到達の証拠がなくても100% holdとなる。[mutation_harness.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:261)
- 一度立てば同じcheckoutのtests/provenance dispatchは全て停止するが、rootはrepoごとである。[dispatch_compute.py:1417](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1417) fan-out shardも別checkout/rootを持つ。[mutation_fanout.py:597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout.py:597)
- local実行、別worktree、直接submit scriptsは停止対象外である。

定量頻度は静的コードから推定できないが、事象条件付きでは「通常完走0%、dispatch timeout 100%、qdel非0/例外100%、その後の同一root dispatch 100%拒否」である。停止範囲自体は裁定の非対称安全性に収まる。

成果物影響 1 行: false positiveは正しく成果物生成を止めるため誤受理を生まないが、所見5のresume不整合が残ると一時停止ではなくcampaign再作成へ実害が拡大する。

推奨対処: 署名は緩めない。発生率をdispatch receiptのreason別件数として段7へ記録し、回復可能性と診断可視性だけを修正する。

## 総括

最重は、hold書込み失敗をharnessが検出せずsourceを復元できるため、裁定L1.4の安全保証が欠ける点である。  
次に、orphan-stopが通常ledgerを上書きする一方でwrapperが実行不能なresume commandを案内している。  
事前登録P1は5つの独立detectorを一変異にまとめており、単一理由性と完全集合を満たさない。  
consumerは概ねfail-closedだが、fan-out上位reportがhold理由とrequest IDを十分に露出しない。  
既知の焦点test赤はgateを緩めず、2回のdispatchへ別output rootを与えて直すべきである。