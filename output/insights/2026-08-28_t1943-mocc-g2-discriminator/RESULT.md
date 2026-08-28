# T-1943 MoCC G2 payload-lineage discriminator — 1-cell result

authority: none
default_effect: no-state-change

## 観測の束縛

- request: `956466.nqsv` (`0:956466.nqsv`)、execution host: `bnode010`
- outer commit: `d8a6410da1ddbc8bf8423fabfdc78fad6c092c9b`
- CCBench commit: `e9e477ca1b55348ab4530de0b1cf663ce4555290`
- fixed cell: 3 秒、48 threads、10,000 records、read ratio 50、skew 0.9、RMW 0、max ope 10
- raw receipt: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1943-mocc-g2-discriminator/attempts-final1/t1943-raw-receipt.json`
- raw snapshot: 同directoryの`raw-staging-0_956466.nqsv/`。worktree stagingとのhard-link snapshotであり、生trace本文はrepoへ収録しない。

## 結果

- TRACE=0 absence gate: marker absent、symbol absent、全5 forbidden binary token absent、`nm rc=0`。
- verifier: `rc=0`、integrity clean、anomaly 0、cycle 0、verdict `serializable`。
- payload discriminator: `rc=0`、conclusion `no-g2`、blocker 0、comparison 0。
- したがって、この1 cellではG2 read-from edgeが発火せず、payload lineageによる原因識別は行われなかった。これはMoCC根因やtrace投影誤りの否定ではない。
- 規定どおり、`no-g2`を見て追加cellは投入していない。

## finalization failureと是正

- discriminator完了後、completed pilot receipt公開前のartifact classificationが`rc=2`で停止した。
- 計算ノードのembedded `python3`が`Path.stat(follow_symlinks=False)`を受けず、`TypeError`になったことがroot causeである。
- `267741106e7cec98c8ab667cbb9c7ef8a9b9a4fa`で`os.lstat`へ変更し、real directory正例、directory symlink負例、regular-file負例を固定した。親の関連走は124 passed、焦点再レビューはGO。
- この失敗のためcompleted pilot receiptとjob-resultは存在しない。上の結果はraw verifier/discriminator bytesへ束縛したnon-certifying observationである。

## 主要digest

| artifact | SHA-256 |
|---|---|
| `discriminator.json` | `91cb025d51b06dcccfd81c2be62b2221c98e2932304c3994729e855a40f8c97a` |
| `verifier.json` | `abd589b0a7097c6edc51374dfb2add5535f57f472a7e7e21d277cf981466561c` |
| `failure.json` | `49b7e0dcd429122eacbd28c6802a5535576863047f5be5b2aaf9ffc37edb81d7` |
| `trace0-watermark-absence.json` | `3fbb8248fcb7d5b6d1252a51841cf08849bc9c7a1fd2a9f2d8c331a006c6dc6d` |
| `trace-manifest.json` | `a257b3457c033cca68cd642ce0662cc084156d1f0520e8ce9237c4fc7fd2ad5c` |
| `witness-manifest.json` | `55cefa8090da7371acb591a93b06e65bddaa75c7b11d2140fa1e7ec48002854e` |
| `submit-receipt.json` | `18b51580dc7ec1c4207775ac15786284c1c448251885f1392bc66887d2c2d2eb` |

## 主張上限とscope外

- `no-g2`からserializableへ昇格する新しい主張は作らない。標準verifierの当該cell verdictを記録しただけである。
- MoCC一般根因、writer version、commit order、一般replay、他CC、42-run再実行、Silo対照だけの追加、性能値は未検証または未実施である。
- upstream push / PRは行っていない。CCBench local branchの2 commitは人間が必要なら後でpushする。
