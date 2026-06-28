# P2 ケーススタディ評価: silo 静的 backoff の合成が stock 最良を上回る (敵対的検証済み)

- **日付:** 2026-06-22 (Phase 2 ケーススタディ, env=linux-baremetal)
- **種別:** 方法論ケーススタディ (critic 帰属 → フラグ空間外の合成 → 正しさゲート → stock 超え)
- **検証:** 解析 workflow (critic 解釈 + 5 レンズ敵対的反証 + 完全性 + 合成, 8 agent / 357k tok)。
  **fatal 反証ゼロ・中核主張は5レンズを生存。** mechanism レンズが機序の特定的分解を反証 (weakens)
- **データ:** 3 campaign × 8 genome = 24 variant、全て certified serializable・anomalies=0。
  records=1m/48thread/skew0.9/clk1800、noise floor CV=2.28%。BACKOFF_FIXED = patches/silo-backoff-fixed.patch

## 確定した主張 (反証を生き残った)

- **C1. 空間外合成が contention 域で stock 最良を上回った (頑健).** write-heavy: no-backoff 1,882,125 →
  静的 10us **2,603,521 = +38.3%**。balanced: 2,791,760 → 静的 5us **3,106,342 = +11.3%**。勝者の 5-rep 配列が
  no-backoff と**完全非重複** (Mann-Whitney U=0, p=0.012)、差は noise floor の 5〜17 倍。p2-2 全探索の真の
  stock 最良比でも +39.0%/+12.9% で headline はむしろ控えめ (cherry-pick でない)。
- **C2. 全 variant が certified serializable で正しさを保った (規律2).** 性能帰属は certified 集合内の比較。
  +38% は検証緩めでなく機序由来。
- **C3. patch は構造的に inert で apples-to-apples (規律6 監査済み).** `BACKOFF_FIXED=-1` は `#else` で stock と
  プリプロセッサ的に同一。BACK_OFF gate は silo 内 2 箇所のみ (transaction.cc:42 abort 内 / :596 leaderWork)、
  validation/commit/locking パスに分岐なし。静的側は hill-climb 簿記を無視するだけで**むしろ余分なコストを払う**
  (有利化でない)。
- **C4. 逆U字 (内点ピーク) と単調性は実在.** abort%・ipc とも backoff 量に単調減 (3 workload)。内点ピークは
  warmup/熱ドリフトでは生成不能 = 人工物説の反証。
- **C5. read-heavy 対照が機序を支える.** abort baseline 低 (16%) で正の backoff 量が一つも no-backoff を超えず
  (最小 2us で -6.6%、以降単調減)。「backoff の利得は abort baseline が高いほど大きい」の対照群。

## 留保すべき主張 (over-claim を削る)

- **[weakens 機序] 「throughput = (1-abort)×ipc の積でピーク」は看板 write-heavy で peak 位置を外す.**
  write-heavy で積のピークは **25us** だが throughput のピークは **10us**。一致は balanced のみ。残差
  K=tps/((1-abort)·ipc) が backoff 増で 15-31% 単調低下 = 第三因子。`backoff.hh` の `_mm_pause`+`rdtscp` スピン
  命令が perf の instructions に算入され、ipc 低下は「stall」と「スピン命令希釈」の混交。**正しい定性は
  「abort 単調減 × (ipc 単調減 + 純待ち latency) のトレードオフで内点ピーク」**。「積で peak 位置を予測できる」
  とは書かない。なお latency[ns] は ccbench で 10^9/tps×thread の恒等再記述 (`result.cc`) = 独立情報ゼロ。
- **[weakens 一般化] 勝利は high-abort に条件付き (3 workload 中 2 勝 1 敗).** read-heavy では負ける。主張は
  「**contention 域 (write/balanced) で**」と明示的に狭める。
- **[再現性 — cross-run 確認済み, 別 boot のみ未]** 別 campaign・逆順 (fix10→fix5→none) で再測した結果:
  **balanced はクリーン再現** (+11.3%→+11.7%, drift +0.4%)、**write-heavy は勝者 fix10 が完全再現**
  (2,603,521→2,599,032 = -0.17%)。"乖離"に見えるのは no-backoff 参照が -2.9% (CV 2.19%, floor 2.28% 近傍)
  ドリフトし比が +38.3%→+42.2% に動いたため。**win は両系列で +38%超・頑健**、精度は参照ばらつき ~3% の幅。
  no-backoff (abort 82% で最も churn 激しい) が最大の run 間分散源で backoff variant の方が安定、順序は勝者を
  偏らせない (fix10 は 5番目→1番目で同値)。**残: 別 boot / rounds≥3 での確認** (本 repro は同一 boot・別系列)。
- **[soft] ピーク位置 (5 vs 10us) は soft.** 粗 grid {2,5,10,25,50,100}us の最良点。勝利の**大きさは robust、
  位置は soft**。
- **[minor 正しさの範囲] certified は perf workload を直接検証していない.** 検証 workload (tuple200/thread4/
  rmw=true) と perf (1m/thread48/rmw=0) が違う。「全 variant certified」は backoff が correctness-inert (純スピン
  待ちで read/write set・lock・validation に触れない) という**機序論証に依存**。機序は backoff.hh から構造的に
  堅固だが外挿である点は明示。

## 機序の最終説明 (read-heavy 対照を含む)

backoff 量↑ で **(a) abort 単調減** (無駄 retry 削減 = 正) と **(b) ipc 単調減 + 純待ち latency** (負) が同時。
両者のトレードオフが high-contention で内点ピークを作る:
- **write-heavy (abort 82%)**: (a) の伸び代大、sweet spot 10us。**ipc≥1.08 を保ったまま abort を半減** (81.8→49.8%)。
- **balanced (abort 70%)**: 中程度、sweet spot 5us (ipc 1.20)。
- **read-heavy (abort 16%, 対照)**: (a) の伸び代小 (16→7% しか削れず) で (b) の負だけ残る → ピークが 0 に潰れ純損。
  sweet spot は abort baseline と相関。

**over-throttling (stock 適応の敗因, 独立に頑健)**: 適応は contention 低減自体は成功 (abort を固定 grid 上端
100us 点と同等以上に潰す) だが ipc が全 workload 0.38-0.50・latency 25-52us と**固定 100us 点よりさらに低い
プラトーに駐車**。Cicada hill-climbing (kIncrBackoff=100us / kMaxBackoff=1000us) の刻みが sweet spot (5-10us) に
対し粗すぎ 1 ステップで飛び越える。**ただし収束 backoff 量そのものは未測定** (`Backoff_` の dump 経路なし、外挿)。

## 方法論的含意 (ループが実証したこと)

1. **leading indicators の帰属が空間外合成を駆動した.** throughput 単独でなく (abort, ipc, latency) の組から
   「適応は abort を潰せているが ipc 崩壊で遅い、sweet spot を行き過ぎ」と帰属 → 「binary BACK_OFF の外に backoff
   量を静的固定する新パラメータ」という具体的変異を導いた。throughput だけなら「適応は遅い」で止まった (Jitskit §3.5)。
2. **正しさゲートが空間外でも機能した (規律2).** 合成軸でも 24 variant 全て verifier 通過。
3. **stock 超えが certified 集合内で起きた.** 「ワークロード特化 CC を AI が合成し正しさを保ったまま既存最良を超える」
   という本プロジェクト中核仮説の、**限定スコープでの最初の成立例**。
4. **critic ablation は含意であって実証でない.** 帰属付き指示が sweet spot 近傍を狙わせたが、「critic 有/無の
   探索効率比較」自体は本 campaign では未実施 (P2-5 へ)。

## 次に測るべきこと (優先度順)

**必須 (方法論ケーススタディとして弱い穴):**
- **[P0 — 一部解消] cross-run 再現性.** ✅ 別 campaign・逆順で再測し headline 再現を確認 (balanced クリーン、
  write 勝者完全再現、参照 ~3% ドリフトで比に幅)。`backoff_repro.py`。**残: 別 boot / rounds≥3** (本 repro は
  同一 boot・別系列のみ。boot 間ドリフトは依然未拘束)。
- **[P0] 機序の純度 (スピン命令分離).** backoff スピン命令を instructions から分離 (perf record で `backoff()`
  占有率) し「有用 ipc」で残差 K が定数化するか。**看板 workload で積モデルが破綻 = 「なぜ速いか」が最大の穴。**
  (P2-4 profiler と地続き。)

**比較的安価 (外挿を実測に):**
- **[P1] 正しさを実測に.** 各静的 variant の trace を実 perf 構成で 1 回 verify。broken-silo を同一 backoff フラグで
  赤検出させ「backoff が verifier を盲目化しない」も確認。
- **[P1] 適応の収束 backoff 量を実測.** stock 適応 run で `Backoff_` 収束値を 1 行ログ → over-throttling を実測に。
- **[P1] base flag の一般性.** stock 第2・3位 base 上でも fix5/fix10 が no-backoff を超えるか。

**主張を広げる:**
- **[P2] 動作点 (thread/skew/records) を広げて述語付き主張へ** (「backoff の効く範囲 = abort が閾値超」)。
  ピーク位置確定 (fix2/3/5/7 を reps≥15)。待ち方 vs 待ち量の直交化 (physical-core ピンで SMT 副作用分離)。
- **[P3] rmw=1 で 1 点** (blind write 限定帰属のスコープ明確化)。

---

**最も致命的だった 2 つ (現状):** (1) ~~再現性が単一系列のみ~~ → **別系列・逆順で headline 再現を確認**
(balanced クリーン / write 勝者完全再現 / 参照 ~3% ドリフト)。残るは別 boot のみ。(2) **機序「積で peak 説明」が
看板 write workload で算術的に外れる** — 成果は本物だが「なぜ速いか」(最終成果物の一部) が看板例で破綻、依然
最大の穴 [P0]。スピン命令分離 (P2-4 profiler) が次の鍵。

**規律確認:** 全 variant certified serializable、性能帰属は certified 集合内 (規律2)、WAL/レポート内文字列に
振る舞い誘導なし (規律6)、本評価は読み取り+解析のみ。

---

## 追記 (2026-06-28): over-throttling を直接実測 [P1] — 検証済み (ODR fix #118 で解禁)

ccbench の ODR バグ ([[2026-06-22_ccbench-backoff-add-analysis-segfault]], PR #118 で master 還元 + izanagi-trace
取込) を直したことで `ADD_ANALYSIS=1` の `backoff_latency_rate` (= total_backoff_latency / 全スレッドサイクル =
machine の何割を backoff スピンに費やしたか) が使えるようになり、`backoff_overthrottle.py` で sweep 各点を
1m/48thread/skew0.9 で実測。**3レンズ敵対的検証済み** (measurement-artifact / mechanism / overthrottle-validity)。

### 実測値 (write-heavy, ADD_ANALYSIS=1)

| backoff | spin% | abort% | eff_tps=tps/(1-spin) |
|---|---:|---:|---:|
| none | 0% | 81.8% | 1.84M |
| fixed-10us (fitness sweet spot) | 51.8% | 50.7% | 4.97M |
| fixed-100us | 77.6% | 18.5% | 7.32M |
| **adaptive (stock)** | **87.3%** | 15.6% | 7.51M |

(read-heavy も同形: adaptive spin 78.0%。)

### 生存した主張 (検証済み)

- **[S1 強化] over-throttling は実在し計装固有でない (確信度 高)。** 最大の攻撃「AA=1 が適応の収束点を動かすので
  87% は計装固有」を、検証者が **AA=0/AA=1 両 build の Backoff_ 収束値を probe 実測**して反証: 時間加重平均保持
  backoff = write AA=0 **559us** vs AA=1 562us (差 0.6%)、read 603 vs 593us (差 1.6%) で**統計的に区別不能**。
  **実 fitness build (AA=0) でも適応は ~560us(write)/~600us(read) に駐車** = sweet spot 5-10us の **56-80倍**。
  → **前回の最大の留保「収束 backoff 量は未測定・外挿」を実測に置換** ([P1] を閉じた)。
- **[S1 構造的決定打] 適応コントローラは sweet spot に物理的に到達不能。** `backoff.hh` の grid は
  kMinBackoff=0 / kIncrBackoff=100us。非ゼロ最小グリッド点が 100us = sweet spot (5-10us) を既に 13x 超過。
  AA とも throughput 歪みとも無関係なコード不変条件で、桁超え over-throttling の最も強い根拠。
- **[S2] 「abort 駆動 throughput トレードオフ分解」は生存 (中〜高)。** spin% は tps と独立計測 (transaction.cc:42-50
  の rdtscp)。eff_tps 単調増は SMT/cache 人工物でない (それらは attempt-rate を増やす向きだが実測は減る = 交絡が
  逆符号)。前回破綻した「(1-abort)×ipc 積の peak 不一致」を、peak を「eff_tps の伸び vs スピン税のトレードオフ」へ
  正直に再帰属。

### 削った over-claim / 残る穴

- **[major 縮約] 「eff_tps が機序の穴を解決」は過大。** `tps = eff_tps×(1-spin)` は eff_tps:=tps/(1-spin) の
  **定義的トートロジー** (再構成誤差 全点 0)。`eff_tps/(1-abort)` が平坦 (CV 5.5%) = **eff_tps 単調増は前回 C4
  「abort が backoff 量で単調減」の再表現にすぎない** (新機序を足していない)。spin 分解は peak を tps から再構成
  するだけで**予測しない**。「解決」でなく「破綻した積モデルを正直なトレードオフ分解に置換 (ただし peak は再構成)」と書く。
- **[P0 核心は未解決]** 「非スピン時間あたりの**真の IPC** が backoff 量で一定/単調か」を**直接計測していない**。
  spin% はその代理にすぎず、eff_tps/(1-abort) 平坦性は abort 曲線の再表現で IPC を分離していない。**`perf record` で
  backoff() のスピン命令を instructions から分離し有用 ipc を測る** のが未完 = P2-4 profiler の核。
- **[minor] AA 計装 caveat:** tps の絶対値は committed fitness と非比較。load-bearing な spin%/abort% は AA に頑健
  (オーバーヘッドは rate の +0.02〜0.14%)。低 backoff の eff_tps 曲線は歪み tps 経由で揮発 (再測で fixed-5us −36%) →
  低端の曲線形状は quantitative に主張しない。生存は単調性と adaptive>fixed-100us。
- **[minor] adaptive spin% 単発の再現ばらつき ±5-7pt** (hill-climb が彷徨う)。87.3% を点推定として強く主張しない。
  robust なのは時間加重平均保持 backoff (~560us) と grid floor 構造論証。
- **[未測定] 低 contention で適応が 0us 近傍へ降りる可能性は未確認** (contention 域 write/read では ~560/600us)。
  AA=0 build の spin% 絶対値も未測定 (spin counter が #if ADD_ANALYSIS ゆえ)。

**正味:** ODR fix で [P1]「適応の駐車を外挿でなく実測」を**閉じた** (適応 ~560us / grid floor 100us / 静的 500us
spin% の3経路一致)。[P0]「なぜ速いか」核心 (有用 IPC 分離) は **perf record = P2-4 profiler** に残る。
測定ドライバ `orchestrator/campaign/backoff_overthrottle.py` (ADD_ANALYSIS 診断専用、正しさは AA=0 build で検証済み)。

---

## 追記 (2026-06-28): [P0] 機序純度を perf record で解消 (P2-4 profiler)

`BACKOFF_NOINLINE=1` 診断 build (inert patch、観測者効果 +0.76% で stock 不変を実測) で `backoff()` を
独立シンボル化し、`perf record -e cycles,instructions` で `Backoff::backoff` の cycle%/instruction% を分離 →
**有用 IPC = (全命令−spin命令)/(全cycle−spin cycle)** を write-heavy で実測
(`output/env/linux-baremetal/profile/backoff_profile_t48_skew0p9_rr5.{json,md}`、driver `backoff_profile.py`、
profiler.md エージェント実走)。

**解消した命題 (sweet-spot 域):** throughput ピークがある帯 (0-10us) で **有用 IPC は一定** (1.92/1.96/2.01/1.94、
散布 4.4% = noise floor の ~2 倍内)。一方 total IPC は 1.92→1.09 と崩壊 (全域散布 117.7%)。→ **total IPC の崩壊は
純 spin 希釈** (spin は cycle を食うが命令は少ない: fix10 で cyc 48.7%/instr 8.5%、spin IPC≈0.17)。「なぜ fix10 が
no-backoff より速いか」= **abort 半減 (82→49%) が有用 IPC 不変のまま効いた** (待たせて効率化したのではない)。
**元の積モデルが peak を 25us に外した理由を名指せた**: ipc 項に spin 混入の `total_ipc` を使っていたから
(有用 IPC では sweet-spot で ipc は減らない)。

**正直な留保 (over-claim を切る):** K_useful = tps/((1-abort)·useful_ipc) は **一定でない** (5.24M→1.47M, -72% 単調減)。
よって「有用 IPC を使えば積モデルが定数 K で predictive になる」は**不成立**。言えるのは「**sweet-spot の total IPC
低下 = spin 希釈**」まで (これが [P0] の核命題を閉じる)。残る K_useful の単調減は有効並列度低下/commit あたり命令数の
変化等の混交で、predictive な積モデルは主張しない (先行 `[major 縮約]` eff_tps トートロジーと整合、IPC レンズで再確認)。

**第二次効果 (新発見):** over-throttle 域 (25-100us) では **有用 IPC 自体が低下** (1.94→1.47、散布 20.9%) =
待ちすぎは spin 税 (cycle 食い) だけでなく有用仕事の効率も二次的に削る。stock 適応 ~560us 駐車の敗因を裏付け
(spin 希釈 + 有用 IPC 二次低下の両方を最大に食らう最悪点; 560us 点の有用 IPC は本 sweep ≤100us の外挿)。

**規律/限界:** trace-disabled build (規律1, noinline は trace と直交・既定 inert)、単一テナント直列 (規律4)。perf 下 tps は
sampling overhead 込みで **headline 非使用** (絶対値は stock build の committed fitness)。caveat: cycles/instructions の
multiplex は低 IPC 域で粗い (有用 IPC 低下の**幅**は soft、方向・単調性は頑健)、48thread 単断面。**[P0] は sweet-spot で
機序的に閉じ、over-throttle の有用 IPC 二次低下という新しい境界を足した。**
