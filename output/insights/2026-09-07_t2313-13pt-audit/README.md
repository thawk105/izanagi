# [T-2313] 13 点較正での歩行 model 再走 — 独立検算

wave `dev-wave-t2313-walk-model-13pt` / 2026-09-07 / 起点 local main `d19d2182fbc324f67b47f600be70136d6503aa59`

**この文書の成果物は非認証である。** 元になっているのは trace-disabled の性能測定と、それを入力に
した歩行 model の再計算であって、直列性の検査を通していない。variant 採用の根拠には使えない (規律 2)。

---

## 0. 依頼と、着手前の実測で分かったこと

依頼は「13 点較正での歩行 model 再走を行う」だった。**着手前に一次資料を照合したところ、その再走は
既に完了し main へ着地していた。**

| 何が | いつ | どこに |
| --- | --- | --- |
| `--tail-json` 入力機構 | 2026-09-05 20:49 JST | commit `0ef73f882` |
| 8 点格子の tail 実測 | 2026-09-07 | job 979843 / 979844 / 979845 |
| **13 点較正での再走** | **2026-09-07 09:55 JST** | **job 980043、所要 76 分** |
| その記録 | 2026-09-07 10:05 JST | commit `51ced9c10`、`output/insights/2026-09-07_t2266-tail-measurement/README.md` §4.3 |

依頼文は entry 1298 の `[T-2266]` carry 本文「残るのは 13 点較正での歩行 model 再走 (下記 [T-2313])」
を写したものである。ところが**同じエントリの `[T-2313]` 本文は「13 点較正での再走も 2026-09-07 に
完了した」と書いており、1 エントリの中で食い違っていた。** 依頼文はそのうち古い側を写している。

**同じ条件の再測定を投入し直すことはしなかった。** 値は変わらず計算資源と時間だけを食うためで、
規律 4 に反する。代わりに本 wave は**着地済みの結果を独立に検算**し、ユーザーが固定した受入条件 2 点を
現物で確認し、台帳の食い違いを閉じた。段 2 / 3 の省略は D884 (先行実測で解決済みと判った task の
軽量経路) に従う。

---

## 1. 検算の対象と方法

- 旧 (7 点較正): `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2216-backoff-mechanism/results/t2216_model_final.json`
- 新 (13 点較正): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/results/t2216_model_tail.json`
- 実測 tail report 3 本 (campaign 出力、B-10 `t2266-tail`)

検算 script は `verify_13pt.py` と `reconcile.py` の 2 本で、先行 wave の `compute-r6.py` /
`compare-tail.py` と同じく **repo へは入れず** wave の job dir
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2313-walk-model-13pt/`) に置いた。stdout は
`verbatim/verify-13pt.txt` と `verbatim/reconcile.txt` に逐語で置いてある。

**本 wave の実装面 (コード・テスト・repo 内の実行可能 script) の差分はゼロである。** したがって
DW-S04 により変異 matrix は免除される。受入全走は免除されないので実走した (§5)。

---

## 2. 結果 — 140 項目すべて緑

### 2.1 R1 較正格子

3 workload (write-heavy / balanced / read-heavy) とも次を満たす。

- 新 model の格子はちょうど **13 点**で、昇順。
- 先頭 7 点の座標が既存格子 `[0, 2, 5, 10, 25, 50, 100]` µs と exact に一致。
- 末尾 6 点の座標が exact に `[150, 200, 300, 500, 750, 999]` µs。
- **既存 7 点の値は bit 単位で不変** — `throughput_tps`、`abort_rate`、
  `leader_period_us_at_static_points`、`raw_cells` の 4 つすべてを旧 model と直接比較した。

事前登録 R1 の「昇順に並べるだけで重み付け・再フィットをしない」が現物で成立している。

### 2.2 R2 集約規則

tail 6 点の `throughput_tps` と `abort_rate` は、対応する report の **全 rep (各 5 本) の算術平均**と
一致した (相対許容 1e-6 / 1e-9)。`.dat` の median や代表 abort 率ではない。

### 2.3 R4 — none / adaptive を較正に入れていない

report の 8 点格子は **static 6 点 + none 1 点 + adaptive 1 点**である。較正へ入った 6 値は
none / adaptive の平均値のいずれとも一致せず、static 由来だけであることを確認した。
**依頼文の「8 点格子」はこの 8 点であって、較正へ入るのはそのうち static 6 点である。**

### 2.4 受入条件 2 点 (ユーザーが固定)

3 report とも次のとおりで、両方とも成立している。

```
"requested_us": [150, 200, 300, 500, 750, 1000],
"realized_us":  [150, 200, 300, 500, 750,  999],
"unrealized":   [{"backoff_us": 1000,
                  "reason": "F718 — 現符号化では商 1・振幅 0 となり固定 0 へ復号される"}]
```

- **(受入 1) 1000 µs は F718 により測定不能。** `unrealized` にちょうど 1 件、理由つきで記録されている。
- **(受入 2) 999 µs は 1000 µs の代替であり、6 点目を新設していない。** 999 は `requested_us` に
  現れず、`realized_us` の 6 番目の枠を 1000 から引き継いでいるだけである。tail 点の総数は
  requested・realized とも 6 で変わらない。

なおこの読み方は 2 通りありうる。「999 を較正の 6 点目に使ってはならない」という読みは採れない —
凍結済みの R1 が 999 を tail 6 点の 1 つとして明示的に列挙しており、そう読むと事前登録を破ることに
なる。現物の `requested_us` / `unrealized` の形は「1000 と 999 を別々の点として数えてはならない」
という読みと整合する。

### 2.5 同一性

| 対象 | 結果 |
| --- | --- |
| tail report 3 本の sha256 | `provenance.tail_inputs` の記録と一致 (3/3) |
| 凍結 `measured.json` | sha256 `f46cebdd…` が旧走行と同一 (path だけ wave 差) |
| `backoff.hh.txt` | sha256 `3e9f5485…`、`source_pin` `511c9538…` とも旧走行と同一 |
| `static_calibration_jobids` | 旧走行と同一 (6 件) |
| numpy | 2.2.6、旧走行と同一 |
| **generator** | sha256 `00a034bc…` が **main 着地版の `tools/t2216_backoff_walk_model.py` と一致** |

最後の 1 行が重要である。**記録された再走は、現在 main にある `--tail-json` 版のコードが出したもの
である**ことが内容ハッシュで裏付けられる。path の違い (wave ごとの複製先) は束縛ではないので、
照合は内容ハッシュで行った。

### 2.6 R5 — 閾値・種・反復・評価経路の不変

`configuration`、`protocol`、全 214 条件の `seed_sequence`、各条件の rep 本数、
`consistency_checks` の key 集合、`not_certified` 文字列がすべて旧走行と同一だった。
形状ゲート 4 本の上限値 (2 / 3 / 1.5 / 0.2) も不変である。

### 2.7 R7 — 判定

| ゲート | 旧 (7 点) | 新 (13 点) |
| --- | --- | --- |
| A_stage1 | 不合格、kendall 距離 6 (上限 2) | 不合格、kendall 距離 6 |
| A_d1475 | 不合格、kendall 距離 10 (上限 3) | 不合格、kendall 距離 10 |
| B_flattening | 合格、比 1.1088646764700947 (上限 1.5) | 合格、**同じ bit** |
| C_valley | 不合格、相対誤差 1.303127163583053 | 不合格、1.2768901074976113 |

`shape.passed` は旧新とも False。**R7 の結論は 3 択のうち「変わらない」で、§4.3 の記述どおりである。**
ゲートが読む `predicted_mean_tps` の最大変化は A_stage1 の 100 µs で +1.77% にとどまり、
B_flattening が読む条件は bit 単位で 1 つも動いていない。

---

## 3. §4.3 の数字の母集合を特定した

§4.3 の「214 件の予測のうち変わったのは 61 件 (write-heavy 13 条件、balanced 7、read-heavy 2…)」は、
13 + 7 + 2 = 22 で 61 と合わない。**これは誤りではなく、1 文の中で数え方が 2 つ使われている**ためで、
検算で次のとおり切り分けた。

| 母集合 | 定義 | 数 |
| --- | --- | ---: |
| A | 変化した prediction (workload × scenario × condition) | **61** / 214 |
| B | 変化した相異なる (workload, condition) | **22** (write-heavy 13 / balanced 7 / read-heavy 2) |
| C | 母集合 A の rep (61 × 8) | **488** 本 |

- 「61 件」は母集合 A、「write-heavy 13 条件…」は母集合 B である。1 つの条件が複数の scenario に
  現れるため A > B になる。
- `r7.txt` の rep 統計 (中央値 −0.141%、最小 −14.361%、最大 +41.929%、`p>100µs` が下がったのは
  147 本) はすべて**母集合 C** で再現した。全 214 予測を母集合にすると中央値は 0.000% になる —
  変化しない 153 予測が中央値を 0 へ寄せるためで、こちらは §4.3 の意図する数ではない。

食い違いではないと確定したので、§4.3 の値は 1 つも書き換えず、母集合を明示する 1 文を追記した
(規律 7 の「追記でのみ訂正」)。

---

## 4. 事前登録が結果より前に凍結されていたことの裏取り

ユーザーは「補間規則は結果を見る前に固定する」を条件に挙げた。時系列で成立している。

| 時刻 (JST) | 出来事 |
| --- | --- |
| 2026-09-05 13:10 | R1〜R7 を確定 (t2266 wave の handoff `## 段 1 brief`) |
| 2026-09-05 20:31 | `brief-stage5.md` が R1〜R3 を逐語で保持 (mtime、job dir) |
| 2026-09-05 20:49 | 実装 commit `0ef73f882` — R1 / R2 をコードとテストに符号化 |
| 2026-09-07 | tail 実測 job 979843 / 979844 / 979845 が完走 |
| 2026-09-07 09:55 | 13 点較正の再走 job 980043 が出力 |

**規則を符号化した commit が、結果が存在するより約 35 時間前に着地している。** repo 内の逐語
(insight §1) は結果より後の commit `51ced9c10` に入っているが、規則そのものの凍結証拠は
それより強い形 (実行されるコード) で先行している。

---

## 5. 受入と検査

本節の各行は実走の後に書いた。実施していないものは「未実施」とそう書く。

| 検査 | 対象 tip | 結果 |
| --- | --- | --- |
| `python3 tools/check_docs.py` | 記録 commit 前の作業木 | rc=0、違反なし |
| `python3 tools/spool_fold.py --dry-run` | 同上 | rc=0 (`status` planned) |
| `python3 tools/check_ai_provenance.py --message-file` | 記録 commit の message | rc=0、1 件、違反なし |
| `python3 tools/check_ai_provenance.py` (全史) | `636d88a9` | rc=0、**8396 件、新規違反なし** (計算ノード job 980378、Elapse 66 秒) |
| 受入全走 1 回目 | `636d88a9` | **21020 passed / 68 skipped / 0 failed** (collected 21088)、`child-green`、rc=0 |
| 受入全走 2 回目 | 本節を書いた追記 commit | 結果は land の receipt に残る (理由は下の段落) |

受入 1 回目の `claimed_main` は `d19d2182fbc324f67b47f600be70136d6503aa59` で、tested main と一致する。
全史 provenance が挙げた既知違反 1 件は `9e6e4ee9` (2026-08-27 の親 probe) で、本 wave とは無関係、
後続 commit `f87a06cf7` で削除済みである。

**受入を 2 回走らせている理由。** 受入の結果は、それを載せる commit より後にしか存在しない。
記録 commit `636d88a9` を 1 回目で受入し、その結果を本節へ書いた追記 commit を 2 回目で受入して、
その tip を land する。2 回目の結果は land の receipt に残る (本文へ書くと同じ前後関係が
もう一段生まれるだけなので書かない)。

---

## 6. 確定していないこと

- **機序は未検証のままである。** なぜ実測 tail が指数的に消えず床へ近づくのかは本 wave の対象外で、
  `[T-2265]` (機序の直接観測) が担う。
- **歩行を大 backoff 域に滞在させる条件での再評価は行っていない。** より大きい step、より長い
  duration での再評価は凍結した事前登録の外にあり、新しい事前登録を要する。
- 本 wave は**新しい測定を 1 件も投入していない**。すべて既存成果物の再計算と照合である。

---

## 7. 再現条件

```
python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2313-walk-model-13pt/verify_13pt.py \
    <repo>/tools/t2216_backoff_walk_model.py
python3 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2313-walk-model-13pt/reconcile.py
```

前者は最後の引数に着地版 generator を渡すと sha256 の束縛まで検査し、rc=0 で 140 項目緑。
入力 3 種 (旧 model 出力・新 model 出力・tail report 3 本) は script 内に絶対 path で書いてある。
