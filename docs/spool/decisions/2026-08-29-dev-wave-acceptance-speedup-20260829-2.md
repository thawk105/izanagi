---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: dev-wave-acceptance-speedup-20260829
seq: 2
---

## {{D:acceptance-tmpdir-axis-refuted}}. 受入の実効 TMPDIR を共有 filesystem へ移す案は採らない

**決定:** 受入形の実効 `TMPDIR` を node-local `/tmp` から Lustre 等の共有 filesystem へ移す案を
**採用しない。実装差分ゼロで閉じる。** 一時領域の置き場を理由に受入 wall を語る提案は、
**計算ノード regime の実測を添えない限り再提案しない。**

**理由:**

- **効く場所が無い。** 受入成果物の全数解析で、549 session 中 549 が shard を計算ノードへ
  dispatch している (母集合 568、dispatch-intents なし 1、confirm/handled 欠落 18 を除外)。
  ログインノードで走るのは全件 `--collect-only` の**単一 process** 1 回だけである。
- **計算ノードでは `/tmp` が両軸で勝つ。** bnode041、48 core、loadavg 0.80 の実測 (wall 秒) で、
  fsync は `/tmp` 0.058 対 Lustre 0.193 (3.3 倍)、小 file 生成は 0.235 対 2.805 (12 倍)。
  `/tmp` は n=1 の 0.012 秒から n=48 の 0.058 秒までで**崩れない**。
- **絶対量が問題にならない。** 計算ノードの fsync 費用は 48 並列でも 0.2 秒未満で、
  実行の中央値 191 秒の 0.1% にも満たない。この機構では wall を動かせない。
- **ログインノードの崩れは実在するが受入とは無関係である。** pegasus02 では
  `/tmp` の fsync が n=1 の 19.4 ms/回 から n=32 の 291 ms/回 へ 15 倍悪化し、
  総処理量は約 110 fsync/s で頭打ちになる (median column)。しかし崩れには並列度が要り、
  ログインノードで走る `--collect-only` は単一 process なので発火しない。
- **単一 process の測定でこの軸を裁定してはならない。** n=1 だけを見ると Lustre は
  metadata が 30 倍遅く、逆の結論になる。並列度を変えて初めて順位が決まる。
- **設計どおり入れると正しさ防壁が退行する。** 提案は明示 `TMPDIR=/tmp` を尊重し未設定時だけ
  共有 root を使う形だったが、その 2 種類の session が同時に同じ tree を触ると
  別々の filesystem 上の lock を取り、**互いに排他しない**。現状は両者が同じ `/tmp` lock を
  使うので現行保証からの退行である。詳細は {{F:tmpdir-mixed-regime-lock-fragmentation}}。
- **共有 root の stale prune が別ホストの live な状態を壊す。** 既存の 6 時間 prune は
  自 session の key しか保護しないため、共有化すると別ホストの live な memo と `.lock` を消す。
  open 中の lock file を unlink すると新しい inode ができて lock identity まで分断される。
- **共有 filesystem 上の POSIX 保証を示す gate が無い。** 一時領域は `os.replace`、
  file と directory の `fsync`、`os.link`、別 client からの即時可視性まで load-bearing だが、
  本 wave の probe は単一 host の flock と `O_EXCL` までしか示していない。

**却下した選択肢:**

- **ログインノード形に限定して入れる** — 実受入で発火しない形を「受入全走の高速化」として
  実装することになる。日常の焦点走は速くなりうるが、それは別の目的であり別に諮る。
- **ログインノードの paired 全走で採否を決める** — 測定形が実 regime と違う。
  加えて shard 数を 1 にしても login admission が dispatch を選べば計算ノードへ送られるため、
  その測定形自体が保証されない。
- **tmpfs へ戻す** — ユーザーの memory cgroup 16 GiB を直接削る。受入 1 走の tmpfs peak は
  7.39 GiB で、2 走並ぶと使い切る。既存の fstype ガードも tmpfs 族を拒む。

## {{D:acceptance-phase-decomposition}}. 受入の所要は会計サマリの 4 層で語り、queue 待ちを律速と呼ばない

**決定:** 受入の所要を語るときは、次の 4 層を出所付きで分けて書く。
**queue 待ちを短縮対象として提案しない** — 中央値では job の 5.1% にすぎない。
session 合計と job 合計の差 (約 75 秒) は**未分解であり、分解したかのように書かない。**

| 層 | 中央値 | 出所 |
|---|---|---|
| queue 待ち (Created→Started) | 9 秒 | NQSV 会計サマリ、n=1297 |
| 計算ノード上の実行 (Elapse) | 191 秒 | NQSV 会計サマリ、n=1297 |
| job 合計 (Created→Ended) | 263 秒 | NQSV 会計サマリ、n=1297 |
| session 合計 (confirm→handled) | 338 秒 | 成果物 mtime の proxy、n=549 |

**理由:**

- **一次資料は scheduler 自身の会計サマリである。** 各 job の stderr 末尾にある
  `Created / Started / Ended Request Time` と `Elapse` を全件 parse した
  (対象 1297、会計サマリ無し 0、parse 失敗 0)。dispatch receipt の `queue_wait_s` は
  測点の違う別量であり (中央値 5.2 秒、n=1294)、向きは一致するが会計サマリを権威とする。
- **queue 待ちは中央値では小さいが裾は重い。** p75 75 秒、p90 307 秒、max 1231 秒。
  session は K=3 の shard 全部の終了を待つので、session が払う待ちは 3 回の抽選の最大値に近い。
  **中央値だけで裾を語らず、裾だけで中央値を語らない。**
- **1 session からの一般化は成立しない。** 親が最初に開いた session は shard が
  `queue-wait-timeout` で qdel されており、そのまま一般化すれば「所要は timeout が支配」と
  誤読しえた。全数では該当 session は 549 中 14 本 (2.6%) の例外である。
- **pytest wall の分布も同じ資料から取れる。** job stdout の要約行を全件 parse すると
  shard あたり中央値 181.4 秒 (n=1269、要約行なし 28)。3 shard 揃った 206 session の
  最大 shard 中央値は 244.9 秒で、D1260 の paired K=3 実測 244.810 / 245.707 秒と一致する。
  D1260 の一次資料は 3 走ずつだったので、これは独立な裏取りである。
- **shard 不均衡は割付では取れない。** 3 shard 揃った 206 session の shard 間最大差は
  中央値 116.3 秒 (p90 225.0) ある。総和の中央値 469.4 秒を 3 等分した 156.5 秒と
  実測の最大 shard 244.9 秒の差は 88 秒だが、D1019 が「完璧な予言者でも利得は 0.0 秒」を
  実測済みであり、real-repo の排他 group が 1 worker に直列で載り続けることが理由である。
  **本集計は D1019 を反証せず裏取りする** — D1019 の一次資料は K=2 の 2 走であり、
  本集計は K=3 の 206 session で同じ大きさの不均衡が残ることを示す。
  **鎖が律速である以上、不均衡はその影であって原因ではない。**

**却下した選択肢:**

- **session 合計だけで「受入は遅い」と語る** — mtime proxy であり、queue 待ちと
  親側の検知遅れを含む。層を分けずに 1 つの数で語ると短縮対象を誤る。
- **残余 75 秒の内訳を推測で書く** — 候補 (collection、帳簿処理、検知遅れ) は挙げられるが
  現 artifact では分解できない。分解していないものを分解したと書かない。
- **shard 不均衡 116 秒を短縮余地として計上する** — D1019 の反実仮想が 0.0 秒を示している。
