---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-03
wave: dev-wave-t2111-silent-barrier-inputs
seq: 2
---

## {{D:terminal-is-a-record-not-a-skip}}. 合成不能な検査を terminal に落とすことは、静的 skip を足すことではない

**決定:** 入力を合成できないと実測した検査を「terminal」と扱うとき、行うのは
**記録上の分類**であって、その test へ `pytest.mark.skip` を足すことではない。
実データが無くても走る assert を同じ関数が持つなら、その部分は常時実行のまま残す。
参照の付け替え以外はコードを変えない。

D1382 が terminal と定めた `test_real_rollout_collector_golden_is_source_bound` には、
消えた rollout に依存しない assert (凍結 token slice の digest 照合、
collector 台帳の検証) が同居している。プランはこの関数へ静的 skip を付ける案を出したが採らない。

**理由:**

- 関数ごと skip すると、実データに依存しない assert まで落ちる。**受理集合が広がり**、
  token slice や台帳検証を壊す実装までその機体で通る。絶対規律 2 に反する。
- degrade 構造 (実データがあるときだけ source 結合 assert を実行する) は、
  corpus 消失より前から在る設計であり、今回の発明ではない。壊す理由がない。
- 「terminal」は**その検査を合成入力で復帰させる試みを打ち切る**という意思決定であって、
  検査を止める指示ではない。二つを同一視すると、復帰不能の記録が防壁の削除に化ける。

**却下した選択肢:**

- 関数へ静的 `pytest.mark.skip` を付ける — 上記のとおり受理集合を広げる。
- 合成 rollout を置いて source 結合 assert を通す — source-bound でない bytes を
  正例として受理することになり、検査の主題そのものを失う。
- 実データ依存の assert だけを別 test へ切り出す — 受理集合は保てるが、
  本件は分割の必要が実証されておらず、要求外の一般化にあたる。
