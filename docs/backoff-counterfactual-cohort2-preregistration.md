# adaptive backoff の反実仮想対照 — cohort 2 の事前登録

`patches/cicada-adaptive-counterfactual.patch` が入れた 3 値の step policy を使い、「制御器が選んだ
一歩の向きは、直後の窓の commit 速度を変えるか」を測る試験の、**2 番目の cohort** の事前登録である。
機構の一次資料は `output/insights/2026-09-07_t2265-backoff-counterfactual/README.md`。測定対象の
protocol は Silo (`ycsb_silo.exe`) で、「Cicada」は adaptive backoff 算法の由来を指す。

cohort 1 の事前登録は `docs/backoff-counterfactual-preregistration.md` である。**本書はそれを
置き換えない。** 同書 §9 が「v2 用の解析器はこの 12 件の cohort 専用であり、将来 cohort 用の
互換層は作らない。将来の cohort を解析するときは、その cohort に対応する束縛を持つ解析を別に
用意する」と定めている。本書はその「別に用意する束縛」である。

## 0. 本書の版と発効

**cohort 2 v1 (2026-09-08)。** dev-wave `t2265-cohort2` の段 4 で凍結し、**この cohort の測定を
1 件も投入する前に** docs のみの commit で固定する。本走は本書を含む commit を指して起動し、
成果物 JSON は本書の bytes の sha256 を `counterfactual_preregistration` へ記録する。
結果 commit より後に書かれた変更は事前登録として数えない。発効後の変更は旧版を Git 履歴に
残したまま新しい commit で行い、変更理由と時点を本節へ明記する。

**cohort 1 の 12 成果物、その解析器、その判定は本書によって 1 bit も変わらない。**
cohort 1 の主判定は `inconclusive` のまま確定しており、本書はそれを覆さない。

### 0.0 本書が扱う推定対象は cohort 1 と同一ではない

**これが本書の最も重要な限定である。**

- cohort 1 の推定対象は、**「commit 数 10,000 到達」か「10,240 µs 経過」のどちらか早い方で閉じる
  混合窓**の上で定義した局所 ITT である。
- cohort 2 の推定対象は、**「commit 数 10,000 到達で閉じる窓」**の上で定義した局所 ITT である
  (§3 で時間 cap を実質無効化するため)。
- count で閉じる窓では `window_commits` がほぼ閾値に張り付き、`window_us` が処置の影響を受ける
  停止時間になる。**これは無効な outcome ではないが、cohort 1 とは別の outcome である。**

**したがって本書の判定を「cohort 1 の主判定を確定させた」「cohort 1 の主仮説を確認した」と
読んではならない。** 本試験は **cohort 1 を pilot とした、関連する新しい count-closed 推定対象に
対する前向き確認試験**である。

**なぜ同一の推定対象で決着させないのか。** cohort 1 の主層では、12 run のうち 1 run が
`seq >= 1` の `window_commits = 0` により無効化された。同じ窓構成で同じ規模を測り直すと、
12 run のどれかで再発する確率は `1 - (11/12)^12 = 0.648` である。**同一の推定対象のままでは、
事前登録した規則の下で判定を安定して出せない。** 規則を緩めて 0 commit の窓を個別に落とす案は、
処置後 outcome による選択なので採らない (絶対規律 2 と cohort 1 §7)。残る道は、0 commit の窓が
構成上生じない窓構成を**結果を見る前に**固定することだけである。本書はそれを行う。

### 0.1 本書は盲検の holdout ではない — 見たものを列挙する

**cohort 2 のデータはまだ 1 bit も存在しない。** その意味で本書は前向きである。しかし設計は
cohort 1 の outcome を見たうえで決めている。**data-informed な前向き protocol であって、
未観測からの設計ではない。**

本 cohort 2 は outcome-naive な追試ではない。設計凍結前に、cohort 1 の全 12 成果物と v1 / v2 の
結果を閲覧した。閲覧したものを列挙する。

1. **v2 の主判定が `window_commits_zero` により `inconclusive` であること。**
2. **`seq >= 1` の 0 commit が policy 2 / write-heavy / 48 threads の同一 seed
   (`13467815584134101060`) に 2 件あり (`seq = 10`, `seq = 11`)、いずれも time-cap closure
   だったこと。**
3. **全 18 cell では `seq >= 1` の cap closure が 206 件だったこと** (p1 balanced 24t が 201、
   p1 write-heavy 48t が 1、p2 write-heavy 48t が 4)。
4. **主層の event 数が run あたり 555 から 671 件 (中央値 617) だったこと。**
5. **最後の記録済み窓の `window_us` が 2,560 から 10,846 µs だったこと。**
6. **`seq = 0` の窓が起動の暖機を含み、`window_us` が 15,000 から 75,557 µs だったこと。**
7. **1 job (18 run) の所要が 135.9 から 138.7 秒だったこと。**
8. **cohort 1 の 11 run の個別推定値。** `estimate_log` の平均は `0.0684247345914534`
   (比では +7.082%)、run 間標準偏差は `0.0283107778380306` である。この 11 件に cohort 1 の判定則を
   そのまま当てると `SE = 0.008173`、95% CI = `[0.050437, 0.086413]` となり、下端が
   `Delta = 0.029559` を上回るため「推奨方向の実用優越」になる。
   **ただしこれは cohort 1 の判定ではない。** cohort 1 §7 は、欠落理由が outcome の 0 である以上
   11 run の complete-case 集計を禁じている。上の数値は **cohort 2 の設計に使った pilot 情報**として
   だけ開示する。
9. **cohort 1 の副次 5 層がいずれも正の点推定を示したこと** (write-heavy 24 で +7.293%、
   balanced 24 で +10.268%、balanced 48 で +7.284%、read-heavy 24 で +4.242%、
   read-heavy 48 で +6.058%)。
10. **cohort 1 の生死確認で見た腕の構造** (割当比、割当前の両方向可否、反転の実現率)。

`window_commits` と `window_us` は指定 outcome `T` の構成要素であり、trigger と event 数も速度に
依存する量である。これらの観察を受けて、time cap の実質無効化、count-closed terminal、
nominal 観測長 6 秒、terminal 期限 5 秒を選んだ。

**したがって本設計は cohort 1 の outcome に informed された新規 cohort の前向き protocol であって、
盲検の holdout でも cohort 1 と同一推定対象の反復でもない。**

**それでも判定則は 1 文字も変えない。** 片側検定にしない。等価域を動かさない。主層を変えない。
`R` を効果量に合わせて削らない。開示済みの情報を使ってよいのは「`R = 12` が足りるかの確認」までで
あり、その確認も §5 の限定つきである。**cohort 2 の結果が上の pilot と食い違った場合、pilot に
合わせて解析を変えない。**

**confirmatory set に含める固定 12 run の outcome は、本書の凍結前に一つも閲覧していない。**

**凍結後に走らせる生死確認 (pilot) の扱い。** 本書を凍結した後、機構が仕様どおり動くことを確かめる
ため 1 job だけ pilot を走らせる。**pilot は別の出力 namespace へ置き、confirmatory set から
永久に除外する。** pilot で閲覧した field と集約値は insight へ全て列挙する。
**pilot が仕様どおりの挙動を示さなかった場合、本書を書き換えず、新しい版を新しい commit で凍結し、
その理由と時点を §0 へ記す。** pilot を confirmatory set へ算入しない。

## 1. 主張してよい範囲と限界

cohort 1 の事前登録 §1 を引き継ぐ。要点を再掲する。

- **推定対象は trace 有効な診断系における局所応答である。** 絶対規律 1 に従い、この build の
  commit 速度を性能主張に使わない。成果物は `throughput_scope=diagnostic_only` /
  `headline_eligible=false` を記録する。**本書の判定は機構の局所効果についてのものであって、
  throughput の性能結果ではない。**
- **同一軌跡上の反実仮想ではない。** 更新 i の pre-state は先行する割当の結果である。
  推定するのは「混合方策の軌跡のまわりで 1 歩を反転させたときの限界効果」である。
- **常に反転する腕 (policy 1) の run 全体効果へ読み替えてはならない。**
- 方向的中率は処置効果の推定量ではない。判定に使わない。
- 単一環境 (Pegasus gen_S、48 物理コア、HT 無効)、単一 protocol (Silo)、YCSB 3 workload、
  records 1,000,000 の下でしか言えない。
- **本試験の判定を variant の採用根拠・fitness・選択結果へ昇格させてはならない (絶対規律 2)。**
- **§3 が定める時間 cap の値と比較方法は計装ではなく CC 本来の機構である。** trace の有効・無効に
  関わらず同じ値が効く。したがって cohort 2 の cell は cohort 1 の cell とは異なる CC 設定である。

## 2. 腕と割当

cohort 1 の事前登録 §2 の 3 腕をそのまま使う。**step policy の意味、LCG、bit 63 の取り出し、
clamp との順序、`both_actions_feasible` の定義は 1 字も変えない。** cell 文字列の 12 field 書式も
変えない。変えるのは §3 が定める窓構成の field の値と label だけである。

割当は、更新ごとに 1 回だけ進む 64 bit LCG
`state <- state * 6364136223846793005 + 1442695040888963407 (mod 2^64)` の bit 63 である。
LCG は勾配 0・推奨差分 0・clamp のときも毎更新で進む。反転は clamp の**前**に当たるので、
反転した一歩も clamp されうる。`both_actions_feasible` は**割当を当てる前**の pre-state から決まる。

**「無作為」の意味の限定も引き継ぐ。** 割当列は seed と更新 index だけで決まる決定的な疑似乱数列で
あり、すべて同じ full-period LCG 周期上の異なる開始点である。**形式的に独立な乱数 stream ではなく、
物理過程との統計的独立性は証明されていない。** 推定するのは「事前に固定した疑似無作為列が run の
物理過程と同期していない」という as-if 無作為化の仮定のもとでの割当 ITT である。この仮定は
検証していない。

**(cohort 2 で追加) 割当整合性検査 (assignment-integrity check)。** 解析器は、成果物の
`assigned_invert` 列が `step_policy_seed` から上の LCG で生成される列と exact に一致することを
検査する。一致しない成果物は入力として不適格とする。

**この検査は無作為化の検証ではない。** 割当が実装どおりに記録されたことを示すだけであり、
上の as-if 無作為化の仮定は依然として未検証である。「LCG により無交絡の因果効果が証明された」と
書いてはならない。

## 3. 測定条件

| 項目 | 値 |
| --- | --- |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 24, 48 |
| records | 1,000,000 |
| 観測長 | nominal `extime` = 6 秒、1 job あたり 1 rep、rep index 0 |
| terminal 期限 | `CCBENCH_BACKOFF_TRACE_TERMINAL_US` = 5,000,000 µs |
| build | trace 有効 (`BACKOFF_TRACE=1`)。診断専用 |
| trace schema | `izanagi-dynamic-backoff-trace/v4` |
| 反復 | 12 seed = 12 job。1 job が 3 腕 x 3 workload x 2 threads = 18 run を回す |

**cohort 2 の exact な cell 文字列 (12 field 書式)。**

| label | cell 文字列 | 役割 |
| --- | --- | --- |
| `cw-as-dyn-c2-p0` | `cw-as-dyn-c2-p0:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:0` | stock の更新則 (反転なし) |
| `cw-as-dyn-c2-p1` | `cw-as-dyn-c2-p1:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:1` | 常に反転 |
| `cw-as-dyn-c2-p2` | `cw-as-dyn-c2-p2:1:1:1000:2560:10000:9223372036854775807:1:1:4:1:2` | 更新ごとに反転を割り当てる (**主推定量の腕**) |

**窓構成。** 更新は「前回の更新から `2,560` µs 以上経過し、かつ (commit 数が `10,000` 以上、
または経過が時間 cap 以上)」で発火する。cohort 2 は時間 cap を `9223372036854775807` µs とし、
**どの run 内でも cap が発火しないようにする。** したがって記録される通常窓はすべて commit 数で
閉じ、`window_commits >= 10,000 > 0` が**構成上**保証される。

**この巨大な cap を安全に扱うため、cap の比較を `elapsed / clocks_per_us_ >= cap_us` へ変える。**
正の整数では `floor(e/c) >= cap` と `e >= c * cap` は厳密に同値なので、既存 cell の挙動は 1 つも
変わらない。乗算のままでは `clocks_per_us_ * cap_us` が 64 bit を溢れ、cap が即座に発火する。

**terminal event。** run 開始から terminal 期限を過ぎた後、**最初に commit 数で閉じた窓**を
terminal event として 1 件だけ記録する。terminal event は
- 通常の更新を行う**前に**記録し、
- **backoff を更新せず、LCG を進めず、割当を当てず**、
- `assigned_invert` に非適用を表す sentinel を持ち、
- run につき **ちょうど 1 件**であり、**必ず trace の末尾**である。

terminal event も commit 数で閉じるので `window_commits >= 10,000` を満たす。
terminal を記録した後、その run では以後の event を記録しない。

**保証の範囲を限定する。** 上の構成上の保証が及ぶのは、**count 閾値へ到達して受理された窓**に
限られる。commit が止まって count 閾値へ到達しない場合の扱いは §7 に定める。

**直列性認証の状態。** 本 cohort の policy≠0 cell については、**既定の step policy seed で build した
実行体と 48 スレッドの条件についてのみ**直列性認証を行う。**cohort 2 が実際に使う 12 本の seed 別
実行体の認証ではなく、24 スレッド条件の認証でもない。** したがって本試験は**未認証**であり、
判定を正しさの主張に使わない (絶対規律 2)。

## 4. 主推定量

run `r` の policy 2 trace event を時系列 `i = 0, ..., n_r - 1` (通常 event) とし、terminal event を
`f_r` とする。次を固定する。

```text
Z[r,i] = assigned_invert            0 = 推奨方向を割当 / 1 = 反転方向を割当
T[r,i] = window_commits[r,i] / window_us[r,i]
T[r,f] = window_commits[r,f] / window_us[r,f]      (terminal。割当を持たない)
Y[r,i]     = ln(T[r,i+1] / T[r,i])     i = 1, ..., n_r - 2
Y[r,n_r-1] = ln(T[r,f]   / T[r,n_r-1])
D[r]   = mean(Y[r,i] | Z[r,i] = 0) - mean(Y[r,i] | Z[r,i] = 1)
theta  = (1/R) * sum_r D[r]
```

- **符号**: `theta > 0` は、推奨方向の一歩の方が反転方向の一歩より直後の窓の commit 速度を
  大きくしたことを意味する。
- event `i` に載る窓統計は割当 `Z[r,i]` より**前**に終了した窓のものであり、`Z[r,i]` が変えた
  backoff が支配するのは次の窓である。
- **`i = 0` は §7 の位置除外により、分子としても分母としても使わない。**
- **terminal は `following` としてだけ使う。** `Z[r,f]` は定義しない。割当数、割当率、
  `recommended_delta_sign`、`both_actions_feasible`、時間 block の current event に terminal を
  入れない。terminal を current として扱う実装は schema 違反とする。
- **terminal があるので、位置除外の後に残るすべての割当が後続窓を持つ。** cohort 1 §4 が持っていた
  「最後の更新は次の窓を持たないので必ず落とす」という限定は、cohort 2 には無い。
- 隣接する `Y` は同じ窓を共有し、持ち越しもありうる。この依存は run 内でモデル化せず cluster 化する。

**推定対象の逐語定義。** 「初回更新を除き、terminal 期限より前に発生した割当について、次の
count 閾値閉鎖までの rate 変化を測り、最後の割当も count-closed terminal を following として
含める割当 ITT」である。

**集約**: run を cluster とする等重み平均。

```text
s_D^2       = sum_r (D[r] - theta)^2 / (R - 1)
SE(theta)   = s_D / sqrt(R)
R           = 12
df          = R - 1 = 11
```

表示は `100 * (exp(x) - 1)` % で行う。

**主層は (policy 2, write-heavy, 48 threads) の 12 run だけ。** 他の 5 つの (workload, threads) は
副次であり、主判定に使わない。**主層を cohort 1 の副次層の結果を見て選び直していない** —
cohort 1 v1 が outcome を見る前に固定した層をそのまま使う。

## 5. 等価域と検出力

```text
Delta = ln(1.03) = 0.029558802...
等価域 = [-Delta, +Delta]
```

**判定** (主層について。cohort 1 と同一):

- **等価**: 90% CI の TOST が非等価を棄却する (両側の片側 5% 検定)。`t(0.95, 11) = 1.7958848`。
- **推奨方向の実用優越**: 95% CI の下端が `+Delta` より大きい。`t(0.975, 11) = 2.2009852`。
- **反転方向の実用優越**: 95% CI の上端が `-Delta` より小さい。
- それ以外は **inconclusive**。**非有意を等価と呼ばない。95% CI が 0 を跨がないだけでは実用優越と
  呼ばない。** TOST の結果と 95% CI を別に報告する。

**`R = 12` が十分だとは主張しない。**

- 真値 `theta = 0`、独立で概ね正規な run 差、cluster SD `<= 0.032`、12 run 完備という条件の下で、
  cohort 1 v1 §5 の計画モデルでは等価判定力は約 `0.823` である。
- **この計画仮定は cohort 1 の推定対象に対するものであり、cohort 2 の新しい推定対象に対する
  cluster SD は未検証である。** 観測長を伸ばせば run 内の誤差は減りうるが、隣接する `Y` は同じ窓を
  共有し持ち越しもあるので、event 数は有効独立数ではない。cluster 間のばらつきが減る保証はない。
- **実用優越については効果量の仮定を置いておらず、検出力を主張しない。**
- **実測した `s_D`、達成 CI 半幅、`decision` を必ず報告する。TOST が棄却しなければ inconclusive と
  書く。検出力が足りなかった試験から等価を主張しない。**

## 6. 層と副次解析

副次はすべて探索的な記述であり、主判定を置き換えない。多重比較の補正はしない。

1. 残る 5 つの (workload, threads) それぞれの `D[r]` と 95% CI。
2. `recommended_delta_sign` (`-1` / `0` / `+1`) による層別。
3. `both_actions_feasible` (`0` / `1`) による層別。
4. run 内の相対位置で 4 分した時間 block による層別。**4 分割は §7 の位置除外を適用した後に残る
   outcome の index と件数を基準に数える。** 生の event 列で数えない。terminal は current に
   入らないので block の分母にも入らない。

**2〜4 の層別変数はいずれも現在の割当より前に確定するが、先行する割当の影響を受けた状態である。**
したがってこれらの層内の対比を因果効果として解釈せず、機序の手がかりとしてだけ読む。
層を恣意的に交差させて「効いた部分集合」を選ばない。各軸の周辺層だけを出す。
`inversion_realized` は層にも除外にも使わない。

**trace 有効な走行の `median_tps` を腕どうしで比べた表は作らない。**

**cohort 1 の副次 5 層の符号を、cohort 2 の主判定の確認・救済・一般化に使わない。**
既に閲覧した探索的な prior context として開示するだけである。

## 7. 除外規則

cohort 1 v2 §7 を引き継ぐ。**緩めない。**

- **落としてよいのは 1 つだけである。`seq = 0` の event、すなわち各 run の最初の更新。**
  分子としても分母としても使わない。除外は **event の位置だけ**で決まる — outcome の値、割当、
  実現した反転、clamp、勾配、trigger のいずれも見ない。全 run から一律に先頭 1 件を落とす。
  除外後、最初の outcome 対は (`seq = 1`, `seq = 2`) になる。
  (cohort 1 にあった「後続 event を持たない最後の更新」の除外は、§4 の terminal により不要になった。)
- **禁止する除外**: clamp が当たったか、実適用差分が 0 か、`inversion_realized`、
  `recommended_delta_sign`、`both_actions_feasible`、trigger、勾配、刻み、上限、時間 block、
  outcome の値、外れ値、および結果を見てからの run・層の取捨。
  `recommended_delta_sign = 0` と `both_actions_feasible = 0` の更新も主解析に残す。
  **これが ITT である。**
- **`window_commits = 0` の判定は、位置除外を適用した後に残る event (terminal を含む) に対して
  行う。残存 event に 0 が 1 件でもあれば、その event だけを落とさず主判定全体を inconclusive に
  する。** **窓構成を変えたことを理由にこの規則を緩めない。** 窓構成の変更は 0 が構成上生じない
  ようにするものであって、生じたときの扱いを変えるものではない。
  **結果を見た後に本規則を改訂しない。**
- **terminal 非閉鎖の扱い。** 固定した 12 seed のいずれかで terminal event が生成されなかった
  場合 (commit が止まって count 閾値へ到達しなかった場合を含む)、**その seed を outcome に基づいて
  置換も除外もせず、主判定全体を inconclusive にする。** 設備・queue・build・identity の
  outcome-blind な不成立 (§8 の再投入事由) とは区別し、区別できない場合は inconclusive 側に倒す。
- **片方の割当が run 内に 1 件もない場合も、その run を選択的に除外せず主判定を inconclusive に
  する。**
- 主判定には **12 cluster の完備を要求する。** 12 未満なら確認的判定を出さない。
- schema、sha256、exact axes、seed、trace summary、`seq` の連続性、terminal の一意性と末尾性、
  **および §2 の割当整合性**に違反する成果物は入力として不適格とする。
  **`seq` の連続性検査は生の成果物に対する schema 検査であり、上の位置除外とは別物である。**

## 8. seed と停止規則

- **停止規則**: 固定 12 job を投入する。**途中解析をしない。結果を見てから job を足さない。**
  再投入は、outcome を開く前に確認できる理由 (queue、node、prologue、build、identity、成果物の
  未完成) に限り、同じ seed で最大 2 回まで許す。成果物が完成した slot は最初に完走した 1 件だけを
  採り、値を見てから測り直さない。**完成した成果物を、遅さ・分散・効果・clamp・terminal 非閉鎖を
  理由に置き換えない。**
- 12 run が揃わなければ確認的判定を出さない。

### 8.1 seed の逐語一覧

生成規則は、ASCII 文字列 `izanagi-t2265-cohort2-policy2-seed-NN` (`NN` は 2 桁 10 進、00〜11) の
SHA-256 の先頭 8 byte を big-endian の符号なし 64 bit 整数と読んだものである。親が 12 値すべてを
独立に再計算し、相異なることと 0 でないことを確認した。**cohort 1 の 12 seed とは別である。**

| slot | seed (10 進) |
| ---: | ---: |
| 00 | 14481721328008317845 |
| 01 | 7453732891837486670 |
| 02 | 766609016836229506 |
| 03 | 14479507243158715447 |
| 04 | 3736279228254271919 |
| 05 | 6574519577559702715 |
| 06 | 15525319108568766040 |
| 07 | 13039315294558381935 |
| 08 | 16889140200793892447 |
| 09 | 15536816158447092057 |
| 10 | 13171317188614694465 |
| 11 | 3421410286381859835 |

**seed を複数使う理由。** 割当列は seed と更新 index だけで決まる。同じ seed の run はどれも同一の
割当列を持つので、その列が run の周期的な物理過程と偶然そろった場合、その偏りは run を増やしても
平均化されない。異なる開始点を使えばこの偏りは平均化される。**ただしこれらは同じ LCG 周期上の
異なる開始点であって、形式的に独立な stream ではない** (§2)。

**無作為化の検査 (割当前の量)**: 各 run の実測割当比を記録し、0.5 から大きく外れる run があれば
その事実を報告する。**この検査の結果で run を除外しない。**

## 9. 記録する束縛

各成果物 JSON に次を記録する: `repo_head`、`counterfactual_preregistration` (**本書**の bytes の
sha256、64 文字の小文字 hex)、`prereg_sha256` (旧書の sha256、測定条件の束縛)、`patch_stack` と
各 sha256、`binary_sha256`、`step_policy`、`step_policy_seed`、`hostname`、`pbs_jobid`、
`measured_utc`、`backoff_trace_symbol_count` / `backoff_trace_string_count`、`throughput_scope`、
`headline_eligible`、trace schema 版、terminal event の有無と件数。

**解析上の run identity は `(exact cell literal, step_policy_seed, binary_sha256)` の組とする。**
seed は compile 時の define なので、12 の成果物は同じ cell label でも genome・buildcache key・
binary sha が異なる。**解析はこれらの一致を要求してはならない。** policy 0 / 1 は seed を使わないので
既定 seed の genome を保つ。

**本書用の解析器は本 cohort 専用である。** cohort 1 と同じ理由で、将来 cohort 用の互換層は作らない。
`counterfactual_preregistration` に本書の sha を付けてよいのは、**§2 の exact な 3 腕と §3 の
exact な軸・cell・観測長で走った成果物にだけ**である。ほかの格子で走った成果物へ付けてはならない。

## 10. 本書が覆わない次の一手

- **policy 腕の trace 無効な性能測定。** 腕どうしの throughput 比較には、腕と job 内時刻の交絡を
  避ける巡回順の block 設計と、独自の事前登録が要る。本書は覆わない。
- **12 seed 別 binary の全認証と 24 スレッド条件の認証** (§3 の限定)。
- cohort 1 と cohort 2 の推定対象の数値的な近さの評価。本書は近いとも遠いとも主張しない。
