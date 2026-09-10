# 段 1 brief 追補 — 拡張生死実験 (32 形)

`s1-brief.md` の実測 1 (7 形) を 32 形へ広げて測り直した。**この追補が実測 1 の正本である。**
測り方は実測 1 と同じ — pin `028f34d` の実 `include/backoff.hh` に実 `patches/silo-backoff-fixed.patch`
を適用した木を repo 外に作り、本物の `p3_s4_loop.quarantine(write=False)` を通した。
probe は repo 外 (job dir) にあり、repo へは入れない。

## 結果: 32 形中 25 形が受理、拒否は 7 形

**拒否された 7 形 (= 今日すでに効いている防壁)**

| 形 | subtype |
|---|---|
| `while (true) {}` | HOST_EFFECT (無条件 loop 規則) |
| `for (;;) {}` | HOST_EFFECT (同上) |
| 行末コメント `// izanagi` | HOLE_ESCAPE (コメント delimiter) |
| 行末 backslash による継続行 | HOLE_ESCAPE (物理行 splice) |
| `system("id")` | HOST_EFFECT (denylist) |
| `std::ofstream f("x")` | HOST_EFFECT (denylist) |
| `asm("nop")` | HOST_EFFECT (denylist) |

**受理された 25 形のうち、合成軸の意味を壊すもの (= 純増検出力の対象)**

| 群 | 形 | なぜ危険か |
|---|---|---|
| B 非決定 | `50 + (rdtscp() & 1)` | 実行のたびに値が変わり genome 帰属が成立しない |
| B 非決定 | `0.0 / 0.0` (NaN) | 比較が全部偽になり外側 spin が事実上無効 |
| B 非決定 | `1.0 / 0.0` (inf) | spin が終わらない (無条件 loop 規則は式を見ない) |
| B 非決定 | `-50` | 負の backoff。role は 1..1000 と宣言しているが未執行 |
| C 共有状態 | `Backoff_.load(...)` | 合成枝が stock 枝と同一になり treatment が消える |
| C 共有状態 | `Backoff_.store(0, ...)` | **他スレッドの stock 適応を書き換える。効果が run 全体へ漏れる** |
| D 隠れ適応 | `static double s; s = s * 0.9;` | 呼出しを跨いで状態を持ち、固定値のはずの variant が時間変化する |
| D 隠れ適応 | `thread_local` | 同上 (スレッドごと) |
| E 制御フロー | `goto` / `return` / `throw` | 外側の spin ループを飛ばす。`return` は backoff 自体の消去 |
| F 別名 | `double now_backoff = 50, other = 0;` | 多重宣言子 |
| F 別名 | `double &now_backoff = t;` | 参照束縛 |
| F 別名 | `int now_backoff = 50;` | 型変更 |
| F 別名 | `now_backoff_x = 50; now_backoff = 0;` | 宣言値と実効値の乖離 |
| G 式 | lambda 即時呼出し / comma 演算子 / 関数呼出し一般 | 任意の副作用の運び屋 |
| H 空 | `""` (空実装) | **hole が空行になる。宣言そのものが消える** |

## `s1-brief.md` からの訂正 2 点

1. **実測 5 の含意を訂正する。** role が宣言する `//` `/*` 行末 `\` の禁止は
   **既に機械執行されている** (`HOLE_ESCAPE`)。未執行なのは
   「単一の宣言文 `double now_backoff = <式>;` という形」の側だけである。
   したがって (P1) の争点は「コメント禁止の機械化」ではなく
   「**単一宣言文への限定が role 契約を狭めるか否か**」に絞られる。
2. **実測 1 の「敵対 6 形すべて素通り」は 32 形版で「25 形受理 / 7 形拒否」へ更新する。**
   拒否 7 形のうち 3 形は既知の denylist、2 形は無条件 loop 規則、2 形は
   コメント / 継続行である。**hole の「形」を見る規則は 1 つも無い**という結論は変わらない。

## 追加で確定した設計要件

- **空実装を受理してはならない。** 現行は受理する。文法は最低 1 個の宣言文を要求する必要がある。
- **無条件 loop 規則は字句規則であって式を見ない。** `1.0 / 0.0` は loop を書かずに
  無限 spin を作る。文法側で値域と非決定ソースを閉じる必要がある。
- **`Backoff_` への書込みは他スレッドへ漏れる。** これは hole 内で完結せず、
  「編集面は合成枝に限る」という骨格の主張を実質的に破る唯一の受理形である。
  負例として最優先で pin する。
