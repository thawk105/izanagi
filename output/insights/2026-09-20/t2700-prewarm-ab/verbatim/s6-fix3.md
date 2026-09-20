## 変更内容

`probe-t2700/t2700_ab_analyze.py` のみ修正しました。

- `inspect_series` に系列検算を集約し、`analyze` と新しい `--series-state` で共有。
- request の必須引数について、両複製で存在・一意性・値を検査。
- 既存の反例5件、判定文言、解析締切、失敗集計、`--check-run` の JSON／rc 契約を維持。

## 実走結果

`python3 probe-t2700/t2700_ab_analyze.py --selftest`：**PASS、rc=0**。

合成 runs に対する実際の `--series-state` CLI の結果です。

| case | runs_seen | valid_pairs | 次番号／slot／腕 | stop_reason |
|---|---:|---:|---|---|
| a 空 | 0 | 0 | 1／1／E | null |
| b 第一腕成功 | 1 | 0 | 2／1／L | null |
| c 対成立 | 2 | 1 | 3／2／L | null |
| d 第二腕無効 | 2 | 0 | 3／1／E | null |
| e digest 不一致 | 2 | 0 | 3／1／E | null |
| f 8対成立 | 16 | 8 | 17／9／E | target-pairs |
| g 20走到達 | 20 | 7 | 21／8／L | max-runs |
| h 同 slot で3回無効 | 4 | 0 | 5／1／E | series-invalid |
| i 欠番 | 1 | 0 | 2／1／E | sequence-violation |

重複番号、時刻重複、worktree 不一致、引数の同時欠落・重複・不一致、`repo_root` 欠落、計算不能入力の rc=2 も確認しました。

## 総括

`--series-state` は stdout に JSON を1行出力します。

| field | 意味 |
|---|---|
| `runs_seen` | 記録された走数 N |
| `valid_pairs` | 停止判定までに成立した対数 |
| `cutoff_reached` | 投入停止なら true |
| `stop_reason` | null／target-pairs／max-runs／sequence-violation／series-invalid |
| `next_run_number` | N+1 |
| `next_slot`、`next_arm` | 次の slot と腕 |
| `pending_first_arm` | 有効な第一腕が第二腕を待っているか |
| `last_run` | 最後の走の検査結果全体。空系列では `{}` |

停止時も **rc=0**、入力破損などで計算不能なら **rc=2**。停止時の次走 field は投入許可を意味しません。運用上の停止は、既存の解析締切を変更しません。

必須引数は `--izanagi-acceptance-shard-index`、`--izanagi-acceptance-shard-count`、`--izanagi-acceptance-shard-session`。`repo_root` は両 request オブジェクトの必須 field としました。

**互換性の残件：** 読んだ実物の `receipt.request` には `repo_root` がありません。指定どおりの検算ではこの形式は `artifact` になります。測定開始前に生成側との整合が必要です。

実走検査は上記 selftest が PASS。実 launcher との連続運転は未実走です。所有外編集・docs 編集・commit・git 操作は行っていません。