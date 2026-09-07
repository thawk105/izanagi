---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-08
wave: dev-wave-t1281-qsub-waiter
seq: 2
---

## {{D:compute-waiter-scope}}. 計算ノード待ち手の完了述語は D1290 の 2 材料だけに閉じる

**決定:** `tools/dev_wave_wait.py compute` の完了述語は、done-marker が実在して非空であることと、
会計本文が対象 request ID へ束縛された `Ended Request Time:` 行を持つことの論理和だけとする。
`qstat` はこの経路から一度も呼ばない。会計側は「`Request ID:` 行がちょうど 1 本」「その行より後ろに
`Ended` 行がある」の両方を要求し、対象 ID 行より前の `Ended` 行は拒否する。CRLF は両 regex で
対称に扱う。段 6 の敵対レビューが挙げた次の 3 件は採らない。

- **symlink を done-marker として拒否する** — 既存の producer 待ち手 (`_producer_file_state`) も
  `is_file` を素で使っており、compute だけに symlink 拒否を足すのは要求外の仮想リスク向け gate に
  なる。TOCTOU は filesystem 検査に内在し、fd 束縛なしには閉じない。
- **空白だけの done-marker を証拠として受理する** — 現行の「`.strip()` 後に非空」は DW-C00 の
  「非空」より厳しい側であり、緩めることは完了判定の受理集合を広げる方向である。規律 2 に従い
  広げず、手順書へ「job body は空白以外を含む内容を書く」と明記して閉じる。
- **deadline の切り捨てを直す** — `経過 + poll > 上限` は既存 producer 待ち手と同一の式で、
  15 秒未満の値では sleep せず即 timeout し、15 秒の倍数でない値は最大 14 秒早く終わる。
  6 時間既定に対して無視できる差であり、producer と揃っている方が読み手の負担が小さい。

**理由:**

- D1290 は判定材料を 2 つに確定させている。早期離脱のための `qstat` 参照や、job の生死を
  scheduler へ問い合わせる経路は、その外側にある。終了した request は数秒で `qstat` から消えるため、
  終了後に問い合わせる待ち手はそもそも作れない。
- 会計本文の束縛は「実行中の job を完了と受理しない」ための本体である。束縛が無いと、同じ file に
  他 job のレコードが混ざるだけで誤完了する (本 wave が現物で再現した)。
- 上の 3 件はいずれも、放置しても誤完了を生まないか (symlink・deadline)、直すと受理集合が広がる
  (空白 marker) 側であり、要求の外にある。手順書に限界として書けば運用で閉じる。

**却下した選択肢:**

- **`tools/pegasus/dispatch_compute.py` の私有 `_accounting_present` を共有化して使う** — 同述語は
  project 名・`Started Request Time:`・`Elapse:` まで要求する別判定である。統合すると
  dispatcher 側の受理集合が動く。共有層 `orchestrator/scheduler_nqsv.py` へ別の公開述語を足す。
- **手順書だけ書いて実装を先送りする** — D1290 が実装まで決めており、実測 wave は毎回
  待ち手を書き起こしている。
