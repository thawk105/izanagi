---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-05
wave: dev-wave-t2257-formal-consumer-wal-shape
seq: 3
---

## 再発

### F39

- **再発: 2026-09-05** — 8c formal consumer の WAL 形状を直す wave ([T-2257]) で、fixture builder の trigger record を変えると
  result evidence record の bytes が変わるのに、その **sha256 を値で literal pin する 4 定数**
  (`orchestrator/tests/test_reflux_result_evidence.py` の `_RECORD_RAW_GOLDEN` 等) を、段 2 プラン・段 3 の 2 レンズ・親の
  pin 閉包 (path 検索 + fixture builder 利用 9 file の列挙) がそろって落とした。key が path でも fixture 名でもなく派生 digest
  値なので path 検索に原理的に掛からない、F39 本体と同じ機序の再発。検出は親の焦点走 1 回目 (4 赤、land 前、実害なし)。
  旧 baseline の hash 値そのもので `git grep` すると同 file だけが当たり、他に漏れはなかった。恒久対応は F39 から変更しない。
  運用として、fixture / baseline を変える wave では**旧 hash 値を値で `git grep`** して閉包に入れる (memory
  `edit-surface-growth-reopens-pin-closure` と同旨)。

### F1

- **再発: 2026-09-05 (near-miss)** — [T-2257] wave の親が、producer 実走の record を job refs へ保存し直したとき (2 回目の走)、
  brief には 1 回目の走の `ts` を写したまま残した。段 5 の実装子は refs を byte 単位で正しく写していたのに、親は brief の値を
  根拠に「逐語と不一致」と誤裁定し、fix 子に refs と食い違う値へ書き換えさせた。親の byte 比較 script が refs との不一致を
  出して発覚し、次の fix 子で refs の bytes へ戻した (land 前、実害なし)。転写対象が「自分が保存し直した artifact と、
  それ以前に自分が書いた引用」の食い違いへ広がった顕在化。照合は brief の引用でなく artifact そのものと行う。
