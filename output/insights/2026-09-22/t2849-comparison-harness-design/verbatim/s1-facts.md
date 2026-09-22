# 設計の前提となる事実 (local main 8fd2a2f5c、2026-09-22)

記号: [親] = 親が file を読んで照合、[子] = 調査子 (Claude Explore、sonnet) の報告で親は未照合。

## 口と記録

- [親] 機械生成 proposal: `orchestrator/campaign/b5_generator_contrast.py:139-153` `machine_proposal_document` (arm は random / sweep-matched のみ、値は `validate_backoff_value` 通過のみ)。`slot_argv` (:506-528) は `p3_s4_loop --run-iteration <path> --machine-generated-proposal` を組む。
- [親] `p3_s4_loop.py:3450` `--machine-generated-proposal`、:3557-3559 `requires --run-iteration and --b5-slot`、:3550 `--b5-slot requires ... B-5 prefix`、:3552 `--b5-slot requires --calibrated-perf --perf-workload --verify-performance`。
- [親] loop の genome は silo 固定: `p3_s4_loop.py:2314, 2465, 3160` (`Genome("silo", {**_BASE, "BACK_OFF": 1, ...})`)、`b5_generator_contrast.py:588` `_genome`。`MARKER_ID = "silo-backoff-magnitude"` (:132)、`SOURCE_REL = "include/backoff.hh"` (:133)。
- [親] `build_admission.py:92-104` `BuildProvenance` = STOCK_BASELINE / CODER_AUTHORED / MACHINE_GENERATED / HUMAN_REVIEWED ("never selected by callers")。
- [親] `p3_s4_loop.py:1517` `_PROVENANCE_OUTCOMES`。[子] 値 = certified / aborted / rejected / dry-pass / duplicate / duplicate-skip / rejected-preprocess / rejected-tier0。
- [子] proposal schema: `p3_s4_loop.py:2934-2936` docstring、closed keyset `projection_guard.py:285-361`。由来 field は無い。
- [親] B-5 定数 `b5_generator_contrast.py:43-56`: PREREG_VERSION、B=10、A=30、N_EVAL=5、BLOCK_STOCK_SESSIONS=5、MAX_MACHINE_RETRIES=2、LLM_WAIT_S=2700、ARMS=("llm","random","sweep-matched")。[子] EVENT_FIELDS (:69-73) に a / b / outcome / failure_class / quality / fitness_tps / anomalies / timing ほか、END_REASONS (:65-68)。
- [子] B-5 の compile 失敗は `outcome="build-failed"` (:412)、Tier0 不通過は `rejected-tier0` で A のみ (D2215)。

## 空間と参照点

- [親] `p2_2_flag_opt` = `output/s1-freeze/known_axes_freeze.json:90-99` variant 5185ee5e6094、label B0-L-W0、flags BACK_OFF=0 / NO_WAIT_LOCKING_IN_VALIDATION=1 / NO_WAIT_OF_TICTOC=0 / WAL=0 (read-heavy は :544 B0-T-W0)。backoff 値の空間 (BACK_OFF=1) の外。
- [親] B-5 の候補 genome は silo・BACK_OFF=1・NO_WAIT_LOCKING_IN_VALIDATION=1・NO_WAIT_OF_TICTOC=0・WAL=0、stock は同じ flags で BACKOFF_FIXED=-1 (B-5 §5.2)。
- [子] silo の flag 空間 `genome.py:106-117` 有効 8 点。sort 79 値 `sort_swo_oracle.py:788-813`、trigger 5-bit 32 点 `reflux_ir.py:92-121`。近傍関数はどれも未実装。
- [親] D2214 §5 (insight `output/insights/2026-09-21/silo-function-synthesis-space/README.md` §5): 比較 A / B の分離、最小 arm = 非 LLM×IR / LLM×IR / LLM×C++、共通条件 (B・A・初期候補・観測・workload・verify・rep・停止・retry・endpoint 再評価)、初期候補 = exact reference (stock・元 flags の p2_2_flag_opt・調整済み静的 backoff) + 新骨格内 seed (待機 0 + 即 abort、静的 5 / 10 µs)、BO は後段 (差分分析 P2) へ。§6 の試走案は「初期 3 + 探索 8 + endpoint 5」。
- [子] silo-function-policy の実装コードは 0 件 (識別子 grep)。

## 実装の出所

- [子] repo の orchestrator/ と tools/ に BO・進化 (GP、TPE、optuna、skopt、smac、botorch、EI、GA、CMA、population、crossover、hill-climb、coordinate descent) の実装 0 件。`evolve_block.py` は marker の text 処理だけ。
- [子] login の `/usr/bin/python3` 3.10.12: numpy 2.2.6 のみ import 可。scipy / sklearn / optuna / skopt / botorch / torch / smac / nevergrad / deap は ModuleNotFoundError。計算ノードの python は未測定。repo に requirements / pyproject は無い。

## 観測

- [子] `p3_s4_loop.py:1303-1304`: current_perf / leading_indicators の組立は「メインセッションが別途合成」(module の責務外)。whiteboard 5 field (:656-667)、`k2_next_generation_inputs` (:1273-1292)。autonomous 版 `p3_autonomous_workload_trial.py:2043-2076` に payload 組立がある。
- [子] P2-5: `search_baselines.py` の random / critic-free greedy / oracle は WAL replay、`critic/online_digest.py:35-57` の online digest (LeakageError)。両 arm とも digest.axis_effects だけを見る対称設計 (D21 付近)。

## MOCC

- [親] MOCC は `include/backoff.hh` を include (`external/ccbench/cc/mocc/transaction.cc:7`、`cc/mocc/include/transaction.hh:6`)、BACK_OFF 時に `Backoff::backoff` (:1079-1087)。`patches/silo-backoff-fixed.patch:12-23` は `BACKOFF_FIXED` を `ccbench_universal_definitions` (全 protocol 共通) に足す。
- [親] `orchestrator/verifier/model.py:37` `_PROOF_SURFACE_PROTOCOLS = {"silo","si","mocc"}`、`source_digest.py:85-86` の編集面に `cc/mocc/transaction.cc`、`between_run_floor.py:67` に MOCC の baseline genome、`genome.py:125,211` に MOCC_SPACE。
- [子] MOCC_SPACE = BACK_OFF / TEMPERATURE_RESET_OPT / KEY_SORT の 2^3 = 8、消費 driver なし。MOCC の既知最良 (P2-2 相当) の実測 0 件。
- [子] MOCC の certified 実走は T-2294 (tuple 200・extime 1 秒・thread 1 / 4、rratio 0・rmw) と T-2844 の候補 C 上の 6 走だけ。温度述語 hole (`axis_mocc_temperature.py:15-30`) は proof-only (D2134 項 9)。
- [子] pin: gitlink・`pin.CURRENT_PIN`・`s8b_approved.CCBENCH_FULL_SHA` は e9e477ca。候補 C 68106660 は driver 定数に未出現。T-2858 = 人間の push (D16) → D1603 材料で pin 再承認を提示 → gitlink 更新は別 wave。第 31 回項 8 で push は人間手番と確認。

## 裁定

- [子] D2212 項 4 (2 node 時間以上は事前確認)、第 31 回 (2026-09-22) 項 1・6・8 [親が inbox 原本で照合]。D2216 = LLM arm 親運用 (同時親 p=4、1 機会 2,700 秒)、D2217 = 共通 walltime W = ceil(21,259 s × k)。いずれも「設計のみ」で未実装 [子]。
