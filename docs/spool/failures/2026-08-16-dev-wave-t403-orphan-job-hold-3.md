---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t403-orphan-job-hold
seq: 3
---

## 新規

### {{F:receipt-sample-survivorship}}. 保存に成功した receipt だけを数えて「孤児は 1 件」と一般化しかけた [テスト代表性]

- 事象: 実 dispatch receipt 135 件の内訳 (正常完了 124 / cleanup 未 claim の infra 8 /
  gate 許可 + qdel rc=0 が 2 / 孤児 1) から、「`qdel.job_may_remain` field の欠落 = 孤児なし」を
  安全側の根拠として brief に書いた。段 6 の敵対レビューが標本の偏りを実証して差し戻した。
- 根本原因: 標本が「receipt を保存できた invocation」に限られる (survivorship bias)。
  receipt 保存前に強制終了された invocation は標本に現れず、qdel field を持たない
  setup receipt も親の glob が root 直下を走査していなかったため落ちていた。
  観測できた集合の分布を、観測できなかった集合の不在証明に使った。
- 恒久対応: 判定を receipt 標本に依存させない。変異 harness 側へ dispatcher の生存に依存しない
  独立判定 (dispatch 試行の timeout、receipt 由来の `job_may_remain` / hold 書込み失敗) を置き、
  dispatcher が latch を書けなかった場合と強制終了された場合を harness 自身が塞ぐ
  ({{D:orphan-hold-latch}})。
- 再発検知: 変異 M5 (timeout 判定の削除) と M12 (receipt 判定の削除) が、この二重化を
  消すと赤になることを固定する。両者とも本 wave の matrix で KILLED を実測した。
