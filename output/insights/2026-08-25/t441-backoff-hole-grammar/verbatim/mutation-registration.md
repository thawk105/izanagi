# 変異事前登録 (改訂版) — DW-M01 の単一理由性を実測してから登録する

段 4 で登録した t441.m01〜m14 は、実装子が「t441.m03 (空実装検査) は宣言必須に包含されるので
単独では受理集合を広げない」と申告したため、**登録し直した**。
`DW-M01` は「同じ入力を拒否する層が前後に無いこと、無効化時の赤理由が一つに絞れることを
**コードで確認**する。確認できなければ登録せず実効 gate へ再照準する」と要求している。
親は推測でなく**実測**した。

## 測り方

`backoff_hole_grammar.py` の guard はすべて `return _reject("<stage>")` の形なので、
`return` を外して `_reject("<stage>")` にすると値が捨てられ制御が続く = **その規則だけの除去**。
repo 外の scratch へ 13 通りの除去版を作り、40 入力 (implementation 29 + value 11) の
受理集合を除去前後で比較した。repo には 1 byte も書いていない。

## 結果 — 13 規則のうち独立検出力があるのは 8 件、fail-closed 寄与が 2 件、診断のみが 3 件

**baseline 受理 = 40 入力中 7 件。**

### A. 受理集合が広がる (accepted-set kill。8 件を登録する)

| 規則 | 除去で新たに受理される入力 |
|---|---|
| `raw-size` | 5000 空白で padding した正当な宣言 |
| `storage` | `static double s = 20; double now_backoff = s;` / `thread_local` 版 |
| `control-flow` | `goto` / `return` / `throw` / label の 4 形 |
| `reference` | `double &now_backoff = t;` |
| `declaration-count` | `double now_backoff = 20;` を 2 回宣言する形 |
| `rebinding` | `now_backoff = 0;` / `now_backoff += 1;` |
| `value-integer` | `20.5` / `"20"` (str) / `True` (bool) |
| `value-range` | `0` / `1001` / `-5` |

### B. 受理集合は不変だが fail-closed 挙動が壊れる (fail-closed kill。2 件を登録する)

`DW-M03` は「受理集合**か fail-closed 挙動**が期待方向へ変わったとき」を kill と定める。
この 2 件は除去すると**きれいな拒否が未捕捉例外へ倒れる**。
`run_one_iteration` の中で例外が出れば campaign が異常終了し、reject として台帳に残らない。
つまりこの 2 件は load-bearing である。

| 規則 | 除去後の挙動 |
|---|---|
| `input-type` | `None` / `123` → `TypeError`、`list` / `bytes` → `AttributeError`、`str` 派生型 → `AssertionError` |
| `tokenize` | 終端しない文字列リテラル・括弧 2000 重・900 項の加算 → いずれも `UnboundLocalError` |

### C. 拒否 rule ID が変わるだけ (登録しない。3 件)

`DW-M03` の「診断文字列だけの赤を kill にしない」に該当するため**登録から外す**。
実効 gate は `declaration-count` であり、この 3 件はその**診断上の細分化**である。
実装が誤っているわけではない (rule ID が具体的なほど critic への構造化診断は良くなる) が、
**記録に「13 層の独立した関門」と書いてはならない。**

| 規則 | 除去後 | 実効 gate |
|---|---|---|
| `empty` | `""` / `"   "` → `declaration-count` で拒否 | `declaration-count` |
| `declaration-type` | `int now_backoff = 20;` → `declaration-count` で拒否 | `declaration-count` |
| `single-declarator` | `double now_backoff = 20, other = 0;` → `declaration-count` で拒否 | `declaration-count` |

## D. 過剰拒否を捕まえる正例 (DW-M01 の「承認外の過剰拒否を検出する正例」)

受理集合を縮小する wave なので、**全部拒否する実装も緑にしない**ための正例を対で登録する。

| ID | 変異 | 期待 |
|---|---|---|
| t441.p01 | validator を無条件 `accepted=False` にする | KILLED (正準正例 `double now_backoff = 20;` と value=20 が落ちる) |
| t441.p02 | marker 条件を全 marker へ拡張する | KILLED (trigger / sort の非影響テストが落ちる) |
| t441.p03 | marker 条件を削除し backoff でも走らせない | KILLED (Tier 1 の負例テストが全部落ちる) |

## 手順 (DW-M07 / DW-M08)

1. 段 6 の fix を全部入れ、**最終 commit を作ってから** anchor (old 逐語) を再検証する。
2. まず**全件 SURVIVED 期待の probe spec** で走らせ、観測 node を集める
   (`DW-M07`: 期待 node が空の spec は起動前に中止されるため)。
3. 観測 node を `expected_nodes` の**完全集合**として最終 spec を作る (`DW-M08`)。
4. `tools/mutation_harness.py` を `--runner-mode dispatch` で使い、runner argv へ
   `--force-dispatch` を入れる。`--attempt-out` と `--wrapper-attempt` は同時指定。`--detached` 必須。
5. baseline 緑を先に取る。既存赤は `--deselect` で外し根拠を台帳へ書く。
6. `DW-M04` に従い置換対象の一意性を累積適用ごとに assert する。
   `raw-size` は 3 箇所、`empty` は 2 箇所、`value-integer` は 4 箇所あるので、
   **これらは全 site を同時に外して 1 変異とする** (1 site だけでは他 site が同じ入力を拾う)。
