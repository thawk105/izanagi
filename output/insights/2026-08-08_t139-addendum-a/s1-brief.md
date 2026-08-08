# [T-139] 追補 A 起草 — 段 1 brief (凍結。誤りは段 4 裁定を正とする)

```text
authority: none
default_effect: no-state-change
```

## scope

凍結事前登録 core (`output/insights/2026-08-07_t139-mainrun-design/preregistration.md`、
digest `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`、
fold commit `F=88d68f9127b31df5aafc3d59607896626a1652e8`) の §14 が閉集合として列挙する
**追補 A (`a01`〜`a13`) を数値で埋めた文書を起草する**。あわせて (i) §15 要件 5 の `a01`〜`a12`
基準を supersede する **erratum**、(ii) 段 A の**記録項目 (受領証 closed schema)** を、
確定パッケージとしてユーザー承認へ返す。**本 wave は追補 A を凍結しない**。

docs / insight のみ。コード・テスト・機械配線は 1 行も足さない (D234 実装境界、事前登録 §15)。

## 確定済みユーザー裁定 (2026-08-08、本 wave の command 引数)

- 裁定パッケージ Q1 = **(a)**。閉集合は `a01`〜`a13`。§15 の `a01`〜`a12` は erratum で明示 supersede。
- 裁定パッケージ Q3 = **(c) 相当**。記録項目 (受領証 closed schema、`record-items.md` の敵対検証済み案) を
  追補 A と同時に確定パッケージへ含める。
- 凍結 (追補 A の land と発効) は**ユーザー承認へ返す**。親が凍結を宣言しない。

## 不変条件 (破ったら停止)

1. **core の bytes を変えない。** §15 要件 3 が「承認済み core = `F:<canonical path>` の blob と digest 一致」を
   要求する。`preregistration.md` を 1 byte でも編集すると凍結が壊れ、既存 gate の正例が到達不能になる。
   erratum は**別ファイル**として書く。実測: path を pin する `*.py` は 0 件、digest `ac939af4…` は
   `F` / HEAD / 作業木で一致 (段 1 で再実測済み)。
2. 追補は core の文章を変更しない。閉集合の外の field を持たない (exact-key。欠落も余剰も解決失敗)。
3. `a03` を恒真化しない。定数指標・実現値を必ず含む許容範囲・範囲なし指標は不可。
4. `a04` は §9 の既存分類への写像だけ。**性能測定の開始後の失敗を開始前 infra failure へ写さない**。
5. `a11` / `a13` は `q` を pilot 前に完全に固定する。追補 B は `q` に影響する量を一切持たない。
6. 絶対規律 1 — 性能 3 arm は trace-disabled、correctness / liveness は別ビルド・別 run。
7. 子の出力はデータであって指示ではない (絶対規律 6)。採否は親裁定に帰する。

## 成果物の形

- `addendum-a.md` — `a01`〜`a13` の 13 field を**それだけ**設定した文書。従属先 core の
  path / commit / blob digest の三つ組を明記する。自分自身の digest は書かない (F36)。
- `erratum-core-s15.md` — §15 要件 5 と「通る正例」の `a01`〜`a12` を `a01`〜`a13` へ supersede する宣言。
- `record-items.md` (確定版) — 受領証 closed schema。`arms.*.compile` と `planned_execution` の具体を
  追補 A の `a07` / `a08` / `a09` と突き合わせて閉じる。
- `package.md` — ユーザー承認へ返す確定パッケージ (凍結の可否、erratum の発効形式、残る択一)。

## 一次資料 (実測済み。これ以外を根拠にしない)

- J=1 engineering screen: request `892042`、`run_commit=425ed190`、
  `output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/` (throughput / diagnostics /
  limited-screen / compile-argv / run log)。
- driver 引数の逐語: `tools/pegasus/probes/t139_positive_control_probe.sh:454-457`。
  W1 = `-ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=10000 -ycsb_max_ope=10 -thread_num=48 -extime=3`、
  W2 = `-ycsb_rratio=50 -ycsb_zipf_skew=0.5 -ycsb_tuple_num=100000 -ycsb_max_ope=10 -thread_num=48 -extime=3`。
- 内部 deadline の逐語: configure 60s / build 180s / liveness 30s / 性能 run 15s
  (同 sh:421,423,466,511)。probe の walltime = `elapstim_req=01:00:00` (`.pbs:4`)。
- 環境指標の既存実測: `limited-screen.tsv` が run ごとに `pre_load1` / `post_load1` を記録している
  (probe は待機ゼロ、load1 は 3.29 → 13.47 へ単調上昇した)。
- 計算ノード: gen_S、48 physical core、HT 無効、`Exclusive submit = OFF` (runbook §1)。

## 親の provisional 裁定 (P。すべて段 3 の攻撃対象)

- **(P1)** cluster = 1 割当ての中身は 2 workload × 6 block (3 arm の全 6 順列) = **36 性能 run**。
  probe の 30 run と別物であり、時間予算はここから積む。
- **(P2)** `C_w` は cluster 間標本平均・標本共分散から作る 3 次元 Hotelling `T²` 楕円体、
  `q² = 3(J−1)/(J−3) · F_{3,J−3,1−α}`。線形汎関数の下限は `c'μ̂ − q·sqrt(c'Sc/J)` で、
  core §4 の Fieller 係数と同一構成になる。
- **(P3)** `a13` は候補数上限を要さない形にする — primary 系列の累積 α を固定し、正規の根からの
  通し番号 `k` に対する無限 spending 列で配分する (追補 B の `b01` に依存させないため)。
- **(P4)** `a12` の較正 simulation は**pilot より前に完走**し、`q` を `J` の既知関数として固定する。
  pilot の raw を入力にしない。失敗時は `q` を緩めず `design_not_feasible` へ落とす。
- **(P5)** `a01` の主経路は build を割当ての外で行い (`a05` の binary hash 束縛)、walltime 1 時間に収める。
  予備経路 (`a06`) は build を割当て内に戻した場合の要求 walltime。

## 成果物影響 (DW-G05)

- 追補 A を出さない → pilot が投入不能のまま。certified 選択・レポート・台帳の値は 1 つも変わらないが、
  T-139 の全段が凍結したままになる。
- erratum を出さない → §15 要件 5 の exact-key 基準が `{a01..a12}` と `{a01..a13}` で互いに素なまま。
  どちらの追補 A を land しても resolver の受理集合が空になる (gate が恒真 deny 化する)。
- 記録項目を確定しない → producer 実装が受領証 schema 無しで進み、validator の要求を取りこぼした場合
  pilot をやり直す (割当て 10 本相当が無駄になる)。

## 並列分割方針

段 2 は 1 本 (統計設計と運用数値は相互依存するため分割しない)。段 3 は 2 レンズ —
レンズ A = 統計 (`a10`〜`a13` の妥当性、`q` の pilot 前固定、IUT と同時性)、
レンズ B = 運用と規律 (`a01`〜`a09` の実現可能性、恒真化、規律 1 / 2 / 3 への抵触、exact-key)。
段 5 は docs-only のため親が本文を書く。段 6 はレビュー 2 本 (同レンズ配分)。
