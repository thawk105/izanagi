# [T-2566] 親が実測した前提と、変更面の実アンカー表

基準 commit = `a551cdd30` (local main)。wave worktree =
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2566-tail-formal-driver`。
以下の行番号はこの commit のもの。**行番号を pin として写さず、必ず現物を開いて確かめること。**

## 1. 事前登録 (一次資料)

- `docs/b10-backoff-static-tail-preregistration.md` — §4.3 (整数カウンタ再計算)、§4.5 (結末集合)、
  §4.6 (正しさ)、§4.7 (変動係数)、§4.8 (出所)、§4.9 (3 job 同一性)、§5 (機械可読 spec)、
  §7 (失敗条件)、§8.1 (投入前条件 5 件)、§8.2 (本走 driver への要求)。
- spec の marker は HTML comment 対。開始 = `IZANAGI-B10-STATIC-TAIL-SPEC-BEGIN`、
  終了 = 同じ語に `-END`。marker 文字列を JSON の値として置いてはならない。
- 文書は main に commit 済み。本 wave では 1 bit も変えない。

## 2. 投入前条件 5 件の現状 — 親が explore の成果物を直に読んで確認した

対象 = `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/` 配下の balanced 走
(campaign slug `t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8`)。

- 走行記録は 25 行。stage の内訳は `build_start` 5 / `build_done` 5 / `verify_done` 5 /
  `bench_done` 5 / `commit` 5。**1 cell あたり正しさ記録は 1 本** (§8.1 条件 4 が未充足)。
- 走行記録の全文に `abort_counts_` は **0 件** (§8.1 条件 2 が未充足)。
- 性能記録 (`bench_done`) の payload key は 14 件 —
  `bench_wall_s, build_attempt_id, cv, cv_history, high_variance, leading_indicators, median_tps,
  perf_observation, rep_notes, rounds, run_cmd, settled, tps, unstable`。
  `tps` は rep ごとの数値 5 件の配列で、最初の cell では
  `[3958382, 3752160, 3727702, 3692363, 3695293]` という**整数表記**で保存されている
  (「浮動小数」と型契約に書かないこと)。`leading_indicators.abort_rate` は cell 全体で 1 値の
  丸め値。**rep ごとの整数カウンタも rep ごとの abort 率も無い。**
  この走の 5 cell の代表 abort 率は `[0.6869, 0.0404, 0.211, 0.0145, 0.0268]` で、
  **cell ごとに違う。1 つの cell の値を走全体へ一般化しないこと。**
- 正しさ記録 (`verify_done`) の payload key は
  `aborts, anomalies, build_attempt_id, certified, commit_witness, commits, proof_surfaces,
  verdict, workload`。`workload` は `{"tag": "legacy"}` で、これが §4.6 が要求する mode 座標の
  比較基準である。`commits` / `aborts` は整数 (**最初の cell では** 630878 / 240566。
  cell ごとに違う)。`verdict` は `"serializable"` であり `"certified"` ではない。
  **正しさの権威は `payload.certified is True` であって `verdict` の文字列ではない。**
- 走行記録 1 行の exact key 集合は `env_tag, payload, stage, ts, variant` の 5 件。
  payload を除いた envelope 側の座標は `env_tag, stage, ts, variant` の 4 件。
  campaign id は layout root の basename から、lock digest は campaign の施錠 file から導出する
  (既存 loader の実装がそうしている)。§4.8 の「envelope から導出」はこの容器のことであって、
  JSON 行の top-level key だけを指すのではない。
- spec を parse する consumer は repo 内に存在しない (§8.1 条件 1 が未充足)。
- observation ごとの出所 field は発行されていない (§8.1 条件 3 が未充足)。

## 3. 変更面の実アンカー表

### 既存の同族 driver (受理集合を変えてはならない)

- `orchestrator/campaign/backoff_extended_sweep.py` (1543 行) — 既存 3 系列が同居する。
  `EXTENDED_SWEEP_US` (55 行)、`encode_static_backoff_us` / `decode_static_backoff_us` (64/71 行)、
  `EXTENDED_RUN_KIND` / `T2266_RUN_KIND` / `T2418_RUN_KIND` / `RUN_KINDS` (81-84 行)、
  `T2418_REPORT_SCHEMA` (95 行)、`WORKLOADS` (104 行)、`MEASUREMENT_SEEDS` (112 行)。
- `_T2418RepCapture` (789 行) — `campaign_pipeline.measure_point` と
  `calibrator_runner.parse_abort_rate` を差し替えて rep ごとの abort 率を**実行中に捕捉**し、
  report へ直接書く。走行記録には載らない。これが §4.3 が「再構成できない」と書いた経路である。
- `_load_t2418_report_points` (1023 行) — 採用済み記録から点を組み立てる loader。
  `state.committed_verify` は**リスト**で、複数本の正しさ記録を既に表現できる。
  campaign id は layout root の basename から取っている。
- `materialize_t2418_report` (1258 行)、`run_workload` (1331 行)、`main` (1490 行)。

### 事前登録 consumer の先例

- `orchestrator/campaign/b10_backoff_shape_sweep.py` — `_SPEC_BLOCK_RE` (358 行) が
  marker と ```json fence を正規表現で 1 個だけ取り出す。`parse_preregistration` (1113 行) が
  key 集合を exact で閉じる。`load_preregistration` (1763 行) が canonical path・symlink 拒否・
  祖先関係・作業木 bytes と commit blob の一致を検査する。
- **ただし hash の定義が違う。** 先例の `prereg_blob_sha` は `git rev-parse <commit>:<path>` の
  **Git blob ID**。本件の `document_blob_sha256` は **file の raw bytes の SHA-256** で
  Git の blob header を含めない。両者は別の値であり、取り違えると別の束縛になる。
- 正規表現アンカーの閉包 pin は整形変更で外れる。先例をそのまま写さず、本件の marker 契約
  (HTML comment 対 + fence 2 行の除去) に合わせて書くこと。

### rep ごと整数カウンタの経路

- `orchestrator/calibrator/benchparse.py` — `abort_rate` (66 行) は `abort_counts_` /
  `commit_counts_` を既に知っており、`abort_rate` key が欠損か `-nan` のときだけ生カウントから
  再計算する。**丸め値が印字されている限り丸め値を返す。**
- `orchestrator/calibrator/runner.py` — rep ごとの観測 dict は 938-1012 行あたりで組み立てられ、
  `rep_index` / `returncode` / `execution_failure` / `counter_status` / `missing_perf_events` /
  `perf_raw` / `throughput` を持つ。CCBench の metrics dict は同じ scope に在る。
- `orchestrator/campaign/pipeline.py` — 性能記録の payload key 集合は exact 閉包で、
  `_BENCH_DONE_REQUIRED_PAYLOAD_KEYS` (1248 行) / `_BENCH_DONE_CONDITIONAL_PAYLOAD_KEYS` (1254 行) /
  `_BENCH_PAYLOAD_EXTRA_KEYS` (1257 行、現在は `screening_disabled` の 1 件だけ) に分かれる。
  `_assert_bench_done_payload_keys` (1265 行) が missing / unexpected の両方を拒否する。
  `_assert_bench_payload_extra_keys` (1277 行) は extra 側にも exact 一致を要求するので、
  呼び手が key を 1 つ足すだけでは通らない。
- これらの閉包は `orchestrator/tests/test_layer3_report.py` が AST で pin している
  (993-1093 行あたり、`bench_payload_extra` の呼び順と assert の引数名まで)。

### 正しさ反復と mode 座標

- `orchestrator/campaign/pipeline.py` — 正しさ workload の `reps` 既定は 1 (151 行)。
  `_run_one_repetition` (2117 行) / 反復駆動 (2150-2291 行) が反復ごとに 1 本の正しさ記録を出す。
  `_project_repetition_outcome` (2087 行) が記録を書き出す。
- したがって「1 cell 5 本」は既存の反復機構で満たしうる。**新しい反復機構を作らない。**

### exact 閉包の登録簿 (新規 module を置くなら必ず触れる)

- `orchestrator/tests/test_official_perf_closure.py` — `_REVIEWED_PERF_FILES` (44 行〜) は
  frozenset の exact 閉包。`_REVIEWED_PREDICATES` (128 行〜) は path・関数・呼び先・回数の組。
- `orchestrator/tests/test_p3_build_authority_cli.py` — `MACHINE_CALLERS` (147 行) /
  `MANUAL_BUILD_FILES` (157 行) / `ADMITTED_MANUAL_BUILD_FILES` (170 行)。
- `orchestrator/tests/test_ccbench_spawn_sites.py` — `_DIRECT_SAFE_ALLOWLIST` (46 行) 等の
  Counter による exact 在庫。既存 driver の Git 問い合わせが 1 件登録済み。
- `orchestrator/tests/acceptance_duration_ledger.json` — 新規テスト file は登録が要る。
- `docs/test-environment-coincidence-ledger.md` (333 行) — 同時実行の同居関係。

### 契約 loader 束縛 (運用上の罠)

- `orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` (49 行) に
  `pipeline.py` / `wal.py` / `loop.py` / `ident.py` / `artifact_admission.py` / verifier 一式が入る。
- `orchestrator/campaign/contract_loader_binding.py` の `verify_live_contract_loader_binding`
  (535 行) は**作業木の file と HEAD commit の blob を照合する**。これらを編集したまま commit せずに
  焦点走を回すと、実装の回帰ではない赤が広範囲に出る。**編集したら焦点走の前に commit すること。**

## 4. 本 wave で使ってよい実測入力

- 既存 explore の走行記録・施錠 file・report (上記 path)。読み取り専用で使う。
- 新規の計算ノード計測は行わない。本走の投入も行わない。

## 5. 段 3・段 4 で訂正した点 (この節が最新。上の本文と食い違えばこちらを採る)

- **契約 loader の束縛対象には `orchestrator/calibrator/runner.py` も含まれる。**
  `CONTRACT_LOADER_RELATIVE_PATHS` は 40 件以上あり、`loop.py` / `pipeline.py` / `wal.py` /
  `ident.py` に加えて calibrator 側の `runner.py` / `perf_preflight.py` / `stability.py` なども入る。
  照合先は binding に記録された commit の blob であって、常に HEAD ではない。
- **`orchestrator/campaign/loop.py` の `run_campaign` の signature には correctness workload を
  渡す引数が無い。** 1 cell 5 本には配線の追加が要る。反復機構自体は `pipeline.py` に既にある。
- **`orchestrator/tests/test_campaign.py` に `expected_inventory` と `expected_run_calls` という
  exact Counter がある。** 新規 module を足すなら両方に登録が要る。
- **`orchestrator/calibrator/runner.py` には測定関数が 2 つある** (`capture_measure_point` と
  通常の `measure_point`)。片方だけ見ない。
- **探索成果物には整数カウンタを含む生 stdout が無い** (親も検索して 0 件を確認)。
  条件 2 の入力は `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/run-R01.log` 系列を使う。
  親が実在と 4 値 (abort `24435129` / commit `2270481` / 印字率 `0.9150` /
  throughput `756827`) を現物で確かめた。R02〜R05 も同形式で実在するが、**throughput が
  76 万〜1071 万と散らばるので cohort の正例には使えない** (保存経路の実測にだけ使う)。
- **`docs/test-environment-coincidence-ledger.md` は過去 wave の先送り一覧であって
  新規 test の常設登録簿ではない。** 今回の追記は不要。
- **manual-build 在庫 (`MANUAL_BUILD_FILES`) は `--build` を含む file を全文文字列で抽出する。**
  新 module が CMake `--build` を直接実行しないなら変更不要。必要なのは machine caller 登録。
- **`orchestrator/tests/test_screening_opt_in.py` は `loop.py` の全文を読んで
  `ScreeningConfig` と `screening=` の不存在を検査する。** 焦点走に含める。期待値は緩めない。
