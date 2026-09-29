## 修正

[集計器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-probe/probe-t2273is/t2273is_ab_analyze.py) に E1' を実装しました。対の有効性には shard-0 の一致を使い、旧 E1 の成否と shard ごとの不一致件数、各走の host と重複数、旧 E1 による land 区分を JSON と Markdown に残します。W_1・W_2・pre の対差には、shard の test 集合が異なるため実装効果として読めない旨を表示しました。同一条件内の比較は変更していません。

## 検査

全 `.py` の `py_compile`、全 `.sh` の `bash -n`、`git diff --check` が通りました。前 wave の読み取り専用コピーを再集計し、対差 **+55.355 / +46.001 / +47.740 秒**、対率中央値 **12.7%**、区分 **land**、5 分判定 **not-met** が一致しました。旧 E1 も全対で成立し、旧区分は **land** です。合成入力では shard-0 一致・shard-1/2 不一致の対が有効、shard-0 不一致の対が無効になりました。検査用コピーは削除済みです。

## 未実走・懸念

今回の計測系列は読まず、実走もしていません。指定された probe ファイル自体が Git tracked であり、「修正する」と「tracked file は変更しない」が矛盾します。**差分は probe 内のこの 1 ファイルだけ**で、commit はしていません。修正を残すか戻すか、確認をお願いしています。

## 総括

E1' の実装と指定の検査は完了しました。tracked file の扱いについて回答待ちです。