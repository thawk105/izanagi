# [T-2500] 段 4 裁定 — plan v2

## Erratum 1 (段 6 で発覚、2026-09-10)

**本裁定文の R1 と §5 が書いた格子の literal `3536` / `7071` は算術誤りである。**
同じ裁定文が書いた生成規則 `b_k = round(9999 / 2^(k/2))` の解は `3535` / `7070` である
(9999/2^1.5 = 3535.180、9999/2^0.5 = 7070.361)。親が下端から上向きに掛けて出したのが原因である。

- **事前登録の本文 (`docs/b10-backoff-static-tail-preregistration.md`) は `3535` / `7070` で正しい。**
  本文は規則から再生成した値を持っている。段 6 の 2 レンズが独立に再計算して確認した。
- **後続 wave は本裁定文の literal を数値の権威にしてはならない。** 権威は本文の生成規則と、
  そこから再生成した値である。
- 誤った literal を適用すると、格子・raw 値・3 つの測定順・6 区間・spec の SHA がすべて変わる。

初出の誤りは消さずに残す (追記でのみ訂正する)。

## Erratum 2 (段 6 の裁定で変更、2026-09-10)

段 6 のレビューが「`U_flat > 0.05` を先に見る 2 分割は、明白な低下継続まで `indeterminate` へ
吸収する」と指摘したため、**R5 の検出力事前条件は分類規則から外し、3 分割 (`saturated` /
`declining` / `indeterminate`) へ置き換えた。** `U_flat` は分類に使わない診断値として残す。
多重度は片側 18 から両側 36 の片側限界へ変えた。詳細は本文 §4.4 / §4.5 を正本とする。


段 3 の 2 レンズ (A = 恒真性・前向き性・規律 2、B = 数値の実在性・検出力) の所見を real/refuted に裁定し、
プラン v2 を確定する。親は所見の主要な根拠をすべて現物で独立に裏取りした。

## 0. 親が独立に裏取りした事実 (裁定の土台)

| 事実 | 現物 |
|---|---|
| abort 率の 4 桁量子化は CCBench の表示精度である | `external/ccbench/common/result.cc:41` の `setprecision(4)` |
| 整数 counter は同じ display 経路で必ず印字される | 同 `:33-49` と呼び出し `:634-637` / `:677-680` |
| parser は両 counter の key を知っている | `orchestrator/calibrator/benchparse.py:66-78` |
| **しかし campaign WAL に整数 counter は残らない** | 探索走 WAL の `leading_indicators` は率だけ。`abort_counts_` の hit 0 件 |
| point 側の `certified` は常に false の literal | `orchestrator/campaign/backoff_extended_sweep.py:1098` |
| 正しさの権威は WAL committed verify record の `certified` | 同 `:1080-1086` (畳んだ結果が `correctness_verified`) |
| **正値ゼロ分散は既に実在する** | `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/t2266-backoff-static-tail-read-heavy.json` の `fixed-999us` = `[0.0237,0.0237,0.0237,0.0237,0.0237]` |
| 測定順は `random.Random(seed).shuffle(昇順 label)` で決定的 | `backoff_extended_sweep.py:112-116, 485-520` |
| D1678 は B-10 の**機序** 5 項目を見送っている | `docs/decisions.md:51202-51218` |

レンズ B の検出力計算を親が独立に再計算し、一致を確認した (半オクターブ `U_flat`=3.04%、
終端短区間 `U_flat`=9.14%、探索 6 区間の `U`=30.4〜37.7%)。

## 1. real / 採用 (プラン v2 へ反映する)

### R1. 格子を「表現上限アンカーの半オクターブ」へ変更する (B5 由来、親の設計変更)

**所見:** プランの終端二分 (8000 / 8944 / 9999) は区間長が `h=0.1115` しかなく、5 rep では
真に平坦でも `U_flat`=9.14% > 5% になる。**飽和が最も起こりうる右端でだけ述語が恒偽**であり、
8944 を足した目的 (上限直前にも判定窓を持たせる) を達成しない。

**裁定:** 半オクターブを 1000 からではなく **9999 から下向きに刻む**。
`b_k = round(9999 / 2^(k/2))`、`k = 6,5,4,3,2,1,0`、`b_k > 1000` のものだけ採る。
→ tail = `1250, 1768, 2500, 3536, 5000, 7071, 9999` (7 点)。境界参照 `1000` を足して 1 workload 8 genome。
**全 tail 隣接区間の `h` が 0.3465〜0.3467 で均一**になり、終端の検出力低下が構造的に消える。
点数は t2266 の先例 (8 genome / 11 分) と同数で、絶対規律 4 を満たす。

**副次:** 探索の abscissa 再利用は 9999 だけになる。2000 / 4000 は正式格子に入らない。
`(P1-b)` は「再利用してよい」であって「しなければならない」ではないので、裁定の変更で足りる。

### R2. 飽和述語は tail 内の 6 区間だけを対象にする (R1 の帰結)

境界参照 1000 → 1250 は `h=0.2231` で検出力が異なる。混ぜると区間ごとに述語の強さが変わる。
1000 µs は**左境界の記述と、正式格子上端との同一 job 内での接続**のために測るが、飽和述語には入れない。
多重度は 3 workload × 6 区間 = **18**。

### R3. abort 率は整数 counter から全精度で再計算する (A1 / B6)

**所見:** 4 桁量子化を精密測定として扱うと、右端 (量子が平均の 0.7〜1.4%) で標本 sd が量子に支配され、
区間が不当に狭まり、**「測れていないこと」を「飽和」と判定する**向きに倒れる。規律 2 と 3 に触れる。

**裁定:** 本走 driver は rep ごとに `abort_counts_` と `commit_counts_` を**整数のまま**保存し、
解析の abort 率は `aborts / (aborts + commits)` で再計算する。**4 桁の `abort_rate` を解析入力にしない。**
保存が無い走行は失敗条件とし、量子化された率への fallback を禁じる。

**実在の確認 (DW-O13):** counter は CCBench が abort_rate と同じ display 経路で必ず印字する。
現行 WAL には残らないので、**この捕捉の追加が本走 driver の投入前条件**になる。

### R4. 区間解析を total にする (A2 / B6)

分散和が 0 の区間は Welch の自由度が `0/0` になる。プランの特例は「両 cell が全ゼロ abort」だけで、
**正値ゼロ分散を閉じていない**。この入力は既に t2266 の成果物に実在する。

**裁定:** `v_i + v_(i-1) == 0` の区間は `indeterminate` とし、飽和区間に数えない (fail-closed)。
`se=0` として通す扱いは偽の飽和を作るので禁じる。

### R5. 検出力の事前条件を述語自身に持たせる (B5 の一般化)

区間ごとに「真に平坦なら得られる `U`」= `U_flat` を観測分散から計算し、`U_flat > 0.05` の区間は
`indeterminate` とする。**飽和にも非飽和にも数えない。** これで「述語が届かない区間」を
「飽和しなかった」と読み替える経路が閉じる。

### R6. 判定入力の field 契約を固定する (A6 / B2)

`analysis_input_contract` を spec に置き、field 名・型・単位・権威を固定する。
**correctness の権威は WAL committed verify record の `certified`** であり、report の point 側
`certified` (常に false の literal) ではない。プランの `required_verdict="certified"` を
そのまま凍結すると全 27 cell が誤って失敗する。

### R7. CV は metric を分けて開示し、閾値の根拠を取り違えない (A3 / B2)

report の `cv` は throughput の変動係数である。`maximum_reported_throughput_cv` と
`maximum_recomputed_abort_cv` を別 key で開示し、**量子化された率から再計算した abort CV を
検出精度の根拠に使わない**と明記する。CV gate は abort・throughput の双方へ 0.02 で掛ける。

### R8. 探索の開示は 5 rep の生配列で行う (B3)

プランの `median_abort_rate` は write-heavy 2000 µs で中央値 (0.0292) でなく代表値 (0.0293) を
載せていた。**5 rep の生配列をそのまま開示**すれば、中央値/平均のラベル誤りが構造的に起きない。

### R9. 前向き性の限定を明記する (A4)

前向きなのは **formal cohort に対する測定・判定規則だけ**である。格子・5% 幅・非飽和の結末は
探索結果を見た後に選んだ。先例 `docs/b10-backoff-shape-preregistration.md:41-51` と同じ強さで限定する。

### R10. 効力を限定し、投入前条件を書く (A7)

本書の効力は「将来実装への規範」と「formal 結果より前に bytes が存在したことの証拠」に限る。
**「後続走を拘束している」とは書かない。** consumer が spec を parse し発火が確認されるまで
formal 投入不可、と前向きに書く。docs-only 自体はレンズ A も妥当と判定した。

### R11. observation ごとの provenance を要求する (A8)

formal 解析は formal campaign の admitted WAL から再構成し、入力 report の `qL` / `U` / verdict /
correctness bool を権威として受け取らない。各 observation に `source_run_kind`・campaign id・
campaign-lock digest・attempt id・rep index を必須化する。

### R12. raw hole を明記する (B1 nit、採用)

raw 値 `[1000, 2999]` は C++ 側で別の形 (商 1 / 2) へ落ちる発行禁止域である。物理値と raw 値を
分けて表に書き、禁止集合として併記する。

### R13. 上位選言を科学的主張と呼ばない (A5 nit、採用)

反証可能な主張は「全 workload で登録述語を満たす飽和位置が存在する」。域内非飽和はその反証結果
として報告する。「飽和または域内非飽和」という選言自体は結果分類であって仮説ではないと明記する。

### R14. 研究前進の表現を正す (レンズ A の brief 攻撃、採用)

D1678 は B-10 の**機序** 5 項目を見送っている。本 wave が前進させるのは機序ではなく
**静的右 tail の記述的特性化**である。brief の「過抑制域」表現を改める。
同じく「docs に静的 tail の事前登録は無い」は絶対表現では過大で、D1813 が既に 2 段構成を登録している。

## 2. refuted (実装しない)

| # | 所見 | 判定理由 |
|---|---|---|
| B1 | 登録格子に到達不能点・別分岐がある | レンズ B 自身が refuted。親も codec と C++ 分岐で確認済み。nit 部分 (R12) だけ採用 |
| B4 | 探索値が 5% を通ってしまう | 探索 6 区間の `U` は 30.4〜37.7% で全て非飽和。閾値は恒真でも恒偽でもない |
| B7 | 9 点格子が時間枠を超える | 8 点 11 分からの比例上界で 12.4 分/job。cap 195 分・PBS 300 分に対し十分 |
| B8 | 既存系列・test・docs lint と衝突する | 識別子・stem は分離済み。`EXTENDED_SWEEP_US[-1]==1000` の pin に触れない |
| A | 個々の停止・失敗・格子規則が恒真 | レンズ A 自身が refuted。偽になる観測を各条項について書けている |
| A | binary 相異要求が先例より弱い | レンズ A 自身が refuted。全 genome 完全性を要求しており generic helper の穴に依存しない |

## 3. scope 外 (裁定パッケージへ返す。本 wave では実装しない)

1. **正値 `BACKOFF_FIXED` の pointwise meaning witness gate の新設** — [T-2501] として既にユーザー裁定待ち。
   本書は既存系列と同じ限定を機械可読 field で明記するに留める (規律 2 を緩めない — 既存より弱くしない)。
2. **`check_docs.py` へ新規 prereg 本文の検査を足す案** (B9) — 本 wave では要求しない。
   **checker 緑を本文検査済みの証拠として報告しない**という報告上の制約だけ守る。

## 4. 変異事前登録 (DW-M01 / DW-S04)

本 wave は **実装面 (D95 決定 2) の差分が 0** である (変更は `docs/` の 2 file と `docs/spool/` のみ)。
DW-S04 により変異 matrix を免除する。**受入全走は免除しない。**

## 5. plan v2 の確定値

- 境界参照: `1000` µs (raw 3000)。飽和述語の対象外。
- 本格 tail (7 点): `1250 / 1768 / 2500 / 3536 / 5000 / 7071 / 9999` µs
  (raw `3250 / 3768 / 4500 / 5536 / 7000 / 9071 / 11999`)。
- 1 workload 8 genome × 3 workload = 24 cell。性能 5 rep・正しさ 5 rep。
- 動作点 literal: `records=1000000` / `threads=48` / `extime_s=3` / `reps=5`。
- 測定順 (`random.Random(seed).shuffle(昇順 8 label)` の解決結果):
  - write-heavy (seed 0xB10005): 2500, 3536, 1250, 1000, 1768, 9999, 5000, 7071
  - balanced (seed 0xB10050): 1250, 5000, 1000, 7071, 3536, 1768, 2500, 9999
  - read-heavy (seed 0xB10095): 3536, 1250, 7071, 2500, 1768, 5000, 9999, 1000
- 多重度 18、familywise α = 0.05、片側 α = 0.05/18。
- 飽和区間 = `qhat <= 0` かつ `U <= 0.05` かつ `U_flat <= 0.05` かつ分散和 > 0。
- 飽和位置 = 連続 2 飽和区間の中央格子点。域内非飽和も正当な結末。
