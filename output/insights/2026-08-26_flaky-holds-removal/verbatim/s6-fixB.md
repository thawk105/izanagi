## 総括

- FIX-B1 と FIX-B2 を実装し、静的検査まで完了した。
- pytest は未実走のため、両 must-fix の状態は `unverified`。
- 変更は指定された 2 file の unstaged 差分だけ。`git add`、`git commit` は未実施。
- thread ごとに独立した偽 clock を注入し、全協調 watchdog を 30 秒へ統一した。
- summary は synthetic 2 行による `2/1/1` を復元した。
- 性質 assertion、`_EMPTY_REGISTRY_SHA256`、live registry は変更していない。

## FIX-B1 の実装 (偽 clock で協調が壊れないことの静的確認を含む)

各 `invoke()` 内で `_Clock()` を生成し、`clock=clock` と `sleep=clock.sleep` を渡した。`invoke()` は各 thread で別々に呼ばれるため、thread-safe でない `_Clock` は共有されない。

静的確認結果は次のとおり。

- `_acquire_control_lock()` は `fcntl.flock(..., LOCK_EX)` による blocking lock であり、poll loop や注入 clock を使用しない。
- first thread の qsub 到達は `qsub_entered`、first の再開は `release_qsub` が制御する。
- second thread の lock 取得開始は `second_acquire_entered` が通知する。通知後に blocking `flock` へ入るため、main thread は first を解放できる。
- 偽 sleep が進めるのは `_Scheduler` の `QUE -> RUN -> DONE` などの poll 状態だけであり、thread 間の因果順序には使われない。
- したがって偽 clock 注入で assertion の成立条件は変わらないと判断した。

`poll_interval_s` は同 file の標準慣行である 5 秒へ戻した。偽 sleep なので実 wall time の床にはならず、1 秒という対象 test 固有の scheduler 挙動を残す理由がないため。

module-level の `_THREAD_COORDINATION_WATCHDOG_S = 30.0` に、3 種の Event の全 wait と両 test の join を統一した。comment には以下を記録した。

- hang 回収用であり latency 合否予算ではない。
- 注入前の決定的な床は 10.015 秒。
- 母集合は計算ノードでの同 file 単独走 3 回で、受入全走と同一 regime ではない。
- 48 並列では 5 秒の thread 起動期限を性質とみなせない。
- 注入後の実所要は親が段 6 で確定する。

`results`、qsub 回数、`submission-disabled.json`、control lock file、`_orphan_hold_present` の全 assertion は残している。

## FIX-B2 の実装 (digest の計算方法を含む)

`_HELD_NODE` に加え、`_SIBLING_NODE` を key とする 2 行目を追加した。2 行目は `_synthetic_valid_hold()` を基に、`known_failure_node_ids` だけを `_SIBLING_NODE` へ置換している。live registry は参照していない。

collected と skipped は `_HELD_NODE` のみなので、期待値を次へ復元した。

- registered: 2
- matched: 1
- skipped: 1

digest は実際の 2-row mapping を `REG.flaky_test_hold_registry_sha256()` へ渡して再計算した。この関数は node ID 順に payload を並べ、`ensure_ascii=True`、`sort_keys=True`、空白なし区切りの canonical JSON を作り、その ASCII bytes の SHA-256 を計算する。

計算結果は `ed29898f01a3d4693bceae000423b429ea44141e51ea18d1ad5b2dcc8be3c594`。実装後にも同じ mapping から再計算して一致を assertion で確認した。`_EMPTY_REGISTRY_SHA256` は変更していない。

## 変更した file と行

- [test_pegasus_dispatch_compute.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:32)
  - watchdog 定数と根拠 comment
  - [1 個目の対象 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:5384)
  - [2 個目の対象 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_pegasus_dispatch_compute.py:5443)
- [test_flaky_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/flaky-holds-b/orchestrator/tests/test_flaky_test_holds_contract.py:887)
  - synthetic 2-row payload、`2/1/1`、新 digest

新設・改名した test はないため、追加で登録すべき exact-node meta-test はない。

## 実走したか (nodeid と範囲、または「実装済み・未実走」)

実装済み・未実走。

許可外の `output/` や repository 外への test artifact 書込みを避けるため、pytest と `tools/run_tests.py` は起動していない。したがって緑は主張しない。

read-only の静的検査として以下を実施した。

- 変更 2 file の `ast.parse`
- `git diff --check`
- 2-row registry digest の再計算と golden 一致確認
- working-tree 差分が許可された 2 file だけであることの確認

## 各 must-fix の状態 (closed / unverified / not-done)

| must-fix | 状態 | 理由 |
|---|---|---|
| FIX-B1 | `unverified` | 実装と静的協調確認は完了したが、対象 nodeid は未実走 |
| FIX-B2 | `unverified` | `2/1/1` と digest の静的確認は完了したが、対象 nodeid は未実走 |

## 所有外への波及可能性

- production の `tools/pegasus/dispatch_compute.py` は変更していない。影響は対象 test の注入引数だけ。
- `orchestrator/tests/conftest.py::pytest_sessionfinish` が FIX-B2 の consumer。monkeypatch した synthetic mapping だけで検査するため live registry への影響はない。
- `orchestrator/tests/flaky_test_holds.py` は段 5 の空 registry のままで、今回は触れていない。
- acceptance duration ledger には対象 node の旧値 `10.0` が残る。親が段 7 で再計測後に扱う必要がある。
- failure ledger、再発分類手順、設計メモは親所有であり未変更。
- snapshot helper の caller は `test_s8b_oracle_driver.py`、`test_real_repo_serialization.py`、`test_s8b_floor_campaign.py` に広がるが、本変更から直接の呼出し関係はない。
- 既存の staged 差分は保持したまま、今回の変更は unstaged。index 操作はしていない。

## 期待赤の finding 集合

fix 子 A の tracked-path 可視化が未 land のため、次は既知の期待赤。

- `test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary`
  - `output/env/pegasus/silo_ladder_rung1/job-staging/` 配下の tracked file 418 件を、現 helper が規則由来 prefix 配下として fail-closed にする。
- 同じ real-repository snapshot helper を通る oracle、serialization、floor campaign の caller も、目的の assertion 前に同じ tracked-descendant 拒否へ到達する可能性がある。
- fix 子 A の process 削減が未 land である点は性能 risk だが、それ自体を assertion の期待赤とは分類しない。

上記以外、特に今回の FIX-B1 2 node と FIX-B2 1 node の赤は回帰として扱う。

## 未完・未確認

- 対象 3 nodeid の pytest 実走
- 48 並列 regime での Event watchdog 確認
- 偽 clock 注入後の実所要の親実測
- acceptance duration ledger の更新
- fix 子 A の tracked-path 可視化と process 削減の land
- 親所有の docs closure と受入全走確認