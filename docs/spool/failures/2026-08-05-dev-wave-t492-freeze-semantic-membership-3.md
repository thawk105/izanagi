---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t492-freeze-semantic-membership
seq: 3
---

## 再発

### F113

- **再発: 2026-08-05** — 生成層の負例が `_campaign_file` の mock に repo 外の相対 path を
  返していたため、検査呼び出しを削除する変異では非正準入力の受理を観測する前に
  `Path.relative_to()` が `ValueError` を投げていた。node は赤くなるが受理集合の変化は
  観測していない偽 kill である。公開 producer の負例も mock の side_effect 枯渇で
  同じ偽 kill になり、「書き込み前に拒否した」証拠になっていなかった。
  F113 の恒久対応どおり段 6 の敵対レビュー 1 本がこのレンズを持っており、harness を
  走らせる前に 3 件すべてを検出した。mock を repo 内絶対 path へ直し、検査が無ければ
  実際に書き切るところまで mock を閉じて是正した。
  同じ登録には F113 と同型の「期待 node の不足」も 1 件あり、こちらはレビューを通り抜けて
  harness が MISMATCH で止めた。検査を**恒偽化**する正例側の変異では、走査の最初の値で必ず
  落ちるため、診断文言を別 workload / 別 configuration まで完全一致で固定している負例も
  道連れで赤くなる。親は正例 1 本だけを登録していた。恒真化 (検査を素通しにする) 変異の
  期待 node から機械的に類推せず、恒偽化変異は「文言一致に依存する負例すべて」を数える。
