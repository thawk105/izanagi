## 変更前の挙動

runtime spool を `.pbs` ではなく `_BOUND_RELATIVE_PATHS[1]` の `.py` と比較していました。そのため先行関門を通過しても、正しい `.pbs` bytes の spool を拒否していました。

## 実装

- [probe 実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/tools/pegasus/probes/t316_sandbox_backend_probe.py:2290) に `_RUNTIME_PBS_RELATIVE_PATH` を追加し、tuple の3番目と比較対象から参照しました。tuple の値・順序、例外文言、6件の hash key は不変です。
- [テスト helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2503-pbs-binding/orchestrator/tests/test_t316_sandbox_probe.py:1406) と指定名の正例・負例を追加しました。Git 環境隔離、全 Git timeout、異なる5 bytes、repo 外 spool/nodefile、clean status を検査します。
- 編集は許可された2ファイルだけです。commit、add、stash、branch 操作は行っていません。

## 検査

すべて repo root から実走しました。

- `PYTHONPATH=. python3 orchestrator/tests/test_t316_sandbox_probe.py` — `rc=0`、全129 node green。
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_binds_runtime_spool_to_pbs`
  - `orchestrator/tests/test_t316_sandbox_probe.py::test_execution_binding_rejects_runtime_spool_matching_python_instead_of_pbs`
- `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py` — `rc=0`、全3 node green。
- `PYTHONPATH=. python3 orchestrator/tests/test_update_acceptance_duration_ledger.py` — `rc=0`、全24 node green。
- `PYTHONPATH=. python3 orchestrator/tests/test_acceptance_schedule_order.py` — `rc=0`、全79 node green、警告1件のみ。
- `PYTHONPATH=. python3 orchestrator/tests/test_pytest_collection_config.py` — `rc=0`、全76 node green。
- `git diff --check` — `rc=0`。

未実走は、計算ノード上の PBS 統合、M1〜M5 の変異 matrix、repository 全体の受入 suite です。

## 波及可能性

- caller: `main()` と `run_probe()` の既定 binding、および `.pbs` job body からの起動が新しい比較先を使用します。保証範囲は Python preflight 時点の spool と worktree `.pbs` の bytes 一致までです。
- fixture: `conftest.py` の site fixture は `probe.socket` を変更しないため、新規 helper が明示的に hostname を固定します。未知 duration は既存の既定 cost 処理に流れます。
- consumer: admission registry、driver ID、performance inventory、hooks registry、runbook 投影は `.py` hash や node 数の変化を観測し得ます。将来 receipt の `.py` hash は変わりますが key 集合は不変です。

## 総括

差分: runtime spool の比較先を名前付き `.pbs` 定数へ修正し、実 Git repo を使う正例・負例を追加しました。  
実走: 追加2 nodeを含む対象全129 nodeと、制約 meta-test全182 nodeが `rc=0` です。  
未実走: 計算ノード PBS 統合、変異 matrix、repository 全体受入です。  
波及: caller の比較結果と将来 receipt の `.py` hash に影響し、共有 fixture・hash key・例外文言は不変です。