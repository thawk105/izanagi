---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: t1912-pair-completeness
seq: 2
---

## {{D:pair-binding-already-closed}}. 既に束縛されている性質へ、消費境界の同型再検査を足さない

**決定:** B-4 の pair 完全性のうち、block id・precursor・proposal・on/off receipt を封印 registry と
凍結 manifest へ束縛する部分は sanctioned assembler `assemble_b4_raw_analysis` で閉じている。
同じ 4 性質を材料レポートの消費境界でもう一度検査する層を新設しない。閉じていないのは
publication 間の選別であり、それを閉じるかはユーザー裁定へ返す。

**理由:**
- 束縛は `orchestrator/campaign/p3_b4_raw_record_producer.py:2322-2333` の `expected_binding` 完全一致
  要求として実在し、raw の precursor は `:2366` で照合済み binding から代入されるため arm の
  自己申告を経由しない。正例・負例も同 commit に着地している
  (`orchestrator/tests/test_p3_b4_raw_record_producer.py:2063` ほか)。
- 消費境界へ同型の検査を置いても、発火するのは「sanctioned assembler が正しく動いた後に、その
  戻り値だけを改竄した」場合に限られる。実 artifact から到達する経路が無い検査は、受理集合を
  1 つも変えない。これは仮想リスク向けの gate 追加であり、追加しない。
- 段 3 の敵対相談 2 本が、異なるレンズから独立に同じ結論へ到達した。親も producer と test の
  現物、および `git log -S` による着地 commit を自分で確認した。

**却下した選択肢:**
- 消費境界の完全性 consumer を新設する — 上記のとおり実経路で発火しないため却下。
- 分析閉包 5 module を編集して純粋契約層へ束縛を足す — 事前登録 §5 の記入値 (5 module の
  whole-file sha256) が黙って偽になる。受理集合を変える改訂であり AI が既成事実にしない。
- publication を跨ぐ append-only の権威を今作る — D1936 前文の「付随する gate・台帳・汎用化を
  足さない」と項 8 の「母集合を作るための追加基盤は採らない」に抵触する。裁定へ返す。

## {{D:stale-carry-falsified-only-by-code}}. 持ち越し項目の前提は、一次資料ではなく実装コードで反証する

**決定:** 持ち越し項目を対象とする wave では、段 1 の前提実測を carry 本文と初出エントリの照合で
終わらせない。**その項目が「無い」と主張する機構の名前で実装側を検索し、着地 commit を
`git log -S` で確かめる**ところまでを前提実測に含める。

**理由:**
- carry 本文は「機構が存在しない」という否定命題を運ぶ。否定命題は台帳の中では反証されない —
  別 ID の実装 wave が機構を着地させても、その wave は自分の T しか次の一手に書かないため、
  carry 側の本文は無傷のまま残る。
- 本件では carry 本文の 2 日後に機構が着地し、以後 40 エントリ carry されていた。段 1 で
  初出エントリの逐語まで当たっても検出できず、段 3 の敵対相談が実装コードを読んで初めて崩れた。
- 子を 3 本起動した後に前提が崩れる方が、段 1 で 1 回検索するより高くつく。

**却下した選択肢:**
- 全 carry item に定期棚卸しを課す — 件数が多く、発火しない項目まで一律に読むことになる。
  対象となった項目についてだけ、着手時に 1 回行う。
- 実装 wave 側へ「他 ID の carry も更新せよ」と義務づける — 実装 wave は他 ID の carry 本文を
  知らないのが普通であり、知り得ない義務を課すことになる。
