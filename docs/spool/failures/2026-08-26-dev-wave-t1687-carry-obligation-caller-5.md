---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1687-carry-obligation-caller
seq: 5
---

## 新規

### {{F:mutation-spec-drops-registered-ids-silently}}. 段 4 で登録した変異 ID が spec から黙って落ち、報告が完備に見えた [恒真ゲート] [手順漏れ]

- 事象: 段 4 裁定が A1〜A8 / B1〜B3 / C1 の 12 ID を事前登録したのに、親が組んだ変異 spec は
  11 件で、`A6` (義務述語を 2 回呼ぶ) と `A8` (2 つの終端を同じ型にする) が除外理由の記録なく
  落ちていた。本走は 11/11 KILLED で完走し、報告だけを見れば「全変異が殺された」と読める。
  段 6 の焦点再レビューが登録表と spec を 1 件ずつ突き合わせて発見した。land 前に是正した near miss である。
- 影響: 是正しなければ、変異 matrix の covered 集合が事前登録より狭いまま「完備」として台帳へ
  残り、撃たれていない不変条件 (呼出し回数の一意性と、2 終端の型の区別) が検査済みとして
  数えられた。恒真な保証を台帳へ記録する経路である。
- 根本原因: 事前登録 (段 4 の裁定文) と実走 spec (段 6 で親が組む JSON) が別の成果物で、
  両者の ID が 1:1 かを機械にも人にも照合させていなかった。`DW-M01` は登録の作法を、
  `DW-M07` は anchor と期待 node の再検証を定めるが、**登録 ID と spec ID の対応**は
  どちらの対象でもない。件数が減っても、走った分がすべて緑なら summary は完備に見える。
- 恒久対応: 本 wave では 2 件を復元して 13 件で組み直し、全 ID を実走した。逐語の対応表を
  `output/insights/2026-08-26_t1687-carry-obligation-caller-mutation.md` の「本走の内訳」に
  登録 ID 列付きで置き、以後の wave が同じ形で照合できるようにした。
  `docs/dev-wave/mutation.md` の `DW-M01` へ「spec を組んだら登録 ID と 1:1 で照合し、
  落とす ID は理由を台帳へ書く」を足す案は、`tools/check_docs.py` の L1 層予算
  (10,625 bytes) に対して現状がちょうど満杯で 1 byte も入らないため実施していない。
  予算の変更は `docs/skill-self-improvement.md` により独立審査対象であり、裁定へ送った。
- 再発検知: 変異本走の報告に「登録 ID → spec ID」の対応表が無い、または登録件数と
  `registered` の値が食い違うこと。焦点再レビューの lens に登録表との突き合わせを含める。
