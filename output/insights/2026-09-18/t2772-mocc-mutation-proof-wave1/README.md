# [T-2772] mocc の auditor-live 相当の機械実証 wave 1 — hot 経路の実行証拠と 36 走 matrix (2026-09-18)

authority: none
default_effect: no-state-change

- wave: `dev-wave-t2772-mocc-mutation-proof-wave1` (branch `worktree-dev-wave-t2772-mocc-mutation-proof-wave1`、base = local main `d2ebef7a4`)
- 起点: ユーザーの `/dev-wave [T-2772]` 引数 (D579、D2134 項 3〜5・8)。設計正本 = `output/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md` §6〜§7・§12
- 逐語: `verbatim/` (親 brief、段 2 plan、段 3 レンズ A / B、段 4 裁定、段 5 author 報告、段 6 レビュー A / B と fix 報告、prompt 8 本)。sha256 は `verbatim/MANIFEST.json`
- 計測: compute (Pegasus gen_S、generic dispatch) 2 回。`compute-1.json` (fix 前 driver `b112a2898`、request 5045.nqsv、Elapse 794 秒、all_pass=True) と `compute-2.json` (fix 後 driver `ec765587a`、request 5096.nqsv、Elapse 791 秒、all_pass=True)。repo に commit した proof JSON は compute-2 の bytes

## 0. 位置づけと非解禁

D579 が mocc の変異探索面化に要求する「独立の auditor-live 相当の機械実証」のうち、D2134 項 3 の**経路共通部分** (固定 producer e9e477ca + 計装 patch 上の
X/P、hot / cold / 既定の 3 regime × 1 / 4 thread、既存負例 3 本、hot 専用負例) を実装・実走した。**本 wave の緑は、mocc の変異探索・pin 前進・
温度述語の軸採用・certified 比較のいずれも認可しない** (D2134 項 9)。template 接続の実証 (wave 2 = [T-2773]) と軸の A / B、pin 手続き
(D1603 / D297 / D2114 項 3、[T-2756]) は別途である。

## 1. 成果物

| 物 | path | 内容 |
|---|---|---|
| 新負例 patch | `patches/broken-mocc-hot-update-unlock.patch` (sha256 `5562c566…`) | 裸 define `IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK`。file scope の 1 directive で `static constexpr bool … = TRACE != 0` と `static thread_local Tuple* izanagi_hot_update_pending` を両腕に宣言し、3 site を `if constexpr` で従わせる: (1) `update()` の hot 分岐 (論理行 459) で `lock(tuple, true)` 成功直後に `w_unlock()` + pending 記録、(2) `writePhase()` の publish 検査後・tidword store 前に `pending->rwlock_.w_lock()` で直接再取得、(3) `abort()` の `unlockCLL()` 前に同じ再取得。`#line` 17 / 460 / 1069 / 1195。preimage = e9e477ca + `instr-mocc-lock-coverage.patch`、touch set = `cc/mocc/transaction.cc` のみ |
| 新 driver | `orchestrator/campaign/s3_mocc_mutation_proof.py` | 36 走 matrix、32 check、run ごとの実 argv・終了状態・timeout・`wall_seconds`・verifier raw record。旧 driver `s3_mocc_lock_coverage.py` の helper (`_prepare_dependencies`、`_common_configure_args`、`_apply_owned_patch`、`_trace0_record`、`_run_checked` 等) を import で再利用し、旧 driver・旧 JSON・旧 14 check は 1 byte も変えない。新規の直接 subprocess site は `_run_trace` の 1 箇所 |
| 新 test | `orchestrator/tests/test_mocc_mutation_proof.py` | 11 node (balanced 構造、一意 witness、matrix / check key の exact、入力由来、JSON consumer、失敗 / timeout 記録、verifier 束縛、gate の driver ID、論理行列、U の R 行計数) |
| 新 JSON | `output/env/pegasus/calibration/s3_mocc_mutation_proof.json` | schema `s3-mocc-mutation-proof/v1`、patch 5 本の sha256・旧 JSON の sha256 に束縛 |
| 登録簿閉包 | `materializer_admission.py` (新 `_build_variant` を NON_ADMISSIBLE)、`condition_meaning_gate.py` (DefineSpec + witness、供給 39 / witness 15)、`screening_driver.py`、`test_condition_meaning_gate.py` (route 17)、`test_ccbench_spawn_sites.py` (`_run_trace` allowlist、W/U 4 FLAGS、Counter 35 / 39 / 25 / 25)、`test_p3_build_authority_cli.py`、`test_p3_s4_loop.py` (B-3) | |
| docs | `patches/README.md` の mocc 節に新負例の項 | |

## 2. 36 走 matrix の実測 (compute-2 = repo の JSON。compute-1 は同型で job dir に保全)

略号: X = lock 被覆違反総数、P = permutation 違反総数、R = trace の R 行数、W = 非 INSERT の W 行数。verdict / certified は verifier の値をそのまま。

| run | 区分 | verdict | certified | cycles | txns | X | P | R 行 | 非 INSERT W | version_dups |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| stock_hot_t1 | 必須 | serializable | True | 0 | 183,974 | 0 | 0 | 862,908 | 862,908 | 0 |
| stock_hot_t4 | 必須 | serializable | True | 0 | 201,220 | 0 | 0 | 943,914 | 943,914 | 0 |
| stock_cold_t1 | 必須 | serializable | True | 0 | 190,360 | 0 | 0 | 892,811 | 892,811 | 0 |
| stock_cold_t4 | 必須 | serializable | True | 0 | 203,978 | 0 | 0 | 956,855 | 956,855 | 0 |
| stock_default_t1 | 必須 | serializable | True | 0 | 190,070 | 0 | 0 | 891,368 | 891,368 | 0 |
| stock_default_t4 | 必須 | serializable | True | 0 | 205,899 | 0 | 0 | 966,060 | 966,060 | 0 |
| stock_u_hot_t1 | 必須 | serializable | True | 0 | 1,094,184 | 0 | 0 | 0 | 1,094,184 | 0 |
| stock_u_hot_t4 | 必須 | serializable | True | 0 | 3,435,007 | 0 | 0 | 0 | 3,435,007 | 0 |
| stock_u_cold_t1 | 必須 | serializable | True | 0 | 1,099,152 | 0 | 0 | 0 | 1,099,152 | 0 |
| stock_u_cold_t4 | 必須 | serializable | True | 0 | 3,789,769 | 0 | 0 | 0 | 3,789,769 | 0 |
| stock_u_default_t1 | 必須 | serializable | True | 0 | 1,101,157 | 0 | 0 | 0 | 1,101,157 | 0 |
| stock_u_default_t4 | 必須 | serializable | True | 0 | 3,698,353 | 0 | 0 | 0 | 3,698,353 | 0 |
| lockskip_hot_t1 | 観測 | indeterminate | False | 0 | 154,551 | 1,123,521 | 0 | 725,418 | 725,418 | 0 |
| lockskip_hot_t4 | 観測 | non-serializable | False | 587 | 173,003 | 1,251,762 | 0 | 811,601 | 811,601 | 3,564 |
| lockskip_cold_t1 | 必須 | indeterminate | False | 0 | 137,262 | 1,931,289 | 0 | 643,763 | 643,763 | 0 |
| lockskip_cold_t4 | 必須 | non-serializable | False | 3,882 | 177,106 | 2,446,672 | 0 | 831,191 | 831,191 | 21,954 |
| lockskip_default_t1 | 必須 | indeterminate | False | 0 | 135,620 | 1,908,921 | 0 | 636,307 | 636,307 | 0 |
| lockskip_default_t4 | 必須 | non-serializable | False | 3,622 | 173,578 | 2,399,309 | 0 | 814,673 | 814,673 | 20,668 |
| perm_hot_t1 | 必須 | indeterminate | False | 0 | 55 | 0 | 1,111 | 264 | 209 | 0 |
| perm_hot_t4 | 観測 | indeterminate | False | 0 | 115 | 0 | 4,362 | 547 | 432 | 0 |
| perm_cold_t1 | 必須 | indeterminate | False | 0 | 225,537 | 0 | 225,537 | 1,057,768 | 832,231 | 0 |
| perm_cold_t4 | 観測 | indeterminate | False | 0 | 229,851 | 0 | 235,900 | 1,078,012 | 848,161 | 0 |
| perm_default_t1 | 観測 | indeterminate | False | 0 | 221,275 | 0 | 221,275 | 1,037,926 | 816,651 | 0 |
| perm_default_t4 | 観測 | indeterminate | False | 0 | 227,717 | 0 | 234,641 | 1,068,013 | 840,296 | 0 |
| early_unlock_hot_t1 | 必須 | indeterminate | False | 0 | 138,724 | 1,301,972 | 0 | 650,986 | 650,986 | 0 |
| early_unlock_hot_t4 | 観測 | non-serializable | False | 3,636 | 162,091 | 1,464,897 | 0 | 760,121 | 760,121 | 17,866 |
| early_unlock_cold_t1 | 必須 | indeterminate | False | 0 | 145,182 | 1,362,538 | 0 | 681,269 | 681,269 | 0 |
| early_unlock_cold_t4 | 観測 | non-serializable | False | 1,556 | 161,444 | 1,480,018 | 0 | 757,167 | 757,167 | 8,807 |
| early_unlock_default_t1 | 観測 | indeterminate | False | 0 | 145,540 | 1,364,976 | 0 | 682,488 | 682,488 | 0 |
| early_unlock_default_t4 | 観測 | non-serializable | False | 1,437 | 159,875 | 1,466,919 | 0 | 749,779 | 749,779 | 8,324 |
| hot_update_unlock_hot_t1 | 必須 | indeterminate | False | 0 | 697,364 | 2,092,092 | 0 | 0 | 697,364 | 0 |
| hot_update_unlock_hot_t4 | 観測 | indeterminate | False | 0 | 2,431,108 | 7,241,088 | 0 | 0 | 2,431,108 | 67,777 |
| hot_update_unlock_cold_t1 | 必須 | serializable | True | 0 | 1,095,541 | 0 | 0 | 0 | 1,095,541 | 0 |
| hot_update_unlock_cold_t4 | 必須 | serializable | True | 0 | 3,568,503 | 0 | 0 | 0 | 3,568,503 | 0 |
| hot_update_unlock_default_t1 | 必須 | serializable | True | 0 | 1,096,458 | 0 | 0 | 0 | 1,096,458 | 0 |
| hot_update_unlock_default_t4 | 必須 | serializable | True | 0 | 3,794,676 | 0 | 0 | 0 | 3,794,676 | 0 |

- **hot 専用負例 (主証拠)**: hot t1 は 697,364 txn で `not-locked-at-entry` / `lock-lost-before-write` / `lock-lost-before-publish` が各 697,364 (1 txn 1 回ずつ)、
  P 0、cycle 0、R 行 0、W = txn。hot t4 も 2,431,108 txn を hang なしで完走し X 7,241,088 (reason 別正数は保証しない、観測。version_dups 67,777 は lock を欠いた 4 thread の許容挙動)。cold / default の 4 走は
  stock-U と同じ certified で沈黙 (温度述語 false で site 1 に入らない)。**これが D2134 項 4 の保証名「stock 等価述語における hot-update 負例の到達と、
  既存 X 3 検査点の検出」の実測である。** 4 site 全被覆・read 側 hot 経路・RLL 再試行・DELETE 経路は含意しない。
- **stock**: W / U × 3 regime × 2 thread の 12 走すべて certified。hot 強制 (閾値 0) でも 4 thread で cycle 0。U 4 thread は 343〜379 万 txn。
- **lockskip**: hot t1 でも 3 reason が正数 (観測のみ)。理由: 多操作 txn で `lock()` の canonical restore (834〜858) が先に取った早期 w_lock を
  解放して CLL から消し、validation の lock skip でそのまま writePhase へ入るため。cold / default の 4 走は設計どおり (t1 = I、t4 = cycle 正数の N)。
- **perm-erase の hot regime**: t1 で commit がわずか 55 txn (P 1,111。compute-1 では 20 txn / P 620,462 と走ごとに大きく揺れる)。`pop_back()` で write_set_ から落ちた要素の早期 w_lock は CLL に
  残り、read 検証 (1024〜1036) が「W_LOCKED かつ write_set_ に無い」として abort する。cold / default では validation 時にしか lock しないので起きない。
  受入必須の `perm_hot_t1_only_size_changed` は I・P>0・X 0・cycle 0・txn>0 を要求するので緑だが、hot での perm-erase は「ほぼ全 abort」という
  意味の負例になっている (設計は予見していない。記録のみ)。
- **early-unlock**: 3 regime とも入口 0・保持 2 reason 正数 (hot でも同じ)。t4 は cycle 正数 (観測)。
- **trace0**: 無 patch ↔ 計装のみで nm `izanagi` 0、strings 0、`.text` 一致 (差分 0 行)、TRACE=0 論理行列 543 行一致 (D1687)。
- **condition gate**: 負例 4 本とも supply / meaning green、admission admitted (driver ID `orchestrator.campaign.s3_mocc_mutation_proof`)。

### 2.1 compute-2 (fix 後 driver、repo の JSON)

compute-2 (request 5096.nqsv、08:00:48〜08:13:55 JST、Elapse 791 秒、driver `ec765587a`、toolchain g++-11 policy 一致、site PEGASUS_COMPUTE): **32 check all_pass=True**。
compute-1 と同じ形で、値は走ごとの揺らぎの範囲 (hot 専用負例 hot t1 = 697,364 txn × 3 reason 各 697,364、hot t4 = 2,431,108 txn / X 7,241,088、
stock-U 4 thread = 343〜379 万 txn、perm-erase hot t1 = txn 55 / P 1,111 — compute-1 の txn 20 / P 620,462 から大きく動いた。ほぼ全 abort + backoff の挙動で走ごとに変わる)。
4 thread 負例の `version_dups` は lockskip cold/default t4 = 21,954 / 20,668、lockskip hot t4 = 3,564、early-unlock hot t4 = 17,866、hot-update hot t4 = 67,777 で、
**裁定 R1 (段 3 レンズ A の予見) のとおり lock を欠いた 4 thread では balanced のまま同じ版が重複する。** 全 36 走に integrity clean を要求していれば all_pass は偽だった。
1 thread の負例 7 走と stock 12 走・hot-update cold/default 4 走は version_dups 0 (要求どおり clean)。JSON は 14.8 MB (gzip 1.6 MB) — verifier の
`integrity.notes` が version dup ごとに 1 行 (最大 67,778 行) を持つため。旧 JSON (640 KB) との差はこの raw record の保存 (裁定 R5) による。

## 3. login の生死確認 (build のみ、benchmark なし、`liveness-run-1.log`)

- 新負例 macro=1 / TRACE=1 と macro=0 / TRACE=1 を `-Wall -Wextra -Werror` で build 通過。既存負例 3 本と計装 stock も通過。
- macro=0 / TRACE=0 と **macro=1 / TRACE=0** (`TRACE != 0` の隔離) は無 patch base-t0 と `.text` 完全一致 (59,854 行、binary sha も両者同一 `71fc8a8e…`)、
  nm / strings 0。計装のみ TRACE=0 の 158 行差は source dir 名長の差 (`cc-instr` が 1 文字長い) による `__FILE__` の lea ずれ (D1687 既知) であり、
  compute の等長 dir では差分 0 行。

## 4. 検査・変異

- 焦点走 1 (gen_S 5029.nqsv、fix 前): 303 passed / 1 failed / 2 skipped (既存 skip)。赤 = test の repo 内 scratch dir が xdist で rmdir 競合 → fix 1 で system tmp へ。
- 焦点走 3 (gen_S 5152.nqsv、fix 後 + JSON consumer 込み): 305 passed / 0 failed / 2 skipped (既存の `except*` skip)。
- 変異 matrix (`mutation-spec-final.json`、`mutation-ledger.json`): baseline PASSED、12/12 KILLED (期待 node 完全一致)、等価 M0 SURVIVED、MISMATCH 0、TIMEOUT 0 (harness `tools/mutation_harness.py`、runner = `run_tests.py --force-dispatch` で新 test + 旧 proof test + condition gate + spawn_sites + build authority + s8b materializer 閉包 node、repo HEAD `bd7d7e09e`、spec sha `a40f19fad6b3…`)。patch 変異 M1〜M6 と M10 の JSON consumer 赤は sha / 登録簿束縛による冗長 gate であり検出力に数えない (主 killer は balanced 構造 node と登録簿 test)。期待 node は login probe 2 回 (自走 harness で probe-1 = 登録簿側、JSON commit 後の probe-2 = 新 test file) で実測して固定した。`test_screening_driver.py` は pytest 専用で probe 不能のため runner argv に含めず、B-3 (`test_p3_s4_loop.py`) は 260 秒/走で matrix 外 (T-2294 と同じ)。

| # | 変異 (対象 / 内容) | 期待 | 結果 | 赤 node (file::name) |
|---|---|---|---|---|
| M0-equivalent-comment | driver の comment 1 行を等価な文言へ (harness の SURVIVED 検出の正例) | SURVIVED | **SURVIVED** | — |
| M1-publish-relock-removed | patch: publish 側 relock block を削除 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M2-abort-relock-removed | patch: abort 側 relock block を削除 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M3-relock-via-txexecutor-lock | patch: relock を `lock(pending, true)` へ | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M4-publish-guard-inverted | patch: publish 側 guard を `!=` に反転 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M5-directive-duplicated | patch: 裸 directive を 2 箇所へ複製 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_hot_unlock_has_unique_condition_witness, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound, test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches, test_mocc_mutation_proof.py::test_mocc_mutation_condition_gate_uses_new_driver_id |
| M6-line-460-off-by-one | patch: `#line 460` → 461 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_is_balanced_on_commit_and_abort, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M7-hot-t1-check-constant-true | driver: hot t1 主 check を定数 True | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_mutation_checks_are_input_derived, test_mocc_mutation_proof.py::test_mocc_mutation_u_trace_counts_reads |
| M8-timeout-recorded-false | driver: `_run_trace` の timed_out を常に False | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_mutation_run_records_failure_and_timeout |
| M9-definespec-entry-removed | condition_meaning_gate: 新 DefineSpec entry 削除 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_hot_unlock_has_unique_condition_witness, test_condition_meaning_gate.py::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches, test_condition_meaning_gate.py::test_v1_domain_and_claim_boundaries_are_exact, test_condition_meaning_gate.py::test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK], test_mocc_mutation_proof.py::test_mocc_mutation_condition_gate_uses_new_driver_id, test_ccbench_spawn_sites.py::test_patch_define_inventory_matches_condition_gate_registry |
| M10-materializer-entry-removed | materializer_admission: 新 entry 削除 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_mutation_matrix_is_exact, test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound, test_p3_build_authority_cli.py::test_single_registry_has_typed_compatible_projections, test_p3_build_authority_cli.py::test_python_ccbench_manual_materializers_are_explicitly_non_admissible, test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches |
| M11-json-hot-patch-sha-changed | JSON: 新 patch の sha256 を 1 文字変更 | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |
| M12-json-all-pass-false | JSON: all_pass を false | KILLED | **KILLED** | test_mocc_mutation_proof.py::test_mocc_mutation_proof_json_is_complete_and_bound |

## 5. 段 2 / 段 3 / 段 4 / 段 6 の所見と裁定 (逐語は `verbatim/`)

- 段 2 plan (`gpt-6-astra`、medium): 負例 patch の逐語 (ON 側 bool を `TRACE != 0`)、U 限定の balanced 論証、helper 再利用の範囲 (`_verify` は新設)、
  36 走 / 32 check、登録簿逐語、変異候補 12。親 brief の P3 (t4 負例の integrity 免除) を棄却案とし、全 36 走に共通 integrity check を置く案。
- 段 3 レンズ A (正しさ境界・hang): must-fix 1 (P3 の根拠は誤りだが全走 clean も過剰 — 実証の合格と variant の認証を分ける)、should 6、nit 1。
  hot/t1 の 3 reason 発火と cold/default の沈黙に反例なし。U 限定の循環待ち不在は成立、starvation・120 秒内完走は未証明。
- 段 3 レンズ B (過剰・削除・閉包): must-fix 2 (件数 pin 5 箇所の閉包漏れ、新 main の site / 単独性契約)、should 3。旧 test の exact 集合は不変で赤にならない。
- 段 4 裁定 (`verbatim/s4-ruling.md`): R1 = integrity clean の要求範囲を D2134 項 5 で固定 ({{D:mocc-proof-wave1-integrity-scope}})、R2〜R12。refuted のうち不採用にした所見なし。
- 段 6 レビュー A (must-fix 2: scratch 競合、verifier 異常 rc の誤記録) / B (must-fix 1: scratch 競合) → fix 1 巡 (impl worktree `t2772-fix1`、Codex fix)。
  fix 後の焦点再レビューは投じず、変異 matrix (M8 timeout 記録) と焦点走 3 (305 passed) で裏取り。

## 6. 時間予算の実測 (DW-O13、裁定 R6)

- 事前: verifier は write-only 合成 trace 100 万 txn で 17.3 秒 (login、load 25)。
- compute-1: 36 走 + build 7 本 + condition gate 4 組で Elapse 794 秒 (gen_S 3600 秒の 22%)。U 4 thread は 360〜373 万 txn。
- compute-2 の走ごとの `wall_seconds`: benchmark は全走 ≤ 1.0 秒 (extime=1)。verifier は最大 54.8 秒 (stock_u_cold_t4)、上位 5 = stock_u_cold_t4 54.8 秒, hot_update_unlock_default_t4 54.4 秒, stock_u_default_t4 53.7 秒, hot_update_unlock_cold_t4 50.5 秒, hot_update_unlock_hot_t4 50.3 秒、36 走合計 607.6 秒 (Elapse 791 秒の 77%)。事前見積 (100 万 write-only txn = 17.3 秒 login) に対し compute の U 4 thread ≈ 370 万 txn が 55 秒 = 同程度の速度。

## 7. 主張しないこと・残件

- mocc が certified な第 2 例として成立すること、温度述語が正式な変異軸であること、stock mocc の観測間隙 (§3.2 (a)、別 T-2774 が実走中) の再現。
- read 側 hot 経路・RLL 再試行・DELETE の動的被覆、多操作 txn での balanced 性 (U 限定)。
- 4 thread 負例の別 integrity 異常は raw record に残すだけで check にしていない (R1)。
- wave 2 ([T-2773]) = template 接続、auditor.md の mocc 節、DQ / consumer 束縛の対照、gate test、n=1。
