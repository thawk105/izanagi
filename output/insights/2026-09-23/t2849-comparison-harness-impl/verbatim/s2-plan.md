# 段 2 実装プラン

対象は brief の単位 1〜8。以下の行番号は現 worktree の変更前コードを指す。静的確認と束の SHA 照合のみ実施し、書込み・テスト・計算投入はしていない。

**方針は、既存評価入口への小変更と、S1 専用の兄弟 module 3 本で実装する。** B-5 module・事前登録・発効束・役割定義は編集しない。P2 を採用する場合、D2220 の critic 還流と初期点一覧の射影は未実装として明記する。

## 1. コード確認で判明した注意点

| 箇所 | 確認結果と実装への帰結 |
|---|---|
| `orchestrator/campaign/b5_generator_contrast.py:106–137` | random / sweep は接頭辞だけでなく系列 1..12・A≤30 を固定している。関数を直接呼んで名前空間だけ変える引数はない。重み表・格子を import し、hash 抽選部分だけ兄弟 module に置く。 |
| 同 `:208–249` | `SeriesLedger` は module global の schema を参照する。継承だけでは schema を変更できない。global の差替えはせず、同じ保存方式・event 契約の小さい専用実装を置く。 |
| 同 `:478–497` | 継承照合は評価 2 以降で K2 診断を必須にする。K0 では呼べない。whiteboard と current_perf の照合部分を兄弟側に置く。 |
| `orchestrator/campaign/p3_s4_loop.py:3484–3486,2976–2984` | `--coder-role` は K2 専用。K0 の role は親側で `coder-v4-autonomous` を指定し、評価 CLI では `--coder-role` 自体を省略する。 |
| `b5_generator_contrast.py:338–363` | `BACKOFF_FIXED` がない genome も候補と判定し、Tier0 を要求する。exact な参照 genome は、この分類関数へ無加工で渡せない。参照専用の分類処理が必要。 |
| 同 `:441–445` | endpoint の最後の tie-break は `b`。初期点は両方 B=0 なので、兄弟側では実 slot 順を tie-break に使う。 |

これらを B-5 module の編集、偽の Tier0 証拠、参照 genome への余分な flag 追加で回避しない。

## 2. 固定する interface

### 2.1 評価 CLI

既存の `--b5-slot` を拡張し、接頭辞として次の二つだけを受ける。

```text
b5-generator-contrast-v1|
t2849-harness-v1|
```

`--b5-sidecar-dir`、sidecar schema、`search_config["b5_slot"]` は維持する。新しい slot 用 flag や sidecar schema は作らない。

harness の slot key：

```text
t2849-harness-v1|<cohort>|<arm>|<workload>|<series>|<kind>|<n>|attempt-<t>
```

- arm：`random`, `sweep`, `bo`, `evolution`, `llm`。共有対照のみ `stock`, `reference`。
- kind：`stock-start`, `initial`, `search`, `score`, `block-stock`, `block-reference`。
- series：正整数。共有対照では block 番号。
- n：初期点順、提出機会 a、再計測順など、kind ごとの論理 ordinal。
- t：0..2。retry で cohort・arm・workload・series・kind・n・proposal bytes を変えない。

新規 flag は **`--reference-genome PATH.json`**。`--stock-control` の明示拡張とし、harness slot・stock-only の場合だけ使う。

```json
{
  "protocol": "silo",
  "flags": {
    "BACK_OFF": 0,
    "NO_WAIT_LOCKING_IN_VALIDATION": 1,
    "NO_WAIT_OF_TICTOC": 0,
    "WAL": 0
  }
}
```

exact flags：

| workload | BACK_OFF | NO_WAIT_LOCKING_IN_VALIDATION | NO_WAIT_OF_TICTOC | WAL |
|---|---:|---:|---:|---:|
| balanced / write-heavy | 0 | 1 | 0 | 0 |
| read-heavy | 0 | 0 | 1 | 0 |

出典は `output/s1-freeze/known_axes_freeze.json:90–98,316–324,542–549`。**`BACKOFF_FIXED=-1` は足さない。** 旧 `reference_fitness_tps` も実行入力にしない。

slot argv の差は以下に限定する。

| slot | 基本入口に追加する argv |
|---|---|
| 機械生成の探索・初期点 | `--run-iteration PATH --machine-generated-proposal` |
| K0 LLM の探索 | `--run-iteration PATH --allow-coder-derived-build` |
| 系列開始 / block stock | `--stock-control` |
| 参照 | `--stock-control --reference-genome PATH` |
| endpoint 再計測 | 選ばれた proposal の由来に対応する上記入口 |

共通部分は B-5 `slot_argv`（`:512–516`）と同じ隔離・prebuild・較正・performance verify・sidecar 引数とする。LLM arm の初期点が endpoint になった場合も、その機械生成 proposal を coder 由来へ付け替えない。

### 2.2 系列 driver

新規 `orchestrator/campaign/t2849_comparison_harness.py`：

```text
python3 -B -m orchestrator.campaign.t2849_comparison_harness run-series
  --cohort ID --cohort-root PATH --ledger-root PATH
  --arm {random,sweep,bo,evolution,llm}
  --workload W --series R --block Q
  --a-limit A --b-limit B --initial-values 5 10 --n-eval N
  --fetchcontent-prebuild-receipt PATH

... run-block-controls
  --cohort ID --cohort-root PATH --ledger-root PATH
  --workload W --block Q --n-eval N
  --fetchcontent-prebuild-receipt PATH

... expected-inputs
  --ledger-root PATH --next-evaluation B --out PATH

... aggregate
  --cohort-root PATH --job-costs PATH --out PATH
```

A・B・N は必須入力。初期点は本 scope の `[5,10]`、k はその長さとして header に記録する。系列数の上限・割当順・登録 schedule は実装しない。R0 専用で、R1 切替も追加しない。

`run-block-controls` は同一 workload × block の stock と参照を測る。stock は設計の 5 session、参照は `N` fresh session として各 median を報告する。

### 2.3 台帳と費用

schema は `t2849-harness-ledger/v1`。B-5 と同じ `header.json`、番号付き immutable `events/`、再生成可能な `series.json` を使う。別の監査台帳は作らない。

event kind は B-5 `:60–64` の集合を維持する：

```text
series-start, stock-start, proposal-opportunity, proposal-rejected,
pipeline-submitted, evaluation-result, machine-retry, endpoint-fixed,
score-session, series-end, slot-attempt-start
```

- 初期点：`evaluation-result`、`slot_kind="initial"`、`a=b=0`、`whiteboard_entry=null`。
- 探索：`evaluation-result`、`slot_kind="search"`、whiteboard の iteration は b。
- 共有参照：`score-session`、`slot_kind="block-reference"`。
- 種別の判別を event kind だけに依存させない。

field は B-5 `EVENT_FIELDS`（`:70–75`）を維持し、既存の拡張 field として以下を固定する。

```text
slot_kind, n, value, genome, submitted, argv, returncode,
bench_payload, src_token, duplicate_of, proposal_origin
timing.started_utc / ended_utc / available_utc
timing.subprocess_wall_s / generator_wall_s / proposal_wait_wall_s
provenance.role_calls
provenance.human_interventions
```

`role_calls` は `{role, count, wall_s, reported_tokens}` の列、介入は `{at_utc, action, note}` の列。未報告値は null とし、0 と混同しない。親の保存済み役割実行記録から渡し、役割呼出しを tool 自身で行わない。

header の `job.PBS_JOBID` を費用の結合 key にする。`--job-costs` は scheduler の記録から親が与える `{PBS_JOBID: {elapse_s, queue_wait_s, source}}`。集約時に job ごとに一度だけ加算し、slot wall を加えて二重計上しない。job 終了前の wall を Elapse と称しない。

### 2.4 保全 opt-in

新規 env：

```text
IZANAGI_TRACE_ARCHIVE_ROOT=/absolute/persistent/path
```

未設定なら従来どおり。保全のための CLI・WAL field・proof schema は増やさない。

```text
ROOT/<campaign-id>/<variant>/<build-attempt-id>/<tag>/<temporary-dir-name>/
  archive/<元の相対path>.zst
  inventory.json
```

inventory は反復単位の一ファイル。元 file ごとの相対 path・sha256・bytes・行数、archive path・圧縮 bytes、workload flags・genome・trace binary SHA・保全状態を記録する。これは保全物の目録で、certification の根拠には加えない。

圧縮は shell を使わず `zstd -T0 -3`。全 file を streaming で処理する。成功後に一時 dir を削除する。失敗時は verdict を変えず、保全失敗を inventory / stderr に記録し、未保全の原本を消さない。

## 3. U-A：評価入口・trace 保全

### 既存 file の変更

| file:line / 関数 | 変更 |
|---|---|
| `orchestrator/campaign/p3_s4_loop.py:3449–3456` / `main` | `--reference-genome` を追加。既存 slot flag は改名しない。 |
| 同 `:3540–3583` | slot の二接頭辞受理。参照は harness の stock-only に限定し、pair / proposal と混ぜない。既存 B-5 の条件は維持。 |
| 同 `:3700–3701` | 参照指定時だけ canonical genome を search_config に加え、参照違いが campaign identity に入るようにする。 |
| 同 `:3756–3761,3416–3429` | 参照指定時だけ stock 経路へ `reference_genome` keyword を渡す。省略時には新 keyword を渡さない。 |
| 同 `:2290–2314` / `_run_stock_control_resolved` | keyword-only `reference_genome=None` を追加。None の既存 genome 式はそのまま。指定時は exact genome を用いる。 |
| 同 `:2322–2365` | stock と同じ patch・既存 condition gate・`run_campaign` へ渡す。別の評価 callsite を増やさない。 |
| `orchestrator/campaign/pipeline.py:2149–2178` / `_run_one_repetition` | 検証結果の投影後、削除前に opt-in 保全を挿入。例外終了時に残った trace も対象。 |

保全 helper は `pipeline.py` 内に `_preserve_trace_directory(...) -> bool` として置く。新しい campaign module を pipeline から import しない。新規公開 API / CLI は不要。

**参照の注意：** `p3_s4_loop.py:426–428` は `BACKOFF_FIXED` 不在時に既存 condition gate を適用しない。そこへ sentinel を足して gate を強制する変更はしない。参照も `:2357–2364` の同じ検証・計測へ進む。

### 新規試験

- `orchestrator/tests/test_t2849_loop_entry.py`
  - 二つの slot 接頭辞、既存 B-5 argv、machine / K0 admission。
  - 参照 3 workload の exact genome が `run_campaign` まで届く。
  - 参照なしの stock kwargs・search_config・genome 不変。
  - 参照と候補の同時指定を受けない。
- `orchestrator/tests/test_t2853_trace_preservation.py`
  - 未設定時の呼出し・出力・cleanup 不変。
  - certified / anomaly / parse failure の保全。
  - 複数 rep の archive 非衝突、空 file・末尾改行なしの bytes / 行数。
  - zstd 失敗時の原本保持と verdict 不変。
  - anomaly 後に bench へ進まないこと。

`orchestrator/tests/test_p3_s4_loop.py` は変更しない。

## 4. U-B：系列制御・生成器・集約

### 新規 file と公開関数

**`orchestrator/campaign/t2849_comparison_harness.py`**

```text
SeriesLedger
slot_key
slot_argv
machine_proposal_document
reference_genome
classify_reference_slot
expected_inputs
assert_inherited_inputs
run_series
run_block_controls
aggregate
main
```

B-5 から直接呼ぶもの：

- `weights_table`、`validate_backoff_value`、`classify_session`。
- 候補・通常 stock の `classify_slot`、`wal_timing`。
- `default_runner`。新しい評価 subprocess callsite を増やさない。
- 保存 byte 形式等の既存 helper は必要箇所で import して使う。

参照分類は B-5 `:299–438` と同じ sidecar / WAL / identity / terminal / 品質の分類を用い、候補専用 Tier0 条件だけを持たない小さい専用関数にする。`classify_session` と `wal_timing` は直接再利用する。新しい受理規則は作らず、参照の genome・variant を偽装しない。

**`orchestrator/campaign/t2849_generators.py`**

```text
random_value(workload, series, a, *, namespace=...)
sweep_order(workload, series, initial_values)
matern52(x, z, length_scale, signal_variance)
gp_posterior(observations, candidates, ...)
expected_improvement(mean, variance, incumbent)
BOGenerator.ask / tell
EvolutionGenerator.ask / tell
```

生成器 module に CLI は設けない。

### 系列制御

B-5 `run_series`（`:722–841`）の順序・retry・終了分類を踏襲する。

1. fresh 系列開始 stock。
2. fresh 初期点 5 → 10。A/B の外、費用には含める。
3. 全 arm に A 上限を掛け、1 ask につき A を先に増やす。
4. proposal bytes を固定して単回評価。pipeline 投入が確認された論理 slot だけ B を増やす。
5. 候補起因の Tier0 不通過は A のみ。投入後失敗は B を返さない。
6. retry は追加 2 回、同じ入力で fresh attempt。B は論理 slot ごとに一度。
7. 機械故障上限超過・未解決は endpoint の有無にかかわらず終了し、score 欠測。
8. 初期点と探索点から endpoint を固定し、fresh N session で再計測。

根拠は B-5 `:603–668,744–758,769–841`。成功値のキャッシュ、性能による早期停止、失敗系列の差替えは入れない。

### 生成器の数値仕様

random は B-5 の整数重み・rejection sampling、sweep は同じ 28 点格子から `[5,10]` を除く。hash preimage は次で固定する。

```text
t2849-harness-v1|random|W|R|A|counter
t2849-harness-v1|sweep|W|R|v
t2849-harness-v1|bo-fallback|W|R|A|counter
t2849-harness-v1|evolution|W|R|A|counter
t2849-harness-v1|evolution-fallback|W|R|A|counter
```

BO：

- x=ln(v)、y=ln(tps)、学習 y の平均を差し引いた GP。
- Matérn 5/2、観測雑音 `(ln 1.03)^2`、対角 jitter `1e-10`。
- 実装案として長さ尺度 `{0.25,0.5,1,2}`、信号分散 `{0.25,1,4}`。header に値を残し、較正済みとは称さない。
- 対数周辺尤度最大。同値は長さ尺度、信号分散の昇順。
- EI は潜在関数の予測分散を用い、1..1000 を全列挙。同値は小さい v。
- certified・品質正常だけを学習。候補起因の Tier0 / build / anomaly の v は除外。品質欠測は除外集合に入れない。
- 学習点 0 の fallback でも候補起因の失敗集合を尊重する。

進化：

- 初期の親は正常な初期点の最良。同値は v、slot 順。
- hash の一様値から δ∈[−ln4,ln4] を得る。`floor(exp(log(parent)+δ)+0.5)`、1..1000 に clip。
- 親と同値なら δ の向きへ 1、境界では内側へ。δ=0 は正方向に固定。
- 親置換は **strict `>`**。同値改善・失敗点による置換や再抽選をしない。
- 親なしは専用名前空間の log-uniform fallback。

格子・平均関数・jitter・丸めは設計本文に未指定の実装選択であり、T-2850 が確認できるよう header と insight に記録する。

### K0 の期待入力

B-5 `:452–485` を基に、以下だけ変更する。

- whiteboard は `slot_kind="search"` の投入済み event のみ。5 field・iteration=b の連続性を維持。
- current_perf / baseline は stock・初期点・探索から **最新** の certified・品質正常を選ぶ。
- 初期点の識別には `slot_key` も返す。両初期点が b=0 でも混同しない。
- K2 診断の必須条件は持たず、K0 入力に知識・診断の追加 key を出さない。

P2 の下では、初期点全件の `(v,fitness)` と投入前拒否一覧を LLM に渡したとは報告しない。

### endpoint 集約

`--cohort-root` 配下の同一 cohort の結果から workload 別の anomaly 値集合を作る。これは endpoint の資格判定にだけ使い、ask / tell・親 prompt へ渡さない。

- endpoint 固定前に既知の全系列 anomaly を除外する。
- 候補は初期点＋探索、順序は fitness 降順・v 昇順・実 slot 順。
- 固定後に判明した他系列 / score の anomaly は、日付付き集約結果の訂正にする。元 event を書き換えず、次点へ選び直さない。
- stock 不成立、機械欠測、品質欠測、候補不採用の fallback を設計 `:195–202` の順で区別する。
- 参照欠測を stock で補完しない。stock 比と参照比の可用性を別々に報告する。
- endpoint が初期点か、探索最良が初期点最良を超えたか、一意候補数・重複率も出す。

集約結果は派生 report 一つであり、新しい ledger / registry は作らない。

### 新規試験

- `orchestrator/tests/test_t2849_generators.py`
  - 重み・hash 抽選・26 点格子の固定入力。
  - GP posterior・尤度・EI の独立計算との値照合。
  - 一観測 `(v=1,tps=100)`、固定 kernel の解析解：残差 0、`s²(x)=σ²-k(x,0)²/(σ²+noise+jitter)`、EI=`s/√(2π)`。全域 ask と失敗点除外を検査。
  - 二観測は独立な 2×2 逆行列計算で posterior / EI を照合。production の Cholesky を期待値生成に使わない。
  - 進化の親10、δ=±ln4 → 子40 / 3、同値補正、境界、strict replacement。
  - 固定 preimage の候補列を literal fixture として保持。
- `orchestrator/tests/test_t2849_comparison_harness.py`
  - 5 arm、A/B/k、fresh slot、retry の一度だけ B 計上。
  - 初期点が endpoint、初期点失敗、全品質欠測、Tier0 枯渇。
  - K0 latest-baseline と whiteboard 継承。
  - exact reference flags と実 WAL 分類。
- `orchestrator/tests/test_t2849_comparison_aggregate.py`
  - 他 arm・他系列・score anomaly の波及、workload 間非波及。
  - 欠測優先順位、固定後の訂正、次点への差替え禁止。
  - PBS_JOBID の重複計上防止、初期点・retry・LLM 待ちの費用保持。

## 5. U-C：K0 巡 tool・job body

### 新規 file

**`tools/t2849_llm_round.py`**

公開関数・class：`render_context`, `RoundTool`, `main`。

CLI：

```text
context --workload W --out PATH
inputs|coder|proposal --ledger-root PATH --materials-root PATH --a A
reject --ledger-root PATH --materials-root PATH --a A --reason TEXT
critic --ledger-root PATH --materials-root PATH --evaluation B --job ID --window TEXT
```

`proposal` / `reject` に `--costs PATH` を設け、親が記録した役割費用・介入を既存 handshake の provenance へ渡す。critic の費用は実行後の materials に残し、集約で取り込む。未実行の critic 費用を先に埋めない。

`tools/b5_llm_round.py:227–365,368–415` の材料保存・publish 手順を踏襲するが、次は移植しない。

- `:209–217` の knowledge manifest。
- `:234–240,258–260` の K2 診断。
- `:35–121` の K2 用 context 全文。

K0 context は役割が指定する `src/coder-leakproof-context.md` を基に、較正済み動作点と検証回数を明示する。既知結果禁止の文を落とさない。

planner は既存の3入力、coder は既存の4入力を使う。coder 出力は通常 proposal schema に包み、`load_proposal_file(path)` を role / knowledge 引数なしで呼ぶ。親の役割実行・モデル・入出力は materials に残す。critic prompt は作成するが、P2 で見送った診断還流を別 field や自由文に隠して戻さない。

### job body の変更

`tools/pegasus/p3_s4_loop_pegasus.sh`：

| 行 | 変更 |
|---|---|
| `:54–91` の隣 | harness mode の環境入力を読む。B-5・proposal・fixture・pair とは排他的にする。 |
| `:93–149` の前後 | harness では K2 env を使わない。既存 K2 分岐の条件は維持。 |
| `:189–196` の隣 | harness ledger / cohort root を既存と同様に解決する。 |
| `:652` の直前 | prebuild 完了後に harness driver を一度起動し、その rc で終了する。 |

新規 env は接頭辞 **`IZANAGI_S4_T2849_`** の以下に固定する。

```text
MODE=series|block-controls
COHORT, COHORT_ROOT, LEDGER_ROOT, WORKLOAD, BLOCK, N_EVAL
ARM, SERIES, A_LIMIT, B_LIMIT, INITIAL_VALUES
```

最後の5項目は series 用、`INITIAL_VALUES="5 10"`。文字列を shell `eval` せず array にする。

harness 起動直前だけ：

```bash
export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"
```

`IZANAGI_TRACE_ARCHIVE_ROOT` は明示指定された値を継承する。保全先を scratch に自動設定しない。既存 `IZANAGI_RESERVATION_DEADLINE_EPOCH` を系列側でも利用する。

### 新規試験

- `orchestrator/tests/test_t2849_llm_round.py`
  - K0 の input key 集合、manifest / K2 診断なし。
  - 初期点由来の latest baseline、a と b が異なる巡。
  - planner / coder の実入力保存と handshake の完全 publish。
  - malformed / empty output が拒否され A を消費すること。
- `orchestrator/tests/test_t2849_job_contract.py`
  - stub shell による実 argv・環境・driver 一回・rc 伝播。
  - 全5 arm と block-controls。
  - harness branch の lock、非 harness 環境不変。
  - B-5 と既存3経路への fallthrough がないこと。

## 6. 素集合の所有 path と依存順

| 単位 | 所有 path |
|---|---|
| U-A | `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/pipeline.py`、`orchestrator/tests/test_t2849_loop_entry.py`、`orchestrator/tests/test_t2853_trace_preservation.py`、`orchestrator/tests/test_ccbench_spawn_sites.py` |
| U-B | `orchestrator/campaign/t2849_comparison_harness.py`、`orchestrator/campaign/t2849_generators.py`、`orchestrator/tests/test_t2849_generators.py`、`orchestrator/tests/test_t2849_comparison_harness.py`、`orchestrator/tests/test_t2849_comparison_aggregate.py`、`orchestrator/tests/test_official_perf_closure.py` |
| U-C | `tools/t2849_llm_round.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_t2849_llm_round.py`、`orchestrator/tests/test_t2849_job_contract.py`、`orchestrator/tests/test_p3_s4_loop_job_contract.py` |

この interface の確定後、3 単位は並行実装できる。U-B は評価 runner を stub、U-C は固定 handshake を使って進める。統合は **U-A の入口 → U-B の系列 → U-C の実 argv / handshake → 全体回帰** の順。

insight・worklog fragment は段7の親所有とし、author 3 単位の共通編集 file を作らない。

## 7. inventory / registry 試験の扱い

新 module があるだけで登録数を増やさず、実際に変わる面を更新する。

| 実 file:line | 予定・担当 |
|---|---|
| `orchestrator/tests/test_ccbench_spawn_sites.py:92–104` | **更新必須、U-A。** `pipeline._preserve_trace_directory` の zstd subprocess 一箇所を non-CCBench に登録。U-B は B-5 `default_runner` を呼ぶため launch site を追加しない。 |
| `orchestrator/tests/test_official_perf_closure.py:44–101,503–525,912–915` | **U-B 所有。** 新 module の perf predicate discovery 結果を照合し、該当する path のみ追加。profiler を起動しない単なる `current_perf` 値の扱いと区別する。 |
| `orchestrator/tests/test_campaign.py:4836,5408–5436` | **更新不要を想定、U-A が回帰確認。** `run_campaign` は22、evaluate は5のまま。参照用 callsite を複製しない。 |
| `orchestrator/tests/test_p3_exploration_namespace.py:133–159,515–524` | **更新不要を想定、U-B が確認。** 新 driver は ledger を作るが exploration campaign root は作らず、子の既存 CLI が作る。 |
| `orchestrator/tests/test_p3_b4_wiring_probe.py:324–329,702–714` | **更新不要を想定、U-A が確認。** 新兄弟 module を既存 loop / pipeline から import しないため、静的 import 閉包49を保つ。数値だけ追随させない。 |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py:546–559,1280–1331,1985–2227` | **U-C。** shell stub が新 module 呼出しを記録できるよう必要箇所を拡張。既存 driver 2箇所・B-5 1箇所と既存 argv の期待値は維持する。 |
| 同 `:1825–1851` の admission registry 照合 | **更新不要、U-C が確認。** job body path は同一。launcher・新 submission policy は作らない。 |

更新不要を想定した test が赤になった場合は、まず予定外の import / caller / predicate が増えていないか調べる。固定 inventory を一括緩和しない。

## 8. kill を期待する変異

新規 file の行番号は未成立なので関数・変更点を指定する。

| 所有 | 変異位置・内容 | 赤になるべき試験 |
|---|---|---|
| U-A | `main` の harness 接頭辞を削除 | `test_t2849_loop_entry.py::test_harness_machine_slot` |
| U-A | `_run_stock_control_resolved` が参照にも `_BASE` を使う | 同 `::test_read_heavy_reference_exact_flags` |
| U-A | 保全前に `rmtree`、または失敗後も削除 | `test_t2853_trace_preservation.py::test_archive_before_cleanup` / `test_failure_retains_original` |
| U-A | 保全処理で anomaly の結果を成功へ変更 | 同 `::test_anomaly_verdict_and_no_bench_unchanged` |
| U-B | 初期点で B を加算、retry ごとに B を加算 | `test_t2849_comparison_harness.py::test_initial_and_retry_budget` |
| U-B | Tier0 不通過を BO の失敗集合から外す | `test_t2849_generators.py::test_bo_excludes_candidate_failures` |
| U-B | Matérn の距離を v にする、EI に観測雑音を加える | 同 `::test_gp_two_point_independent_values` / `test_ei_latent_variance` |
| U-B | 進化の `>` を `>=` にする | 同 `::test_equal_fitness_keeps_parent` |
| U-B | initial を endpoint 候補から外す | `test_t2849_comparison_harness.py::test_initial_can_be_endpoint` |
| U-B | anomaly を自系列だけに限定、欠測を fallback で埋める | `test_t2849_comparison_aggregate.py::test_cross_series_disqualification` / `test_missingness_precedence` |
| U-B | current_perf を最新から最良へ変更 | `test_t2849_comparison_harness.py::test_k0_uses_latest_normal_initial` |
| U-C | K0 argv に machine 印 / K2 role を付加 | `test_t2849_llm_round.py` と job argv 試験 |
| U-C | harness branch の exit / lock を削除 | `test_t2849_job_contract.py::test_single_driver_and_local_lock` |
| U-C | b の代わりに a を whiteboard iteration に使う | `test_t2849_llm_round.py::test_rejection_does_not_advance_whiteboard` |

実装後は親が関連試験・既存 inventory 群・通常の受入を実行する。本段では未実行であり、緑とは報告しない。

## 9. 既存動作と規律 1・2 の保持

- **B-5 argv**：生成元 `b5_generator_contrast.py:507–529` を編集しない。slot 接頭辞の追加受理は既存接頭辞の分岐を変えない。
- **通常の候補・fixture・pair**：job body `:151–161,673–687` を維持し、harness env がある場合だけ新分岐へ入る。
- **既存 stock**：`p3_s4_loop.py:2314` の式を None 分岐として残す。省略時の search_config / kwargs へ参照用値を追加しない。
- **verify / anomaly reject**：`pipeline.py:655–670,2137–2146,2185–2188` の判定と即時終了を変更しない。
- **trace と perf の分離**：`pipeline.py:2016–2017` の `trace=True` / `trace=False` build、compile flag・patch・verifier を変更しない。
- **保全未指定**：`pipeline.py:2177–2178` の cleanup と既存出力を保つ。圧縮・inventory・追加ログを行わない。
- **保全の射程**：今回の口は指定されたローカル反復。harness は `BACKOFF_SWEEP`（`p3_s4_loop.py:3742–3747`）なので、`BACKOFF_REPRO` に限定された fanout（`pipeline.py:2422–2433`）へ入らない。remote worker の保全まで実装済みとは称しない。

## 10. 行数見積り

追加・変更行の概算。削除行、段7の文書は別。

| 単位 | production | tests / inventory | 計 |
|---|---:|---:|---:|
| U-A | 160〜230 | 280〜380 | 440〜610 |
| U-B | 950〜1,200 | 550〜750 | 1,500〜1,950 |
| U-C | 300〜420 | 250〜350 | 550〜770 |
| **合計** | **1,410〜1,850** | **1,080〜1,480** | **2,490〜3,330** |

最大部分は B-5 固定結合を外した系列制御と、欠測・retry・集約の試験。汎用 runner、追加 protocol、registered launcher は含まない。

## 総括

- 既存評価経路を保ち、兄弟 module に5 arm・初期点・予算・集約を置く。参照は exact 4 flags、保全は env opt-in とし、B-5 と proof chain を編集しない。
- **P1：賛成。** 束 `output/insights/2026-09-22/t2797-effect-bundle/bundle/b5-effective-bundle.draft.json:18` は承認対象を land commit と status / effective section だけを変える発効 commit に限定している。`:198–199,220,222` の4 SHA は現行と一致した。旧 land を親とする発効 commit なら本 wave の変更を含めずに済む。ただし現 main 上で発効させてよいという意味ではない。束を変えず、この分岐条件を段7に残す。
- **P2：賛成。ただし D2220 の部分実装と明記する。** `.claude/agents/planner-v4.md:62–73` と `p3_s4_loop.py:1317–1331` は診断を K2 に限定し、coder の入力は `.claude/agents/coder-v4-autonomous.md:31–49` の4 key。役割を変更せず K0 入口と latest-baseline を実装できるが、critic 診断・初期点一覧・投入前拒否一覧の還流は満たさない。また K0 CLI に `--coder-role` は付けない（`:3484–3486,2976–2984`）。
- **P3：賛成。** job body `tools/pegasus/p3_s4_loop_pegasus.sh:652–670` が prebuild 後の driver 起動と node-local lock を持つ。同位置の排他的 harness 分岐なら既存 `:673–687` を維持できる。driver 側に別の lock 配置規則を増やす必要はない。