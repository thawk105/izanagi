## 所見対応表

変更ファイルは `probe-t2766/t2766_ab_analyze.py` のみです。

| 項目 | 判定 | 根拠（変更行） |
|---|---|---|
| 1. 投入順照合 | closed | 414–436行、457行：指定形式で時刻を解析し、投入時刻の厳密増加・前走終了との非重複を検査。違反は走番号と時刻付きで集計全体を停止。 |
| 2. env検査 | closed | 294–299行：bytecode記録が `"no"` 以外なら指定理由で無効化。Bのexact token、Aのkey不在も検査。 |
| 3. selftest | closed | 687–693行、764–807行：正常系列、終了＝次走投入、時刻逆転・同時刻・重複、bytecode `"yes"`・空・欠落などを検査。既存検査も維持。 |
| 4. runs走査維持 | closed | 3行：未投入停止はlauncherがruns外へ保存する旨を追記。`numbered_run_paths` は変更なし。 |

## 総括

指定コマンドを実行し、**PASS（終了コード0）**でした。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 probe-t2766/t2766_ab_analyze.py --selftest
```

変更関数は `analyze_run`、`analyze`、`selftest`、`main`、追加関数は `validate_run_times` です。実測は行っていません。docs編集・git操作・commitは行っていません。