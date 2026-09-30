---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-10-01
wave: vhash-ro-novelty-sota
seq: 3
---

## 新規

### {{F:vhash-index-liveness-probe-shape}}. 文献索引の生死確認に本走と違う引数 (arXiv の max_results=0) を使い、同じ HTTP 500 を 5 回「索引の停止」と読んで本走を 1 時間半止めた [手順漏れ] [コンテキスト浪費]

- 事象: VHash md_43 の文献 wave (2026-09-30 22:30〜2026-10-01 00:01 JST) で、件数の事前確認と再開確認に arXiv API の `max_results=0` を使った。
  同じ式・同じ 500 を 20 分おきに 5 回受け、本文を読まずに「arXiv 停止中」と事前記述へ書き、arXiv の本走を止めた。同じ式で `max_results=1` は 200 で、
  本走の実行器 (`max_results=200`) は最初から動いた。OpenAlex の 503 は本物だった。事前記述の「追記」で訂正し、逸脱 (arXiv だけ先に本走) を記録した。
- 根本原因: 生死確認の request が本走と別の引数を持ち、確認の失敗が「索引の停止」か「確認手順の欠陥」かを区別できなかった。同じ原因の失敗を 2 回見た時点で引数を変えた切り分けをしなかった。
- 恒久対応: memory `index-liveness-probe-uses-production-request-shape` (生死確認は本走と同じ URL 形、非 200 は本文を読み 2 回目の前に引数を変えて切り分ける)。
  land 調整役の 2026-10-01 通達「同じ原因で 2 回失敗したら止めて報告」。
- 再発検知: 事前記述の「追記」と worklog に、生死確認の request の URL 形を書く (目視)。

## 再発

### F728

- **再発: 2026-10-01** — VHash md_43 の段 3 相当の read-only 相談 B が `event_invalid` で不受理になった。射影した原典テキスト (md_1 が pdftotext で作った Steam の txt) に
  結合ダイエレシス U+0308 があり、子の grep 出力に混ざった。DW-O02 の「非 NFC 資料は ASCII escape」を段 3 の射影で適用し忘れた。NFC に正規化した写しを作り、
  「写しだけを読め」と prompt に書いて再投入し受理された。以後の段 6 レビューにも全原典の NFC 写しを渡し、1 回で受理された。
