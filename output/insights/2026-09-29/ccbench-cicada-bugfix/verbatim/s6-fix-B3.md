## 変更内容

[R/scripts/run_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/run_judge.sh:77) の変更 path 照合を、直親 F→新 tip の 2 file ちょうどに修正し、エラー文言を「F to new」に変更しました。検査器に渡す old=C、親・bundle head の照合、GCC 11/12 の並行実行、Python 3.10 固定は変更していません。

## 実走した command と rc

- `bash -n R/scripts/run_judge.sh`: **rc=0**
- `bash R/scripts/run_judge.sh`（引数なし）: **rc=2**
- G.bundle を `R/tmp/judgecheck/clone` に clone: **rc=0**。checkout 対象のない remote HEAD について警告が出ました。
- clone 上で `git diff --name-only --no-renames F G`: **rc=0**、指定の Cicada 2 file。`git diff --name-only --no-renames C G`: **rc=0**、6 file。修正後と同じ配列照合も **rc=0** で、F→G の完全一致を確認しました。

## 未実走・残る懸念

判定器と計算ノードの job 全体は起動していません。今回確認したのは入力照合までです。

## 総括

判定 job の rc=2 を生んだ path 照合を段 4 追補 1 どおりに修正し、G.bundle の実データで確認しました。