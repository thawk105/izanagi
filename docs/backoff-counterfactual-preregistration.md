# adaptive backoff の反実仮想対照 — 事前登録

`patches/cicada-adaptive-counterfactual.patch` が入れた 3 値の step policy を使い、「制御器が選んだ
一歩の向きは、直後の窓の commit 速度を変えるか」を測る試験の事前登録である。機構の一次資料は
`output/insights/2026-09-07_t2265-backoff-counterfactual/README.md`。測定対象の protocol は Silo
(`ycsb_silo.exe`) で、「Cicada」は adaptive backoff 算法の由来を指す。

## 0. 本書の版と発効

**v1 (2026-09-07)。** dev-wave `t2265-backoff-itt` の段 4 で凍結し、**反実仮想の腕の outcome を 1 つも
見る前に** commit した。本走は本書を含む commit を指して起動し、成果物 JSON は本書の bytes の
sha256 を `counterfactual_preregistration` へ記録する。結果 commit より後に書かれた変更は事前登録として
数えない。発効後の変更は旧版を Git 履歴に残したまま新しい commit で行い、変更理由と時点を本節へ
明記する。

**本書だけが本試験の事前登録である。** 同 wave の段 2 プラン
(`output/insights/2026-09-07_t2265-backoff-itt/verbatim/s2-plan.md`) と親の草稿
(同 dir の `prereg-draft.md`) は、符号・seed・等価判定・欠測規則が本書と異なる**破棄済みの中間成果物**
であり、事前登録として参照してはならない。採否の理由は同 dir の `s4-ruling.md` にある。

**旧事前登録 `docs/dynamic-backoff-preregistration.md` は本試験を覆わない。** 旧書は 7 腕の run 単位
throughput 比 (等価域 ±3%) を固定したもので、腕 `cw-as-dyn-p1` / `cw-as-dyn-p2`、seed、更新単位の
推定量、その等価域を一度も固定していない。成果物が記録する `prereg_sha256` は旧書を指し続けるが、
それが束縛するのは旧書が定めた測定条件 (workload、records、build、patch stack) だけであり、
**本試験の推定量と判定は本書だけが束縛する。**

### 0.1 本書は盲検の holdout ではない — 見たものを列挙する

前向きに固定できるのは「**指定した outcome を一度も観測していない時点で** §1〜§9 を固定した」ことだけ
である。設計は次の 3 つを見たうえで決めている。**これは data-informed な前向き protocol であって、
未観測からの設計ではない。**

1. **既存の v1 診断走行** (job `0:978021.nqsv`、policy 未実装、現行 policy 0 と同じ更新則) の更新数・
   窓 log 比の散らばり・実現 backoff の分布。逐語は
   `output/insights/2026-09-07_t2265-backoff-itt/verbatim/stage1-measurements.md`。
2. **48 スレッド write-heavy の静的 backoff 曲線**
   (`output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`)。
   **本書はこの曲線を等価域の根拠に使わない** (§5)。
3. **反実仮想の腕そのものの構造データ** (job `0:981337.nqsv`、生死確認)。見たのは event 数・割当比・
   割当前の両方向可否・反転の実現率・trace の版だけで、指定 outcome (窓の commit 速度、その比、
   `median_tps`、`abort_rate`、方向的中率) は見ていない。検査器は field を allowlist で絞ったうえで
   artifact を開く前に書いた。逐語は同 dir の `stage1-liveness.md` と `stage1-liveness-inspector.py`。
   **これらは処置に依存する構造量である。**「腕の出力を一切見ていない」とは言えない。
   この構造データは主層の説明 (§4) と反復数の説明 (§5) に使った。
   **job `0:981337.nqsv` の成果物は本試験の証拠に数えない** (旧 driver、既定 seed、`pending` 束縛)。

## 1. 主張してよい範囲と限界

- **推定対象は trace 有効な診断系における局所応答である。** 絶対規律 1 に従い、この build の
  commit 速度を性能主張に使わない。成果物は `throughput_scope=diagnostic_only` /
  `headline_eligible=false` を記録する。**本書の判定は機構の局所効果についてのものであって、
  throughput の性能結果ではない。** 対比は同一 build・同一 run の中の更新どうしで取るので、
  計装の負荷は両群に共通であり対比を交絡しない。
- **すべて未認証である。** policy≠0 の cell は現行の直列性認証の exact 2 cell 契約に入らない。
  本試験は正しさを主張せず、認証は本 wave の scope 外に置く。判定結果を variant の採用根拠、
  fitness、選択結果へ昇格させてはならない (絶対規律 2)。
- **既知の記録上の欠陥。** driver が全成果物へ書く共通の `not_certified` 文言は
  「trace-disabled performance runs only」と述べるが、本試験の成果物は trace 有効である。
  この文言は本試験より前から存在する欠陥であり、本 wave では直さない。**build 種別の正本は
  `backoff_trace` / `throughput_scope` / `kind` であって、この文言ではない。**
- 単一環境 (Pegasus gen_S、48 物理コア、HT 無効)、単一 protocol (Silo)、YCSB 3 workload、
  records 1,000,000 の下でしか言えない。
- **同一軌跡上の反実仮想ではない。** policy 2 は更新ごとに反転の有無を割り当てるが、更新 i の
  pre-state 自体が先行する割当の結果である。したがって推定するのは「混合方策の軌跡のまわりで
  1 歩を反転させたときの限界効果」である。
- **常に反転する腕 (policy 1) の run 全体効果へ読み替えてはならない。** 持ち越しは測っておらず、
  policy 0 と policy 1 は最初の更新から別の軌跡を辿る。実際、生死確認では policy 1 の
  write-heavy 48 で割当 1.000 に対し反転の実現が 0.492 しかなく、割当前に両方向可なのは 0.246 だった。
  常に反転する腕はこの regime で backoff を clamp 領域へ追い込んでいる。
- 方向的中率は処置効果の推定量ではない。本書はそれを判定に使わない。

## 2. 腕と割当

機械 label と exact な cell 文字列 (12 field 書式):

| label | cell 文字列 | 役割 |
| --- | --- | --- |
| `cw-as-dyn-p0` | `cw-as-dyn-p0:1:1:1000:2560:10000:10240:1:1:4:1:0` | stock の更新則 (反転なし) |
| `cw-as-dyn-p1` | `cw-as-dyn-p1:1:1:1000:2560:10000:10240:1:1:4:1:1` | 常に反転 |
| `cw-as-dyn-p2` | `cw-as-dyn-p2:1:1:1000:2560:10000:10240:1:1:4:1:2` | 更新ごとに反転を割り当てる (**主推定量の腕**) |

policy 2 の割当は、更新ごとに 1 回だけ進む 64 bit LCG
`state <- state * 6364136223846793005 + 1442695040888963407 (mod 2^64)` の bit 63 である。
LCG は**勾配 0・推奨差分 0・clamp のときも毎更新で進む** (patch C の該当行で確認済み)。反転は clamp の
**前**に当たるので、反転した一歩も clamp されうる。`both_actions_feasible` は**割当を当てる前**の
pre-state から決まる。

**「無作為」の意味を限定する。** 割当列は seed と更新 index だけで完全に決まる決定的な疑似乱数列で
あり、すべて同じ full-period LCG 周期上の異なる開始点である。**形式的に独立な乱数 stream ではなく、
物理過程との統計的独立性は証明されていない。** 本書が推定するのは、**「事前に固定した疑似無作為列が
run の物理過程と同期していない」という as-if 無作為化の仮定のもとでの**割当 ITT である。この仮定は
検証していない。

## 3. 測定条件

| 項目 | 値 |
| --- | --- |
| workload | write-heavy (rr 5) / balanced (rr 50) / read-heavy (rr 95)、zipf 0.9、rmw 0、max_ope 10 |
| threads | 24, 48 |
| records | 1,000,000 |
| extime | 3 秒、1 job あたり 1 rep、rep index 0 |
| build | trace 有効 (`BACKOFF_TRACE=1`)。診断専用 |
| ccbench | pin `511c9538e4e8efa54b45cda62e72389ed3b706ec` + patch A (`9b2153e0547e167888ba2616750951365c4a075a80f9a95be6000e60b6f8f54b`) + patch B (`f3fe6b7e67931775bcef0a7831dda8c6cb53dfc7fc52a74f4508360e1fedf824`) + patch C (`794b7b48dd19e30560dddc27f4408d67923d801241046df53257a8aefe82a396`) |
| driver | `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` の `--backoff-trace` |
| 反復 | 12 seed = 12 job。1 job が 3 腕 x 3 workload x 2 threads = 18 run を回す |
| 出力 | `/work/1/SFC/tanab/izanagi-job-evidence/dynamic-backoff/trace/t2265-itt/` |

**投入経路の契約は変更しない。** 上記の cell 集合・workload・threads・rep index は、
`_validate_backoff_trace_contract` と投入スクリプトの exact literal 検査を**改訂せずに**通る。
新しい Pegasus 実行体を作らない。

## 4. 主推定量

run `r` の policy 2 trace event を時系列 `i = 0, ..., m_r - 1` として、次を固定する。

```text
Z[r,i] = assigned_invert            0 = 推奨方向を割当 / 1 = 反転方向を割当
T[r,i] = window_commits[r,i] / window_us[r,i]
Y[r,i] = ln(T[r,i+1] / T[r,i])      i = 0, ..., m_r - 2
D[r]   = mean(Y[r,i] | Z[r,i] = 0) - mean(Y[r,i] | Z[r,i] = 1)
theta  = (1/R) * sum_r D[r]
```

- **符号**: `theta > 0` は、推奨方向の一歩の方が反転方向の一歩より直後の窓の commit 速度を
  大きくしたことを意味する。
- event `i` に載る窓統計は割当 `Z[r,i]` より**前**に終了した窓のものであり、`Z[r,i]` が変えた backoff が
  支配するのは event `i+1` の窓である。添字は 1 個もずれていない (patch と parser の現物で確認済み)。
- **最後の更新は次の窓を持たないので必ず落とす。** ただし「どの更新が最後になるか」は割当に依存しうる
  (割当が commit 速度を変えれば、次の更新が 3 秒の測定内に起きるかが変わる)。したがって本書の推定量は
  厳密には**「後続 event を持つ更新の上で定義した割当 ITT」**である。影響量は 1 run あたり 1 件、
  主層の実測長 583 件に対して 0.17% である。
- 隣接する `Y` は同じ窓を共有し、持ち越しもありうる。この依存は run 内でモデル化せず cluster 化する。

**集約**: run を cluster とする等重み平均。

```text
s_D^2       = sum_r (D[r] - theta)^2 / (R - 1)
SE(theta)   = s_D / sqrt(R)
df          = R - 1 = 11
```

表示は `100 * (exp(x) - 1)` % で行う。

**主層は (policy 2, write-heavy, 48 threads) の 12 run だけ。** 他の 5 つの (workload, threads) は
副次であり、主判定に使わない。

**主層の根拠 (outcome を見る前に固定した).** policy 0 相当の既存 v1 診断で、この regime が最大の
backoff 滞在量 (中央値 5〜6 µs、p90 10〜11 µs、最大 17〜21 µs) と最小の勾配 0 比 (0.1〜0.3%) を示し、
局所効果が最大と予想されるためである。これは **data-informed に前向きに 1 つ固定した主層**である。
**「他の regime には腕が届かない」という主張ではない。** 実際、balanced 48 の勾配 0 比は 2.1〜8.1% で
あり、policy 2 の生死確認では全 6 regime で割当前の両方向可否が 0.967〜0.982 だった。処置は全 regime に
届いている。全 6 regime の結果を副次として示す。

## 5. 等価域と検出力

```text
Delta = ln(1.03) = 0.029558802...
等価域 = [-Delta, +Delta]      (比では [1/1.03, 1.03] = [0.970873786..., 1.03])
```

**±3% を採る根拠は、旧事前登録および B-10 が実用差として使ってきた幅を踏襲することだけである。**
腕の向きを入れ替えても不変にするため、比の域 `[0.97, 1.03]` ではなく対称な log 域を使う
(`ln(0.97) = -0.030459` と `ln(1.03) = +0.029559` は絶対値が異なる)。

**静的 backoff 曲線を等価域の根拠にしない。** 固定 backoff の定常応答から、約 2.5 ms の直後 1 窓に
どれだけの効果が出るかは導けない。次の窓には更新前に始まった transaction、制御状態の持ち越し、
窓長の変化が混ざる。「機構が効いているなら必ず等価域の外に出る」とは書かない。

**判定** (主層について):

- **等価**: 90% CI の TOST が非等価を棄却する (両側の片側 5% 検定)。`t(0.95, 11) = 1.7958848`。
- **推奨方向の実用優越**: 95% CI の下端が `+Delta` より大きい。`t(0.975, 11) = 2.2009852`。
- **反転方向の実用優越**: 95% CI の上端が `-Delta` より小さい。
- それ以外は **inconclusive**。**非有意を等価と呼ばない。95% CI が 0 を跨がないだけでは実用優越と
  呼ばない。** 等価と統計的非ゼロは両立しうるので、TOST の結果と 95% CI を別に報告する。

**検出力は未観測の仮定に全面依存する。** 既存 v1 診断の run 内 SE は自己相関を無視した単一 run の
計算値であり、12 個の `D[r]` の run 間 SD の推定ではない。本書は **cluster SD = 0.032 を計画仮定**と
して置く。真値 0・正規な run 差・上記 TOST の計画モデルでの等価判定力は次のとおり (親が
200,000 回の模擬で独立に検算した)。

| 仮定 cluster SD | R = 12 での等価判定力 | 判定力 80% に要る R の目安 |
| ---: | ---: | ---: |
| 0.020 | 0.998 | 12 未満 |
| 0.025 | 0.972 | 12 未満 |
| 0.028 | 0.924 | 12 未満 |
| 0.030 | 0.878 | 12 |
| **0.032** | **0.823** | **12** |
| 0.035 | 0.726 | 15 |
| 0.040 | 0.550 | 18 |
| 0.050 | — | 27 |

**したがって R = 12 は「cluster SD <= 0.032 を仮定した条件付き計画」である。**
実測した `s_D` と達成した CI 半幅を必ず報告し、TOST が棄却しなければ inconclusive と書く。
**検出力が足りなかった試験から等価を主張しない。**

## 6. 層と副次解析

副次はすべて探索的な記述であり、主判定を置き換えない。多重比較の補正はしない。

1. 残る 5 つの (workload, threads) それぞれの `D[r]` と 95% CI。
2. `recommended_delta_sign` (`-1` / `0` / `+1`) による層別。
3. `both_actions_feasible` (`0` / `1`) による層別。
4. run 内の相対位置で 4 分した時間 block による層別。

**2〜4 の層別変数はいずれも現在の割当より前に確定するが、先行する割当の影響を受けた状態である。**
したがってこれらの層内の対比を因果効果として解釈せず、機序の手がかりとしてだけ読む。
層を恣意的に交差させて「効いた部分集合」を選ばない。各軸の周辺層だけを出す。
`inversion_realized` は層にも除外にも使わない。

**trace 有効な走行の `median_tps` を腕どうしで比べた表は作らない。** 性能への滑落経路を作らないためで
ある。

## 7. 除外規則

- **落としてよいのは 1 つだけ**: 後続 event を持たない、run の最後の更新 (§4 の限定つき)。
- **禁止する除外**: clamp が当たったか、実適用差分が 0 か、`inversion_realized`、`recommended_delta_sign`、
  `both_actions_feasible`、trigger、勾配、刻み、上限、時間 block、outcome の値、外れ値、
  および結果を見てからの run・層の取捨。`recommended_delta_sign = 0` と
  `both_actions_feasible = 0` の更新も主解析に残す。**これが ITT である。**
- **`window_commits = 0` の event が 1 件でもあれば、その event だけを落とさず主判定全体を
  inconclusive にする。** これは処置後 outcome による除外を避けるためである。
- **片方の割当が run 内に 1 件もない場合も、その run を選択的に除外せず主判定を inconclusive にする。**
- 主判定には **12 cluster の完備を要求する。** 12 未満なら確認的判定を出さない。
- schema、sha256、exact axes、seed、trace summary、`seq` の連続性など、事前の契約に違反する
  成果物は入力として不適格とする。

## 8. seed と停止規則

- **停止規則**: 固定 12 job を投入する。**途中解析をしない。結果を見てから job を足さない。**
  再投入は、outcome を開く前に確認できる理由 (queue、node、prologue、build、identity、成果物の
  未完成) に限り、同じ seed で最大 2 回まで許す。成果物が完成した slot は最初に完走した 1 件だけを
  採り、値を見てから測り直さない。完成した成果物を、遅さ・分散・効果・clamp を理由に置き換えない。
- 12 run が揃わなければ確認的判定を出さない。

### 8.1 seed の逐語一覧

生成規則は、ASCII 文字列 `izanagi-t2265-policy2-seed-NN` (`NN` は 2 桁 10 進、00〜11) の SHA-256 の
先頭 8 byte を big-endian の符号なし 64 bit 整数と読んだものである。親が 12 値すべてを独立に
再計算して一致を確認した。

| slot | seed (10 進) | 先頭 583 割当の Z=1 比 |
| ---: | ---: | ---: |
| 00 | 5744733223455690259 | 0.487 |
| 01 | 781552995023334429 | 0.467 |
| 02 | 1606918558588661 | 0.521 |
| 03 | 16736322205931003081 | 0.521 |
| 04 | 1227967287010452276 | 0.496 |
| 05 | 2171878327641984105 | 0.513 |
| 06 | 2057459156086657874 | 0.467 |
| 07 | 11135758292722279839 | 0.515 |
| 08 | 13576760736062537317 | 0.503 |
| 09 | 5470969369189575692 | 0.467 |
| 10 | 2410271300384854639 | 0.470 |
| 11 | 13467815584134101060 | 0.516 |

12 値は相異なり、いずれも 0 でない。583 は主層の実測 event 数である。

**seed を複数使う理由。** 割当列は seed と更新 index だけで決まる。同じ seed の run はどれも同一の
割当列を持つので、その列が run の周期的な物理過程と偶然そろった場合、その偏りは run を増やしても
平均化されない。異なる開始点を使えばこの偏りは平均化される。**ただしこれらは同じ LCG 周期上の
異なる開始点であって、形式的に独立な stream ではない** (§2)。

**無作為化の検査 (割当前の量)**: 各 run の実測割当比を記録し、0.5 から大きく外れる run があれば
その事実を報告する。**この検査の結果で run を除外しない。**

## 9. 記録する束縛

各成果物 JSON に次を記録する: `repo_head`、`counterfactual_preregistration` (本書の bytes の sha256、
64 文字の小文字 hex)、`prereg_sha256` (旧書の sha256、測定条件の束縛)、`patch_stack` と各 sha256、
`binary_sha256`、`step_policy`、`step_policy_seed`、`hostname`、`pbs_jobid`、`measured_utc`、
`backoff_trace_symbol_count` / `backoff_trace_string_count`、`throughput_scope`、`headline_eligible`。

**解析上の run identity は `(exact cell literal, step_policy_seed, binary_sha256)` の組とする。**
seed は compile 時の define なので、12 の成果物は同じ cell label でも genome・buildcache key・
binary sha が異なる。**解析はこれらの一致を要求してはならない。** policy 0 / 1 は seed を使わないので
既定 seed の genome を保つ。

`counterfactual_preregistration` は、**§2 の exact な 3 腕の cell 文字列と §3 の exact な軸で走った
成果物にだけ**付ける。ほかの 12 field の格子で走った成果物へ付けてはならない。本書が覆うのは
その exact な条件だけである。

## 10. 本書が覆わない次の一手

- **policy 腕の trace 無効な性能測定。** 腕どうしの throughput 比較には、腕と job 内時刻の交絡を
  避ける巡回順の block 設計と、独自の事前登録が要る。本書は覆わない。
- **policy≠0 の cell の直列性認証。**
- driver の共通 `not_certified` 文言が診断成果物と矛盾している件の修正 (§1)。
- 全ての割当に後続窓を保証する trace の延長 (§4 の限定を外すため)。
