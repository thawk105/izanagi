---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2288-b4-floor-cell-calib
seq: 1
---

## 新規

### {{F:noncertified-precedent-used-to-widen-a-ruled-out-receiving-set}}. 非 certified 先例と文書レイアウトを根拠に、既裁定が却下済みの受理集合拡大へ向かった [手順漏れ] [誤前提]

- 事象: 段 1 brief と段 2 plan が「凍結 spec の calibration↔cell workload 一致要求は repo の先例と
  整合しない欠陥」と判定し、一致要求を外す案を採った。根拠は (a) b10 formal run の provenance が
  3 workload すべてに同一 calibration を束縛し束縛 field に `workload` を含まないこと、
  (b) 事前登録 §5 の校正済み `PerfConfig` 欄が単数であること。段 3 のレンズ A が D15 を引いて反証し、
  親が一次資料で確認して不採用にした。D15 の却下欄は同じ案を「飽和点が skew 依存と実測で割れた以上、
  虚偽」と明記していた。実装前に止まったので実害はコード 0 行。
- 根本原因: 既裁定の閉包検索を**主題語**(`floor`、`b4`、成果物パス) だけで行い、
  変更しようとしている**機構語**(calibration の keying、workload 署名) で `docs/decisions.md` を
  引かなかった。加えて根拠に採った先例の権威を確認しなかった — b10 provenance の
  `official_certification` は `false` で、certified 受理集合を広げる権威ではない。
  文書のレイアウト (欄が 1 セルであること) から意味上の個数を導いたのも同型の誤りである。
- 恒久対応: `docs/dev-wave/core.md` の `DW-C00`「設計択一が割れる・正しさ防壁に触る・受理集合が
  変わる段では独立の敵対検証子を省かない」。本件はこの敵対検証子が実際に発火して止めた事例である
  (軽量版で段 3 を省いていれば実装まで通っていた)。加えて memory
  `closure-and-search-discipline` を「受理集合を緩める前に、緩める対象の機構名で decisions を引く /
  根拠に採る先例は certified か確認する」で更新した。
- 再発検知: 受理集合を緩める差分を持つ wave では、段 3 のレンズに「その緩めを却下した既裁定が
  無いか」を機構語で検索させる項目を入れる (本 wave のレンズ A prompt がこの形)。
  機械検査ではないので、`DW-C00` の敵対検証子の非省略が唯一の防壁である。
