---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-28
wave: worktree-dev-wave-t2068-a2-partial-raw
seq: 2
---

## {{D:a2-partial-raw-authority}}. A-2 partial raw authorityはexact-one成功workloadだけに限定する

**決定:** D1169のexact 2 workload A-2で、driver成功がexact 1のときだけpartial v4 chainを発行する。
partial raw manifestは成功workloadのraw 2件とcampaign lock、WAL、claimのexact 5 memberに閉じ、
failed workloadはrawが物理的に存在してもauthority、cell、effectに含めない。manifestとnested receiptの
pathはwriterのcanonical位置から再導出し、内容を読む前に一致を要求する。full-successとauthority-noneは
既存v3 writerとconsumerを維持する。

**理由:**
- driver非0のsiblingはそのworkloadのraw authorityを失わせるが、別workloadの検証済みrawまで無効にする
  根拠にはならない。一方、failed siblingの値を推定または再利用すればD1169のworkload論理積を破る。
- authoritative workloadのanomalyまたはeffect非正は局所rejectであり、coverage不足より先にgroup全体を
  rejectする。positiveはpartial、判定不能はinconclusiveとし、workload authority mapとouter statusを分ける。
- materialize時にcompletion、acquisition、manifestからauthority、cells、effects、statusを再導出して
  report全体と比較すれば、偽status、failed field混入、v3/v4 cross-chainを同じconsumer境界で拒否できる。

**却下した選択肢:**
- 複数success subsetへ一般化する — A-2のexact 2 workloadを越え、汎用fan-outの別設計になる。
- failed siblingのrawまたは別attemptのevidenceを再利用する — workload authorityの出所を偽る。
- full-successもv4へ移す — 既存の完走済みv3 artifactとconsumerの受理集合を不必要に変える。
- 完走済みA-2 artifactを再発行または遡及昇格する — 当時の判定と現行consumerの主張を混同する。
