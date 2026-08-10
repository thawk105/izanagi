---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t510-ruleops-git-budget
seq: 2
---

## {{D:ruleops-git-timeout-budget}}. ruleops の git timeout は subcommand 別の作業量比例予算にする

**決定:** `tools/ruleops.py` の固定 `GIT_TIMEOUT_SECONDS = 20` を廃し、
`min(BASE + units x rate, CAP)` の per-call 予算へ置き換える。units と rate は subcommand で決める。

- `log`: units = snapshot 捕捉時に一度数えた commit 数、rate = `PER_COMMIT` (0.035 秒/commit)
- `diff-tree --stdin`: units = stdin 行数、rate = `PER_COMMIT` (同じ tree diff 作業)
- `cat-file --batch`: units = stdin 行数、rate = `PER_REQUEST` (0.013 秒/要求)
- `grep` / `ls-tree` / `rev-parse` / `merge-base` / `for-each-ref` / `cat-file -t` /
  `cat-file blob`: BASE 20.0 秒に据え置く

`CAP = 300.0` は rate から独立した literal で、**1 回の git 呼び出しの絶対上限であって
1 走行の累積上限ではない**。commit 数の取得は既存 closed set 内の `log --format=%H` で行い、
`rev-list` を `_GIT_SUBCOMMANDS` へ足さない。この bootstrap 自身は循環回避のため BASE 固定とする。
timeout の detail には mode label と実予算を載せる。reason 文字列 `git-timeout`、CLI exit code 2、
retry の不在は変えない。

保証するのは次である。**timeout 以外の validation predicate は変えない。予算延長で新たに rc=0 に
なるのは、同一 snapshot 上で git が完全な正常結果を返し後続の全検証を通った走行に限る。**
部分結果・retry・握り潰しによる rc=0 は作らない。ただし bootstrap は履歴の走査可能性を新たに
要求するため、祖先 object を欠く repo は `git-failed` で落ちる。これは受理集合を狭める方向の
変更であり、意図的に fail-closed のまま残す。

**理由:**
- D172 は同じ定数を「変えない」と決めていたが、解除条件として「閾値の変更・retry の導入は、
  原因が理由行付きで特定できてから独立に裁定する」を自ら明記していた。理由行付きの再発が
  3 回記録され、ユーザー裁定が下りた時点でこの条件は満たされる。本 D は D172 を迂回せず、
  その解除条件に沿って supersede する。
- D172 の却下理由「理由不明のまま上げると、真に固まった git を待つ時間だけが伸びる」への回答が
  subcommand 別の設計である。伸びるのは実際に重い呼び出しだけで、軽い 7 種は 20 秒のまま動かない。
- **欠陥は履歴長への非追随だけではなかった。** 一次資料の失敗記録が示す実際の経路は
  `inventory` の `cat-file --batch` と path 限定 `log` で、無負荷実測はそれぞれ 0.609 秒
  (6,494 要求 / 99,981,192 bytes) と 0.437 秒 (2,402 commit) である。20 秒での打ち切りは
  33〜46 倍の尾部事象を意味する。作業量で課金することは、**観測された尾部倍率を大きく上回る
  余裕を各呼び出しへ与える**手段として機能する (それぞれ 171 倍・238 倍)。
- 定数は各経路自身の打ち切り観測から導いた。`PER_COMMIT` = 20/2402 = 8.33e-3 秒/commit に
  安全係数 4、`PER_REQUEST` = 20/6494 = 3.08e-3 秒/要求に同じ係数。線形式は仮説であって
  保証ではなく、再較正トリガを production comment に書いた。

**却下した選択肢:**
- 定数の一律引き上げ — 履歴長にも要求数にも追随せず、D172 が却下した形そのものである。
- stdin 行数だけを単位にする既存 module の方式の流用 — ruleops の重い呼び出しのうち
  `log` 族は stdin を持たないため単位が取れない。
- 別 module が確定した 0.0086 秒/要求の流用 — あれは `--batch-check` (header のみ) の実測で、
  本 module が使う `--batch` (本文込み) とは protocol が違う。
- `CAP` を `BASE + 上限 x rate` の式で書く案 — rate を上げた分だけ天井が伸び、絶対上限にならない。
  値が偶然一致しても構造として誤りなので、代入 RHS が単一 literal であることを `ast` で固定する。
- workload に `min(units, N)` の clamp を置く案 — CAP が先に効くため semantic kill にならず、
  かつ N を大きく取る変異をテスト点の追加では原理的に殺せない。clamp の不在を `ast` で検査する。
- `rev-list --count` の導入 — read-only closed set を広げる。既存 `log` で同じ値が
  0.034 秒で得られるため、防壁を広げる理由がない。
- retry の導入 — D172 が却下したとおり、観測すべき事実を隠す。本 D でも導入しない。
