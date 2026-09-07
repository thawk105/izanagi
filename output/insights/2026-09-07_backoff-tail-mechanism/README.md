# 静的 backoff の tail 応答 — 待ち時間そのものが集約時間の 7〜9 割で、指数減衰ではない

**種別:** 機序解析 (記録済み測定の事後再解析)。**すべて非認証である。** 材料は trace-disabled の
性能測定であり、直列性の検査を通していない (`source_measurement = trace_disabled`、
`performance_certified = false`、`claim_scope = descriptive_backoff_shape_only`)。
ここにある値を根拠に variant を採用してはならない (絶対規律 2)。
**新しい測定は 1 件も行っていない** (絶対規律 7)。当てはめはすべて測定を見た後に立てた事後解析である。

- 日付: 2026-09-07
- wave: `worktree-dev-wave-backoff-tail-mechanism`
- 一次資料: `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` (測定の正本、§8)、
  `output/insights/2026-09-07_t2266-tail-measurement/README.md` ([T-2313] の model 再走)、
  `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/README.md` (投入と report 欠陥の修正)、
  `output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` (先行する機序解析)

## 0. 何が分かったか

静的 backoff `b` を 150 µs から 999 µs へ 6.7 倍に伸ばしても、throughput は 2.06〜2.23 倍しか下がらない。
[T-2216] の歩行 model が使っていた指数外挿は、同じ範囲で 19.30〜44.20 倍の過小評価をしていた。
**この落ち方の遅さは、スレッド自身が積む待ち時間そのもので説明できる。**

1 commit あたりの 48 worker 集約時間を `s(b) = 48 / T(b)`、1 commit あたりの abort 回数を
`a(b) = α/(1−α)` と置く (α は abort 率 = aborts/(aborts+commits))。ソース上、backoff は
abort 経路からのみ 1 abort につき 1 回、`b` µs の spin として入る。したがって

    s(b) = u + a(b) · (r + b)          … (1)

`u` は commit まで到達した試行の費用、`r` は abort 1 回の費用のうち backoff を除いた分である。
**(1) のうち `a(b)·b` の項は会計であって仮説ではない。仮説は `u` と `r` が `b` に依らないことである。**

tail 6 点 (150〜999 µs、3 workload、各 5 rep) でこれを検定した。

1. **残余 `y = s − a·b` は `a` の 1 本の直線に、測定の 95% 信頼区間とほぼ同じ精度で乗る。**
   18 点のうち 17 点が区間の内側に入る。外れる 1 点 (write-heavy 150 µs) も半幅の 1.863 倍にとどまる。
   残差の最大は 0.35 / 0.70 / 0.20%。
2. **そこから再構成した `T(b)` の誤差は 3 workload とも 0.064% 以内**
   (最大は balanced 500 µs の +0.0633%)。測定の信頼区間の相対幅 (0.14〜0.77%) より小さい。
3. **明示的な待ち `a·b` は `s` の 68.8〜93.4% を占める** (b ≥ 500 に限れば 81.4〜93.4%)。
4. **abort 率は同じ帯で冪則 `α = c·b^g` に従う** (g = −0.5154 / −0.4790 / −0.4398、
   R² = 0.999915 / 0.999427 / 0.999338)。よって `a·b` は `b` に比例せず約 `√b` でしか伸びない。
   **これが tail が指数的に消えない理由である。**

**言えないこと。** convoy・cache 汚染・leader 更新の飢餓が存在しないことは示していない
(残差が小さいという記述であって、相殺や共変動を排除していない)。α(b) が冪則に従う理由は本稿では
確定しない。adaptive backoff の谷の機序でもない。B-10 の他の項目 (待ち方 grid の判定、
真の静的 1000 µs、adaptive の 3 定数) は閉じない。

## 1. ソース上の事実 — backoff はどこに入るか

pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` のソースと `patches/silo-backoff-fixed.patch` の
合成枝から、逐語で次が言える。

- `Backoff::backoff()` を呼ぶのは `TxExecutor::abort()` だけである
  (ccbench の `cc/silo/transaction.cc`、`#if BACK_OFF` の中)。
  **待つのは abort したときだけ、1 回の abort につきちょうど 1 回。**
- 静的モード (`BACKOFF_FIXED` が 0 以上かつ商 0、すなわち 0〜999 µs) では待ち量は定数 `b` µs であり、
  適応 `Backoff_` を読まない。商が 1 以上になると乱択モードへ落ちる。**だから静的値の上限は 999 µs で、
  真の静的 1000 µs は現符号化では表現できない** (F718、一次資料 §2)。
- 待ち方は `rdtscp()` の始点から経過が `clocks_per_us × b` に達するまで回る **spin** である。
  スリープではないのでコアは占有される。
- abort 率は `aborts / (aborts + commits)` である (`orchestrator/calibrator/benchparse.py`)。
  したがって 1 commit あたりの abort 回数は厳密に `a = α/(1−α)` になる。

ここから (1) が立つ。**`s = 48/T` は 48 worker の集約時間であり、スレッドが同質であることは要らない。**
leader スレッド (`thid_ == 0`) 固有の費用は残余 `y` に吸収されており、分離していない。
その絶対上限は 1 スレッド分 = 集約時間の 1/48 = 2.083% である。
report の `representative_latency_ns` は `48e9 / median_tps` の導出値なので、並列度 48 の
独立な裏づけにはならない。

## 2. tail 6 点での検定

材料は [T-2320] wave が 2026-09-07 03:17 JST に投入した job 979843 (write-heavy) /
979844 (balanced) / 979845 (read-heavy) の report である。repo 内の写しは
`output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/`。
各静的点 5 rep、全点 `serializable` (anomaly 0)、`performance_certified: false`。
**本節の平均と信頼区間はすべて rep 生値から計算した** (t 分布、n = 5、`t_{0.975,4} = 2.776`)。

| workload | `u` (µs/commit) | `r` (µs/abort) | `y` の最大残差 | `T̂` の最大誤差 |
| --- | ---: | ---: | ---: | ---: |
| write-heavy | 3.9499 | 3.2990 | 0.35% | 0.058% |
| balanced | 4.2396 | 2.8353 | 0.70% | 0.063% |
| read-heavy | 3.7611 | 2.8360 | 0.20% | 0.047% |

`u` と `r` は workload をまたいでも 3.76〜4.24 µs / 2.84〜3.30 µs の範囲に収まる。
**同じ実行体・同じレコード数で read ratio だけが違う 3 条件が、近い費用定数を持つ。**

観測と分解 (5 rep 平均):

| b (µs) | write-heavy `s` / `a·b` の割合 | balanced | read-heavy |
| --- | ---: | ---: | ---: |
| 150 | 23.420 µs / 81.4% | 30.229 µs / 84.4% | 12.579 µs / 68.8% |
| 200 | 25.953 / 83.4% | 34.007 / 86.3% | 14.115 / 72.4% |
| 300 | 30.173 / 85.9% | 40.164 / 88.6% | 16.716 / 76.7% |
| 500 | 36.645 / 88.7% | 49.987 / 90.9% | 20.781 / 81.4% |
| 750 | 43.156 / 90.4% | 59.104 / 92.5% | 24.779 / 84.5% |
| 999 | 48.345 / 91.5% | 66.554 / 93.4% | 28.079 / 86.4% |

**この表が本稿の中心である。** b が伸びるほど、1 commit を生むのに費やす時間の中身は
「自分で積んだ待ち」に置き換わっていく。999 µs では write-heavy で 91.5%、balanced で 93.4% が待ちである。

**この一致は自明ではない。** `u` と `r` が `b` とともに動いてよいなら、`y` は `a` の直線から外れる。
実際、同じ会計を b = 0〜100 µs を含む 13 点へ広げると、`y` の残差は 6.05 / 4.49 / 1.74% まで悪化し、
低 b 側に系統的な符号の偏りが出る。**`r` が一定でよいのは tail に限られる。**
また、機序を持たない一般の 3〜4 パラメータ単調曲線を同じ 13 点の throughput へ当てても
最大誤差は 45 / 20 / 5.3% で、当てはまりの良さは自由度の産物ではない。

## 3. なぜ指数外挿が外れたか

[T-2216] の歩行 model は、較正末端 2 点 (50, 100 µs) の log 勾配で `b > 100` を外挿していた。
`k = (log T(100) − log T(50)) / 50`、`T_exp(b) = T(100)·exp(k(b−100))`。

| b (µs) | write-heavy 実測/外挿 | balanced | read-heavy |
| --- | ---: | ---: | ---: |
| 150 | 1.08 倍 | 1.11 倍 | 1.09 倍 |
| 300 | 1.58 | 1.84 | 1.67 |
| 500 | 3.05 | 4.24 | 3.47 |
| 750 | 7.50 | 13.40 | 9.53 |
| 999 | **19.30** | **44.20** | **27.41** |

**外れたのは関数形であって、データ不足ではない。** (1) と冪則から出る形は

    T(b) = 48 / (u + a(b)·(r + b))、  a(b) ≈ α(b) = c·b^g、  g ≈ −0.5

なので、大きい `b` では `a·b ∝ b^(1+g) ≈ √b` となり、`T ∝ b^(−1/2)` という**代数的な減衰**になる。
指数関数はどの区間でも代数関数より速く減衰するので、局所勾配から外挿すれば必ず過小評価になる。
乖離が b とともに単調に開くこと、workload によって開き方が違うこと (balanced が最大) は、
この形の違いから出る。

**同じことを費用側だけで確かめられる。** `(u, r)` を b ≤ 100 の既存 7 点だけで当てはめ、
tail で別途測った α を条件として与えると、tail 6 点の `T` は最大 2.061 / 1.183 / 0.835% で再構成できる。
**ただしこれは無条件の予測ではない。** tail では `a·b` が `s` の 7〜9 割を占めるので、
α を与えた時点で `T` はほぼ決まっている。この検定が示すのは、**残余の費用 `(u, r)` が
b ≤ 100 の帯から tail の帯へ持ち越せる**ことであって、tail の形を予測したことではない。
α まで冪則で外挿すると 999 µs で −11.90 / −24.77 / −28.50% ずれる。

## 4. α(b) を閉じる候補 — 現象論的で、正確な比例則としては破れている

α(b) 自体が冪則に従う理由は、本稿では確定しない。ただし候補を 1 つ記録する。

スレッドが「空回りでなく実際に走っている」時間の割合を `f = (s − a·b)/s` と置く。これは
実行中トランザクションの密度の代理である。仮定 **H**: `α = k · f`。

H を (1) と連立すると α(b) は b の陽な方程式になる — `x = α` として

    (r + b − u)·x² + {u − k(r − u)}·x − k·u = 0

の物理解であり、**代数的な恒真式ではない。** `(u, r, k)` の 3 定数だけで、b = 0〜999 µs の
13 点の `T` と α を同時に近似する。大きい b では `α² · b ≈ k·u` へ縮退し、
**`α ∝ b^(−1/2)` すなわち指数 −1/2 を出す。** 実測の −0.44〜−0.52 と整合する。
b ≈ 10 µs にある throughput の山の位置も同じ 3 定数から出る。

| workload | `u` | `r` | `k` | `T` 最大誤差 | α 最大誤差 |
| --- | ---: | ---: | ---: | ---: | ---: |
| write-heavy | 2.628 | 5.784 | 0.7628 | 4.01% | 6.51% |
| balanced | 5.238 | 2.635 | 0.7434 | 4.89% | 8.62% |
| read-heavy | 4.102 | 3.165 | 0.1592 | 2.26% | 3.18% |

**H は正確な比例則としては実測に破られている。** H が厳密なら `α/f` は定数のはずだが、実際は

- write-heavy: 全域 0.501〜0.860、tail だけでも 0.501〜0.606 (21% の変化)
- balanced: 全域 0.685〜0.936
- read-heavy: 全域 0.154〜0.176 (±7%。ここだけはほぼ一定)

tail の α の rep 間変動が 0.5% 程度であることに比べると、write-heavy の 21% は大きい。
**H は低競合ほどよく成り立つ近似であり、確定した機序ではない。**
本稿は H を候補として記録するにとどめ、図には描かない。
**証拠として数えられるのは「少数の共有パラメータで `T` と α を同時に近似し、−1/2 の漸近形を出す」
という圧縮性までである。** 当てはまりの良さ単独では、滑らかな経験曲線と区別できない。
また 13 点は同じ rep から作った対の集約であり、独立な 26 観測ではない。

## 5. 先行知見との関係

`2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md` は、静的な `T(b)` と α(b) から
adaptive の谷を再現する「素直な滞在説」を反証した。[T-2313] が実測 tail で歩行 model を再走しても、
形状ゲート 4 本の合否は変わらなかった。

**本稿はこれと矛盾しない。** 本稿の model は固定 `b` の応答を閉じるだけで、
adaptive の滞在分布・遷移損失・leader 固有 abort 率を閉じない。
[T-2313] の判定が動かなかったのは、試した step 幅では歩行が大 backoff 域にほとんど滞在しないためであり、
静的側の tail が正しくなっても adaptive の谷は再現されない。
**静的 tail の機序を adaptive 非単調性の機序として読んではならない** (D1637 が両者を分けている)。

## 6. 確定していないこと

- **機序は確定していない。** 滞在分布・遷移損失・スレッド同調・履歴依存・leader 固有 abort・
  窓内 commit 分布はいずれも未観測である。直接観測には診断ビルドが要る。
- **convoy・cache 汚染・leader 更新の飢餓の不存在は示していない。** 残差が小さいことは
  「集約量が追加の正の費用を要求しない」ことであって、相殺や共変動を排除しない。
- **α(b) が冪則に従う理由は分からない。** §4 の候補は近似であり、破れも記録した。
- **1000 µs 以遠は分からない。** 999 µs は F718 の符号化制約による代替であり、6 点目ではない。
  tail の上端が真に 999 µs なのか、それ以遠に別の挙動があるのかは言えない。
- **単一環境である** (Pegasus 48 物理コア、gen_S)。3 workload、非認証。
- 13 点を使う節 (§2 後半、§3、§4) の材料は、**別 job・別 rep 構造の 2 系列を継ぎ合わせたもの**である
  (b ≤ 100 は 2026-08-26 系列で throughput 6 値・abort 2 値、tail は 2026-09-07 系列で各 5 値)。
  継ぎ目 (b = 100 → 150) に残差の跳びは観測されなかったが、均質な標本ではない。
  この継ぎ合わせは [T-2313] の事前登録 R1 が定めたもので、本稿が新しく決めたものではない。

## 7. 図

`fig_tail_mechanism.png` / `.pdf`、provenance は `fig_tail_mechanism.provenance.json`
(schema `izanagi-t2266-tail-mechanism-figure-provenance/v1`)。

3 行 × 3 列。列は workload。全 panel 単一 y 軸で、二軸も基準線も無い。

- **上段 `T(b)`:** 実測 6 点 (95% t-CI つき)、tail 6 点で当てた費用 model 曲線、
  旧 model の指数外挿 (破線、`refuted exponential`)。**2 本の曲線が右へ行くほど開く**のが本稿の主眼。
- **中段 `s(b)` の分解:** `u` / `a·r` / `a·b` の積み上げと、実測 `s` の点 (95% t-CI)。
  **待ちの帯が全体を覆っていく**のが見える。積み上げは fit した会計成分であって直接観測した費用ではない。
- **下段 `α(b)`:** 実測 6 点 (95% t-CI) と冪則 fit。

生成器は `tools/plotting/plot_t2266_tail_mechanism.py`。
**実行時に読むのは repo 内の report 3 本だけ**で、平均・CI・`s`・`a`・`y`・OLS・冪則を
rep 生値からその場で計算する (作図規約 §1)。旧指数外挿の 2 定数 `T(50)` / `T(100)` は
module 定数として pin してあり、出所は `t2216_model_tail.json`
(sha256 `12599199e0694aa7bb7a590c3c34cb53c99a309d22b13e004e9c118e1909a7c9`、
schema `izanagi-t2216-backoff-walk/v2`)。**この 3.8 MB の file は実行時に開かない。**
その帯の rep 生値は repo に無く、規律 7 により測り直さないので、
**旧 7 点は図の測定系列に含めていない** (作図規約 §1・§2 を満たせないため)。

再現:

```
python3 tools/plotting/plot_t2266_tail_mechanism.py \
    output/insights/2026-09-07_backoff-tail-mechanism/fig_tail_mechanism
```

## 8. 再現条件

| 項目 | 値 |
| --- | --- |
| 図の入力 (repo 内) | `output/insights/2026-09-07_t2320-backoff-sweep-gate-layer2/t2266-tail/` の report 3 本 |
| write-heavy report sha256 | `d462e146b8b5d1fa804556225facd27f0d49975c81622c9922766f92170caada` (campaign `…9cce192b`) |
| balanced report sha256 | `5ad6f095cfca3477d5668f582deec9e240ad1c69b0b760f46a758e1e8e3d9ecf` (campaign `…0ffee20c`) |
| read-heavy report sha256 | `66bc31956766b030e54add0788b50d9409647b7454a7d79557abc7affef40da0` (campaign `…7e90afbe`) |
| 生成器 sha256 | `034a372169a520878f3842a24347c28c34090b8e3ff51d63b5556a2bf6139aaa` |
| §2 以外の 13 点の出所 | `t2216_model_tail.json` の `calibrations` (sha256 `12599199…`、[T-2313] の事前登録 R1) |
| 測定 job | 979843 / 979844 / 979845 (2026-09-07 03:17 JST 投入、Elapse 629〜632 秒) |
| ccbench pin | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 静的側 patch | `patches/silo-backoff-fixed.patch` |
| 実行体 | `ycsb_silo.exe` (protocol = silo) |
| スレッド数 | 48 (物理コア数、HT 無効) |
| レコード数 | 1,000,000 / zipf 0.9 / rmw 0 / max_ope 10 |
| workload | write-heavy = rratio 5、balanced = 50、read-heavy = 95 |
| 1 点あたり | extime 3 秒 × 5 rep |
| ビルド | trace-disabled (絶対規律 1)、perf 計測なし |
| 環境 | Pegasus 計算ノード、gen_S |

解析の逐語 (会計分解・out-of-sample 検定・閉包候補・帰無曲線) は wave の job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-backoff-tail-mechanism/` の `numbers.txt` と
`analysis-*.txt` にある。**解析 script は repo へ入れていない** (図の生成器だけが repo にある)。

## 9. 変異 matrix

`tools/mutation_harness.py` を直接使用 (`--runner-mode dispatch --detached`)。
probe (全件 SURVIVED 登録で観測 node 収集) → 本走 (期待 node 完全一致) の 2 段。

- baseline PASSED、**10/10 KILLED**、SURVIVED 0、MISMATCH 0、TIMEOUT 0、PARSE_ERROR 0
- `repo_head` = `1be077d2f441c078ae970c5ae219c57b32f6ffad`
- 本走 spec sha256 = `d50608587b18170ce826a617c64493d6bd87fa4a4269e377e5f8acf3c2b1a50a`
  (probe spec `76065b2a2a23d6c717c2c41dea8e704713803ab66c6b7a29de3573d369bcaf22`)
- runner sha256 = `b35e5fbf243fa1f88ec025d002f4f173a1b004411b413ebf5bec5e1ad4a3ad03`、
  tool sha256 = `830e61412cdf348e4de89e43317d00d578b4f5bd20f98a2cf31d50ff61012531`
- runner argv: `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_plot_t2266_tail_mechanism.py -q -rf -p no:cacheprovider`

| ID | 変異 | 事前登録の検出 test | 観測 (赤 node 数) |
|---|---|---|---|
| M01 | `THREADS` を 47 にする | `test_service_time_uses_48_worker_threads` | 2 (冗長 gate 1) |
| M02 | `a = α/(1−α)` を `α` にする | `test_aborts_per_commit_from_abort_rate` | 2 (冗長 gate 1) |
| M03 | `y` から `a·b` を引かない | `test_residual_fit_recovers_known_u_and_r` | 1 |
| M04 | rep 平均を中央値にする | `test_point_means_are_arithmetic_over_five_reps` | 1 |
| M05 | CI を正規近似 1.96 にする | `test_confidence_interval_uses_t_distribution_for_n5` | 1 |
| M06 | 指数外挿を 150/200 の勾配で引く | `test_refuted_exponential_uses_50_and_100_us_pins` | 5 (冗長 gate 4) |
| M07 | `a·r` に `a·b` を含めて二重計上 | `test_stacked_components_sum_to_model_service_time` | 1 |
| M08 | 静的 exact 検査を外し非静的点を混ぜる | `test_rejects_non_static_points_in_the_series` | 11 (冗長 gate 10) |
| M09 | provenance から入力 sha256 を落とす | `test_provenance_records_input_report_digests` | 1 |
| M10 | twinx を足す | `test_each_panel_has_a_single_y_axis_and_no_baseline` | 3 (冗長 gate 2) |

`DW-M03` に従い、M01 / M02 / M06 / M08 / M10 の追加 node は冗長 gate として記録する
(赤理由はそれぞれ 1 つ)。

## 10. 段 6 の敵対レビューが見つけたもの

レビュー 2 本 (数値と検査の実効性 / 規約・scope・波及) がどちらも NO-GO を返し、6 件を出した。
**全件を real と裁定して直した。**

- **caption が図に描画されていなかった。** 文字列は定義されていたが、PNG / PDF に artist として
  存在せず、非認証の 3 値も 6 つの但し書きも成果物に入っていなかった。
  さらに、それを検査する test が matplotlib の private 属性を見ていたため、
  **描画されていなくても通る恒真な検査**になっていた。
  実 artist として足し、test は `figure.findobj(Text)` を走査する形へ直した。
  **変異 matrix の外にあった偽の正例である。**
- 段 4 裁定が scope 外と決めた workload 順序拒否が 2 箇所にあった (削除)。
- 図中の略語 `M tps` と `RMW` が caption で展開されておらず作図規約 §5 違反 (展開)。
- in-sample の当てはめ値が `predicted_log_alpha` という名前だった (`fitted_log_alpha` へ改名)。
- 集約時間と残余の CI の中心が点推定値とずれていた (rep 平均を中心とする上下限を明示、非対称誤差棒)。
- 親の段 4 裁定にあった「誤差 0.06% 以内」が厳密には不成立 (balanced 500 µs が 0.0633%)。
  **0.064% 以内**へ訂正した。

段 3 の敵対相談 2 本も、親 brief の数値を 5 件訂正している (指数外挿との最大乖離 44.20 倍、
`a·b` の占有率 68.8〜93.4%、out-of-sample は測定 α を条件に与えた再構成であって予測ではない、
`representative_latency_ns` は導出値、閉包候補 H の破れ)。
