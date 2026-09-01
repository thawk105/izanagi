---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2098-session-job-gap
seq: 1
---

## {{D:session-job-gap-is-mostly-a-unit-mismatch}}. session 合計と job 合計の差 約 75 秒は、ほぼ全量が観測単位の違いであって費用ではない

**決定:** D1320 が未分解として残した「session 合計 338 秒 − job 合計 263 秒 = 約 75 秒」を、
**費用の内訳として語らない。** この差は 549 session の中央値から 1297 job の中央値を引いた
非対差であり、観測単位も母集合も違う。session は K 本の shard のうち**最も遅い 1 本**を待つので、
「全 job の中央値」は session が待つ量ではない。

以後、受入 session の所要を語るときは次の 3 量を分けて書く。定義と時計も併記する。

| 記号 | 定義 | 時計 |
|---|---|---|
| `S` | `max_j H_j − min_j F_j` (session envelope) | ログインノードが書く marker mtime 内で閉じる |
| `Env` | `max_j E_j − min_j C_j` (scheduler envelope) | NQSV 会計時刻内で閉じる |
| `Jmax` | `max_j (E_j − C_j)` (最長単体 job) | 同上 |

`F` = `shard-j.confirm.json` の mtime、`H` = `shard-j.handled.json` の mtime、
`C` / `E` = NQSV 会計の `Created` / `Ended Request Time`。
`Rout = S − Env`、`Skew = Env − Jmax`、`Rpair = S − Jmax` はいずれも**期間どうしの差**なので、
静的な時計 offset に依存しない。**時計を跨ぐ引き算を主推定量に使わない。**

**実測 (親が実行、主集合 680 / 母集合 739 session、2026-09-01T22:15:56Z 〜 22:16:11Z の走査):**

- 対の残差 `Rpair` の中央値は **14 秒** (p25 12 / p75 15 / p90 16 / 最小 9 / 最大 67)。
  内訳は `Rout` 13 秒と `Skew` 1 秒。
- 全 shard の job span の pooled 中央値は **259 秒** (n = 1720)。
  `median(S) − median(全 shard の job span) = 339 − 259 = 80 秒`で、これが歴史的な 75 秒と同じ形の量である。
- その 80 秒は `(339 − 327) + (327 − 259) = 12 + 68` と割れる。
  **68 秒が観測単位の違いによる分**であり、費用ではない。
- **`median(S) − median(Jmax) = 12` と `median(S − Jmax) = 14` は一致しない。**
  中央値は項別に足し引きできない。80 秒の 2 分割は中央値の値の間の算術であって、session ごとの分解ではない。
- `Rout` は行ごとに `head + tail` に等しく、`head` は 680 行すべてで −2 秒以上 0 秒以下である。
  したがって**どの行でも `Rout` は `tail` (最後の `Ended` → 最後の `handled`) の 2 秒以内**にある。
- `confirm` は qsub が返った後に書かれるため `Created` は必ず `confirm` 以前であり、
  投入前の帳簿処理は残差の内訳にならない。

**理由:**

- D1320 は「session 合計と job 合計の差は未分解であり、分解したかのように書かない」と明記した。
  本決定はその差が**そもそも量として成立していない**ことを実測で示すものであり、
  D1320 の禁止を解くのではなく、禁止が正しかった理由を与える。
- 加法分解は代数の恒等式であって検証ではない。`Rpair = Rout + Skew` は 680 行すべてで
  ns 差 0 だが、これは実装が同じ値から両辺を作っているだけである。
  独立検査は別に置き、種別を `恒等式` / `自己整合` / `診断` / `反証可能` に分けて記録した。
- 唯一の外部反証可能な検査 (D1320 cohort の再現) は **fail** した。cutoff 2026-08-29 で
  fallback あり `(586, 1, 26, 559)`、fallback なし `(559, 0, 0, 559)` となり、
  目標 `(568, 1, 18, 549)` と件数が一致しない。**合わせ込んでいない。**
  一方、中央値 338 秒は両版・両候補式で再観測された。両候補式が同じ値を出すため、
  D1320 がどちらの集計式を使ったかは**同定できない**。

**この決定が変えないこと:**

- 短縮の実装・提案はしていない。D1035 が指す排他閉包の細分化にも踏み込んでいない。
- D1420 (pytest wall 層の残差 約 58 秒、計算ノード 48 worker の全 collection 約 51.7 秒) は
  自ら job 層・session 層へ一般化しないと書いており、本決定と対象が重ならない。内側は測り直していない。
- 受入の判定・排他・選択・受理集合を 1 bit も変えていない。新規の受入走行は 0 本である。

**主張の射程:**

走査は snapshot ではない (実測中もコーパスは増えた)。主集合は complete-case (680 / 739) であり、
timeout・qdel・共有 deadline・遅い会計で marker や `Created` / `Ended` が欠けると
**長時間側が選択的に落ちうる。** 偏りの向きと大きさは確定できない。
104 checkout 群・2 か月・K=2 と K=3 が混ざった集団であり、**単一の受入の姿として語れない**
(月別の `S` 中央値は 8 月 334 秒 / 9 月 369 秒、K 別は K=2 が 333 秒 / K=3 が 357 秒)。

**却下した選択肢:**

- **75 秒を per-session の残差として分解する** — 非対差なので分解する対象が存在しない。
  段 3 の 2 レンズが独立に BLOCKER として指摘した。
- **`max_j (E_j − C_j)` を session の臨界経路と呼ぶ** — shard ごとに `Created` がずれるため、
  短いが遅く開始した job が最後に終わりうる。scheduler の包絡は `max_j E_j − min_j C_j` である。
  実測では両者の差 (`Skew`) の中央値は 1 秒 (最大 6 秒) と小さかったが、成立しない定義は使わない。
- **file の mtime を単一の時計として扱う** — marker はログインノード・計算ノード・scheduler の
  3 者が書く。共有 filesystem 上でも同一時計である保証がない。
  主推定量から時計を跨ぐ引き算を追い出し、`head` / `tail` の 2 項分割だけを
  offset 込みの生値として別枠に出した。

## {{D:login-collection-is-not-on-the-observed-critical-path}}. ログインノードの全件 collection は、保存された marker の順序では臨界経路に載っていない

**決定:** 受入 session の所要を語るとき、**ログインノードの全件 `--collect-only` を
短縮対象の候補に挙げない。** ただし「寄与は 0 秒」とも書かない。

**実測:** `login-collection.log` の mtime が最後の `handled` の mtime より後だった session は
**0 件**である (主集合 680 件すべてが `off_path`、母集合 739 件でも `on_path_candidate` は 0 件、
判定不能 47 件)。比較した 2 つの marker はどちらもログインノードが書くので時計が揃っている。

**理由:**

- `tools/acceptance_shards.py` は全 shard の dispatcher worker を `start()` した**後**に
  `collect_login` を同期実行し、その後に worker の結果を待つ。
  `tools/run_tests.py` の `_collect_login_universe` の docstring も
  「compute shard と並行に login 親で独立の U を観測する」と書いている。
  設計上、collection は job の実行区間と重なる。
- 計算ノードが書く `report.json` や `junit.xml` とは比較していない。別ホストの時計になるためである。

**この決定が主張しないこと:**

- **「collection が親を遅らせなかった」とは言えない。** 2 つの理由がある。
  (a) `login-collection.log` の mtime は collection の subprocess が返った後の log 書込み時刻であり、
  collection の終了そのものではない。
  (b) 親は collection が返ってから worker の結果を読み始めるので、
  順序が先でも、既に ready だった worker を待たせた可能性は残る。
- 言えるのは marker の順序までである。因果的な寄与を出すには、collection の開始・復帰、
  各 worker の payload ready・送信、親の受信開始を同一 login monotonic clock で刻む必要がある。

**却下した選択肢:**

- **`off_path` を「寄与 0 秒」と読む** — 上記 (a) (b) により因果を含意しない。
- **計算ノードの `report.json` の mtime と比べる** — 書き手のホストが違い、時計の同期保証がない。

## {{D:receipt-queue-wait-is-not-scheduler-queue-wait}}. receipt の `queue_wait_s` を NQSV 会計の queue 待ちの代用にしない

**決定:** dispatch receipt の `queue_wait_s` と、NQSV 会計の `Started Request Time − Created
Request Time` を**別量として扱い、一方を他方の代用にしない。** 会計値を権威とする。

**実測 (比較できた 1737 shard):** 差 (`queue_wait_s` − 会計値) は**全行で負**である
(最大 −1.41 秒、p90 −1.77、p75 −2.69、中央値 −2.99、p25 −14.58、最小 −789.75 秒)。
照合 session の shard-0 では 5.34 秒 対 208 秒だった。

**理由:**

- `queue_wait_s` は qsub が復帰した時点から、qstat の状態が初めて `RUN` と解釈されるまでを測る。
  D805 の正規化は `staging` と `queued` を `QUE`、`running` と `pre-running` を `RUN` へ写すので、
  実行開始より前に `RUN` になりうる。
- 会計値は `Created` から `Started` までであり、起点も終点の意味も違う。
- D1320 も両者を別量と書き会計を権威としていた。本決定はそれを全数の符号で裏づける。

**この決定が主張しないこと:**

- どちらが「正しい queue 待ち」かは述べない。差の原因 (NQSV の staging か、qstat の表示仕様か、
  state の解釈か) は保存された記録からは断定できない。後続 poll の生 qstat 応答が
  receipt に残らず、正規化後の `state` だけが残るためである。

**関連する診断:** `Elapse` と `Ended − Started` も一致しない (1740 shard で差は全行正、
中央値 4 秒、範囲 1〜10 秒)。同値と仮定せず、この差を起動費用・終了費用と呼ばない。
