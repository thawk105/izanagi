---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: t2273-issue-subprocess
seq: 1
---

## 新規

### {{F:t2273-e1-shard-partition}}. 前 wave から写した計測の有効性条件 E1 (3 shard 割付の完全一致) が、自 wave の新設 test による受入 shard 分割の変化で構造的に不成立になり、系列の途中で erratum が要った [手順漏れ] [テスト代表性]

- 事象: [T-2273] (b) の隣接対の実受入で、事前登録は前 wave (a) の計測 probe と E1 「A/B 共通 node の 3 shard 割付の完全一致」をそのまま使った。01-A・02-B の後、03-B の投入前検査が E1 不成立で系列を止めた。新設 8 node が所要時間台帳に無く B の shard-1 に入り、shard-1 / 2 の間で分割が変わっていた (shard-0 の共通 node 4,302 件は一致)。A/B の木で決まる決定的な性質なので残る対も必ず不成立になり、W を見る前に割付一致を shard-0 に限定する erratum E1' を codex の賛否相談を経て固定した ({{D:t2273-issue-subprocess-land}})。
- 根本原因: 前 wave では新設 1 node で分割が変わらず E1 が成立したため、E1 が「新設 test の数・重みによらず成り立つ」と暗黙に仮定した。shard 割付は所要時間台帳の重みによる決定的な分割で、系列を投げる前に login collection から計算できたのに、段 4 で確かめなかった。
- 恒久対応: 手順。隣接対の計測で E1 相当の割付一致を事前登録するときは、系列の前に A/B の login collection と受入と同じ割付で各 shard の共通 node 集合を比べ、成立を確かめてから登録する。不成立なら、判定量に必要な shard だけの一致に登録段階で絞るか、分割を揃えた B を作る。gate・検査は足さない。
- 再発検知: 系列投入前の検査 (集計器の E1) が 1 対目の後に止める (今回と同じ)。
