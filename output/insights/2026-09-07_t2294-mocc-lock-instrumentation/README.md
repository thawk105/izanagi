# [T-2294] mocc に lock 被覆と permutation の計装を入れた — 真実源は RWLOCK と CLL、性能 build は `#line` で bytes まで preimage と一致

**すべて非認証である。** 本 wave は verifier の入力 (X / P 行) を増やし、その歯を負例で立証しただけで、mocc の certified 昇格の
判定は変えていない。性能値も出していない (診断 build は materializer 登録簿で NON_ADMISSIBLE)。

## 0. 依頼と結論

依頼: mocc に lock 被覆 (X) と permutation (P) の `#if TRACE` 計装を入れ、正例 (被覆あり) と負例 (被覆を落とした変異 patch) を
実体を名指しして立証する。Silo の Tidword 計装は転用しない。性能 build から D14 契約で完全除去する。verifier は無編集。

結論:

| 項目 | 結果 |
| --- | --- |
| compute 実走 (Pegasus gen_S job 979791、Elapse 130 秒) | **14 check all_pass** |
| stock 1 thread / 4 thread | certified、X 0・P 0、txn 190,384 / 203,460 |
| lockskip 1 thread | X 1,927,227 (3 reason 各 642,409)、cycle 0、indeterminate |
| lockskip 4 thread | X 2,382,127、**cycle 3,754 (non-serializable)** |
| perm-erase 1 thread | P 221,097 (全て `size-changed`)、X 0 |
| early-unlock 1 thread (balanced) | 完走、`not-locked-at-entry` 0、保持 2 reason 各 685,184 |
| TRACE=0 (規律 1) | nm / strings 0、`.text` 差分 0 行 (compute)、`.text` bytes sha 一致 e5ba3e07… (login、同長 dir) |
| 変異 matrix (harness 本走、19 件) | **19 / 19 KILLED**、MISMATCH 0、baseline 緑 (08:26〜08:47 JST) |

## 1. 設計 (段 4 裁定と段 6 の再裁定)

- **3 検査点**: mocc は payload 書き込み (`memcpy` / `remove_value_if_present`)・tidword publish (`__atomic_store_n`)・`unlockCLL()` が
  別の場所にあるので、Silo の 2 点では publish 前の lock 喪失を見逃す。入口 / payload 直前 / publish 直前の 3 点にし、reason
  `lock-lost-before-publish` を足した (verifier は reason を自由 token として数えるので無編集で通る)。
- **CLL predicate**: `key_ == rcdptr_ ∧ mode_ ∧ lock_ == &rcdptr_->rwlock_` を要求する。counter に owner ID が無いので
  「CLL が stale で他 worker が同じ lock を再取得した」状態は入口では区別できない (既知限界、README に明記)。
- **`#line` 例外** (D14 の brief 不変条件の字面を変更): 各 `#endif` の直後に preimage の論理行番号を復元する `#line N` だけを
  `#if TRACE` の外に置く。無いと後続 `ERR` / `NNN` の `__LINE__` immediate と rip 相対 lea が 14 箇所動く (login probe)。
- **witness の再裁定 (段 6)**: 段 4 は「line marker 込みの `-E` byte 一致」を正本にしたが、`#line` 自体が marker 行を増やすので
  生 byte 一致は構造的に不可能 (fix 子の初回実装は必ず赤)。marker を論理行へ畳んだ「(行番号, 非空本文) 列」の一致へ再裁定した。
  `-P` は `__LINE__` drift に盲目なので不可。列比較は `#line` ±1 を検出する (fix 子が実測: index 445 で `(1160, …)` vs `(1161, …)`)。
- **early-unlock を balanced に**: `w_unlock()` は `counter_++` なので単純挿入は counter を `0 → 1` に壊し次の writer が永久 spin する。
  入口検査後に unlock、publish 検査後に `w_lock()` で再取得し、最後の `unlockCLL()` が `-1 → 0` を正常に行う。
- **裸 directive は owner file に 1 回**: 段 5 の実装は 2 site に同じ `#if` を置き、production の condition gate (exactly-one) で
  driver が停止する構造だった (段 6 レビュー B が静的に発見)。file scope の `static constexpr bool` 1 箇所 + `if constexpr` 2 site へ。
- **`#error` は置かない**: 裸 define 登録簿が `RWLOCK` を新設 interface と数える。RWLOCK 無しでは `CLL_` が宣言されず compile error。

## 2. 実測

### 2.1 login (pegasus02、`liveness-run-{1,2}.log`、`probe-samelen-{1,2}.log`、`pp-compare.log`)

- TRACE=1 の instr / lockskip / perm / early の 4 binary は CCBench の CMake (`-O3 -Wall -Wextra -Werror -std=c++20`) で `ycsb_mocc.exe`
  まで通過 (各 8〜10 秒)。TRACE=0 (instr 適用) は `nm -C` の `izanagi` 0、`strings -a` の `izanagi_trace` / `IZANAGI_` 0。
- **`.text` は同じ長さの dir で build すると bytes まで一致** (sha256 e5ba3e07…、objdump 59,779 行完全一致)。dir 名の長さが 1 文字違うだけで
  `__FILE__` 文字列長の差により `.rodata` が 16 byte 動き、rip 相対 `lea` 158 行が不一致になる (命令・immediate は同一)。
  観測者効果ゼロを bytes で言うには path 長まで揃える必要がある。driver は build dir 名を等長 (`trace0-base` / `trace0-inst`) にした。
- 前処理の論理行列: 無 patch と instr 適用で 543 行完全一致 (`#line` 7 箇所: 17 / 990 / 991 / 1158 / 1169 / 1187 / 1195)。
- condition gate の probe (`gate-probe-{1,2,3}.log`): 1 回目は supply / meaning とも `configure-failed` (下記 §3)、修正後は lockskip・
  early-unlock とも green (`requested-default-preprocess-different` / `declared-compile-time-branch-selection-observed`)。

### 2.2 compute (Pegasus gen_S、generic dispatch、`compute-{1,2}.log`)

- 1 回目 job 979769 (52 秒): `condition gate rejected IZANAGI_BREAK_MOCC_LOCK_COVERAGE: red/red`。
- 2 回目 job 979791 (03:01〜03:03 JST、Elapse 130 秒): all_pass。toolchain = `/usr/bin/x86_64-linux-gnu-g{cc,++}-11`、version body sha は
  policy と一致。JSON = `output/env/pegasus/calibration/s3_mocc_lock_coverage.json` (patch 4 本の sha256 に束縛、consumer test が読む)。
- lockskip 4 thread が本物の cycle 3,754 本を出したのは副産物として重要: lock 被覆の破れは 1 thread では X でしか見えず、
  多 thread で初めて直列性違反として現れる。被覆検査は cycle 検出より早い段で歯を持つ。

## 3. レビュー・裁定の台帳

- 段 2 plan (must-fix: `#line`、裸 define 登録簿の閉包、policy 束縛 compiler、early-unlock 3 本目)。
- 段 3 敵対相談 2 本 (A: must-fix 6、B: must-fix 7) → 段 4 裁定 `stage4-ruling.md` (採用 10 / refuted 5)。
- 段 6 敵対レビュー 2 本 (A: must-fix 4、B: must-fix 9、いずれも NO-GO) → 裁定 `stage6-ruling.md` R1〜R8 + 親担当 P1〜P3。
  親が refuted: `toolchain_matches_policy` 定数は到達後条件 (改善として観測値比較へ)、build dir 等長化は correctness ではない (保険)。
- fix 3 巡: fix-1 (R1〜R8、一枚岩)、fix-2 (compute 1 回目の blocker = `-DRULE_LAUNCH_COMPILE=` 除去)、fix-3 (焦点再レビューの
  partial R3 = 条件式の逐語固定、resolver unit node)。焦点再レビュー 1 本 (closed 7 / partial 1 / regressed 0)。4 巡目は投じず、
  R3' の閉じは変異 M18〜M20 で裏取り (DW-O16 の 3 巡上限)。
- compute 1 回目の原因: condition gate は configure が成功しても stderr 非空を fail-closed で red にする。driver が渡した
  `-DRULE_LAUNCH_COMPILE=` を CCBench の project は使わず CMake が「未使用変数」警告を出していた。login の生死確認は警告を無視して
  build を通していたので見えなかった。

- 受入 1 回目 (tip 3d08167bd、main dcf053f1c を post-claim merge): 20,957 緑 / 1 赤
  `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`。この test は campaign 配下で
  文字列 `--build` を持つ全関数と materializer 登録簿 (`NON_ADMISSIBLE_MATERIALIZERS`) の exact 一致を要求する。driver の
  `_install_dependency` (gflags / glog の一時 static install) が未登録だった。fix 子 4 が `NON_ADMISSIBLE` で登録
  (CCBench binary を生まず性能値の出所にならない、理由は登録簿の文言)。実装は変えていない。

## 4. 変異台帳 (spec v3、19 件、runner = proof_surface / condition_gate / spawn_sites / build_authority / verifier の 5 file)

| id | 変異 | 期待 killer (probe 観測、file::node) | 本走 |
|---|---|---|---|
| M1 | instr patch: P block の `#if TRACE` → `#if 1` | 6 node: test_broken_mocc_patches_have_unique_production_condition_witnesses, test_broken_mocc_permutation_patch_pops_between_sort_and_trace_check, test_compute_positive_control_json_is_all_pass_and_bound, test_instr_patch_keeps_trace0_preprocess_identical, test_mocc_clean_fixture_is_certified_with_patched_snapshot, test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch | KILLED |
| M2 | instr patch: 入口 reason を `not-locked` へ改名 | 3 node: test_broken_mocc_early_unlock_patch_unlocks_after_entry_and_relocks_before_publish, test_compute_positive_control_json_is_all_pass_and_bound, test_instr_patch_names_cll_lock_pointer_predicate | KILLED |
| M3 | instr patch: CLL predicate の `lock_ ==` 条件を `true` へ | test_compute_positive_control_json_is_all_pass_and_bound; test_instr_patch_names_cll_lock_pointer_predicate | KILLED |
| M4 | instr patch: `#line 1169` → `1170` | 3 node: test_compute_positive_control_json_is_all_pass_and_bound, test_instr_patch_keeps_trace0_preprocess_identical, test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch | KILLED |
| M5 | condition_meaning_gate: lockskip の DefineSpec 削除 | 4 node: test_patch_define_inventory_matches_condition_gate_registry, test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches, test_compile_time_branch_selection_accepts_each_registry_macro[IZANAGI_BREAK_MOCC_LOCK_COVERAGE], test_v1_domain_and_claim_boundaries_are_exact | KILLED |
| M6 | lockskip patch: `#if` → `#ifdef` | 4 node: test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches, test_broken_mocc_lockskip_patch_guards_validation_lock, test_broken_mocc_patches_have_unique_production_condition_witnesses, test_compute_positive_control_json_is_all_pass_and_bound | KILLED |
| M8 | fixture m3: X 行削除 | test_mocc_x_fixture_routes_to_lock_coverage_indeterminate | KILLED |
| M9 | driver: CHECK_KEYS から 1 key 削除 | 3 node: test_compute_positive_control_json_is_all_pass_and_bound, test_driver_check_keys_are_exact, test_driver_compute_checks_is_input_derived_per_key | KILLED |
| M10 | driver: `_verify` の `--protocol mocc` 削除 | test_driver_verify_passes_mocc_protocol_and_given_root | KILLED |
| M11 | materializer_admission: mocc entry 削除 | test_python_ccbench_manual_materializers_are_explicitly_non_admissible; test_single_registry_has_typed_compatible_projections | KILLED |
| M12 | early patch: relock `w_lock()` を無効化 | test_broken_mocc_early_unlock_patch_unlocks_after_entry_and_relocks_before_publish; test_compute_positive_control_json_is_all_pass_and_bound | KILLED |
| M13 | fixture m4: P 行削除 | test_mocc_p_fixture_routes_to_permutation_indeterminate | KILLED |
| M14 | instr patch: 入口 counter 条件を `false` へ | test_compute_positive_control_json_is_all_pass_and_bound; test_instr_patch_names_cll_lock_pointer_predicate | KILLED |
| M15 | early patch: 裸 directive を 2 回出現させる | 4 node: test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches, test_broken_mocc_early_unlock_patch_unlocks_after_entry_and_relocks_before_publish, test_broken_mocc_patches_have_unique_production_condition_witnesses, test_compute_positive_control_json_is_all_pass_and_bound | KILLED |
| M16 | driver: `trace0_text_identical` を定数 True へ | test_driver_compute_checks_is_input_derived_per_key | KILLED |
| M17 | driver: `_resolve_toolchain` の不一致 raise を除去 | test_driver_resolve_toolchain_accepts_bound_versions_and_fails_closed | KILLED |
| M18 | instr patch: UPDATE 保持条件に `false &&` を前置 | test_compute_positive_control_json_is_all_pass_and_bound; test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch | KILLED |
| M19 | instr patch: `izanagi_cll_has_writer` 初期値を true へ | test_compute_positive_control_json_is_all_pass_and_bound; test_instr_patch_names_cll_lock_pointer_predicate | KILLED |
| M20 | instr patch: P emitter 条件に `false &&` を前置 | test_compute_positive_control_json_is_all_pass_and_bound; test_mocc_x_p_proof_surfaces_are_present_only_after_instr_patch | KILLED |

- M7 (B-3 allowlist 削除) は `test_p3_s4_loop.py` が 260 秒/走で重いため matrix 外。閉包は自走 harness で確認済み (冗長 gate、新規検出力に数えない)。
- patch を変異する件は JSON の sha 束縛により consumer node も併発赤になる。単一理由は主 node で判定し、consumer は冗長 gate として記録。
- probe 走 (全件 SURVIVED 期待、node 空) で観測 node を集め、final spec に KILLED 期待で登録して本走した (DW-M07)。

## 5. 一次資料

- 本 dir の同梱: `mutation-spec-final.json` (spec、観測 node 込み)、`mutation-ledger.json` (harness 本走の台帳)、
  `mutation-probe-login.json` (login probe の観測、M3 再照準後)、`s3_mocc_lock_coverage.compute-2.log` (compute 2 回目の dispatch log)。
- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2294-mocc-lock-instrumentation/` (brief、裁定 3 本、prompt 9 本、codex 出力 9 本、
  liveness / gate / compute / 変異の log と receipt、snapshot patch 4 本)。
- compute JSON `output/env/pegasus/calibration/s3_mocc_lock_coverage.json`、dispatch receipt `output/pegasus-dispatch/3fc180881d9a…/receipt.json`。
- 受入 receipt は本 commit を含む tip に対して走らせ、path `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2294-mocc-lock-instrumentation/acceptance-1-receipt.json` に置く (結果は worklog fragment の完了項と handoff に記録)。

## 6. scope 外 (裁定パッケージ、ユーザー判断)

- mocc trace pilot (`tools/pegasus/mocc_trace_pilot.sh`) へ計装 patch を重ねる経路 (T-2195 の面)。
- verifier core の P 説明文 (`orchestrator/verifier/parse.py`) の protocol 中立化 (本 wave は verifier 無編集)。
- gitlink の e9e477ca (+patch) への前進 (T-2295)。
- YCSB に DELETE が無いため DELETE 経路の検査点は build と静的読解のみ。
