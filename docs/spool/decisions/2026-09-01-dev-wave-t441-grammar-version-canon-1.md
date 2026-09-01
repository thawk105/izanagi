---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t441-grammar-version-canon
seq: 1
---

## {{D:backoff-canonicalize-at-materialization}}. hole の数値正準化は台帳併記でなく材料化で行う

**決定:** D901 条項 3 の正準化は、受理判定を全部通過した後に**材料化するソースそのもの**を
`double now_backoff = <基数 10 整数>;` へ書き換えることで達成する。台帳へ正準形を別 field として
併記する案は採らない。拒否された候補には触れない。

**理由:**
- 併記案では raw source が綴りのまま残るため、`source_digest` の digest、variant id、
  legacy と v2 の cache key が綴りごとに分裂したままになる。D901 が条項 3 を置いた理由
  (「同じ値の別表記が別 token として台帳に残る」) を達成できない。
- 受理判定の後に置く限り受理集合は動かない。既存テストが `20` / `20.0` / `1e2` / `001` /
  `0x14` / `024` / `0b10100` / `2'0` / `0x1.4p4` / `0xFF` の 10 表記すべての受理を固定しており、
  判定の前に正準化を置くとこの期待を反転させることになる。
- 提出 bytes と材料化 bytes が分かれる代償はあるが、帰属検査は値の一致を見るので保たれる。

**却下した選択肢:**
- **台帳へ正準形を併記する** — 上記のとおり重複が畳まれない。
- **受理判定の前に正準化する** — 受理集合が動き、絶対規律 2 の面に触れる。

## {{D:backoff-grammar-version-explicit-campaign-arg}}. 文法版の source/cache 束縛は campaign 由来の明示引数で渡す

**決定:** D901 条項 2 の cache 束縛は、`source_digest` が編集された path を見て判定する形ではなく、
`run_campaign` から `pipeline.evaluate` を経て `source_digest` まで、**campaign config 由来の版を
keyword-only の追加引数で渡す**形にする。既定は `None` とし、既定経路の bytes は現行と変えない。

**理由:**
- path 判定では campaign 帰属を表せない。`include/backoff.hh` は hole 文法を通らない別 producer
  (`backoff_extended_sweep`、`b10_backoff_shape_sweep`) も材料化しており、path で判定すると
  版を持たない campaign の variant id と cache key まで動く。段 3 の 2 レンズが独立に指摘した。
- 明示引数なら「版を宣言した campaign だけが版付き token を得る」が構造で保証され、
  P2-4 の sweep campaign の既存 id は 1 byte も動かない。
- 同じ値が identity・WAL・source・cache へ渡るため、版の producer が 1 本になる。

**却下した選択肢:**
- **編集された path で判定する** — 上記のとおり非対象 campaign を巻き込む。
- **build admission policy の pre-image へ版を混ぜる** — 全 campaign の identity が動き、
  かつ「build 受入」と「文法の版」という別の意味を同じ識別子へ二義化する。

## {{D:backoff-reject-ledger-duplication-deferred}}. 拒否候補の台帳 token の重複は本項の scope 外とする

**決定:** `diffq_variant_id()` が拒否候補の raw implementation を hash するため、値が同じで綴りの
違う拒否は別 token のまま残る。これは実在する重複だが、本項では正準化しない。版の束縛だけを行う。

**理由:**
- D901 条項 3 の理由は「certified 選択の母集合を汚す」であり、拒否候補は母集合へ入らない。
- 拒否候補の literal を正準化するには、文法に落ちた入力へ値抽出器を走らせることになる。
  絶対規律 2 が守る面をわざわざ広げる方向であり、「正準化が判定より前に来る」型の危険を招く。
- 放置したときに変わるのは critic への診断入力の重複だけで、certified 成果物の値・受理集合・
  参照は変わらない。

**却下した選択肢:**
- **diffq の pre-image の中だけで literal を正準値へ置換する** — 段 3 のレンズが提案したが、
  拒否入力への値抽出という攻撃面を新設する。
