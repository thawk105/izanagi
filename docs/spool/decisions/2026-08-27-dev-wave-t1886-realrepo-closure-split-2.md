---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1886-realrepo-closure-split
seq: 2
---

## {{D:realrepo-lock-key-common-dir}}. real-repo lock key は資源ごとの Git common-dir から導く

**決定:** D1008 が定めた「lock file の path は repo root の realpath から決定的に導出する」を、
**資源ごとの Git common-dir realpath から導出する**へ改める。保証の射程 (同一 host・同一
filesystem まで、cross-host 排他は主張しない) は変えない。

移行のあいだは、旧 (worktree root) key と新 (common-dir) key の**両方を、常に旧・新の固定順で
同じ mode により取得する**。順序を固定するのは deadlock を作らないためである。
Git 解決に失敗したときに worktree root の key へ落ちる fallback は作らない。

**理由:**
- 同じ Git common-dir を共有する sibling worktree は、object database と linked-worktree registry を
  共有しているのに、repo root 由来の key では別の lock file を取っていた。**排他が成立していない。**
  izanagi は日常的に 10 本以上の linked worktree を並行させるため、これは仮想の穴ではない。
- 切り替えるだけだと、移行のあいだ旧コードの session と新コードの session が別 lock file を取り、
  互いを排他しない。両取りにすればどちらの世代とも排他できる。
- fallback を作ると、Git 解決が失敗した session だけが他と排他されない状態を静かに作る。

**却下した選択肢:**
- 新 key への一括切り替え — 移行期に排他が消える窓を作る。
- 旧 key の即時廃止 — 同上。旧世代の稼働 session を止められる保証がない。
- lock 取得より前に common-dir を解決する形 — 解決の `git rev-parse` 自体が無保護な実 repo 読取りになる。
  旧 key を取ってから解決する。

## {{D:realrepo-conflict-edges-same-shard}}. 衝突する loadgroup は同一 shard へ寄せ、group は分けたまま残す

**決定:** 実 repo / 実 submodule の同じ資源へ触れ、少なくとも一方が writer である loadgroup の対を
**独立した exact な集合として宣言し、shard 割付の連結成分を union する。**
runtime の loadgroup 名は分けたまま残し、同一 shard 内では従来どおり別 worker で並行に走らせる。

宣言した衝突辺の集合は、production の行列と**独立に書いた golden との完全一致**を先に検査してから
連結成分の検査へ進む。行列自身から golden を導出してはならない。

**理由:**
- shard は別 process・別 host で走りうるため、`/tmp` の flock は shard を跨いで効かない。
  衝突する仕事が別 shard へ行くと、どの機構でも排他されない。
- 一方、衝突する node を 1 つの loadgroup へ統合すると単一 worker 上の直列鎖になる。
  実測では 83.5 秒と 52.0 秒の 2 group が並行に走っているものが 135.6 秒の鎖になり、
  5 分の絶対上限に対する余裕を半分近く失う。**排他の細分化を選んだ既裁定と逆向きである。**
- shard 割付は file と group 名しか union しないので、資源の衝突はこの層から見えない。
  見えないものは明示的に宣言するしかない。
- 行列から golden を導出すると、辺を消す変異が検査対象ごと消えて必ず生存する。

**却下した選択肢:**
- 全衝突 node を canonical group へ統合する — 上記の直列鎖を作る。
- shard を跨ぐ排他を filesystem lock で作る — 保証の射程を広げる設計変更であり、別裁定が要る。
- 衝突辺を持たず「同じ file にあるから同じ成分」に頼る — file 境界と資源境界は一致しない。

## {{D:realrepo-lock-manager-per-process}}. real-repo lock は資源ごとに 1 process 1 fd とし、同一 process 内では昇格する

**決定:** real-repo の flock は、資源 (および移行期の旧・新 key) ごとに **1 process 1 fd** を共有し、
参照 count と mode の優越 (共有 < 排他) を持つ manager が管理する。同一 process 内で
共有を保持したまま排他が要求されたら、**同じ fd の上で排他へ昇格**し、内側が終わったら
**同じ fd の上で共有へ降格**する。全保持者が抜けたときだけ解錠して fd を閉じる。

**理由:**
- 別 fd を開くと、同じ process が同じ資源へ共有と排他を取ろうとした時点で自分自身と競合し、
  deadline (245 秒) いっぱい待って落ちる。module scope の共有 fixture を保持したまま
  同じ module の function scope の排他 fixture へ入る経路が実在した。
- `flock` は同じ fd に対しては再入し、昇格・降格が解錠を挟まずに行える。
  したがって別 process に対する排他は 1 bit も弱まらない。
- 有効 mode を保持者の最大値にすれば、内側の排他が終わるまで外側の共有保証は排他に強められるだけで、
  弱まる向きの遷移が起こらない。

**却下した選択肢:**
- 衝突する fixture を別 module へ移す — nodeid が変わり、逐語 pin を持つ consumer を巻き込む。
  かつ「同じ process に載らない保証」は scheduler の実装依存で、契約として書けない。
- 共有の保持期間を縮めて `yield` を覆わない形 — consumer が実行中に実 repo を読み直すため、
  保護の穴を作る。
- 再入を許す独自の再帰 lock を作る — flock の意味論から離れ、別 process との相互作用の検証面が増える。
