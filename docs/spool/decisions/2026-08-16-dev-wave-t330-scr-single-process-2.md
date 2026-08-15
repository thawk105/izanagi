---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t330-scr-single-process
seq: 2
---

## {{D:t330-return-zero-diff}}. `/scr` fresh namespace を `single_process` 強制から切り離し、強制側は実装差分ゼロで再裁定へ返す

**決定 (1): 実装差分ゼロで再裁定へ返す。** 2026-08-03 の裁定は「使用権を供給する wrapper の新設と
セットで実装する」形を指定し、その wave の追加条件は「caller が実在することをテストで固定する」で
あった。現行 main ではこれが満たせない。`campaign.loop.run_campaign` へ到達する計算ノード caller は
実在するが、repo 外・untracked の wave 専用 job script であり tracked なテストで固定できない。
tracked 化するには 8c を計算ノードで運転する wrapper を新設するしかなく、それは D125 決定 (6)、
D108 決定 (2)〜(5) の campaign task 凍結、および T-276 / 8c live pilot 側の所有境界である。
**本決定はその境界を開かない。**

**決定 (2): `/scr` fresh namespace は本件から切り離す。** 対象を取り違えていた。
床値 wrapper は依存を `/scr/${PBS_JOBID}` へ build して `CMAKE_PREFIX_PATH` へ export し、
v2 build identity は dependency prefix を path 要素の配列として pre-image に束縛する (D125 決定 (3))。
したがって床値経路は durable な cache root を使っていても job ごとに digest が変わり、
跨ジョブ cache hit は構造的に起きない。加えて F319 の汚染対象は third-party source cache であり、
本件が動かそうとしていた build-variants cache root ではない。
**懸念自体は 8c 経路 (共有 checkout の `build-variants` と `TMPDIR` 未設定時の `/tmp` checkout) で
生きている**が、それは F319 の恒久対応と同じ層であり、その所有者へ返す。

**決定 (3): 差分ゼロは「解決済み」を意味しない。** `loop.run_campaign` は required attestation を
発火させる一方、claim 取得・reservation 検査・`allow_resume=False` 拒否をいずれも行わない。
Pegasus 契約は `single_process=True` / `allow_resume=False` を宣言しているので、これは
**宣言だけで強制しない gate** である。8c live pilot の transport 欠陥が直った時点で、この sink は
単独性が未検査のまま exploratory WAL・report・binary を受理し始める。再裁定はこれを止めるためのもので
あり、本決定は現状維持を推奨するものではない。

**決定 (4): 発火 caller が既に実在する穴を先に直す方を推奨する。** 床値 campaign の claim identity は
秒精度の run ID であって protocol 単位の排他ではなく、reservation は caller の自己申告である。
こちらは発火 caller (床値 campaign) が実在するため DW-G04 を確実に満たす。

**理由:**
- 発火 caller を持たない強制は「謳うだけで発火しない gate」になる (DW-G04)。2026-08-03 の裁定自身が
  部分実装を明示的に禁じており、その禁止を wave 側で黙って解除しない。
- 別タスクが所有する裁定対象 (8c の計算ノード運転、F319 の恒久対応) を、実装の都合で横取りしない。
- 差分ゼロでも、宣言と強制の乖離を台帳へ残さなければ次の実装者が同じ調査を繰り返す。

**却下した選択肢:**
- 強制だけを先に入れる — 2026-08-03 の裁定が明示的に禁じた形であり、解除はユーザー手番である。
  再裁定の択一としては残す。
- 8c 用 tracked wrapper を本件で新設する — 他タスクが所有する境界を独断で開く。
- `/scr` へ cache root を一律移設する — 床値では既に job ごとに cold であり、F319 も閉じない。
  1 cell あたり build cap 900 秒の予算を cold build で圧迫するだけになる。
- 「前提が失効したので完了」として閉じる — 失効したのは wrapper 不在の前提だけで、
  宣言と強制の乖離は生きている。完了扱いは事実に反する。
