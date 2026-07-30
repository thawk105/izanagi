指定された所有範囲内で段6 fix を完了しました。commit はしていません。変更は [test_dev_waves_integration.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145-author/orchestrator/tests/test_dev_waves_integration.py:1215) のみです。

主な変更:

- 実 serve harness を独立 child process に隔離。
- 親に180秒の finite ceilingを設け、timeout を明示的な `INFRA_TIMEOUT` failureとして報告。
- timeout 時は `terminate → bounded wait → kill → reap`。強制 timeout control で child reap を確認。
- child の `PASS/FAIL/SKIP`、例外型・args表現・tracebackをJSONで返却。capability不足は親でpytest skipへ復元。
- thread の `daemon is True` をstart直前にassert。
- readersを「socket listener 1個＋厳密なint relay fd 1個」として検査。list/tupleと順序変更を許し、duplicate listenerを拒否。
- timeoutを `0 < timeout <= 0.25` に限定し、bool、None、非有限、0以下、上限超過を拒否。
- patch開始、shutdown/release、thread join、patch復元を単一`try/finally`に集約。primary exceptionの型・argsは変更せず、cleanupだけの失敗は元の型で送出。
- nodeの新設・改名、production、T-136/T-138契約、docs、output、submoduleの変更なし。

検査結果:

- `test_dev_waves_integration.py::test_short_alias_bind_probe_separates_capability_loss_from_regression`
  - 1 PASSED
- `test_dev_waves_integration.py::test_socket_roundtrip_works_beyond_108_byte_repository_path`
  - 1 SKIPPED
  - 理由: `sandbox does not permit AF_UNIX bind through /proc/self/fd`
  - childから構造化SKIPとtracebackが返ることを確認
- `test_dev_waves_isolation_contract.py`
  - 3 PASSED
- 追加control:
  - list/tuple、reader role、duplicate listener、timeout正負境界: PASS
  - 強制ceilingによる明示的`INFRA_TIMEOUT`とreap: PASS
- `python3 tools/check_codex_agents.py`: PASS
- `python3 tools/check_docs.py`: PASS
- `py_compile`、`git diff HEAD --check`: PASS

子の実走は親の全走を代替しません。現環境ではreal long-path roundtripがcapability不足でNOT_RUN相当のため、非skip `COMPLETED`、mutation matrix、統合後の全受入は親側に残ります。

静的な波及確認:

- 所有外caller: 新規helperの外部callerなし。既存nodeから親wrapper、child import entry、実harnessへ閉じています。
- 共有helper: `_isolated_process_environment`、`_temporary_repo`、`_supervisor`、`_request`、`_wait_terminal`、`_sandbox_permits_short_alias_bind`を利用しますが変更していません。
- consumer test: isolation contract meta-testがAST call graphと`xdist_group`を検査します。既存nodeidは維持しているため、runnerや選択済みfocused nodeへの名称波及はありません。
- Git状態は継承済みstage差分と今回差分により `MM orchestrator/tests/test_dev_waves_integration.py`。他ファイル・submodule差分はありません。

## 総括

- 変更: serve harnessをchild processへ隔離し、構造化結果、有限ceiling、確実なreap、reader/timeout/daemon/cleanup契約を実装。
- テスト: capability node 1 PASS、long-path node 1 SKIP、isolation meta-test 3 PASS、静的・境界control PASS。
- closed: 段6裁定のfix要件1〜7をコード上で反映。
- remaining: capabilityのある環境でのreal roundtrip、mutation matrix、親の統合全走。
- 残リスク: 現環境では実serve/thread/roundtrip経路がSKIPのため、real `COMPLETED`のgreenは未主張。