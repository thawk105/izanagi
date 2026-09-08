## 性能文言の不変性の確認

- [driver 定数](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:65) の旧文言は変更していない。
- [_performance_artifact_identity](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:1747) は [1773 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:1773) で旧文言を exact 比較している。
- [plot consumer の定数](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/plotting/plot_t2187_adaptive_consts.py:41) と [344 行目の exact 比較](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/plotting/plot_t2187_adaptive_consts.py:344) も確認した。
- この文言を変えると凍結済み性能 artifact が両 consumer で拒否されるため、1 byte も変更していない。

## 実装した内容

- [t2187_adaptive_const_probe.py:68](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:68) に診断用 `DIAGNOSTIC_NOT_CERTIFIED` を追加した。
- [_artifact_contract_metadata](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:2761) が `backoff_trace` に応じて性能用・診断用文言を選ぶよう変更した。
- [payload 構築](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:3304) から共通の `not_certified` 代入を削除した。`kind` と `throughput_scope` の分岐方向は不変。
- [新規 mode-specific test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2042) で両文言を test-local literal と比較し、旧文言の性能 artifact が引き続き受理されることも確認した。
- [legacy v2 fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2018) も `probe.NOT_CERTIFIED` から旧文言の test-local literal へ変更した。

## 期待値を直した箇所

`_artifact_contract_metadata` の全呼び手を確認した。

- production caller: [main の payload 展開](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/tools/pegasus/probes/t2187_adaptive_const_probe.py:3305)。
- exact performance dict: [1968 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:1968) に旧性能文言を追加。
- exact diagnostic dict: [1982 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:1982) に新診断文言を追加。
- 新規 mode 別呼出し: [2053 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2053) と [2056 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2056)。
- counterfactual exact dict: [2154 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2154) に新診断文言を追加。
- [2162 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2162) と [2182 行目](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py:2182) は `counterfactual_preregistration` の不在だけを検査する既存 caller。exact dict 期待ではないため変更せず、assertion も緩めていない。

## 実走

- `python3 tools/run_tests.py orchestrator/tests/test_t2187_adaptive_const_probe.py`
  - rc=16。
  - `qstat -Q` preflight の dispatch infrastructure failure。child は未起動、test 実走 0 件。
- `PYTHONPATH=. python3 /work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-b/orchestrator/tests/test_t2187_adaptive_const_probe.py`
  - rc=0。
  - nodeid 範囲: `orchestrator/tests/test_t2187_adaptive_const_probe.py` 全体。
  - 118 passed、赤 0 件、293.00 秒。
  - 更新対象 4 node と新規 node を含む全 test を実走済み。

## 波及

- `tools/plotting/plot_t2187_adaptive_consts.py` は旧性能文言の exact consumer。文言・受理挙動とも不変。
- `orchestrator/tests/test_plot_t2187_adaptive_consts.py` は独立した旧文言 fixture を持つ consumer test。静的には影響なしだが、所有外のため未実走。
- `orchestrator/campaign/backoff_counterfactual_analysis.py` と対応 test は診断 artifact の consumer だが、`not_certified` を admission field に含めないため、凍結済み診断 artifact の受理集合は変わらない。
- `_certify_argv` など共有性能 fixture は `probe.NOT_CERTIFIED` を使うが、性能定数自体が不変なので影響なし。
- 変更前後とも、性能 artifact は旧文言だけを受理し、診断文言やその他の文言は拒否する。診断側は受理 gate を増やさず、将来生成される記録だけが trace-enabled の正しい文言へ変わる。
- schema、`kind`、`throughput_scope`、`headline_eligible`、counterfactual preregistration 条件は変更していない。

## 総括

- must-fix: なし。依頼された記録上の矛盾は修正済み。
- 対象 test file 全 118 件が fallback harness で緑。
- 未解決点は `tools/run_tests.py` の外部 dispatch 障害 rc=16 のみ。実 test は指定 fallback で完走済み。
- 所有された 2 ファイル以外は編集していない。docs、commit、staging、branch 操作も行っていない。