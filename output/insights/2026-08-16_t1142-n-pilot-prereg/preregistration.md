# 8b oracle の n 導出 pilot — 事前登録 [T-1142]

**この文書は実測値を見る前に凍結する。** 実走はこの文書と protocol を pin した commit の後に行う。
本 pilot は探索計測であり、certified 成果物・floor・oracle・`n` の決定のいずれの入力でもない
(出力 schema の `eligibility` 4 flag はすべて `false` に固定されている)。

本文書は目標・定義・条件付け・無効化規則の事前登録であり、実測値を含まない。
規模 (R) は生死実験の実測から決めるため、機械正本の protocol は R 確定後に同ディレクトリへ置く。

## 0. なぜこの pilot が要るか

[T-987] は 8b oracle spec の `n` について「**導出不能**」と確定させた。原因は 3 層ある。

1. **判定規則の誤認。** 8b の勝者決定は on/off の 2 者比較ではなく、holdout ごとに
   6 configuration を並べた median-of-medians + float 完全一致 argmax である
   (`orchestrator/campaign/s8b_oracle_judge.py` の verdict 形成)。
   a12 stress-check の `mean - q*sqrt(s/J) > 0` は別 study の規則であり、根拠にならない。
2. **目標の未定義。** 真の順位が未知なので素朴な誤選択率は定義できない。
   連続ノイズ下の完全一致 argmax はほぼ常に false unique-best を返すため、
   「拮抗のとき誤りか否か」の定義の取り方だけで結論が 0 から 1 まで反転する。
3. **標本の不足。** 対象条件 (Pegasus・rr20/rr80・extime=5) の between-run 実測が存在しない。
   登録済み較正は within-run・rr50 のものである
   (`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json`:
   `noise_floor.kind = within-run`, `cv = 0.01171`)。
   between-run の既存実測は linux-baremetal の rr5/rr50/rr95・extime=3 しかない。

本 pilot は (1) を estimator の再現で、(2) を indifference-zone の事前宣言で、
(3) を対象条件での実測で解く。

## 1. 事前固定する目標

### 1.1 誤選択の定義

**indifference-zone 選択**を採る。holdout ごとに、母集団 median-of-medians が最大の
configuration を「真の best」とし、**選ばれた configuration の真値が真の best より
相対 δ を超えて劣るとき**にだけ誤選択とする。

- δ 以内の差しかない configuration を選ぶのは誤りに数えない。
- **tie verdict は誤選択に数えない。** δ 以内で分離不能という事実の正しい報告だからである。
  tie 発生率は別欄で報告する。

この定義により [T-987] が突き当たった 2 つの逆理が同時に消える —
「全構成が同性能なら誤り 0 か 1 か」も「false unique-best を誤りと呼ぶか」も、
δ の宣言によって一意に決まる。

### 1.2 事前登録するパラメータ格子

| 項目 | 値 | 根拠 |
|---|---|---|
| δ (相対 indifference margin) | 0.005, 0.01, 0.02, 0.05 | 単一値を選べる根拠が現時点で無いため格子で報告する |
| α (許容誤選択率) | 0.05, 0.10 | 同上 |
| 制御単位 | holdout ごと **と** family-wise (rr20/rr80 のどちらかでも誤る) の**両方**を報告 | どちらを採るかは集約規則の再凍結 wave が決める |
| UCL | 片側 Wilson、信頼水準 0.95 | 点推定でなく上側信頼限界で n を選ぶ |
| n の選択規則 | **その candidate 以上の全 candidate が合格する最小の n** | 単調性を仮定しない。孤立した偽合格を採らない |
| resampling | round を単位とする block bootstrap | 同一 round の 6 configuration vector を一単位として再抽出する |

**出力は単一の n ではなく、表 `n(δ, α)` と各点の合否列・非単調 flag・UCL である。**

### 1.3 この形が [T-987] の問題を解く理由

[T-987] は「同じ仮定の変奏で必要な n が 7 から 14 まで振れる」と記録した。
振れの原因は**宣言されていない仮定**だった。本形では答えが振れるのは
**宣言済みの (δ, α) の違いによってだけ**になる。同じ (δ, α) なら同じ n が出る。
これが「n を統計的に導出可能にする」ということの内容である。

## 2. 測る分布

- **cell** = (holdout × configuration) の直積。holdout = rr20, rr80。
  configuration = backoff_fixed_best, ident_all, p2_2_flag_opt, sort_best,
  stock_common, system_gate。計 12 cell。
- **outer trial** = `measure_point(reps=5)` の median (`ScalePoint.throughput`)。
  実 judge の内側集約と同一であることを実行時に検査する。
- **1 round** = 12 cell を 1 巡。巡内順序は
  `s8b_oracle_manifest.build_schedule` (oracle 自身の完全ブロック replicate) が決める。
  floor 側の scheduler は使わない。
- 保存するもの:
  - cell ごとの outer trial の **raw binary64 全点** (要約だけにしない)
  - `candidate_set`: 6 configuration の同時分布、共分散行列・相関行列
  - `diagnostic_contrasts`: stock_common との差 (絶対・相対)。
    **これは診断であって検定比較対ではない** — 既存凍結が stock_common を
    「併記用の文脈セル」として比較対から除いているため
    (`orchestrator/campaign/s1_measurement_freeze.py`)。
  - 交絡診断: position、単調時刻、duration、load1、cache hit/miss、materialize elapsed

## 3. 母集団と条件付け

**結果は次に条件付ける。この条件を外して一般化しない。**

- `all-rows-eligible`: 実 judge は各 row の verify / eligibility 状態も見るが、pilot は
  throughput しか集めない。したがって誤選択率は「全 row が eligible」条件下の値である。
  **certified error rate と呼んではならない。**
- `three-allocations`: 母集団は「割当内の連続 round」である。R を 3 allocation へ均等分割し、
  allocation 差は**有無と向きだけ**を報告する。K=3 (自由度 2) は分散成分の推定にも
  UCL にも使わない。
- `exact-pin-and-binaries`: 使用した ccbench pin と全 binary SHA に条件付ける。
  **noise 分布が pin に対して不変という仮定は置かない** (未検証のため)。

**帰結: 得られる `n(δ, α)` は下限である。** cold-boot・温度ドリフト・
allocation 間変動を部分的にしか含まないため、実際に必要な n はこれ以上になりうる。
出力 schema はこれを `status: "lower-bound"` として持つ。

## 4. 規模 (R) の決め方

**R を見積りで決めない。** 生死実験 (`--build-only` と `--rounds 1`) で
12 cell の build と 1 round の実 wall time を実測し、そこから決める。

制約:

- 分散の相対標準誤差 ≤ 25%、すなわち自由度 ≥ 31、**R ≥ 32**。
  R=8 では `SE(s^2)/sigma^2 = sqrt(2/7) = 53.5%` となり、
  [T-987] の 7〜14 の幅をそのまま再生産する。
- R は 3 で割り切れること (3 allocation へ均等分割)。

## 5. ドリフト診断と無効化規則

**閾値を実測前に固定する。超えたら `n_analysis` を `null` にして理由を残す。**

| 診断量 | 閾値 | 意味 |
|---|---|---|
| cell ごとの (round 内 position の順位, outer median の順位) の標本相関 | `max_abs_position_correlation = 0.50` | 巡内の実行位置と性能の系統的な関係 |
| cell ごとの outer median を単調時刻へ回帰した傾き ÷ 母集団 median の絶対値 | `max_abs_relative_time_slope_per_second = 5e-06` | 相対性能の時間ドリフト。5,000 秒で 2.5% に相当する |

**閾値超過時も raw 分布は出力する。** 本 wave の第一の成果物は分布の実測であり、
n 表はその上に載る二次成果物である。診断が赤でも分布は失われない。

## 6. 規律との対応

- **規律 1 (観測者効果)**: build は `trace=False` のみ。build receipt の trace flag と
  binary SHA を検査し、測定直前に binary を再 hash して build receipt と照合する。
- **規律 4 (スケール)**: records / threads は holdout freeze の凍結値から読む。
  pilot 側に埋め込まない。Pegasus の登録済み較正が records=1,000,000 を飽和最小として
  登録済みであり、freeze の値と一致する。**新規較正は行わない。**
- **単独性**: job 開始時と各 `measure_point` の直前・直後に競合検知を実行する。

## 7. holdout 未知性 (規律 6 の送り手側)

`measure_point` は workload dict をそのまま CLI flag へ展開するため、
`ScalePoint.run_cmd` は rr20/rr80 の三軸 conjunction を必ず含む。既存 driver と同じ形で
保存すると repo が汚染され、floor / oracle の launch certificate clean scan
(`s8b_floor_campaign.clean_scan_digest`) が**恒久的に**赤になる。

対策:

- `run_cmd` を保存しない。workload object を出力に載せない。
- `write_guarded_result` を JSON / Markdown / spool の唯一の writer とし、
  書込み前に `s8b_holdout_freeze.holdout_conjunction_hits` を通す。
  汚染時は destination も親 directory も作らない。
- driver source に workload 値を書かない (freeze から読む)。
  test の汚染 payload は `HOLDOUTS` から実行時に組み立てる。
- 実測 artifact は repo 外へ出す。repo へ commit するのは三軸を含まない要約だけとする。

**I1 の主張範囲は「repo 内に三軸 literal を残さない」に限る。**
JSON Unicode escape 迂回は本 gate の対象外である (backlog として記録する)。

## 8. 凍結検証の状態

`orchestrator/campaign/freeze_verification_hold.py` は `HELD = True` であり、
21 件の同一性検査 (holdout の source bytes / frozen head 照合を含む) が
ユーザー裁定により保留中である。したがって `verify_document` は held marker を返す。

**pilot はこれを保存し `freeze_verification_status = "held"` とする。
「verified input」と表示しない。** held のまま探索実走することを、ここに明記して事前登録する。

## 9. F7 計測 closure との関係

承認済み F7 (2) は v2 の未知性を二層とし、「v1 以後の conjunction hit が
申告済み計測 closure と完全一致」することを要求する。
本 pilot は conjunction hit を 1 件も残さない設計なので、機械検査には抵触しない。

一方で、**pilot が rr20/rr80 を実測した事実自体は literal-hit 台帳に現れない。**
そこで pilot は `measurement_declaration` に全成果物の canonical path と sha256、および
「v1 凍結以後に rr20/rr80 を Pegasus 上の特定 pin で測った」旨を明記する。

`measurement_closure` は ratified freeze v2 の field であり、v2 は現時点で存在しない。
**本 wave では宣言のみとし、登録は v2 を作る wave (世代移行) へ引き渡す。**
新しい承認機構は作らない。

## 10. 本 wave がやらないこと

- **`n` の値を確定しない。** 集約規則の再凍結 (D143 (b) + [T-987] (b) + 世代移行) に従属する。
  `judge_oracle` の docstring 自身が「この集約規則はまだ再凍結されておらず、
  実測開始前に明示的な再凍結が必要」と記している。
- `holdout_freeze.json` の `floor` / `budget` を埋めない。
- 8b oracle spec の承認値を書き換えない。ratified freeze を作らない。
- 単一の (δ, α) を選ばない。
- allocation 変動の本格推定 (K≥5) をしない。
