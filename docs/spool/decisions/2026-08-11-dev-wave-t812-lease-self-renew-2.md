---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t812-lease-self-renew
seq: 2
---

## {{D:lease-self-renew-scope}}. 受入 lease の自己保持は更新して進み、invocation の識別は裁定へ返す

**決定:** 受入 lease を保持したままの `claim` は、EX flock の中で lease の mtime を更新し
`held-self` を返す。正本待ち手はこれを `acquired` と並ぶ受理状態として扱い、受入を投入する。
自己保持なのに進めないとき (更新失敗、`held-self` の形が契約を満たさない、`held` / `queued` /
`stale-held` / `unavailable` が自己 holder を指す) は polling を続けず、理由付きで fail-closed
する。`held-self` はその呼出しが lease を作っていないので **release 権限を持たない** — 失敗時も
保持したまま返し、終端 release は親が行う。

自己保持の判定に使える holder は wave slug の digest だけであり **invocation を識別しない**。
したがって同一 slug の別 invocation も `held-self` を得て進める。この穴は塞がず、
「1 slug につき active な待ち手は 1 本」を**運用前提**として文書化し、capability / fencing の
機構案は裁定パッケージで返す。同じ束に、受入が TTL を跨いだときの結果受理、stale な自己保持の
扱い、連続更新の上限 (owner 優先と FIFO の折り合い)、版混在時の未確定 cleanup の release 権限を
含める。

**理由:**
- 自己保持で `held` を返す旧挙動は、待ち手が `acquired` の exact 一致しか受理しないため
  最大 7200 秒の無言空転になる。実害 4 例を数え、うち 1 例は待ち手そのものを迂回させた。
- 更新を伴わない受理は不十分である。保持したまま 2 走目を回すと TTL (2400 秒) を超え、
  自分の lease が stale として他 wave に回収される。更新は「進める」ことと不可分である。
- 更新の実効性には flock 取得**後**の mtime 再取得が要る。取得前の snapshot で stale を判定すると、
  更新直後の lease を先行 claimant が回収でき、更新したという報告と実際の排他が食い違う。
- 更新失敗を例外として外へ出すと helper が内部エラーで終了し、待ち手が所有権を確定できないまま
  cleanup で **稼働中の lease を release** する。失敗は必ず構造化して返す必要がある。
- invocation の識別は受入結果を受理してよいかの条件そのものであり、正しさの機構に触れる。
  設計択一が割れるものを wave 側で凍結しない。

**却下した選択肢:**
- release して取り直す — 待ち行列の最後尾へ戻り、解放窓で並行受入の穴が開く (裁定で却下済み)。
- 専用の `renew` subcommand を足す — 裁定は `claim` へ寄せており、状態語彙を増やす利益がない。
- `holder_self` が真なら状態を問わず受理する — 旧形の `held` まで通り、deadlock を別の形で残す。
- 版混在のための互換層 — 未知状態は fail-closed が既定であり、互換層は穴を静かに広げる。
- stale な自己保持も更新する — TTL 超過は排他喪失の可能性を意味し、黙って延命すると
  直列化の意味論が壊れる。従来どおり回収 → 再取得に倒す。
