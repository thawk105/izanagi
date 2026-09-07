# [T-2266] / [T-2313] 実測 tail で歩行 model を再走し、旧 model の指数外挿が tail を 20〜40 倍過小評価していたこと、それでも形状判定は動かないことを確定した

**すべて非認証である。** trace-disabled の性能測定と、それを入力にした model の再計算であり、直列性の検査を
通していない。variant 採用の根拠には使えない (絶対規律 2)。

## 0. 依頼と、実際に起きたこと

依頼は「着地済み opt-in mode で 3 workload を 3 job として同時投入し、完走後に歩行 model を実測 tail と
rep 単位 abort 率で再走して、旧 model の指数外挿との乖離を更新する」だった。

- **投入は行った。** 2026-09-05 13:18 JST、固定 checkout (local main 2632aed56) から
  `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2266-tail` で 978201 (write-heavy) / 978202 (balanced) /
  978203 (read-heavy) を gen_S へ投入した。receipt と job 出力は `/work/1/SFC/tanab/b10-backoff-grid-t2266-tail/`。
- **3 job とも build 前の測定条件関門で落ちた** (経過 90 秒、rc=1、stage `t2266_tail_sweep`)。
  `backoff_extended_sweep.py` の `_require_condition_gate_before_measurement` が呼ぶ
  `backoff_sweep.py` の `_require_backoff_condition_gate` が `BACKOFF_FIXED=red/preprocess-failed` を
  7 件 (固定 6 点 + adaptive) 返した。campaign WAL は 0 件、成果物は 0 件。
- **これは [T-2320] が直している既知欠陥 (第 2 層、関門文脈での masstree `config.h` 不在) である。**
  [T-2211] の再投入 (2026-09-04、2 job) も同じ理由で止まり、当時の worklog が「[T-2320] の着地を待つ」と書いていた。
  本件はその 3 例目である。[T-2266] の opt-in mode は着地時点で「測定はまだ走っていない」と明記されており、
  関門 (T-1999 / D1198、2026-08-26 の拡張格子走行より後に義務化) を一度も生で通していなかった。
- **再投入は本 wave では行わない。** [T-2320] wave の brief が「着地前に同 wave で T-2266 tail 3 job を再投入し、
  rep 単位値を `output/insights/2026-09-04_t2266-backoff-static-tail/` へ追記する」を含むことを、同 wave の
  job dir の brief.md で確認した。重複投入を避け、本 wave は [T-2313] (model 側) に絞る。

### 0.1 [T-2320] wave による再投入 (2026-09-07) — 関門は通ったが、別の 2 型で止まった

[T-2320] wave は修正込みの固定 SHA 0ade09d5e (detached submit-tree) から、同じ submitter で 3 job を
2 回投入した。出力親は `/work/1/SFC/tanab/b10-backoff-grid-runs6/`。いずれも当方は現物 (failure.json、
stderr、campaign 台帳) で確認した。peer session の報告はデータとして扱い、裁定には使っていない。

- **1 回目 (979596 / 979598 / 979599、02:22〜02:31 JST、group `…T172151Z-81318`):** 関門を通過して build が
  終わり、genome の commit が write-heavy 6 / balanced 6 / read-heavy 4 まで進んだところで、3 本とも同時刻
  (02:31:26〜29) に `patchharness.checkout` の後片付けが「`git worktree list` 失敗 (rc=128)」で止まった。
  各 job 自身の ccbench worktree の管理 dir (`…/.git/worktrees/submit-tree2/modules/…/worktrees/ccbench-source{,1,2}`)
  が消えていた。機構: worktree の本体は node ローカル `/scr` にあり、管理 dir は同じ submit-tree の submodule
  gitdir を 3 job (と同時に走っていた A-5 の 2 job) が共有する。同 SHA から走っていた A-5 write-heavy (979578) の
  終了処理 (`a5_second_boot_backoff_sweep.sh` の `git worktree prune --expire now`) が 02:31:24 に共有 gitdir を
  prune し、別ノードに本体がある残り 4 job の登録を「消えた」として削除した (発火点の特定は [T-2320] session)。
- **2 回目 (979703 / 979704 / 979705、02:36〜02:47 JST、group `…T173602Z-433694`、同 SHA、他 job 無し):**
  8 genome とも build (cache 命中)・verify (serializable、anomaly 0)・bench (5 rep、CV < 0.3%)・commit まで完走し、
  campaign 台帳に rep 単位 throughput (5 本) が残った。その直後の `materialize_t2266_report` →
  `_T2266RepCapture.reps_for` が「T-2266 adopted bench round lacks rep capture」で 3 本とも停止し、report は
  作られなかった。原因 ([T-2320] session が特定、当方の現物で整合): 凍結 view (`artifact_admission._deep_immutable`)
  が台帳の list を tuple、dict を `MappingProxyType` にするのに、突合が `list == tuple` で行われ必ず不一致になる。
  続く `type(indicators) is not dict` も同様に落ちる。unit test (`_t2266_certified_view`) は view を list / dict で
  手組みし、capture 自身の rounds から台帳を組み立てる同語反復だったため、実物の評価経路を一度も通していなかった。
  **t2266-tail mode が report 段に到達した実走はこれが初めてである。**
- rep 単位の abort 率は report にしか出ない (台帳の `leading_indicators.abort_rate` は 1 点 1 値)。producer の外で
  report を手組みすることはしない (規律 6・7)。
- **3 回目 (job 979843 / 979844 / 979845、修正 `2177b85aa`、2026-09-07 03:17 JST 投入) が完走した。**
  値は §4.1、測定そのものの正本は前 README §8 である。

## 1. 事前登録した補間規則 (2026-09-05 13:10 JST、結果を見る前に固定)

- R1: workload ごとの較正格子 = 既存 7 点 (0, 2, 5, 10, 25, 50, 100 µs; T-2216 の凍結 measured.json、静的セル 2 rep) +
  tail 6 点 (150, 200, 300, 500, 750, 999 µs; B-10 `t2266-tail` の 5 rep)。昇順に並べるだけで重み付け・再フィットをしない。
- R2: 各点の T と abort 率は全 rep の算術平均 (既存規則と同一)。
- R3: 点間の補間と 999 超の外挿は既存 scenario 規則 (EXACT = linear 補間、primary = 最後の 2 点からの指数 tail) をそのまま使う。
- R4: tail 走行の `none` と `adaptive` は較正に使わない。
- R5: 判定閾値・種・反復数・評価経路は変えない。
- R6: 「旧 model の指数外挿との乖離」は、旧 model (tail 無し) の T(b) 外挿値を 150 / 200 / 300 / 500 / 750 / 999 で評価し、
  実測 5 rep 平均との比を取る。
- R7: 混合仮定は検証しない。結論は「否定的結論が強まる / 弱まる / 変わらない」の 3 択で、既存判定 `status` をそのまま使う。
- (P1) 較正を 2 campaign (T-2216 静的 2 rep + B-10 tail 5 rep) から継ぎ合わせる。同一 job 内で 0〜100 µs も測り直す案は
  着地済み格子を変えるため scope 外。

## 2. 旧 model の指数外挿 (tail 無し) — R6 の左辺 (実測を見る前に計算)

出所: T-2216 wave の model 出力 `t2216_model_final.json` の `calibrations` (schema `izanagi-t2216-backoff-walk/v2`)。
最後の 2 点 (50 µs, 100 µs) の log 勾配で外挿した T(b) (tps)。

| b (µs) | write-heavy | balanced | read-heavy |
| --- | ---: | ---: | ---: |
| 150 | 1,902,344 | 1,433,048 | 3,503,981 |
| 200 | 1,537,983 | 1,101,021 | 2,763,894 |
| 300 | 1,005,255 | 649,928 | 1,719,652 |
| 500 | 429,463 | 226,467 | 665,701 |
| 750 | 148,333 | 60,629 | 203,272 |
| 900 | 78,384 | 27,497 | 99,760 |
| 999 | 51,451 | 16,317 | 62,364 |

参考: 2026-08-26 の B-10 拡張格子 (5 rep 中央値、別 job) との比は前 README §3.1 のとおり
write-heavy で 150 µs 1.08 倍、200 µs 1.20 倍、500 µs 3.04 倍、900 µs 13.21 倍。

## 3. 本 wave が実装したもの ([T-2313] の準備)

Codex author 1 本 (receipt `t2266-tail-s5-author-1`) で `tools/t2216_backoff_walk_model.py` に実測 tail の入力機構を足した。
統合 commit は `0ef73f882`。

- **CLI:** `--tail-json WORKLOAD=PATH` を 0 本または 3 workload (write-heavy / balanced / read-heavy) 各 1 本だけ受理する。
  1 本でも欠ける・重複する・`=` が無い・未知 workload は fail-closed。`allow_abbrev=False` にして、既存 test が要求する
  「`--tail` を受理しない」を新 option の接頭辞解釈から守った。
- **受理検査は構造で行い、bytes の pin は足していない。** schema `t2266-backoff-static-tail-report/v1`、`run_kind`
  `t2266-tail`、`status` complete、`workload` 一致、`source_measurement` trace_disabled、`performance_certified` false、
  `campaign_id` 非空、static 点の `realized_us` が exact に [150, 200, 300, 500, 750, 999]、点の kind が static / none /
  adaptive のみ、各 static 点の throughput と abort 率が 5 rep とも有限で throughput > 0・abort ∈ [0, 1]。
- **較正 (R1・R2):** 既存 7 点 (T-2216 凍結 `measured.json`、静的 2 rep) と tail 6 点 (5 rep の算術平均) を結合して
  昇順に並べ、workload ごとに 13 点にする。tail の none / adaptive は読むが較正へ入れない (R4)。補間・外挿・閾値・種・
  反復・評価経路は不変 (R3・R5)。
- **同一性:** 出力 `provenance.tail_inputs` に workload ごとの path・sha256・campaign_id・backoffs_us を記録し、
  再現 argv に `--tail-json` を含める。
- **tail 無しの出力は従来と同値。** calibrations / predictions / evaluation が旧経路と一致することを test で直接検査した。
- テスト: 正例 2 (13 点・順序・平均・provenance、tail 無しの同値) + 負例 12 + CLI 再現 1。author の自走 harness 53 pass、
  親の焦点走 (計算ノード、request 978654) 56 passed。

## 4. 実測 tail での再走

### 4.1 実測 tail (2026-09-07、job 979843 / 979844 / 979845、5 rep 平均)

[T-2320] wave が修正 commit `2177b85aa` から投入した 3 job が完走し、3 workload とも
`completion.json` (status complete) と report (`.dat` / `.json`) が出た。realized は
150 / 200 / 300 / 500 / 750 / 999 µs の 6 点、requested の 1000 µs は F718 のため unrealized
として理由つきで記録されている。write-heavy report の sha256 は
`d462e146b8b5d1fa804556225facd27f0d49975c81622c9922766f92170caada`。当方は 3 root の
`completion.json` と report を現物で検算した (schema / run_kind / status / workload /
source_measurement / performance_certified / realized_us / static 6 点 / rep 5 本)。

**測定そのものの正本は `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8 である**
(投入条件、campaign identity、3 report の sha256、rep 単位の生値、非静的 2 点)。本節はそれを
再掲するものではなく、**R2 が定める全 rep 算術平均**を載せる。§8.1 の median / 代表 abort 率とは
別の集約であり、値が一致しないのは正しい (例: write-heavy 150 µs は median 2,049,661 に対し
平均 2,049,534)。

| b (µs) | write-heavy tps | balanced tps | read-heavy tps |
| --- | ---: | ---: | ---: |
| 150 | 2,049,534 | 1,587,861 | 3,815,756 |
| 200 | 1,849,492 | 1,411,488 | 3,400,664 |
| 300 | 1,590,852 | 1,195,115 | 2,871,506 |
| 500 | 1,309,859 | 960,241 | 2,309,855 |
| 750 | 1,112,250 | 812,127 | 1,937,139 |
| 999 | 992,863 | 721,214 | 1,709,480 |

| b (µs) | write-heavy abort | balanced abort | read-heavy abort |
| --- | ---: | ---: | ---: |
| 150 | 0.1128 | 0.1453 | 0.0546 |
| 200 | 0.0976 | 0.1280 | 0.0486 |
| 300 | 0.0796 | 0.1061 | 0.0410 |
| 500 | 0.0610 | 0.0833 | 0.0327 |
| 750 | 0.0495 | 0.0679 | 0.0272 |
| 999 | 0.0424 | 0.0586 | 0.0237 |

### 4.2 R6 — 旧 model の指数外挿との乖離

事前登録どおり、旧 model (tail 無し) の外挿値を実測 5 rep 平均で割った。外挿規則は §2 と同じく
較正の末端 2 点 (50 µs, 100 µs) の log 勾配である。**この規則だけで再計算できる** — 旧 model の
`calibrations` と §4.1 の平均から直接出る。実際の算出は wave の job dir (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/compute-r6.py`)
で行い、その stdout を本 dir の `r6.txt` に置いた。解析 script 自体は repo へ入れていない。

| b (µs) | write-heavy | balanced | read-heavy |
| --- | ---: | ---: | ---: |
| 150 | 0.928 | 0.903 | 0.918 |
| 200 | 0.832 | 0.780 | 0.813 |
| 300 | 0.632 | 0.544 | 0.599 |
| 500 | 0.328 | 0.236 | 0.288 |
| 750 | 0.133 | 0.075 | 0.105 |
| 999 | 0.052 | 0.023 | 0.036 |

- **3 workload とも同じ向きで、旧 model は tail を大幅に過小評価していた。** 999 µs で外挿は実測の
  2〜5% しか出さない。150 µs 付近では 1 割以内の差でしかなく、b が伸びるほど比が単調に小さくなる。
- **実測の減衰は指数ではない。** 999 µs でも write-heavy は 992,863 tps = 100 µs 時点 (2,353,026 tps) の
  42% を保つ。balanced 39%、read-heavy 38%。指数外挿が予測した「消える」形にはならず、緩やかに下がって
  床へ近づく。前 README §3.1 が 2026-08-26 の中央値 (別 job、5 rep 中央値) から得ていた「900 µs で 13.21 倍」
  という乖離の向きと一致し、5 rep 平均でも 750 µs で 7.5 倍、999 µs で 19.3 倍 (write-heavy 換算) になる。
- **abort 率は 999 µs でも頭打ちにならない。** 3 workload とも単調に下がり続け、write-heavy は
  100 µs の 0.1374 から 999 µs の 0.0424 へ、まだ下降の途中である。tail の上端でも「abort を減らす」
  効果が飽和していないことを、rep 単位の値で初めて確認した。
- これは **R6 の左辺と右辺だけで確定する量**であり、歩行 model の再走を待たずに出せる。再走が担うのは
  R1 の 13 点較正と R7 の判定である。

### 4.3 R1・R7 — 13 点較正での再走

`tools/t2216_backoff_walk_model.py` を実測 tail 3 本つきで再走した (2026-09-07、計算ノード、
job 980043、所要 約 76 分)。出力は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/results/t2216_model_tail.json` (3.8 MB)、比較は同 job dir の
`compare-tail.py` と `inspect-predictions.py` で行い、後者の stdout を本 dir の `r7.txt` に置いた。`provenance.tail_inputs` には 3 report の path・sha256・
campaign_id・backoffs_us が入り、sha256 は §4.1 の値と一致する。

- **R1 の較正は事前登録どおりに組まれた。** 3 workload とも既存 7 点の座標と値が bit 単位で不変のまま、
  tail 6 点が末尾へ昇順で加わって 13 点になった (比較 script が assert で検査した)。
- **R7 の判定は変わらない。** 形状ゲート 4 本すべてが合否を保ち、順位統計も同一である。

| ゲート | 旧 (tail 無し) | 新 (13 点) |
| --- | --- | --- |
| A_stage1 | 不合格、kendall 距離 6 (上限 2) | 不合格、kendall 距離 6 |
| A_d1475 | 不合格、kendall 距離 10 (上限 3) | 不合格、kendall 距離 10 |
| B_flattening | 合格、比 1.1089 (上限 1.5) | 合格、比 1.1089 (完全同一) |
| C_valley | 不合格、相対誤差 1.3031 | 不合格、相対誤差 1.2769 |

- **動いた量は小さい。** 214 件の予測のうち変わったのは 61 件 (write-heavy 13 条件、balanced 7、
  read-heavy 2、step 幅 0.5〜100 µs)。rep 単位 throughput の相対変化は中央値 −0.14%、絶対値の最大 41.9%
  で、ゲートが読む predicted_mean_tps の動きは 2% 以内 (最大は A_stage1 の 100 µs で +1.77%)。
  B_flattening が読む条件は 1 件も変わらなかった。
  **(2026-09-07 追記) 上の 1 文は数え方を 2 つ使っている。** 「61 件」は prediction
  (workload × scenario × condition) を数えたもので、「write-heavy 13 条件、balanced 7、
  read-heavy 2」は相異なる (workload, condition) を数えたもの (合計 22) である。1 つの条件が
  複数の scenario に現れるため 61 > 22 になる。rep 統計 (中央値 −0.14%、絶対値の最大 41.9%、
  および下の 488 本) の母集合は、変化した 61 予測の rep 61 × 8 = 488 本である。値は
  `output/insights/2026-09-07_t2313-13pt-audit/` の独立検算で 1 つ残らず再現した。
- **なぜ較正が 20〜40 倍変わって判定が動かないのか。** 試した step 幅では歩行が大きな backoff 域に
  ほとんど滞在しないためである。100 µs 超の滞在確率は 488 本の rep のうち 147 本で下がり、平均は
  0.1152 から 0.1074 へわずかに減った (中央値は 0.0380 → 0.0623 と上がっており、条件によって向きが違う)。
  **したがって R7 の結論は 3 択のうち「変わらない」である。ただし否定的結論の足場は外挿から実測へ移った。**
- **再走の所要時間そのものが tail 補正の傍証である。** `_simulate_condition` は 3 秒分
  (`DURATION_US`) を leader period 刻みで進める while ループで、刻み幅は throughput から決まる。旧 model は
  tail で throughput が指数的に消えたので大 backoff 域の刻みが粗く、7 点較正の全走が 728 秒で終わっていた。
  実測 tail では刻みが細かいままとなり、13 点較正では 40 分の walltime でも完走せず、76 分を要した。
  **事前登録した閾値・種・反復・評価経路 (R5) は一切変えていない** — 増えたのは反復回数だけである。

## 5. 確定していないこと

- **機序は未検証である。** なぜ実測 tail が指数的に消えず床へ近づくのか、混合仮定 (前 README §5) が
  成り立つかは、本 wave では検証していない。R7 も混合仮定を検証しない前提で事前登録してある。
- **1000 µs は依然として測定不能である。** F718 の符号化により固定 0 へ復号されるため、999 µs は代替であって
  6 点目ではない。tail の上端が真に 999 µs なのか、それ以遠に別の挙動があるのかは言えない。
- **abort 率が 999 µs でも頭打ちにならない理由は分からない。** 単調下降が続いていることは実測できたが、
  どこで飽和するかは格子の外である。
- **判定が動かなかったことは「tail が model にとって無関係」を意味しない。** 試した step 幅で歩行が
  大 backoff 域に滞在しないことの帰結であり、滞在させる条件 (より大きい step、より長い duration) は
  事前登録の外なので試していない。

## 6. 変異 matrix

対象は `tools/t2216_backoff_walk_model.py` の tail 入力機構。runner は `python3 tools/run_tests.py
orchestrator/tests/test_t2216_backoff_walk_model.py -q -rf --force-dispatch` (計算ノード、dispatch mode)。
2 段で走らせた: probe (全件 SURVIVED 登録で failed node を収集、台帳 `mutation-probe-out3.json`) → 本走
(観測 node を期待値に焼き込んだ spec、sha256 `5a65b22b1e11763394da31287726013c67aaf7935b54cfe4a9ec9cf9c43dd526`、
台帳 `mutation-final-out.json`、HEAD `0ef73f882`)。本走の結果は **KILLED 10 / SURVIVED 1、期待一致 11/11**。

| ID | 変異 | 結果 | 殺した test |
| --- | --- | --- | --- |
| M01 | realized_us の exact 検査を外す | KILLED | `…rejects_realized_1000_instead_of_999` |
| M02 | throughput の平均を中央値にする | KILLED | `…uses_six_sorted_rep_means_and_provenance` |
| M03 | tail を読むが較正へ足さない | KILLED | 同上 |
| M04 | workload 一致の検査を外す | KILLED | `…rejects_workload_field_mismatch` |
| M05 | rep 数 5 の検査を外す | KILLED | `…rejects_four_throughput_repetitions` |
| M06 | schema_version の検査を外す | KILLED | `…rejects_schema_version_mismatch` |
| M07 | 3 workload 揃わなくても受理する | KILLED | `…inputs_reject_missing_workload` |
| M08 | provenance の sha256 を落とす | KILLED | `…uses_six_sorted_rep_means_and_provenance` |
| M09 | 結合後の昇順 sort をやめる | KILLED | 同上 |
| M10 | abort 率の上限 1.0 の検査を外す | KILLED | `…rejects_abort_rate_above_one` |
| EQ | `list(TAIL_BACKOFFS)` → `[*TAIL_BACKOFFS]` (等価) | SURVIVED (期待どおり) | — |

probe の経緯: 1・2 回目は gen_S の混雑 (QUE 147 / RUN 35) で collection 段の queue 待ち 900 秒 (harness には
D612 上書きが届かない、F762) に掛かり rc=16。3 回目で collection と baseline が通り、M02 の走行が rc=16 で
PARSE_ERROR となって停止。`--resume` で M02 から再開し完走 (PARSE_ERROR 1 件は台帳の履歴へ退避)。

## 7. 再現条件

すべて**非認証**である (trace-disabled の性能測定と、それを入力にした model の再計算。直列性の検査は通していない)。

### 7.1 本 wave の投入 (関門で停止、成果物 0)

| 項目 | 値 |
| --- | --- |
| 投入 checkout | local main 2632aed56 (detached)、submodule 初期化済み、freeze digest c405c742… |
| 投入 script | `tools/pegasus/submit_b10_backoff_grid.sh --run-kind t2266-tail` (job body sha256 bc340672…) |
| job | 978201 / 978202 / 978203 (gen_S、2026-09-05 13:18 JST 投入、13:19〜13:21 JST 終了) |
| 失敗 receipt | `<出力親>/b10-backoff-grid-20260905T041811Z-3016630-<workload>.failure.json` |
| ビルド | 到達せず (関門で停止)。到達していれば trace-disabled、perf 無し |

### 7.2 採用した実測 tail ([T-2320] wave が投入)

| 項目 | 値 |
| --- | --- |
| 投入 checkout | 2177b85aa8cf1877f11be3e0adf6e4c8751646c6 (detached、他 job 無し) |
| job | 979843 (write-heavy) / 979844 (balanced) / 979845 (read-heavy)、2026-09-07 03:17 JST 投入 |
| 出力親 | `/work/1/SFC/tanab/b10-backoff-grid-runs6/b10-backoff-grid-20260906T181718Z-1158057-<workload>` |
| report sha256 | write-heavy `d462e146…`、balanced `5ad6f095…`、read-heavy `66bc3195…` |
| 正本 | `output/insights/2026-09-04_t2266-backoff-static-tail/README.md` §8 |

### 7.3 model の再走

| 項目 | 値 |
| --- | --- |
| commit | dac508a5b (本 wave、main 9194bfef8 取り込み後) |
| job | 980043 (gen_S、2026-09-07 08:35 JST 投入、09:55 JST 完了、所要 約 76 分、walltime 04:00:00) |
| argv | `python3 tools/t2216_backoff_walk_model.py <measured.json> <backoff.hh.txt> <out> --tail-json write-heavy=… --tail-json balanced=… --tail-json read-heavy=…` |
| 入力 pin | measured.json `f46cebdd…`、backoff.hh.txt `3e9f5485…` (model が定数で pin) |
| 出力 | `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2266-tail-measure/results/t2216_model_tail.json` (3.8 MB)。比較 script は同 job dir、stdout は本 dir の `r6.txt` / `r7.txt` |
| 比較対象 | T-2216 の `results/t2216_model_final.json` (2026-09-02 生成、tail 無し) |
