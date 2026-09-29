## 変更

- [診断 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-work/diag-cicada-gc-records.patch)（160 行）を作成しました。validation の失敗段、install 済みで abort した版、削除 commit、ERR 直前の版鎖を stderr に記録します。修理は含みません。
- [起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-launcher/launch_gcfix_run.py)（全 1,382 行）に F 基点、絶対パスの patch、CUSTOM の `--repeat`、異常終了した run の記録、診断行の集計と版ポインタによる照合を追加しました。既存 job と出力 field は残しています。

## 観測の設計

[patch の validation 部](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-work/diag-cicada-gc-records.patch:77)は失敗分岐に入った時点の段名を記録します。[abort 部](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-work/diag-cicada-gc-records.patch:45)は既存の aborted 状態への遷移後に atomic load と出力だけを行い、pending 版を待ちません。[削除 commit 部](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-work/diag-cicada-gc-records.patch:112)は診断専用の表・key を保存して出力します。[ERR 部](/work/1/SFC/tanab/izanagi/.codex/worktrees/gcfix-d/.gcfix-work/diag-cicada-gc-records.patch:128)は最大 32 版を出力した後、元の `ERR` を実行します。commit・abort の選択や版鎖の変更は追加していません。

## 自己検査

- F の素の木を `git -C external/ccbench archive 25898d00b9a6bbf09329ff8e8318c77d4f08b46e cc/cicada | tar -x -C .gcfix-work/f-source` で展開し、その中で `git apply --check ../diag-cicada-gc-records.patch`：**rc=0、無出力**。
- `PYTHONPYCACHEPREFIX=.gcfix-work/pycache python3 -m py_compile .gcfix-launcher/launch_gcfix_run.py`：**rc=0**。
- `python3 .gcfix-launcher/launch_gcfix_run.py --list-jobs >/dev/null`：**rc=0**。
- F・TPC-C・絶対パス patch・`--repeat 2` の CUSTOM `--dry-run`：**rc=0**。適用確認 rc=0、touch set は `cc/cicada/` の 2 ファイル、計画には repeat 1・2 が入りました。診断行の照合も合成入力で期待する分類と commit の thid を確認しました。

計算ノードでの build・benchmark と C++ の単一 TU 構文検査は**未実走**です。

## 所有外への波及

ありません。最終確認の出力は次のとおり空です。

```text
$ git -C external/ccbench status --porcelain
$ git -C external/ccbench diff --stat
```

`.gcfix-work/` には診断 patch だけを残しました。commit は作成していません。

## 未解決

F×4 thread の異常終了を診断 patch 付きで実走していないため、版鎖の実測結果と原因の確定はまだありません。

## 総括

修理前の仮説を支持・棄却できる観測 patch と起動器を用意し、F への適用と dry run まで確認しました。