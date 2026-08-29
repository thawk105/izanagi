---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-t1881-axis3-rescue
seq: 2
---

## {{D:axis3-executor-successor-base}}. 軸 3 検索実行器の後継基盤は exact type 版とし、自己申告版は着地させない

**決定:** 軸 3 検索の実行器を後継 wave で閉じるとき、出発点は救出物の resume2 版 (production 境界を
exact type 検査と private 構築 receipt で判定する版) とする。もう一方の版 (transport の自己申告属性
`_axis3_artifact_class` を読む版) は、テストが緑であることを理由に着地させない。
この判断は、後継 wave が「動く方を採る」として再び逆へ倒すことを禁じる。

**理由:**
- 自己申告版の境界は、取得結果が実取得か模擬かを決める。この境界の読み取りは module 内 1 箇所しか
  なく、独立に裏付ける検査が無い。任意の object が class 属性 1 行で production を名乗れる。
- 偽装経路は属性だけではない。同版の `LiveHTTPTransport` は任意の `connection_factory` を受け取って
  それを通信元に使うため、属性を触らずに模擬応答を production として通せる。
- そのテストが 78 件すべて緑なのは、テスト自身の transport クラスがこの境界を偽装して通しているから
  である。**緑であること自体が、境界が発火しない証拠になっている。** 緑を着地の根拠にしない。
- 実行器は改訂文書の bytes を凍結 digest として pin する。自己申告版は旧文書を pin するので、
  限界記述を持つ新文書と組めない。版の選択は文書の選択と不可分である。
- 規律 2 は、性能や利便のために正しさゲートを緩めることを禁じる。既存 gate の弱体化でなく新規 gate の
  導入であっても、発火しない関門を成果物の真正性判定へ置くことは同じ害を持つ。

**却下した選択肢:**
- 自己申告版を先に着地させ、境界を後続 wave で直す — 技術的には可能だが、既知の偽装経路を main へ
  置く利益が無い。境界とテストを同時に直すなら、それは後継作業そのものである。
- exact type 検査を remote attestation の保証として記述する — 同一 UID が source・private state・
  manifest・validator を一括改変する攻撃は保証範囲外であり、保証できない範囲を謳わない。
