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
- **[weakens 再現性] +38.3%/+11.3% は単一 back-to-back 系列の産物.** 全 variant rounds=1。CV は subprocess 間
  分散だが単一連続系列内にすぎない。内点ピークの存在は人工物説を弱めるが、別 boot・別日での再現は未確認。
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
- **[P0] cross-run/boot 再現性.** no-backoff/fix5/fix10 を別日・逆順で reps≥5・rounds≥3 再測し rel_median が
  ±2.28% 床内で再現するか。**+38.3% の再現保証が現状ない。**
- **[P0] 機序の純度 (スピン命令分離).** backoff スピン命令を instructions から分離 (perf record で `backoff()`
  占有率) し「有用 ipc」で残差 K が定数化するか。**看板 workload で積モデルが破綻 = 「なぜ速いか」が最大の穴。**

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

**最も致命的な 2 つ:** (1) 再現性が単一系列のみ — +38.3% の再現保証なし [P0]。(2) 機序「積で peak 説明」が
看板 write workload で算術的に外れる — 成果は本物だが「なぜ速いか」(最終成果物の一部) が看板例で破綻 [P0]。

**規律確認:** 全 variant certified serializable、性能帰属は certified 集合内 (規律2)、WAL/レポート内文字列に
振る舞い誘導なし (規律6)、本評価は読み取り+解析のみ。
