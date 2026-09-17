## 実装した変更 (file:line と要旨)

- [probe.py:1891](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/tools/pegasus/probes/t316_sandbox_backend_probe.py:1891)：manifest取得前に`ccbench_dir`・`dependency_prefix`・`source_dirs`を記録。成功時の上書き、失敗時のargv=`None`を維持。
- [test.py:2215](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/orchestrator/tests/test_t316_sandbox_probe.py:2215)：成功時の入力3項とobserverの引数との一致を追加。
- [test.py:2291](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2654-impl/orchestrator/tests/test_t316_sandbox_probe.py:2291)：configure／target失敗時の入力3項を検査。

既存行の変更・削除なし。受理集合、failure_stage、verdict、集約処理は不変です。

## 変異 anchor 行の保持 (段 4 の old 行が現物に残っているかの逐語照合)

M0〜M12（M6b・M7bを含む）のold行は現物との静的照合で保持を確認しました。特に以下はインデント込みで維持しています。

```python
    if not inside and failure_stage is None:
                    dependency_prefix=str(prefix),
    if failure_stage is None:
```

最後の行は引き続き関門呼出し直前です。

## 実走した test (nodeid・範囲・結果) と実走不能の node

**pytest実走0件。実装済み・未実走です。**

Pegasusログイン上のrunnerに禁止された`qstat`へ進む経路があるため、起動していません。対象3 nodeとも未実走で、node固有の実行不能は未確認です。

Python 3.10互換AST検査（2ファイル）と`git diff --check`は通過しました。

## 所有外 caller・共有 fixture・consumer test への波及 (静的列挙)

- `orchestrator`／`tools`検索では`_execute_ccbench_build`の所有外callerなし。
- 共有helper、conftest、fixture、PBS、docs、policyは今回未編集。
- consumer候補：`test_official_perf_closure.py`、`test_hooks.py`、`test_acceptance_schedule_order.py`、`test_real_repo_serialization.py`、`test_ccbench_spawn_sites.py`、`test_plain_runner_coverage.py`。今回未実走。

## 未完・限界

manifest例外でも入力が残る配置は静的確認のみ。変異実走・計算ノード受入は未実施です。commit・PBS操作はしていません。

## 総括

親の再取り込み後：`orchestrator/tests/test_t316_sandbox_probe.py::test_s6_live_offline_source_paths_and_prepare_order`
同ファイル：`test_s6_prepare_failure_stops_before_gate[configure]`
同ファイル：`test_s6_prepare_failure_stops_before_gate[target]`