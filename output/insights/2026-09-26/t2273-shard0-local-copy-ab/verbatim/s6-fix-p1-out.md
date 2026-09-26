## 変更

[t2273lc_ab_analyze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273lc-probe/tools/t2273lc_ab_analyze.py) に E1 の照合を実装しました。A 走どうし・B 走どうしの collection と 3 shard の selected を完全照合し、A/B 対では指定の B 固有 node 1 件と共通 node の割付を検査します。不一致の走・対には理由を出力します。未使用の `Decimal`、`ESTIMATE_NOTE`、`all_rows` も削除しました。

## 実走

前回 T-2825 の実データを読み取り専用で確認し、W₀ は **482.215 / 334.439 / 310.663 / 511.326 / 374.494 / 344.931 秒**、対差は **147.776 / 200.663 / 29.563 秒**で指定値と一致しました。前回系列には共通 node の shard 移動があるため、E1 を適用した対は無効になります。

インラインの合成入力では、B 固有 node 1 件を正例として通し、A のみの差、B の 2 件、共通 node の割付差をそれぞれ拒否しました。空集合を指定した照合も通過しました。`bash -n`、Python 構文検査、`git diff --check` は成功しました。

## 総括

変更は集計器の 1 ファイルだけです。判定式・閾値・系列順序は変更していません。実受入の投入と dispatch は行わず、commit も作成していません。