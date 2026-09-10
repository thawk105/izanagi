# T-1933 受入最長node短縮の現行main再裁定

## 結論

実装面は0 byteとした。受理集合、assertion、live repository再観測、独立oracleを保ち、かつ現行実測の最長nodeへ意味のある効果を持つ所有内の共有境界を証明できなかったためである。「最長nodeを短縮した」とは主張しない。

## 現行mainで覆った前提

- 開始tipは `61b92342beb259363eb5ed094ac200dd39a7a1f5`、段4後のmain同期tipは `728475c9fc619100ca270afd2292c914ab7a089e`。対象2 test fileと直接helperはこの同期で変化していない。
- duration ledgerの全体最長は、所有外の140秒nodeだった。旧T-1933の「floor snapshot 79秒が全体最長」はstaleである。
- 固定4 node、固定順、`-n 0`、`--force-dispatch` の変更前baselineはrequest `954274.nqsv`、child rc=0、4 passed / 147.55秒。
- node durationはfloor snapshot 4.18秒、T-080 single-defect 86.57秒、draft-finalize 51.93秒、T-080 snapshot 2.61秒。ledgerのsnapshot 79/50秒はこの条件で再現しなかった。

## fresh planと敵対相談

最初の段2はbaseline結果の追記と同時に走ったため無効化した。immutableなbaseline入力から段2を再実行し、続いて正しさ・実効性の2レンズを並行実行した。全3成果物はCodex出力検査を通った。

- plan v2: snapshot規則共有はlive再観測または独立性と衝突し、T-080跨ぎ共有はD104で棄却済み。0 byteを勧告。
- 正しさレンズ: 「安全な構造候補が一切ない」は過剰と訂正した。無変更区間snapshot再利用やT-080分岐前prefixは安全化の余地があるが、実効的な最長短縮を証明しないため0 byteを支持。
- 実効性レンズ: fixed serial sliceをacceptance critical pathへ一般化できないと指摘。cached baseの全量copyを未計測候補として残したが、CoW境界、独立inode、環境対応、効果量が未証明なのでauthor投入は支持しなかった。

## 段4裁定

- optional rules注入、optimized/reference間の値源共有、live再観測省略、worker/session跨ぎT-080 cache、grouping、variant統合、case縮小、assertion変更は不採用。
- snapshot 2 nodeの全消去でも固定sliceの上限は6.79秒であり、86.57秒nodeも全体140秒nodeも変えない。安全化可能性と実益を分け、実益gateで不採用とした。
- cached base copyのCoW化は安全境界も効果も未証明であり、試作機構を増やさない。真の律速であるproduction履歴走査は所有外で、D104の裁定を本waveから開き直さない。
- 実装面0 byteのため段5/6と変異matrixを省略した。既存nodeid、assertion、独立性test、single exact reason、held/released検査は変更していない。

## 証拠

段1 brief、固定argvとbaseline、段2 plan v2、段3の2相談、段4裁定を `verbatim/` に保存した。旧waveのplan/consultは使っていない。

## scope外

- 全体最長140秒node、duration ledgerの測定条件metadata、T-1934の残差、T-1938の共通helper分離は本waveで変更しない。
- CoW cloneの局所profileは、対象最長と全体最長を動かす見込みを事前に示せず、安全境界も未証明なので新規task化しない。

## dev-wave改善候補

T-1934の開始inventoryが既存T-1933 ownerを落とした件は、F606の「branch/worktree dirtだけでなくrepo外job directoryの編集予約も走査する」既存恒久対応の再発と裁定した。新しいreference義務は足さず、F606へ2026-08-28の再発としてroutingした。
