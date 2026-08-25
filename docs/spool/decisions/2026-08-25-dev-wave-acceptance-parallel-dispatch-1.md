---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-acceptance-parallel-dispatch
seq: 1
---

## {{D:acceptance-wall-decomposition}}. 受入全走の所要は 4 相へ分解して測り、compute 相の下限は real-repo 直列鎖で決まる

**決定:** 受入全走の所要を論じるときは、次の 4 相へ分解した値で論じる。単一の総時間や
pytest の総時間だけを根拠にした高速化案は採らない。

| 相 | 中央値 | 母集合 |
|---|---|---|
| login preflight (claim・merge・全史 provenance 監査・dispatch 準備) | 96 秒 | pid→intent の実測 7 本 (64/70/92/96/104/123/643) |
| PBS queue 待ち | 14 秒 (平均 111、最大 849) | 141 session |
| compute job | 288 秒 | 141 session |
| 併合・後処理 | 約 17 秒 | session 内 mtime |
| **end-to-end** | **471〜502 秒** | pid→done の実測 12 本 |

compute 相の内訳は 288 session 分の shard report で安定している。

- shard-0: pytest wall 中央値 275 秒 = pole 中央値 211 秒 + 残余中央値 63 秒
- shard-1: pytest wall 中央値 139 秒 = pole 中央値 92 秒 + 残余中央値 47 秒
- pole は `real-repo` loadgroup を 1 worker が抱えた時間そのもので、shard-0 の ideal
  (busy/48) を常に上回る

**理由:**
- D820 は「shard 数の増加と shard 間 balance の是正は現行の worker 数では律速を動かさない」と
  決めた。本決定はその母集合を pole の中身が入れ替わった後で取り直し、結論が保たれることを
  確認したものである。ある session の実測では real-repo 183.9 秒 (74 test) に対し
  shard-0 の busy 合計は 5954 秒・ideal は 124.0 秒で、pole が ideal を 60 秒上回っていた
- 割付 weight は `tools/acceptance_shards.py` が item 件数で計算しており所要時間を見ていない。
  それでも shard-0 は pole 拘束なので、weight を所要時間へ変えても max(shard) は動かない
- 相分解を経ずに「pytest が遅い」とだけ見ると、実際には pytest の外にある
  login preflight (全体の約 20%) を取り逃す

**却下した選択肢:**
- shard 数を 3 へ上げる — D820 の実測に加え、本決定の母集合でも pole > ideal が保たれるため
  max(shard) が動かない。受領証の `env_projection` を動かす副作用だけが残る
- `real-repo` loadgroup を分割する — 直列性が防壁そのものであり規律 2 に反する。D820 が却下済み
- 総時間だけを見て高速化案を選ぶ — 相ごとに律速の性質が違うため、効かない層へ投資することになる

## {{D:pytest-rewrite-cache-already-warm}}. pytest の assertion-rewrite cache は受入で既に効いており、外部 cache を足しても利得はない

**決定:** 受入全走の高速化手段として、repo 外の共有 bytecode / assertion-rewrite cache を
新設しない。既存の repo 内 `__pycache__` が既に同じ役割を果たしていることを実測で確定した。

**実測:**
- 計算ノードで test を 1 件も実行しない走行 (48 worker) の所要は、cache を持たない worktree で
  49.32 秒、cache を満たした worktree で **15.40 秒**。差は 33.9 秒
- しかし実在する wave worktree 49 個はすべて 548〜577 件の `.pyc` を持ち、うち 247〜259 件が
  pytest rewrite cache である。mtime + size 照合でいずれも 100% 有効だった
- ある wave の 4 回の受入は、それぞれ 254 / 255 / 258 / 258 件 (全 258 件中) の rewrite cache が
  **既に書かれた後**に走っていた。cache 最古 09:57 に対し受入は 11:48・12:06・12:45・13:12
- login 側の focus 走が repo 内 `__pycache__` を書き、計算ノードは読み出しだけを行う。
  dispatch が計算ノードの子へ渡す `PYTHONDONTWRITEBYTECODE=1` は**書き込みしか止めない**
  (`_pytest/assertion/rewrite.py` の `write = not sys.dont_write_bytecode`)

**理由:**
- 上の 49.32 秒は「pytest を一度も走らせていない新品 worktree」でしか出ない値であり、
  実運用の受入はこの条件に入らない。probe の条件が本番を代表していなかった
- 外部 cache を新設する案は、独立 2 レンズの敵対相談がいずれも NO-GO と判定した。
  (a) generation identity が pytest version だけでは不足する。rewrite 結果は
  `Config` の `enable_assertion_pass_hook` にも依存する。(b) 走行前の sidecar 検証では
  F52 型の TOCTOU が閉じない。受入の tree fingerprint は走行前後の境界しか見ないため、
  走行中の同一長・同一秒の往復を観測できない。(c) rewrite cache を作るには
  `sys.dont_write_bytecode` を解除する writer が要り、「子に bytecode を書かせない」現行の
  防壁と両立しない
- 全 `.py` の内容 digest で generation を鍵付けする設計の実 hit 率は 8.0% (直近 3 日の
  受入受領証 112 件を tested tip の Python tree で比較)。損益分岐は 24〜33% なので、
  採用すれば 1 走あたり平均で悪化する

**却下した選択肢:**
- `PYTHONPYCACHEPREFIX` で repo 外へ cache を集約する — 上記のとおり利得がゼロで、
  正しさの穴が 3 件残る
- `compileall` で warm する — 利得の主部である rewrite cache を作れない。実測で
  cache 無し 32.78 秒に対し 31.34 秒にしかならなかった
- 子の bytecode 書き込み禁止を緩める — F52 の再発面を広げる。速度のために正しさゲートを
  緩めない (規律 2)
