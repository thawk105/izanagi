## 実装した変更

- C1 — [test_p3_autonomous_workload_trial.py:164](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:164): helper に optional `binding=None` を追加し、`build_v2_lock` へ素通し。
- C1 — [test_p3_autonomous_workload_trial.py:1858](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1858): recorded-head binding を32反復前に1回だけ計算。
- C2 — [test_p3_autonomous_workload_trial.py:56](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:56): module-level の並行度定数を1箇所に追加。初期値は4。
- C2 — [test_p3_autonomous_workload_trial.py:1860](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1860): 全 per-wire assert を保持した局所 worker を実装。
- C2 — [test_p3_autonomous_workload_trial.py:1959](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1959): `ThreadPoolExecutor` と ordered `executor.map(run_wire, range(32))` へ変更。集約は main thread のみ。
- C3 — [test_p3_autonomous_workload_trial.py:1970](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1970): 4 role、trusted variants、secret records の32件検査を横断 assert 直前に追加。
- C4 — [test_p3_autonomous_workload_trial.py:1942](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1942): worker が wire を返し、集約時に入力順との一致を検査。
- C5 — [test_p3_autonomous_workload_trial.py:1847](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:1847): 被覆命題、逐次スケジュールを対象外とする裁定、その損失を5行の docstring に記載。

## 実走した nodeid と結果

- `orchestrator/tests/test_p3_autonomous_workload_trial.py` 全266 nodeid。対象 nodeid を含め `266 passed in 149.24s`。
- `orchestrator/tests/test_p3_build_authority_cli.py` 自走 harness 全19 test 関数。`19/19 PASS`。AST consumer の `::test_tracked_python_coder_authority_ast_closure_is_exact` を含む。
- `orchestrator/tests/test_reflux_originless_compatibility.py` 全2 nodeid。pytest専用 allowlist のためインプロセス `pytest.main` harness を使用し、`2 passed in 57.60s`。
- `git diff --check` も成功。

## 現行の受理・拒否挙動

変更前後とも、32 wire の各 trial は `do_build=False` で実際の no-build rejection、WAL、campaign lock、certified admission、critic 再構築を通る。

固定 checkout では、32回再計算していた recorded-head binding と今回共有する binding の内容は同一。32 trial、64回の real admission、64回の live closure captureはいずれも維持している。production file と受理集合は変更していない。

## 波及

- 所有外 caller: [test_p3_autonomous_workload_trial.py:3432](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2383-author/orchestrator/tests/test_p3_autonomous_workload_trial.py:3432) は新引数を省略。既定値 `None` により従来どおり binding を内部計算する。
- 共有 fixture: `campaign_lock_test_support.py` は無変更。既存の `build_v2_campaign_lock(..., binding=None)` 契約を利用した。
- `_WireRecordingFixture`、`_critic_relation_equivalent`、`_canonical_without_json_pointers`、`_AUDITOR_D_POINTERS` は無変更。
- Consumer: `test_p3_build_authority_cli.py` のAST走査と、`test_reflux_originless_compatibility.py` の対象module importを全件実走済み。
- production 配下、docs、その他ファイルは無変更。作業ツリーの変更は指定テスト1本だけ。

## 期待赤

無し。

## 総括

C1〜C5を指定テスト1本へ実装し、焦点集合3ファイルはすべて緑です。  
逐次時だけ wire を混ぜる欠陥を決定的に捕捉できなくなる損失はdocstringへ明記しました。  
並行度は親が実測できる単一定数として初期値4にしています。  
受入 wall の短縮は主張していません。commit、push、branch操作は行っていません。