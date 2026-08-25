# [T-1633] 段 0 blocker 範囲の D778 追随 — 変異台帳と検出力の実測

`authority: none` / `default_effect: no-state-change`

可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。本文書は測定記録
(measurement record) であり、裁定台帳ではない。

- 起点: 段 4 裁定の変異事前登録 9 件 (負例 8 + 正例 1)。裁定正本は D778 と本 wave の新規決定。
- 測った checkout: branch `dev-wave-t1633-stage0-blocker-scope`、
  変異束縛 commit `c9f88dfe`。
- 変異 spec: `izanagi-dev-wave-mutation-spec/v1`、
  sha256 `22eda437b1b92853c1b6fd6967d7c85cadb40390ae7e73aa47d9a9e9a45eca93`。
- probe spec: 同 schema、sha256
  `8e0e240a28484a60a9a5f91f43cfbd704cae42e63daaacec517015c3559ff99f`。
- 実行環境: Pegasus 計算ノード dispatch (`--runner-mode dispatch --detached`)。
  runner argv は `python3 tools/run_tests.py --force-dispatch` に対象 2 file と
  `-q -rf` を渡す形で固定した。

---

## 1. 結果

baseline PASSED。9 変異すべて KILLED で、期待 node 集合と実測 node 集合は完全一致した。
SURVIVED、MISMATCH、TIMEOUT、PARSE_ERROR はいずれも 0 件である。

| ID | 単一変異 | 期待 node 数 | 結果 |
|---|---|---|---|
| M1 | 除外述語から owner 条件 (`stage1-and-later`) を外す | 1 | KILLED |
| M2 | 除外集合を常に空にする | 8 | KILLED |
| M3 | 除外を全 blocking gate へ広げる | 6 | KILLED |
| M4 | owned 対象から `binding_state == "pending"` の要求を外す | 1 | KILLED |
| M5 | 繰越義務述語を常に成功させる | 2 | KILLED |
| M6 | 三者一致から module literal 照合を外す | 1 | KILLED |
| M7 | required-gates pin を manifest 由来の計算値にする | 1 | KILLED |
| M8 | 繰越未了集合を gate 依存へ戻す (段 6 fix の回帰) | 4 | KILLED |
| P1 | (正例) 繰越義務述語を常に拒否させる | 1 | KILLED |

合計 25 node。P1 だけが「承認外の過剰拒否」を測る正例で、他の 8 件は負例が受理へ反転すること、
または除外の射程が広がりすぎることを測る。

## 2. 期待 node の確定手順

`DW-M07` が定める手順に従った。期待 node 集合を事前に確定できなかったため、

1. 全 9 件を `expected_status = SURVIVED`、`expected_nodes = []` として probe spec に登録し、
   1 回走らせて観測 node を集めた (全件 MISMATCH = 全件が赤を出した)。
2. 観測集合をそのまま `expected_nodes`、`expected_status = KILLED` として本走 spec を再登録した。
3. 本走で 9/9 KILLED、MISMATCH 0 を得た。

probe の結果は消さず `mutation-probe-result.json` として job artifact に残している。

## 3. 単一理由性

各変異の注入点は contract module の 1 箇所で、置換前の逐語 anchor は module 内で一意であることを
注入前に機械確認した (9 件すべて出現数 1)。

`DW-M03` の意味で、9 件すべてが受理集合または fail-closed 挙動の変化を測っている。
診断文字列だけが変わる変異は登録していない。

- M1・M3・M4 は**除外の射程**を広げる方向の変異で、除外されてはならない gate / fixture が
  除外されることを測る。いずれも純 helper `_project_stage0_blockers()` へ parsed 構造を直接渡す
  unit test が殺しており、schema 検査や hash pin に先回りされていない
  (段 3 の敵対レビューが指摘した mask 型を回避した)。
- M2 は**除外が発火しない**方向の変異で、除外集合が空でも緑になる gate になっていないことを測る。
- M5・P1 は繰越義務述語が恒真でも恒偽でもないことを両方向から測る。
- M6 は三者一致が実際に三者を見ていることを測る。
- M7 は独立 pin が manifest 入力から再計算される退化を測る。
- M8 は段 6 fix (繰越未了集合を gate の blocking 状態から分離した修正) の回帰を測る。

## 4. 測定の限界

- 期待 node は probe の観測から作った。probe と本走は同じ commit・同じ runner argv で走らせたが、
  期待集合を独立に導出したものではない。
- 段 0 完了判定の production caller は 0 件である。本変異は contract module とその
  テストが持つ検出力を測っており、実 campaign 成果物の受理集合は測っていない。
