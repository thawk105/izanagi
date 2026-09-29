# [T-2867] 段 4 裁定と plan v2 (親、2026-09-29 15:0x JST)

入力: 段 2 plan `codex/s2-plan/out.md`、段 3 相談 A (正しさ境界、NO-GO) `codex/s3-consult-a/out.md`、相談 B (過剰・削除) `codex/s3-consult-b/out.md`。
裁定 inbox: local main は wave 開始時の `035fc11fa` から不動、新しいユーザー発話なし → 取り込む新裁定なし。DW-O09: 変更予定 file の sha256 pin 0 件 (path の出現は過去の変異台帳と consumer test だけ)。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | 処置 (plan v2 の節) |
|---|---|---|---|
| A1 系列履歴の保存先 | real | 採用 | 系列 dir = 系列 cfg の campaign dir が `policy_history.jsonl` の唯一の置き場。計測 campaign は WAL 専用。対照の経路は `check_stop`・`loop_state.json` を読まず書かない (§2.2) |
| A2 auditor 省略の照合 | real | 部分採用 | 機械 proposal は arm ∈ {random-ir, evo-ir} の系列でだけ受理し、provenance の生成器名と arm の対応を閉じた表で照合する。初期点は proposal file を経由させず、driver が `silo_policy_ir.enumerate_recon()` の `0000`・`0001` から自分で組む (外から IR を入れる口が無い)。**生成器の再計算による照合は足さない** (launcher も自前 code、DW-G05 の仮想リスク) (§2.3) |
| A3 開始前照合の主体 | real | 採用 | 単位 file に台帳の絶対 path を持たせ、job (driver) が header の submit checkout・HEAD と自分の HEAD、`next_unit(ledger)` と単位の (kind, index, proposal sha256)、未終端の slot 開始の有無を、最初の slot 開始 event より前に照合する (§2.4) |
| A4 A/B と異常終了の境界 | real | 採用 | 機会の開始と A の確定を別 event にする。429 と役割の異常終了は A を確定しない。B は評価 slot の最初の attempt 開始で 1 回だけ確定 (§2.5) |
| A5 anomaly 波及と訂正 | real | 採用 | report が全系列・全 arm の slot 結果を identity (variant) で突き合わせ、草稿 §6 の優先を判定前に当てる。後発の訂正は report の再生成で出る (§2.8) |
| A6 job body の配線 | real | 採用 | `contrast` mode の env 契約を固定 (§2.6)。launcher が作る qsub argv を job body test と同じ形で検査する |
| A7 critic 材料の主体 | real | 採用 (B2 と統合) | 評価 slot の critic digest は job が台帳の slot 結果 event に文字列で残す。critic の材料は台帳の event から導く。第 2 の状態 file は作らない (§2.7) |
| A8 生成器の契約 | real | 採用 | §2.9 に閉じた仕様を書く |
| A9・B5 生成不成立の数え方と表示名 | real | 採用 | 探索点を持つ系列の数を判定入力に渡し、出力の表示名を置き換え、certified endpoint 数も別に出す (§2.8) |
| A10・B8 見積りの出所 | real | 採用 | 換算と walltime 上限を分けて示す (§4) |
| B1 単位 file の重複 | real | 採用 | 単位 file は最小 (§2.4) |
| B3 driver action の数 | real | 採用 | 新 action は `--contrast-run-unit` 1 つ。login 側は既存 `--emit-coder-input`・`--preview-diff`・`--record-reject` に `--contrast-ledger ROOT` を足して系列 cfg に向ける (§2.2) |
| B4 round tool と親 | real | 採用 | round tool は 3 subcommand。親は新しい小 file (B-5 `Parent` は resume 前提なので使わない、`classify_exit` だけ import) (§2.7) |
| B6 再利用の境界 | real | 採用 | §3 の各単位に書く |
| B7 テスト量 | real | 採用 | 新しいテストの合計所要は 60 秒以内、長い job を作らない。各境界に 1〜2 本 |
| B9 fixed10 と 1 slot 1 identity は維持 | real | 採用 | §2.3 |

## 2. plan v2 (固定する interface)

### 2.1 座標と名前

- arm の文字列: `llm-cpp`・`llm-ir`・`random-ir`・`evo-ir`、参照は `reference`。form は arm から決まる (`llm-cpp` → cpp、他の 3 arm → ir、`reference` → cpp)。
- 試験・生死確認の版文字列 (cohort 名を兼ねる): `silo-policy-contrast-test-2026-09-29`。登録版 `silo-policy-generator-contrast-v1` は発効後の本走だけが使う。v1 の preimage で生成器を呼ぶテスト・ログを作らない。

### 2.2 driver (U1、`orchestrator/campaign/p3_s4_loop_policy.py`)

- `default_cfg(..., contrast=None)`。`contrast=(cohort, arm, series)` のときだけ search_config に `contrast_cohort`・`contrast_arm`・`contrast_series` と `verify_performance_concurrent: True` (D2251、write-heavy。loop.py:902 に委ねる) を足す。`contrast=None` の bytes・campaign ID は不変 (回帰 test)。
- 計測 cfg = 系列 cfg + `contrast_slot: "<slot>-<index>-a<attempt>"` の 1 key (B の畳み込み)。slot ∈ `stock`・`seed`・`eval`・`score`・`ref-stock`・`ref-fixed10`。attempt は 0 始まり、機械故障 retry で 1・2。
- 系列 dir (系列 cfg の campaign layout) に `policy_history.jsonl` を書く。初期点 2 行 (iteration −2 = 5 µs、−1 = 10 µs) は job 1 の完了時、評価の行 (iteration = 原提案番号 a) は評価 job の完了時、却下の行 (a) は login の record-reject で。行の形は既存 `_append_history` と同じ key。coder 射影 (`make_policy_coder_input`) は変えない。
- `--contrast-ledger ROOT` (台帳 dir の絶対 path) を `--emit-coder-input`・`--preview-diff`・`--record-reject` に付けたとき、cfg は台帳 header の (cohort, arm, series, form) から作る (`--form` は header と一致必須)。record-reject は WAL の拒否記録と履歴行だけを書き、`loop_state.json`・`check_stop` を使わない。A の計上は台帳側 (U4/U5) が行う。
- 機械 proposal の形: `{"generator": {"name", "version", "series", "a", "counter", "preimage"}, "ir": <tagged IR>}` (top key はこの 2 つだけ)。`name` と arm の対応は `random-ir` ↔ {`random-ir`}、`evo-ir` ↔ {`evo-ir`, `evo-fallback-ir`}。LLM arm の系列では拒否。LLM arm の proposal は既存 `{coder, auditor}` のまま (`load_proposal_file`)。
- `policy_gate`: 機械 proposal と初期点だけ auditor 段を省く。書込後の digest 再照合は全由来で行う。`auditor is None` での書込は「呼び側が機械由来と初期点を明示したとき」だけ許し、既定は今どおり拒否。
- `measure_slot(...)` (関数): 1 slot を自分の計測 cfg の campaign で 1 評価し、結果を返す: `{logical_slot, attempt, campaign_id, campaign_root, variant, source_digest, outcome, failure_class, quality, fitness_tps, abort_rate_pct, anomalies, wal_sha256, timing, critic_digest}`。分類は B-5 の `classify_session` と `MACHINE_FAILURE_ABORT_REASONS`・`wal_timing` を再利用し、outcome ∈ `certified`・`anomaly`・`candidate-failure`・`quality-missing`・`machine-failure`・`unclassified-missing`、failure_class ∈ `candidate`・`machine-failure`・`quality`・`unclassified`・null。`critic_digest` は評価 slot だけ既存 `L.make_critic_digest` で作る。
- stock slot は既存 `run_stock_control` の形 (軸 OFF の 4 flag)。ref-fixed10 は D2240 と同じ形 (stock 木に `patches/silo-backoff-fixed.patch`、genome `BACK_OFF=1, BACKOFF_FIXED=10` + 4 flag から軸 flag を除いた形、骨格 patch なし、hole 本文を書き換えない)。define の効きの確認は既存の仕組み (p3_s4_loop の `_require_condition_gate` か `silo_policy_recon` の define 検査) を呼び、新しい検査を書かない。どちらも run_campaign 経路で通らないなら、実装子は理由を報告して止める。
- 新 action `--contrast-run-unit UNIT.json` (計算ノード、`--allow-coder-derived-build` 必須、`--campaign-env pegasus`): 台帳との照合 (§2.4) → 単位の slot を順に `measure_slot` → 台帳へ event を追記 → stdout に `{kind, index, slots: [...]}`。rc: 全 slot の結果が記録できた 0、照合の不一致 2、その他 1。1 job の全 slot は 1 つの authorization session を共有する (D2205・D2281 と同じ)。

### 2.3 初期点と機械候補

- 初期点は job 1 で driver が `enumerate_recon()` の `0000` (5 µs) → `0001` (10 µs) を組み、系列の form で評価する (cpp 系列は描画後の本文、ir 系列は IR)。全 arm 共通。auditor なし。
- 機械候補 (random・evo) の生成・preview・拒否記録は login の launcher が行い、通った候補だけ評価 job を起こす (草稿 §5.6「却下は job を起こさない」)。

### 2.4 台帳と単位 file (U4、`orchestrator/campaign/silo_policy_contrast.py`)

- 台帳 = 系列 1 本に 1 dir。`header.json` + `events/NNNNNN-<kind>.json` (連番・create-only、t2849 `SeriesLedger` の書き方を移す、B-5 の EVENT_KINDS は変えない)。schema `silo-policy-contrast-ledger/v1`。
- header: `schema, version, cohort, arm, series, form, submit_checkout, checkout_head, pin, budgets {B: 10, A: 30, k: 2, n_eval: 5, machine_retries: 2, role_retries: 2}`。参照の台帳は arm `reference`、series = batch 番号 1〜3。
- event の種類: `series-start`・`slot-start`・`slot-result`・`opportunity-start`・`opportunity-end`・`critic-result`・`endpoint-fixed`・`series-end`。
  - `opportunity-start {a}` は A を消費しない。`opportunity-end {a, outcome, proposal_path?, proposal_sha256?, role_attempts?}` で outcome ∈ `proposed` (A+1、評価待ち)・`rejected` (A+1)・`empty` (A+1)・`outage` (A 不変、同じ a で再開)・`role-failure` (A 不変、3 回目で series-end `unclassified-missing`)。
  - `slot-start {logical_slot, attempt, unit_kind, unit_index}`、`slot-result {measure_slot の戻り値 + ir?/implementation?}`。B は評価 slot の attempt 0 の `slot-start` で確定 (retry は B を増やさない)。
  - `series-end {reason}`、reason ∈ `b-complete`・`a-exhausted`・`machine-retry-exhausted`・`stock-unestablished`・`model-mismatch`・`unclassified-missing`・`dead-job`。
- 単位 file (launcher が create-only): `{"schema": "silo-policy-contrast-unit/v1", "ledger_root": <abs>, "kind": "job1"|"eval"|"score"|"reference", "index": <int>, "attempt": <int>, "proposal_path": <abs>|null, "proposal_sha256": <hex>|null}`。
- `next_unit(ledger) -> dict | None` と `series_state(ledger)` (A・B の使用数、未終端 slot、endpoint 候補、進化の親候補) を公開関数にする。未終端の `slot-start` (結果なし) があれば `next_unit` は `dead-job` を返し、launcher は自動再投入せず止めて報告する。
- endpoint: 資格ある certified・quality normal の初期点と探索点のうち探索時 fitness 最大、同値は slot の早い方。`endpoint-fixed` を score 前に書く。
- launcher (`tools/pegasus/silo_policy_contrast_launch.py`): `init` (台帳作成)、`generate` (機械 arm の次の原提案: 生成 → driver preview → 拒否なら record-reject と `opportunity-end rejected`)、`submit` (next_unit → 単位 file → qsub、系列 C の `submit-policy.sh` の env 形、`-h`/`--after` 可)、`status`。LLM arm の原提案は U5 の親が進める。qsub は既定で dry-run 表示、`--submit` で実投入。

### 2.5 A・B・retry

草稿 §3・§5.5 のとおり。B = 評価 slot の attempt 0 開始。候補起因の失敗 (anomaly・build 失敗・時間切れ) も B を返さない。機械故障は同じ論理 slot を attempt+1 で新しい job に (台帳の `next_unit` が retry 単位を返す)、上限を超えたら `series-end machine-retry-exhausted`。品質欠測は retry しない (score 欠測の分類で report が扱う)。

### 2.6 job body (U2、`tools/pegasus/p3_s4_loop_pegasus.sh`)

`IZANAGI_S4_POLICY_MODE=contrast` を足す。必須 env = `IZANAGI_S4_POLICY_FORM` (既存)、`IZANAGI_S4_POLICY_UNIT_PATH` (絶対 path)、`IZANAGI_TRACE_ARCHIVE_ROOT` (既存の必須)。`IZANAGI_S4_POLICY_PROPOSAL_PATH` は contrast では禁止 (候補は単位 file が指す)。driver argv = `--form <FORM> --campaign-env pegasus --fetchcontent-prebuild-receipt <既存> --allow-coder-derived-build --contrast-run-unit <UNIT>`。既存 stock|pair|replay の argv と排他は不変。

### 2.7 LLM の原提案 1 機会 (U5)

- round tool `tools/silo_policy_contrast_round.py`: `prepare --ledger <root> --a <a> --out <dir>` (台帳に新しい slot 結果があれば critic prompt を作る。driver の `--emit-coder-input --contrast-ledger` の stdout を無加工で保存し coder prompt を作る。`opportunity-start` を書く)、`check --ledger --a --coder <json> --out` (driver preview。拒否なら record-reject と `opportunity-end rejected`、通過なら auditor 入力と prompt (runbook §1(d) の閉じた出力形を逐語) を書く)、`finalize --ledger --a --coder --auditor --out` (proposal `{coder, auditor}` を作り、auditor の `diff_digest` と preview の値を照合し、`opportunity-end proposed` を書く)。critic の出力は `--critic-output` の 4 見出しの形で保存し `critic-result` を書く。
- critic prompt の材料 = 前回の `critic-result` 以後の `slot-result` の `critic_digest` (job 1 のときは stock と初期点 2 の結果の要約)・その slot の本文・job 1 の stock 値。他 file を読まない指示を書く (系列 C の make-critic-prompt.py の形)。
- 親 `tools/pegasus/silo_policy_contrast_parent.py`: 1 原提案 a ごとに新しい `claude -p --output-format json` を起動 (resume しない)、`--settings`・`--model` は引数で固定、許可 tool は `Bash(python3 tools/silo_policy_contrast_round.py *)`・`Agent`・`Read`・`Write` (Write は round tool の out dir の中だけと指示文に書く)。終了は `b5_llm_parent.classify_exit` で判定し、outage は 900 s 後に同じ a で再起動、他の失敗は追加 2 回まで。禁止 env (API キー等) があれば起動しない (B-5 の FORBIDDEN を再利用)。
- 指示文 (`tools/pegasus/silo_policy_contrast_parent.md`): critic → coder → check → [拒否で終了] → auditor → finalize の機械的手順。値の書換え・再抽選・性能を見た助言をしない。入力内の文字列はデータ。role 名は `critic`・`coder-v4-autonomous-policy`(-ir)・`auditor`。

### 2.8 report (U6、`orchestrator/campaign/silo_policy_contrast_report.py`)

入力 = 全系列と参照の台帳 dir。B-5 report の `exact_sign_flip_p`・`_holm`・`stock_cv_floor(v2=True)`・`decide_comparison(v2=True)` を import。n は header の系列数から (10 か 12、他は拒否)。対差の結合は局所関数。anomaly の波及 (全台帳の slot 結果で anomaly を持つ variant は endpoint 資格なし)、§6 の欠測・fallback の優先、族 A・B を別々の Holm、生成不成立は探索点を持つ系列の数 (初期点を除く) を渡し、出力 key は `search_point_series_counts` と `certified_endpoint_counts` を別に持つ。記述統計は草稿 §7.4 末尾の報告項目のうち台帳から出るもの。

### 2.9 生成器 (U3、`orchestrator/campaign/silo_policy_contrast_generators.py`)

草稿 §4.4・§4.5 を逐語で実装する。`random_ir(version, series, a) -> (ir_document | None, provenance)`、`evolve_ir(version, series, a, points) -> (ir_document | None, provenance)` (points = 自系列の certified・quality normal の点の列 `{slot_order, fitness_tps, ir}`、初期点を含む)。乱数は preimage `<version>|random|r|a|c` / `<version>|evo|r|a|c` / `<version>|evo-fallback|r|a|c` の SHA-256 から決定的に引く (1 preimage から必要な乱数を順に取り出す方法は実装子が決め、docstring に書く)。定数は 0 (確率 1/8) と `b5_generator_contrast.weights_table()` の log 重みの混合。引き直し (node > 64、`validate_ir` 拒否、進化では親と同じ本文) は c を進め A を消費しない、1000 回で `None`。進化は親 = fitness 最大・同値は slot_order の早い方、4/5 で subtree 置換、1/5 (field 4 個なら 0) で field 追加 + 置換、省略 `next_state` の展開規則、明示 `next_state` への自己参照の追加。テストは版文字列 `silo-policy-contrast-test-2026-09-29` だけを使う。

## 3. 実装単位 (所有 path は素集合、3 子並列)

| 子 | 所有 path | 依存 |
|---|---|---|
| X (driver + job body) | `orchestrator/campaign/p3_s4_loop_policy.py`、`orchestrator/tests/test_p3_s4_loop_policy.py`、`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`、(必要なら) `orchestrator/tests/test_campaign.py` の caller inventory の行 | Y の `silo_policy_contrast` の API (§2.4 の関数名・event 名) を import する。Y 未着地の間は §2.4 の signature を前提に書き、結合は親が統合後に走らせる |
| Y (生成器 + 系列制御 + launcher) | 新 `orchestrator/campaign/silo_policy_contrast_generators.py`・`orchestrator/campaign/silo_policy_contrast.py`・`tools/pegasus/silo_policy_contrast_launch.py` と各 test、`tools/pegasus/admission_registry.json` の登録行 | driver は subprocess (CLI) でだけ呼ぶ |
| Z (round tool + 親 + report) | 新 `tools/silo_policy_contrast_round.py`・`tools/pegasus/silo_policy_contrast_parent.py`・`tools/pegasus/silo_policy_contrast_parent.md`・`orchestrator/campaign/silo_policy_contrast_report.py` と各 test | Y の台帳 API、driver CLI |

docs (`tools/pegasus/README.md`・runbook・`docs/README.md` の地図・草稿) は親が書く。

## 4. 計算の見積り (ユーザー確認用)

- 生死確認 6 job: 換算 job 1 ≈ 1,310 s × 3 + 評価 ≈ 520 s × 3 = 5,490 s ≈ 1.53 node 時間 (段階 F の stock 300 s・R2 491 s、系列 C の bootstrap 308 s からの換算。同時検査の効果は含めない)。walltime 上限: job 1 45 分・評価 25 分 → 3.5 node 時間。
- 検査: 受入 ≈ 0.25 node 時間/回 (実測) × 2〜3 回 + 変異 dispatch ≈ 0.5 → ≈ 1.3 (上限 1.9)。
- 合計: 見込み ≈ 2.8 node 時間、上限 ≈ 5.4 node 時間。2 node 時間を越えるので投入前にユーザー確認。

## 5. 変異の事前登録 (DW-M01、位置と期待 node は実装後に確定して台帳へ)

| ID | 単位 | 変異 | kill 期待 (機構の実体) |
|---|---|---|---|
| M1 | X | LLM arm でも機械 proposal を受理 | LLM arm の系列で機械 proposal を拒否する test |
| M2 | X | 計測 cfg の `contrast_slot` から attempt を落とす | retry の campaign ID が別になる test |
| M3 | X | `contrast=None` でも search_config に key を足す | 既定 cfg の campaign ID 不変 test |
| M4 | X | 対照経路で `auditor is None` の書込を常に拒否 (機械候補の口を閉じる) | 機械候補が書込・評価まで進む test |
| M5 | X | 単位の照合で proposal sha256 を比べない | 不一致で rc=2・slot-start 無しの test |
| M6 | X | job body の contrast mode で unit path 必須を外す | env 排他 test |
| M7 | Y | 定数 0 の確率 1/8 → 1/7 | 固定入力の分布 test |
| M8 | Y | 進化の親の同値を遅い slot で破る | 親選択 test |
| M9 | Y | B を評価 slot の開始で数えない | A/B 計上 test |
| M10 | Y | 未終端の slot-start を無視 | dead-job test |
| M11 | Y | outage でも A を消費 | 429 保留 test |
| M12 | Z | 生成不成立の数に初期点を含める | 探索点 0 の系列の test |
| M13 | Z | 族 A と B を 1 つの Holm にする | 族別補正 test |
| M14 | Z | 親が前の session を resume する | 新 session の argv test |
