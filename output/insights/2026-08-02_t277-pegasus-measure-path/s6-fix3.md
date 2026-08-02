原因 sink は `screening-candidate` で、修正済みです。コードとテストのみ編集し、docs 編集・commit は行っていません。

### 原因と修正

原因は [screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/screening_driver.py:128) の `evaluate_candidate()` でした。

全 sink の追跡結果:

| sink | 防壁位置／結果 |
|---|---|
| p3-loop | `do_build` 後、layout 作成前 |
| sort-loop | `do_build` 後、layout 作成前 |
| coverage-build | build dir／subprocess 前 |
| coverage-run | trace 作成前 |
| coverage-trace | temp dir 作成前 |
| frequency-run | temp dir 作成前 |
| sort-sweep | quarantine／WAL 前 |
| trigger-sweep | quarantine／WAL 前 |
| backoff-screening | source digest／campaign 作成前 |
| screening-candidate | **防壁欠落。WAL repair が先行** |

`screening-candidate` は拒否前に `ident.ensure_resumable_wal()` へ進み、`layout=None` から [wal.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/wal.py:625) の `layout.lock_file` で落ちていました。

修正後は [screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/screening_driver.py:139) で、実 evaluator の場合だけ COMPUTE 拒否を実施します。これは WAL repair/replay、campaign lock、layout/provenance 書込みより前です。

fake evaluator は `_REAL_EVALUATE` との identity が異なるため拒否せず、配線確認を継続できます。この正例を [test_screening_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_screening_driver.py:139) で COMPUTE と明示して固定しました。

### 恒真性と F1〜F10

防壁を削除すると、M14 behavioral テストの `screening-candidate` は再び `ensure_resumable_wal(None, None)` → `wal.read_lock()` → `AttributeError` となります。期待する `RuntimeError` ではないため同テストは赤くなり、防壁検査は恒真ではありません。

F1〜F3、F5〜F9 の実装面は未変更です。F4 は最初の副作用前の実 sink 拒否として閉鎖し、F10 の behavioral sink 集合・match・対象 sink は変更していません。fake evaluator の COMPUTE 正例のみ強化しました。

### 検査

通過した静的検査:

- `python3 -m py_compile`（変更2ファイル）
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

計算ノードへ次の nodeid を dispatch しました。

- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py::test_all_legacy_programmatic_measurement_sinks_reject_compute`
- `orchestrator/tests/test_screening_driver.py::test_evaluate_candidate_repairs_tail_before_replay_and_evaluate`

結果は `qstat -Q preflight rc=1`、runner `rc=16`。pytest 実走は0件で、緑は主張しません。

## 総括

- 原因は `screening_driver.evaluate_candidate` の先行 WAL repair でした。
- 実 evaluator の拒否を最初の副作用より前へ移しました。
- fake evaluator の COMPUTE 配線確認は維持しています。
- M14 は防壁削除で元の赤へ戻ることを静的確認しました。
- F1〜F10 に新たな静的回帰はありません。
- pytest は dispatch 障害により未実走です。