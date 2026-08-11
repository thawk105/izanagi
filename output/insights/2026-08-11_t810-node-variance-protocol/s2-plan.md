結論から言うと、親 brief の (P1) はそのままでは成立しません。共通加法効果が相殺されるのは `N,D,G` であり、`H` には一般に残ります。また単一 arm の観測だけでは加法効果と乗法効果を識別できません。一方、(P3) の `N=12, R=10` は「何を検出可能にしたいか」を先に固定すれば、最小値として導出できます。

以下を新規文書 `docs/pegasus-node-variance-protocol.md` の完全な設計プランとします。これは文面の下書きではなく、各節で固定すべき内容・判定式・根拠を定めるものです。実走、pytest、build は行っていません。

## 0. 文書の権威・適用範囲・非効力

冒頭に次を置く。

- 文書の目的は、同一 binary・同一 workload を同一 occasion に複数ノードへ割り付け、ノード間分散を推定する新規 protocol の事前登録である。
- この wave では設計だけを確定し、投入、build、測定、登録、activation は行わない。根拠は親 brief の scope `brief.md:6-11`。
- 測定結果は calibration、floor/oracle、campaign trial、T-139 pilot の受理判定へ自動流入しない。親 brief の不変条件は `brief.md:24-29`。
- 文書が効力を持つ条件を「Stage 4 の全択一が裁定され、未記入値がなく、実装・受入検査が同じ commit で完了した後」とする。事前登録で数値・祖先・適用範囲を実走前に埋める先例は `docs/phase3-8c-preregistration.md:25-42,74-99`。
- negative claims として、クラスタ同等性、全 Pegasus ノードへの母集団推論、T-139 の受理、既存 calibration の置換、one-treatment-one-node 比較の正当化を明示的に否定する。先例は `docs/phase3-8c-preregistration.md:44-55`。

## 1. 目的、estimand、(P1) の検証可能性

### 1.1 主目的

主目的を次の仮説として固定する。

\[
y_{ir}=\mu+a_i+e_{ir},
\qquad
a_i\sim(0,\sigma_a^2),\quad e_{ir}\sim(0,\sigma_e^2)
\]

ここで `i=1,…,N` は同じ occasion に scheduler が割り当てた distinct node、`r=1,…,R` は同じ固定 workload の反復である。

主 estimand は、

\[
\kappa=\sigma_a/\sigma_e
\]

すなわち「ノード間標準偏差を同一ノード内反復標準偏差で割った値」とする。生の `σ_a` も報告するが、ノード差の運用上の大きさを異なる throughput 水準から切り離すため、判定は `κ` を主とする。

既存 2 件は同じ head/workload/R=10 だが、occasion と binary が交絡した約 1.774% の差であり、ノード効果の推定ではない。`facts.md:5-22,24-44`。runbook 自身も、node block/randomization と固定 estimator のない job-to-job 比較を無効としている。`docs/pegasus-runbook.md:968-982`。

### 1.2 T-139 への識別可能性

T-139 のクラスタ単位量は、

\[
N=X-D_g,\quad D=S-D_g,\quad G=S-X
\]

であり、`H` は以下のいずれかである。`preregistration-draft.md:29-49`。

\[
H_a=D-k_wS
\]
\[
H_b=D/S-k_w
\]

受理条件は、両 workload について `N>0 ∧ H>0 ∧ G>0` の同時信頼領域である。`preregistration-draft.md:51-71`。

文書では (P1) を次のように修正する。

| ノード効果 | `N,D,G` | `H_a=D-kS` | `H_b=D/S-k` |
|---|---:|---:|---:|
| 全 arm 共通の加法効果 `c` | 相殺 | `H_a-kc` となり残る | `D/(S+c)-k` となり残る |
| 全 arm 共通の正の乗数 `s` | `s` 倍、符号保存 | `sH_a`、符号保存 | 不変 |
| arm 固有または node×arm 効果 | 一般に残る | 残る | 残る |

したがって、「加法効果なら contrast で相殺、乗法効果なら残る」という (P1) は反証される。

- 加法効果が確実に相殺されるのは `N,D,G` のみ。
- 乗法効果は `H_b` では相殺される。
- 正の共通乗数なら点推定の符号は保存されても、クラスタ間共分散と同時信頼領域の幅は変わり得る。
- 単一 arm・単一 workload の T-810 主測定では、あるノード偏差を加法 intercept と乗法 factor のどちらでも表現できるため、両者は識別不能である。これは親 brief 自身の (P7) `brief.md:55-57` と一致する。

### 1.3 T-139 のどの量へ入るか

T-139 pilot は allocation-level の標本平均・標本共分散を自分自身で推定する。`preregistration-draft.md:53-59,98-113`。従って、T-810 の分散を pilot の標本共分散へ後から足すと二重計上になる可能性があり、禁止する。

T-810 の出力を入れてよい場所は、事前固定された感度分解だけとする。

\[
Z_{wj}=(N,H,G)^\mathsf T,\qquad
\Sigma_{Z,w}=\Sigma_{\text{other},w}
 + L_w\Omega_{\text{node}}L_w^\mathsf T
\]

- `Ω_node` は T-810 が与える reference-workload 上の上限または点推定。
- `L_w` は「共通加法」「共通乗法」など、Stage 4 で明示的に採択された構造仮定から導く loading。
- 単一 arm の主測定だけなら `L_w` を識別できないため、T-810 は pilot の生の `N,H,G`、標本共分散、臨界値、受理確率、main-run の `J` を変更しない。
- 出力は「仮定した node CV が同時信頼領域の幅をどれだけ動かし得るか」という感度表にだけ使う。
- T-139 の実 pilot は三 arm を同一 allocation 内で測る設計である。`facts.md:61-70`。従って T-810 の単一-arm 分散を「pilot の node 分散そのもの」と呼ばない。

## 2. 固定する測定面

主測定は既存 2 記録との比較可能性を優先し、次を pre-registration の literal field として固定する。

- trace-disabled Silo binary。
- workload: `records=1,000,000`, `threads=48`, `extime=3`, `clocks_per_us=2100`, `read_ratio=50`, `skew=0.9`, `rmw_ratio=0`。
- `R=10`。
- adaptive sweep、scale measurement、remeasure/best-round selection は行わない。
- throughput の各反復値を保存し、平均だけを保存しない。

既存 job の実引数は `tools/pegasus/certify_calibration.sh:720-732`、登録済み workload field は各 calibration JSON の `workload`、例えば `output/env/pegasus/calibration/registered/calibration-94a4….json:1685-1689` にある。`calibrate()` の固定 noise 測定は `orchestrator/calibrator/sweep.py:235-249`、adaptive saturation は同 `:73-116` であり、本 protocol では後者を呼ばない。

`between_run_noise_floor` は直列 session を前提に欠損を落とす実装なので、同時ノード比較の主推定器には使わない。`orchestrator/calibrator/stability.py:97-145`。remeasure の最良 CV 選択も事後選択になるため使わない。`orchestrator/calibrator/stability.py:58-90`。

## 3. N と R の導出

### 3.1 ANOVA 推定量

balanced one-way random-effects ANOVA として、

\[
\widehat{\sigma_e^2}=MS_E
\]
\[
\widehat{\sigma_a^2}=\max\{(MS_A-MS_E)/R,0\}
\]
\[
\widehat{\kappa^2}
=\max\{(F_{\rm obs}-1)/R,0\},
\quad F_{\rm obs}=MS_A/MS_E
\]

を固定する。

自由度を

\[
\nu_1=N-1,\qquad \nu_2=N(R-1)
\]

とすると、

\[
\frac{F_{\rm obs}}{1+R\kappa^2}
\sim F_{\nu_1,\nu_2}
\]

である。片側 95% 上限は、

\[
\kappa_U(N,R)=
\sqrt{
\max\left(
0,\frac{F_{\rm obs}/F_{0.05;\nu_1,\nu_2}-1}{R}
\right)
}
\]

とする。下限は `F_0.95` を用いる対称な反転で求める。

絶対量 `σ_a` については、plug-in 値だけを「95% 上限」と呼ばない。文書では次を固定する。

- `κ` の exact F inversion を主 CI とする。
- `σ_e²` の片側 97.5% chi-square 上限と `κ²` の片側 97.5% F 上限の積から、

\[
\sigma_{a,U}^{\rm Bonf}
=\sqrt{\kappa^2_{U,97.5}\,
       \frac{\nu_2MS_E}{\chi^2_{0.025;\nu_2}}}
\]

を同時被覆率 95%以上の保守的絶対上限として報告する。
- null 設計時の上限幅は、

\[
W_{a,0}(N,R)=
\sigma_{e,\rm plan}
\sqrt{
\frac{1/F_{0.025;\nu_1,\nu_2}-1}{R}
\frac{\nu_2}{\chi^2_{0.025;\nu_2}}
}
\]

であり、明示的に `N,R` の関数になる。

### 3.2 先に固定する識別目標

(P3) を導くための design targets を次の組として Stage 4 に出す。

1. materiality: `κ*=0.5`。
2. 片側誤判定率: `α=0.05`。
3. 真の `κ=0` のとき `κ_U<κ*` となる assurance: 80%以上。
4. ノード内標準偏差の近似相対標準誤差を 25%未満。
5. 最小の整数 `R,N` を採る。

`κ*=0.5` は、実測された大きい方の within-node CV `0.0124789655` に当てると node CV 約 `0.0062395`、すなわち 0.624% である。独立 2 ノードの中央 95% 差は概算 1.73% となり、交絡した既存差 1.774% とほぼ同じ運用スケールになる。元 field は `output/env/pegasus/calibration/registered/calibration-94a4….json:1568-1596`、既存差は `facts.md:14-22`。既存差を node 効果の証拠としては使わず、materiality の尺度にだけ使う。

### 3.3 `R=10`

標準偏差の相対標準誤差の近似を

\[
RSE(\hat{\sigma}_e)\simeq
\frac{1}{\sqrt{2(R-1)}}
\]

とすると、

- `R=9`: 25.0% で「25%未満」を満たさない。
- `R=10`: 約23.6% で満たす。

従ってこの基準では `R=10` が最小である。既存登録も10反復だが、単なる慣例ではなくこの精度基準で採る。既存 field は各登録 JSON の `noise.repetitions` と `noise.throughputs`、例えば同 JSON `:1568-1596`。

### 3.4 `N=12`

真の `κ=0` のときの assurance を、

\[
A(N,R)=
P\left[
F_{\nu_1,\nu_2}
<
(1+R\kappa_*^2)F_{0.05;\nu_1,\nu_2}
\right]
\]

とする。

`R=10, κ*=0.5` では、

| N | `F_0.05` | assurance |
|---:|---:|---:|
| 11 | 0.3862625 | 0.785893 |
| 12 | 0.4077022 | 0.828815 |

したがって 80% を初めて満たす最小値は `N=12`。`Fobs=1` の典型点では `κ_U≈0.3812`、worst observed within-node CV に掛けた raw-CV 上限は約0.476%である。

この導出は `κ*=0.5 / α=.05 / assurance=.80 / RSE<25%` が裁定されて初めて有効である。これらを裁定せず `N=12,R=10` だけを固定する案は棄却する。

### 3.5 ノード時間

登録 JSON の `walltime_s` は各 measurement point の代表反復時間であり、runner は `R` 回をループした後に代表反復を保存する。`orchestrator/calibrator/runner.py:396-418,431-477,499-500`。実測最大値は約 `4.540403 s/rep`。`output/env/pegasus/calibration/registered/calibration-94a4….json:1638-1682`。

したがって、

- critical benchmark:  
  `12 × 10 × 4.540403 = 544.85 node-s`、約9.08 node-min。
- shared build を上限1080秒で1回だけ行う場合:  
  約1624.85 node-s、約27.08 node-min。
- 最短 quiet preflight 60秒を12ノードへ加えた下限:  
  約2344.85 node-s、約39.08 node-min。
- timeout 予約量の保守上限は、各測定 job を  
  `1200 + 10×120 + 600 = 3000 s`、共有 build を1080秒とすれば  
  `37,080 node-s ≈ 10.3 node-hours`。最終値は実装前に reservation 式へ合わせる。

既存 full certification の予約は build 1080、noise repetitions 1200、全体6610秒である。`facts.md:72-78`。12本の full certification を投げる案は `12×6610=79,320 node-s` に加え、不要な sweep/build/登録を生むので採らない。

## 4. 割付け、occasion、同時性

### 4.1 何が無作為化されるか

現行 submit wrapper の `qsub` には host selector がなく、node は scheduler が割り当てる。`tools/pegasus/submit_certify.sh:166-201`。従って、

- node は研究者による無作為抽出でも無作為割付けでもない。
- estimand の母集団は「その occasion に scheduler が割り当て可能だった eligible node の交換可能モデル」に限定する。
- 「Pegasus 全ノードの design-based estimate」とは書かない。
- 無作為化するのは slot の投入順だけとし、事前登録した seed と permutation を receipt に残す。
- 主測定は treatment が1つなので、node-to-treatment randomization は存在しない。
- secondary arm を採択した場合だけ、node 内の arm 実行順を balanced order で割り付ける。

### 4.2 distinct node の保証

1 job は1ノード48 core を要求する。`tools/pegasus/policy.json:1-17`。ただし Pegasus allocation 自体は exclusive ではない。`docs/pegasus-runbook.md:33-50`。

protocol は scheduler が別 node を与えることを仮定せず、次の検出を必須にする。

1. N 本を独立 PBS request として投入する。独立 job の並行投入要件は `docs/pegasus-runbook.md:904-934`。
2. 各 job は benchmark 前に `PBS_JOBID`、`PBS_NODEFILE`、`hostname`、allocation の実体を ready receipt に書く。
3. controller は `hostname` の cardinality が正確に12であることを検査する。
4. 重複 host、未承認 host、host identity 不一致が1つでもあれば release token を発行せず、その group attempt を `premeasurement_invalid` とする。
5. ready receipt 全12件が揃った後、共有 release epoch を発行する。実 benchmark の最大 start spread を暫定5秒以下とし、各 node の monotonic start timestamp から検査する。
6. queue への投入時刻ではなく release 後の benchmark 区間を occasion の共通部分とする。PBS の開始時刻自体が揃うとは主張しない。
7. ready assembly timeout は暫定20分。超過時は benchmark を開始せず全体を失敗とする。

§7.5 は generic N-job barrier が既存実装にないと明記している。`docs/pegasus-runbook.md:999-1003`。従ってこれは protocol の必須実装面であり、既存 helper が保証すると書かない。

### 4.3 各ノードの isolation / quiet preflight

各 node で release 前と終了後に以下を閉じた schema の field として記録する。

- CPU model、physical core 数、HT、memory、NUMA、cache、CPU frequency policy。
- `qstat` から得た allocation host と `hostname` の一致。
- 48-thread 実行面。
- competing workload の process scan。
- load average が `≤1.0` の観測を30秒間隔で3回。最大待ちは1200秒。
- benchmark 前後の composite isolation probe。
- binary SHA-256 と runtime dependency manifest。
- trace symbol が存在しないこと。
- benchmark 前後の時刻、exit code、全10反復値。

現行 cooldown 条件は `orchestrator/calibrator/cli.py:234-258`、compute-node isolation と binary identity は `docs/pegasus-runbook.md:1103-1110`、既存 certification の allocation receipt は `tools/pegasus/certify_calibration.sh:208-339`。

### 4.4 B 系並走ガード

投入前に毎回、次の3条件を fail-closed で満たす。

1. 各 node で co-location がなく、isolation/quiet preflight が成立する。
2. T-139 pilot/main が RUN 中なら投入しない。保守的な初版では QUEUED 状態も競合扱いにする。
3. A 系ユーザー裁定の帯域を優先し、競合時は T-810 を取り下げる。

正本は `docs/phase3-8b-restart-runbook.md:11-23`。この wave では `qstat` も `qsub` も行わない。

## 5. 同一 binary の成立方法

F-2 の問題は実在する。既存2件は build path を含む hash input が job-local `/scr` を参照し、binary hash も異なる。`facts.md:24-44`。現行 certification は各 job で gflags/glog/CCBench を `/scr` に build する。`tools/pegasus/certify_calibration.sh:486-516`。

設計は次に固定する。

1. 測定12 job より前に、専用の1 compute-node builder job を1回だけ実行する。
2. repo 外の専用 `cache_root` を明示し、`build_v2` の完全な build preimage と completion manifest を得る。
3. build 完了後に `BuildResult.bin_sha256` と full completion manifest hash を protocol manifest へ固定する。
4. 完成 binary の bytes を repo 外の read-only shared binary store へ公開する。
5. 12 measurement job は build を行わず、同じ shared object を各 `/scr` へ byte copy する。
6. 各 job は copy 前の shared object、copy 後の local object、測定後の local objectを同じ SHA-256 と照合する。
7. `ldd` 相当の dependency name・resolved path・hash も固定し、binary bytes だけが同じで runtime が異なるケースを拒否する。
8. trace-disabled symbol gate と toolchain attestation を全 node で再検査する。
9. 1件でも不一致なら release 前は全体中止、release 後なら全体を incomplete とする。

この構造は成立する。根拠は以下。

- `BuildResult` は binary path、full SHA-256、cache root を保持する。`orchestrator/campaign/buildcache.py:165-182`。
- `assert_binary_sha256` は完全な小文字64桁 SHA-256 を要求し、prefix/fallback を認めない。`orchestrator/campaign/buildcache.py:80-117`。
- v2 cache entry は completion、preimage、toolchain、binary hash を検査する。`orchestrator/campaign/buildcache.py:366-433`。
- claim は directory の排他的作成であり、既存 claim に対する待機や共同 build の仕組みではない。`orchestrator/campaign/buildcache.py:538-572`。
- v2 publish は staging から fsync/rename する。`orchestrator/campaign/buildcache.py:701-799`。

従って12 job が同時に同じ `build_v2` を呼ぶ設計は不可。buildcache は bytes のノード配布までは行わないため、copy/hash receipt は新 protocol の責務とする。

既存 `calibrator.cli --certify` は使わない。certify mode は out-root を自由に変更できず、attempt を書いた後に registered へ自動 publish する。`orchestrator/calibrator/cli.py:625-666,793-856`。

## 6. 推定量、報告、判定

### 6.1 主推定量

事前固定する主出力は次の4つ。

1. `κ̂=σ̂_a/σ̂_e`。
2. `κ` の片側95%下限・上限。
3. `σ̂_a` と保守的 `σ_a,U^Bonf`。
4. ICC:

\[
\rho=\frac{\sigma_a^2}{\sigma_a^2+\sigma_e^2}
\]

主解析の scale は raw throughput とする。log throughput による同じ random-effects fit は副次解析として常に併記し、診断結果を見て scale を選ばない。

### 6.2 副次量

- node ごとの10反復、平均、標準偏差、CV、median、IQR。
- 全 node mean の min/max/range と相対 range。
- `MS_A`, `MS_E`, `Fobs`, degrees of freedom。
- start spread、pre/post load、isolation result。
- descriptive leave-one-node-out estimates。ただし主判定には使わない。
- secondary crossed arm が採択された場合は node random intercept と node×configuration random slope を別々に報告する。

### 6.3 結論対応表

| 条件 | 固定する結論 |
|---|---|
| 全 validity 条件成立かつ `κ_U95 < 0.5` | 「この binary/workload/occasion では、事前固定した material node variance を反証」 |
| 全 validity 条件成立かつ `κ_L95 > 0.5` | 「material node variance を支持」 |
| `κ_L95 ≤ 0.5 ≤ κ_U95` | 「識別力不足・未決」 |
| `σ̂_a=0` または有意差なしのみ | 「同じ」とは結論しない |
| job failure、rep 欠損、hash/isolation/quiet/start-spread 違反 | 全体 `invalid` または `incomplete_after_start`。主推定による結論なし |
| single-arm の結果 | 加法/乗法のどちらかとは結論しない |
| どの有効結果でも | one-treatment-one-node の比較禁止を解除しない |

`p` 値による零分散検定は副次量だけとし、materiality 判定には使わない。

### 6.4 欠損と retry

- 必要データは distinct 12 node × 10 reps の120値。
- complete-case subset、imputation、反復の追加、外れ値除去は禁止。
- release 前の失敗では数値を一切見ず、attempt 全体を `premeasurement_invalid` にできる。
- 再投入を許すなら最大 attempt 数を事前固定する。推奨は最大2 attempt。
- 有効 attempt は「固定順で最初に全 validity 条件を満たしたもの」。全 attempt を報告する。
- 1回でも performance interval が始まった後は、同じ attempt 内で node や rep を差し替えない。
- postflight 違反を含む開始後の欠損は全体 `incomplete_after_start` とし、部分推定を参考値としても主表へ載せない。

T-139 の「測定開始前だけ infrastructure failure を置換し、開始後は置換しない」という規律は `preregistration-draft.md:139-145`。

## 7. 成果物へ流入させない仕組み

### 7.1 推奨配置

repo 外の専用 durable root を推奨する。例は絶対 path を Stage 4 で固定し、実行時の変数展開に頼らない。

repo 外の利点:

- calibration/campaign/floor/oracle の discovery path から構造的に分離できる。
- `output/` の親ディレクトリを走査する consumer に誤認されにくい。
- git や frozen-artifact 対象へ偶発的に入らない。

欠点:

- git commit による保存性がない。
- retention、読取権限、別 backup が必要。
- report から binary/receipt への参照切れを別途検出する必要がある。

`output/` 配下の利点:

- repo-relative で発見しやすく、hash inventory をレビューしやすい。
-既存 report tooling と親和性がある。

欠点:

- frozen-artifact test は列挙された既存 path しか検査せず、任意の新規 output を検出しない。`orchestrator/tests/test_frozen_artifacts.py:38-85,125-153`、`facts.md:55-59`。
- calibration/campaign の既存 discovery surface に近く、誤流入防止を別途証明する必要がある。
- §7.5 は parallel job の共用親ディレクトリ・journal・registry を非並行 surface としている。`docs/pegasus-runbook.md:936-956`。

従って repo 外を推奨し、protocol 文書だけを repo に置く。

### 7.2 successful attempt の exact expected file set

閉じた集合を次に固定する。slot 名は `s01`〜`s12`。

```text
protocol.json
group-plan.json
group-submit.json
release.json
group-terminal.json
estimates.json
report.md
protected-before.json
protected-after.json
inventory.json
SHA256SUMS
binary/ycsb_silo.exe
binary/build.json

slots/sXX/submit.json
slots/sXX/job.json
slots/sXX/scheduler.stdout
slots/sXX/scheduler.stderr
```

successful attempt は13個の group/binary fileと48個の slot file、計61 file。symlink、socket、未列挙 file、nested directory は禁止する。

`job.json` は、allocation、binary/dependency hash、preflight、release/start、全10反復、postflight、terminal status を含む exact-key schema とする。既存 `calibration/v2` schema は calibration 固有の top-level key と publish semantics を持つため流用せず、別 schema ID を作る。既存 exact-key validation は `orchestrator/calibrator/schema_v2.py:563-580`。

失敗 attempt については、文書内に status 別 presence matrix を置く。

- `premeasurement_invalid`: `release.json`、`estimates.json` を禁止。
- `incomplete_after_start`: `release.json` は必須、`estimates.json` は禁止。
- 各 slot で `job.json` が存在しない場合、その欠損自体を `group-terminal.json` に記録する。
- 失敗時も、実在する stdout/stderr、submit receipt、node receipt を削除しない。
- exact-set 検査失敗は性能結果と独立に protocol failure とする。

### 7.3 exact forbidden set

次のどれにも追加・変更を許さない。

```text
output/env/*/calibration/attempts/**
output/env/*/calibration/job-staging/**
output/env/*/calibration/registered/**
output/campaigns/**/runs/wal.jsonl
output/s8b-freeze/**/journal.jsonl
output/**/trial-registry/**
orchestrator/campaign/env_contract.py
orchestrator/campaign/env_contract_activations/**
```

さらに以下を禁止する。

- calibration record または `calibration/v2` と名乗る JSON。
- registration、activation、restart handoff。
- floor/oracle/certification receipt。
- campaign attempt journal。
- frozen artifact、proof-chain、採択 report の変更。
- T-139 pilot の sample covariance、critical value、accept/reject field の変更。

`_build_registry` は static literal registry である。`orchestrator/campaign/env_contract.py:240-304`。activation は head と同じ commit の record と restart を要する。`tools/issue_env_contract_activation.py:26-32,143-152,194-212`。成果物流入の既存三段階は `facts.md:46-53`。

### 7.4 検出手順

投入前後に次を保存・比較する。

1. repository の status と tracked-file hash。
2. forbidden glob 全体の path inventory、size、SHA-256、mtime。
3. `env_contract.py` と activation directory の Merkle 相当 inventory。
4. calibration attempts/registered/job-staging の inventory。
5. 全 campaign/freeze journal の inventory。
6. frozen manifest 全 member の SHA-256。
7. repo 外 evidence root の expected-set、path type、size、SHA-256。
8. 実行 executable/argv の allowlist。`calibrator --certify`、campaign runner、floor/oracle、activation issuer が1つでも出たら失敗。

before/after が一致しなければ `nonflow_violation` とし、性能数値が完全でも結論を出さない。検査自身の出力は `protected-before.json` / `protected-after.json` に保存する。

## 8. DW-G01 生死確認

本走の前に `N=2,R=2` の liveness-only group を1回行う設計とする。これは推定にも N の再設計にも使わない。

確認対象は次に限定する。

- 共有 build を1回だけ作成・公開できる。
- 2 job が distinct node に落ち、重複を検出できる。
- ready barrier と共有 release が成立する。
- bytes copy と前後 SHA-256 が一致する。
- per-node pre/post isolation が記録される。
- repo 外 exact file set と no-flow audit が成立する。
- failure receipt が closed schema で終端する。

critical benchmark cost は実測最大を使って、

\[
2\times2\times4.540403 \approx 18.16\ {\rm node\text{-}s}
\]

である。共有 build が未作成なら build cap 1080 node-s を別途要する。

`N=3` は、standby/replacement path を本 protocol に採択した場合だけ使う。単純な barrier と distinct-host 検出には `N=2` で足り、3へ増やす根拠はない。これは「大きい仕組みの前に最安の生死確認を置く」という DW-G01 に対応する。`docs/dev-wave/core.md:45-48`。

liveness の値は以下へ絶対に使わない。

- `κ`、`σ_a` の推定。
- material threshold の調整。
- `N,R` の再選択。
- 本走との pooling。
- T-139 の sensitivity input。

## 9. preregistration に固定する field

実装前に空欄を残さず、少なくとも以下を literal value として commit する。

- protocol schema/version、protocol commit。
- CCBench commit、dependency commits、build preimage、binary SHA-256。
- exact workload argv と environment。
- `N=12`, `R=10`。
- `κ*=0.5`, `α=.05`, assurance `.80`、RSE threshold `.25`。
- raw-primary/log-secondary scale。
- F/chi-square CI 式と quantile tail。
- start spread、ready timeout、cooldown、max attempts。
- eligible-node attestation predicate。
- random seed と submission permutation。
- missing/retry rules。
- exact expected/forbidden file sets。
- repo 外 evidence root。
- B guard の判定 field。
- nonflow before hash。
- liveness group ID と「非統合」の宣言。
- secondary-arm の有無。
- occasion の意味と一般化限界。
- 全 Stage 4 裁定の ID。

## 10. Stage 4 に回す設計択一

| 論点 | 選択肢 | 推奨 |
|---|---|---|
| N/R の design target | A: `κ*=.5, α=.05, assurance=.80, RSE<.25`。B: 別の数値を決め再計算。C: N12/R10を根拠なく固定 | **A**。このときのみ N12/R10 が最小値として導ける |
| 1 occasion の限界 (P6) | A: occasion-specific snapshot と明記。B: scheduler 任せの第2 occasionを追加。C: 同じ host ID を再測定する crossed occasion | **A** を現 wave の主張範囲にする。Bだけでは安定 node 効果と node×occasion を分離できない。分離が必要なら別 protocol としてC |
| 加法/乗法識別 (P7) | A: single arm のまま機構を主張しない。B: node 内2 configurationをbalanced orderで追加。C: T-139の3 arm×2 workloadを再現 | **A** を主 protocol。pilot への機構的外挿が必須なら **Bを副次 protocolとして事前登録**。CはT-139の重複になるため採らない |
| T-139 への入力 | A: 感度表だけ。B: pilot covarianceへ加算。C: main J を自動変更 | **A**。B/Cは二重計上・事後変更の危険がある |
| occasion 同期閾値 | A: start spread≤5秒、ready timeout20分。B: 別閾値を性能データを見る前に固定 | **A** を暫定推奨。ただし実装 liveness で仕組みの生死だけを見て、性能値から閾値を調整しない |
| retry | A: release前のみ最大2 attempt、開始後置換なし。B: complete-case。C:不足repを継ぎ足す | **A** |
| 保存場所 | A: repo 外 dedicated root。B: `output/` 内 dedicated subtree | **A**。Bなら frozen test が任意新規 file を検出しない点を別検査で補う必要がある |
| liveness | A: N2/R2。B: N3/R2。C:なし | **A**。standby/replacement を採る場合だけB |
| §7.5 stale 記述 | A: 本 wave で「bnode011のみ」を2件・交絡ありへ訂正。B: 別 docs waveへ延期 | **A**。protocol の根拠箇所に隣接する既知の誤記なので同時訂正を推奨。ただし親 brief の指示どおり、訂正を含めた場合は段6で acceptance 全走を行う。`brief.md:31-35`; stale 箇所は `docs/pegasus-runbook.md:960-965`; 実物2件は `facts.md:5-22` |
| eligible-node 母集団 | A: 当該 occasion の scheduler-available nodes。B: 全 Pegasus node | **A**。host を選べない設計からBは導けない |
| secondary configuration | A: なし。B: 固定した2 configuration。C: 結果を見て追加 | pilot への加法/乗法議論を要求するなら **B**。Cは禁止 |

## 11. 段 2 の静的完了条件

親へ返す際の静的チェック項目は次のとおり。

- brief の (P1)〜(P7) を無条件に継承せず、P1/P3/P6/P7 の限界を明示している。
- N/R が数値目標と式から再現可能である。
- node allocation を「無作為」と誤称していない。
- binary identity が build path ではなく bytes/hash/dependency で固定されている。
- partial data、retry、postflight failure に事後裁量がない。
- T-139 のどの量へ入り、どの量へ入らないかが列挙されている。
- exact expected set と forbidden set が閉じている。
- calibration/campaign/activation の既存 API を呼ばない。
- DW-G01 が本推定から隔離されている。
- Stage 4 の裁定なしに実装へ進めない。

## 総括

- **結論:** (P1) は原文のままでは誤りである。共通加法効果も `H` に残り得て、共通乗法効果は `H_b` では消える。単一 arm は両機構を識別できない。
- **結論:** `κ*=0.5`、片側5%、null assurance 80%、within-node SD の RSE 25%未満を先に固定すれば、`R=10` と `N=12` はそれぞれ最小値として導ける。
- **結論:** 主結果は `κ` の exact ANOVA CI とし、`κ_U<0.5` のときだけ material node variance を当該 workload/occasion に限って反証する。「ノードは同じ」とは結論しない。
- **結論:** 同一 binary は専用 compute builder で1回 buildし、共有 bytesを各 nodeへ配布して完全 SHA-256 を前後照合する。既存 certify/calibration route は登録へ流入するため使わない。
- **結論:** 出力は repo 外の閉じた evidence root を推奨し、成功時61 fileの exact setと protected before/after auditを設ける。
- **未解決:** 1 occasion では stable node 効果と node×occasion を分離できない。scheduler 任せの2回目を追加するだけでも解消しない。
- **未解決:** T-139 への加法/乗法別の外挿には crossed configuration が必要。主 protocol 単独の出力は感度解析用の reference envelope に限られる。
- **親への要求:** Stage 4 で design target、single-arm/secondary crossed design、occasion 範囲、保存場所、retry、同期閾値、§7.5 訂正を明示裁定すること。
- **実施状況:** 本回答は一次資料の静的読解と数式設計のみ。測定、qsub、build、pytest、benchmark は実施しておらず、緑または実走確認済みとは主張しない。