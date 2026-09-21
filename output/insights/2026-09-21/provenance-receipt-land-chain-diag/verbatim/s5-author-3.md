## 総括

[receipt_reuse_replay.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/receipt_reuse_replay.py:34) を修正しました。

- 系統表を定数 `CHECKER_LINEAGES` に集約し、指定の新形・中間形・旧形を登録。親の実測方法、commit と SHA をコメントに記載しました。
- cause 分岐を指定どおり変更し、未登録 SHA は `"attributes 差 (系統不明)"` としました。
- 前巡ファイルとの bytes 差分は、定数・出所コメントの追加と cause 分岐だけです。変更の逆適用で元 bytes と完全一致を確認しました。追加の bug fix はありません。

同じ入力で自己実走し、**rc=0** で完了しました。[stdout](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/out/reuse-replay-self-3.stdout.txt) と [JSONL](/work/1/SFC/tanab/izanagi/.codex/worktrees/pcd-unit-probe/build/probe/out/reuse-replay-self-3.jsonl) を保存済みです。

cause が変わった行は以下の3件です。すべて population `R`、partition `2a6c7dae048c`、checker `65476dafe9c0` です。

| mtime（2026-09-20、JST） | tip |
|---|---|
| 23:12:12 | `7cac2d8c7d07` |
| 23:17:15 | `b8fa2c57629e` |
| 23:36:39 | `43c32588b3e6` |

3件とも `"attributes 差 (新形、原因未特定)"` → `"参考区分: 旧形 attributes fingerprint の候補集合変化"` に変更されました。旧形分岐による `gitattributes_commits: []` の追加以外、結果の他項目に変更はありません。残り82件は完全一致です。

集計表部分の全文：

```text
REUSE SUMMARY rows=85 excluded_ledger_errors=0
再利用可能性の事後推定であり実績ではない。mtime順・残存集合・現行checker条件に限定。
population	verdict	cause	n
M	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	候補あり (replay 成功)		47
R	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	25
R	候補あり (replay 成功)		4
R	候補なし	checker sha 変更	6
R	候補なし	partition 跨ぎ	2
PARTITION SUMMARY: population	partition	verdict	cause	n
M	4608b761416c	候補あり (replay 成功)		10
M	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
M	c508d1de93e1	候補あり (replay 成功)		37
R	18d19753b740	候補なし	checker sha 変更	1
R	2a6c7dae048c	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	3
R	2a6c7dae048c	候補あり (replay 成功)		2
R	2a6c7dae048c	候補なし	checker sha 変更	1
R	4608b761416c	候補なし	partition 跨ぎ	1
R	53e9a718e601	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	8
R	53e9a718e601	候補あり (replay 成功)		1
R	5f183033771c	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	13
R	7669d7b2ef9a	候補なし	partition 跨ぎ	1
R	8c683754078a	候補あり (bindings 不一致)	参考区分: 旧形 attributes fingerprint の候補集合変化	1
R	ae7ec43852ce	候補なし	checker sha 変更	1
R	c508d1de93e1	候補なし	checker sha 変更	1
R	cceb9da4d834	候補なし	checker sha 変更	1
R	cfdf571bda61	候補あり (replay 成功)		1
R	cfdf571bda61	候補なし	checker sha 変更	1
```

作業前後の tracked status は空で、**tracked file 変更0**。未完了はありません。並走・prune・上書き・当時の実行時失敗を復元できないという、事後推定の既存制限は残ります。