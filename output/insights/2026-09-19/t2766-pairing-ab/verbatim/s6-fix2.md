## 所見対応表

変更行はすべて `probe-t2766/t2766_ab_analyze.py` 内です。

| 項目 | 状態 | 対応・根拠 |
|---|---|---|
| 1. tip・clean | closed | 前後 SHA と必須 CLI tip、前後 dirty=0 を照合し、無効理由を保持。276行、804行以降。 |
| 2. 順序・再試行・上限 | closed | 01始まりの連続・一意番号、12走上限を検査。無効対は slot を消費せず、順序・任意の `pair_slot` を照合。有効3対後は「上限後 / 余剰」として表に保持。350・395行以降。 |
| 3. 複製成果物 | closed | `session_dir="session"` のみ使用。`copy_ok is True` と全3 shardの必須ファイルを検査。origin は表への記録のみ。276・440行以降。 |
| 4. 2個目 unit・実測最長 | closed | testcase timeを保持し、連続scopeをunit列へ集約。`second_unit`、`ledger_max_units`、`measured_longest_units`、主張範囲の `claims` を追加。21・83・197行以降。 |
| 5. cost加算順 | closed | sorted cost列を要素ごとの `math.isclose(rel_tol=1e-9, abs_tol=1e-9)` で比較。headのcardinalityは厳密に区別。128・181行以降。 |
| 6. selftest | closed | 既存検査を維持し、指定の異常系・再試行・unit正負例・実測最長・狭い許容誤差の受理／拒否を追加。486行以降。 |

## 総括

変更fileは [probe-t2766/t2766_ab_analyze.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2766-unit-impl/probe-t2766/t2766_ab_analyze.py) のみです。実装4file・docsの編集、git操作・commitは行っていません。

指定コマンドを実行し、**PASS、終了コード0**でした。

```text
PYTHONDONTWRITEBYTECODE=1 python3 probe-t2766/t2766_ab_analyze.py --selftest
```

`run.json` の入力契約：

- **有効性検査**：`condition`、`tip_sha`、`tip_sha_after`、`dirty_lines_before`、`dirty_lines_after`、`rc`、`env`、`session_dir`、`copy_ok`。
- **任意・存在時に検査**：`pair_slot`。
- **表示・provenance**：`session_dir_origin`、`submitted_at`、`finished_at`、`run`、`measurement_tip`、`main_sha_at_launch`、`other_leaders`、`load1`、`gate`。測定tipの正本は必須CLI引数 `--measurement-tip`。
- **成果物**：`session/shard-{0,1,2}/{junit.xml,report.json}` は必須。`dispatch/receipt.json` は任意。JUnit testcaseの `time` を使用します。

実測A/Bの再集計は未実行です。今回のclosedは修正実装と合成入力による検証の範囲です。