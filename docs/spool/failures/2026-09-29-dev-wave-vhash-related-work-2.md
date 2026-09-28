---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-related-work
seq: 2
---

## 新規

### {{F:dblp-bot-challenge-http200}}. DBLP 検索 API が bot 判定の HTML を HTTP 200 で返し、0 件の検索に見えかけた [手順漏れ]

- 事象: 2026-09-29、Pegasus login node から DBLP publ search API (`https://dblp.org/search/publ/api?...&format=json`) へ送った
  事前登録済みの 12 本が、全て HTTP 200・`content-type: text/html` の bot 判定ページ (7,441 bytes、題 "Making sure you're not a bot!") を返した。
  JSON として読めずに気づき、結果を 1 件も判定せず走行無効とした。子エージェントの WebFetch でも dblp.org・dblp.dagstuhl.de が同じページを返した。
  記録は `output/insights/2026-09-29/vhash-related-work/README.md` §10.1。
- 根本原因: DBLP 側が自動取得に challenge を返すようになった。HTTP の状態コードだけでは取得の成否を判定できない。
  `docs/related-work/README.md` 7.7.4 は登録母集合検索 (RW3) の最小索引に DBLP を含めるため、この状態が続く限り RW3 は DBLP 枝で完走できない。
- 恒久対応: memory `dblp-api-bot-challenge-http200` (取得の成否は content-type と JSON の構造で判定し、状態コードで判定しない。
  DBLP 枝が取れないときは使えなかった索引として記録し、黙って母集合から外さない)。
- 再発検知: 応答本文を JSON として読む段で失敗する (content-type が `text/html`)。件数 0 を「未検出」と読む前に `result.hits.@total` の実在を確かめる。
