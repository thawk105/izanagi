# 段 4 裁定 — [T-2797] plan v2 と変異事前登録

作成 2026-09-20 20:05 JST。入力: `brief.md`、`brief-addendum-1.md`、`codex/s2-plan.md`、`codex/s3-consult-A.md` (sol)、`codex/s3-consult-B.md` (luna)。
裁定 inbox 再走査: local main は `b9904a5f8` まで進んだ (docs のみ、対象 code 5 file の差分 0)。D2186 項 4 (pin 比較の正規化は据え置き、
「既知の B-5 要件と T-2797 の残部品は stock-baseline class を要求しない」) と項 5 (production file を変えた wave は inventory test 4 群を焦点走に含める) を取り込む。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 / B1 | BUILD_START 不在から未投入を導けない (投入後・最初の WAL record 前の中断) | real / must-fix | **採用**: `p3_s4_loop` が B-5 mode で `run_campaign` 直前に sidecar `pipeline-submitted.json` を durable に書く。driver はこれと WAL で分類 |
| A2 / B2 | 同 slot の subprocess retry は残存 claim に拒否される | real / must-fix | **採用**: slot key に物理 attempt を含める (`…\|attempt-<t>`)。論理 slot は台帳で別記。claim 削除禁止 |
| A3 / B6 | 45 分無応答を一律機械故障にしない | real / must-fix | **採用**: 無応答 timeout = 分類不能欠測 (`proposal-wait-timeout`)、retry なし、系列終了。空出力・schema 不合格は親が `.rejected.json` で A 消費を閉じる |
| A5 | Tier0 未実装の費用試走 | real / should | 採用: 台帳 header に `tier0_status="not-implemented"`。§10 完全充足とは書かない |
| A7 追加 | current_perf / baseline / 出所も継承検査に含める | real / should | 採用: `assert_inherited_inputs` は whiteboard に加え `current_perf` と coder `baseline` を台帳の値と照合 |
| A8 | 親の介入禁止は機械保証しない旨の明記 | real / should | 採用 (insight と台帳 header の `limits`) |
| A9 | 重み表の床確定は受入時の証拠 | 根拠不足 / should | 採用: 1000 要素の prec 100 / 130 一致・表・sha256 を材料 JSON に残す |
| A12 追加 | machine mode は L:3145 の coder opt-in guard も変更対象 | real / should | 採用 |
| A13 / B8 | 115 s / 12〜14 分は外挿、8h/3h は暫定管理値 | real / should | 採用: 記録では「外挿」「暫定」と書く。本走上限は試走の実測 max から |
| A14 | P7 の反証対象の書き方 | nit | 採用 |
| B3 | P9 は 2 seam では完成しない | real / should | 採用: seam は §2 のとおり 4 点 (slot key・machine mode・sidecar・B-5 mode の skip 拒否 + rounds 明示) |
| B4 | TJ の変異行 (:698–704, :939–951) も更新、新 shell test | real | 採用 |
| B5 | launcher は `-v` で env を明示、dry-run は最終 argv | real / should | 採用 |
| B7 | 待機費用と allocation 残時間 | real / should | 採用 (部分): 待機は 1 opportunity 45 分上限 × 最大 1 回。残時間で新規待機・評価を始めない判定は `IZANAGI_RESERVATION_*` の deadline (`SH:292–321` が計算) を driver が env から読んで「残り < 見積り所要なら series-end (`allocation-exhausted`)」。新しい 3600 秒制限にはしない |
| B9 | pin 閉包の追加面 (`test_campaign_import_invariant.py:883,931`、`test_pegasus_tools.py:540–558`、`test_p3_build_authority_cli.py:95–140`) | real / should | 採用: author の検査対象に加える |
| B10 / B11 | consumer は本走統計 + pilot 記述、両方 scope 内 | refuted (削減案) | 採用: A2 は §7 全部 + pilot 経路を実装 |
| B12 | `check_stop` spy 変異は P9 と両立しない | real | 採用: 挙動 test (系列履歴で次 slot が止まらない) に置換 |
| B13 | 削除候補 | real / should | 採用: hash8 事前網羅・純 verifier adapter・新 entrypoint・alias 群・汎用 retry/再配置・108 系列 launcher・発効 gate は作らない |
| A4, A6, A10, A11, B4 (既存 pin 全面赤), B5 (3h pin が禁止) | refuted の疑い | — | plan の記載を維持 |

(P1)〜(P9): P1 条件付き (attempt 分離) 採用、P2 = P9 の fresh layout 運用で停止不適用 (別 driver 不要)、P3 採用、P4 条件付き採用 (timeout 分類修正)、
P5 採用、P6 採用 (受入証拠)、P7 反証採用 (pilot 経路)、P8 暫定として採用、**P9 修正採用**。

scope 外の real 所見 (実装しない、insight §裁定パッケージ候補へ): 共通 Tier0 の exact 契約、純 verifier 計時、D2183 同 campaign stock の claim 衝突
(peer の scope)、本走の総 wall 上限・発効束。

## 2. plan v2 — 変更面と契約

### 2.1 `orchestrator/campaign/p3_s4_loop.py` (A1 所有、seam 4 点、既定経路は bytes / kwargs / 分岐 / 戻り値 不変)

1. **`--b5-slot KEY`** (str)。受理: 非空 ASCII、空白なし、`b5-generator-contrast-v1|` 始まり。`search_config["b5_slot"] = KEY` を較正 fold と同じ位置で焼く
   (identity・claim・protocol digest が slot ごとに別になる)。`--calibrated-perf --perf-workload W --verify-performance` の 3 つを必須にし、
   `--value` (supplied) / `--emit-planner-context` / `--no-build` / `--b4-reflux-ablation` と排他。`--run-iteration` または `--stock-control` のどちらかが必須。
2. **`--machine-generated-proposal`**。`--run-iteration` と `--b5-slot` が必須。`--allow-coder-derived-build` / `--coder-role` / `--knowledge-manifest` /
   `--knowledge-classification` (supplied) / `--knowledge-de-novo-claim` (supplied) と排他。効果: `build_context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)`
   (coder authority 無し)、L:3145 の「明示 opt-in が必要」guard の限定例外、`capability_resolver = _machine_proposal_capability_resolver(build_context, proposal_sha256)`
   = evidence の `src_token != STOCK` のときだけ `attest_generator_output(build_context, evidence, generator_input_sha256=sha256("p3-s4-loop-machine-proposal/v1|" + proposal_sha256 + "|" + evidence.genome_sha256))`、
   STOCK なら None (fail-closed)。proposal_sha256 = `--run-iteration` file の raw bytes の sha256。admission class = machine-generated (D2186 項 4 と整合)。
3. **`--b5-sidecar-dir DIR`** (`--b5-slot` 必須、DIR は既存 directory)。`p3_s4_loop` が B-5 mode で 2 file を書く (tmp → fsync → `os.link`/rename、既存なら rc≠0 で拒否):
   - `DIR/slot-start.json` = `{schema:"p3-s4-loop-b5-slot-start/v1", b5_slot, campaign_id, campaign_root, genome, identity_preimage_sha256, ts_utc}` — layout 確定直後
     (`drive_iteration` の `layout.ensure()` 後、`_run_stock_control_resolved` の入口)。
   - `DIR/pipeline-submitted.json` = `{schema:"p3-s4-loop-b5-submission/v1", b5_slot, campaign_id, genome, ts_utc}` — `run_campaign` 呼出しの**直前** (候補 L:2165、stock L:1986)。
4. **B-5 mode の挙動 2 点** (`--b5-slot` 指定時のみ): (a) `run_campaign` が skip を返したら `_resolve_duplicate` を呼ばず `{"outcome": "duplicate-skip", ...}` を返し rc 1
   (成功復元なし)。(b) `run_campaign(..., bench_max_rounds=3)` を明示 (§5.3 の flag 束縛; 既定経路は kwarg を増やさない = `campaign_options` に条件付きで入れる)。
   実装は keyword-only 既定 None/False の引数 (`b5_sidecar_dir=None`, `capability_resolver=None`, `b5_mode=False`) を `drive_iteration` → `_run_one_iteration_resolved` と
   `_run_stock_control_resolved` に通す。既定 None のとき `run_campaign` の kwargs は現行と同一。
   `MAX_ITER` / `MAX_WALLTIME_S` / `check_stop` / `_resolve_duplicate` 本体 / `default_cfg` / `default_perf` / `calibrated_perf` は不変。pipeline.py / loop.py / ident.py /
   build_admission.py / materializer_admission.py は不変。

### 2.2 `orchestrator/campaign/b5_generator_contrast.py` (A1 所有、新設。import 方向は b5 → p3_s4_loop、逆無し。`run_campaign` を直接呼ばない)

定数 (CLI で上書き不可): `PREREG_VERSION="b5-generator-contrast-v1"`, `COHORT_PILOT="t2797-beta-v1"`, `B_EVALUATIONS=10`, `A_PROPOSALS=30`, `N_EVAL=5`,
`BLOCK_STOCK_SESSIONS=5`, `PILOT_LOGICAL_SESSION_CAP=60`, `MAX_MACHINE_RETRIES=2`, `LLM_WAIT_S=2700`, `LLM_POLL_S=15`, `ARMS=("llm","random","sweep-matched")`,
`WORKLOADS=("write-heavy","balanced","read-heavy")`, `MACHINE_FAILURE_ABORT_REASONS=frozenset({"bench-probe-error","bench-competing-tenant"})`。

生成器: `integer_log_weights(prec)`, `weights_table()` (prec 100 と 130 の全 1000 要素一致を検査、不一致は例外), `weights_material()` (JSON: schema, formula, precisions,
weights, M, weights_sha256 (配列 bytes の sha256), python/decimal 版), `random_value(w, r, a, weights) -> (v, c)` (§4.2 逐語), `sweep_order(w, r) -> tuple[28]`,
`machine_proposal_document(arm, value, provenance: dict) -> dict` (planner: axis=MARKER_ID, direction="explore_both", magnitude="small", justification=固定文字列
"B-5 <arm> generator (mechanical); <preimage>", uncertainty=""; coder: axis, value=v, implementation=f"double now_backoff = {v};", justification 同型, confidence="low";
prior_critic_reverse=None)。`assert_no_ability_probe_material` を通る文字列にする。

slot key: `slot_key(cohort, arm, workload, series, kind, n, attempt) = f"{PREREG_VERSION}|{cohort}|{arm}|{workload}|{series}|{kind}|{n}|attempt-{attempt}"`、
kind ∈ {`stock-start` (n=1), `search` (n=a), `score` (n=1..5), `block-stock` (arm="stock", series=block, n=1..5)}。

台帳 (`b5-generator-contrast-ledger/v1`): `<ledger_root>/header.json` + `<ledger_root>/events/<000001>-<kind>.json` (連番・不変・atomic publication・上書き禁止) +
`series.json` (再生成 view)。header: cohort, purpose="pilot", arm, workload, series, block, repo HEAD, PIN, calibrated PerfConfig, verify mode, B/A/N_eval 定数,
`tier0_status="not-implemented"`, job identity (PBS_JOBID / host), `limits` (親の介入・実送達は機械保証しない)。event 必須 field: `event_seq`, `kind`, `ts_utc`,
`a`, `b`, `logical_slot`, `attempt`, `slot_key`, `proposal_path`, `proposal_sha256`, `provenance`, `campaign_id`, `campaign_root`, `variant`, `build_attempt_id`,
`wal_sha256`, `outcome`, `failure_class`, `quality`, `fitness_tps`, `anomalies`, `whiteboard_entry`, `timing`, `note`。
kinds: `series-start`, `stock-start`, `proposal-opportunity`, `proposal-rejected`, `pipeline-submitted`, `evaluation-result`, `machine-retry`, `endpoint-fixed`,
`score-session`, `series-end` (reason ∈ {`b-complete`, `a-exhausted`, `grid-exhausted`, `stock-unestablished`, `proposal-wait-timeout`, `inheritance-mismatch`,
`allocation-exhausted`, `unclassified-missing`})。

分類 (`classify_slot(sidecar_dir, campaign_root, expected_reps, expected_genome)`):
- slot-start 無し → `pre-start-failure` (機械故障、同論理 slot を attempt+1 で最大 2 回 retry、stderr 尾を evidence に)。
- slot-start あり・submitted 無し: WAL に diff-reject / grammar-reject record → `rejected-preprocess` (A のみ)。record 無し → `unclassified-missing` (A 消費済み、B 無し、retry 無し)。
- submitted あり: WAL terminal = COMMIT → `certified` + `quality` = `classify_session(bench_done)` (`len(tps) != reps ∨ unstable ∨ settled is not True` → `quality-missing`、
  endpoint 資格なし、B 消費); ABORT reason ∈ anomaly 系 → `anomaly` (B 消費); reason ∈ `MACHINE_FAILURE_ABORT_REASONS` → `machine-failure` (同 slot retry +2、論理 B は 1 回だけ);
  他の ABORT → `build-failed` / `bench-aborted` / `aborted` (B 消費、retry 無し); terminal 無し → `submitted-unresolved` (B 消費、score 無し); CLI が duplicate-skip →
  `duplicate-skip` (fail、B 消費扱いにしない・成功にしない・retry 無し・系列は継続しない = `unclassified-missing` で series-end)。
- stock 成立 = `certified` ∧ variant == variant_id(stock genome) ∧ BUILD_START `src_token == STOCK` ∧ quality 正常 ∧ fitness 有限正。不成立 → `series-end(stock-unestablished)`。

系列 driver (`run_series(arm, workload, series, block, *, ledger_root, prebuild_receipt, repo_root, k2: K2Args|None, runner: SlotRunner)`):
stock-start → (A < 30 ∧ B < 10 の間) opportunity → proposal (random / sweep: 生成; llm: handshake) → `assert_inherited_inputs` (llm) → slot subprocess
(`[python, "-B", "-m", "orchestrator.campaign.p3_s4_loop", "--run-iteration", P, "--isolate-worktree", "--fetchcontent-prebuild-receipt", R, "--calibrated-perf",
"--perf-workload", W, "--verify-performance", "--b5-slot", KEY, "--b5-sidecar-dir", D] + (llm: ["--allow-coder-derived-build", "--knowledge-manifest", M,
"--coder-role", "coder-v4-autonomous-k2", "--knowledge-classification", C, "--knowledge-de-novo-claim", N] | random/sweep: ["--machine-generated-proposal"])`,
cwd = repo_root) → classify → 台帳 → 次。sweep は hash 順の先頭から順に、候補起因の不通過なら次点 (11 点目以降も)、機械故障は同点 retry、28 点枯渇で
`grid-exhausted`。random は a ごとに `random_value(w, r, a)`。終了後 `select_endpoint` → `endpoint-fixed` → score slot × 5 (同 proposal bytes、kind=score) →
`series-end`。runner は subprocess 実行の唯一の seam (test は fake runner で sidecar / WAL を合成)。
LLM handshake (`<ledger_root>/handshake/`): job が `request-<a>.json` (a, next_evaluation k, expected_whiteboard, current_perf + source, deadline_utc) を atomic 公開 →
15 s 間隔で `proposal-<a>.json` (+ `inputs-<a>.json` = {planner_input, coder_input}) か `proposal-<a>.rejected.json` ({reason}) を待つ (上限 2700 s) →
rejected → A 消費 `proposal-rejected` → 次 a; timeout → `series-end(proposal-wait-timeout)` (retry 無し); proposal → `assert_inherited_inputs(ledger, planner_input,
coder_input, next_evaluation=k)` (whiteboard = 評価 1..k−1 の射影と順序・値・全 field 一致、`delta_pct` None、`current_perf` と coder `baseline` = 台帳の
「直近の certified かつ品質正常な評価、無ければ stock-start」の値、`k2_critic_diagnosis` は planner / coder で同一) → 不一致は `series-end(inheritance-mismatch)`。
評価後 `slot-<k>.json` を公開 (outcome, quality, fitness, whiteboard_entry, campaign_root, digest path)。
allocation 残時間: `IZANAGI_RESERVATION_*` の deadline を env から読み、残りが `SESSION_BUDGET_S` (定数 1800) 未満なら新しい待機・評価を始めず `series-end(allocation-exhausted)`。
block stock (`run_block_stock(workload, block, *, ...)`): kind=block-stock × 5、各 stock 成立判定、台帳 `block-stock` header。
計時 (`timing`): subprocess wall (monotonic)、WAL から build 区間 (`build_start`→`build_done`)、verify 区間 = 隣接 `verify_done` の差 (tag 付き、legacy / performance rep i)、
verify 全区間、`bench_done.payload.bench_wall_s`、bench 周辺込み区間。名称は「trace+verifier+周辺処理 区間」。欠落 rep は欠測 / 打切りとして残す。
CLI: `python -m orchestrator.campaign.b5_generator_contrast run-series --arm --workload --series --block --ledger-root --fetchcontent-prebuild-receipt [--knowledge-manifest --knowledge-classification --knowledge-de-novo-claim]`
と `run-block-stock --workload --block --ledger-root --fetchcontent-prebuild-receipt`、`weights-material --out PATH`、`expected-inputs --ledger-root --next-evaluation k --out PATH`
(親が planner 入力を組むための射影出力)。K2 argv は llm のみ必須、他 arm で指定は rc=2。

### 2.3 `orchestrator/campaign/b5_generator_contrast_report.py` (A2 所有、新設)

plan §8 のとおり: `build_report(ledgers, *, purpose)`, `exact_sign_flip_p`, `holm_six`, `stock_cv_floor`, `pair_differences`, `decide_comparison` (§7.4 の順 1〜8)、
anomaly の横断失格集合、fallback 対の主 / 副解析切替、pilot 経路 (`registered_judgment="not-applicable-pilot"`、記述統計 = A/B・論理 session・物理 attempt・品質 round・
stock / endpoint / score・fallback・anomaly・欠測・stock 5 件の記述 CV (本走 f(w) とは呼ばない)・session 所要分布と max・build / bench / verify 区間・job Elapse・LLM 手番)。
入力は A1 の台帳 schema。合成データの固定例 (11/12 正 → 13/4096、10/12 → 79/4096 ほか)。

### 2.4 `tools/pegasus/p3_s4_loop_pegasus.sh` + `tools/pegasus/b5_contrast_launch.py` (A3 所有)

job body: `IZANAGI_S4_B5_MODE` ∈ {`series`, `block-stock`} (未設定だけ off、設定済み空値・他値は rc=2、repository path 解決より前)、`IZANAGI_S4_B5_ARM`
(series: llm / random / sweep-matched; block-stock: stock)、`IZANAGI_S4_B5_WORKLOAD` (3 値)、`IZANAGI_S4_B5_SERIES` (1..12、先頭ゼロなし)、`IZANAGI_S4_B5_BLOCK` (1..3)、
`IZANAGI_S4_B5_LEDGER_ROOT` (非空絶対 path、repository 外)。B-5 mode では `IZANAGI_S4_PROPOSAL_PATH` / `IZANAGI_S4_FIXTURE_VALUE` / `IZANAGI_S4_STOCK_CONTROL=1` の併用を拒否、
K2 env は arm=llm で必須・他 arm で禁止 (`SH:95–96` の proposal-path 必須条件は B-5 llm だけ例外)。prebuild receipt の後、既存 3 分岐の**前**に B-5 分岐 1 箇所:
`"$PY" -B -m orchestrator.campaign.b5_generator_contrast <subcommand> ... || b5_rc=$?; exit "$b5_rc"`。既存 3 経路の argv は bytes 不変。TJ: required に B5 pins、
stage order、B-5 呼出し 1 箇所、既存変異 (:698–704, :939–951) の保持、新 shell test (4 mode 各 1 起動、非零 rc の trap 転記、旧経路不実行、不正 env の rc=2)。
`#PBS -l elapstim_req=03:00:00` は不変。launcher: `validate_submit_tree`, `build_job_environment` (必要 env を dict で、`-v k=v,...` に整形), `qsub_argv(spec, tree)`
(`qsub -v ... -l elapstim_req=<08:00:00|03:00:00> -o <evidence>/job.stdout -e <evidence>/job.stderr tools/pegasus/p3_s4_loop_pegasus.sh`、`-q`/`-A`/`-b` は script 指示行に任せる
(既存 K2 投入と同型)), `pilot_jobs(workload, ledger_root, evidence_root, k2)` = 4 job 固定 (random / sweep-matched / llm / block-stock)、`--dry-run` は最終 argv と env を印字して
qsub も mkdir もしない。`PILOT_LOGICAL_SESSION_CAP` の検査 (3×16+5=53 ≤ 60)。admission_registry.json への launcher 登録は親が既存 login 側 tool の class に合わせて行う (A3 は class 候補を報告)。

### 2.5 test file (所有)

A1: `orchestrator/tests/test_b5_generator_contrast.py` (新設、`__main__` harness、subprocess は `-B` + `PYTHONDONTWRITEBYTECODE=1`)、`orchestrator/tests/test_p3_s4_loop.py` (seam の test 追加)、
`orchestrator/tests/test_official_perf_closure.py` (述語に該当した場合の inventory 追加のみ)。A2: `orchestrator/tests/test_b5_generator_contrast_report.py`。
A3: `orchestrator/tests/test_p3_s4_loop_job_contract.py`、`orchestrator/tests/test_b5_contrast_launch.py`。
親: docs (`tools/pegasus/README.md`、insight、spool)、`tools/pegasus/admission_registry.json`。

## 3. 変異事前登録 (DW-M01、実装前)

| ID | 位置 | 変異 | 殺す test (単位内) |
|---|---|---|---|
| M0 | b5 module | comment 1 行追加 (等価対照) | SURVIVED 期待 |
| M1 | `integer_log_weights` | `2**128` → `2**127` | 重み表の固定期待値 (m_1 と sha256 を独立定数で pin) |
| M2 | `random_value` | preimage 区切り `\|` → `/` | 既知 vector (親が独立 script で算出した (w,r,a) → v) |
| M3 | `random_value` | `U < L` → `U <= L` | U == L の境界 vector (引き直しが起きること) |
| M4 | `sweep_order` | key を数値順に | 固定 (w,r) の期待順序 vector |
| M5 | `classify_session` | `or` → `and` | 単一条件の負例 3 本 (reps 欠落 / unstable / settled None) |
| M6 | `classify_slot` | submitted を certified 時だけ B と数える | submitted + ABORT で B=1 の test |
| M7 | `select_endpoint` | 同値 tie を value 降順 | tie test |
| M8 | `run_series` | score を探索 median で置換 | score session の median を使う test |
| M9 | `assert_inherited_inputs` | 順序検査を外す | 順序交換で拒否する test |
| M10 | `p3_s4_loop.main` | `--b5-slot` を search_config に焼かない | 2 slot で campaign_id が異なる test |
| M11 | `p3_s4_loop.main` | machine mode で coder authority を発行 / guard 例外除去 | machine mode で `build_run_context` の authority が None である test / opt-in 無しで通る test |
| M12 | `_run_one_iteration_resolved` | sidecar `pipeline-submitted` を run_campaign の後に書く | run_campaign を例外で止める fake で marker 実在を見る test |
| M13 | job body | B-5 mode で旧候補分岐へも落ちる | TJ 実 shell test (driver 呼出し 1 回) |
| M14 | job body | 設定済み空値 `IZANAGI_S4_B5_MODE` の拒否除去 | TJ rc=2 test |
| M15 | `run_series` (handshake) | timeout を機械故障 + retry に | timeout → `proposal-wait-timeout` / retry 0 の test |
| M16 | report | Holm 族 6 → 5 | 固定例 (13/4096 系) の補正 p test |
| M17 | report | pilot で優越を返す | `not-applicable-pilot` test |
| M18 | launcher | cap 60 → 61 / 4 job → 5 job | cap test |
| M19 | `classify_slot` | `duplicate-skip` を certified 扱い | duplicate-skip が fail になる test |

各変異は「その単位の test だけが殺す」ことを実装後に確認 (DW-M01 の単一理由性)。fix 後は DW-M07。

## 4. 実行順

A1 (core + p3_s4_loop seam + tests) → A2 (report) ∥ A3 (job body + launcher + TJ) → 統合 → 焦点走 (inventory 4 群を含む、D2186 項 5) → 段 6 review 2 本 → fix →
変異 matrix → 受入投入 → 試走 4 job (submit-tree = 統合 commit) → 記録 → land。
