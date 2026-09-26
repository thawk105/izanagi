## 直した内容

[test_silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-a/orchestrator/tests/test_silo_policy_recon.py:372) の対象 test だけを修正しました。build stub が `_one` から受け取った build dir に define 列を書き、欠落・値違いでは拒否され、正しい値では verify に進むことを確認します。

## 確認の実測

`py_compile` は rc=0。test 関数の直接呼び出しも rc=0、例外なしでした。`git diff --check` も rc=0 です。

## 総括

変更は指定された test ファイルのみです。index・履歴は変更していません。