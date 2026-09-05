# 段 6 レビュー B の must-fix 3 件に対する親の再実測 (2026-09-02 01:05 JST)

## MF1: 「列挙しない flag は fresh configure で default 0」— **指摘は正しい。事実誤り**

`external/ccbench/cmake/Options.cmake:38-39` を親が読んだ結果:

```
set(CCBENCH_INSERT_READ_DELAY_MS  "" CACHE STRING "ms; empty = unset")
set(CCBENCH_INSERT_BATCH_DELAY_MS "" CACHE STRING "ms; empty = unset")
```

**default は `0` ではなく空文字 (unset) である。** したがって cicada notes の
「genome に列挙しない flag は -DCCBENCH_* に現れず、fresh configure では default 0 に落ちる」は
**全 flag への一般化として事実でない**。`SINGLE_EXEC` (`Options.cmake:33` で `0 CACHE STRING`) には
当てはまるが、delay 2 件には当てはまらない。

**判定: real / must-fix / scope 内。** 主張を `SINGLE_EXEC` へ限定する。
成果物影響: 下流が「省いた flag は一律 0」と読み、build identity や軸候補の判定根拠を誤る。

## MF3: 正しさ境界の fail-closed 箇所 — **指摘は正しい。機構名を誤っていた**

親は `s3-parent-remeasure.md` で「`BASELINES[protocol]` を先に引くため `KeyError` で止まる」と書いた。
**これは誤りである。** 親が現物を読み直した結果、`_parse_cli_args` の末尾
(`orchestrator/campaign/between_run_floor.py:344-348`) が先に `ValueError` を送出し、
`:361` の添字参照へは**到達しない**。

親の実測 (2026-09-02 01:04 JST):

```
tictoc -> ValueError: unknown protocol: 'tictoc' (選択肢: ['mocc', 'silo'])
cicada -> ValueError: unknown protocol: 'cicada' (選択肢: ['mocc', 'silo'])
silo   -> 受理
```

**fail-closed であるという結論は変わらないが、機構名と例外型を訂正する。**
正しくは「`_parse_cli_args` が `protocol not in BASELINES` を `ValueError` で拒否する
(`between_run_floor.py:344-348`)」。その先に D1373 の source 束縛 admission (`:363`) がある。
**判定: real / must-fix / 親の docs 側の訂正。** 実装面 (notes) には `BASELINES` の記述は無い。

## MF2: レビュー射影に無い範囲の断定 — **指摘は方法論として正しい。親が全件で確かめた**

レビュー B は `cc/tictoc/include/`、workload source、共通 header、cicada の README /
CMakeLists / workload source を射影されておらず、親の断定を独立に検証できなかった。
親が base 時点の worktree で全件確認した結果を記す。

| 断定 | 親の再実測 | 結果 |
|---|---|---|
| tictoc `PARTITION_TABLE` に live site 無し | `cc/tictoc/` 全体 (`include/` 部分木と 4 workload source を含む) + `include/` + `common/` を全件検索 | CMakeLists.txt:7 の 1 件のみ。**live site 0 を確認** |
| tictoc OPTIONS に bare define 無し | `cc/tictoc/CMakeLists.txt` 全文 | 全 entry が `NAME=${VAR}` 形式。**bare define 0 を確認** |
| cicada OPTIONS に bare define 無し | `cc/cicada/CMakeLists.txt` 全文 (1-15 行) | 全 9 entry が `NAME=${VAR}` 形式。**bare define 0 を確認** |
| cicada README が現行コードと食い違う | `cc/cicada/README.md:46` を親が直接読んだ | 「If this is 1, it devide the table into the number of worker threads not to occur read/write conflicts.」と書かれている。現行コードは `util.cc:326-336` の印字のみ。**食い違いを確認** |
| cicada の delay 2 件 | `cc/cicada/` 全体を検索 | `INSERT_READ_DELAY_MS` / `INSERT_BATCH_DELAY_MS` は `CMakeLists.txt:12-13` にのみ現れ、cicada の source に使用箇所は無い。`WORKER1_INSERT_DELAY_RPHASE` だけが `transaction.cc:925` で `clock_delay()` を呼ぶ |

**判定: 断定は維持できる。ただし独立検証を成立させるため、焦点再レビューでこれらの file を射影する。**

## MF2 の nit 部分: `WRITE_LATEST_ONLY` の引用が不完全

レビュー B は「作用点は `transaction.cc:242-262` だけでなく validation の `:490-529` もある」と指摘した。
軸集合は変わらないので nit だが、**この軸は規律 2 に最も近い判断**であり、
notes の引用が不完全だと下流が再検証しにくい。fix 子へ引用の補完を含める。
