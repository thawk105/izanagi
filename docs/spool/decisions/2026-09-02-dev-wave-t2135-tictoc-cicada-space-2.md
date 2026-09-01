---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2135-tictoc-cicada-space
seq: 2
---

## {{D:tictoc-no-wait-not-xor}}. tictoc の no-wait 制約は silo の XOR を転用せず、冗長な両 1 だけを除く

**決定:** tictoc の `NO_WAIT_LOCKING_IN_VALIDATION` と `NO_WAIT_OF_TICTOC` に置く制約は
「ちょうど一方が 1」(silo の XOR) ではなく「両方 1 を禁止する」とする。有効空間は 16 ではなく 24。
両 0 を探索空間に残す。

**この決定が主張しないこと:** 両 0 が競合下で実際に完走すること。公平性。starvation の不在。
これらは tictoc では**未実測**であり、判断は制御フローからの静的導出である。この限界を
`_tictoc_no_wait_not_both` の docstring と `TICTOC_SPACE.notes` に逐語で書く。

**理由:**

- silo で両 0 が livelock するのは、`lockWriteSet()` の内側 spin loop に lock word の再読込が
  無く、stale な `expected` を保持し続けるためである (実測 = insight 2026-06-22)。
  tictoc は骨格 (`#if` / `#elif` で `#else` 句なし) こそ同じだが、`#endif` の後に
  `expected` の再読込があり、それが内側 spin loop の**内側**にある。外側は write-set を回る
  `retry` label 付きの loop で、内側が spin loop である。したがって unlock を観測した次の反復で
  CAS 側へ進める。両 0 は空の分岐ではなく blocking spin になる。
- 両 1 は `#if` が選ばれ `#elif` が dead code になるため、挙動が (1,0) と同一の冗長組である。
  これは silo と同じ理由で除く。
- **骨格の同型だけを根拠に制約を転用すると、有効な点を過剰除外する。** 今回それが実際に起きかけた
  (親が段 1 brief で XOR を provisional 裁定として置き、段 2 と段 3 の独立レンズが覆した)。
  protocol が違えば、同じ `#if` / `#elif` の形でも周囲の制御フローが違いうる。

**却下した選択肢:**

- **silo の `_no_wait_xor` を tictoc へ再利用する** — 有効な両 0 を落とし、探索空間を 24 から 16 へ
  誤って縮める。過剰除外は「探索しても見つからない」を静かに作るので、発見が遅れる。
- **両 0 も未実測を理由に除外し、安全側へ倒す** — 除外の根拠が「測っていないから」になり、
  コードの事実に束縛されない。同じ論法で任意の点を落とせてしまう。限界は notes に書き、
  実測は certified campaign の前提として別に立てる。
- **制約を置かず 32 点すべてを残す** — 冗長組は同じ binary を 2 回測ることになり、規律 4 に反する。

## {{D:cicada-axis-vs-measurand}}. 多版 MVCC のノブは「最適化か、測る対象そのものの変更か」で軸への採否を決める

**決定:** cicada の探索軸は、そのノブが**性能を変えるだけか**、**測っている対象そのものを
変えるか**で分ける。後者は軸にしない。この基準で `SINGLE_EXEC` を除外し、
`WRITE_LATEST_ONLY` を採用する。

- `SINGLE_EXEC` は除外する。timestamp に基づく version chain の探索、pending 待ち、aborted
  version のスキップを迂回して常に inline version を読み、version の生成と timestamp 順挿入も、
  abort / commit 後の多版 maintenance も省く。update payload の扱いも通常経路と異なる。
  これは多版 MVCC を単版実行へ変えるものであり、軸に入れると**別のものを同じ workload として
  比較する**ことになる。
- `WRITE_LATEST_ONLY` は採用する。読み側の版の選択はこの flag を参照しない。有効時は blind write の
  latest が自分より新しければ保守側に abort し、無効時は version chain を辿って timestamp 順の
  位置へ install する。作用点は blind write 側と validation 側の両方にある。
  **正しさを緩めて速く終える方向ではなく、余分に abort して許容スケジュールを狭める方向**である。

**理由:**

- silo / mocc の単版 playbook は多版へそのまま通用しない。単版では「どの版を読むか」という
  自由度が無いため、可視性を変えるノブと速さを変えるノブの区別が問題にならない。多版では
  同じ形の boolean flag が、一方は最適化で、一方は測定対象の定義変更になる。
- 「最適化っぽいか」で選ぶと、可視性規則を変えるノブを取り込みうる。それは規律 2 が禁じる
  「正しさゲートを緩める方向の変異」を探索空間へ持ち込む経路になる。
  **読み側の可視性を変えるか**を基準にすれば、コードの事実で判定できる。
- この基準は導出可否ではなく**何が値を拘束するか**で分類する D993 の考え方と整合する。

**却下した選択肢:**

- **`SINGLE_EXEC` も軸に入れ、比較時に注記で断る** — 注記は読み飛ばされる。空間の定義に
  入れた時点で、下流は同じ workload の点として扱う。
- **`WRITE_LATEST_ONLY` も疑わしいので外す** — 読み側の可視性が不変であることはコードで確かめられる。
  疑わしさだけで外すと、コードの事実でなく心証で空間を決めることになる。
- **多版 protocol は軸導出の対象から外す** — 依頼の主目的そのものを放棄することになる。
