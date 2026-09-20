# S-1a (合成軸 = 系側 gate 構成 `g_rl` / `g_rt` 対 既知軸最良 3 種) の直接比較 9 対の結果節 — 登録追試 S-1 (2026-07-16) の family 判定は不成立 (2026-09-20)

**これは投稿本文ではない。** 論文の結果節・表・限定へ落とすための、一次資料に束縛した執筆者向けの日本語統制稿である。
D12 が定める機械射影の材料レポートではない (数値は一次資料から転記し、散文は執筆者の判断を含む)。
英語化のときは事実命題を足さず、本稿の表と一次資料へ再照合する。

**この文書は `results/` 系列の凍結物である。** 書いた後は更新しない。規則は `docs/paper-story/README.md` の
「results 系列」節が正本である。

**本稿は同系列の既存の稿を改めるものではなく、版・図の README を出所にもしない。** S-1a の 9 対は論文ストーリー版
(`docs/paper-story/2026-08-26.md` 以降の各版の §4 と §8 B-1) と `figures/README.md` の fig4 節に要約されているが、
それらは版・図の文書であって、S-1 という 1 つの登録追試の一次資料全体から作った結果節ではない。**本稿は版・README・
stale 注記を数値・判定の出所にしていない。** 出所は §5 に挙げる一次資料だけである。S-1a の単独 results 稿は本稿が最初で、
台帳 ID は未起票である (2026-09-20 時点)。

---

## 0. 位置づけ — 本稿が判定しないことを先に置く

**本稿が判定しないこと。**

- 研究として成功か失敗かの宣告 (D12)。S-1a の「不成立」は事前登録が定めた family 判定の出力であって、研究の失敗宣告ではない。
- 合成 (系側 gate 構成) が無価値であること。既知軸集合は「単軸最良の凍結集合 = 合成未探索の下界」であり (§1.1、§3.3)、
  それを超えなかったことは合成の価値の否定ではない。**「既知軸最良を超えなかった」を「合成が無価値」と読まない。**
- 新しい否定的発見。S-1 は既知結果を見た後に登録された追試であり (事前登録の HARKing 境界、§1.1)、S-1a の不成立は
  「結果既知の追試として登録した複合主張が、測ってみたら成立しなかった」型の失敗報告である。
- S-1a の 6 対のマージン (最大 −55.1%) が合成で埋まりうる規模かどうか。事前登録はその議論を報告義務にしているが、
  本稿は数値を出すだけで議論を判定しない (§3.3)。
- 既知軸最良に対する敗因の機序。abort 率・LLC miss 率・IPC は WAL にあるが、本稿は機序を同定しないので転記しない (§4 限定 16)。
- 現行環境 (Pegasus、CCBench pin `511c953` + patch) での同じ比較の結果。本稿の値は旧環境 `linux-baremetal`・CCBench
  `d706650`・`perf stat` 下の 2026-07-16 の値であり、A-2 / A-6 / [T-1998] / B-7 / A-1 / B-10 / 検証相のどれとも
  比較ではない (§3.6)。
- 適格率次元 (S-2 / S-3) の判定。本稿は必須の併記 (§3.2) だけを行い、S-2 / S-3 の確定文言には作用しない。
- S-1b (同じ report の別 family) の結果節。§3.1 に関係だけを書く。

**書くもの:** 凍結 report `output/reports/s1_direct_comparison/report.json` が持つ S-1a family の 9 比較行
(`judgment`・`gates`・`p_perm`・`p_star`・`effect_sizes`・`unstable_counts`・`block_effects`・`retry_events`) と
`families.s1a`・`hard_gates`・`budget`、fig4 の provenance JSON が同じ 4 campaign の WAL から再計算した 12 cell の
8 標本・中央値・平均・95% 信頼区間、S-1 計測 freeze が定める 18 cell の構成と 9 対の定義、事前登録が定める判定規則、
2026-07-16 に人間承認された Holm 族 4 判定表の中での S-1a の位置、実行 identity、限定の一覧。

**実施回数と主張範囲を分ける。** 本稿の凍結資料に記録された S-1 の本走は **1 回** (develop / floor / block1 / block2 の 4 campaign、
2026-07-16 JST、旧環境) で、第 2 の本走や別環境での再測はこれらの資料から特定していない (§3.7)。主張範囲は **登録した 9 対の
family 判定 (S-1a) のみ**であり、9 対のうち成立した 3 対 (対 `sort_best`) を単独の主張にしない。

**主判定文 (結果節へ落とすときの形。文を分けたまま使う):** S-1 登録追試 (2026-07-16、旧環境 `linux-baremetal`) の直接比較
9 対では、系側 gate 構成 `g_rl` / `g_rt` の中央値は `sort_best` に対して 3 workload とも +55.5%〜+98.4% で判定境界 +3% を
超えたが、`p2_2_flag_opt` に対して −9.3%〜−55.1%、`backoff_fixed_best` に対して −36.0%〜−51.9% で超えず、家族連言
(9 対すべて成立) を満たさないため **S-1a は不成立**である (family p = 1.0)。これは結果既知の事前登録付き追試の出力であり、
新しい否定的発見でも、合成が無価値であることの証明でもない。必須の併記を原文のまま添える — 確定文言 §3 付記:
「S-1 が成立しても適格率次元の発見再現性は未実証のままであり、報告ではこの限界を S' に併記する」。S' 最終報告 §4:
「適格率次元の発見再現性は未実証のままである (S-1b の成立はこの限界を解消しない。S-1a が不成立となった今回、性能次元でも
『既知軸最良の超越』は実証されていない)」。

---

## 1. 何を測ったか

### 1.1 事前登録と主張の性格 (HARKing 境界)

S-1 は `docs/phase3-main-experiment.md` の 2026-07-12 追記 (D52、headline 主張の系レベル再構成) で登録され、2026-07-15
追記 (S-1 サンプル設計 4 点、ユーザー承認 2026-07-15) で数値が確定した。主張 S の分解のうち **S-1a = 系レベル発見優越**
(対象軸 = trigger-gating 1 本に事前固定、交絡許容の系主張) が本稿の対象である。

事前登録は改訂時点の既知結果台帳 (HARKing 境界) を明記している — 「本改訂は D50 偵察 (+61〜99% cross-run)・F 段 iteration
1〜2・axis-proposer n=1 採点・既知軸側全実測を**見た後**に行われた。S-1 = 結果既知の『事前登録付き追試』(confirmatory と
呼ばない限定表現義務)」。2026-07-15 追記も「S-1 は結果既知の登録追試 (confirmatory と呼ばない)・対象軸 n=1 という限定は
不変」と再掲する。

既知軸集合の定義は「既知軸集合 (2026-07-12 凍結、以後追加しない) = P2-2 フラグ最適 / BACKOFF_FIXED grid 最良 / sort 全列挙最良」
で、主張 S の本文はこれを「既知軸集合の実測最良 (単軸最良の凍結集合 — 合成未探索の下界)」と呼ぶ。既知限界として
「既知軸集合はリポジトリ探索履歴依存の凍結有限集合 (合成未探索の下界 — S-1a のマージンが合成で埋まりうる規模かの議論を
報告義務化)」が登録されている。失敗条件 (c) 系レベル版は「S-1a が既知軸実測最良と floor 以下の差 → 軸発見の固有価値なし
(判定不能はそのまま報告)」である。

### 1.2 18 cell と 9 対の定義 (S-1 計測 freeze)

`output/s1-freeze/measurement_freeze.json` (「S-1 計測 freeze v2 (18セル・比較対・schedule・実装 hash)」、`frozen_at_head`
`2066ce6b47c6a5d43ca2c8ab3cc7728d32336be1`、`ccbench_pin` `d706650`、`master_seed` 20260715、`schedule_hash`
`b76333da5db1945908641679773bf7ef307ac2dc2bb3462a171b15be235ae150`) が 3 workload × 6 構成 = 18 cell を定める。
動作点は `RECORDS` 1,000,000 / `THREADS` 48 / `EXTIME` 3 / `REPS` 5、workload は `ycsb_rratio` 5 (write-heavy) / 50
(balanced) / 95 (read-heavy) だけが異なる。共通 flag は `NO_WAIT_LOCKING_IN_VALIDATION=1`、`NO_WAIT_OF_TICTOC=0`、`WAL=0`
(read-heavy の `p2_2_flag_opt` だけ例外、下表)。

| 構成 | balanced | write-heavy | read-heavy | 役割 |
|---|---|---|---|---|
| `system_gate` (合成軸、比較の左側) | `g_rl`: `BACK_OFF=1`, `BACKOFF_TRIGGER_GATING=1`、gate 述語 = abort 理由が `kUnset` または `kReadValiLocked` のとき backoff を発火 | `g_rt`: 同 flag、gate 述語 = `kUnset` または `kReadValiTid` | `g_rl` (balanced と同じ) | D50 の workload 別勝ち gate に事前固定 |
| `p2_2_flag_opt` (既知軸 1) | variant `5185ee5e6094`、label `B0-L-W0`: `BACK_OFF=0` | 同左 | variant `b971a1d9f80a`、label `B0-T-W0`: `BACK_OFF=0`, `NO_WAIT_LOCKING_IN_VALIDATION=0`, `NO_WAIT_OF_TICTOC=1` | P2-2 全列挙の argmax |
| `backoff_fixed_best` (既知軸 2) | `BACK_OFF=1`, `BACKOFF_FIXED=5` (5 µs) | `BACKOFF_FIXED=10` (10 µs) | `BACKOFF_FIXED=2` (2 µs) | backoff sweep の argmax |
| `sort_best` (既知軸 3) | `sp_dd`: `BACK_OFF=1`, `SORT_VARIANT=1`、comparator は `storage_` 降順・同点は `rcdptr_` 降順 | `sk_ad`: `storage_` 昇順・同点は `key_` 降順 | `sk_ad` (write-heavy と同じ comparator) | sort 全列挙の argmax (選定履歴は §4 限定 9) |
| `ident_all` (S-1b 対照) | `g_rl` と同じ flag、gate 述語 = 6 つの abort 理由すべてで発火 | 同左 | 同左 | S-1a の対には含めない |
| `stock_common` (文脈) | `BACK_OFF=1` のみ (CCBench `Options.cmake` の既定) | 同左 | 同左 | freeze の注記「stock_common は併記用の文脈セルであり、検定比較対には含めない。」 |

freeze の `comparisons` は 12 行 (S-1a 9 行 + S-1b 3 行) で、S-1a の 9 行はすべて `left_cell` = `<workload>:system_gate`、
`right_cell` = `<workload>:{p2_2_flag_opt, backoff_fixed_best, sort_best}`、`alternative` = `greater` である。
**S-1a の問いは「合成軸の中央値が既知軸最良の中央値を判定境界を超えて上回るか」を 9 対それぞれに問い、9 対すべてで成立する
ことである。**

### 1.3 判定規則 (事前登録 層 2 を report が実装)

事前登録 2026-07-15 追記 層 2「スクリーニングの gate 連言化」と層 1 (iii) の規則を、`orchestrator/campaign/s1_report.py`
(report 生成時) が実装した。本稿は report の出力を読むだけで再計算しない。

- **gate (1):** 相対中央値差 (= 左 cell の中央値 / 右 cell の中央値 − 1) の点推定が `floor_cmp` を**厳密に**超える。
  `floor_cmp` = max(floor campaign での当該比較両側 cell の between-session CV, 3.0%)。floor campaign の標本だけから計算し、
  検定標本 (block1 / block2) を使わない。9 対とも `floor_cmp` = 0.03 (report の `floor_cmp`、両側の floor CV はいずれも
  3.0% 未満、§2.3)。
- **gate (2):** 2 campaign ブロック (block1 / block2) の間で差の方向が一致する (cross-run 再現)。
- **p\*:** gate (1)(2) を両方通れば p\* = p_perm、いずれか不通過なら p\* = 1。p_perm は層別 exact permutation
  (ブロック内の割付数を保存する全列挙 = C(8,4)² = 4,900 分割、片側、主統計量 = 層別 rank-sum、tie は tail 包含)。完全分離時の
  p = 1/4,900 = 0.000204082。
- **family:** S-1a = 9 比較の p\* の max (intersection-union、α inflation なし)。9 対すべて成立で family 成立。
- **α:** report は Holm 第 1 段の α = 0.0125 を**参考値**として `reference_alpha` に持ち、`judgment_basis` =
  `reference_alpha_only_not_holm_family4_adjudication`、`holm_family4_adjudication` = `not_performed_human_or_future`
  と自ら記録する。Holm 族 4 (S-1a / S-1b / S-2 / S-3) 全体の裁定は 2026-07-16 に人間が行った (§2.6)。
- **三値判定:** 判定不能の発火条件 (retry 上限超過による n 未達、総予算 12 h 超過、freeze / schedule / certified 照合の失敗、
  `floor_cmp` 入力の欠測) はいずれも発火していない (§1.5)。
- **効果量:** 中央値差・確率優越 A・cell CV は併記であって判定には使わない。
- **検定力:** N = 8 は「p 値解像度の確保 (完全分離時に Holm 全段を通る + 少数の順位交差への耐性)」を根拠とする設計であり、
  事前登録は「**prospective power は未保証と明記する**」と定める (層 1 (iii))。完全分離時の最小 p 値 1/4,900 は検定力の保証ではない。
  「事後の『判別力再評価』は行わない — N=8 完走時は常に p\*・効果量・CV を報告し、判定不能の発火は層 2 の機械条件のみ」。

### 1.4 実行 identity

| 項目 | 値 | 出所 |
|---|---|---|
| 環境タグ | `linux-baremetal` (旧環境。現行の Pegasus ではない) | 4 campaign の WAL 全行の `env_tag`、provenance `measurement_conditions.env` |
| CCBench commit | `d706650` (現行 pin `511c953` ではない) | campaign.lock の `ccbench_commit`、freeze の `ccbench_pin` |
| trial / spec | `s1-direct-v2`、`spec_content` = 「S-1 登録追試の計測実行系。freeze の18セルと固定 schedule を pipeline.evaluate の COMMIT 唯一経路で実行する。」、`search_config.verify` = `legacy` | block1 の campaign.lock |
| campaign (正典 4 件) | develop `s1-direct-develop-direct-comparison-d0f495bf` (18 session)、floor `…-floor-…-b82b9229` (144)、block1 `…-block1-…-74ff9ba2` (72)、block2 `…-block2-…-9645b16a` (72) | report の `hard_gates.schedule`、provenance `inputs` |
| campaign 開始 (UTC、report) | develop 2026-07-15T16:31:06.667567、floor 17:36:17.226403、block1 19:49:16.446864、block2 21:26:58.960473 | report の `hard_gates.schedule.<role>.campaign_started_at` |
| WAL の先頭〜末尾 (JST、本稿で換算) | develop 2026-07-16 01:31:06〜02:35:00、floor 02:36:17〜04:48:43、block1 04:49:16〜05:55:39、block2 06:26:58〜07:32:52 | 各 WAL の `ts` の最小・最大 |
| WAL の行数と段 | develop 127 行 (`s1-session` 37、`build_start` 18、`build_done` 18、`verify_done` 36、`commit` 18、`bench_done` 0)。floor 1,009 行 (`s1-session` 289、build 144 + 144、`verify_done` 144、`bench_done` 144、`commit` 144)。block1 / block2 各 505 行 (`s1-session` 145、build 72 + 72、`verify_done` 72、`bench_done` 72、`commit` 72) | 各 WAL (本稿の執筆時に数えた) |
| session の結果 | 4 campaign とも全 session が `attempt` 0、`session-result` は `status=success` / `reason=certified` (develop 18、floor 144、block1 72、block2 72) | 各 WAL の `s1-session` 行 |
| toolchain / 性能 build | `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF -DCMAKE_C_COMPILER=gcc-13 -DCMAKE_CXX_COMPILER=g++-13`、**`-DCCBENCH_TRACE=0`** (306 build 全件で同一)。build は `trace_bin` と `perf_bin` の 2 本で、develop (正典 v2) の 18 build は 15 件が `trace_cached = perf_cached = true`、3 件が `false` (新規 build)、floor / block1 / block2 の 288 build は全件 `true` (先行 build の再利用) | 各 WAL の `build_done.perf_configure_cmd` ほか |
| 性能 run の argv | `numactl --interleave=all perf stat -e LLC-load-misses,LLC-loads,instructions,cycles -- …/ycsb_silo.exe -thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -clocks_per_us=1800 -ycsb_zipf_skew=0.9 -ycsb_rratio={5,50,95} -ycsb_rmw=0` (288 `bench_done` 全件で、`…` の binary path (variant ごとの build cache dir) と `rratio` を除く引数が同一) | 各 WAL の `bench_done.run_cmd` |
| 1 標本 | 1 session = `REPS` 5 反復の中央値 (`bench_done.median_tps` = `commit.fitness_tps`)。`bench_done` は全件 `unstable = false`、`high_variance = false`、`rounds = 1` | 各 WAL |
| 正しさ検査 | trace-enabled build の別走行。floor / block1 / block2 は session ごとに `verify_done` 1 件 (`workload.tag` = `legacy`)、develop は cell ごとに 2 件 (`legacy` と `s2`)。全 324 件が `verdict = serializable`、`certified = true`、`anomalies = 0` | 各 WAL の `verify_done` |
| variant と `src_token` (block1 の `build_start`) | `g_rl` = `d1e92d85ba65` (`4608a96ecda4a7799bbb61ea49d219196b069a4dcb555c1d3cfb524c9656afe6`)、`g_rt` = `e932c4502198` (`ff0e2dd53b5a24457cae5bfc8bfbc93b50f2967f4ca7e9c5af1a8740cbb7fc3b`)、`ident_all` = `97cf65d3d89e`、`p2_2_flag_opt` = `5185ee5e6094` (balanced / write-heavy) と `b971a1d9f80a` (read-heavy) (いずれも `src_token` = `stock`)、`backoff_fixed_best` = `6d6907b6f827` (balanced) / `d71cb6f1ef53` (write-heavy) / `fdbbbfb602a2` (read-heavy)、`sort_best` = `9f0174fd03dc` (balanced) / `fce171c04c87` (write-heavy と read-heavy)、`stock_common` = `db4764543546` (`stock`) | block1 の WAL、report の `accepted_evidence` |
| report | `generated_at_head` `24202e270782a58343ef016592c1a4ae767ee0ce`、`freeze_ref.sha256` `5c719c076e17f385a781933c081bf02abcd85b9edb01ad8c50a37740c134a191` (§3.4) | report.json |
| 時間台帳 | `total_budget_s` 43,200、`spent_s` 22,943.711507913657 (≈ 6.37 h)、`remaining_s` 20,256.288492086343、phase 別 develop 7,061.066371955909 / floor 7,946.350974834524 / block1 3,983.106109729968 / block2 3,953.1880513932556、`retry_spent_s` 120.65006890986115、`preflight_refusals` 空 | report の `budget`、`output/s1-budget/time_ledger.json` |
| 検証相校正 | read-heavy × `g_rl` の trace-enabled build で extime {3, 6} s を各 1 回実測し、extime = 3 s に確定 (事前登録 2026-07-16 追記) | `output/env/linux-baremetal/calibration/s1_verify_extime.json` / `.md`、事前登録 |

**develop 相には正典でない campaign がもう 1 つある (v1)。** `output/campaigns/s1-direct-develop-direct-comparison-7bccdf1a`
は tracked だが、report の accepted develop 18 件に対応せず、provenance の `inputs` にも入っていない。v1 の WAL
(sha256 は §5.1) は 151 行で、`s1-session` 58 (`campaign-start` 1 = 2026-07-15T15:36:15.424828Z、`session-start` 24 =
attempt 0 が 18 + attempt 1 が 3 + attempt 2 が 3、`session-result` 27、`retry` 6)、`build_start` 24、`build_done` 15、
`verify_done` 30、`commit` 15、`abort` 9 を記録する。build-error の `schedule_index` 3 / 9 / 15 はそれぞれ
`balanced/backoff_fixed_best` / `write-heavy/backoff_fixed_best` / `read-heavy/backoff_fixed_best` で、各 attempt 0・1・2 が
`status=retryable reason=build-error`、attempt 2 の後に `abandoned` (`retry上限/非retryable: build-error`) と記録されている
(`abort` 行の `error` は `-Werror=unused-variable` による build 失敗)。時間台帳の develop 相 44 entries (session 36 = attempt 0 が
18 + 18、`machine-failure-retry` 6、`campaign-overhead` 2) はこの v1 と正典 v2 の両方を含み、retry 6 件の `index`・`attempt`・
`reason`・時刻は v1 の WAL の記録と整合する (§2.7)。trial を v1 → v2 に版上げして v2 で 18 / 18 が通った経緯 (F19) は worklog
2026-07-16 (1) による。**v1 の WAL は本節と §2.7 の v1 に関する記述の出所であり、9 対の数値・判定の出所ではない。**

### 1.5 hard gate の記録 (report の `hard_gates`、全項 `pass`)

| gate | scope | status | 記録値 |
|---|---|---|---|
| `freeze` | all | pass | `reasons` 空 |
| `schedule` | develop / floor / block1 / block2 | pass ×4 | `expected_sessions` 18 / 144 / 72 / 72、`recorded_attempt_starts` = `recorded_initial_starts` = 18 / 144 / 72 / 72、`next_index` 18 / 144 / 72 / 72、`recorded_sessions` は 4 role とも 0 (field 名のまま転記、本稿は意味を解釈しない)、`reasons` 空 |
| `certified` | samples | pass | `accepted_samples` develop 18 / floor 144 / block1 72 / block2 72、`rejected_or_unbound_commits` 4 role とも 0、`issues` 空。`accepted_evidence` は role ごとに `role`・`schedule_index`・`cell_id`・`variant_id`・`src_token`・`fitness_tps`・`verify_configs`・`unstable` を列挙 (develop の 18 件は `verify_configs` `["legacy", "s2"]` で `fitness_tps` は null、floor / block1 / block2 の 288 件は `["legacy"]` で `fitness_tps` は数値) |
| `sample_counts` | cells | pass | 18 cell すべて develop `expected_n` 1 = `actual_n` 1、floor 8 = 8、block1 4 = 4、block2 4 = 4 |
| `budget` | incomplete comparisons | pass | §1.4 の時間台帳、`reasons` 空 |

---

## 2. 結果

### 2.1 9 対 — 6 対が gate (1) を通らず、S-1a は不成立 (family p = 1.0)

左 = `system_gate` (合成軸)、右 = 既知軸。中央値は各 cell の 8 標本 (block1 4 + block2 4) の中央値 (provenance の
`facts.comparisons[].left_median_tps` / `right_median_tps`)。相対中央値差は report.json の `relative_median_difference`
(全桁) と、その百分率を小数第 1 位に丸めたもの (fig4 の caption と同じ丸め)。

| workload | 右 cell (既知軸) | 左 median (tps) | 右 median (tps) | 相対中央値差 (report 全桁) | 同 (%) | 中央値差 (tps) | gate (1) `passed` | gate (2) `passed` (block 符号) | 判定 | `p_perm` | `p_star` |
|---|---|---:|---:|---:|---:|---:|---|---|---|---:|---:|
| write-heavy | `p2_2_flag_opt` | 1,689,666.5 | 1,863,839.5 | −0.09344849704065183 | −9.3 | −174,173.0 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| write-heavy | `backoff_fixed_best` | 1,689,666.5 | 2,639,678.5 | −0.35989685865153653 | −36.0 | −950,012.0 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| write-heavy | `sort_best` | 1,689,666.5 | 1,086,580.5 | 0.5550311274682364 | +55.5 | 603,086.0 | true | true ([1, 1]) | 成立 | 0.00020408163265306123 | 0.00020408163265306123 |
| balanced | `p2_2_flag_opt` | 1,705,405.0 | 2,723,265.0 | −0.3737645803842079 | −37.4 | −1,017,860.0 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| balanced | `backoff_fixed_best` | 1,705,405.0 | 3,078,552.0 | −0.4460366432010893 | −44.6 | −1,373,147.0 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| balanced | `sort_best` | 1,705,405.0 | 929,335.0 | 0.8350809987786966 | +83.5 | 776,070.0 | true | true ([1, 1]) | 成立 | 0.00020408163265306123 | 0.00020408163265306123 |
| read-heavy | `p2_2_flag_opt` | 3,803,639.0 | 8,474,516.5 | −0.5511674323839006 | −55.1 | −4,670,877.5 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| read-heavy | `backoff_fixed_best` | 3,803,639.0 | 7,906,185.5 | −0.518903395322561 | −51.9 | −4,102,546.5 | false | true ([−1, −1]) | 不成立 | 1.0 | 1.0 |
| read-heavy | `sort_best` | 3,803,639.0 | 1,916,834.0 | 0.9843340633565556 | +98.4 | 1,886,805.0 | true | true ([1, 1]) | 成立 | 0.00020408163265306123 | 0.00020408163265306123 |

- gate (1) の `required_strictly_greater_than` は 9 対とも 0.03。落ちた 6 対はすべて gate (1) 不通過で、gate (2) は 9 対とも
  通過している (`pooled_direction_sign` と `block_direction_signs` が一致)。したがって **6 対の負けは 2 ブロック間で方向が
  一致した負けである** — これは cross-run 再現の観測であって、機序の説明ではない (§4 限定 8)。
- 9 対の `reasons` は空、`unstable_counts` は floor / block1 / block2 とも左右 0、`retry_events` は空 (§2.7)。
- **family:** `families.s1a` = `judgment` 不成立、`p_family` 1.0、`reference_alpha` 0.0125、`reference_below_alpha` False、
  `judgment_basis` `reference_alpha_only_not_holm_family4_adjudication`、`holm_family4_adjudication`
  `not_performed_human_or_future`、`reasons` 空。`comparison_ids` は上の 9 件。
- 成立した 3 対の `p_perm` = 1/4,900 (完全分離) で、いずれも `reference_alpha` 0.0125 を下回るが、**family は max を取るので 1.0
  のままである。** 本稿は 3 対を主結果にしない (§0)。

### 2.2 12 cell の標本 — 各 8 標本 (block1 4 + block2 4)、unstable 0

provenance JSON (`facts.cells`) の値。標本は同一 session 内 5 反復の中央値 (tps)。mean と 95% 信頼区間の半幅は fig4 生成器が
WAL の 8 標本から再計算した記述用の値 (t 分布) で、判定・相対中央値差・family のどれにも使われていない (caption)。

| cell | genome (短名) | n | median (tps) | mean (tps) | 95% CI 半幅 (tps) | 標本 block1 | 標本 block2 | `unstable_count` |
|---|---|---:|---:|---:|---:|---|---|---:|
| `write-heavy:system_gate` | `g_rt` | 8 | 1,689,666.5 | 1,690,600.0 | 8,108.61861581508 | 1692127 / 1677830 / 1679991 / 1684973 | 1702034 / 1687206 / 1703276 / 1697363 | 0 |
| `write-heavy:p2_2_flag_opt` | `B0-L-W0` | 8 | 1,863,839.5 | 1,864,359.125 | 15,330.600288272033 | 1887156 / 1857967 / 1863724 / 1887159 | 1863955 / 1843671 / 1837027 / 1874214 | 0 |
| `write-heavy:backoff_fixed_best` | fixed 10 µs | 8 | 2,639,678.5 | 2,635,185.25 | 20,498.296915098297 | 2601215 / 2662293 / 2620848 / 2663058 | 2649716 / 2648970 / 2630387 / 2604995 | 0 |
| `write-heavy:sort_best` | `sk_ad` | 8 | 1,086,580.5 | 1,085,677.125 | 3,118.374771827901 | 1083370 / 1086952 / 1087718 / 1081278 | 1091937 / 1086209 / 1087266 / 1080687 | 0 |
| `balanced:system_gate` | `g_rl` | 8 | 1,705,405.0 | 1,705,079.5 | 4,934.403285157961 | 1706425 / 1707580 / 1701935 / 1702938 | 1694448 / 1715085 / 1707840 / 1704385 | 0 |
| `balanced:p2_2_flag_opt` | `B0-L-W0` | 8 | 2,723,265.0 | 2,727,597.875 | 30,364.120363602113 | 2747758 / 2766305 / 2719336 / 2727194 | 2701236 / 2717742 / 2777033 / 2664179 | 0 |
| `balanced:backoff_fixed_best` | fixed 5 µs | 8 | 3,078,552.0 | 3,080,929.875 | 9,351.77496267694 | 3078607 / 3100929 / 3095241 / 3069985 | 3072088 / 3073414 / 3078497 / 3078678 | 0 |
| `balanced:sort_best` | `sp_dd` | 8 | 929,335.0 | 927,247.75 | 4,661.616487534486 | 921873 / 930821 / 924344 / 930405 | 917262 / 933362 / 928265 / 931650 | 0 |
| `read-heavy:system_gate` | `g_rl` | 8 | 3,803,639.0 | 3,804,878.25 | 8,275.595265053593 | 3802516 / 3805646 / 3800916 / 3811494 | 3804762 / 3791457 / 3797663 / 3824572 | 0 |
| `read-heavy:p2_2_flag_opt` | `B0-T-W0` | 8 | 8,474,516.5 | 8,475,483.875 | 9,986.059607345553 | 8493333 / 8469808 / 8481531 / 8479225 | 8459748 / 8468043 / 8463981 / 8488202 | 0 |
| `read-heavy:backoff_fixed_best` | fixed 2 µs | 8 | 7,906,185.5 | 7,905,730.125 | 5,227.476985881604 | 7907216 / 7906683 / 7897080 / 7913668 | 7914116 / 7903105 / 7898285 / 7905688 | 0 |
| `read-heavy:sort_best` | `sk_ad` | 8 | 1,916,834.0 | 1,915,392.625 | 9,329.919785881159 | 1918301 / 1912442 / 1895687 / 1923595 | 1931416 / 1915367 / 1905039 / 1921294 | 0 |

provenance の `measurement_conditions` は `samples_per_cell` 8、`repetitions_per_session` 5、`session_statistic` median、
`unstable_policy` 「retain all accepted evidence; do not filter」、`unstable_sample_count` 0 を記録する。**floor campaign の
各 cell 8 標本はこの表に含めない** — `floor_cmp` の算出と照合にだけ使う契約である (`figures/README.md` fig4 節が
`s1_report.py` の `bind_left_target` と `floor_cmp` の生成契約として記録)。

### 2.3 効果量と CV (report の `effect_sizes`) — 判定には使わない

| 対 (workload : 右 cell) | `median_difference` | `probability_superiority_stratified` | `probability_superiority_pooled` | `target_cv` (左) | `control_cv` (右) | `floor_left_cv` | `floor_right_cv` |
|---|---:|---:|---:|---:|---:|---:|---:|
| write-heavy : `p2_2_flag_opt` | −174,173.0 | 0.0 | 0.0 | 0.005736141524543065 | 0.009834299631186696 | 0.003570770671913571 | 0.007199019400657359 |
| write-heavy : `backoff_fixed_best` | −950,012.0 | 0.0 | 0.0 | 0.005736141524543065 | 0.009302945506563682 | 0.003570770671913571 | 0.010356820766525538 |
| write-heavy : `sort_best` | 603,086.0 | 1.0 | 1.0 | 0.005736141524543065 | 0.0034351164903177883 | 0.003570770671913571 | 0.0060341024878958595 |
| balanced : `p2_2_flag_opt` | −1,017,860.0 | 0.0 | 0.0 | 0.0034610179894298348 | 0.013313560289731402 | 0.0031637615622310887 | 0.012635179626584602 |
| balanced : `backoff_fixed_best` | −1,373,147.0 | 0.0 | 0.0 | 0.0034610179894298348 | 0.003630162637065496 | 0.0031637615622310887 | 0.0031397060273033236 |
| balanced : `sort_best` | 776,070.0 | 1.0 | 1.0 | 0.0034610179894298348 | 0.006012493243957198 | 0.0031637615622310887 | 0.017799458912131735 |
| read-heavy : `p2_2_flag_opt` | −4,670,877.5 | 0.0 | 0.0 | 0.002601191500549005 | 0.0014091054691462363 | 0.0028525726560881984 | 0.0016368044873934927 |
| read-heavy : `backoff_fixed_best` | −4,102,546.5 | 0.0 | 0.0 | 0.002601191500549005 | 0.0007907951425718076 | 0.0028525726560881984 | 0.0043184706284402135 |
| read-heavy : `sort_best` | 1,886,805.0 | 1.0 | 1.0 | 0.002601191500549005 | 0.005825509937570341 | 0.0028525726560881984 | 0.004908597932807654 |

確率優越 A が 9 対とも 0.0 か 1.0 なのは、各対の 8 対 8 標本が完全に分離していることを示す (負けた 6 対は左の 8 標本すべてが
右の 8 標本すべてより低い)。`floor_left_cv` / `floor_right_cv` は 18 値とも 3.0% 未満なので、`floor_cmp` は 9 対とも
下限の 3.0% で決まっている (§1.3)。

### 2.4 ブロック効果 (併記義務)

事前登録は「ブロック efect の観測値は報告に併記」と定める。report の `block_effects` (block1 の中央値 − block2 の中央値、tps)。

| workload | 左 cell (`system_gate`) | 右 `p2_2_flag_opt` | 右 `backoff_fixed_best` | 右 `sort_best` |
|---|---:|---:|---:|---:|
| write-heavy | −17,216.5 | 21,627.0 | 1,892.0 | −1,576.5 |
| balanced | −1,431.0 | 27,987.0 | 10,968.5 | −2,583.0 |
| read-heavy | 2,868.5 | 14,366.0 | 2,553.0 | −2,959.0 |

ブロック効果の絶対値は 1,431〜27,987 tps である。各比較では左右いずれのブロック効果の絶対値も、その比較のプールした中央値差の
絶対値 (§2.1) より小さい (比が最も小さいのは write-heavy 対 `p2_2_flag_opt` で、中央値差 174,173 に対し右側のブロック効果 21,627、
約 8.05 倍)。report は 9 対すべてで gate (2) の方向一致を記録する。**この観測から、ブロック間変動に対する判定の頑健性までは主張しない。**
ブロック効果の統計的な検定はしない (事前登録も定量閾値を置いていない)。

### 2.5 正しさ — 全 session が別 build の検査で certified (性能の判定ではない)

正しさは trace-enabled build (`trace_bin`) の別走行から来る。性能値は `-DCCBENCH_TRACE=0` の build (`perf_bin`) の走行から
来ており、build も run も別である (絶対規律 1)。

| campaign | `verify_done` 件数 | `workload.tag` | verdict / certified / anomalies |
|---|---:|---|---|
| develop | 36 (18 cell × 2) | `legacy` 18、`s2` 18 | 全件 `serializable` / `true` / 0 |
| floor | 144 (session ごと 1) | `legacy` | 全件 `serializable` / `true` / 0 |
| block1 | 72 (session ごと 1) | `legacy` | 全件 `serializable` / `true` / 0 |
| block2 | 72 (session ごと 1) | `legacy` | 全件 `serializable` / `true` / 0 |

report の `hard_gates.certified` は、accepted session (develop 18 は `fitness_tps` null の開発相 session、性能標本は floor 144・
block1 72・block2 72) すべてについて certified evidence (`variant_id`・`src_token`・`verify_configs`) と照合し
`rejected_or_unbound_commits` 0 と記録する (事前登録 層 2「certified gate
の consumer 登録」)。**これは性能の認証ではない。** 正しさ検査の合格は性能の優越を保証せず、S-1a の不成立は取得済みの
正しさ証拠を取り消さない。

**検証相 (事前登録 (iv 付属) の `N_verify` = 8 独立反復 × 3 workload = 24 verify) の記録は、本稿の一次資料 (report・4 campaign
の WAL・時間台帳) には無い。** 時間台帳の phase は develop / floor / block1 / block2 の 4 つだけで、report.md は「本設計は
独立な検証相を持たない。ブロック化した単一登録追試 + gate 連言であり、旧記述の『スクリーニング → 検証相』はこの gate 連言
として読み替える。」と冒頭に明記する。校正 (extime = 3 s の確定) は行われている (§1.4)。

### 2.6 Holm 族 4 の中での S-1a (2026-07-16、人間承認)

`output/reports/s_prime_final_report.md` §1 の確定表。族 α = 0.05、段階 α は p 昇順に 0.05/4、0.05/3、0.05/2、0.05/1。

| 検定 | 名目 p (family) | Holm 段階 α (p 昇順割当) | 調整済み判定 |
|---|---:|---|---|
| S-1b | 0.000204 | 0.0125 (第 1 段) | 有意 — 成立 |
| S-2 | 0.115 | 0.0167 (第 2 段) | 非有意 (ここで手順打ち切り) — 不成立 |
| **S-1a** | **1.0** | (打ち切り後) | **非有意 — 不成立** |
| S-3 | 1.0 | (打ち切り後) | 非有意 — 棄却 (退化を示せない) |

S-1a の family p = 1.0 は打ち切り前でも第 1 段 α を上回る (report の `reference_below_alpha` False)。同報告 §2 の確定報告文は
本稿 §0 の主判定文の出所の 1 つで、「合成軸 trigger-gating は既知軸の一部 (sort) には明確に勝るが、単軸最良の凍結集合という
下界を超えない」と結ぶ。事前登録への 2026-07-16 追記は「帰結として縮小主張 S' の headline (既知軸最良の超越) は不成立」と
記録し、freeze の再凍結 3 回目 (値不変・`schedule_hash` 同一) を伴った。

### 2.7 retry と時間台帳

- report の 9 比較行の `retry_events` は空、正典 4 campaign の WAL は全 session `attempt` 0 (§1.4)。
- 時間台帳 (`output/s1-budget/time_ledger.json`、335 entries、`spent_s` は report と同値) の `machine-failure-retry` は 6 件
  で、すべて develop 相 (`index` 3 / 9 / 15 の `attempt` 1 と 2、`reason=build-error`、各約 20 秒、合計 120.65 秒 = report の
  `retry_spent_s`)。加えて同じ 3 index の `attempt` 0 が `status=retryable reason=build-error` として session に数えられている
  (各約 20 秒)。これらは §1.4 の v1 campaign に属する — `index` 3 / 9 / 15・attempt 0〜2・`reason=build-error` と `started_iso`
  (2026-07-15T15:49〜16:25Z、正典 develop campaign の開始 16:31:06Z より前) が v1 の WAL の `session-result` (attempt 0 の
  `ts` 15:50:06.819968Z / 16:09:10.290446Z / 16:25:13.419437Z 以下) と整合する。時刻の前後だけでなく index・attempt・reason の
  一致で帰属している。retry の上限 (≤ 2 / session) に達した 3 cell が `abandoned` と記録されたことは v1 の WAL、その後の
  版上げは worklog 2026-07-16 (1) の記録による (F19)。
- 事前登録の retry 規則 (プロセス異常終了・build 失敗・measure_point の例外のみ、≤ 2 / session、観測値を理由とする再測は禁止)
  の下で、正典 4 campaign には retry が 1 件も無い。
- **校正費用の台帳上の位置は未特定である。** 335 entries は `session:` 324 + `machine-failure-retry:` 6 + `campaign-overhead:` 5 で尽き、
  検証相校正 (§1.4、extime 3 s / 6 s の verify 各 1 回) に対応する明示的な entry は無い。事前登録 (iv) は総予算に「検証相校正・検証相」を
  含めると定めるが、`spent_s` 22,943.711507913657 秒がその範囲全体を計上したものかどうかは本稿では確認できない。`budget` gate の
  `pass` は report の記録として転記する。

---

## 3. この結果と他の記録の関係 — 関係の記述であって、結果の一部ではない

### 3.1 S-1b (同じ report の別 family) — 成立だが S-1a を救わない

同じ report の `families.s1b` は `judgment` 成立、`p_family` 0.00020408163265306123 で、3 対 (`gate_on_vs_gate_off`、
`system_gate` 対 `ident_all`) の相対中央値差は report.md の表で balanced 0.874244 / write-heavy 0.60638 / read-heavy 0.999298
である。S' 最終報告 §3 は「この効果は D50 の機械 sweep 偵察 (2026-07-11) で既知であり、本測定は配線確認を含む結果既知の
事前登録付き追試であって、confirmatory な新発見とは呼ばない」「既知軸最良との優劣 (S-1a) とは独立の主張である」と書く。
fig4 の caption も「S-1b は既知軸最良との優劣を問う S-1a とは独立の主張であり、その成立は S-1a の不成立を救わない」と結ぶ。
**本稿は S-1b の結果節ではない。** S-1b の単独稿を書くなら同じ一次資料から別に作る。

### 3.2 縮小主張 S' と確定文言 — 必須の併記

S' 最終報告 §4 は「S' は不成立 (S-1a 不成立による)。族 4 のうち成立は S-1b のみ」と総括し、確定文言
(`output/insights/2026-07-13_s6-report-language.md` §3 付記) の必須併記を再掲する。原文は 2 つある。確定文言 §3 付記:
「S-1 が成立しても適格率次元の発見再現性は未実証のままであり、報告ではこの限界を S' に併記する」。S' 最終報告 §4:
「適格率次元の発見再現性は未実証のままである (S-1b の成立はこの限界を解消しない。S-1a が不成立となった今回、性能次元でも
『既知軸最良の超越』は実証されていない)」。**本稿 §0 の主判定文はこの 2 文を逐語で含む** (引用の入れ子になる内側の括弧だけ『』に置き換えた)。言い換えて弱めない
(「S-1b の成立はこの限界を解消しない」を落とさない)。S-2 (名目 p = 0.115、不成立) と S-3 (名目 p = 1.0、棄却) の確定文言には
本稿は作用しない。

### 3.3 既知軸集合の性格 — 下界を超えなかったことは合成の無価値ではない

事前登録は既知軸集合を「単軸最良の凍結集合 — 合成未探索の下界」と定義し、「既知軸集合はリポジトリ探索履歴依存の凍結有限集合
(合成未探索の下界 — S-1a のマージンが合成で埋まりうる規模かの議論を報告義務化)」を既知限界に置く (§1.1)。したがって
S-1a の不成立が言うのは「2026-07-12 に凍結した 3 軸の実測 argmax を、trigger-gating 1 本の系側 gate 構成は 3 workload ×
2 軸で下回った」までであり、合成一般の価値、他の合成軸、凍結集合の外の既知手法との優劣は言わない。

議論の材料として数値だけを置く: 負けた 6 対の相対中央値差は −9.3% (write-heavy 対 `p2_2_flag_opt`) から −55.1% (read-heavy 対
`p2_2_flag_opt`) で、`backoff_fixed_best` に対しては −36.0%〜−51.9% である。**このマージンが合成で埋まりうる規模かどうかは本稿は
判定しない。** 事前登録は同時に「(c') 事前自認 = trigger-gating の軸内探索で LLM は機械列挙を上回れない (D48 決定 2) —
主張範囲外として最初から明記」と記録しており、系側 gate 構成の探索空間が機械列挙で閉じている軸であることは結果を見る前に
自認されている。合成の側の別の壁 (非列挙のコード片軸の有限幅と代理の二重の壁) は D1409 (2026-09-01) が確定しており、同 D は「非列挙」の
定義の置き直しをユーザー裁定へ返したと記録する (本稿の執筆時点 2026-09-20 で未裁定)。本稿はどちらも S-1a の結果の一部としては
書かない。

### 3.4 fig4 — 同じ凍結 report と 4 campaign から描いた失敗報告図

`docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.{png,pdf,provenance.json}` は 2026-08-26T16:54:23.355492Z に
`tools/plotting/plot_s1_9pair.py` (provenance の `generator_source.sha256` `4a76d59c854cf8021a711cb27ebeb7aad599c4dda448dd9ee6f15c80ab7d772c`)
が描いた。判定・p 値は本稿と同じ凍結 report (sha256 `491ad38d…`)、標本は正典 4 campaign の WAL (sha256 は §5.1) に由来し、
provenance の `inputs` は併せて各 campaign の `campaign.lock` と現行 `measurement_freeze.json` (`current_measurement_freeze`) を
入力として束縛する (計 6 entry)。新規計測は無い。判定と p 値は凍結 report から読み、生成器は再計算していない (`figure_conventions_compliance.status` = `partial`、理由
「samples and aggregates are recomputed from WAL; frozen judgment and p-values are read from the hash-bound report」)。
`facts.claim` は `pair_count` 9、`passed_pair_count` 3、`failed_pair_count` 6、`conjunction_required` true を記録する。
本稿 §2.1 / §2.2 の値は provenance の `facts` から転記したので、図と表の値は同じ生値から同じ計算で出ている。

**report が参照する freeze と現行 bytes は異なる。** report の `freeze_ref.sha256` は `5c719c07…`、現行の
`output/s1-freeze/measurement_freeze.json` は `203de36b…` で、provenance の `facts.freeze_proof` は
`freeze_ref_matches_current` false、`historical_emission_commit` `b4e5cb621e3f8f93de952e9400d4b8dcd34107e0`、差は
`/frozen_at_head`、`/implementation_hashes/known_axes_freeze/sha256`、`/cells/read-heavy:sort_best/variant/sources[0]/sha256`
の 3 か所だけで、`figure_semantics_equal` = 18 cell 定義・12 比較定義と注記・`operating_point`・`workload_flags` と記録する。
これは worklog 2026-07-16 (1)(2) が記録する freeze の再凍結 (値レベル不変・`schedule_hash` 同一を機械確認) に対応する。
本稿 §1.2 の cell 定義は現行 bytes から転記したが、上の記録により report 時点の定義と意味内容が同一である。

**現行コードとの差。** 本稿の執筆時点 (local main `947fd160a`) の `tools/plotting/plot_s1_9pair.py` は sha256
`61559d90b62d752870a542e0317012b5da42c0ac7ab64d87ddc621d48131b767` で provenance の `4a76d59c…` と異なり、
`orchestrator/campaign/s1_stats.py` (`ace74689f612d9f11194f58ecf144b3cda19f9378b7857c7c5d052786a74061c`) と
`orchestrator/campaign/s1_measurement_freeze.py` (`54d95622e50d991410fa273a39aa12daa634c62be11f45262dc7c2aef4dde5b5`) も
freeze の `implementation_hashes` (`d1aef1c8…`、`a7c41a81…`) と異なる。図・report・freeze はいずれも再生成していない。
**現行コードとの差は、記録された測定と判定を無効にする理由にならない** (絶対規律 7)。

### 3.5 `stock_common` — 文脈 cell であって登録比較ではない

freeze の注記どおり `stock_common` は 9 対に含まれず、fig4 も描かない (基準線にすると登録外の第 10 の比較を図が主張するため、
`figures/README.md` fig4 節)。provenance の `facts.context_cells` は `registered_comparison` false を付けて次を記録する。

| workload | `stock_common` median (tps) | 8 標本 | `sort_best_relative_to_stock` | `system_gate_relative_to_stock` |
|---|---:|---|---:|---:|
| write-heavy | 1,051,498.5 | 1049939 / 1060600 / 1040535 / 1062661 / 1046920 / 1053058 / 1056961 / 1045239 | 0.03336381364310077 | 0.6069128962143074 |
| balanced | 916,888.0 | 916354 / 917422 / 913774 / 900064 / 917564 / 913442 / 924945 / 924894 | 0.013575267644466937 | 0.8599927144863931 |
| read-heavy | 1,904,557.5 | 1925519 / 1902558 / 1901042 / 1906557 / 1900992 / 1918013 / 1908053 / 1901553 | 0.006445854220731062 | 0.997124791454183 |

`system_gate_relative_to_stock` は文脈値であり、事前登録の比較でも判定でもない。**本稿は「合成軸は stock を +60〜100% 上回る」を
結果として書かない。**

### 3.6 現行環境の記録との非関係 — 前後比較として読んではならない

本稿の 12 cell は 2026-07-16 の旧環境 (`linux-baremetal`、CCBench `d706650`、`perf stat` 下、`clocks_per_us` 1,800、gcc-13) の
値である。現行環境 (Pegasus、pin `511c953` + patch、`perf` 不使用、`clocks_per_us` 2,100 など) で取った次の記録は、いずれも
本稿の比較ではない: A-2 `t2364-20260907b` (`results/2026-09-07-a2-certification-observed-positive.md`)、A-6 `a6-20260908b`
(`results/2026-09-18-a6-certification-reject.md`)、[T-1998] balanced stock-inline (`results/2026-09-18-t1998-balanced-stock-inline-accepted.md`)、
B-7 fixed 5 µs (`results/2026-09-19-b7-fixed5-three-workload-regression.md`)、A-1 attempt-0001
(`results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md`)、B-10 右 tail 2 cohort、採用候補 2 genome の検証相
(`results/2026-09-20-verify-phase-adopted-backoff.md`、D2160)。これらが比べているのは採用静的 backoff と無 backoff (または
backoff 値の grid) であり、系側 gate 構成も既知軸最良 3 種も測っていない。

特に `backoff_fixed_best` cell の genome 値 (balanced 5 µs / write-heavy 10 µs / read-heavy 2 µs) は、A-2 / A-6 の採用値
(rr50 = 5 µs、rr5 = 10 µs、rr95 = 2 µs) と数値が同じである。**同じ genome 値でも、環境・pin・build・run の契約・`src_token` の
定義 (本稿は D1644 以前の identity) が違うので、本稿の cell と A-2 / A-6 の cell を同じ測定として扱わず、値を並べて前後比較
しない** (絶対規律 7、D496)。fig4 の caption も「本図の絶対スループットは論文の headline 値の出所ではなく、現行の同一 campaign
内対測定契約 (D496) を満たすとも主張しない。この限定は凍結済みの S-1a 判定を変更しない」と書く。

### 3.7 本稿の凍結資料に記録された本走は 1 回である

本稿が対象とする凍結資料 (事前登録・S' 最終報告・report・4 campaign・時間台帳) に記録された S-1 の本走は 1 回 (4 campaign) である。
事前登録は S-1 の反復 attempt を定めておらず、上記の資料から第 2 の本走や別環境での再測は特定していない。この走査で言えるのは
「これらの資料が報告する本走数が 1 である」までで、全履歴にわたる実施の不在ではない。**本走間の変動 (符号と効果) の観測は本稿の
証拠範囲に含まれない。** gate (2) が担う cross-run 再現は同一本走内の 2 ブロック間の再現であって、本走間の再現ではない。本稿はこれを
限定として残す (§4 限定 1)。

---

## 4. 限定 (この結果が言わないこと)

1. **1 本走・n = 8 / cell (block1 4 + block2 4) の family 判定である。** 本稿の凍結資料に記録された本走は 1 回で、第 2 の本走や
   別環境での再測はそれらの資料から特定していない (§3.7)。本走間の変動は本稿の証拠範囲に含まれない。gate (2) の方向一致は
   同一本走内の 2 ブロック間の再現であり、本走間・環境間の再現性は判定しない。
2. **旧環境の値である。** `linux-baremetal`・CCBench `d706650`・`perf stat` 下・`clocks_per_us` 1,800・gcc-13・48 thread・
   1,000,000 record・Zipf 0.9・`rmw` 0・3 秒の値であって、現行 Pegasus・pin `511c953` + patch・他の thread 数・他の record 数へ
   外挿しない。絶対スループットは `perf stat` のオーバーヘッドを含み、headline 値の出所ではない (§3.6)。
3. **結果既知の登録追試の出力である。** 「S' の不成立を『新しい否定的発見』と書かない」「S-1b の成立を『発見』と書かない」は
   恒久の表現規律である (事前登録の HARKing 境界、§1.1)。
4. **既知軸集合は凍結有限集合 = 合成未探索の下界である。** 超えなかったことは合成の無価値ではなく (§0、§3.3)、凍結集合の外の
   既知手法・他の合成軸・現行の合成ループとの優劣は言わない。S-1a のマージンが合成で埋まりうる規模かは判定しない。
5. **適格率次元の発見再現性は未実証のままである** (確定文言の必須併記、§3.2)。S-1a が不成立となった今、性能次元でも
   「既知軸最良の超越」は実証されていない。
6. **正しさの証拠は別 build の `legacy` 条件の検査であり、性能の認証ではない。** floor / block は session ごと 1 回、develop は
   cell ごと 2 回 (`legacy` と `s2`) で、事前登録 (iv 付属) の検証相 (8 独立反復 × 3 workload) の記録は一次資料に無い (§2.5)。
   verifier の射程は YCSB の point read / write に限った観測 trace 上の直列化可能性である (L01)。正しさ側の run argv は WAL に
   記録されていない (`verify_done` が持つのは `workload.tag` のみ)。
7. **判定の根拠は report の参考 α (0.0125) の下の family 判定と、2026-07-16 の人間承認 (Holm 族 4 判定表) である。** report
   自身は `holm_family4_adjudication` = `not_performed_human_or_future` と記録し、族 4 全体の裁定を行っていない (§1.3、§2.6)。
8. **6 対の負けは方向が 2 ブロック間で一致した負けである (gate (2) 通過)。** 本稿はそれを cross-run 再現の観測として書き、
   機序 (なぜ `p2_2_flag_opt` / `backoff_fixed_best` に負けたか) は同定しない。
9. **`sort_best` cell の選定履歴に限定がある。** freeze の注記: balanced は「本走 argmax 規則により sp_dd を固定。balanced の
   sp_dd は remeasure campaign p3-s6-sort-sweep-balanced-sweep-1b39095e で floor 超を再現せず、D46 裁定は差なし。」(remeasure の
   argmax は `sk_aa`、`reference_fitness_tps` 921,457.0)、read-heavy は「read-heavy は sweep 未実施。D52 §2.1 の事前固定 sk_ad を
   採用し、comparator は write-heavy 本走 provenance から流用。」。したがって「`sort_best` に勝った」の相手は凍結時点の argmax
   構成であり、sort 軸の真の最良ではない。事前登録は「再計測での順位入れ替わりは観測として報告するが基準点は動かさない」と
   定める。
10. **`stock_common` は登録比較ではない** (§3.5)。`system_gate_relative_to_stock` を結果に使わない。
11. **freeze の bytes は report 時点と現行で 3 か所異なる** (§3.4、意味内容は同一)。現行の生成器・統計実装・freeze 生成器の
    sha256 は測定時点と異なるが、記録された測定と判定を無効にしない (絶対規律 7)。
12. **session 間の独立は操作的仮定である** (事前登録 層 1 (ii): プロセス分離 + RNG の run ごと自己シード。時間ドリフト等の
    系列相関は除去されず、層別化・ランダム化 schedule が担う)。within-run の 5 反復は観測単位にしない (median に縮約)。
13. **mean と 95% CI は標本分布の記述用であり、効果・判定・median の信頼区間ではない** (§2.2)。効果量 (中央値差・確率優越 A・
    CV) は併記であって判定には使わない (§2.3)。
14. **develop 相には v1 の build-error 3 cell と retry 6 件がある** (§1.4、§2.7)。正典 4 campaign に retry は無い。`index` と
    cell の対応 (`backoff_fixed_best` 3 cell) と abandoned は v1 の WAL から、版上げの経緯は worklog の記録による。v1 の性能値は
    存在しない (`bench_done` 0 件) ので、v1 が 9 対の値に混入する経路は無い。
15. **図は fig4 (失敗報告図) である。** 本稿の表と図は同じ生値から出ている (§3.4)。fig4 は `stock_common` を描かず、9 点を
    同面積で置き、「1 軸に勝った」を主結果として描いていない。
16. **先行指標 (abort 率・`llc_miss_rate`・`ipc`・`latency_ns`) は WAL の `bench_done.leading_indicators` にあるが、本稿は
    転記しない。** 機序を語らないためであり、必要なら同じ WAL から別稿で扱う。
17. **対象軸は n = 1 (trigger-gating 1 本) の系側 gate 構成であり、workload 特化 (8b) は本改訂の主張に含めない** (事前登録の
    既知限界)。S-1a は `g_rl` / `g_rt` という 2 つの gate 述語 (workload 別に事前固定) の値であって、trigger-gating 軸の他の
    gate 述語の値ではない。
18. **prospective power は未保証である** (§1.3、事前登録 層 1 (iii))。N = 8 は p 値解像度の確保を根拠とする設計で、完全分離時の
    最小 p 値 1/4,900 は検定力の保証ではない。事後の判別力再評価は行わない。
19. **校正費用の台帳上の位置は未特定である** (§2.7)。時間台帳の 335 entries に検証相校正の明示的な entry は無く、`spent_s` が
    事前登録 (iv) の計上範囲全体を含むかどうかは本稿では確認できない。`budget` gate の `pass` は report の記録として転記した。

---

## 5. 一次資料

### 5.1 権威 bytes と転記元 (repo 内、tracked)

sha256 は本稿の執筆時 (2026-09-20、local main `947fd160a` の fresh worktree) に現物から取った。provenance JSON が値を
記録している file (report.json、現行 freeze、4 campaign の WAL と lock、図 2 file) は記録値と全件一致した。

| file | 役割 | SHA-256 |
|---|---|---|
| `output/reports/s1_direct_comparison/report.json` | 凍結 report (判定・p 値・gate・効果量・hard gate・時間台帳の要約) | `491ad38dbabc4a9d57fc7a0ae5a4f5b37f67a5862712e158a9cc34e8552fa725` |
| `output/reports/s1_direct_comparison/report.md` | 同 (人間可読) | `02e41ce703e34aab9be170f25caffea084c2b61084b16bbac61bd796b508723d` |
| `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json` | 12 cell の標本・中央値・平均・CI、9 対の median、文脈 cell、freeze 差、caption | `7e9901d8dead9283effcd87b8b0944b350beb38b131053362262d9245fd646a1` |
| `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.png` / `.pdf` | 図 (provenance の `outputs` が束縛) | `61c6eeb6932252f87ad8e2bc8f828e5e7543658a2aea22c7ff5c7847eaf157b7` / `669ad045fe34dbd73e4a157168656c15bc2d2ef3fe214f441edb79ce33db70fa` |
| `output/s1-freeze/measurement_freeze.json` | 18 cell・12 比較の定義、schedule、実装 hash (現行 bytes) | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` |
| `output/s1-freeze/known_axes_freeze.json` | 既知軸基準点の freeze | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` |
| `output/campaigns/s1-direct-develop-direct-comparison-d0f495bf/runs/wal.jsonl` / `campaign.lock` | develop (正典) | `fb1af21ea7da95cbf5e40dbb8a2da8af41f6c2a44bd18945290eb17f0dfaa7ac` / `d0f495bf6fc97bb4666471f0258f47c72f65557c8b0a0c530855ebb9a3327f62` |
| `output/campaigns/s1-direct-floor-direct-comparison-b82b9229/runs/wal.jsonl` / `campaign.lock` | floor | `a5542d6cba6b4470a828e96e77f826dcd553ce38fe635a7a4c88141c03d99c38` / `b82b9229331d4ac7371647c63032fc593202c8e24b6ea030a1ad4490b122e432` |
| `output/campaigns/s1-direct-block1-direct-comparison-74ff9ba2/runs/wal.jsonl` / `campaign.lock` | block1 | `57726aadb08b1833cd2a8e919c9f766ac83c1cdce551c4bc82ad4fdeb1f2ad20` / `74ff9ba28a70e18ece2d87777d95a147b222f5ab8576071b798a7820e492e8a5` |
| `output/campaigns/s1-direct-block2-direct-comparison-9645b16a/runs/wal.jsonl` / `campaign.lock` | block2 | `2194ca8936bb0d6f812e6ad94ffbd1f278ab40386abc5123c36d0ea75c7342bd` / `9645b16a86d769bdb2fa8a7fb7c4c2494ba125d8d1f29fff7de47266a58628a9` |
| `output/s1-budget/time_ledger.json` | 時間台帳 (335 entries) | `180d5d171d5642e5a68c7a8165e570ad52bc5498b9ea71e1c18e8a6e9b066894` |
| `output/env/linux-baremetal/calibration/s1_verify_extime.json` / `.md` | 検証相校正 (extime = 3 s) | `5a672ba0a1262b26a276cdb3606c9e2a1c1b9ba6ef7f6369a3de7fbe9d74a4cc` / `636d2ea796dd3339d9cb7e4f79b0c95b48d13571c824438d129a455c5c63ccb0` |
| `docs/phase3-main-experiment.md` | S-1 事前登録 (D52 の 2026-07-12 追記、2026-07-15 追記と承認記録、2026-07-16 追記)。凍結 source (現行 freeze の `read-heavy:sort_best` の `sources[0]` と同じ bytes) | `e544de1969dd4df13dc42aa3d165e22b70fab2ab399dc011baa46359727bea45` |
| `output/reports/s_prime_final_report.md` | Holm 族 4 判定表と S-1a / S-1b の確定報告文 (2026-07-16 人間承認) | `ff7115c96e8013ba45d94ee5dac43382cc5326ad684e2b72b3cfcac469afca16` |
| `output/insights/2026-07-13_s6-report-language.md` | 確定文言 (S-2 / S-3 の報告文、必須併記、限定表現) | `db652562bdcc0d5de7fad61d84c84d956afb52c191dbf76021c23b9219bd34fb` |
| `docs/archive/worklog-phase3-0714-0716.md` | worklog 2026-07-16 (1)(2) (本走の実施記録、develop v1 の abandoned、族 4 確定の手続き) | `6203480d955cb3b0b58335992ab6e8139cf9b5a6addea2eaebb2efad32185d81` |
| `output/campaigns/s1-direct-develop-direct-comparison-7bccdf1a/runs/wal.jsonl` | develop v1 (正典でない。§1.4 / §2.7 の v1 に関する記述の出所。9 対の値・判定の出所ではなく、provenance の `inputs` にも無い) | `d620ff914d91944d06a78c15609bbbea3138bf955665f4e43a666641fdf1d416` |

### 5.2 値の出所

| 値 | 出所 |
|---|---|
| 9 対の `judgment`・`gates` (gate1 / gate2 の `passed`・`required_strictly_greater_than`・`pooled_direction_sign`・`block_direction_signs`)・`floor_cmp`・`p_perm`・`p_star`・`reference_alpha`・`unstable_counts`・`block_effects`・`retry_events`・`reasons` | report.json の `comparisons[]` |
| `median_difference`・確率優越 A・`target_cv`・`control_cv`・`floor_left_cv`・`floor_right_cv` | report.json の `effect_sizes` |
| family 判定・`p_family`・`judgment_basis`・`holm_family4_adjudication` | report.json の `families.s1a` (S-1b は `families.s1b`) |
| hard gate の記録値、時間台帳の要約、`generated_at_head`、`freeze_ref` | report.json の `hard_gates`・`budget`・`generated_at_head`・`freeze_ref` |
| S-1b の相対中央値差 (6 桁)、report.md 冒頭の「独立な検証相を持たない」 | report.md |
| 12 cell の 8 標本 (block 別)・median・mean・95% CI 半幅・`unstable_count`、9 対の左右 median、文脈 cell、`measurement_conditions`、`freeze_proof`、`claim`、`figure_conventions_compliance`、生成器の sha256、caption | provenance JSON の `facts`・`generator_source`・`generated_utc`・`caption` |
| 18 cell の genome・gate 述語・comparator・選定履歴の注記・`reference_fitness_tps`、12 比較の定義、`frozen_at_head`・`ccbench_pin`・`master_seed`・`schedule_hash`・`implementation_hashes` | `measurement_freeze.json` |
| 環境タグ・CCBench commit・trial・spec・verify 設定・campaign の時刻・WAL の行数と段・session の結果・toolchain・configure / run の argv・build の cache・`verify_done` の件数と verdict・variant と `src_token` | 4 campaign の WAL と campaign.lock (本稿の執筆時に集計) |
| retry 6 件・attempt 0 の build-error 3 件・phase 別 entries 数・`started_iso` | `time_ledger.json` の `entries[]` |
| develop v1 の WAL の行数と段、`session-start` 24 / `commit` 15、build-error の `schedule_index` 3 / 9 / 15 と cell の対応、attempt 0〜2 と `abandoned`、`abort` の `error`、`campaign-start` の時刻 | v1 の WAL (`…-7bccdf1a/runs/wal.jsonl`、本稿の執筆時に集計) |
| 判定規則・既知軸集合の定義・HARKing 境界・既知限界・失敗条件 (c)・(c') 事前自認・独立性の操作的仮定・retry 規則・判定不能の発火条件・Holm 族 4 追記 | `docs/phase3-main-experiment.md` の 2026-07-12 / 2026-07-15 / 2026-07-16 追記 |
| Holm 族 4 判定表・S-1a の確定報告文・S' の総括 | `s_prime_final_report.md` §1〜§4 |
| 必須併記の原文 | `2026-07-13_s6-report-language.md` §3 付記 |
| develop v1 から v2 への版上げ (F19)、freeze 再凍結の運用、族 4 確定の手続き | worklog 2026-07-16 (1)(2) |
| JST 時刻 | WAL の `ts` (epoch) を本稿で +9 h 換算 |
| 現行コードとの差 (§3.4) | 本稿の執筆時に local main `947fd160a` の現物から sha256 を取った |

### 5.3 裁定

D12 (protocol status を成功・失敗の宣告へ拡張しない)、D19 (採否 floor は between-run、wired 保守 floor 3.0%)、D46 (sort 軸の
機械 sweep 先行実測)、D48 (trigger-gating の軸定義、決定 2 = 偵察空間 = coder 変異空間)、D50 (trigger-gating の機械 sweep 偵察、
3 workload で floor 超が cross-run 再現)、D52 (headline 主張の系レベル再構成 = S-1 の登録)、事前登録 2026-07-15 追記の
ユーザー承認 (2026-07-15)、Holm 族 4 判定表のユーザー承認 (2026-07-16)、D496 (性能比較は同一 campaign 内の対測定、凍結した過去値を
比較の基礎にしない)、D1409 (非列挙のコード片軸の二重の壁)、D2120 項 15 (単独 results 稿は権威 bytes から作る既存経路、層 3 の
材料レポートと同一視しない)。

### 5.4 同じ結果についての既存の文書 (本稿の出所ではない)

論文ストーリー版 (`docs/paper-story/2026-08-26.md` 以降、直近は `2026-09-20.md` の「S-1a が何を測って落ちたか」節と §8 B-1)、
`docs/paper-story/figures/README.md` の fig4 節、claim-evidence 系列の該当行は、S-1a の 9 対を要約・引用している。本稿は
それらを参照して書いておらず、値が一致するのは同じ凍結 report と provenance から独立に転記しているからである。
**S-1a の 1 本走の執筆材料には本稿を使い、論文全体の中での位置づけには版を使う。** どちらも凍結物として残る。
