# 2026-07-16 8b floor protocol 凍結案 — codex 敵対相談 4 本の記録

- 実行: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=repo (基準 64905d6)
- 目的: wave 2 floor protocol 凍結案のプラン骨子 v0 に対する承認提示前の敵対的検証。C-α = 統計設計 / C-β = budget・停止条件・運用 / C-γ = floor driver 実装設計 / C-δ = 世代 field 列挙 + 承認束縛方式
- 並列 4 本を独立コンテキストで実行。本ファイルは prompt と出力の逐語保存 (failures F20 対応: scratchpad にだけ置かない)。所見の real/refuted 裁定と採否は凍結案パッケージ (output/insights/2026-07-16_s8b-floor-protocol-package.md) と worklog に記録する

---

## C-alpha prompt

````markdown
# 敵対的検証依頼 C-α — 8b floor protocol 凍結案の統計設計

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。以下の「私のプラン」を攻撃し、裁定を返せ。忖度不要。気に入られようとするな。所見ゼロでもよいが見逃しは罪。弱い所見には自分で反駁を併記せよ。

## 背景 (検証可能な事実)

- Phase 3 段 8b selector 実験。holdout = rr80 / rr20 (zipf skew 0.9, rmw 0, records=1M, threads=48, extime=3s, reps=5)。正本: `output/s8b-freeze/holdout_freeze.json`、設計: `docs/phase3-8b-descriptor-design.md` §5–§6・§9 (全 8 項発効)
- 判定表の条件 3 は方向付き絶対差比較: `oracle(on) − oracle(off) > floor_<holdout>`。floor は holdout 単位スカラー。off arm = `stock_common` 固定 (§9 項 1)。oracle 集約 = median of medians (§9 項 7)。実装: `orchestrator/campaign/s8b_verdict.py:200-261`
- floor 数値は §8 再凍結 + ユーザー承認事項。今回の私の任務は「凍結案の作成」であり発効ではない
- 前例 1: `orchestrator/campaign/between_run_floor.py` — baseline 1 構成を 8 独立セッション (各 reps=5) で測り session-median の CV を between-run floor とする。fresh back-to-back は cold-boot/温度ドリフト未含の**下限**という注記あり
- 前例 2: S-1 サンプル設計 (`docs/phase3-main-experiment.md:234-345`) — floor 推定標本 N_floor=8 独立セッション/セル (検定標本と分離)、floor_cmp = max(両セル between CV, 3.0%) の純関数、2 時間分離 block、宣言総予算 12h
- 既知の fresh between-run CV 実測 (stock baseline): write-heavy(rr5) 0.67% / balanced(rr50) 1.07% / read-heavy(rr95) 0.11%。wired 保守 floor = 3.0% (D19)。no-backoff 構成の write-heavy abort 率は 82% に達した実績があり、high-abort 域は run 間ドリフトが大きい
- 6 構成 = {p2_2_flag_opt, backoff_fixed_best, sort_best, system_gate, ident_all, stock_common} (§5.1)。rr80/rr20 の各 holdout に variant_binding (nearest-read-ratio-v1) で実体が束縛済み

## 私のプラン (これを攻撃せよ)

1. **対象集合 = 12 セル** (2 holdout × 6 構成すべて)。理由: on は 6 構成のどれでもあり得る。構成間で分散が大きく異なる (high-abort 構成) ため baseline 1 点では on 側分散を過小評価する。oracle 実走と同一 build 経路・同一 binary hash で測る
2. **n = 8 独立セッション/セル、1 セッション = measure_point 1 回 (reps=5)、セッション値 = reps の median**。加えて各セル 1 回の within-run 品質セッション (reps=10) を別途測る (floor 算出には使わない)
3. **時間分離: 2 block × 4 セッション/セル。block 内は 12 セルを決定的 round-robin で interleave** (ランダム化しない。系統ドリフトは round-robin で全セルへ均等に混ざる、という理屈)
4. **算出式 (純関数):**
   - CV_c = stdev(n-1)(8 session medians) / median(8 session medians)
   - floor_rel_h = max( max_{c∈6構成} CV_c , 0.03 )
   - **floor_h (絶対 tps) = floor_rel_h × median(stock_common セルの 8 session medians)** — 判定側が絶対差比較のため stock median を参照点に変換
   - 縮退: どこかのセルで CV 算出不能 (欠測・非有限・median≤0) → floor_h = null → 判定不能 (fail-closed)
5. **cross-block 統合: CV は 2 block 合算 8 セッションから計算。加えて block 別 median の相対差 drift_c = |m_B1 − m_B2| / m_all を記録し、セル分散指標を max(CV_c, drift_c) とする** (保守側)
6. **別 build 分散は floor に含めない** (全セッション同一 binary、hash 束縛)。fresh 下限問題への防御は (i) 2 block 時間分離、(ii) wired 3.0% 下限、の 2 つで行う

## 攻撃してほしい点 (これに限定しない)

- A. 算出式が条件 3 の false-positive を実際に抑えるか。特に: floor は**単一セッション**の分散 (CV) から作るが、判定に使う oracle(on/off) は N_oracle セッション (数値未凍結、8 を想定) の median of medians であり、median の SE は単一セッション分散より小さい。この保守側ギャップは「正直な保守性」として許容できるか、逆に検出力を殺しすぎて §6 が常に不成立になる装置にならないか (§6 は「成立を作る装置ではない」が「構造的に成立不能な装置」も設計ミス)
- B. floor_rel → 絶対値変換の参照点に stock median を使うのは正しいか。on 構成の median が stock より大きい場合、on セル側の絶対分散は stock 参照の絶対 floor を超え得る (CV × 大きい median > CV × stock median)。max_c CV_c で collapse しているから大丈夫、という私の理屈は成立しているか — 反例を構成せよ
- C. 12 セルの過不足。high-abort 構成 (backoff 系が rr20 で abort 高い可能性) のセッション median が不安定な場合、CV_c が発散して floor が使い物にならなくなる経路はないか。その場合の縮退は「正直」か
- D. round-robin 決定的順序で系統ドリフトの混入は本当に均等か。セル数 12 × 4 セッション/block の周期性がドリフト周期と共鳴する攻撃シナリオ
- E. max(CV, drift) の二重保守はやり過ぎ/不足か。drift の分母 m_all の選択は正しいか
- F. within-run 品質セッション (reps=10) の使い道が「floor 算出に使わない」なら、そもそも測る意味と、測った値が後から floor 判定に影響する経路 (HARKing / 事前凍結違反) の遮断
- G. n=8, reps=5, 3.0% 下限などの数値の根拠が「前例踏襲」で足りるか。rr80/rr20 は未実測なので前例 CV は直接使えない — 凍結案として正直な書き方
- H. 私が見落としている統計的・手続き的な穴

## 出力形式

`## 所見` に番号付き (A1, A2, ...) で列挙。各所見: **severity (must-fix / should / note)** / 攻撃シナリオ (具体的に、可能なら数値例) / 根拠 (file:line 可能なら) / 提案。最後に `## 総評` 2-3 行。日本語。
````

## C-alpha output (逐語)

````markdown
## 所見

1. **A1 / must-fix — false-positive 率は制御されていない**

   - **攻撃シナリオ:** 帰無仮説下で on/off の session median が独立な \(N(\mu,\sigma^2)\)、oracle が各 n=8 とする。median 差の標準誤差は近似的に \(0.627\sigma\)。floor を単一セッションの \(\sigma\) とすると閾値は約 1.60 SE にすぎず、片側誤判定率は約 5.5%/holdout。2 holdout の存在量化なら独立近似で約 10.7%。「median の SE が小さいから十分保守的」は成立しない。
   - **根拠:** リポジトリ自身も単一セッション CV は差の分散を \(\sqrt2\) 分過小評価すると認めている。[stability.py:238](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/stability.py:238)。一方、8b は n・検定力を未凍結のままにできない。[phase3-8b-descriptor-design.md:237](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:237)。現行 judge は n≥1 なら受理し、8 を強制しない。[s8b_oracle_judge.py:128](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_judge.py:128)。
   - **提案:** 条件3を単なる「実務的効果量 gate」とし、α 制御を主張しないと明記するか、N_oracle・帰無仮説・族 α を同時凍結し、oracle median 差の片側誤差分位点を floor に組み込む。2 holdout には Bonferroni/max-T 等が必要。
   - **自己反駁:** stable な CV=1%、3% floor、真の差4%、n=8なら同じ正規近似で通過確率は約94%。したがって単一セッション floor が常に検出力を殺すわけではない。問題は「誤判定率が保証される」と扱うことと、後述の全構成 max である。

2. **A2 / must-fix — n=8 の plug-in CV は保守上界ではない**

   - **攻撃シナリオ:** 正規仮定でも n=8 の標本標準偏差の相対 SE は約27%。95%片側上限は概ね \(1.8s\) であり、観測 \(s\) をそのまま floor に使うと最大分散セルを半数程度の確率で過小推定する。最大 CV セルが一つだけなら、6セルの max を取っても救われない。
   - **根拠:** 前例コード自身が n=8 の CV 推定相対 SE を約27%と明記する。[between_run_floor.py:55](/home/SFC/tanab/github/izanagi/orchestrator/campaign/between_run_floor.py:55)。また oracle の推定量は median of medians であり、単一セッションの標準偏差とは別の汎関数である。[s8b_oracle_judge.py:99](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_judge.py:99)。
   - **提案:** raw CV ではなく分散の事前規定した上側信頼限界を使う、n を増やす、または oracle と同じ n の median 差を直接対象にした block-aware resampling を使う。high-abort の非正規性を考えると、n=8 bootstrap だけで保証を謳うのも弱い。

3. **B1 / must-fix — `max CV × stock median` は絶対分散を覆わない**

   - **攻撃シナリオ:** stock median=100k、構成 c の median=200k、CV=4%、他セルも≤4%なら floor=4k。しかし c の絶対 SD は8kで、半分しか覆わない。逆に median=1k、SD=1k の無関係な低速セルは CV=100%となり、stock 基準で floor=100kを生成する。絶対ノイズは1kなのに、安定構成の+10k利得まで消える。
   - **根拠:** CV は各セル自身の位置尺度に対する比である。前例実装も `stdev / mean` と定義する。[analyze.py:212](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/analyze.py:212)。消費側は絶対 tps 差と比較する。[s8b_verdict.py:238](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_verdict.py:238)。
   - **提案:** 3%という効果量基準だけを `0.03 × m_stock` とし、ノイズは絶対単位で別計算する。最低限 `s_c` と `s_stock` から pair の絶対不確実性を作り、scalar が必須ならその pair 値を構成間 max にする。
   - **自己反駁:** `floor_rel` が純粋に「stock に対する最小相対利得」なら stock を掛けるのは正しい。誤りは、各構成の CV をその意味へ無変換で混ぜ、「on 側分散も覆った」と主張する部分である。

4. **B2 / must-fix — 凍結した絶対 floor は後日の尺度変動で相対意味を失う**

   - **攻撃シナリオ:** floor campaign の stock=100kから3kを凍結し、oracle 時に周波数・温度で全 TPS が1.25倍になると、3kは3%ではなく2.4%。ノイズも概ね1.25倍するため anti-conservative になる。逆方向の変動では過剰保守になる。
   - **根拠:** exact binary hash は build 差を除くが、時間・温度ドリフトまでは除かない。既存決定も same-window 値を楽観的下限としている。[decisions.md:327](/home/SFC/tanab/github/izanagi/docs/decisions.md:327)。
   - **提案:** 事前凍結した relative floor を oracle の off median で機械変換するか、それが現行契約上不可なら、oracle stock median が floor campaign の凍結範囲を外れた場合は判定不能にする尺度適合 gate を置く。

5. **C1 / must-fix — 12セルは妥当だが、全セル max は無関係セルによる veto になる**

   - **攻撃シナリオ:** rr20 の未選択 high-abort 構成だけが有限だが巨大な CV を持つと、選択された安定構成対 stock の比較まで不成立になる。さらに巨大な有限 floor は `null` にならず、消費側は「判定不能」でなく `REFUTED` を返す。[s8b_verdict.py:200](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_verdict.py:200)、[s8b_verdict.py:261](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_verdict.py:261)。
   - **提案:** 予測 choice ごとの pair floor 表を全構成について事前計算し、予測後に凍結規則で1値へ射影する。単一 scalar 契約を維持するなら、相対 CV でなく pair の絶対不確実性を max にし、事前定義した感度不成立時は `design-inadequate/indeterminate` とする。観測後の cap は不可。
   - **自己反駁:** 巨大 CV が選択構成自身の真の性質なら肯定主張を拒むのは正直である。問題は、選択されない構成まで同じ veto を持つことと、それを descriptor 不成立の証拠に見せることである。

6. **D1 / must-fix — 固定 round-robin はドリフトを均等化しない**

   - **攻撃シナリオ:** 12セル1周と同周期の温度 governor、監視 daemon、NUMA reclaim があり、throughput が周期内で±4%変動するとする。同じ順序を4周繰り返せば各セルは常に同じ位相を踏み、セル内 CV=0、block drift=0でもセル間に最大8%の偽差が残る。直前セルの abort 負荷による熱・cache carry-over も後続セルへ固定される。
   - **根拠:** 現行 oracle schedule は完全 block ごとに seed 付き shuffle を行う。[s8b_oracle_manifest.py:143](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:143)。S-1 前例も schedule の均衡ランダム化と hash 凍結を要求する。[phase3-main-experiment.md:346](/home/SFC/tanab/github/izanagi/docs/phase3-main-experiment.md:346)。
   - **提案:** 再現可能性は「非ランダム」ではなく事前 seed で確保する。replicate ごとの均衡 permutation、または開始位置を回す Latin/Williams 型順序を生成し、schedule と hash を凍結する。floor と oracle の位置分布も揃える。

7. **E1 / must-fix — `max(CV_c, drift_c)` は比較差の drift を測っていない**

   - **攻撃シナリオ:** block median を次のようにする。

     | | B1 | B2 |
     |---|---:|---:|
     | stock | 100 | 103 |
     | c | 104 | 101 |

     各セルの drift は約3%で floor 下限と同程度だが、比較差は +4 から −2 へ反転し、block 間 swing は6%。B1型の oracle なら +4>約3で条件3が成立し得る。逆に両セルが同率で10%低下する共通 drift は比較差を変えないのに、現式は10% floorを作る。

   - **根拠:** S-1 はまさに比較差の block 間方向一致を別 gate にしている。[phase3-main-experiment.md:321](/home/SFC/tanab/github/izanagi/docs/phase3-main-experiment.md:321)。
   - **提案:** `d_{c,b}=median(c,b)−median(stock,b)` または log-ratio を計算し、符号一致と contrast drift を評価する。scalar には pair contrast の不確実性を集約する。
   - **自己反駁:** `max` なので literal な二重加算ではない。問題は過剰保守そのものより、共通 drift に反応し、構成×時間 interaction を取り逃がすこと。`m_all` の分母を変えるだけでは直らない。

8. **E2 / should — 2 block は時間分離の証明になっていない**

   - **攻撃シナリオ:** block 間隔が未規定なら実質 back-to-back にできる。2点が同じ日周期位相なら drift=0であり、cold boot・日跨ぎ変動は観測されない。2 block は drift 分布を推定せず、一つの差を得るだけである。
   - **根拠:** 既存前例は same-window 測定を明示的に下限とする。[between_run_floor.py:14](/home/SFC/tanab/github/izanagi/orchestrator/campaign/between_run_floor.py:14)。現行 oracle manifest は単一 block を強制しており、floor との時間構造も一致しない。[s8b_oracle_manifest.py:199](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:199)。
   - **提案:** 最低間隔、別 process、boot ID、開始時刻を数値で凍結する。cold boot を含めないなら、その限界を明記する。可能なら3以上の時間窓、または oracle 側にも blockwise再現 gateを置く。

9. **F1 / must-fix — within-run 品質セッションと実際の採否規則が空白**

   - **攻撃シナリオ:** reps=10診断で高CVを見た後に、人間が再測定・除外・floor変更を選べる。一方、実際の reps=5 セッションは部分失敗でも中央値を返し得る。`measure_point` は1 repでも成功すれば進む。[runner.py:238](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/runner.py:238)。oracle 側も非空の `bench_values` を受理するため、2/5と5/5が同じ重みになり得る。[s8b_oracle_judge.py:90](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_judge.py:90)。
   - **根拠:** oracle pipeline はさらに最大 `bench_max_rounds` 回の再測定から低CV roundを採るため、floor の「measure_point 1回」と標本生成過程が一致しない可能性がある。[pipeline.py:236](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:236)。
   - **提案:** floor/oracle とも exact 5/5、`bench_max_rounds=1`、部分 rep は事前規則どおり欠測、を凍結するか、同一の共有測定 primitiveを使う。reps=10を残すなら閾値・発火結果・再測定禁止を事前定義し、値を変えても floor 出力が変わらないテストを置く。用途がないなら削除する。

10. **G1 / must-fix — `stdev/median` は前例の CV ではなく、安全側でもない**

   - **攻撃シナリオ:** session medians が `[1,100,100,100,100,100,100,100]` なら、`s/median=35.0%`、標準的な `s/mean=39.9%`。低側外れ値では依頼案の方が小さく、上側外れ値では逆になるため、一方向の保守性がない。
   - **根拠:** リポジトリの CV 定義は `stdev/mean`。[analyze.py:220](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/analyze.py:220)。同件の現行 handoff も初稿の median 分母を誤りとして mean へ修正済みと記録する。[floor-protocol-wave2.md:22](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-16-floor-protocol-wave2.md:22)。
   - **提案:** 前例継承なら `s/mean` に統一する。median中心の頑健尺度が欲しいなら `MAD/median` 等を別名・別根拠で設計し直す。n=8のS-1根拠は permutation のp値解像度であり、本案にはその検定がない。[phase3-main-experiment.md:278](/home/SFC/tanab/github/izanagi/docs/phase3-main-experiment.md:278)。3%も「rr80/rr20で実証済み」でなく政策的下限と書くべきである。

11. **H1 / must-fix — 現状は凍結可能な完全プロトコルになっていない**

   - **攻撃シナリオ:** N_oracle、floor/oracle の block topology、block間隔、seed、exact rep数、correctness-red の扱い、allowed exclusions、retry/crash/resume、予算、環境・NUMA・clock、測定 round数のどれかを結果閲覧後に選べる。これらは分散と欠測率を直接変える。
   - **根拠:** 正本は n・seed・block・reps・機械故障一覧等を後日再凍結する項目として明記する。[phase3-8b-descriptor-design.md:322](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:322)。現行 freeze も floor/budget が null のままである。[holdout_freeze.json:622](/home/SFC/tanab/github/izanagi/output/s8b-freeze/holdout_freeze.json:622)。
   - **提案:** protocol/schema、schedule/hash、全 run contract、binary byte hash、純関数実装/hash、欠測truth table、総 bench/wall予算を測定前に承認する。`floor_rel` が point 5 で `dispersion` に置換されるのかも、数式一つへ統合する。

12. **H2 / must-fix — floor campaign 自体が oracle 相当の性能データを露出する**

   - **攻撃シナリオ:** 12セル×8の floor campaign は、独立標本とはいえ全構成の順位・on−stock差をほぼそのまま見せる。これを見た後に selector実行、品質判断、除外規則、N_oracle、budget、floor式を変更すれば、標本分離だけではHARKingを防げない。
   - **根拠:** 予測と oracle の分離は規定済みだが、floor データ閲覧との順序は明文化されていない。[phase3-8b-descriptor-design.md:308](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:308)。
   - **提案:** 「protocol・schedule・calculator・budget承認 → 予測封印または構造的blind runner確定 → floor実走 → calculatorによる自動数値化 → provenance照合だけの承認 → oracle」の順を凍結する。floor後の裁量変更は当該 attempt 無効とし、reps=10診断も事前規則以外へ使わない。

## 総評

**裁定は差し戻し。** 12セル、独立floor標本、n=8×reps=5、同一binary hashという骨格は防御可能だが、現式は false-positive を制御せず、構成尺度・周期ドリフト・無関係high-abortセルによって過小・過大の両方へ壊れる。  
最低限、pair絶対差ベースの尺度、均衡ランダム化、N_oracle/α/欠測規則の同時凍結が必要。それをしない場合は「3%を含む記述的効果量gateであり、統計的誤判定率・検定力は未保証」と限定すべきである。````

---

## C-beta prompt

````markdown
# 敵対的検証依頼 C-β — 8b floor campaign の budget 導出・停止条件・運用設計

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。以下の「私のプラン」を攻撃し、裁定を返せ。忖度不要。所見ゼロでもよいが見逃しは罪。弱い所見には自分で反駁を併記せよ。

## 背景 (検証可能な事実)

- Phase 3 段 8b。floor protocol の凍結案を作る (発効はユーザー承認後)。正本: `docs/phase3-8b-descriptor-design.md` §5.2 (探索予算 = 累積ベンチ実時間、B_arm/B_total を発効時に数値凍結、予算不足は未実施 arm を**対称に**判定不能へ)、`output/insights/2026-07-16_s8b-ruling-package.md` 裁定 6 (工数 3 欄・実行計画テンプレート・「budget は floor から自動では出ない」注意)
- 裁定 6 = 択 C 採用済み: env-neutral 共通実装を先行し、v2 数値を束縛する唯一の env-tag は floor 実測開始時にユーザーが確定 (worklog 2026-07-16 (11))。候補: cygnus (linux-baremetal、既存 tag、reuse qualification 要) / Pegasus (新 env-tag、D59 4 条件)
- S-1 前例 (`docs/phase3-main-experiment.md:256-345`): 総予算 12h 宣言・全費用込み計上・残予算を各セッション起動前に検査・不足時は未完走の全比較を対称に判定不能・予備枠は機械故障 retry のみで目的間移転禁止・allowed_excluded_reasons の閉じた列挙・floor campaign 実績 54.8s/セッション (reps=5)・検証相 verify 実測 433.3s/1 verify (extime=3s, trace-enabled)
- T 層 (wave 1 実装済み): 予算台帳は事前一括 reservation・crash 非解放・3 値分離 (`orchestrator/campaign/s8b_budget.py`)。crash 後の再走なし (§9 項 8 択 a) — ただしこれは selector 実験本走の規定
- 計測there の規律: 単独性確認は計測ノード上で pgrep (F3 恒久対応 — 検索パターンは wave 1 で binary path 非依存化済み)、外乱検知 → 破棄・再計測 (failures F3)

## 私のプラン (これを攻撃せよ)

**floor campaign の停止条件・品質ゲート (protocol で事前凍結):**
1. 競合検知 (単独性違反) → 当該セッション無効・再測。再測しても当該セルが n=8 を完走できない → その holdout の floor 未確定 (fail-closed、判定不能へ)
2. rep 全滅 (throughput 非有限) のセッションは無効。**abort rate による閾値除外はしない** (観測値を見た選択的除外を避ける。high-abort の分散は floor に正直に乗せる)
3. allowed_excluded_reasons の閉じた列挙 = {competing_process, launch_failure, nonfinite_output} のみ。理由コードなしの除外は不可
4. wall-time 上限超過見込み → 未完セルを**対称に**未確定へ (途中成績で止めない)

**budget 導出 (式を protocol に凍結、数値は再凍結時に充填):**
5. B_floor_bench = 12 セル × 8 sess × 5 reps × 3s + 12 セル × 1 within sess × 10 reps × 3s = 1800s (bench 実時間)
6. wall 外挿 = S-1 実績 54.8s/セッション → 12×8×54.8s + 12×~110s ≈ 1.8–2.0h (ロード・プロセス起動込み)
7. oracle 本走 B_oracle = 12 セル × N_oracle × 54.8s (N_oracle は再凍結項目、8 を想定) ≈ 1.5h
8. verify (trace-enabled 別ビルド別 run) = 12 (構成×holdout) × ~433s ≈ 1.5h — ただし rr80/rr20 は未実測なので pilot で校正
9. **full-pipeline pilot**: 既知 workload 1 セル (rr50 など、holdout を汚さない) で build→verify→bench→報告の wall/bench 比を実測し B_total を校正。pilot の wall も台帳に計上
10. 総額 = floor + oracle + verify + pilot + 機械故障予備 (使途を閉じる)。floor campaign 自体の予算は §5.2 の実験予算とは別枠だが、同じ台帳規律 (monotonic wall 累積・起動前検査・対称打ち切り) を適用

**実測の前提 (実行計画テンプレート充填、env はユーザー確定待ち):**
11. revision = committed HEAD のみ・未 commit 作業木で走らせない / preflight = 計測ノード上の単独性確認 + calibration 動作点照合 + trace-disabled build 確認 / artifact = output/env/<env-tag>/calibration/ へ JSON+md / freeze v2 への数値充填は §8 再凍結の別 commit / 実行責任者・開始時刻 = ユーザー側

## 攻撃してほしい点 (これに限定しない)

- B1. 品質ゲート 1–4 に「観測値を見た選択的打ち切り」が紛れ込む経路。特に「再測」は何回まで許すのか無限 retry は时间を食い潰す — retry 上限を置くとそれ自体が選択になるか
- B2. allowed_excluded_reasons の列挙の過不足 (S-1 や wave 1 の R6/rc 契約 — `orchestrator/campaign/s8b_run_marker.py`, `s8b_prediction_runner.py` — と整合するか)
- B3. budget 式の漏れ: build 時間 (6 構成 × 2 holdout のビルド)、within セッション、preflight、pilot、正しさゲート (verify) の trace-enabled build 時間。§5.2「予算台帳は両者を合算計上してよい」との整合
- B4. floor campaign の予算を実験予算 (B_total_seconds) と別枠にするのは §5.2 の予算契約と矛盾しないか。台帳 (T 層 reservation) との関係を凍結案でどう書くべきか
- B5. 54.8s/セッション・433s/verify は cygnus 実測。env 未確定 (択 C) の下でこれらを外挿に使う正直な書き方 (Pegasus なら別の値になる)。pilot 校正の設計はこれを救うか
- B6. crash 時の扱い: floor campaign は selector 本走ではないので §9 項 8 (crash 再走なし) の適用外と私は解釈した — この解釈の穴。floor campaign が crash した場合の再開 (途中セルからの resume) を許すか、全 campaign やり直しか
- B7. 実行計画テンプレートの残りの穴 (私が埋め忘れているもの)
- B8. その他、運用が「盛る」方向に流れる経路

## 出力形式

`## 所見` に番号付き (B1', B2', ...) で列挙。各所見: **severity (must-fix / should / note)** / 攻撃シナリオ / 根拠 (file:line 可能なら) / 提案。最後に `## 総評` 2-3 行。日本語。
````

## C-beta output (逐語)

````markdown
## 所見

1. **B1' — severity: must-fix** / **攻撃シナリオ:** 「再測」の上限・発火条件が未凍結である。既存 `remeasure_until_stable` を流用すると、CV を見て停止し、複数 round 中の最小 CV を採るため、floor を人工的に縮められる。また「wall 超過見込み」も予測方式が未定義で、実行者裁量になる。**根拠:** [`stability.py:58–90`](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/stability.py:58)、S-1 は理由を限定し `retry ≤ 2/session` を事前固定していた [`phase3-main-experiment.md:353–356`](/home/SFC/tanab/github/izanagi/docs/phase3-main-experiment.md:353)。**提案:** floor 標本は `max_rounds=1`。別途 `K_floor` を観測前に固定し、理由コードによる自動発火・全セル同一・first-authorized-valid のみ採用・全 attempt 課金とする。固定上限自体は選択ではない。結果を見る前に同じ規則で機械発火する限り、むしろ選択経路を閉じる。

2. **B2' — severity: must-fix** / **攻撃シナリオ:** 「全 rep 非有限だけ無効」では、2/5 成功や非ゼロ終了後の部分出力が完全な 5-rep session と同じ重みで入る。現行 `measure_point` は rep 例外を飛ばして残りを採用し、`run_once` は metrics があれば process rc を検査しない [`runner.py:187–202`](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/runner.py:187)、[`runner.py:238–276`](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/runner.py:238)。この穴は v2 設計素材でも明示済みである [`s8b-freeze-v2-design-material.md:178–185`](/home/SFC/tanab/github/izanagi/output/insights/2026-07-16_s8b-freeze-v2-design-material.md:178)。**提案:** session valid を「expected reps と完全一致、全 rep rc=0、throughput 有限、必要メトリクス完全」と逐語凍結する。部分成功・平均ゼロ・actual_extime 逸脱の伝播も固定し、欠測を黙って縮約しない。

3. **B3' — severity: must-fix** / **攻撃シナリオ:** `{competing_process, launch_failure, nonfinite_output}` は `excluded_reason` の意味領域を混同している。`excluded_reason` は機械故障専用である [`phase3-8b-descriptor-design.md:143–150`](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:143)。preflight の競合は「未起動」、非有限値は「測定不成立」、`launch_failure` は deterministic build/config error や correctness-red まで洗浄できる広すぎる語である。correctness-red への excluded 指定は現行 report も protocol violation にする [`s8b_oracle_report.py:323–335`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_report.py:323)。**提案:** `{reason code, 発生 stage, 必須証拠, retry 可否, bench/wall 課金, 終端伝播}` の閉じた表に分ける。correctness-red・identity/config/build の恒久不良は吸収的失格、preflight refusal は attempt 外、部分/nonfinite output は invalid attempt とする。現行 manifest は任意 identifier を受けるだけなので、名前を列挙するだけでは機械契約にならない [`s8b_oracle_manifest.py:497–505`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:497)。

4. **B4' — severity: must-fix** / **攻撃シナリオ:** `1800s` は `extime` の名目和としては正しいが、「累積ベンチ実時間」ではない。現行 T 層も `extime×reps×max_rounds` で予約する一方 [`s8b_oracle_driver.py:539–549`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:539)、精算値は process 起動等を含む実測 `bench_wall_s` である [`s8b_oracle_driver.py:366–380`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:366)。成功 run でも予約枠超過になり得る。retry・失敗済み rep・`max_rounds` も 1800 に入っていない。**提案:** budget 単位を、(a) nominal extime とするか、(b) monotonic bench wall とするか選び直す。§5.2 の文言どおりなら (b) とし、per-rep timeout を使った最大 wall envelope を予約する。oracle は少なくとも  
   `12 × N_oracle × reps × extime × max_rounds`、floor は全 preauthorized attempt を含む式にする。さらに §5.2 が要求する `B_arm_seconds` と holdout 枠も明記する [`phase3-8b-descriptor-design.md:209–212`](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:209)。固定 selector で arm の bench がゼロなら、`B_arm=0 + oracle_shared` と明示して承認対象にすべきで、欠落は不可。

5. **B5' — severity: must-fix** / **攻撃シナリオ:** `54.8s/session` と `12×433s` の組合せは現行 pipeline と両立しない。54.8 秒の S-1 floor session は **legacy verify + bench 1 round** である [`s1_direct_comparison.py:1–7`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s1_direct_comparison.py:1)。現行 8b oracle は各 trial で legacy + S2 を実行する [`s8b_oracle_driver.py:631–648`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:631)。`N_oracle=8` なら 12 ではなく 96 S2 verify であり、433 秒を単純適用しただけでも verifier 単体約 11.6h になる。さらに pipeline は trace/perf の両 build を作り [`pipeline.py:407–424`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:407)、holdout ごとに実装 binding が異なるため最大 12×2 cold build である [`phase3-8b-descriptor-design.md:298–301`](/home/SFC/tanab/github/izanagi/docs/phase3-8b-descriptor-design.md:298)。**提案:** 「S2 を trial ごとに96回」か「exact build/source/config hash ごとに1回認証し、証明書を全 bench session が hard-consume」のどちらかを凍結する。後者なら driver/report の certificate reuse 実装が必要。一セルの wall/bench 比では固定費を推定できないため、build・legacy・S2・verifier・bench・cleanup を分解した pilot にする。

6. **B6' — severity: must-fix** / **攻撃シナリオ:** floor 予算を別枠にすること自体は§5.2への直ちの違反ではない。しかし「同じ台帳規律」だけでは scope が定まらず、pilot/floor を消化後に v2 の `B_total` を決めるという遡及予算になる。現行 `s8b_budget.py` は明示的に oracle 用で、上限は total/per-holdout の bench のみ。wall は完了 entry に記録するだけで上限検査がない [`s8b_budget.py:1–11`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_budget.py:1)、[`s8b_budget.py:25–40`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_budget.py:25)。crash・preflight・pilot・未完 build の wall は消え得る。**提案:** 数値を別名で三層化する。

   - floor 開始前に `B_pilot_wall`、`B_floor_bench`、`B_floor_wall` を凍結
   - v2 には `B_oracle_bench`、per-holdout、`B_arm`
   - 全 build/verify/bench/timeout/pilot を覆う親 `B_campaign_wall` を置き、子枠間移転禁止

   S-1 同様、親 wall cap は全費用込みにする [`phase3-main-experiment.md:290–297`](/home/SFC/tanab/github/izanagi/docs/phase3-main-experiment.md:290)。別枠を採るならこの namespace と親子関係を逐語化すれば矛盾は解消できる。

7. **B7' — severity: must-fix** / **攻撃シナリオ:** 12 セルを測る理由と `floor_<holdout>` への縮約式がない。全6構成の最大 CV、on/off 予測対だけ、within CV も含める、のどれでも結論が変わる。裁定6自身が対象集合・比較対の解釈を未確定としている [`s8b-ruling-package.md:304–314`](/home/SFC/tanab/github/izanagi/output/insights/2026-07-16_s8b-ruling-package.md:304)。また n=8 の 2×4 block、均衡 schedule、別 process、cross-block 統合がプランにない。back-to-back 8本なら既知の「fresh 下限」に戻る [`s8b-ruling-package.md:324–335`](/home/SFC/tanab/github/izanagi/output/insights/2026-07-16_s8b-ruling-package.md:324)。**提案:** 実測前に、対象構成集合、within 10-rep の用途、CV の分母・境界、holdout scalar の純関数、2 block×4、schedule seed/hash、process 分離、block 統合を凍結する。必要セルが一つでも n=8 未達なら、理由を問わず当該 **holdout 全体**の floor 未確定とする。T 層の単一 block 制約は oracle 用なので、floor の二 block は別 driver + 親台帳で表現する。

8. **B8' — severity: must-fix** / **攻撃シナリオ:** 「§9 項8は floor に直接適用されない」という解釈は妥当だが、そこから自由 resume は導けない。oracle marker は freeze-wide 再走拒否専用 [`s8b_run_marker.py:2–13`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_run_marker.py:2)、prediction は別の at-most-once 契約である [`s8b_prediction_runner.py:2–16`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_prediction_runner.py:2)。floor crash 後に campaign 全体や完了セルを再走すれば、複数 floor 標本から都合のよい一組を選べる。**提案:** floor 専用 append-only attempt registry を置く。完了 session は不変、resume は immutable schedule の次の未着手 session または事前割当 retry slot のみ、途中 session は crash terminal + 全予約額課金。registry がないなら crash は当該 holdout floor 未確定。campaign 全やり直しは不可。

9. **B9' — severity: should** / **攻撃シナリオ:** cygnus の 54.8/433 を Pegasus の凍結値へ流用できる。433 秒は `linux-baremetal` の rr95×g_rl 一点である [`s1_verify_extime.md:3–17`](/home/SFC/tanab/github/izanagi/output/env/linux-baremetal/calibration/s1_verify_extime.md:3)。D59 は Pegasus に専用 tag・再 calibration・binding・module/toolchain/job script 追跡を要求する [`pegasus-runbook.md:245–260`](/home/SFC/tanab/github/izanagi/docs/pegasus-runbook.md:245)。**提案:** 両値は「cygnus planning prior、非拘束」と明記する。pilot は env-tag 確定と D59 qualification 後、同一 node class/toolchain/pin/binding で実施する。cygnus なら reuse qualification、Pegasus なら専用 tag と再校正が先。**反駁:** 参考値として工数の桁を見る用途まで禁じる必要はなく、凍結値への転用だけを禁止すればよい。

10. **B10' — severity: must-fix** / **攻撃シナリオ:** binary path 非依存化は済んだが、pgrep 自体の失敗が「競合なし」に化ける。現行 helper は `OSError` 等で空配列を返し、pgrep rc も検査しない [`runner.py:107–144`](/home/SFC/tanab/github/izanagi/orchestrator/calibrator/runner.py:107)。さらに確認は bench 前だけなので、session 中に出現・消滅する競合を捕れない。`settled=False` も現行 pipeline は記録するだけで採用する [`pipeline.py:281–297`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/pipeline.py:281)。**提案:** pgrep rc=1 のみ「該当なし」、起動不能・rc>1・parse不能は fatal。pre/post または連続 monitor の cadence、load/frequency/actual_extime の機械 gate、`settled=False` の invalid 化を凍結し、raw probe を artifact に残す。

11. **B11' — severity: must-fix** / **攻撃シナリオ:** 実行順と artifact 世代が未固定である。floor を見てから selector の model/prompt/effort や予測実行時期を決める、pilot cache を本走へ持ち込む、再走 JSON を固定名へ上書きする、という経路が残る。既存 floor driver は固定 path を通常 `"w"` で上書きする [`between_run_floor.py:111–119`](/home/SFC/tanab/github/izanagi/orchestrator/campaign/between_run_floor.py:111)。**提案:** selector prediction とその provider/model/prompt/parser basis を最初の holdout 計測前に封印する。順序を `prediction seal → env qualification → known-workload pilot → floor → v2 refreeze → oracle` に固定する。raw attempt は世代別 immutable path、final JSON/md はその hash 射影とし、上書き禁止。revision gate は「tracked source/input と submodule が pin に一致、campaign 所有 output のみ変更可」とする。単なる「作業木 clean」では、最初の WAL 出力後に自己矛盾する。

12. **B12' — severity: note** / **攻撃シナリオ:** high-abort 構成が大きな CV を出し floor を膨らませる。**反駁:** transaction abort rate は正当な workload 結果であり、観測後の閾値除外の方が明白な cherry-pick である。「abort rate 閾値なし」は維持してよい。**提案:** abort rate を全件報告し、process failure・partial rep・correctness-red と型分離する。病的構成が floor を支配する問題は B7' の対象集合・縮約式で解決し、abort 閾値で隠さない。

## 総評

**裁定: 現状のまま凍結不可。** 1800 秒の名目算術、abort-rate 非除外、択C下での再校正方針は妥当だが、rep/retry 契約、S2 verify 回数、予算単位・scope、floor 純関数、crash registry が未閉鎖である。  
特に B2'・B4'・B5' は単なる文言不足でなく、現行実装をそのまま使うと予算超過または選択的標本化が実際に発火する。````

---

## C-gamma prompt

````markdown
# 敵対的検証依頼 C-γ — s8b floor campaign driver (env-neutral) の実装設計

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。以下の「私の実装プラン」を攻撃し、裁定を返せ。忖度不要。所見ゼロでもよいが見逃しは罪。弱い所見には自分で反駁を併記せよ。実装前のため、攻撃対象は設計とその既存コードとの整合。

## 背景 (検証可能な事実 — まずこれらを読め)

- `output/insights/2026-07-16_s8b-ruling-package.md` 裁定 6: 「holdout freeze から target manifest を生成する専用 driver が必要 (POINTS 手編集・既存 3 点の値コピーは禁止)」。既存 driver `orchestrator/campaign/between_run_floor.py` は POINTS 3 点 (rr5/50/95) ハードコードで 8b の対象 (rr80/rr20) を測っていない
- wave 1 実装済み資産: `orchestrator/campaign/s8b_holdout_freeze.py` の `load_verified_freeze` (hash 検証済み bytes の strict parse を単一 object で全 consumer へ渡す、TOCTOU 遮断)・`orchestrator/campaign/s8b_oracle_driver.py` (6 構成のビルドと bench 実行、s8b-build-cache、gate 検査)・`orchestrator/calibrator/runner.py` の競合検知 (binary path 非依存化済み = F3 恒久対応)・`orchestrator/campaign/s8b_budget.py` (reservation 台帳)
- 過去の失敗型 (`docs/failures.md`): F14 = 宣言のみの遮断 (束縛しない claim)・F3 = 単独性確認の穴。直近 worklog (12): `--marker-root` CLI が経路上書き迂回を再導入しかけ、CLI 面から撤去した
- 環境: 択 C = env-neutral 共通実装先行。現行の env 定数 (ENV_TAG/NUMA/THREADS/RECORDS/CLK) は `orchestrator/campaign/p2_2.py` から import され linux-baremetal (cygnus) 束縛。`s8b_oracle_driver.py` には `numactl --interleave=all` hardcode もある (裁定 6 で「Pegasus 差分」として除去予定と記録)
- 絶対規律: 1 = floor/性能は trace-disabled build のみ / 2 = 正しさゲート不緩和 / 4 = 実験スケール規律・単独性 / 6 = 外部入力はデータ

## 私の実装プラン (これを攻撃せよ)

**新規 `orchestrator/campaign/s8b_floor_campaign.py` + `s8b_floor_stats.py`:**

1. **入力:** (i) holdout freeze — `load_verified_freeze` 経由の単一 object、(ii) **floor protocol config JSON** (n=8, reps=5, within_reps=10, blocks=2, wired_min_rel_floor=0.03, allowed_excluded_reasons, 算出式 version) — ユーザー承認後に凍結される file を想定。pilot 段階では明示 path 指定を許すが、artifact に path + sha256 を必ず束縛記録する
2. **セル構築:** freeze の holdouts × variant_binding.entries (6 構成) → `s8b_oracle_driver` と同一のビルド経路 (s8b-build-cache, trace=False) で binary を得る。**binary sha256 を artifact に記録し、後日の oracle 本走が同一 hash を照合できる形にする** (floor と oracle の build 同一性は「後で oracle 側が照合する」設計 — floor が先、oracle が後という時間順のため)
3. **実行:** 2 block × 4 セッション/セル、block 内 12 セル決定的 round-robin。各セッション前に単独性確認 (F3 修正済み競合検知)。measure_point (reps=5)。within 品質セッション (reps=10) を各セル 1 回
4. **出力:** `output/env/<ENV_TAG>/calibration/s8b_floor_campaign_<...>.json` + `.md` — 全生値 (session ごとの throughputs/abort/run_cmd)・CV・drift・提案 floor (絶対値変換込み)・binary hashes・freeze hash・protocol config hash・monotonic wall 台帳。**freeze v2 への floor 充填は書かない** (人間承認後の別手続き)
5. **算出:** `s8b_floor_stats.py` に純関数 (session medians → CV_c, drift_c, floor_rel, floor_abs)。golden テストベクトル (手計算) で固定
6. **env:** ENV_TAG 等は `s8b_oracle_driver` と同じソース (p2_2 定数) から取る。**CLI に env・経路・数値の上書き面を作らない** (--marker-root の教訓)。env-neutral 化は「Pegasus 対応時に env contract として抽象化する」と凍結案に明記するにとどめ、今回は cygnus 定数のまま実装 (ただし artifact に env_tag を記録し、oracle 側 gate が freeze v2 の env_tag と実行環境の一致を検査する将来形を壊さない)
7. **テスト:** fixture freeze → manifest 決定性 / 算出式 golden / 縮退 fail-closed (欠測→null) / 競合検知→セッション無効→セル未確定 / rr80・rr20 が freeze から来る (POINTS 非依存) / protocol config 欠落・hash 不一致→起動拒否 / 既存 3 点の値コピー検出 (するべき?)

## 攻撃してほしい点 (これに限定しない)

- G1. freeze → manifest → 計測 → artifact の束縛連鎖に F14 型の穴 (どこかで自己申告値・未検証 path・再読込が紛れる) はないか。実在コードの行を指して指摘せよ
- G2. protocol config を「pilot では任意 path、本走では凍結 file」とする二相設計は、本走で pilot 用の緩い config を掴む混同経路を作らないか。機械的にどう区別すべきか (承認束縛は §8 裁定待ちという制約の下で)
- G3. binary hash の「後日 oracle が照合」は実効性があるか — oracle driver 側に照合実装がない現状で、凍結案・実装のどちらに何を置けば恒真でない保証になるか
- G4. p2_2 定数依存のまま実装して env-neutral (択 C) と言えるか。逆に env 抽象化を今やるのは過剰設計 (「段階導入・盛らない」違反) か。artifact の env_tag 記録だけで将来の Pegasus 対応と D59 (env-tag 混合禁止) に足りるか
- G5. `s8b_oracle_driver` のビルド・bench 経路の再利用は具体的に何を import/共有すべきか。コピペ実装 (drift する二重実装) と、oracle driver の関数を floor が呼ぶ (密結合) のどちらの害が大きいか — 実コードを読んで判定せよ
- G6. 単独性確認・NUMA・スレッド固定まわりで between_run_floor.py と s8b_oracle_driver.py の間に既に流儀の差があるなら、floor campaign はどちらに揃えるべきか
- G7. テスト列挙の過不足。特に「凍結案の算出式」と「実装の算出式」の同一性をどう機械保証するか (protocol config の formula version と純関数実装の対応)
- G8. スケジューラ環境 (Pegasus) で将来走らせる場合に壊れる暗黙前提 (ノード専有・pgrep 可視性・ジョブ時間上限で block 分離が壊れる等) — 凍結案に書くべき将来制約
- G9. その他、実装が「動くが嘘をつく」方向に流れる経路

## 出力形式

`## 所見` に番号付き (G1', G2', ...) で列挙。各所見: **severity (must-fix / should / note)** / 攻撃シナリオ / 根拠 (file:line 必須 — 実在コードを読んで指せ) / 提案。最後に `## 総評` 2-3 行。日本語。
````

## C-gamma output (逐語)

````markdown
## 所見

1. **G1' — must-fix: freeze は現状「検証済み単一 object」になっておらず、そもそも現物が検証不合格**

   **攻撃シナリオ:** floor driver が `load_verified_freeze(path)` を呼ぶだけなら、攻撃者は任意の freeze を渡せる。`expected_hash` は省略可能で、v1 の意味検証では同じ path を再読込するため、hash 検証後の差し替えも理論上可能である。加えて、現在の freeze は design source hash が不一致なので、本走を正しく fail-closed すると起動できない。

   **根拠:** `load_verified_freeze` は計画記載の `s8b_holdout_freeze.py` ではなく `orchestrator/campaign/s8b_oracle_driver.py:90-128` にあり、`expected_hash=None` を許す。v1 gate は `orchestrator/campaign/s8b_oracle_driver.py:136-178` から `orchestrator/campaign/s8b_holdout_freeze.py:761-773` を呼び、path を再読込する。現在の source verifier は作業木の現物を照合する `orchestrator/campaign/s8b_holdout_freeze.py:573-595`。worklog にも不一致が記録されている `docs/worklog.md:935-940`。実際に現物の `verify` は design source sha256 mismatch で rc=1 となる。

   **提案:** 本走の入力は必須の承認済み expected hash から開始し、raw bytes を一度だけ読み、duplicate key を拒否して strict parseし、その同じ object に `verify_document` 相当の意味検証をかけること。返却値も mutable `dict` のままにしない。現 freeze の hash 不一致は黙認せず、承認された refreeze または承認済み historical blob への束縛が完了するまで本走を拒否する。

2. **G2' — must-fix: freeze 以外の protocol・manifest・schedule に同じ TOCTOU/F14 穴が残る**

   **攻撃シナリオ:** protocol の hash を最初に記録しても、セル構築や実行時に path を再読込すれば、検証した bytes と実行した内容が分離する。manifest を単なる中間データとして再生成すると、最終 artifact に記載された対象集合と実際の実行順・実行セルも独立に差し替えられる。

   **根拠:** 現 oracle は manifest を検証した後に別途 `_load_json_object` する `orchestrator/campaign/s8b_oracle_driver.py:199-222`。さらに run 経路でも `verify_manifest` を再度呼ぶ `orchestrator/campaign/s8b_oracle_driver.py:493-515`。`verify_manifest` 自身も path を読む `orchestrator/campaign/s8b_oracle_manifest.py:586-673`。この既存経路を「同一経路」として流用すると穴も継承する。F14 の失敗定義は `docs/failures.md:125-133`。

   **提案:** `VerifiedProtocol` と `VerifiedFloorManifest` を raw bytes、full sha256、strictly parsed immutable object の組として用意する。manifest は全セル、block、session、seed、順序を確定した create-only artifact とし、各 session record に manifest hash と session ID を束縛する。最終 JSON/MD は manifest と後述 WAL の検証済み projection とし、path の再読込を実行判断に使わない。

3. **G3' — must-fix: pilot の任意 path と本走を hash/path 記録だけで区別するのは承認の自己申告**

   **攻撃シナリオ:** pilot 用の緩い config を「hash は記録済み」として本走 artifact に流用できる。同一 schema・同一出力先なら、後から見ても ratified protocol か pilot か判別できない。hash は同一 bytes の証明であって、承認済みであることの証明ではない。

   **根拠:** approval record だけでは F14 になるとの設計判断が `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:150-169` にある。protocol、reps、block、allowed reasons 等は refreeze 対象 `output/insights/2026-07-16_s8b-ruling-package.md:368-369`。承認束縛の方式は未裁定 `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:203-213`。

   **提案:** pilot と official を異なる schema ID・名前空間・出力ディレクトリに分離し、pilot artifact に機械判定可能な `eligible_for_refreeze: false` を固定する。本走 mode は CLI の config path を受けず、固定された承認 binding が未実装の間は常に拒否する。§8 裁定後に official protocol を作り直し、その protocol で再計測する。pilot artifact の昇格は禁止する。

4. **G4' — must-fix: binary hash の「後日照合」は現状では恒真でない将来 claim**

   **攻撃シナリオ:** floor は hash A を記録するが、oracle は hash B の binary を実行しても何も拒否しない。「後で照合予定」のまま refreeze されれば、同一 binary 保証があるように見える artifact だけが残る。

   **根拠:** oracle binding schema に binary hash はない `orchestrator/campaign/s8b_oracle_manifest.py:20-39,349-399`。`BuildResult.bin_hash` は full SHA-256 ではなく16文字への切詰め `orchestrator/campaign/buildcache.py:51-68`。oracle report は build 完了数を数えるだけで hash 同一性を検証しない `orchestrator/campaign/s8b_oracle_report.py:397-419`。

   **提案:** floor artifact に `(holdout_id, config_id, binding_sha256, full_binary_sha256)` を記録し、freeze v2 はその artifact path+hash を束縛する。同じ変更系列で oracle manifest に expected full hashes を取り込み、oracle driver が bench 開始前に実 binary を照合して不一致なら拒否し、report verifier も再検証すること。oracle 側を同時に実装しないなら、凍結案ではこの保証を削除して未実装 prerequisite と明記する。

   **反駁:** source token と build recipe の束縛で十分、binary 同一性は強すぎるという立場は成立する。しかし計画が明示的に「同一 hash」を保証すると言う以上、consumer 不在の claim は許容できない。

5. **G5' — must-fix: p2_2 定数依存の実行物を env-neutral と呼ぶことはできない**

   **攻撃シナリオ:** Pegasus で driver を起動すると、artifact は linux-baremetal の env tag、48 threads、1M records、CLK1800、`numactl --interleave=all` を事実上持ち込む。env tag を記録しただけでは、実機環境との一致は証明されない。さらに build cache key に環境・compiler version・architecture がないため、共有出力では他環境の binary を再利用し得る。

   **根拠:** cygnus 定数は `orchestrator/campaign/p2_2.py:39-47`、oracle の NUMA hardcode は `orchestrator/campaign/s8b_oracle_driver.py:33-36`。manifest の env 検証は非空 identifier 程度 `orchestrator/campaign/s8b_oracle_manifest.py:293-306`。build key は env、architecture、compiler version/module fingerprint を含まない `orchestrator/campaign/buildcache.py:34-48`。裁定自体が driver env contract 抽出と NUMA hardcode 除去を共通前提としている `output/insights/2026-07-16_s8b-ruling-package.md:320-322`。D59 の環境採用条件は tag 以外にも calibration、隔離、toolchain/job provenance を要求する `docs/decisions.md:2282-2297`。

   **提案:** 大規模な汎用化は不要だが、純粋な campaign engine と小さな `ExecutionEnvironmentContract` を今分離すること。contract は env tag、records、threads、clock policy、NUMA/affinity command、calibration binding、isolation policy、toolchain fingerprint を持ち、未登録環境は本走拒否とする。cache も env/contract hash で分離する。Pegasus の具体値は D59 採用時まで追加しない。

   **反駁:** Pegasus adapter 全体を今作るのは過剰設計である。しかし狭い contract 抽出は裁定 6 の明示 prerequisite であり、後回しにすると今回の driver 自体が cygnus 専用品になる。

6. **G6' — must-fix: 再利用境界が未定義。oracle driver 丸ごとの呼出しもコピペも不適切**

   **攻撃シナリオ:** oracle driver をそのまま呼ぶと、floor/budget が未充填の freeze を gate が拒否し、oracle 固有の一 block topology や budget/marker 契約まで持ち込む。逆に private helper をコピペすると、binding identity、source token、build cache、trace 設定が将来 drift する。`prepare_cell` を素直に使うだけなら s1 cache を参照する危険もある。

   **根拠:** oracle gate は v1 の floor/budget null を特別扱いし、v2 manifest builder は非 null floor/budget を要求する `orchestrator/campaign/s8b_oracle_driver.py:136-178`、`orchestrator/campaign/s8b_oracle_manifest.py:471-547`。materialization は private helper 群 `orchestrator/campaign/s8b_oracle_driver.py:227-275`。`prepare_cell` は `output/s1-build-cache` を返す `orchestrator/campaign/s1_direct_comparison.py:466-540` ため、oracle は後から cache root を差し替えている `orchestrator/campaign/s8b_oracle_driver.py:604-648`。二重実装 drift は既知の失敗型 `docs/failures.md:32-34`。

   **提案:** 公開された小さな共通モジュールへ、variant binding 検証、cell materialization、binding identity、trace-disabled perf build を抽出し、oracle と floor の双方をその consumer にする。floor は oracle の gate、budget、marker、schedule を呼ばない。全12セルを計測開始前に build・hash確定し、途中 rebuild を禁止する。長期的にはコピペ drift の害が大きいが、oracle orchestration 全体への密結合も現在の依存循環を作る。

7. **G7' — must-fix: 単独性・settle は現在 fail-closed でなく、計画の「各 session 前確認」には check/run race がある**

   **攻撃シナリオ:** `pgrep` 自体が失敗すると「競合なし」と判定される。確認直後に別 process が起動しても session は進む。settle timeout も記録だけされ、値は採用される。競合 session だけを無効化して残りを集計すれば、block の時間構造を壊したまま好都合なセルだけ再試行できる。

   **根拠:** pgrep 例外を空集合として扱う `orchestrator/calibrator/runner.py:107-144`。この fail-open はテストでも固定されている `orchestrator/tests/test_calibrator.py:479-490`。settle timeout は `settled=False` を返すだけ `orchestrator/calibrator/runner.py:38-57`、bench はそのまま実行・採用する `orchestrator/calibrator/pipeline.py:241-290`。既存 floor driver は `bench_lock` を取らず、session 間 pgrep のみ `orchestrator/campaign/between_run_floor.py:69-91`。一方 oracle pipeline は lock 内で pgrep と計測を行う `orchestrator/calibrator/pipeline.py:241-260`。F3 の原則は `docs/failures.md:36-44`、block 単位の discard/requeue 要求は `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:409-429`。

   **提案:** lock取得 → pgrep 能力/return code 検証 → 競合確認 → settle/load/frequency確認 → session全体 → 事後確認、を一つの臨界区間にする。pgrep 不可視・実行失敗・`settled=False` は本走拒否または protocol で固定した block 全体の discard/requeue とする。再試行上限と再配置規則も protocol に凍結する。基本形は oracle 側に寄せるべきだが、NUMA・affinity・lock scope は G5' の環境 contract に委ねる。

8. **G8' — must-fix: 12セルの統計から verdict が要求する「holdoutごと1個の絶対 floor」への写像が未定義**

   **攻撃シナリオ:** 実装者が6構成のうち都合のよい CV、baseline、block、絶対値変換基準を選べる。`drift` を表示するだけで floor に反映しない実装も計画上は通る。その結果、計算は再現可能でも判断境界を恣意的に下げられる。

   **根拠:** verdict は `on_median - off_median > floor` という絶対 TPS scalar を使う `orchestrator/campaign/s8b_verdict.py:250-272`、floor は holdout ごと1値 `orchestrator/campaign/s8b_verdict.py:315-346`。off arm は `stock_common` 固定 `docs/phase3-8b-descriptor-design.md:288-291`。既存 S1 の `max(cv_a, cv_b, 0.03)` は二 arm 比較用である `orchestrator/campaign/s1_report.py:116-140`。凍結案は n、時間 block、算出式を事前固定するよう要求する `docs/phase3-8b-descriptor-design.md:199-212`。

   **提案:** rep → session median → cell/block統計 → relative floor → holdout scalar → absolute TPS までを数式として完全に凍結する。特に6構成間の集約、sample/population CV、drift の定義と採否、ゼロ/負/非有限値、stock baseline のどの統計量を絶対変換に使うかを決める。最終 artifact verifier が raw rep から独立再計算し、driver が自己申告した summary を信用しない構造にする。

9. **G9' — must-fix: `measure_point` は要求する「全生値」を保存せず、欠測も fail-closed ではない**

   **攻撃シナリオ:** reps=5 のうち3回失敗しても2回の成功値から median が作られる。abort、wall、latency は代表rep一件だけが残るので、失敗したrepや悪いrepを追跡できない。記録される `run_cmd` も実際に渡した argv の証跡ではなく再構成文字列である。

   **根拠:** individual rep failure は note にして skip し、全rep失敗時だけ例外にする `orchestrator/calibrator/runner.py:207-262`。返却時に代表repを一件選ぶ `orchestrator/calibrator/runner.py:264-277`。`ScalePoint` は throughputs の列と代表 wall/abort/latency しか持たない `orchestrator/calibrator/model.py:55-84`。実行 argv と reproduction command は別に組み立てられる `orchestrator/calibrator/runner.py:147-204`。2/5成功が判断に混入し得る点も既に設計資料で問題化されている `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:178-185`。

   **提案:** floor 用には rep 単位の構造化 recordを持つ runner API が必要である。rep index、status、TPS、abort、wall、latency、実 argv、開始時刻、競合/settle証跡を全件保存する。exact reps を要求するか、許容失敗数・再試行・欠測規則を protocol に明記し、それ以外は cell 未確定とする。「欠測→null」だけでは、部分成功を正常値に変える現 API を防げない。

10. **G10' — must-fix: final JSON/MD だけでは中断・再開・上書きによる選択的証拠化を防げない**

   **攻撃シナリオ:** 95/96 session 終了時にジョブが落ち、再実行で都合のよい session だけ残す、または同名 artifact を上書きする。monotonic ledger は完成後にまとめて書けば後付け可能であり、実行順や捨てた試行を証明しない。

   **根拠:** 既存 floor driver は JSON/MD を通常の `"w"` で上書きする `orchestrator/campaign/between_run_floor.py:111-145`。一方、リポジトリには append、flush、fsync、directory fsync を備えた WAL がある `orchestrator/campaign/wal.py:1-12,41-60`。oracle の monotonic 値も主にduration記録である `orchestrator/campaign/s8b_oracle_driver.py:594-718`。

   **提案:** immutable manifest を先に create-only で確定し、session開始・各rep・session終端を durable append-only WAL に即時記録する。resume は同じ manifest/protocol/freeze/binary hash に限り、既完了 session の再実行を拒否する。最終 artifact は WAL 全体の hash、完了/中断状態、全 retry を含む create-only projection とする。

11. **G11' — must-fix: protocol config の列挙が不足し、formula version は束縛ではなくラベルにすぎない**

   **攻撃シナリオ:** 同じ version 名のまま実装だけ median→mean、sample CV→population CV に変えられる。round-robin の開始点、seed、block間隔、within session の配置、timeout、retry を実装既定値に置けば、同じ protocol hash でも異なる実験になる。

   **根拠:** refreeze 対象には floor protocol、n、seed、block、extime、reps、machine failure list、allowed reasons 等が含まれる `output/insights/2026-07-16_s8b-ruling-package.md:368-369`。既存 schedule は master seed、block、replicate から明示的に順序を作る `orchestrator/campaign/s8b_oracle_manifest.py:108-166`。median→mean mutation を殺す V9 が要求されている `output/insights/2026-07-16_s8b-freeze-v2-design-material.md:383-407`。

   **提案:** config に少なくとも schema/formula ID、seed、schedule algorithm version、全session順、block分離条件、extime/timeout、within配置、retry/欠測/異常/CV/drift規則、環境contract hash、source/toolchain pin を含める。formula ID は閉じた registry にし、未知IDを拒否する。テストは承認済み protocol fixture から raw→最終scalar を通し、median/mean、n−1/n、block順、絶対変換、非有限値、exact n の mutationを殺す。「既存3点コピー検出」は grep ではなく、79/23等の合成 freeze からセル集合が完全一致し、5/50/95が一切現れない構成不変条件で検査する。

12. **G12' — should: Pegasus 将来制約を凍結案に明記しないと block と隔離の意味が崩れる**

   **攻撃シナリオ:** walltimeでblock途中にkillされ、別job・別nodeで再開する。process間の monotonic clock を連続時系列として扱う。scheduler上は非専有なのに、PID namespaceの都合で他jobが `pgrep` から見えず「単独」と判定する。`/scr` 消失でWALだけ失うこともある。

   **根拠:** Pegasus は exclusive submit が無効 `docs/pegasus-runbook.md:33-50`、walltime指定が必要 `docs/pegasus-runbook.md:79-113`、`/scr` は一時領域 `docs/pegasus-runbook.md:223-231`。node-local pgrep/load、非混合、環境採用条件は `docs/pegasus-runbook.md:245-273` と `docs/decisions.md:2290-2297` にある。

   **提案:** 将来の Pegasus contract に、blockを単一allocation/node/processで完遂する条件、walltime不足時のblock全廃棄、hostname/boot ID/job ID/cpuset/UTC記録、PID可視性の事前probe、共有node干渉の検出基準、永続領域へのWAL同期、module/compiler/job script hash を要求する。monotonic値は同一process内durationに限定する。

   **反駁:** これは cygnus上の純粋な engine 実装を妨げる理由ではない。ただしこれを未定義のまま「後でPegasus対応可能」と主張することはできない。

## 総評

**裁定: 現プランは却下。** freeze/protocol/manifest/binary/environment の束縛が途中で自己申告に戻り、統計から最終floorへの写像と欠測・再開規則も未凍結である。  
択Cを名乗るには、少なくとも狭い環境contract、単一読込の証拠連鎖、rep単位WAL、oracle側binary照合を実装前設計へ入れる必要がある。````

---

## C-delta prompt

````markdown
# 敵対的検証依頼 C-δ — freeze v2 世代 field 列挙 + 承認束縛方式の裁定案

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。以下の「私の裁定案」を攻撃し、裁定を返せ。忖度不要。所見ゼロでもよいが見逃しは罪。弱い所見には自分で反駁を併記せよ。

## 背景 (検証可能な事実 — まずこれらを読め)

- `output/insights/2026-07-16_s8b-freeze-v2-design-material.md` S 層 (146-215 行): 世代別不変 filename + supersedes 連鎖の設計、「承認記録は自己申告にすぎず、承認と世代を束縛する機械検証を設計しない限り F14 型になる」「v2 verifier は承認束縛を検証できない世代を invalid に倒す」
- wave 1 実装済み骨格: `orchestrator/campaign/s8b_holdout_freeze.py:549-640` 付近 — V2 header fields (supersedes_sha256, change_reason, ...)、`_reject_unratified_generation` (承認束縛方式が §8 未裁定のため、新世代は一律拒否)、旧世代 source verify の `frozen_at_head` git blob 束縛
- v1 freeze (`output/s8b-freeze/holdout_freeze.json`): floor/budget = null、design_source.sha256 で設計文書 bytes を束縛、frozen_at_head で HEAD を記録
- AI provenance 規約 (`docs/ai-provenance.md`): AI の commit は `AI-Agent:` trailer 必須、`tools/check_ai_provenance.py` が導入時点から HEAD まで監査
- §8 (design doc): floor/budget の数値充填・世代 schema の field 列挙・承認束縛方式は再凍結 + ユーザー承認事項
- 失敗型 F14 (`docs/failures.md`): 宣言のみの遮断 (謳うだけで発火しない保証)

## 私の裁定案 (これを攻撃せよ)

**(1) 世代間可変 field の閉じた列挙 (これ以外の diff は verifier が拒否):**
- `holdouts.<h>.floor` (null → number)
- `holdouts.<h>.budget` (null → object/number — v1 の budget field の形は freeze を読んで確認せよ)
- 新規 top-level: `env_tag` (v2 数値を束縛する唯一の env-tag、裁定 6)
- 新規 top-level: `floor_protocol` {path, sha256} (凍結された protocol 文書への束縛)
- 新規 top-level: `floor_source` {path, sha256} (floor campaign artifact への束縛)
- 新規 top-level: `experiment_numbers` {n_oracle, seed?, block, extime, reps, B_arm_seconds, B_holdout_seconds, B_total_seconds, allowed_excluded_reasons, 検定 4 点} (§5.2/§6/§8 の数値充填)
- v2 header: schema_version (v1→v2), supersedes_sha256, change_reason, approved_by, approved_at, approval_ref, frozen_at_head (新 HEAD), design_source.sha256 (設計文書改訂への追随)
- 上記以外 (holdout 条件・unknownness_check・variant_binding・derangement 等) は byte 同一を要求

**(2) 承認束縛方式 — 択 (a) を推奨:**
- **(a) 承認 record file 方式 (推奨):** `output/s8b-freeze/approvals/<generation_sha256>.md` を**ユーザーが** commit する。内容 = 世代 file の sha256 + 承認者 + 日付 + 承認対象の要約。verifier は (i) approval file の存在、(ii) filename と内容の hash が世代 bytes hash と一致、(iii) **approval file を導入した commit が `AI-Agent:` trailer を持たない** (= AI provenance 規約の逆用: 人間 commit の機械判定)、を検査。どれか欠け → 未承認 = 拒否 (実装済み骨格の既定)
- **(b) git tag 方式 (代替):** ユーザーが `s8b-freeze-v2-g<N>-approved` tag を世代 blob を含む commit に打つ。verifier は tag の存在 + tag が指す tree に世代 bytes が含まれることを検査。署名付き tag (GPG) ならより強い
- **(c) header 自己申告のみ:** F14 型 → 却下済み (設計素材)
- **正直な限界の明記:** ユーザー保有鍵の署名なしでは、in-repo のどの方式も「規約を無視する agent」を暗号学的には遮断できない。防壁は 規律 + provenance 監査 + hooks の多層。この限界は凍結案に明記する

## 攻撃してほしい点 (これに限定しない)

- D1. field 列挙の過不足。私が列挙し忘れた「変わらざるを得ない field」(それが漏れると verifier が正当な v2 を拒否する) と、「可変にしてはいけないのに紛れ込んでいる field」の両方向。実在の v1 freeze と骨格実装を読んで指摘せよ
- D2. 方式 (a) への攻撃: (i) AI が trailer なし commit を作れば偽装可能 — check_ai_provenance はそれを検出できるか (実装を読め)。(ii) approval file の**別世代への流用 (replay)** は hash 束縛で本当に塞がっているか。(iii) 承認後に世代 file を差し替える (hash が変わる → 検出される?) 経路。(iv) approvals/ ディレクトリ自体の削除・改竄。(v) 承認の**取り消し**をどう表現するか
- D3. 方式 (b) との比較優位の妥当性。tag は AI too が打てる (hooks で `git tag s8b-*` を拒否する防壁を足す価値?)。tag の push 忘れ・ローカル tag の消失など運用穴
- D4. supersedes 連鎖の分岐攻撃: 同じ v1 を supersede する 2 つの v2 世代が併存したとき、verifier はどちらを「発効中」と判定するか。「最新 = 有効」は安全か、明示的な active pointer が要るか
- D5. design_source.sha256 追随の穴: 設計文書が改訂されるたびに世代を切る運用は現実的か。設計文書の改訂と floor 数値の承認が別タイミングで来た場合の整合
- D6. `_reject_unratified_generation` の既定 (一律拒否) と、この裁定案の発効順序。裁定案自体の承認前に v2 世代を「準備」できる必要はあるか (ないなら不要な柔軟性を足さない)
- D7. 検定 4 点・seed 等を freeze 本体に入れるか、protocol 文書側に置いて {path, sha256} 参照にするか — どちらが改竄・drift に強いか
- D8. その他、「承認された」という主張が恒真になる経路

## 出力形式

`## 所見` に番号付き (D1', D2', ...) で列挙。各所見: **severity (must-fix / should / note)** / 攻撃シナリオ / 根拠 (file:line 必須 — 実在コード・freeze を読んで指せ) / 提案。最後に `## 総評` 2-3 行。日本語。
````

## C-delta output (逐語)

````markdown
## 所見

1. **D1′ — must-fix / floor・budget の位置と型が実体と不一致。**  
   **攻撃シナリオ:** 提案どおり `holdouts.<h>.floor/budget` を追加すると、既存 consumer は top-level `floor` / `budget` を null のまま読み、正当な v2 を拒否する。逆に top-level を削除すれば世代差分規則にも反する。v1 の budget の「形」は object/number ではなく、単なる `null` である。[output/s8b-freeze/holdout_freeze.json:622](/home/SFC/tanab/github/izanagi/output/s8b-freeze/holdout_freeze.json:622)  
   **根拠:** manifest は `floor.by_holdout` と `budget.{total_bench_s,per_holdout_bench_s,oracle_shared}` を要求し、数値単体を拒否する。[orchestrator/campaign/s8b_oracle_manifest.py:402](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:402) [orchestrator/campaign/s8b_oracle_manifest.py:413](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:413) [orchestrator/campaign/s8b_oracle_manifest.py:420](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:420)  
   **提案:** v2 も top-level を維持し、`floor={"by_holdout":{全 holdout: finite nonnegative number}}`、`budget={exact key set}` と逐語固定する。`object/number`、`seed?`、単なる「検定4点」は閉じた schema ではない。

2. **D1″ — must-fix / 正当な v2 で必ず変わる field と必須規則が漏れている。**  
   **攻撃シナリオ:** `generator.sha256` を不変にすると、v2 verifier を実装した正当世代が必ず拒否される。実際、freeze 記録値は `1910…`、現行 generator bytes は `2356…` で既に異なる。また `refreeze_note` は「後で充填する」と書かれており、充填後も byte 同一なら偽記述になる。[output/s8b-freeze/holdout_freeze.json:13](/home/SFC/tanab/github/izanagi/output/s8b-freeze/holdout_freeze.json:13) [output/s8b-freeze/holdout_freeze.json:624](/home/SFC/tanab/github/izanagi/output/s8b-freeze/holdout_freeze.json:624)  
   **根拠:** generator は source record として生成される。[orchestrator/campaign/s8b_holdout_freeze.py:492](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:492) 骨格は `approval_scope` で、案の `approval_ref` と一致しない。[orchestrator/campaign/s8b_holdout_freeze.py:555](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:555) さらに v2 必須の unstable・high_variance・部分 rep・expected reps 採否規則が列挙から落ちている。[output/insights/2026-07-16_s8b-freeze-v2-design-material.md:178](/home/SFC/tanab/github/izanagi/output/insights/2026-07-16_s8b-freeze-v2-design-material.md:178)  
   **提案:** 「v1→v2 migration」と「v2 gN→gN+1」を別 transition table にする。前者には `generator.sha256`、`refreeze_note` の置換/削除、rep 採否規則、selector-basis v2 束縛を明記する。`schema_version` の変更は最初の遷移だけ許す。

3. **D2′ — must-fix / 「trailer なし＝人間」は規約と逆で、人間性も証明しない。**  
   **攻撃シナリオ:** 正常な人間 approval commit は `AI-Agent: none` を持つため、提案 verifier に拒否される。一方、AI が trailer を省いた commit は verifier に承認扱いされ、provenance lint だけが違反にする。つまり承認条件が「既知の規約違反」を正としている。  
   **根拠:** 規約は全 commit に trailer を要求し、人間専用値を `AI-Agent: none` とする。[docs/ai-provenance.md:14](/home/SFC/tanab/github/izanagi/docs/ai-provenance.md:14) [docs/ai-provenance.md:33](/home/SFC/tanab/github/izanagi/docs/ai-provenance.md:33) 検査器は欠落を検出するが、`none` の真偽は検査しない。[tools/check_ai_provenance.py:56](/home/SFC/tanab/github/izanagi/tools/check_ai_provenance.py:56) さらに既定監査は policy commit の descendant だけなので、policy 導入前から分岐した branch 上の無 trailer commit を後で mergeする経路は漏れる。[tools/check_ai_provenance.py:104](/home/SFC/tanab/github/izanagi/tools/check_ai_provenance.py:104)  
   **提案:** 規約上は「approval commit は正確に `AI-Agent: none`、policy commit と approval commit はともに HEAD ancestry 上」とする。ただしこれは人間認証ではなく規約 attestation と明記する。人間性を機械判定したいなら、allowlist 済み鍵による signed commit・署名済み approval record・signed tag のいずれかが必須。

4. **D2″ — must-fix / hash replay は概ね塞がるが、approval record の履歴・取消・自己参照が未定義。**  
   **攻撃シナリオ:** approval file の「導入 commit」だけを見ても、その後の改変、削除→再追加、approver/date/summary の差替えを捕まえない。`approval_ref` が hash 由来の approval path を指すなら、世代 bytes が自分自身の SHA-256 を含む固定点問題になり生成不能。  
   **根拠:** 世代 file には create-only があるが、approval file の不変契約はまだ存在しない。[orchestrator/campaign/s8b_holdout_freeze.py:521](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:521) 現行の単一 read + raw-byte hash object は差替え窓を閉じる正しい先例である。[orchestrator/campaign/s8b_oracle_driver.py:101](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:101)  
   **反駁:** filename と内容の両方を raw generation hash に一致させ、同じ read object を使う限り、別 bytes 世代への replay と承認後の世代差替えは SHA-256 衝突を除き塞がる。ここ自体は弱い所見ではない。  
   **提案:** approval は strict canonical JSON、exact keys、HEAD tree の blob が導入時 blob と同一、その後 path 変更履歴なしを要求する。approval path は verifier が generation hash から導出し、generation header には入れない。取消は削除でなく `revocations/<generation_sha>.json` の不可逆 tombstone とし、取消後の再有効化は新 generation hash + 新承認だけにする。active approval 欠落時は旧世代へ fallback しない。

5. **D3′ — should / (a) の優位は運用面だけ。signed tag は認証面で上。**  
   **攻撃シナリオ:** unsigned/lightweight tag は AI も作成・移動・削除できる。現行 Bash guard は `tag` を非破壊 Git subcommand 群に含め、Codex には hooks 自体が未配線である。[hooks/guard_bash.py:116](/home/SFC/tanab/github/izanagi/hooks/guard_bash.py:116) [hooks/README.md:13](/home/SFC/tanab/github/izanagi/hooks/README.md:13) また tag target が HEAD 外なら既定 provenance 監査対象外になる。  
   **根拠:** 通常の branch push は tag を必ず運ばず、clone/fetch 側にも tag 欠落が起こり得る。この穴は未承認 acceptance ではなく fail-closed 停止・再現性喪失である。  
   **提案:** 鍵なしなら「(a) は通常 push で運ばれ、diff review しやすいから推奨」とだけ裁定する。認証強度まで求めるなら、canonical approval record を commitし、その commit または record hash を allowlist 鍵で署名するのが最良。`git tag s8b-*` hook 拒否は誤操作防止には価値があるが、Codex・script・履歴操作を塞がないため主防壁に数えない。

6. **D4′ — must-fix / supersedes DAG に active の定義がない。**  
   **攻撃シナリオ:** v1 を親に持つ承認済み v2 が2本あれば、filename の最大 N、commit 時刻、`approved_at` のどれも攻撃者が選べる。「最新＝有効」は高い g999 を置くだけで奪える。現 consumer はそもそも世代列挙をせず、固定 `holdout_freeze.json` を読む。[orchestrator/campaign/s8b_holdout_freeze.py:27](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:27) [orchestrator/campaign/s8b_oracle_driver.py:33](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:33) [orchestrator/campaign/s8b_selector_freeze.py:49](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_selector_freeze.py:49)  
   **提案:** `valid` と `active` を分離する。署名/承認された active record に `{generation_number,path,sha256,parent_active_sha256,approval_sha256}` を持たせ、番号の +1、canonical filename、親の一意性を検査する。複数の active successor、pointer 不正、active の取消はいずれも「active 世代なし」に倒す。単なる最新探索は禁止。

7. **D5′ — must-fix / 「旧世代 git blob 照合は実装済み」という前提が事実でない。**  
   **攻撃シナリオ:** 設計文書更新後に旧世代を検証しようとしても、現コードは `root / rel` の現在 bytes を hash する。`git cat-file` は commit の存在確認にしか使っておらず、`<head>:<path>` blob を読んでいない。[orchestrator/campaign/s8b_holdout_freeze.py:573](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:573) [orchestrator/campaign/s8b_holdout_freeze.py:590](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:590) [orchestrator/campaign/s8b_holdout_freeze.py:607](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:607)  
   **根拠:** 回帰テストも active v1 は worktree drift を拒否することしか検証していない。[orchestrator/tests/test_s8b_holdout_freeze.py:272](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_holdout_freeze.py:272) また `frozen_at_head` は出力前の現在 HEAD を記録するため、「世代 file を含む新 HEAD」を意味させると commit hash の自己参照になり不可能である。[orchestrator/campaign/s8b_holdout_freeze.py:485](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:485)  
   **提案:** `frozen_at_head` を「依存 source を含む pre-generation source head」と定義し、各 source を `git cat-file <head>:<path>` の blob bytes で照合する。世代 file と approval は後続 commit に置く。全文 design hash は改竄を通さないが、無関係な文言変更でも再世代化する可用性問題があるため、実行規則は不変 filename の machine-readable protocol へ分離し、design_source は説明 provenance に格下げする。

8. **D6′ — must-fix / floor 実測後の v2 は現行 unknownness verifier を原理的に通らない。**  
   **攻撃シナリオ:** v2 は floor campaign artifact を束縛して実測後に作るが、現 verifier は現在の repository を再検索し、holdout の痕跡が1件でもあれば拒否する。[orchestrator/campaign/s8b_holdout_freeze.py:624](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:624) [orchestrator/campaign/s8b_holdout_freeze.py:646](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:646) 除外は `output/s8b-freeze/` だけで、floor WAL/artifact の通常位置は隠れない。[output/s8b-freeze/holdout_freeze.json:35](/home/SFC/tanab/github/izanagi/output/s8b-freeze/holdout_freeze.json:35) 設計素材自身も「実走後は同じ holdout の新世代が verify を通らない」と認めている。[output/insights/2026-07-16_s8b-freeze-v2-design-material.md:84](/home/SFC/tanab/github/izanagi/output/insights/2026-07-16_s8b-freeze-v2-design-material.md:84)  
   **提案:** floor 実測前に、v1 hash・selector prediction hash・承認済み protocol/manifest・env/schedule・許可 artifact closure を束縛した launch certificate を発行する。v2 は前世代 head で歴史的 unknownness を検証し、現在までに増えた conjunction hit がその floor campaign closure と完全一致することを要求する。単に current search を省略したり `output/` 全体を除外すると、未申告の先行測定も隠れて fail-open になる。

9. **D6″ — must-fix / candidate 作成は必要だが、activation bypass は不要。**  
   **攻撃シナリオ:** hash を承認するには承認前に exact generation bytes が必要であるため、「未承認 v2 を一切準備しない」は実現不能。一方、通常 verifier に `--allow-unratified` を足すと実走 consumer が誤用できる。現骨格の一律拒否はこの点では正しい。[orchestrator/campaign/s8b_holdout_freeze.py:561](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:561)  
   **提案:** 順序を、(1) schema・承認方式・pre-floor protocol をユーザー裁定、(2) source head を commit、(3) AI が inactive generation を作成・構造検証して AI trailer 付き commit、(4) ユーザーが別 commit で approval/activation record、(5) 初めて active loader が受理、と固定する。候補検証は `CandidateFreeze`、実走は `RatifiedFreeze` の別 API/型にし、通常 consumer へ候補を渡せなくする。AI が生成した世代と approval を同じ `AI-Agent: none` commit に入れるのは provenance 上も虚偽になる。[docs/ai-provenance.md:46](/home/SFC/tanab/github/izanagi/docs/ai-provenance.md:46)

10. **D7′ — must-fix / freeze と protocol の二重正本、および全数値の未消費。**  
    **攻撃シナリオ:** freeze に `env_tag/reps/extime/n/allowed_excluded_reasons/B_arm` を書いても、現 manifest は caller 提供の `run_contract` と exclusion list を型検査するだけで freeze 値との一致を検査しない。[orchestrator/campaign/s8b_oracle_manifest.py:293](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:293) [orchestrator/campaign/s8b_oracle_manifest.py:497](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:497) driver が実際に使う env_tag も manifest 由来である。[orchestrator/campaign/s8b_oracle_driver.py:518](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:518) `B_arm_seconds` は現 budget consumer に存在せず、総枠と holdout 枠しか射影しない。[orchestrator/campaign/s8b_budget.py:96](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_budget.py:96)  
    **提案:** Markdown protocol は説明用、canonical JSON protocol を唯一の機械正本にする。floor 用と oracle/statistical-plan 用を分けるか、単一 `experiment_protocol.json` 内で namespace を分ける。freeze はその `{path,sha256}` と realized floor/source を束縛し、値を複製するなら verifier が完全一致を強制する。`seed` は required nullable、block/schedule は exact shape、検定は `mode=none|test` の discriminated union、rep 採否規則も明示する。全 field に実 consumer がなければ凍結せず、F14 として拒否する。

11. **D8′ — must-fix / strict v2 verifier を迂回する consumer と parser 差が残る。**  
    **攻撃シナリオ:** selector CLI は holdout freeze を JSON parseするだけで ratification verifier を呼ばず、manifest builder も path を直接再読込する。[orchestrator/campaign/s8b_selector_freeze.py:721](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_selector_freeze.py:721) [orchestrator/campaign/s8b_oracle_manifest.py:471](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_manifest.py:471) さらに holdout/manifest/driver の loader は duplicate JSON key を許す一方、selector loader は拒否するため、同じ承認済み raw bytes の解釈が入口ごとに異なる。[orchestrator/campaign/s8b_holdout_freeze.py:137](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_holdout_freeze.py:137) [orchestrator/campaign/s8b_selector_freeze.py:685](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_selector_freeze.py:685)  
    **反駁:** 現時点の oracle 実走は floor/budget 非 null を一律拒否するため、今すぐ未承認 v2 が走る穴ではない。[orchestrator/campaign/s8b_oracle_driver.py:173](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:173) v2 発効時の migration blocker である。  
    **提案:** raw bytes を一度だけ読み、duplicate key・NaN・未知 key を拒否し、generation hash・連鎖・approval・active をまとめて検証する単一 `load_ratified_freeze()` を全 consumer の唯一入口にする。`approved_by/approved_at/scope` を世代 header に残すなら approval record と逐語一致させる。外部 record を正本にするなら header 側の重複 claim は削除する。

## 総評

現案のままでは却下。特に top-level schema 誤認、`AI-Agent` 条件の逆転、active 未定義、floor 実測後の unknownness 自己拒否が致命的である。  
(a) は「運用しやすい別 record gate」としては採用可能だが、人間認証ではない。最終形は canonical approval record + 明示的 active 遷移、可能なら allowlist 鍵署名を推す。````

