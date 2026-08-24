---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-24
wave: dev-wave-t1619-shared-setup
seq: 2
---

## {{D:shared-prelude-needs-group-and-fixture}}. 受入の重複前置きは group 化と fixture 共有の 2 点で共有する

**決定:** 「同じ前置きを何度も払っている」型を共有化するときは、(1) 対象を 1 つの xdist group へ
入れて同一 worker に閉じ、(2) 前置きの計算結果を module fixture で 1 度だけ評価して共有する、
の 2 点を対で行う。新しい直列鎖の長さは既存の floor 鎖を超えてはならない。
既存の鎖へ対象を足して共有する方法は採らない。

**理由 (すべて実測):**

- `scope="module"` の fixture は xdist worker ごとに作り直される。直列走では前置きの setup が
  1 回 (12.49 秒) だったのに対し、並列走では 5 回 (各 15.44 秒) 計上された。
  **group 化しなければ fixture 共有は効かない。**
- 逆に group 化だけでは、前置きの計算そのものが各 test で繰り返される。s8c predicate 族では
  評価回数が現状 11 回、group だけなら 7 回、2 点セットで 3 回になる。
- 実効果は同一条件の対比較で setup + call の総和が 147.28 秒から 38.9 秒 (73.6% 減)。
  setup は 5 回から 1 回になった。
- 既存鎖へ足す案が悪い理由も実測で決まる。`real-repo` 鎖は既に 102.6 秒、
  `s8c-preregistration-candidate` 鎖は 103.0 秒で、どちらも受入 makespan の floor と同じ桁である。
  共有化後の族 (約 46 秒) を既存鎖へ足すと鎖は約 147.6 秒になり、推定下界を
  約 36 から 40 秒**悪化**させる。新規に独立した group を作れば鎖は約 46 秒で floor を下回る。
- 削減が wall に効くのは work 下界が鎖下界より大きい間だけである。既知の stale entry を
  除いた総 work 5316.9 秒に対し、現 work 下界は 110.8 秒、共有化後の見込みは 108.1 秒で、
  いずれも 103.0 秒の鎖より大きい。**これは下界の改善であって実 wall の短縮保証ではない。**
  効果の外挿は、変更前の setup 回数が distinct worker 数 k (1 以上 5 以下) に依存するため、
  k=5 かつ焦点走と同じ費用比を仮定した条件付き推定である。

**不変条件:**

- テスト削除・skip・xfail・assert 弱化・関数名変更・件数変更をしない。共有するのは入力だけで、
  各 assert は個別に残す。
- 2 つの独立な評価を突き合わせている検査では、片側だけを共有する。両側を同じ共有値にすると
  恒真化して検出力を失う。
- group 名の golden に加えて、group に属する canonical node の独立 literal と
  **item 件数**も固定する。canonical 名の集合比較だけでは parametrize による鎖の増加を
  検出できない。件数の期待値は golden の `len()` から導出せず手書きにする。

**却下した選択肢:**

- 既存の直列 node registry へ対象を足す — 鎖を伸ばして新しい律速を作る。
- 前置きを worker 横断のディスク cache で共有する — 並行書き込みの調停が要り、
  group 化より機構が増える。
- 所要台帳の値を本 wave で更新する — key は不変なので land を妨げない。
  台帳の再生成は別タスクの範疇である。

## {{D:mutation-visibility-probe-before-registering}}. 変異事前登録の前に可視面を probe で実測する

**決定:** 変異を事前登録する前に、その変異が被検査テストから**見えるか**を実測で確かめる。
可視の正例 (変異を入れると赤くなる) と不可視の負例 (変異を入れても緑のまま) を 1 本ずつ走らせ、
可視面の表を作ってから登録する。実測できない面へは登録しない。

**理由:**

- 変異 harness は変異を commit せず working tree へ書く。一方、評価対象を **git blob として
  読む**テストは resolved commit の blob を読むため、working tree の変更が届かない。
  この型の変異は「効かない」のではなく「見えない」ので、**偽の SURVIVED** を作る。
- s8c predicate 族で実測した。評価器コード (テストが import する面) を 1 箇所変えると
  期待どおり 1 件だけ赤くなった。評価対象 file (blob として読まれる面) を変えると
  5 件すべて緑のままだった。後者は当初の plan が「赤くなる」と登録していた変異そのものである。
- 同じ族でも、working tree から読み直される面は可視になる。evidence 契約 file は
  snapshot へ working-tree bytes が再注入されるため、snapshot 側だけが変わる非対称変異になり、
  2 つの評価の同値性を見る検査を単一理由で殺せる。

**却下した選択肢:**

- 静的な読みだけで帰属を判断する — 本 wave では plan と敵対 2 レンズの 3 者がこの欠陥を
  見落とした。読みは probe の代わりにならない。
- 変異を commit して可視にする — harness の固定 HEAD 束縛と復元契約を壊す。
