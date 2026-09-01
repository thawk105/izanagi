---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t2009-checker-mutation-power
seq: 3
---

## 新規

### {{F:static-pin-scope-refuted-by-measurement}}. 同一性 pin の発火範囲を呼び出し関係から静的に結論し、実測が覆した [テスト代表性] [恒真ゲート]

- 事象: 変異の分母から冗長 gate を外す判断のため、段 2 プランと段 3 の独立検査者が
  **それぞれ独立に**「`CONTRACT_LOADER_RELATIVE_PATHS` の pin は
  `capture_/verify_live_contract_loader_binding` を通ったときだけ発火し、選んだ分母は
  その経路を通らないので該当 node は 0 件」と結論した。`--deselect` は不要と勧告された。
  実測すると **53 node** が発火した。分母に入れた `test_campaign.py` と
  `test_s1_direct_comparison.py` が、まさにその経路を通っていた。
- 影響: 静的結論のまま記録していれば、検査器を壊す変異の検出力を 72 node と書いていた。
  実際の挙動検出は 19 node で、差の 53 件は**受理集合を一切変えない等価変異でも同じように
  赤になる層**だった。検出力を 3.8 倍に水増しした主張になっていた。
- 根本原因: 発火点 (関数の呼び出し元) の追跡は正しかったが、**その関数を間接的に通る
  test node の集合**は追跡していなかった。呼び出し元の列挙と、その呼び出し元を実行する
  test の列挙は別の作業であり、前者から後者を導けない。
- 恒久対応: {{D:identity-layer-attribution}} — 冗長 gate の集合は静的に推定せず、
  受理集合を一切変えない**等価変異を 1 件走らせて実測する**。その等価変異が赤にした node が
  その走行における冗長 gate である。これは走行ごとに実測値を取り直す手続きであり、
  宣言ではない。
- 再発検知: 全件 KILLED 期待の変異 matrix に等価変異を 1 件混ぜる。等価変異が
  `SURVIVED` にならない走行は、冗長 gate が分母に残っている。
