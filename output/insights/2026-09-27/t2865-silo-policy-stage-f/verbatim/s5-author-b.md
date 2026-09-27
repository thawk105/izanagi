## 変更 file と要点 (file:line)

- [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-b/tools/pegasus/p3_s4_loop_pegasus.sh:227): 方策 mode の値域・排他・proposal 条件を追加。保全 root 検査、方策 pin 照合、receipt 作成後の driver 呼出しを追加した。
- [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-b/orchestrator/tests/test_p3_s4_loop_job_contract.py:547): 既存 driver の件数照合を module 名の境界まで精密化。方策 mode の実 shell harness 検査を追加した。

## interface の実装 (interface.md §2 との対応)

`stock|pair|replay` の argv、方策 mode 専用の短縮 pin 解決、Python import、保全 root、bench lock、driver rc の伝播を実装した。driver は前処理と masstree receipt の後に 1 回呼ぶ。既存 mode の pin 照合と driver argv は維持した。

## test の実走

`python3 tools/run_tests.py -n 1 orchestrator/tests/test_p3_s4_loop_job_contract.py` は dispatch の `qstat -Q` preflight で **rc=16**。対象 nodeid は全範囲だが、実走 **0 件**（passed 0 / failed 0）。実装済み・未実走。

`python3 -m py_compile` と `git diff --check` は成功。`bash -n` は login 側 guard に拒否されたため未実走。

## 変異 M-F7・M-F8 の fixture と単一理由性の見立て

M-F7 は模擬 CCBench HEAD を方策 pin の commit に固定した。旧 pin に戻すと pin 照合で driver 前に拒否される。M-F8 は保全 root の欠落・相対・repo 内を入力し、driver が呼ばれず rc=2 となることを検査する。変異の実走による単一理由性の確認は残る。

## 所有外への波及と、変えなかった既存 mode の受理・拒否挙動

所有外の caller は `b5_contrast_launch.py`、共有 harness consumer は `test_t2849_job_contract.py`。関連する契約検査は `test_pegasus_tools.py`、`test_hooks.py`、README の qsub fence test、`test_plain_runner_coverage.py`。新しい test file は作っていない。T-2849・B-5・K2・従来 proposal／fixture／stock-control の既存入力に対する受理・拒否条件、期待件数、argv は変更していない。

## 総括

所有 2 ファイルの実装は完了した。計算ノードでの対象 test と変異検査が未実走であり、緑とは報告しない。commit は作成していない。