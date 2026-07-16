# 8b floor protocol 凍結案パッケージ (2026-07-16) — §8 再凍結素材 + ユーザー裁定 7 単位 (F1〜F7)

**本文書は裁定資料 (非正本)。裁定の記録は `docs/phase3-8b-descriptor-design.md` §9 と
`docs/worklog.md` が正本。** 本文書は凍結族 (output/insights/) であり、裁定後も書き換えない —
裁定結果は §9 承認状態と worklog へ記録する。

- **位置づけ:** worklog 2026-07-16 (12) 次の一手 1 の**前半**。§8 手続き
  (docs/phase3-8b-descriptor-design.md:255-267) の再凍結素材 + ユーザー裁定を求める項目。
  本文書は**案であり、ユーザー承認まで何も発効しない** — floor への数値書込み・freeze への floor
  書込み・phase3/worklog の編集は本セッションでは行わず、承認後に親が行う。**数値はすべて「案」**
  であり、承認時に protocol JSON (機械正本) として凍結される。本 md は説明であって機械正本では
  ない (裁定 F7)
- **出自と敵対検証:** 敵対検証 = codex gpt-5.6-sol reasoning=max ×4 本 (C-α/C-β/C-γ/C-δ)。逐語と
  prompt は `output/insights/2026-07-16_s8b-floor-protocol-consultations.md` (512 行、**所見 47 件**、
  must-fix が大半)。親裁定サマリは `docs/handoff/2026-07-16-floor-protocol-wave2.md`。所見はデータ
  であり、本文書の記述はすべて親が現物ファイルと突合済み。**file:line 引用の基準コミット =
  64905d6**。tracked ファイルへの file:line 引用は 64905d6 の内容と一致する。本パッケージが参照する
  実装 2 ファイル (`s8b_floor_stats.py` / `s8b_floor_campaign.py`) とテスト・insight 群は同 commit に
  含まれない untracked 新規 (本セッション成果物)
- **前提裁定:** 裁定パッケージ (`output/insights/2026-07-16_s8b-ruling-package.md`) の裁定 5
  (R5 truth table) と裁定 6 (env 択 C + env_tag は v2 数値を束縛する唯一の env-tag) は発効済み。
  本パッケージは裁定 6 が空欄にした floor protocol・方法論・env_tag を充填する
- **構成:** 裁定 F1 = floor protocol 本体 (算出式) / F2 = 運用・停止条件・retry・resume / F3 =
  budget 導出と namespace / F4 = 実行順序と情報遮断 / F5 = freeze v2 世代 schema field 列挙 /
  F6 = 承認束縛方式 / F7 = v2 検証意味論。末尾に実行計画テンプレート・実装状況・不採用所見・
  ユーザー裁定チェックリスト
- **依存関係:** F1 の per-pair table は F5 (freeze schema の floor 形状) と F7 (freeze の protocol
  束縛) に伝播する。F4 の実行順序は F6 の発効順序と接続する (予測封印 → floor → 機械充填 → 承認 →
  oracle)。F1 の scale-adequacy gate は oracle 実走時の §6 第 3 条件判定と接続する。数値案は F1〜F3
  を横断するため、末尾チェックリストで一括提示する

---

## 裁定 F1 — floor protocol 本体 (対象集合・標本設計・算出式)

### 裁定を求める文言

対象別 between-run floor を、以下の対象集合・標本設計・算出式 (`s8b-floor-stats/v1`) で凍結するか。
これは §5.2 の「`floor_<holdout>` は holdout 単位のスカラー」
(docs/phase3-8b-descriptor-design.md:206-208) からの **per-pair table への変更**を含み、その変更
自体が本裁定の一部である。

### 推奨案

**対象集合 = 12 セル。** 2 holdout (rr80 / rr20 — output/s8b-freeze/holdout_freeze.json:40,:307)
× 6 構成すべて (variant_binding.entries = {p2_2_flag_opt, backoff_fixed_best, sort_best,
system_gate, ident_all, stock_common} — holdout_freeze.json:118 近傍)。oracle と**同一ビルド経路**
(s8b-build-cache, trace-disabled) の**同一 binary** を使う。

**標本設計 (案):**

- `n_sessions = 8` / セル。1 session = `measure_point` 1 回 (calibration 系譜。`pipeline.evaluate`
  は使わない)、`reps = 5` **exact** (部分成功は session 無効)
- `2 block × replicates_per_block 4`。block 間最小間隔 `min_block_gap_s = 1800` (案)
- **within-run 10-rep 品質セッションは置かない** — 用途がなく、reps=10 の高 CV を見た後の再測定・
  除外・floor 変更を許す HARKing 面になるだけ (所見 F1 採用)。between_run_floor.py:53-55,:76-84 の
  within 併記は floor 数値に用途がない
- **schedule = seed 均衡置換。** block × replicate ごとに `master_seed` から導出した seed で 12 セル
  の順序を置換し、全列 + hash を manifest に凍結する。決定的 round-robin は 12 セル周期の温度
  governor / 監視 daemon / NUMA reclaim と共鳴し、セル内 CV=0・block drift=0 でもセル間に固定位相の
  偽差を残す (所見 D1 採用)。oracle manifest の seeded shuffle と同型
  (s8b_oracle_manifest.py:108-166 の `derive_seed` + `build_schedule`)

**算出式 `formula_id = "s8b-floor-stats/v1"` (逐語。実装 `s8b_floor_stats.py` と本文で同一であること):**

- **session 有効** ⇔ `excluded_reason is None` ∧ `exec_failures == 0` ∧
  `len(throughputs) == reps_expected` ∧ 全値が `math.isfinite` かつ `> 0`。有効 session の
  `session_median = statistics.median(throughputs)`。**無効 session は median を作らない**
- セル `c` (holdout × 構成) の統計:
  - `m_c = statistics.median`(有効 session medians の列)
  - `s_c = statistics.stdev`(同列、n-1、**要 2 点以上**)
  - block `b` ごとに `m_{c,b} = statistics.median`(その block の有効 session medians)
  - **セル有効** ⇔ 有効 session 数 `== n_sessions` ∧ 各 block が `replicates_per_block` 本ずつ揃う
- `stock = stock_common` セル。**stock セル無効 → 当該 holdout の全 pair floor = null** (holdout 未確定)
- `c ≠ stock` の pair floor (絶対 tps):
  - `u_noise(c) = sqrt(s_c^2 + s_stock^2)`
  - `d_{c,b} = m_{c,b} - m_{stock,b}` (b = 1,2)、`delta_c = |d_{c,1} - d_{c,2}|`
  - `floor_pair(c) = max(u_noise(c), delta_c, wired_min_rel_floor × m_stock)`
  - **セル c 無効 → `floor_pair(c)` のみ null** (他 pair に veto しない)
- **scalar 代替 (併記用):** `scalar_alt = max`(全 pair の `floor_pair`)。いずれかの pair が null →
  `scalar_alt = null`
- `scale_ref = m_stock` を記録 (oracle 実走時の scale-adequacy gate 用)。診断併記:
  `cv_c = s_c / statistics.fmean`(有効 medians)
- **統計的位置づけ:** これは**記述的な効果量 + noise gate** であり、α・検定力は未保証 (**検定ではない**)

**凍結の形状 = per-pair table。** §5.2 の holdout 単位スカラーからの変更を本裁定で確定する。verdict
充填時は、封印済み予測の on-choice に対応する pair 値を機械選択して holdout→スカラーの Mapping を
組み、`judge_combined(..., floors=...)` へ渡す。s8b_verdict.py は floors Mapping を呼び手から受け
(`judge_combined` シグネチャ = s8b_verdict.py:264-265、`_floor_value` = :200-207)、`_floor_exceeded`
は方向付き `on_median − off_median > floor` を評価する (:238-261) ため、**s8b_verdict.py の実装変更
は不要** (pair→スカラー射影は呼び手の責務)。

**scale-adequacy gate:** oracle 実走時の stock median が floor campaign の `scale_ref` から相対
**±10%** (案) を外れたら §6 第 3 条件は**判定不能**。凍結した絶対 floor は周波数・温度で全 TPS が
一様スケールすると相対意味を失う (100k→125k で 3k 凍結値が 3% → 2.4% となり anti-conservative)
ため、尺度陳腐化を機械検知する (所見 B2 採用)。

### 代替案

- **stock のみ 2 セル (between_run_floor 同型):** stock_common だけを 2 holdout で測り、on 側構成の
  分散を無視する。代償 = on 構成の絶対 SD (特に high-abort 構成) が floor に乗らず、`u_noise(c)` の
  `s_c` 項が欠落する。§6 第 3 条件は on/off 両構成の実測差を締めるため、on 側分散無視は fail-open 側
- **scalar 契約の維持 (`scalar_alt` を凍結値とする):** per-pair table を置かず単一スカラーで束縛。
  代償 = rr20 の未選択 high-abort 構成だけが巨大 CV を持つと、選択された安定構成対 stock の判定まで
  無関係セルの veto で不成立になる (所見 C1)。しかも巨大な有限 floor は null にならず、消費側は
  「判定不能」でなく REFUTED を返し得る (s8b_verdict.py:261)。推奨案は per-pair でこれを回避し、
  scalar_alt は**併記のみ**とする
- **n 増 + 上側信頼限界 (A2 代替):** n=8 の CV 推定は相対 SE ~27% で保守上界でない。分散の事前規定
  した上側信頼限界を floor に使う、または n を増やす。v2 では**不採用**とし限界として記録 (下記)

### 代償・限界 (正直な記録)

1. **fresh back-to-back は cold-boot / 温度を未含の下限。** 2 block 分離 (`min_block_gap_s`) + wired
   3.0% で防御するが**保証ではない** (所見 E2)。cold boot を含めないなら、その限界を報告に明記する
2. **n=8 の CV 推定は相対 SE ~27% で保守上界でない** (所見 A2 — between_run_floor.py:55 が同 SE を
   明記)。最大 CV セルが一つだけなら 6 セルの max でも救われない。n 増と上側信頼限界は代替案として
   記録し v2 では採らない
3. **α・検定力は未保証の逐語限定** (所見 A1)。「median の SE が小さいから保守的」は成立しない — 帰無
   仮説下で median 差の SE は約 0.627σ、単一セッション σ を floor とすると閾値は約 1.6 SE。本 protocol
   は検定を持たないため「記述的効果量 + noise gate、統計的誤判定率・検定力は未保証」と限定する
4. **build-to-build 分散は対象外** (全 session 同一 binary)。binary を跨ぐ性能ドリフトは floor に
   含まれない

### 反映した敵対所見 (ID 列挙)

A1 (α未制御 → 効果量 gate 限定) / A2 (n=8 CV は保守上界でない → 代替記録) / B1 (max CV×stock は
絶対分散を覆わない → pair 絶対差 `u_noise`) / B2 (絶対 floor の尺度陳腐化 → scale-adequacy gate) /
C1 (全セル max = 無関係セル veto → per-pair table) / D1 (固定 round-robin のドリフト共鳴 → seed 均衡
置換) / E1 (`max(CV,drift)` は contrast drift 未測 → block 対比差 `delta_c`) / F1 (within-10 品質
セッションの HARKing 面 → 廃止) / G1 (`stdev/median` は非対称・非保守 → stdev n-1) / B7' (縮約式
不在 → 完全凍結) / G8' (統計→scalar 写像未定義 → 逐語式 + 独立再計算 verifier)。

---

## 裁定 F2 — 運用・停止条件・retry・resume

### 裁定を求める文言

floor campaign の session 有効性契約・停止条件・retry・resume・単独性臨界区間を以下で凍結するか。

### 推奨案

**session 有効性契約** = 裁定 F1 の逐語定義 (excluded_reason None ∧ exec_failures 0 ∧ exact reps ∧
全値有限正)。

**`allowed_excluded_reasons` の閉じた表** ({code, 発生 stage, 必須証拠, retry 可否, 課金, 伝播}):

| code | 発生 stage | 必須証拠 | retry | 課金 | 伝播 |
|---|---|---|---|---|---|
| `competing_process` | preflight probe | probe 生出力 (pgrep argv/pid) | 可 | wall 課金 | session 無効 |
| `launch_failure` | プロセス起動 | journal record (errno/stderr) | 可 | wall 課金 | session 無効 |
| `nonfinite_or_partial_output` | bench | throughputs 全件記録 | 可 | wall 課金 | session 無効 |

**`correctness-red` は floor campaign に存在しない** — floor は perf 専用計測であり、verify は oracle
側の契約 (§5.2 の legacy+S2、trace-enabled 別ビルド別 run)。excluded_reason に correctness 系コードを
入れない (現行 report も correctness-red の excluded 指定を protocol violation とする — 所見 B3')。

**retry** = `retry_slots_per_cell = 2` (案)。セルごとの**campaign 通算**予算 (block を跨いで復活
しない)。無効 session が出た block の末尾で消化する (block の時間窓を保つ)。**first-authorized-valid**
のみ採用、**全 attempt 課金**。それでも n=8 未達 → stock セルなら holdout
全体を未確定、他セルなら当該 pair を未確定。固定上限は結果を見る前に理由コードで機械発火する限り選択
経路を閉じる (所見 B1')。

**journal / resume:**

- journal = **append-only jsonl + fsync** (session 開始/終了/probe 生出力/wall を即時記録)。
  manifest / result は **create-only** (上書き禁止) — between_run_floor.py:111-119 の `"w"` 上書きは
  floor には不適で、95/96 session 完了後の crash → 都合のよい session 再現を許す (所見 G10 採用)
- resume は同一 protocol / freeze / manifest / binary hash に限り **forward-only** (完了 session の
  再実行拒否。resume 時に記録済み binary_sha256 を disk 再ハッシュと照合、不一致拒否)。crash した
  session は **terminal + 課金**。campaign 全やり直しは不可 (所見 B8')

**単独性の臨界区間** (一つの区間として): `probe → measure → post-probe → journal`。

- probe の pgrep rc 意味論: **rc=1 のみ「競合なし」**、rc=0 は競合列挙 (session 無効)、実行不能・rc>1・
  parse 不能は **campaign abort = fail-closed**。現行の共有 helper `competing_bench_pids` は `OSError`
  等で空集合を返す **fail-open** (runner.py:107-144) であり、floor driver は**自前の strict probe**を
  使う。共有 helper 側の是正は v2 前提条件へ登録する (所見 B10 / G7 採用)
- `settled=False` 相当 (settle timeout) は session 無効

### 代替案

- **無限 retry (上限なし):** 時間を食い潰し、CV を見て停止する選択経路を開く (所見 B1')。却下
- **abort rate 閾値による除外:** high-abort 構成の分散を floor から隠す観測後 cherry-pick。**採らない**
  — abort rate は正当な workload 結果であり全件報告、process failure / partial rep / correctness と
  型分離する (所見 B12')。病的構成が floor を支配する問題は per-pair table (F1) で解く

### 代償・限界

- retry_slots を持つこと自体が「n=8 未達で当該 pair/holdout を落とす」fail-closed を強めるため、正当な
  機械故障でも floor 未確定へ倒れやすい (§5.2 の対称判定不能と整合の意図的代償)
- 自前 strict probe は共有 helper と二重実装になる — drift 回避のため共有 helper 是正を v2 前提条件へ
  登録し、是正後に floor driver を切替える

### 反映した敵対所見 (ID 列挙)

B1' (retry 上限 → retry_slots + first-authorized-valid) / B2' (session valid の exact reps) /
B3' (excluded_reason の意味領域混同 → 閉じた表、correctness-red 除外) / B8' (自由 resume → append-only
registry / forward-only) / B10' (pgrep fail-open → strict probe) / B12' (abort 非除外の維持) /
G7' (単独性の check/run race → 臨界区間) / G9' (measure_point の欠測 fail-open → exact reps + 全件記録) /
G10' (`"w"` 上書き → create-only + WAL)。

---

## 裁定 F3 — budget 導出と namespace

### 裁定を求める文言

floor campaign と oracle 実走の予算を、以下の三層 namespace と導出式で凍結するか。

### 推奨案

**三層 namespace** (子枠間移転禁止 — S-1 (iv) と同型):

- floor campaign 開始前に凍結: `B_pilot_wall` / `B_floor_bench` + `B_floor_wall`
- v2 freeze 側 (oracle): `B_oracle_bench` + per_holdout + `B_arm`
- 親: `B_campaign_wall` (全 build/verify/bench/timeout/pilot 込み、全費用込みの親 wall cap)

**導出式:**

- `B_floor_bench = Σ_cells n_sessions × reps × extime_s` (名目) を**下限**とし、予約 envelope は
  pilot 校正した実測 wall/session × (8×12 + retry 上限) + build + preflight。**課金は monotonic wall
  実測**。名目 `extime` 和 (12×8×5×3 = 1440s) は「累積ベンチ実時間」ではなく、process 起動・retry・
  失敗 rep を含まない (所見 B4')

**oracle 側の正直計上 (これを `B_campaign_wall` に含める):**

- 現行 §5.2 の「現行 verify (legacy+S2) をそのまま使用」は `pipeline.evaluate` が trial ごとに verify を
  回すことを意味する。`N_oracle=8` なら **12 セル × 8 = 96 evaluate = S2 verify 96 回**。cygnus 実測
  433s/verify の prior で **~11.6h** + trace/perf 両 build (所見 B5 採用)
- verify 証明書の cell 単位再利用 (exact build/source/config hash ごとに 1 回認証して全 bench session が
  hard-consume) は**正しさゲートのアーキテクチャ変更**であり、本パッケージでは提案しない (規律 2
  保守側)。**別裁定として起票可能**とだけ記す

**cygnus 実績は非拘束の planning prior:**

- 54.8s/session・433s/verify は cygnus (linux-baremetal) 実測。env 未確定 (裁定 6 択 C) の下では
  **非拘束の planning prior** と明記する (Pegasus なら別値 — 所見 B9)
- `pilot` = 既知 workload 1 セル (holdout を汚さない rr50 等) で build→bench→(oracle 側は +verify) の
  wall/bench 比を**分解実測**。一セルの wall/bench 比では固定費 (build/legacy/S2/verifier/cleanup) を
  推定できないため分解する (所見 B5')。pilot の wall も `B_pilot_wall` に計上

### 代替案

- **floor 予算を実験予算と完全別枠で「同じ台帳規律」だけ適用:** scope が定まらず、pilot/floor 消化後に
  v2 の `B_total` を決める遡及予算になる (所見 B6')。**却下** — 親 `B_campaign_wall` と子枠の親子関係を
  逐語化する推奨案で矛盾を解消する
- **verify 証明書 cell 単位再利用で B_oracle を圧縮:** ~11.6h の verify を削れるが正しさゲートの
  アーキテクチャ変更 (規律 2)。本パッケージでは提案せず別裁定に分離

### 代償・限界

- 事前 reservation は保守的 (実消費より大きい枠を先取り) で予算利用効率が下がる。crash 時非解放と
  合わせ「安全側で予算を余らせて判定不能」に倒れやすい (§5.2 対称性維持の意図的代償)
- 96 verify ~11.6h は cygnus prior 依存。env 確定後の pilot で校正するまで拘束値にしない

### 反映した敵対所見 (ID 列挙)

B4' (1800s 名目算術は累積 bench wall でない → 予約 envelope + monotonic 課金) / B5' (54.8s と 12×433s
の非両立、S2 verify ×96 → 正直計上 + 分解 pilot) / B6' (別枠 scope 未定義 → 三層 namespace + 親 wall
cap) / B9' (cygnus 値の凍結転用 → planning prior 明記)。

---

## 裁定 F4 — 実行順序と情報遮断

### 裁定を求める文言

floor campaign を含む実走の凍結順序と env_tag 束縛を以下で凍結するか。

### 推奨案

**凍結順序:**

1. 本パッケージ承認 + protocol JSON 凍結 + env_tag 確定 (裁定 6 の env_tag 保留を解除)
2. **selector 予測封印** (§9 項 6 selector_predictions.json、**floor データ閲覧前**)。floor campaign は
   12 セルで 6 構成の順位・on−stock 差をほぼそのまま露出するため、封印が floor の後だと HARKing 遮断が
   壊れる (所見 H2 / B11 採用)
3. floor campaign 実走
4. calculator 純関数 (`s8b_floor_stats.py`) による**機械充填** + `verify_floor_artifact` の再計算一致
5. v2 候補世代生成 + ユーザー承認 (provenance 照合のみ)
6. oracle 実走

**env_tag:** protocol JSON の `env_tag` が v2 数値を束縛する唯一の env-tag (裁定 6)。driver は
`p2_2.ENV_TAG` (p2_2.py:39 = `linux-baremetal`) との一致を機械検査し、不一致は拒否する。env contract の
抽象化 (`ExecutionEnvironmentContract` の分離) は裁定 6 工数欄どおり **Pegasus 差分に据え置き** — env_tag
一致検査のみ採用し、G5' の env contract 即時実装は**縮小採用** (下記不採用節)。

**Pegasus 将来制約 (文書化のみ — 所見 G12):** block を単一 allocation / node / process で完遂 /
walltime 不足時は block 全廃棄 / hostname・boot id・job id・cpuset・UTC 記録 / PID 可視性の事前 probe /
WAL は永続領域 (`/scr` は一時領域のため不可) へ / module・toolchain・job script hash。monotonic 値は
同一 process 内 duration に限定する。

### 代替案

- **予測封印を floor の後に置く:** pilot cache を本走へ持ち込む・floor を見てから selector の
  model/prompt/effort を決める経路が残る (所見 B11')。却下
- **env contract を今抽出 (G5' 全面採用):** Pegasus adapter 全体を今作るのは過剰設計 (裁定 6 の工数据え
  置きと矛盾)。狭い contract 抽出のみ将来採用余地を残し、本パッケージでは env_tag 一致検査に縮小

### 代償・限界

- env_tag 一致検査のみでは、Pegasus で driver を起動すると artifact が linux-baremetal の 48 threads /
  1M records / CLK1800 / `numactl --interleave=all` を事実上持ち込む (所見 G5')。この env-neutral は
  「cygnus 専用値を hardcode したまま tag だけ記録」の限界を持つ — env contract 化は v2 前提条件
- 予測封印を先行させると、封印後に floor で構成順位が露出しても selector を動かせない (意図的拘束)

### 反映した敵対所見 (ID 列挙)

H2 / B11' (floor データ露出 → 予測封印を floor 前に凍結、実行順序固定) / G5' (p2_2 定数依存を
env-neutral と呼べない → env_tag 一致検査 + env contract は v2 前提条件へ縮小) / G12' (Pegasus 将来
制約 → 文書化)。

---

## 裁定 F5 — freeze v2 世代 schema field 列挙

### 裁定を求める文言

v2 freeze 世代の field 列挙と transition table を以下で凍結するか。

### 推奨案

**floor / budget の位置と形状:** v1 の floor / budget は **top-level null**
(holdout_freeze.json:622 近傍、`floor: null` / `budget: null`)。manifest validator は `floor.by_holdout`
と `budget.{total_bench_s, per_holdout_bench_s, oracle_shared}` の形を要求し数値単体を拒否する
(s8b_oracle_manifest.py:402-425 の `_validate_execution_snapshot`)。よって **top-level を維持**する
(所見 D1' 採用)。v2 の floor は per-pair table を含む形を提案する:

```
floor = {
  "by_holdout": {
    "rr80": {"pairs": {<構成>: <数値>, ...}, "scale_ref": <数値>, "scalar_alt": <数値|null>},
    "rr20": {...}
  }
}
```

manifest validator の per-pair floor 形状への追随変更を **v2 実装項目として列挙**する
(現行 `by_holdout.<h>` は有限非負スカラーを期待するため、object 形へ拡張が必要)。

**transition table を分離** (所見 D1″):

- **v1→v2 で変わってよい** = {`floor`, `budget`, `refreeze_note` (充填済みへ置換), `schema_version`,
  `generator.sha256` (v2 verifier 実装で必ず変わる — 現物で `1910…`→`2356…` の drift を実測済み),
  `design_source.sha256` (R1 追随), `frozen_at_head`, `env_tag` (新規), `floor_protocol {path,sha256}`
  (新規), `floor_source {path,sha256}` (新規), `experiment_numbers` (新規: n_oracle,
  bench_max_rounds=1, extime/reps, seed (required nullable), 検定 `mode = none|test` の discriminated
  union, allowed_excluded_reasons, rep 採否規則), v2 header (supersedes_sha256, change_reason,
  approved_by/at, approval_scope)}
- **v2 gN→gN+1 で変わってよい** = 列挙済み floor/budget/experiment_numbers 系 + header のみ
- **それ以外の diff は verifier 拒否**

**全 field に実 consumer を要求** — consumer 不在の凍結 field は F14 として拒否する (所見 D7')。
`B_arm_seconds` は現 budget consumer に存在しない (所見 D7')ため、消費側 (manifest/budget) の追随を
同時実装しない field は凍結しない。

### 代替案

- **`holdouts.<h>.floor/budget` へ移設:** 既存 consumer は top-level を null のまま読み正当な v2 を拒否
  する (所見 D1')。却下
- **単一 transition table (v1→v2 と gN→gN+1 を分けない):** v2 verifier 実装で必ず変わる
  `generator.sha256` を不変扱いすると正当世代が拒否される (所見 D1″)。却下

### 代償・限界

- per-pair table 形状は manifest validator・budget consumer・verdict 呼び手の追随を要し、v2 実装項目が
  増える。追随なしで floor 形状だけ変えると manifest build が破綻する
- `experiment_numbers` の field は各々 consumer を要求するため、consumer 未実装の field は凍結を後送り
  にする (fail-closed 側の遅延)

### 反映した敵対所見 (ID 列挙)

D1' (top-level floor/budget の位置・型と manifest 要求形状) / D1″ (transition table 分離・generator
drift・rep 採否規則の列挙) / D7' (freeze/protocol 二重正本・全 field consumer 要求)。

---

## 裁定 F6 — 承認束縛方式

### 裁定を求める文言

v2 世代の「承認済み」を機械判定する方式を以下で凍結するか。

### 推奨案 (a) approval record 方式

- **path** = `output/s8b-freeze/approvals/<generation_sha256>.json`。path は verifier が**世代 bytes
  hash から導出**する — 世代 header に approval path を入れない (世代 bytes が自分の SHA-256 を含む
  固定点問題を回避 — 所見 D2″)
- **内容** = strict canonical JSON `{generation_sha256, approver, approved_at, scope}` (exact keys)
- **ユーザーが commit** し、その commit は AI provenance 規約の**人間値 `AI-Agent: none` を逐語**で持つ。
  「trailer なし = 人間」は規約と逆 (docs/ai-provenance.md:13,:36 = 全 commit に trailer 必須、人間 =
  `none`。check_ai_provenance.py:56 は欠落を検出するが `none` の真偽は検査しない) — 所見 D2' 採用
- **検証** = record 存在 ∧ filename と内容の hash が世代 bytes hash と一致 ∧ 導入 commit が HEAD
  ancestry 上 ∧ trailer が `none` 逐語 ∧ 導入後の path 改変履歴なし

**取り消し** = `output/s8b-freeze/revocations/<generation_sha256>.json` の**不可逆 tombstone** (削除
でなく tombstone)。

**active 世代の決定** = 明示 active pointer record
`{generation_number, path, sha256, parent_active_sha256, approval_sha256}`。複数 successor・pointer
不正・revoked は「**active なし**」へ fail-closed。「最新 = 有効」は禁止 (高い g999 を置くだけで奪える
— 所見 D4)。

**発効順序** (所見 D6″):

1. 本方式のユーザー裁定
2. source head commit
3. AI が **inactive** 候補世代を生成・構造検証し、**AI trailer 付き** commit (CandidateFreeze)
4. ユーザーが**別 commit** で approval + active pointer
5. `load_ratified_freeze` だけが実走 consumer (candidate を渡せない型分離)

世代と approval を**同一 `none` commit に入れるのは provenance 虚偽** (AI 生成世代を人間 commit に
混ぜる — ai-provenance.md)。

### 代替案 (b) signed commit / signed record

- allowlist 済み鍵での signed commit / signed record / signed tag。**認証強度は上** (規約 attestation
  でなく暗号学的証明)。運用コストと鍵管理が増える
- **tag 方式は推さない** — hooks の tag guard は Claude 側のみ配線・**codex 未配線** (hooks/README) で
  あり、`git tag s8b-*` を AI が打てる。tag は通常 push で運ばれず fetch 側で欠落し得る (所見 D3')

### 代償・限界 (正直な記録)

- これは**規約 attestation であり人間性の暗号学的証明ではない** — AI が `none` commit を作れば偽装可能
  で、check_ai_provenance は `none` の真偽を検査しない。防壁は 規律 + provenance 監査 + hooks の多層。
  強化選択肢 = allowlist 鍵署名 (代替案 b)
- approval record・revocation・active pointer の新規実装と検証が増える (v2 machinery)

### 反映した敵対所見 (ID 列挙)

D2' (「trailer なし = 人間」は規約と逆 → `AI-Agent: none` 逐語) / D2″ (approval path 自己参照・履歴・
取消未定義 → hash 導出 path + tombstone) / D3' (tag は AI も打てる・codex 未配線 → record 方式推奨、
signed は代替) / D4' (supersedes DAG に active 未定義 → 明示 active pointer + fail-closed) /
D6″ (activation bypass 不要・candidate 必要 → 型分離した発効順序)。

---

## 裁定 F7 — v2 検証意味論 (blob 照合 + 歴史的未知性)

### 裁定を求める文言

v2 freeze の検証意味論 (source blob 照合・歴史的未知性・単一入口) を以下で凍結するか。

### 現状の事実 (再設計の動機)

- v1 `verify_document` は**worktree bytes 照合**であり、`design_source` (1829af…→bce6ef…) と
  `generator` (1910ff…→2356fd…) の drift で**現在すでに不合格** (実測。s8b_holdout_freeze.py の
  `_verify_source` は `root / rel` の現在 bytes を hash し、`git cat-file` は commit 存在確認のみで
  `<head>:<path>` blob を読んでいない — 所見 D5')
- floor 実走後は unknownness 再検索が floor 成果物に conjunction hit して**恒久に不合格**
  (docstring が明記する意図的 fails-closed — s8b_holdout_freeze.py:624-646、除外は
  `output/s8b-freeze/` だけで floor WAL/artifact の通常位置は隠れない — 所見 D6')
- よって v2 検証は**再設計が必要**

### 推奨案 (v2 検証)

1. **source は `frozen_at_head` の git blob bytes で照合** (`frozen_at_head` を pre-generation source
   head と再定義。`git cat-file <head>:<path>` の blob bytes)。現行は commit 存在確認のみで blob を
   読んでいない (所見 D5')。世代 file と approval は後続 commit に置く
2. **未知性は二層** (launch certificate 方式 — 所見 D6' 採用):
   - v1 凍結時点で成立、+
   - v1 以後に増えた conjunction hit が、**申告済み計測 closure** (floor campaign の登録 artifact 集合)
     と**完全一致**
   単に current search を省略したり `output/` 全体を除外すると未申告の先行測定も隠れて fail-open になる
3. **全 consumer を単一 `load_ratified_freeze` へ統一** (duplicate key・NaN・未知 key を拒否、
   generation hash・連鎖・approval・active をまとめて検証。selector loader と holdout/manifest/driver
   loader の duplicate key 許否差・parser 差を解消 — 所見 D8')
4. **floor driver は暫定的に bytes sha256 pin** (protocol 記録) + 構造検査で v1 を束縛し、意味再検証は
   v2 machinery の責務とする

**machine 正本の分離:** protocol JSON = **機械正本** (実行規則・数値)、本 md = 説明。freeze は protocol
の `{path, sha256}` を束縛する (所見 D7')。

### 代替案

- **v1 `verify_document` を worktree 照合のまま流用:** design/generator drift で恒久不合格 (実測)。
  floor 実走後は unknownness も恒久不合格。却下 — v2 は再設計必須
- **`output/` 全体を unknownness 検索から除外:** 未申告の先行測定を隠す fail-open (所見 D6')。却下 —
  申告済み closure との完全一致で締める

### 代償・限界

- launch certificate + closure 完全一致は、申告漏れ artifact が一つでもあれば fail-closed (可用性を
  犠牲に fail-open を塞ぐ)。floor campaign の全 artifact を漏れなく closure へ登録する運用が前提
- `git cat-file` blob 照合は source を含む pre-generation head を要し、世代 file 自身は後続 commit に
  なる (frozen_at_head の自己参照回避 — 所見 D5')

### 反映した敵対所見 (ID 列挙)

G1' (freeze が検証不合格・単一 object 化) / G2' (protocol/manifest の TOCTOU) / D5' (git blob 未照合 →
`git cat-file <head>:<path>`) / D6' (floor 実走後の unknownness 自己拒否 → launch certificate + closure
完全一致) / D7' (二重正本 → protocol JSON 機械正本) / D8' (consumer ごとの parser 差 → 単一
`load_ratified_freeze`)。

---

## 実行計画テンプレート (裁定 6 のテンプレを充填、ユーザー欄は明示的に空欄)

env 確定後に埋めて着手する。

- **revision:** 計測に使う committed HEAD / CCBench pin (未 commit 作業木では走らせない)
- **preflight:** 計測ノード上の単独性確認 (F2 の strict probe + pgrep rc 意味論)、calibration との
  動作点照合、trace-disabled build の確認 (絶対規律 1)、freeze bytes sha256 pin の照合
- **停止条件:** 競合検知時は当該 session 無効 → retry_slots 内で再測 → n=8 未達なら pair/holdout 未確定。
  probe 実行不能・rc>1 は campaign abort。abort rate・CV の異常閾値は protocol で事前凍結
- **artifact 回収:** `output/env/<env-tag>/calibration/` へ JSON + md、freeze v2 への数値充填は §8
  手続きの再凍結として別 commit (機械充填 = `s8b_floor_stats.py`)
- **実行責任者・開始時刻:** **(ユーザー裁定側、本文書では埋めない)**
- **env_tag:** **(ユーザー、承認時に確定 — 裁定 6 の保留解除)**

---

## 実装状況 (本セッション)

**実装済み (env-neutral、発効なし):**

- `orchestrator/campaign/s8b_floor_stats.py` — `formula v1` 純関数 (session 有効性・m_c/s_c・
  u_noise/delta_c・floor_pair・scalar_alt・scale_ref・cv_c) + `verify_floor_artifact` (raw から独立
  再計算し driver 自己申告 summary を信用しない)
- `orchestrator/campaign/s8b_floor_campaign.py` — pilot モードのみ動作。official は §8 承認束縛の裁定
  (F6) まで**常時拒否 = fail-closed** (未承認 protocol での本走を許さない)。protocol config は明示入力
  (未凍結数値のデフォルト内蔵禁止)、CLI に env・経路・数値の上書き面を作らない。pilot artifact には
  `eligible_for_refreeze: false` を焼き込み、official だけが再凍結資格を持つ (`validate_protocol`/
  `main` 参照。**G3' 反映済み** — pilot/official の hash 自己申告区別不能に対応)
- **G11' (protocol config 列挙不足・formula version はラベルにすぎない) = 反映済み (一部残):**
  protocol key の完全列挙 (未知 key 拒否)・formula の `FORMULA_ID` 逐語束縛・mutation-killing テスト
  (median↔mean、stdev n-1↔n、改竄検出) は実装済み。schedule seed 導出の golden pin テストは追補済み
  (並行修正で `test_s8b_floor_campaign.py` に追加)
- テスト 2 本

**v2 前提条件として登録 (未実装):**

- oracle 側 binary **full-sha256** 照合 (floor artifact に記録済みの hash を消費する側。恒真 claim
  回避のため本パッケージでは「保証」と書かない — 所見 G4)。現行 `BuildResult.bin_hash` は 16 文字
  切詰めで、oracle は hash 同一性を検証しない
- 共有 `competing_bench_pids` の fail-open 是正 (floor driver は当面自前 strict probe)
- strict v2 verifier 本体 (F5〜F7 裁定後)
- manifest validator の per-pair floor 形状追随
- oracle `bench_max_rounds=1` の run_contract 凍結
- **共有 materialization モジュール抽出 (G6'):** 現状 `s8b_floor_campaign.py` は
  `s8b_oracle_driver.prepare_cell` / `_prepared_binding` を直接 import して再利用しており
  (:71,:1112 — variant binding 検証・cell materialization・binding identity・trace-disabled build
  を oracle 側 private helper に委ねる形)、G6' が警告した「oracle driver 丸ごとの呼出しもコピペも
  不適切」という再利用境界の未定義状態を現に抱えている。v1 では二重実装 drift (`docs/failures.md:32-34`)
  を避けるため import 経路を選んだが、oracle 固有の gate/budget/schedule 契約への依存循環という
  代償は解消していない (下記「不採用・縮小した敵対所見」参照)。v2 では variant binding 検証・cell
  materialization・binding identity・trace-disabled build を公開の小さな共通モジュールへ抽出し、
  oracle と floor の双方をその consumer にする

---

## 不採用・縮小した敵対所見 (正直な記録)

- **A2 (n 増・上側信頼限界):** n=8 CV の相対 SE ~27% は事実だが、n 倍増は計測時間を線形に増やし、
  上側信頼限界は floor を過剰保守にして「成立」を機械的に困難にする。v2 では raw `s_c` を使い、限界
  として明記 (代替案に記録) — 検定を主張しない本 protocol では効果量 gate で足りる
- **C1 の pair 表を超える design-inadequate sentinel:** pair floor が巨大でも null にせず
  `design-inadequate/indeterminate` を別途発火させる案は、観測後の cap = HARKing 面を作る。per-pair
  table の null 伝播 (セル無効 → 当該 pair のみ null) で必要十分
- **G5' (env contract 抽象の即時実装):** Pegasus adapter 全体は過剰設計 (裁定 6 の工数据え置きと矛盾)。
  env_tag 一致検査のみ採用し、狭い contract 抽出は v2 前提条件へ据え置き
- **G9' (rep 単位 runner API):** rep index/status/argv/開始時刻を全件持つ新 runner API は、floor の
  session 有効性判定 (exact reps + throughputs 全件有限) には `throughputs` の列で足りる。exact reps
  束縛と欠測 fail-closed を protocol で締めれば足り、新 API は不要
- **B10' の共有 helper 即時是正:** 共有 `competing_bench_pids` の fail-open 是正は他 consumer への影響を
  持つため、floor driver は自前 strict probe を使い、共有 helper 是正は v2 前提条件リストへ (即時是正で
  他経路を壊さない)
- **G6' (再利用境界未定義。oracle driver 丸ごとの呼出しもコピペも不適切) — 即時是正は見送り、v2 前提
  条件へ据え置き:** 実装は G5' と同じ工数据え置きの原則の下、`s8b_floor_campaign.py:71,:1112` で
  `s8b_oracle_driver.prepare_cell` / `_prepared_binding` を import 再利用する経路を取った (oracle driver
  丸ごとの呼出しでも private helper のコピペでもない、G6' が示した二択の外側)。これは二重実装 drift
  (`docs/failures.md:32-34`) は避けるが、G6' が指摘した「oracle orchestration 全体への密結合が依存
  循環を作る」代償はそのまま残る — floor は oracle の gate/budget/schedule/marker 契約は呼ばないが、
  materialization の私有 helper 群 (`s8b_oracle_driver.py:227-275`) と cache root 差替え
  (`s8b_oracle_driver.py:604-648`) には結合したままである。公開された小さな共通モジュールへの抽出
  (variant binding 検証・cell materialization・binding identity・trace-disabled build) は「v2 前提条件
  として登録 (未実装)」へ追記した。本パッケージはこの must-fix を反映済みとも不採用とも記録せず脱落
  させていた点を、本注記と上記追記で是正する

## ユーザー裁定チェックリスト

F1〜F7 の各択 + 数値案。数値はすべて**案**であり、承認時に protocol JSON (機械正本) として凍結される。

| 裁定 | 択 | 数値案 (該当時) |
|---|---|---|
| **F1** floor protocol 本体 | (推奨) 12 セル per-pair `s8b-floor-stats/v1` / (代替) stock のみ 2 セル / scalar 契約 | `n_sessions=8`・`reps=5` exact・`2 block × replicates_per_block 4`・`min_block_gap_s=1800`・`wired_min_rel_floor=0.03` (3.0%)・scale band `±10%`・`master_seed=<要指定>` |
| **F2** 運用・停止・retry・resume | (推奨) 閉じた excluded 表 + strict probe + create-only WAL | `retry_slots_per_cell=2` |
| **F3** budget 導出・namespace | (推奨) 三層 namespace + 親 wall cap + verify ×96 正直計上 / (別裁定) 証明書 cell 再利用 | `N_oracle=8` 想定 (~11.6h verify prior、非拘束) / `bench_max_rounds=1` |
| **F4** 実行順序・情報遮断 | (推奨) 予測封印 → floor → 機械充填 → 承認 → oracle / env_tag 一致検査のみ | `env_tag=<ユーザー、承認時に確定>` |
| **F5** freeze v2 schema field | (推奨) top-level 維持 + per-pair table + transition table 分離 | — |
| **F6** 承認束縛方式 | (推奨 a) approval record + `AI-Agent: none` + active pointer / (代替 b) signed 鍵 | — |
| **F7** v2 検証意味論 | (推奨) git blob 照合 + launch certificate + 単一 `load_ratified_freeze` | — |
| 実行責任者・開始時刻 | **(ユーザー裁定側)** | — |

F1〜F7 がすべて得られても、floor 実走には env_tag 確定 (裁定 6 保留解除) と、oracle 実走には v2 machinery
(strict verifier・承認束縛・per-pair manifest 追随) の実装完了を要する。本パッケージは案であり、
ユーザー承認まで何も発効しない。
