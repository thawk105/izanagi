---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-t1434-adjudication-oracle
seq: 3
---

## 新規

### {{F:absence-claim-must-distinguish-live-consumer-from-any-pin}}. 不在の主張を「現行 bytes を pin する live consumer が 0 件」でなく「pin する台帳が存在しない」と書き、歴史記録を落とした [手順漏れ]

- 事象: `DW-O09` の pin 閉包検索を行った親が、段 1 brief の不変条件へ
  「`tools/codex_reasoning_ab.py` を bytes で pin する台帳・test・trust root は存在しない」と書いた。
  段 3 の敵対レンズが `output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` を
  示してこれを覆した。同ファイルは `tool_sha256` に旧装置の値を持ち、README と erratum が
  それを認証の trust root として参照している。
- 根本原因: 検索が出した事実は「**現行 bytes** と一致する pin を持つ live consumer が 0 件」で
  あったのに、書いた命題は「**あらゆる** pin が存在しない」だった。`DW-O09` と F39 は各出現を
  live copy / 独立 golden / 凍結 snapshot / 歴史記録へ分類することを既に求めているが、
  親は分類を**結論の文言へ反映しなかった**。歴史記録は現行 bytes と一致しないので、
  「現行 bytes を pin する consumer」を数える検索では最初から数に入らない。
- 実害: なし (near miss)。更新閉包が 0 件という結論自体は正しく、`apparatus-pin.json` は
  歴史記録として更新しないと裁定した。誤って追随更新していれば、過去の `aggregate.json` /
  `verify.json` がどの装置で certified だったかという参照を改変していた。
- 恒久対応: `DW-O09` の本文は変更しない (F39 の分類義務を既に含む)。運用として、
  **不在を主張する 1 文には、その主張が成り立つ範囲を同じ文の中に書く** —
  「現行 bytes を pin する live consumer は 0 件。旧装置の歴史 pin は存在し、更新対象外」。
  範囲を書けないなら、その不在の主張は brief の不変条件に置かない。
- 再発検知: 段 3 の敵対相談レンズに「親 brief の**不在の主張**を 1 件ずつ、その主張が成り立つ
  母集合と除外を言えるか確かめる」を含める (本 wave のレンズ A 観点 6 が実際にこれを捕らえた)。
