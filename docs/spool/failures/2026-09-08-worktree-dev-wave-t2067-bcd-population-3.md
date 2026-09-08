---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: worktree-dev-wave-t2067-bcd-population
seq: 3
---

## 再発

### F35

- **再発: 2026-09-08** — 床値選択の残件を運ぶ carry item が、先行 wave (entry 1236) が「完了」と
  記録した小項目 (d) を未完として再掲し、母集合の件数も entry 1202 当時の「3 群」へ巻き戻した
  (1236 は 4 群へ訂正済み)。従来の 6 形態 (承認記録側の照合漏れ / 起票から投入までの時間差 /
  完了節への自 ID 明示漏れ / 同一症状の兄弟 finding が別 ID で fix / 既裁定が 2 item を 1 変更単位へ
  併合 / 親項の分割で相互参照が残らない) と異なる新しい角度は 2 つある。第一に、**本文を持つ
  carry item が、後発 wave の書き換えによって自分の前の版へ巻き戻った** — carry stub が
  更新されずに古いままになる従来型と違い、書き換えの向きが後退である。第二に、**letter 付き
  小項目の指す内容が entry ごとに drift した** — 同じ (c) が entry 1202 では旧 public builder /
  writer の迂回口、1236 ではその private 化の完了、1345 では別内容の library 経路
  (`verify_manifest` → judge / verdict 系) を指す。したがって letter を鍵に残件を数えると、
  閉じた作業をやり直すか、別主題を同一視することになる。被害は依頼の前提に及んだ —
  本 wave の依頼はこの carry の (b)(c)(d) を対象に立ったが、(c)(d) は先行 wave が完了として
  記録済みで、(d) の genuine 正負 4 node は今日も現物で成立していた。検出は従来どおり
  dev-wave 段 1 の前提実測 (`DW-S01`) で、子を 1 本も起動する前に止まった。恒久対応 1 は今回も
  投入前の防壁として機能したが、**letter 付き小項目の内容の後退と意味の drift を検出する機械防壁は
  無いままである。**
