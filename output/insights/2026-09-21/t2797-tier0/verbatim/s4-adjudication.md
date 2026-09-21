# [T-2797] 段 4 裁定 — プラン v2 と変異の事前登録 (2026-09-21 15:05 JST、base d99c556df、local main は 47368e7d5 へ前進 = docs のみ)

入力: 段 2 plan `codex/s2-plan.md` (398 行)、段 3 相談 A `codex/s3-consult-A.md` (must-fix 3 / should 4)、B `codex/s3-consult-B.md` (must-fix 3 / should 4 / nit 1)。
裁定 inbox 再走査 (15:00): wave 開始後の新着なし (最新 full29 13:34 は T-2797 に言及なし)。親の実測: smoke 所要 (下記 §2)。

## 1. 所見の裁定

| # | 所見 | 判定 | 裁定 |
|---|---|---|---|
| A1 / B1 | 投入後 (submission あり) の経路が Tier0 証拠を読まない。通過証拠が台帳へ届かない | real・採用 | driver は B-5 候補 slot で submission の有無に関わらず `tier0.json` を読む。submission ありで passed 証拠が無い・壊れている・別 slot なら `unclassified-missing` (B は保持、系列停止)。B は submission、Tier0 判定はその物理 attempt の結果として分ける (前 attempt 投入済み + 今回 Tier0 拒否 は矛盾でない) |
| A2 / B3 | コンパイル失敗の帰属境界が未確定 | real・採用 (境界を固定) | Tier0 の build は pipeline `_build_one` と同じ例外境界を使う: `(RuntimeError, subprocess.SubprocessError)` → `rejected` / reason `build-error` / 候補起因 (A のみ、retry なし、次の A へ)。これは投入後の同じ失敗を D2198 が候補起因 (`build-failed`、B 消費) に分類している既存規約を投入前へ移すだけで、帰属規約を変えない。上記以外の例外 (source evidence・admission の導出、I/O 等) は捕まえず子を落とす → 既存の `unclassified-missing` (系列停止)。A2 の「非ゼロ終了は候補起因の証拠でない」は一般には正しいが、投入後 build 失敗の帰属は既存の登録済み規約で本 wave の scope 外 (insight に限界として記録、裁定パッケージにしない — 研究前進の実測欠陥を示せない。試走 53 session で build 失敗 0) |
| A3 | cohort 内で Tier0 契約の一致を report が検査しない | real・採用 (最小) | report の既存の共通構成比較の key に `tier0_status` / `tier0_contract` を足すだけ。新しい gate・台帳は作らない。試走台帳 (not-implemented) の読取りは不変 |
| A4 | 実効 handshake 期限 = min(2700, 残 walltime − 1800) | real・採用 (設計記録のみ) | P6 の設計記録に書く。期限表示・launcher は変えない |
| A5 | smoke の数値が event → handshake `slot-*.json` → 親の射影へ流れうる | real・採用 | smoke の数値 (wall・commit・abort・throughput 判定) は子の `tier0.json` sidecar にだけ書く。台帳 event には `tier0 = {status, reason, sidecar_sha256}` だけを載せ数値を載せない。fitness・current_perf・leading indicators・endpoint に入らないことを test で固定 |
| A6 / B5 | 変異と検査の対応不成立 (smoke helper 単体 test は呼出し側の binary 取り違えを通らない)。Tier0 通過後 anomaly の負例がない | real・採用 | 呼出し側 (実挿入点) を通る test で「perf build (trace=False) の binary が gateway に届く」を固定。「Tier0 passed → verify anomaly → B=1・endpoint 不採用」の負例を足す |
| A7 | BuildResult の再構成 argv を実行 argv と混同 | real・採用 | build の記録は `trace` / `binary` / `bin_sha256` / `cached` だけ。argv は記録しない |
| B2 | `tier0-interrupted` が停止集合に無い | real・採用 (要素ごと削除) | 開始印 (P5) と `tier0-interrupted` を削る (下の B 表)。Tier0 中の中断 = slot-start あり・submission なし・terminal なし → 既存の `unclassified-missing` (A のみ、B なし、系列停止)。§3.3 の「投入前の時間切れは A のみ」はこの既存計上で満たされる (A = attempt-start、B = submission) |
| B 表: 開始印 P5 | 削除 | 採用 | A / B の計上は既存の attempt-start と submission で閉じる。失うのは中断位置の細分化だけ |
| B 表: trace build の前倒し P2 | 削除 | 採用 | Tier0 のコンパイルは perf (trace-disabled) binary 1 本だけ (smoke が走らせる binary)。trace build は従来どおり投入後 (§3.3 が「correctness の build」を投入後と明記)。perf build は pipeline 側で cache hit |
| B 表: score slot の Tier0 | 削除提案 | 不採用 (明示の契約として維持) | score も同じ候補を certification pipeline へ投入する (§3.1「Tier0 を通過した候補を投入」)。子の経路を 1 本に保ち flag を足さない。score での不通過は探索 A / B を動かさず既存の非 certified 分岐で系列停止 (fallback なし)。header 契約に `applies_to = ["search", "score"]` と明記 |
| B 表: 新 sidecar / 新 event kind / header / 新 test file | — | sidecar は `tier0.json` 1 枚 (通過・不通過とも)。`proposal-rejected.json` は使わない。新 event kind なし (既存 event の追加 field)。header 契約は残す (定義は子の 1 箇所)。新 test file は子側の検査に 1 本 |
| B4 | U1 先行 land 不要、統合 1 回で land | real・採用 (さらに単位を統合) | driver の header が子の契約定数を読むため、driver 単独の worktree では既存 driver test が全滅する。**実装単位は 1 つ (A1) に統合し、T-2632 land 後の local main 上で 1 回 author する** (中間状態の互換分岐を作らない) |
| B6 / P6 | p=4 を §7.1 からの必然とする根拠は誤り | real・採用 | brief の「block あたり 12 組 × 6 通り」は誤引用 (6 順序は workload ごとの 12 組全体に各 2 回)。p=4 は運用上の選択、1 親 1 系列は context 分離の契約として記録 |
| B7 / P7 | W の式は今回、倍率・発効は別段 | real・採用 | 下 §4 |
| B8 | test アンカー誤り (`:328` → `:309`) | real・採用 | author prompt に test 関数名 `test_series_scores_fresh_sessions_after_endpoint_fix` と対象式で渡す |
| plan §1 | 二重 build | 採用 | perf build API は 2 回 (Tier0 / pipeline) 呼ぶが実コンパイルは 1 回、後続は検証付き cache hit。stale claim・破損 entry を自動回収しない |

## 2. 親の実測 (DW-O13): 固定スモークの所要

- 2026-09-21 14:48〜14:52 JST、gen_S `15197.nqsv` / bnode039 (loadavg 0.70、`pgrep ycsb_` 空)、probe = job dir `probe/smoke_timing_probe.py` (repo 外)、結果 `probe/smoke-timing-result.json`。
- binary = 試走 β の build cache の trace-disabled `ycsb_silo.exe` 6 本 (BACKOFF_FIXED = −1 (stock) / 1 / 2 / 3 / 8 / 698)、各 5 回、plan の固定 argv、`runner.run_once(use_perf=False, strict_returncode=True, numactl=[])`。
- **30 / 30 走で rc=0、既存パーサの commit 数 > 0、throughput 有限正。所要 (外側 wall) min 1.0035 / 中央値 1.0046 / max 1.0463 s。** 各 binary の初回だけ +0.02〜0.04 s。
- 観測 regime の差: build から数時間後の binary (Tier0 は build 直後)、値 1000 µs は cache に無く未測 (最大 698)、node-local lock、write-heavy 試走の cache。
- **smoke timeout = 32 s (= ceil(1.0463 × 30))。** 偽の timeout は候補起因として A を消費するので正例側に広い余裕を取る。費用は候補あたり最悪 32 s。bench lock の待ちは timeout に含めない。

## 3. プラン v2 (実装単位 A1 = 1 つ、T-2632 land 後の local main で author)

所有 path: `orchestrator/campaign/p3_s4_loop.py`、`orchestrator/campaign/b5_generator_contrast.py`、`orchestrator/campaign/b5_generator_contrast_report.py`、
`orchestrator/tests/test_b5_generator_contrast.py`、`orchestrator/tests/test_b5_generator_contrast_report.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、
新規 `orchestrator/tests/test_b5_tier0.py`。これ以外 (pipeline / buildcache / runner / materializer 登録 / campaign_lock / T-2830 所有 / T-2632 の他所有) は編集しない。

1. **子 (p3_s4_loop.py、B-5 mode の候補経路のみ):** `_run_one_iteration_resolved` の `_require_condition_gate` の後・`campaign_options` 組立て後・
   `pipeline-submitted.json` 書込みの前に Tier0 を置く。stock-control 経路 (`_run_stock_control_resolved`)・非 B-5 経路・`do_build=False` は不変。
   - 契約定数 `B5_TIER0_CONTRACT` (module 定数、JSON 化可能な dict) を 1 箇所に定義: `contract_id="b5-tier0/v1"`、`applies_to=["search","score"]`、
     build = trace-disabled 1 本 (pipeline と同じ build 経路・引数)、smoke flags = `thread_num=4, ycsb_tuple_num=200, extime=1, ycsb_rratio=50,
     ycsb_zipf_skew=0.9, ycsb_rmw=true, ycsb_max_ope=5` + `clocks_per_us` = env contract の値、numactl = env contract の値、`timeout_s=32`、
     通過条件 = rc 0・既存パーサ (`benchparse.integer_abort_commit_counts` の commit > 0、`benchparse.throughput_tps` が有限正)、
     失敗処理 = build `(RuntimeError, SubprocessError)` と smoke 失敗は候補起因 (A のみ、retry なし)、smoke 値は性能値に使わない旨。
   - build: pipeline `_build_one(trace=False)` と同じ呼び方 (v2 selector があれば `buildcache.build_v2`、なければ `buildcache.build`) を同じ
     `admission` / `build_context` / `source_evidence` / cache root / dependency / grammar version / capability で呼ぶ。新しい `"--build"` 定数・CMake argv を作らない。
     `test_ccbench_spawn_sites.py` の build sink / condition gate 先行検査を弱めない (build 呼出しを無条件 helper に隠さない)。
   - smoke: 既存 gateway `orchestrator.calibrator.runner.run_once(binary, flags, numactl=..., timeout_s=32, strict_returncode=True, use_perf=False)` を
     既存 `bench_lock()` の内側で 1 回。新しい subprocess 起動点を作らない。`test_ccbench_spawn_sites.py` の `_BOUNDED_RUN_ONCE_CLIENTS` に 1 行足す。
   - 記録: `_write_b5_sidecar(b5_sidecar_dir, "tier0.json", ...)` (既存の create-once atomic writer) を判定後・submission 前に 1 回。
     schema `p3-s4-loop-b5-tier0/v1`、identity は既存 `_b5_sidecar_payload(cfg, genome)` と同じ field、`contract` (= 定数全体)、`status` (`passed` / `rejected`)、
     `reason` (null / `build-error` / `smoke-failed` / `smoke-timeout`)、`build = {trace:false, binary, bin_sha256, cached}` (失敗時 null)、
     `smoke = {flags, timeout_s, returncode, wall_s, commits, aborts, throughput_positive}` (未実施 null、NaN/Inf 不可)、`error` (例外要約、成功時 null)。
   - 不通過: submission を書かずに outcome `rejected-tier0` を返す。`drive_iteration` の B-5 早期 return 集合 (`{"duplicate-skip","rejected-preprocess"}`) と
     CLI の rc 3 分岐に `rejected-tier0` を足す。WAL は書かない。
   - T-2632 の land 後の版で行番号・引数・provenance の outcome 値域を再照合し、`rejected-tier0` が T-2632 の side channel で表現できることを確かめる
     (表現できなければ author は止めて報告)。
2. **driver (b5_generator_contrast.py):**
   - `classify_slot`: B-5 候補 slot (proposal あり) で `tier0.json` を読む。identity (b5_slot / campaign_id / genome) と `contract == loop_driver.B5_TIER0_CONTRACT` を照合。
     submission なし + valid rejected → outcome `rejected-tier0` / failure_class `candidate` / submitted False。submission あり + valid passed → 従来の投入後分類。
     submission あり + passed 証拠なし/不正/rejected → `unclassified-missing` (submitted True)。submission なし + passed → 既存どおり未解決扱い。
     stock slot に `tier0.json` があれば `unclassified-missing`。結果に `tier0 = {status, reason, sidecar_sha256}` (数値なし)。
   - `_execute_slot`: retry 対象は不変 (`rejected-tier0` は retry しない)。B は `submitted_once` のまま。
   - `run_series`: search の `rejected-tier0` は既存の非投入分岐 (`proposal-rejected` event、次の A へ)。score の `rejected-tier0` は既存の非 certified 分岐。
   - `_header`: `tier0_status="implemented"`、`tier0_contract=loop_driver.B5_TIER0_CONTRACT`。module docstring の "Tier0 is not implemented" を実態に合わせる。
3. **report:** 共通構成比較に `tier0_status` / `tier0_contract` を加える。新契約台帳の混在・契約差を拒否、試走 (not-implemented 一式) の読取りは不変。A / B 回収は変えない。
4. **test:** 新規 `test_b5_tier0.py` (子): 固定 argv と既存パーサ (fixture executable で gateway・parser を実物で通す)、rc 非 0 / 出力不正 / commit 0 / timeout、bench lock、
   実挿入点での順序 (build → smoke → tier0.json → submission) と perf binary が gateway に届くこと (trace build を Tier0 で作らない)、拒否時 rc 3・digest 非生成・submission なし、
   非 B-5・stock・`do_build=False` で Tier0 が走らない。driver / report: `rejected-tier0` で A だけ進み B 不変・retry なし、random 30 件全拒否で `a-exhausted`、
   LLM 拒否後の `expected_inputs` 不変、score 拒否で停止・fallback なし、前 attempt 投入済み + Tier0 拒否で B 保持、submission あり + passed 証拠欠落/不正で停止、
   Tier0 passed → anomaly で B=1・endpoint 不採用、smoke 値が event・current_perf・endpoint に入らない、header 契約、report の契約混在拒否と試走台帳の読取り。
   既存期待値の変更は `test_series_scores_fresh_sessions_after_endpoint_fix` の `tier0_status == "not-implemented"` (契約変更による) と report fixture の分割だけ。
5. **親の生死確認:** 実装後、gen_S で B-5 slot 1 件分 (機械生成の候補 1 件、scratch の submit-tree、cohort 外) を子で走らせ、`tier0.json` passed・pipeline の
   perf build が cache hit (bin_sha256 一致)・verify / bench 継続を確かめる。費用 ≈ 1 session (≈ 500 s)。B-5 本走・校正ではない。
   (実施可否は段 6 で、scratch 名前空間を汚さず作れるかを確かめてから決める。)

## 4. 設計のみ (実装しない、decisions fragment + insight へ)

- **P6 親運用:** `LLM_WAIT_S = 2700` は変えない。LLM 系列 1 本に親 session 1 本 (系列開始前に確保し終了で context を廃棄、§4.1 fresh context)。同時親数 p = 4 は運用上の選択
  (§7.1 から導かれるものではない)。同時に走る LLM 系列は p 本以下。実効 handshake 期限 = min(2700, 残 walltime − 1800) (poll 15 s の誤差)。試走の 1 巡 10〜13 分は
  n = 1 系列 10 巡の実測で上限保証ではない。親が止まれば系列は登録どおり `proposal-wait-timeout` / `allocation-exhausted` の欠測 (救済しない)。
  1 親に 2 系列以上を順番待ちさせる案は 780 s × 系列数 が期限に近づき、context 分離も崩すので採らない。
- **P7 walltime:** 探索 3 arm 共通 W = ceil(21,259 s × k) (21,259 s = 試走の series job Elapse の実測最大、llm arm、共有 lock 待ちと親待ちを含む。推定で差し引かない)。
  block-stock は探索 arm でない別 job なので W_stock = ceil(5,447 s × k) を別基準として §12 に明記。k は倍率としてユーザーへ再提示 (候補 2 → 42,518 s / 10,894 s)、
  gen_S 上限 86,400 s から k ≤ 4.06。限界: write-heavy のみ・Tier0 追加前・共有 lock 下・n = 1。Tier0 の追加費は候補あたり smoke ≈ 1 s (+ build は pipeline の cache hit)。
  `SESSION_BUDGET_S = 1800` は次 slot 開始の残時間判定で timeout ではない。deadline は scheduler 開始 + 要求 walltime (job body) のまま。

## 5. 変異の事前登録 (DW-M01、実装後に単一理由性を確認して nodeid を確定)

| M | 位置 | 変異 | 落ちるべき検査 |
|---|---|---|---|
| M1 | 子 挿入点 | Tier0 呼出しを削除 (直接 submission) | 子: 順序 test / driver: submission + passed 欠落で停止 |
| M2 | 子 挿入点 | submission を Tier0 より前に書く | 子: 順序 test |
| M3 | 子 build | Tier0 の build を trace=True にする | 子: perf binary が gateway に届く test |
| M4 | 子 smoke | smoke の rratio を workload の値 (または rr20) にする | 子: 固定 argv test |
| M5 | 子 smoke | `strict_returncode=False` | 子: rc 非 0 test |
| M6 | 子 smoke | commit > 0 検査を外す | 子: commit 0 test |
| M7 | 子 smoke | timeout を渡さない | 子: timeout test |
| M8 | 子 smoke | bench lock を外す | 子: lock test |
| M9 | 子 拒否 | 拒否時も submission を書く | 子: 拒否 test / driver: A のみ test |
| M10 | 子 拒否 | `rejected-tier0` を早期 return 集合から外す | 子: 拒否時 digest 非生成 test |
| M11 | 子 build | 捕捉を `Exception` に広げる (admission 等も候補起因に) | 子: 準備段の例外が伝播する test |
| M12 | driver | `rejected-tier0` を submitted 扱い (B 消費) | driver: A のみ test |
| M13 | driver | `rejected-tier0` を retry 対象に入れる | driver: retry なし test |
| M14 | driver | submission ありで passed 証拠を検査しない | driver: 証拠欠落で停止 test |
| M15 | driver | smoke の数値を event に載せる / current_perf に使う | driver: 数値非流出 test |
| M16 | report | 共通構成比較から tier0 key を外す | report: 契約混在拒否 test |
| M17 | driver | header を `not-implemented` に戻す | driver: header 契約 test |
