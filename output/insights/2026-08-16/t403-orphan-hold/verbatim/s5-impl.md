## 1. 変更した file・関数と各層の実装

- `tools/pegasus/dispatch_compute.py`
  - L1.1: `_orphan_hold_required`、`_latch_orphan_hold` を追加。`job_may_remain is True` のみを署名とし、`request-absent`／`terminal-history-conflict` も hold 対象化。
  - L1.2: `_dispatch_impl` で qsub 起動前から結果未観測状態を追跡。未観測終了時は `_discover_request_id` の `qstat` のみ実行し、qdel せず hold を作成。rc 非0を観測した場合は作成しない。
  - L1.3: F47 検査直後、nonce 作成・scheduler command より前に hold を fail-closed 検査。
  - L1.4: hold は `O_EXCL` による create-only。書込み失敗は `qdel.hold_error` と stderr に記録。
  - 状態別復旧手順、手動 qdel による F47 武装の注意を hold record に格納。
- `tools/mutation_harness.py`
  - L2: `OrphanHoldStop`、timeout hold writer、停止 ledger writerを追加。
  - collection／baseline／mutation runner の前後、および mutation `finally` で hold を検査。
  - dispatch timeout は harness 自身が hold を create-only で作成し、変異 bytesを残して rc=2。後続変異へ進まない。
  - timeout でない `PARSE_ERROR` は従来どおり復元し、孤児条件にしない。
  - signal unwind 中も hold があれば復元を見送り、停止記録後に signal を再送出。
- `tools/mutation_worktree.py`
  - L3: `_should_teardown(..., orphan_hold)` を追加。
  - 通常経路、plan-only、例外 fallback の全てで container 内 hold を検査。判定不能も保全側。
  - hold 時は wrapper receipt に `failure="orphan-hold"`、teardown 未試行、evidence 未移動を記録。
- `tools/check_acceptance_reds.py`
  - L4: `_cleanup_dispatch_artifacts` と `_cleanup_probe` の先頭で hold を検査。
  - hold 時は `rmtree`、`rmdir`、`git worktree remove --force` を一切実行せず `InvalidInput`。
- 対応する指定4 test fileへ裁定の必須ケースを追加。新規 file・改名はありません。

`_best_effort_qdel` の定義外呼出しは従来どおり `_fresh_qstat_gated_qdel` 内の1箇所だけです。

## 2. 変更前後の受理・拒否挙動

- `_dispatch_impl`
  - 変更前: F47だけを投入前拒否。qsub return未観測時は `active=False` のため cleanupなし。
  - 変更後: F47の受理集合・文言・優先順位は維持。その直後に hold を検査し、成立時は scheduler command 0本で rc=16。qsub未観測時は discoveryだけ行いhold、rc非0観測時は従来どおりholdなし。
- `claim_cleanup_once`
  - 変更前: fresh gate／qdel receiptを返すだけ。
  - 変更後:同じ receipt に対して `job_may_remain is True` なら理由にかかわらずhold。qdel成功でFalseなら従来どおり許可。
- `_collect_expected_nodes`／`_baseline`
  - 変更前: holdを見ずrunnerを起動。
  - 変更後: dispatch modeだけ起動前後にhold／timeoutを拒否。local modeは不変。
- `_apply_mutation`
  - 変更前:結果やtimeoutにかかわらず必ず復元。
  - 変更後:孤児条件では復元・pycache cleanup・original検証を行わず変異を保全。それ以外は従来どおり復元。
- `mutation_harness.main`
  - 変更前:通常ledger v4を更新し、`HarnessError` は上位でrc=2。
  - 変更後:孤児条件だけ専用非終端停止ledgerを書いてrc=2。通常ledger v4のschemaと通常終了は不変。
- `_should_teardown`／`mutation_worktree.main`
  - 変更前:plan-only、またはchild rc 0/1かつterminalならteardown。
  - 変更後:hold不在という明示条件を追加。holdなし正例は不変。
- `_cleanup_dispatch_artifacts`／`_cleanup_probe`
  - 変更前:検証後に成果物・probeを削除。
  - 変更後:hold存在または判定不能時だけ削除を拒否。holdなし正例は不変。

## 3. 実走した test node と rc

pytest nodeは実走できませんでした。以下はいずれも test本体到達前のrc=16です。

- `python3 tools/run_tests.py orchestrator/tests/test_pegasus_dispatch_compute.py`
- 署名の単一nodeid走
- 指定4 test fileの `--collect-only` 走

原因はworkspace-write sandboxから admission台帳 `/run/user/31609/izanagi-admission` を更新できず自動dispatchへ倒れ、そのdispatchも `qstat -Q preflight rc=1` になったためです。`--force-dispatch` は使用していません。

裁定の必須ケースに対応する新設nodeはすべて「実装済み・未実走」です。既存4 test file全体と、制約meta-test `test_best_effort_qdel_production_caller_is_only_fresh_gate` も未実走です。新規・改名test fileは0件のため、file集合列挙meta-testの追加発火はありません。

実走済み検査:

- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- 8 fileのAST parse、NFC、`git diff --check`: rc=0

## 4. 所有外 caller・fixture・consumer testへの波及可能性

- dispatch caller:
  - `tools/run_tests.py`
  - `tools/check_ai_provenance.py`
- dispatch parser／定数consumer:
  - `orchestrator/campaign/floor_liveness.py`
  - `orchestrator/campaign/queue_state.py`
- mutation consumer:
  - `tools/mutation_fanout.py`
  - `tools/mutation_fanout_contract.py`
- acceptance consumer:
  - `tools/dev_wave_wait.py`
  - `tools/dev_wave_land.py`
- 共有fixture:
  - dispatch `_Scheduler`
  - harness一時git repo fixture
  - worktree fake harness／repository fixture
  - acceptance `committed_repo`
- 波及候補test:
  - `test_run_tests_preflight.py`
  - `test_check_ai_provenance.py`
  - `test_mutation_fanout.py`
  - `test_mutation_fanout_contract.py`
  - `test_dev_wave_land.py`
  - `test_hold_inventory.py`
  - `test_queue_state.py`
  - `test_site_policy.py`
  - `test_pytest_failure_digest.py`
  - `test_check_docs.py`

## 5. 裁定に対して実装できなかった項目

plan v2の実装項目に未実装はありません。pytest実走のみ上記sandbox／scheduler条件で未完了です。

裁定でscope外とされた共有lifecycle lock、直接submit script群、`patchharness.py`、local runner停止、自動解除・tombstoneは実装していません。

## 総括

指定8 fileだけを変更し、docs編集・commitは行っていません。  
qdel実行経路は増やさず、既存呼出し1箇所を維持しています。  
dispatch timeout／hold時は投入・復元・teardown・acceptance cleanupをfail-closedにしました。  
通常ledger v4、wrapper v1、dispatch receipt v2は不変です。  
静的検査はrc=0ですが、pytestは環境上test本体へ到達できず、実装済み・未実走です。