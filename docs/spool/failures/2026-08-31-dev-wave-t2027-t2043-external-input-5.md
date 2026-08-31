---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-31
wave: dev-wave-t2027-t2043-external-input
seq: 5
---

## 再発

### F333

- **再発: 2026-08-31** — T-2027/T-2043 の受入全走 attempt 2 が
  `dispatch-attestation-missing` (`raw_child_rc=16`、待ち手は `rc=70 source_rc=16`) で戻り、
  テストを 1 件も走らせなかった。shard-0 の dispatch が request `957885.nqsv` の
  orphan hold を立て、launcher は `runner binding report count mismatch` を報告した。
  qstat では当該 request は既に存在せず (終端)、作業ツリーは clean だったので hold を撤去し、
  attempt 3 を投げた。**attempt 3 も同じ `rc=16` で戻り、3 shard すべての dispatcher log が
  `Pegasus orphan hold があるため scheduler command を起動しません` だった。**
- **この再発が足す事実: orphan hold は 2 つの path に書かれ、dispatcher が見るのは片方だけである。**
  実際に存在したのは `output/pegasus-dispatch/orphan-holds/957885.nqsv.json` と
  `output/pegasus-dispatch/orphan-hold.json` の 2 つで、**dispatcher が参照して全 shard を
  止めていたのは後者 (単数形) だった**。attempt 2 の後に前者だけを消したため、hold は
  解除されておらず attempt 3 は collection (19126 件) まで進んでから 3 shard とも起動せずに終わった。
  撤去を「1 ファイル」と思い込むと、受入全走 1 回分をそのまま失う。
- 恒久対応: 撤去前に
  `find output/pegasus-dispatch -maxdepth 2 -name "*hold*"` で全 path を列挙し、
  撤去後に同じ列挙が directory だけになることを確認してから再投入する。
  hold の実 path は推測せず **dispatcher log 本文が名指しする path** を読む
  (`IZANAGI_DISPATCH_OUTCOME_V1 ... "reason":"orphan-hold"` の直前行)。
  手動 qdel は行わない — F47 の `submission-disabled.json` を武装させ、解除がユーザー手番になる。
- 再発検知: 受入や焦点走が `child_started=false` / `kind":"infra"` / `"reason":"orphan-hold"` で
  戻ったら、上の列挙を 1 回実行する。空でなければ、その走行は負荷でもテストでもなく
  残存 hold で止まっている。
