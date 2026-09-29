## 作ったもの

[probe-t2273is/](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-probe/probe-t2273is/) に、移植元の 5 ファイルを `t2273is_` 名で配置しました。

## 移植元からの差分

job dir・slug・参照名を本 wave 用に変更しました。集計器の land 区分を `land` / `land-small` / `no-land` / `undetermined` に変更し、5 分判定は別 field のままにしました。各対の W_1・W_2・shard-0 の pre・post・O_max の値と対差、最遅 shard を JSON と Markdown に追加しました。

## 検査

全 `.py` の `py_compile`、全 `.sh` の `bash -n` が通りました。前回系列の読み取り専用コピーによる集計は、対差 **+55.355 / +46.001 / +47.740 秒**、対率中央値 **12.7 %**、B の W_max 中央値 **317.194 秒**と一致し、結果は `land`、5 分判定は `not-met` でした。検査用コピーは削除済みです。

## 未実走・懸念

本 wave の実受入系列は未実走です。投入用スクリプトも実投入していません。

## 総括

変更は新規 `probe-t2273is/` 内の 5 ファイルのみです。tracked file は変更せず、commit も作成していません。