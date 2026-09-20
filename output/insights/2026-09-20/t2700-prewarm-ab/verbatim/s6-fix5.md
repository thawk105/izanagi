## 総括

`probe-t2700/t2700_ab_analyze.py` のみ修正しました。

- `timestamp()`：末尾の `±HHMM` を `±HH:MM` に正規化。その他の処理は維持。
- `selftest()`：`+0900` と `+09:00` の epoch 一致、および負の offset の一致を追加。既存の naive 拒否検査も維持。

`--selftest` 実走結果（rc=0）：

```text
selftest: PASS (5 statistical counterexamples, v2 artifacts, sequence/cutoff, diagnostic, check-run and series-state CLI cases)
```

指定の `--check-run` を読み取りだけで実行しました。stdout の該当フィールドを逐語抜粋：

```text
"classification": "success"
"reasons": []
```

終了コードは `0`。実走 01-E は有効（`"valid": true`）になりました。run directory への書き込み、docs 編集、git 操作は行っていません。