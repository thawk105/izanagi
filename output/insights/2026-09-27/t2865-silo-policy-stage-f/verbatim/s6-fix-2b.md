## 変更 file と要点

- **R1:** [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-b/tools/pegasus/p3_s4_loop_pegasus.sh:358) の resolver で、未定義の `policy_mode` を空として扱うようにしました。
- **R2:** [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-b/orchestrator/tests/test_p3_s4_loop_job_contract.py:1324) の共有偽 driver の環境記録を既存の 2 key に戻し、方策 mode の保全 root は別ファイルで観測するようにしました。
- **R3:** 同ファイルの[保全 root 拒否テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865f-unit-b/orchestrator/tests/test_p3_s4_loop_job_contract.py:1510)を、rc=2・driver 未起動・所定の拒否文・compute-result 不在という既存の拒否動作に合わせました。job body の検査位置は変えていません。

## 実走 (または未実走)

**実装済み・未実走。** `tools/run_tests.py` による焦点テストは `qstat -Q` の事前確認が rc=1 となり、子プロセスが起動せず rc=16 で終了しました。`bash -n` も hook に拒否されました。

`py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は成功しました。これらをテストの緑とは扱いません。

## M-F7・M-F8 の kill 見立て

M-F7 は既存の方策 pin テストが異なる pin を観測して検出する見立てです。M-F8 は保全 root 欠落時の rc=2・拒否文・driver 未起動を確認するテストで検出する見立てです。単一理由性の実走確認は親側に残ります。

## 所有外への波及

既存の B-5 と T-2849 の期待値は変更していません。関連する `test_t2849_job_contract.py`、Pegasus tools・hooks のテスト、README の qsub 記述はいずれも未編集です。

## 総括

R1〜R3 を所有する 2 ファイルで修正しました。commit は作成していません。焦点テストの実走確認が必要です。