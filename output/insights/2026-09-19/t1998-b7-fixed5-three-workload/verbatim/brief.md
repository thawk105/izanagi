# 段 1 brief — 採用候補 fixed 5 µs を 3 workload で同時期に走らせ、床値超の退行を判定する

wave: dev-wave-t1998-three-workload-regression
worktree (投入先・子の repo root): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-three-workload-regression
job dir (prompt・log・patch・逐語資料): /home/SFC/tanab/.claude/jobs/f6bf33bb
基準: local main a99425b66 (2026-09-19)。CCBench pin 511c953。実行環境: Pegasus login (pegasus02) から gen_S へ投入。

## 研究前進 (1 行)

論文の失敗条件 (e)「target workload では勝つが他の workload で floor 超の退行がある → 退行込みで全 workload を報告」
の材料として、**同一候補 (静的 backoff fixed 5 µs) を 3 workload で同一 attempt・同時期に測り、各 workload に同時刻の
stock 対照を置いた表 1 枚 + 床値 (D1639) 超の退行判定**を results 系列稿へ置く。完了判定 = 3 workload の
median・対差・床値・判定・生標本・identity が一次資料に束縛されて 1 稿に書かれ、B-7 の要件充足判定は書かない。

既存被覆 (純増だけを書く): 2026-09-14 / 09-16 の B-7 稿は workload ごとに別の採用値 (10 / 5 / 2 µs) を別 attempt で
測ったものを事後併記した (同一候補の横断ではない、D2044 項 3 が「床値超の判定を供給していない」と確定)。
A-1 sized attempt-0001 (2026-09-18) も workload 別採用値。B-10 tail grid は 1000〜9999 µs。
**同一候補 fixed 5 µs の 3 workload 同時期測定 + 床値判定は無い。** これが純増。

## 確定済みユーザー裁定 (2026-09-19、逐語は rulings-verbatim.md)

- 候補 = `docs/t1998-balanced-stock-inline-preregistration.md` の採用 arm = `BACK_OFF=1, BACKOFF_FIXED=5`。stock = `BACK_OFF=0, BACKOFF_FIXED=-1`。
- 床値 = D1639 の between-run noise floor (3 workload)。実値は `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` の between-run CV (md 表記: rr5 0.95% / rr50 0.73% / rr95 0.22%。**JSON の全桁を計算前に固定して使う**)。
- 判定 = 各 workload で候補 vs stock の対差が −floor を下回れば退行。結果は退行込みで 3 workload 全件を報告。
- B-7 要件充足の判定は本 wave でしない (D2044 項 3 維持)。
- 機構 = A-2 / A-6 の certification 経路 (`orchestrator/campaign/paper_story_a2_certification.py` 系) を descriptive に使う。3 workload を条件で割って複数ノードへ同時投入、同時刻の stock 対照を各 workload に置く。
- 既存材料 `docs/paper-story/results/2026-09-16-b7-three-run-materials.md` と併記し、プールしない (D1993 項 6)。
- 成果 = results 系列稿 1 本 + 図の材料。規律 2 を緩めない。
- scope 外 = certification の昇格・新 protocol・追加 gate。

## scope (変更面の実アンカー)

A. **実装面 (Codex author)** — A-6 追加 commit `60605bec3` と同形の closed-set 拡張:
  1. 新 policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json` — `schema_version` は既存 `paper-story-a2-certification-policy/v2` のまま、`study` = `paper-story-b7-fixed5-regression`、`workloads` = rr5 / rr50 / rr95 (label write-heavy / balanced / read-heavy、rratio "5" / "50" / "95") **すべて `adopted_backoff_us: 5`**、`cells` = `{rr5,rr50,rr95}-stock` (`BACK_OFF 0 / BACKOFF_FIXED -1`) と `{rr5,rr50,rr95}-fixed5` (`BACK_OFF 1 / BACKOFF_FIXED 5`) の 6 cell、`performance_common` / `legacy_correctness` / `controlled_define_base` / `trace0_cmake_argv` / `historical_reference` / `certification_composition` は A-2 v2.json と同値、`scheduler` = `{project SFC, queue gen_S, nodes 5, walltime 12:00:00, job_body tools/pegasus/paper_story_a2_certification.sh}` (A-6 と同形)、`durable_measurement_base` = `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919`、`tracked_destination` = `output/insights/2026-09-19_t1998-b7-fixed5-three-workload`。
  2. `orchestrator/campaign/paper_story_a2_certification.py`: `A6_POLICY_PATH` の隣に `B7_FIXED5_POLICY_PATH` (:74)、`canonical_policy_path` の closed set (:358-370)、`_qsub_job_name` (:373-380、名 `paper-b7-fixed5`)、`_qsub_environment_keys` (:383-390、`IZANAGI_A2_POLICY_PATH` を要する側)、`policy_shapes` (:564-567、`(3, 6)`)。他の関数は触らない (partial 完了の exact two-workload 境界 :1933 は変えない)。
  3. `tools/pegasus/submit_paper_story_a2_certification.sh`: `if [[ "$STUDY" == paper-story-a6-certification ]]` (:263) を新 study も `IZANAGI_A2_POLICY_PATH` を渡す形へ。job body `tools/pegasus/paper_story_a2_certification.sh` は無変更 (`IZANAGI_A2_POLICY_PATH` 経由で policy 選択済み)。
  4. tests: `orchestrator/tests/test_paper_story_a2_certification.py` (:4833-4836 の study 対応表、closed set・shape・job 名の正例/負例)、`orchestrator/tests/test_paper_story_a2_job_contract.py` (:1111-1121 の param、:1296-1301 の env/qsub argv) に新 study を足す。`admission_registry.json` は path 登録のみで無変更 (job body・submitter は既登録)。
B. **投入・回収 (親)**: 実装 commit 後、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1998-b7-fixed5/submit-tree` を detached で切り submodule 初期化・hydrate (`fetch_third_party.py hydrate --staging-root <tree>/output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`)、`submit_paper_story_a2_certification.sh --policy <新 policy> --attempt-id b7f5-20260919a --ccbench-root <tree>/external/ccbench --dependency-prefix-source /work/1/SFC/tanab/izanagi-a2-deps --third-party-source-root <staging>` で 3 request を同時投入 → 待ち手 1 本 → `finish-group` → `collect` (tracked_destination へ materialize)。
C. **docs (親)**: `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md` (系列規則: 一次資料束縛、append-only、判定は descriptive)、`docs/paper-story/README.md` の results 表へ 1 行、spool fragment (worklog / decisions 各 1)、insight README (wave 記録)。図の材料 = 稿内の生標本・median・対差・床値・判定の表と collect 済み leaf (certification.json / raw-manifest / WAL 参照)。plotter は作らない。

## 不変条件

- A-2 / A-6 の policy bytes・`protocol_sha256`・既存 attempt 成果物・`tracked_destination` は 1 byte も変えない。
- 正しさ gate 不変: anomaly を出した cell は機構どおり `reject` (規律 2)。性能値は trace-disabled build (規律 1)。
- 判定規則を**結果を見る前に固定**する: `effect_w = adopted_median_w / stock_median_w − 1` (機構の `effects` そのもの、5 標本 median)。`regression_w ⇔ effect_w < −floor_w`、`floor_w` = 上記 JSON の between-run CV。3 workload 全件を、符号を問わず同じ表に載せる。outer status (3 workload の論理積) は機構の出力として書き写すだけで certification 主張にしない。
- 3 workload をプールしない。既存材料 (2026-09-16 稿) との併記は表を分け、前後比較として読まない (規律 7)。
- 追加 gate を作らない: 床値判定はコードへ入れず、稿で計算する。partial 完了 (1〜2 workload 欠落) の機構対応は足さない — その場合は durable raw / WAL から記述し、欠落を明記する。
- 実装は closed set の拡張 (追加) だけで、受理条件を緩めない (任意 path・任意 shape を受理しない)。

## (P) 親の provisional 裁定 — 攻撃対象

- (P1) **「同一 build」の定義** = 3 workload で genome・controlled define・configure argv・patch 適用下の source bytes digest (`src_token`) が一致すること。binary は workload job ごとに別 node で build されるので `perf_bin_sha256` は一致すれば記し、不一致でも source digest 一致を「同一 build」の充足と読む。login で 1 度 build して配る形は既存機構に無く新 protocol になるので採らない。
- (P2) 新 study policy の追加は「新 protocol」ではない (schema v2 不変、A-6 が同じ形で追加された先例 `60605bec3`)。protocol_sha256 は policy ごとの値であり A-2 / A-6 のものは動かない。
- (P3) 床値 (1 arm の session-median の CV) と対差 (2 arm の median 比 − 1) を**ユーザー裁定どおり直接比較**する。独立同分散なら比の CV は 1 arm の約 √2 倍という注意は稿の限定に書き、判定式には入れない。
- (P4) `scheduler.nodes = 5`、walltime 12:00:00 (A-6 と同形)。根拠: t2489 probe で nodes=5 は 1 workload 12 分、A-6 rr95 は nodes=5 で 73 分。nodes=1 なら rr95 は直列検査で数時間。
- (P5) 「同時期・同時刻の対照」= 同一 attempt で 3 request を同時に qsub し、各 workload 内で stock と adopted を同 node・同 campaign で連続して測る形 (A-2 の既存の形)。`~/.izanagi/bench.lock` による request 間の直列化 (t2489 §3) は所要を延ばすが対照の同時刻性を壊さない (同 node 内の 2 cell は数分差)。
- (P6) 図の材料は稿 + collect 済み tracked leaf で足り、新 plotter・`plot_a2_certification.py` の拡張は scope 外。
- (P7) 3 request が同時に走らないと (queue で分断) 「同時期」が弱まる。投入時に `qstat -Q` の空きを見るが、分断しても attempt は有効とし、実際の開始時刻差を稿に書く。

## 成果物の形

- 実装 commit 1 つ (policy + closed set + tests)、記録 commit (稿・README 行・spool・insight)。
- tracked leaf `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/` (collect の出力: certification.json / raw-manifest / receipts / condition-gate)。
- results 稿 1 本。図の材料 = 稿 §2 の表 (8 → 6 arm の生標本・median・cv・対差・床値・判定) + leaf。

## 並列分割方針

- 段 2 plan 1 本 (read-only)、段 3 consult 2 本 (レンズ A: 正しさ境界・closed set・受理集合・凍結 pin; レンズ B: 実効性と過剰 — 同時期性・床値の適用・partial・scope 外の混入・親の (P1)〜(P7))。
- 段 5 author 1 本 (所有: 上記 A の 4 path 群。所有外は触らない)。段 6 review 2 本 + fix。
- 親: 投入・待ち・finish/collect・稿・記録。

## DW-G05 (成果物影響)

放置すると論文の失敗条件 (e) に要る「同一候補の全 workload 退行込み報告」の材料が無いままになる。本 wave の scope 外に
した partial 対応・plotter・√2 補正は、放置しても 3 workload の値・判定・参照を変えない (欠落時は明記で足りる)。

## DW-O09 (pin 閉包)

変更 file の現 sha256 (`paper_story_a2_certification.py` 95bf0a08…、submitter ac3abc8f…、job body 2a3205cf…) を repo 全体で検索: live pin 0 件 (job body の sha は過去 receipt に歴史記録として残るだけ)。path pin: `test_official_perf_closure.py` (reviewed list、追加不要)、`test_ccbench_spawn_sites.py` (spawn call 数 — 新 spawn を足さない)、`test_campaign.py` (`run_campaign` 呼出 1)、`test_hooks.py` (registry 分類)。A-2 / A-6 policy sha は `test_paper_story_a2_certification.py` と `plot_a2_certification.py` が pin するが両 file は無変更。

## 固定する床値 (JSON `between_run.cv` の全桁、結果を見る前に固定)

| workload | floor_w (between-run CV) | JSON |
|---|---|---|
| rr5 (write-heavy) | 0.009536033056996148 | output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json |
| rr50 (balanced) | 0.00725042525457718 | output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr50_rmw0.json |
| rr95 (read-heavy) | 0.0022283754708938273 | output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json |

床値 JSON の genome は `silo|BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` (stock 側と同じ設定だが `BACKOFF_FIXED=-1` の表記を持たない旧 canonical)。動作点 (records 1,000,000 / threads 48 / clocks_per_us 2100 / skew 0.9 / rmw 0) は A-2 policy の performance_common と一致。

## 追記 (段 2 後、2026-09-19): local main 657e1e5a7 を ff 取り込み

- A-2 policy の `scheduler.nodes` が 1→5 に改版された (T-2489、D2148 項 5)。A-2 policy の bytes sha256 は `f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c` (plan-out.md の表にある `cacfdd5d…` は取り込み前の値)。protocol sha `d99f08bc…` は不変。tests の pin も main 側で更新済み。
- node-local `IZANAGI_BENCH_LOCK` 候補は不採用 (`output/insights/2026-09-19/t2489-a2-nodes5-local-lock/README.md`)。既定 `~/.izanagi/bench.lock` による request 間直列化は残る。稼働中の fp-* 3 request も同 lock を使う可能性がある (job body に `IZANAGI_BENCH_LOCK` 設定なし)。
- module `paper_story_a2_certification.py`・submitter・job body は無変更。plan の行番号はそのまま有効。
