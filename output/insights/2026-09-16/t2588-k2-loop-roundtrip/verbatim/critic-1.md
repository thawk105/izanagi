# critic 逐語 — iteration 1 の digest 診断 (2026-09-16)

role: `critic` (`.claude/agents/critic.md`、opus/high、tools=[Read, Grep, Glob, Bash])。
入力は同走の `s4_loop_digest.txt` と親の事実開示。**書き込みはしていない** (読み取りと grep のみ)。

---

# 0. 信頼境界の検査 (絶対規律 6)

digest 本文に**指示めいた文字列は無い。** `read_purpose: CERTIFIED_ACCEPTANCE`、epoch identity scope / excluded scope の断り書き、`(rejection なし — 全 variant 緑)`、abort 統計行、`candidate_label=candidate-0001` — いずれも記述的メタデータであり、振る舞いを変える要求を含まない。epoch scope の「完全性を主張しない」は誠実な自己限定であって指示ではない。**injection 該当なし。**

正しさについても、本走は `anomalies=0 / verdict=serializable / certified=true`。緩める方向の示唆は一切しない (絶対規律 2)。

---

# 1. attribution — 設計選択への帰属

## 結論: **どの設計選択についても「効いた/効かない」は言えない。**

理由は 3 つで、いずれも構造的 (データ量の問題ではなく、対照の不在):

1. **campaign 内に 1 点しか無い。** digest の「フラグ軸の限界効果」節は BACK_OFF=1 / no_wait=L / WAL=0 の**各 1 水準のみ**を列挙しており、どの軸にもフリップした対照が存在しない。表に見える `1=719,324` `L=719,324` `0=719,324` は同一の 1 点を 3 回書き写したもので、**限界効果ではない** (水準差がゼロ個)。
2. **stock 対照が無い。** digest 自身が `(stock 対照なし — 比は計算不能)` と明記している。faster / slower / tie のいずれも判定できない。
3. **別機体との比較は帰属に使えない。** linux-baremetal の 3 点 (BACKOFF_FIXED=30: 525,721.5 tps / =40: 491,796.5・487,088.5 tps) と本走 719,324 tps の差は、機体差・配線差・campaign 差が全部同じ向きに混ざっており分離できない。**「BACKOFF_FIXED=20 が速い」とは読めない。**

## 本走から言える事実 (帰属ではなく、状態の記述)

- **正しさ:** 469,618 commit / anomalies=0 / verdict=serializable → certified。これは前提であり、性能の議論とは独立。
- **測定品質:** run 内 CV 1.70% は within-run 品質ゲート 2.28% を満たし、`settled=true`。**ただしこれは「1 測定が壊れていない」ことしか言わず、採否 floor (between-run 3.0%, D19) とは別物。**
- **競合の水準:** perf 走の abort_rate 7.75%。skew0.9 / rr50 / threads=4 で「衝突がある regime には居る」ことは言える (0% 近傍なら軸を振っても何も動かないが、そうではない)。これは**次にどの軸を振る価値があるか**の材料にはなるが、どの軸が効いたかの証拠にはならない。

---

# 2. digest 読解上の 2 件の注意 (コードで裏取り済み・critic の本務)

これは親の開示に無かったが、次の一手の設計に直接効くので報告する。

## (a) `latency_ns` は throughput の恒等変換であり、独立な指標ではない

`external/ccbench/common/result.cc:55`:

```cpp
cout << "latency[ns]:\t" << powl(10.0, 9.0) / result * thread_num << endl;
```

直後の行が同じ `result` を `throughput[tps]` として出している。つまり `latency_ns = 1e9 × threads / tps` で、threads 固定なら **throughput の逆数に定数を掛けただけ**。実測でも一致する: `1e9 × 4 / 727,985 = 5,494.6ns` → digest の 5,495ns。

帰結: **本走で観測できる独立な leading indicator は (throughput, abort_rate) の 2 本だけ** (llc_miss_rate と ipc は欠測、latency は throughput に従属)。「throughput は下がったが latency は改善した」といった読み方は**この系では原理的に起こりえない**。次の一手は、この 2 次元で機序が分離できる軸を優先すべき (→ §3)。

## (b) reps が偶数だと、abort_rate / latency は**速い方の rep** から取られる

`orchestrator/calibrator/runner.py:1052-1060`:

```python
throughputs = sorted(result[0] for result in valid)
median = throughputs[len(throughputs) // 2]
rep = min(valid, key=lambda result: abs(result[0] - median))
```

reps=2 では `throughputs[1]` = **上側**が「median」になる。実際、本走の 2 反復は 710,664 と 727,985 で、代表 rep は 727,985 の方 (上の (a) の一致がそれを裏付ける)。一方 headline の `throughput_tps = 719,324` は 2 点の真の中央値 (= 平均) で、**別の量**。

帰結: digest 1 行の中で **throughput と abort_rate/latency の集約が揃っていない**。abort_rate 7.75% は「719,324 tps の点の abort 率」ではなく「727,985 tps の rep の abort 率」。差は小さい可能性が高いが、偶数 reps では**系統的に速い側へ偏る**ので、軸の効果が floor 近傍のときに誤帰属を生む。→ §3 の R0-c で対処を推奨する (実装はしない)。

---

# 3. recommend — 次の一手

優先順に。各項目に「なぜその方向か」を指標名で付ける。

## R0. 比較の土台を先に作る (これ無しでは以後どの iteration も帰属に使えない)

- **R0-a: 同一 campaign・同一機体・同一配線で stock (無改変 silo) を 1 点測る。** 根拠: digest が `stock 対照なし — 比は計算不能` と自己申告している。stock が無い限り、throughput も verify abort 率も「高い/低い」を言う相手が居ない。**これは新しい軸を振るより先に置くべき** — 対照が無いまま variant を増やすと、点は増えるが帰属可能な差はゼロのまま増える (Jitskit §3.5 の停滞そのもの)。
- **R0-b: 配線をこの contrast 系列の間は凍結する。** records=100000 / threads=4 / extime=1 / rr50 / skew0.9 / rmw=false は kickoff 配線であり calibrator 由来ではない (親開示)。**途中で変えると系列内比較まで無効化する。** 飽和点の確認 (規律 4) は別系列として並行に行い、「この系列の絶対値は転移しない」と明記して使う。
- **R0-c: reps を奇数 (>=3) にする。** 根拠は §2(b)。奇数なら代表 rep が真の中央値になり、abort_rate と throughput が同じ rep を指す。reps=2 は CV の自由度が 1 しかなく、within-run 品質ゲート通過 (1.70%) も証拠として弱い。**採否 floor は between-run 3.0% (D19) なので、これ未満の差は何点測っても「差なし」である点は変わらない。**

## R1. BACK_OFF 0 vs 1 を、同配線・同機体で 1 組だけ作る (最優先の軸)

- 理由: **欠測 (llc/ipc) と従属 (latency) を差し引いた観測空間 (throughput, abort_rate) の 2 次元で、機序が一意に読み分けられる唯一の軸**だから。読み分け表:
  - BACK_OFF=0 で abort_rate が**明確に上がり** throughput が下がる → backoff は本当に競合を減らしている (contention 低減が効いている)。
  - BACK_OFF=0 で abort_rate が**ほぼ動かず** throughput が上がる → backoff のコストは「衝突が無くても待つ」純粋な待ち時間。over-throttle。BACK_OFF=1 系列を畳む根拠になる。
  - 両方 floor 内 → この regime (threads=4, abort 7.75%) では backoff 軸は無効。以後この軸に iteration を使わない。
- 現在地の指標: abort_rate 7.75% は「振る価値のある競合水準」。0% 近傍ではないので、上の 3 分岐は実際に分かれうる。

## R2. R1 が「BACK_OFF=1 が支配されていない」と出た場合にのみ、BACKOFF_FIXED を振る

- 水準は現在値 20 を含む対数的に離れた 3 点 (例 5 / 20 / 80) を、**同 campaign 内で**。理由: floor が 3.0% なので、隣接値 (20 vs 30) の微差は検出できない見込みが高い。別機体の 30 vs 40 の差が約 +6.9% だったことは、**「この軸には floor を超える傾きがありうる」という仮説の出所**としては使えるが、本機体の証拠ではない (§1-3)。
- 読み方: throughput が単峰なら sweet spot 探索、abort_rate が単調に下がるのに throughput も下がるなら R1 の「純粋な待ち」側の機序が確定する。

## R3. no-wait 政策 L vs T を、BACK_OFF を R1 の勝ち水準に固定して 1 組

- 理由: L (即 abort) と T (retry) は **abort_rate に逆向きの署名**を出すはずの軸で、2 次元観測でも分離できる。L で abort_rate が上がるのに throughput も上がるなら「早く諦める方が得な regime」、abort_rate が下がるのに throughput が動かないなら「retry の待ちが abort の再実行コストと相殺」。
- 現状は L 固定 (NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0) の 1 点のみで、この軸は**完全に未探索**。

## R4. WAL 0 vs 1 は後回し

- 理由: WAL の機序 (永続化の I/O・memory 帯域・cache 汚染) は本来 **llc_miss_rate / ipc** で読む軸だが、その 2 本が本機体で欠測。(throughput, abort_rate) だけだと「throughput が下がり abort_rate は不変」という弱い署名しか得られず、R1/R3 と同じ署名になりうるので帰属が曖昧になる。perf が使えない間は投資効率が悪い。

## R5. verify 走の abort 率を、シグナルとして継続監視する (閾値判定はしない)

- 本走: verify 15.02% vs perf 7.75% で**約 2 倍**。stock 対照が無いので比は計算できず、**異常とは言わない。** 機序候補は (i) trace-enabled build の観測者効果で critical section が伸び衝突窓が広がる、(ii) verify 走と perf 走の配線差。R0-a の stock を verify 側でも取れば (i)/(ii) の分離に近づく。
- 使い道は正しさ側: **verify の abort 率が将来 0 近傍へ落ちた variant は、certification の証拠力が弱い** (競合経路をほとんど踏まずに serializable と出ている)。これは reject 理由ではないが、certified の重みを読むためのシグナルとして記録する価値がある。**逆向きに「abort が高いから正しさを緩める」方向は当然採らない。**

---

# 4. avoid — 外してよい方向

- **別機体 (linux-baremetal) の絶対値との直接比較。** 719,324 tps を 491,796〜525,721 tps と並べて「速くなった」と読む経路は今後も採らない。使ってよいのは「どの軸に傾きがありそうか」の仮説生成までで、本機体の証拠としては使わない。
- **`latency_ns` を独立指標として扱う探索。** §2(a) の恒等式により情報量ゼロ。「latency が改善した」を throughput と別の所見として数えない。
- **1 点 campaign の「フラグ軸の限界効果」節を効果として読むこと。** 水準が 1 つしか無い軸の平均は、その 1 点の写しである。
- **llc/ipc に依存する仮説の検証に iteration を割くこと** (cache 律速仮説、IPC 低下仮説など)。perf が `status=unavailable / rc=2` の間は検証も棄却もできない。perf が戻ったら再開する棚に置く。
- **floor 未満の差を根拠にした genome 採否。** between-run 3.0% (D19) 未満は「差なし」。`calibrator.stability.compare` の判定に従う。
- (規律 2) **正しさゲートを動かす方向は選択肢に入れない。** 現状 anomalies=0 で certified が取れているので、そもそも性能のために緩める誘因も無い。

---

# 5. uncertainty — データで判断できないこと

1. **llc_miss_rate / ipc は欠測** (perf unavailable, preflight rc=2)。**0 でも「差なし」でもない。** cache 局所性・命令効率に関する機序は本走では一切支持も反証もされない。digest の `—` を「影響なし」と読むのは誤り。
2. **対照ゼロ。** stock も、どの軸のフリップも存在しない。faster/slower/tie の判定は不能で、限界効果は定義されない。
3. **noise floor。** 採否 floor は between-run 3.0%。本走の run 内 CV 1.70% は within-run 品質ゲート (2.28%) 用であって採否には使えない。今後の 2 点比較は 3.0% を超えて初めて差として扱える。floor〜1.5×floor の帯は `near_floor` 相当で cross-run 再現が要る。
4. **機体差。** 別 campaign の 3 点とは機体・配線・時間窓が全て違う。絶対値も、regime (飽和しているか、contention の強さ) も転移しない。
5. **reps=2。** CV の自由度 1。加えて §2(b) の代表 rep 選択が上側へ偏るため、abort_rate 7.75% / latency 5,495ns は headline throughput 719,324 と**同じ rep のものではない**。差が小さければ実害は無いが、floor 近傍の判断には使わない方がよい。
6. **配線が calibrator 由来でない。** records=100000 が cache miss 率の飽和点かどうか未確認 (規律 4)。小さすぎれば many-core 競合が再現されず楽観に、大きすぎれば時間の無駄。この系列の値は**系列内比較専用**として扱うべき。
7. **workload 交互作用は未測定。** skew0.9 / rr50 / rmw=false の 1 点のみ。read-heavy と write-heavy で backoff や no-wait の向きが反転しうることは P2 系で既に知られている型の現象であり、本走からは何も言えない。
8. **verify 15.02% vs perf 7.75% の 2 倍差の帰属不能。** 観測者効果 (trace build) と配線差を分離する材料が無い。異常とも正常とも断定しない。

---

## 参照した file (絶対 path)

- `external/ccbench/common/result.cc` (latency[ns] の定義、§2a)
- `orchestrator/calibrator/runner.py` (代表 rep の選択、§2b)
- `orchestrator/calibrator/benchparse.py` / `model.py` (leading indicator の出所)
- `orchestrator/campaign/pipeline.py` (throughput は nf.median、leading は代表 rep)
- `orchestrator/critic/digest.py` (指標の書式)
- `docs/decisions.md` D19 (between-run floor 3.0%)

---

## 親による検算 (2026-09-16)

critic の §2 は 2 件とも**現物のコードで裏取りできた**。

- (a) `external/ccbench/common/result.cc:52-56` の `displayTps` は
  `result = (total_commit_counts_ + total_batch_commit_counts_) / extime` を求め、
  `latency[ns] = powl(10,9) / result * thread_num`、`throughput[tps] = result` を続けて出す。
  **`latency_ns` は throughput の従属量である。**
- (b) `orchestrator/calibrator/runner.py:1053-1055` は
  `throughputs = sorted(...)` / `median = throughputs[len(throughputs) // 2]` /
  `rep = min(valid, key=lambda r: abs(r[0] - median))` である。
  `reps=2` では `len // 2 == 1` で**上側**が選ばれる。
  本走の 2 反復 710664 / 727985 に対し `1e9 * 4 / 727985 = 5494.6` が
  記録された `latency_ns = 5494.6187` と一致するので、**代表 rep は 727985 側**である。
  一方 `median_tps = 719324.5` は 2 点の真の中央値であり、**別の量**である。

**この 2 件は本 wave では修正していない** (実装面の差分ゼロが不変条件)。次の一手へ送る。
