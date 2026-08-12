---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-acceptance-critpath
seq: 2
---

## {{D:acceptance-wall-needs-repeated-runs}}. 受入 wall の主張は反復走の中央値で行う

**決定:** 受入全走の所要を根拠にして律速を同定したり改善を主張したりするときは、
**同一 tip・同一条件で 3 走以上を逐次に取り、中央値で述べる。** 1 走同士の差が
10% 未満なら「変化なし」と扱い、改善としても退行としても記録しない。
測定中は自分の他 job を同時に走らせない (dispatch receipt と共有ファイルシステムの双方で干渉する)。

**理由:**
- 同一 tip・逐次・条件交互の sweep で、同一条件の 2 走が 99.30 秒と 117.80 秒 (19% 差) まで開いた。
  受入 wall の観測域は 99.3〜117.8 秒 (±9%) である。
- この幅は、これまで 1 走の値で行ってきた律速同定・改善主張の解像度を上回る。
- 48 worker で観測される node 所要は競合で膨らむ。同一 suite の node 秒合計は
  worker 12 / 24 / 32 / 48 本で 1,542 / 2,261 / 2,828 / 3,344 秒と単調に増える。
  **node 秒は仕事量の代理にならない。**

**却下した選択肢:**
- 1 走のまま報告して「参考値」と注記する — 実際には設計択一の根拠に使われてきたので不十分。
- job Elapse で代用する — job 側の設定・収集時間を含み、pytest wall と別量である。

## {{D:real-repo-group-stays-serialized}}. real-repo の排他は単一 worker 直列化のまま維持する

**決定:** D63 の `real-repo` loadgroup を、プロセス間 reader/writer ロックへ置き換えない。
排他機構の変更で受入を速くする路線を閉じる。

**理由:**
- 直列 group を丸ごと無効化した診断走行 (`--dist load`) の wall は 116.63 秒で、
  予測された約 80 秒には遠く及ばなかった。**置き換えの最良ケースに利得が無い。**
- 「現行の対象 node は全て reader」という前提が成立しない。`git status` を
  `GIT_OPTIONAL_LOCKS=0` なしで呼ぶ経路が複数あり、read-only に見える node も
  git の optional index lock を書く。同 repo 内の別経路はこの抑止が必要だと明記しており、
  1 箇所は実際に抑止している。
- 排他の閉包そのものが未確定である。正本リストの外に、module fixture 経由で実材料を読む node と、
  実 git object を書く node が実在する。**閉包が確定していない排他を差し替えてはならない。**

**却下した選択肢:**
- reader を共有ロックで並列化する — 上記のとおり reader 判定が成立しない。
- group を file 単位へ割る — 排他を保つには結局ロックが要るうえ、module fixture の
  worker 跨ぎ重複支払いを増やす。
- worker 数を throughput の頂点へ下げる — 24 / 32 / 48 本の差は run 間変動に埋もれた。
