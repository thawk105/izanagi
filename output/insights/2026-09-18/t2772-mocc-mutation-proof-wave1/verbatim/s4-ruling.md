# 段 4 裁定 — [T-2772] mocc 実証 wave 1 (2026-09-18、親)

所見の判定は real / refuted、採否は採用 / 不採用、scope 内 / 外。plan v2 = 段 2 plan + 本裁定の差分。

## R1. P3 (観測のみ t4 負例の integrity 免除) — 親の根拠は refuted、対象集合を D2134 項 5 で固定 (must-fix、採用)

- 親 brief の「cycle 3,754 が出たので integrity clean を要求すると恒偽」は **refuted** (レンズ A 所見 1、B 所見 7: cycle と integrity は別軸、旧 JSON に version_dups の値は無い)。撤回する。
- しかし plan の「全 36 走に別 integrity clean を要求する共通 check」は**採用しない**。根拠 = (a) D2134 項 5 と T-2772 起票文「受入必須の走だけを check に対応」、(b) レンズ A 所見 1 の具体順序: hot-update/t4 と lockskip/t4 では lock を故意に欠いた 2 worker が同じ版を読んで同じ maxtid を選び、balanced のまま `version_dups` を出しうる (発生頻度は不確実)。これは負例の許容挙動であり実証の欠陥ではない。
- **裁定:** 実証の `all_pass` と各走の `certified` を分離する。`certified` は verifier の値をそのまま記録し、上書きしない。
  - `matrix_runs_complete_and_terminated` は **36 走すべて**に、存在・予定 cell との一致・実 argv・`terminated`・`returncode==0`・`timed_out==false`・verifier の完了 (`terminated`、`timed_out==false`、rc∈{0,1,3}、record 実在) を要求する (hang・欠落は区分を問わず赤 = 設計 §7 のこの部分は維持)。
  - 別 integrity 異常 (旧 `_verify` の 10 項目: orphan_reads / version_dups / dup_txids / genesis_commits / missing_txids / write_version_mismatch / malformed_keys / framing_violations / framing_violation_details / write_intent_violations) の clean を要求するのは次の走だけ: stock 12 走と hot-update cold/default 4 走 (certified を要求するので含意)、および **1 thread の受入必須負例 7 走** (lockskip cold/default t1、perm hot/cold t1、early hot/cold t1、hot-update hot t1: 単一 thread では重複版が構造的に起きないので実質検査になる)。
  - lockskip cold/default **t4** の 2 走 (受入必須) は設計 §7 の述語どおり X>0、P=0、certified=false、txns/write>0 だけ (C>0 なら N、C=0 なら I)。integrity は raw record に残し、check にしない。
  - 観測のみ 11 走は raw record と要約値を記録し、存在・完走以外の check を置かない。
  - 設計 §7 の「別 integrity 異常は区分を問わず赤」は上の形へ限定する。理由と対象集合は decisions fragment に書く。規律 2 は緩めない (壊れた variant を certified にする経路は無い)。
- 共通 check `all_runs_other_integrity_clean` は置かない。check は設計 §7 の候補 32 key を exact とする。

## R2. P1 (helper の import 再利用) — 一部修正 (real、採用)

- 再利用 (import、旧 module 無変更): `PIN`, `SOURCE_REL`, `STOCK_G`, `SINGLE_FLAGS`, `HIGH_FLAGS` (copy して使う), 旧 patch 定数 4 つ, `_sha256_file`, `_run_checked`, `_load_policy`, `_resolve_toolchain`, `_prepare_dependencies` (→ `_install_dependency` は旧 module の登録のまま), `_common_configure_args`, `_apply_owned_patch`, `_trace0_record` (補助 witness として)。
- 新 driver 側に置く: `_require_condition_gate` (driver_id = `orchestrator.campaign.s3_mocc_mutation_proof`)、`_build_variant` (新 materializer 登録)、`_run_trace` (唯一の新規直接 subprocess site。実 argv・`returncode`・`timed_out`・`terminated`・`error` を返し例外にしない)、`_verify` (旧 `_run_checked(..., timeout=900, allowed_returncodes={0,1,3})` を呼び、`RuntimeError.__cause__` が `subprocess.TimeoutExpired` なら `timed_out=True` として record に残す。raw `results[0]` を `verifier.record` に保存)、`_trace_counts` の新版 (`read_rows` を加える。旧関数を呼んで R 行を別途数えてもよい)、D1687 の論理行列比較 (`trace0_logical_rows_identical` の入力。`g++ -E -DTRACE=0 …` の呼出は旧 `_run_checked` 経由)、`_variant_run`、matrix、`compute_checks`、`main`。
- 新 `main` は依存準備・build より前に `site_policy.current_site(require_evidence=True)`、`refuses_heavy_work` による拒否 (rc=2)、`_assert_single_tenant()`、`--third-party-cache` 絶対 path 必須を行い、各 benchmark 直前にも `_assert_single_tenant()` を呼ぶ (レンズ B 所見 5、must-fix、採用)。

## R3. P2 (負例 patch の形) — plan の逐語案を採用 (real、採用)

- file scope: `#if IZANAGI_BREAK_MOCC_HOT_UPDATE_UNLOCK` / `#else` / `#endif` の 1 組、両腕に `[[maybe_unused]] static constexpr bool izanagi_break_mocc_hot_update_unlock = TRACE != 0;` (ON) / `= false;` (OFF) と `[[maybe_unused]] static thread_local Tuple* izanagi_hot_update_pending = nullptr;` を宣言、直後に `#line 17`。
- site 1 `update()` (論理行 459 の 1 行を block 化): `lock(tuple, true)` の直後、`status_ != aborted && pending == nullptr` のときだけ `tuple->rwlock_.w_unlock(); pending = tuple;`。block 後に `#line 460`。stock 枝 (macro=0) では同じ `lock(tuple, true)` を 1 回呼び、後続の `status_` 判定は元の位置 (460〜464) のまま。
- site 2 `writePhase()`: `"lock-lost-before-publish"` の `#if TRACE` block と既存 `#line 1195` の**後**、`__atomic_store_n` の**前**に `if (pending == (*itr).rcdptr_) { pending->rwlock_.w_lock(); pending = nullptr; }`、後に `#line 1195`。
- site 3 `abort()`: `unlockCLL();` (論理行 1069) の前に `if (pending != nullptr) { pending->rwlock_.w_lock(); pending = nullptr; }`、後に `#line 1069`。
- 3 site は `if constexpr (izanagi_break_mocc_hot_update_unlock)`。`TxExecutor::lock()` は使わない。計装 patch の `#line` 7 箇所は不変。touch set = `cc/mocc/transaction.cc` のみ。preimage = e9e477ca + `instr-mocc-lock-coverage.patch`。
- TRACE 隔離の実測 (レンズ A 所見 6、should、採用): 親の login 生死確認に **macro=1・TRACE=0** の build を加え、無 patch base-t0 と `.text` 一致・nm/strings 0 を見る (macro=0・TRACE=0 と併せて 2 組)。

## R4. check 集合 (P5) — 32 key exact (採用)

設計 §7 の候補名をそのまま採る: `stock_{hot,cold,default}_{t1,t4}_certified_and_silent` (6)、`stock_u_{hot,cold,default}_{t1,t4}_certified_and_silent` (6、+ `read_rows == 0` と `non_insert_writes == txns`)、`{cold,default}_lockskip_t1_three_reasons_cycles_zero` (2)、`{cold,default}_lockskip_t4_x_positive` (2)、`perm_{hot,cold}_t1_only_size_changed` (2)、`early_unlock_{hot,cold}_t1_retention_without_entry` (2)、`hot_update_unlock_hot_t1_three_reasons_cycles_zero` (1、+ `read_rows == 0`、`non_insert_writes == txns`)、`hot_update_unlock_{cold,default}_{t1,t4}_silent` (4、stock-U 型)、`matrix_runs_complete_and_terminated`、`hot_path_evidence_method_is_negative_control` (入力 `hot_path_evidence` の `method == "negative-control"` と `guarantee` の exact)、`trace0_nm_izanagi_zero`、`trace0_strings_izanagi_trace_zero`、`trace0_logical_rows_identical`、`toolchain_matches_policy`、`all_broken_patch_touch_sets_are_transaction_only` (負例 4 本の集合 exact、各 `[SOURCE_REL]`)。`compute_checks(runs, trace0, touch_sets, patch_relatives, toolchain, policy, *, hot_path_evidence)` で入力由来。`all_pass` = 32 key 全 true かつ 36 走揃い。

保証名の exact 文字列は設計 §6 の逐語「stock 等価述語における hot-update 負例の到達と、既存 X 3 検査点の検出」に固定する (D2134 項 4 との読点差は意味同一、decisions fragment に注記)。

## R5. JSON の形 — plan §5 から次を削る (レンズ B 所見 4、採用)

- `legacy_proof` は旧 JSON の repo 相対 path と sha256 だけ (14 check の写しは持たない)。
- run record の `integrity` は `verifier.record.integrity` の 1 箇所だけ (top-level 重複を持たない)。要約値 (`verdict`, `certified`, `total_cycles`, `txns`, `lock_coverage_violations`, `permutation_violations`) は record から抽出し、consumer test が raw との一致を検査する。
- `n1_*`、`template`、resume・分割・統合の機構は持たない。
- atomic 保存 (同 dir の一時 file → `os.replace`) は benchmark 後と verifier 後の 2 点。途中 JSON の `all_pass` は false、`complete` は持たず `runs` の欠落で表す。

## R6. 時間予算 (P6/P7) — 初回設定として採用、確度は明記 (採用)

`RUN_TIMEOUT_S=120`、`VERIFIER_TIMEOUT_S=900`、gen_S 1 job。20〜25 分は未検証の見積であり 3600 秒内の保証ではない (レンズ A 所見 7、B 所見 6)。Elapse kill は run timeout の観測に置き換えない。不足が初回で判明したときだけ `--regime` と別 `--out` の最小分割を fix で入れる。

## R7. 登録簿閉包 — レンズ B 所見 1 の件数 pin を加える (must-fix、採用)

plan §8 の逐語に加え: `test_condition_meaning_gate.py:2782` の CXX_FLAGS route 数 16→17、`condition_meaning_gate.py:12〜15` の module docstring と `test_condition_meaning_gate.py:2901〜2904` の文字列 pin (供給 39 / compile-time witness 15 — **現物を AST で数えて確定**、既存の「12 total」不整合をそのまま +1 しない)、`test_ccbench_spawn_sites.py:3466` `proven-unreachable` 34→35、`:3469` `covered` 38→39、`:3493` と `:3502` の `proven-unreachable` 24→25 (静的予測。実走で確定し、違えば現物に合わせる)。新 module の登録は `_run_trace` 1 site のみ (旧 `_run_checked` / `_install_dependency` の再登録はしない)。`_DEFERRED_GATE_MEMBERS` の lineno は触らない。旧 `test_mocc_proof_surface.py` の 14 check / 4 patch / 3 witness の固定集合は変更しない (レンズ B 所見 3)。

## R8. test node — plan §7 の 11 node を採用。JSON consumer の compute 前の扱い (採用)

compute 前の焦点走では `test_mocc_mutation_proof_json_is_complete_and_bound` を `--deselect` で明示除外し、除外を handoff に記録する。skip 化・仮 JSON・空 all_pass は禁止。compute 後は除外なしで焦点走 → 受入全走。

## R9. 段 5 の分割 — author 1 本、wave worktree 内 (採用)

patch・driver・test・登録簿 (production 3 file、test 4 file) を 1 子で。`patches/README.md` は親が author 完了後に書く。author 稼働中、親は worktree へ書かず dispatch もしない。

## R10. 変異事前登録 (DW-M01、段 6 で走らせる。期待 node は probe 走で実測して final spec に固定)

| # | 対象 / 変異 | 期待 |
|---|---|---|
| M0 | driver の comment 1 行を等価な文言へ (等価変異、harness の SURVIVED 検出の正例) | SURVIVED |
| M1 | patch: publish 側 relock block を削除 | KILLED |
| M2 | patch: abort 側 relock block を削除 | KILLED |
| M3 | patch: relock を `lock(izanagi_hot_update_pending, true)` へ | KILLED |
| M4 | patch: publish 側 relock を `"lock-lost-before-publish"` 検査より前へ移動 | KILLED |
| M5 | patch: 裸 directive を 2 箇所へ複製 | KILLED |
| M6 | patch: `#line 460` → `#line 461` | KILLED |
| M7 | driver: `hot_update_unlock_hot_t1_three_reasons_cycles_zero` を定数 True | KILLED |
| M8 | driver: `_run_trace` の `timed_out` を常に False | KILLED |
| M9 | `condition_meaning_gate.py` の新 DefineSpec entry を削除 | KILLED |
| M10 | `materializer_admission.py` の新 entry を削除 | KILLED |
| M11 | JSON: 新 patch の sha256 を 1 文字変更 | KILLED |
| M12 | JSON: `all_pass` を false へ (consumer が再計算・束縛するか) | KILLED |

patch 変異 (M1〜M6) は JSON の sha 束縛でも consumer が赤になるが、それは冗長 gate として記録し検出力に数えない (T-2294 と同じ)。hang_risk の変異は無い。

## R11. 親 brief の訂正

- §3 は「未確定 6 件の現状整理」: 型・U の操作・温度 0 維持は静的確認済み、hang は compute 未確認、§3.2 (a) は別 wave。
- anchor: `_DIRECT_SAFE_ALLOWLIST` は `test_ccbench_spawn_sites.py:45`、`allowed_non_variant_tokens` は `test_p3_s4_loop.py:7867`、旧 `_verify` は `s3_mocc_lock_coverage.py:387`〜、`_variant_run` :417〜、`_apply_owned_patch` :430〜。
- 「R 行 0」は `read_rows` を直接数える (`non_insert_writes == txns` だけでは示せない)。
- 受入必須は matrix 表の 25 走で列挙し「t1 負例」等の略記で再定義しない。

## R12. 段 3 所見の real / refuted 一覧

レンズ A: 1 real must-fix (採用、R1)、2 温度反例 refuted / 実走証拠 real should (採用、R11)、3 refuted (論証を README へ)、4 一般化 real should (採用、限定を README に)、5 恒真疑義 refuted / 集合記述 real (採用、R11)、6 real should (採用、R3)、7 保証名 refuted / 予算 real should (採用、R6)、8 real nit (採用、R11)。
レンズ B: 1 real must-fix (採用、R7)、2 過剰登録 refuted (採用 = 登録しない)、3 refuted (旧 test 不変)、4 一部 real should (採用、R5)、5 real must-fix (採用、R2)、6 real should (採用、R8)、7 real (採用、R1/R11)。
refuted のうち親が不採用にしたものは無い (scope 外の real 所見も無し)。
