## 1. must-fix 1〜6 の対応表

実走不能時は `closed` としない契約に従い、すべて `partial` としています。`regressed` はありません。

| 項目 | 判定 | 根拠 |
|---|---|---|
| must-fix 1 | `partial` | receipt の `qdel.job_may_remain` / `hold_error` を result へ投影し、harness の孤児条件へ追加しました。[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1370)、[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:264)。dispatcher→harness 統合テストも追加済みですが未実走です。[test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:893) |
| must-fix 2 | `partial` | `qsub_result_unknown` では hold を discovery より先に作成します。[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1906)。ただし裁定どおり、SIGKILL と hold 到達前・discovery 中の再 signal の窓は残ります。 |
| must-fix 3 | `partial` | 元例外と保全検証例外を構造化 field に保存し、通常例外では `raise stop from exc` としました。[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1872)、[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2421)。記録テストは未実走です。 |
| must-fix 4 | `partial` | 通常 ledger を維持し、停止記録を `<out>.orphan-stop.json` へ分離しました。[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2407)。worktree の案内も復旧順序を先に表示します。[mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1044)。未実走です。 |
| must-fix 5 | `partial` | cleanup 呼出し配線、4 consumer の `lstat` 判定不能、dispatcher hold 書込み失敗、acceptance の2 cleanup gateを固定するテストを追加しました。代表根拠は [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2056)、[test_check_acceptance_reds.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_check_acceptance_reds.py:1752)。変異本走と期待 node 再導出は未実施です。 |
| must-fix 6 | `partial` | 対象テストの2回の `_dispatch` に別 output root を与えました。assert 行は変更していません。[test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:2621)。未実走です。 |

## 2. 変更した file と関数、実装内容

fix 差分では7 fileを追加修正しました。`tools/check_acceptance_reds.py` は段5実装を維持し、段6では対応テストだけを追加しています。

- `tools/pegasus/dispatch_compute.py`
  - `_dispatch_impl`: qsub未観測時の hold を discovery より前へ移動。
  - infra receipt の保存行を出力し、harness が production consoleからreceiptを取得可能にしました。
- `tools/mutation_harness.py`
  - `OrphanHoldStop`: `origin_error_*`、`verification_error_*` を追加。
  - `_read_dispatch_stdout`: receiptの孤児署名をresultへ投影。
  - `_dispatch_orphan_stop`: timeoutに加えてreceipt署名を孤児条件化。
  - `_apply_mutation`: 元例外とfinally検証例外を保持。
  - `_orphan_stop_path`、`_write_orphan_stop_ledger`、`main`: 停止sidecarへ分離し、`ledger_path`だけで通常ledgerを参照。
- `tools/mutation_worktree.py`
  - `_print_preserved_resume` と各呼出し: hold時の復旧順序と、hold解除後のみresume可能である旨を表示。
- 指定4 test file
  - M10〜M12、4 consumerの判定不能、例外保存、sidecar、案内順序、MF6 root隔離を固定。

`qdel` production callerは従来どおり `_fresh_qstat_gated_qdel` 内の1箇所だけです。[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1332)

## 3. 触った各関数の変更前後の受理・拒否挙動

| 関数 | 変更前 | 変更後 |
|---|---|---|
| `_dispatch_impl` | qsub結果未観測時、discovery完了後にhold。infra receipt pathをconsoleへ出さない | holdを先にcreate-onlyで作成し、その後request IDをreceiptへ追記。qdel経路は増加なし |
| `_read_dispatch_stdout` | receiptのpytest artifactだけをresultへ渡す | artifact検証が後段で失敗しても、権威ある`job_may_remain`と`hold_error`をresultへ残す |
| `_dispatch_orphan_stop` | dispatch timeoutまたはhold file存在だけを拒否 | 上記にreceipt由来の`job_may_remain is True`または`hold_error is not None`を追加。hold不在ならharnessがcreate-only作成 |
| `_apply_mutation` | finallyのstopや検証例外が元のrunner/harness例外を置換し得る | 元例外と検証例外をstopへ併記し、変異bytesを保持したまま停止 |
| `_write_orphan_stop_ledger` / `main` | `--out`を停止schemaで上書きし、通常ledgerを`partial_ledger`へ埋込み | `<out>.orphan-stop.json`へ停止記録。通常ledger v4は維持し、停止記録は`ledger_path`で参照 |
| `_print_preserved_resume` | container保持後すぐresume commandを表示 | hold時は復旧順序を先に表示し、hold解除後だけresume可能と明示 |
| MF6 test fixture | 独立2事例が同じrootを共有 | `trusted` / `untrusted` rootへ隔離。assertは不変 |

通常完走、local runner、非timeout `PARSE_ERROR`、F47の条件・payload・文言・優先順位、通常ledger v4、wrapper v1、dispatch receipt v2は変更していません。

## 4. 実走した test node と rc

以下はすべて `python3 tools/run_tests.py ...`、`--force-dispatch`なしです。いずれも test本体到達前の `qstat -Q preflight rc=1` により、コマンドrc=16でした。

| 範囲 | 指定node | rc |
|---|---:|---:|
| dispatch焦点 | cleanup配線、dispatch lstat、qsub未観測、MF6の4 node | 16 |
| harness焦点 | hold書込み失敗統合、例外保存、harness lstat、timeout sidecarの4 node | 16 |
| worktree焦点 | hold保全、worktree lstat、plan-only fallbackの3 selector | 16 |
| acceptance焦点 | artifact lstat、artifact hold、probe holdの3 node | 16 |

したがって全nodeが「実装済み・未実走」です。緑とは報告しません。

実走済み静的検査:

- AST parse、NFC、`git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- `python3 -m orchestrator.campaign.queue_state`: rc=0、queue状態は観測不能

## 5. 波及可能性の静的列挙

- dispatch caller:
  - `tools/run_tests.py`
  - `tools/check_ai_provenance.py`
- dispatch parser・定数consumer:
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
  - harnessの一時Git repo
  - worktree fake harness/repository
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

infra receipt保存行が新たにconsoleへ出るため、consoleを独自解析する所有外callerには波及可能性があります。既存の正規consumerは完全一致するreceipt行を利用または通常出力として扱う構造です。

## 6. 実装できなかった項目と理由

- pytest本体の実走はPegasus preflight rc=16のため実施できませんでした。親による実測が必要です。
- M10〜M12・P1a〜P1eの実際の変異spec更新と期待node完全集合の再導出は、最終commit後に親がJUnitから行う契約です。許可8 file内に当該specはないため編集していません。
- must-fix 2のSIGKILL・discovery中の再 signal・hold到達前終了は意図的に未解決です。この窓を閉じたとは主張しません。
- docs編集、commit、`tools/mutation_fanout.py`編集は行っていません。

## 総括

must-fix 1〜6のコード・テスト差分を指定8 file内へ収めました。  
qdel経路、F47、既存schema、通常受理集合は広げていません。  
通常ledgerとorphan-stopを分離し、例外原因と変異bytesを保全します。  
静的検査はrc=0ですが、焦点testは全てtest本体前のrc=16で未実走です。  
must-fix 2のSIGKILL・再 signal残余はscope外のまま残ります。