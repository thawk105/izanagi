---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1999-define-gate-family
seq: 4
---

## {{D:do-not-choose-the-analyzed-expression-to-pass-the-gate}}. 関門を通すために、解析される式を選ばない

**決定:** 静的な関門を緑にする目的で、**値が同じ複数の書き方のうち関門が通る方を選ぶことをしない。**
関門が式の書き方で判定を変えるなら、それは関門側の射程の問題として記録し、
除外は名前と理由の付いた形 (繰延べ台帳など) で表に出す。

**理由:**

- 実測でこの型を踏んだ。`s8b_oracle_driver.run_block` の `pipeline.evaluate` 呼び出しの
  第 1 位置引数を `prepared_for_eval.genome` から `prepared.genome` へ書き換えたところ、
  閉包検査の 22 セルが赤から緑へ変わった。`PreparedCell(genome=prepared.genome, ...)` なので
  **値は完全に同一**である。変わったのは検査側の分類だけで、`prepared` は `with ... as` の
  束縛なので `_expression_depends_on_scope_parameter` が追えず `proven-unreachable` になり、
  `prepared_for_eval` は `Assign` なので追えて `unresolved` になる。
- これは {{D:gate-adapts-to-build-not-build-to-gate}} (関門を通すために測定条件を変えない) と
  同じ型である。あちらは実 configure / build の引数、こちらは**解析対象の式**という違いだけで、
  「検査を通すために検査対象を変える」構造は同一である。
- **値が同じであることは免罪にならない。** 免罪にすると、以後どの関門も「同値な別の書き方」で
  回避できることになり、静的関門が一つも意味を持たなくなる。
- 緑と赤のどちらが正しいかは、式の選択ではなく**実行時にその sink が関門に支配されているか**で
  決まる。支配されていて静的に示せないなら、示せないことを記録する。

**却下した選択肢:**

- **値が同じなので書き方は自由とする** — 上のとおり、静的関門一般を無効化する。
- **検査側 (`_expression_depends_on_scope_parameter` / `coverage_for_sink`) を直して緑にする** —
  正しい方向だが受理集合を変える設計判断であり、本 wave の裁定の射程外。ユーザー裁定へ返す。

## {{D:record-gate-exclusions-by-name-not-by-silence}}. 関門の除外は、沈黙ではなく名前で残す

**決定:** 静的関門が sink を除外するとき、除外が**分類の副作用** (`proven-unreachable` など) で
起きているなら、それを緑の理由にしない。除外を、所有者と理由を書いた台帳 entry へ移して明示する。
成果物・記録には「0 件」ではなく**内訳**を書く。

**理由:**

- 閉包検査の「0 failure」は、実測では「真に被覆 40 / 誤って到達不能と分類 44 / 明示繰延べ 66」の
  合計だった。0 という数字だけを見た読み手は「全 sink が関門の下にある」と読む。**読み違える。**
- 誤った `proven-unreachable` は、除外されたことが**どこにも現れない**。台帳 entry なら、
  件数・所有者・理由・解消条件が読める。同じ「緑」でも、後から誰が何を負っているかが分かる。
- これは {{D:promotion-requires-effectuation-not-meaning}} の「未確立を成果物へ必ず持ち越す」と
  同じ考え方を、関門の内部状態へ適用したものである。未確立と確認済みを構造で区別する。
- 変異 M4 で裏を取った。繰延べ entry の行番号を壊すと、その 22 セルは実際に赤になる。
  **繰延べが本当にその 22 セルを抱えている**ことが確かめられている。

**却下した選択肢:**

- **誤った到達不能のまま land する** — 除外が記録に残らず、後続がこの穴を見つけられない。
- **繰延べを使わず赤のまま止める** — 関門そのものが land できず、main には関門が 1 つも無い
  状態が続く。緑の理由を明示できる以上、止める理由がない。
