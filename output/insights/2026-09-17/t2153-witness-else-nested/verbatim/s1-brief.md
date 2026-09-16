# 段 1 brief — [T-2153] 意味 witness を (a) 型 (`#else` + 入れ子) の 2 macro へ広げる

- 基準コミット: 1042a1bc95057fa03117d504cfa2b0fafaae60d0 (local main、着手時点)
- wave worktree (repo root): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-else-nested
- ユーザー依頼 (逐語): 「[T-2153] masstree config.h macro の意味 witness を 9/22 から増やす。残り 13 件の型 (a) #else + 入れ子 2 件、(b) 条件指令が別の条件指令の内側 1 件、(c) 条件指令が複数箇所に散る 3 件、(d) selector / template / 診断混在 4 件、(e) driver 配線が編集面を超える 2 件、(f) 同伴 define を gate が再注入 1 件のうち、既存機構で届く (a)(b)(c) から取る。正本は entry 1195 の持ち越し本文と同 wave の insight。T-2650 の prebuild 供給 (entry 1545) と official 床値の完走 (entry 1577) は着地済みなので前提に使う。Codex author (D95) + 変異事前登録。着手直前の local main から fresh worktree を作る。本題の witness 追加だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。規律 2 を緩めない。」

## 前提の実測 (親、brief 前)

- 現行 registry (`orchestrator/campaign/condition_meaning_gate.py`): 供給 domain `DEFINE_SPECS` = 38 macro (1195 当時 22)、意味確立 = 13 (枝選択 witness `CONDITIONAL_BRANCH_WITNESSES` 12 + 旧型 `BACKOFF_FIXED`)、未確立 25。依頼文の「9/22」は 1195 時点の数で stale だが、作業内容は変わらない。
- 既存機構の制約 (現物で確認):
  - `_instrument_declared_owner_source` (2924〜) は宣言した開始指令の逐語 (`rstrip("\r\n")` 一致) が所有 file に**ちょうど 1 回**あることを要求 (`compile-time-branch-start-not-unique`)。
  - probe は開始指令の行を「`<指令>` / `SELECTED()` / `#endif` / `COMPLETED()` / `<指令>` (元)」へ置換する。つまり元の枝の `#else`・入れ子は probe の評価に入らない。
  - `_assert_compile_time_branch_selection` (3133〜) は要求値と対照値 (`comparison = "1" if requested == "0" else default`) を **同じ route で `-D<MACRO>=<値>` として定義**して 2 回前処理し、`(選択, 完了)` が要求で `(1,1)`・対照で `(0,1)` のときだけ green。同一なら `not-discriminating` red、それ以外は `mismatch` red。
  - factory `declare_define_runtime_meaning` (954〜) は BACKOFF_NOINLINE 以外は要求 `"1"`・既定 `"0"`・`source_rel in spec.owner_tus` のときだけ宣言を返す。
- (a) 型 2 件 — **既存機構で届く**:
  - `IZANAGI_BREAK_NOREAD_VALIDATION`: `patches/broken-silo-norw-validation.patch` が `cc/silo/transaction.cc` の `validationPhase()` 内へ `#if IZANAGI_BREAK_NOREAD_VALIDATION` … `#else` / `#if ADD_ANALYSIS` … `#endif` … `#endif` を 1 箇所追加。stock の transaction.cc に同名 0 件。
  - `IZANAGI_BREAK_HIGHKEY_VALIDATION`: `patches/broken-silo-highkey-validation.patch` が同関数へ `#if IZANAGI_BREAK_HIGHKEY_VALIDATION` … (内側に `#if ADD_ANALYSIS`) … `#else` / `#if ADD_ANALYSIS` … `#endif` … `#endif` を 1 箇所追加。stock に 0 件。
- (b) `IZANAGI_BREAK_TRIGGER_MISATTR` — **届かない**: `#ifdef` (対照 `-D=0` でも定義済み → 両観測 (1,1) → not-discriminating red)、かつ `#if BACKOFF_TRIGGER_GATING` の内側 (既定 0 で COMPLETED も 0)。
- (c) 3 件 — **届かない**: `IZANAGI_SILO_LADDER_RUNG1` は transaction.cc に `#if IZANAGI_SILO_LADDER_RUNG1` ×2 (file scope と `lockWriteSet()`)、`BACKOFF_REQUESTED_US` は transaction.cc に ×2 (counter class と `abort()`)、`BACKOFF_TRIGGER_GATING` は ×12 (+ `#ifndef`)。いずれも一意性検査で `compile-time-branch-start-not-unique`。
- 要求 driver (git grep 実測): 両 macro を `DefineRequest` で要求する production 経路は `orchestrator/campaign/s2_verify_calibration.py::_require_condition_gate` (94〜125) だけ。requested 1 / default 0、`declaration=None` (109 行) → meaning arm は `unestablished`、`use_class="raw-measurement"` で admit。`screening_driver.py` (81〜82) は CCBENCH_ 名前空間 route の既定 0 で admission 前拒否 (D1492 により配線しない)。`tools/pegasus/probes/t2187_adaptive_const_probe.py` (3849) は静的 fixture の provenance 記述のみ。
- pin 閉包: gate file の sha256 (`9fef1f9c…`) は `output/env/pegasus/t316-sandbox-backend/*/receipt.json` の runtime 記録と insight verbatim にだけ現れる (live 比較 pin ではない)。S2 driver の sha256 pin 0 件。registry 会員の pin は `orchestrator/tests/test_condition_meaning_gate.py` の `_COMPILE_TIME_BRANCH_MACROS` (32〜45)、`test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` (972)、`test_v1_domain_and_claim_boundaries_are_exact` (2585、`MEANING_SUPPORTED_MACROS == {"BACKOFF_FIXED", *_COMPILE_TIME_BRANCH_MACROS}`、route 件数 22/16 は DefineSpec 不変なので不変)、`orchestrator/tests/test_s5_permutation_coverage.py::test_condition_preflight_dominates_first_benchmark_build` (86〜91、`if module in {s3, coverage}` で s2 を factory 検査から除外中)。`acceptance_duration_ledger.json` の未登録 node は fail-soft (unknown)。
- 後続裁定: D1613 以後に枝選択 witness の機構を変える D なし (D2087 まで実測)。T-2153 を止める裁定なし。

## brief

- **研究前進**: 論文の「条件付き build の意味を機械が確立する」節 (D1198 の供給 + 意味の二節) の被覆率。S2 検証較正 (verifier の positive control 2 本) の admission が `unestablished_meaning_macros` 非空のまま `raw-measurement` を通っている状態を witness green で閉じる。完了判定 = (i) registry 2 件追加 + S2 配線で、S2 の admission の未確立一覧が 2 件縮む (単体 test で factory 宣言が S2 経路へ渡ることを pin)、(ii) 実 compiler で (a) 型の所有 TU 形 (`#if X … #else #if ADD_ANALYSIS … #endif … #endif`) が要求 1 → (1,1)・既定 0 → (0,1) の green、(iii) 変異 matrix が baseline 緑・負例 KILLED。
- **scope**: `condition_meaning_gate.py` の `_CONDITIONAL_BRANCH_WITNESSES` へ 2 entry。`s2_verify_calibration.py::_require_condition_gate` の `declaration=None` → `declare_define_runtime_meaning(request)`。`test_condition_meaning_gate.py` (`_COMPILE_TIME_BRANCH_MACROS` 追加、(a) 型 owner_text の正例 1 本)。`test_s5_permutation_coverage.py` の factory 検査へ s2 を含める。**scope 外**: (b)(c)(d)(e)(f) の機構変更、新 gate・検査・台帳・一般化、旧 `MeaningWitnessDeclaration` / CLI (D1491 で BACKOFF_FIXED 固定)、既存 8+3+1 macro の期待式、S2 の supply arm の評価経路 (configure 引数)。
- **確定済み裁定**: D1490 (witness の型・主張範囲)、D1491 (集合拡張が旧受理面を広げない — 新 witness は factory 以外から発行不可のまま)、D1492 (配線は未確立一覧が実際に縮む driver だけ = S2 のみ)、D1613 (対照値方式は BACKOFF_NOINLINE 限定、既存 macro の要求 1・既定 0 は不変)、D95 (Codex author)、規律 2 (受理集合は狭まる向きだけ: unestablished(admit) → green(admit) or red(reject))。
- **不変条件**: (I1) 既存 12 witness + BACKOFF_FIXED の factory 条件・期待式・evidence schema を変えない。(I2) 旧宣言型と CLI は BACKOFF_FIXED 固定のまま。(I3) 一意性検査・非識別検査・完了 marker 要求を緩めない。(I4) S2 の supply arm の評価経路 (configure 引数) を変えない。(I5) `screening_driver` 等の非要求 driver へは配線しない (D1492)。(I6) `DEFINE_SPECS` (供給 domain) を変えない。
- **成果物の形**: コード + テスト (Codex author)、変異 matrix (事前登録)、insight `output/insights/2026-09-17/t2153-witness-else-nested/README.md` (届かない 4 件の理由を実測付きで再記録)、spool fragment (worklog)。
- **並列分割**: 実装子 1 本 (registry + driver + tests は密結合で小さい)。段 6 レビュー 2 本 (レンズ A: witness の健全性 = (a) 型の実 TU で false-green / false-red が出る入力があるか; レンズ B: 受理集合と配線 = D1491/D1492 逸脱、S2 経路の consumer 取り残し、pin 閉包)。
- **受入・実測環境**: login node で pytest 焦点走 (実 compiler を要する test は `_any_cxx` で解決)、変異 matrix は container worktree、受入全走は `tools/dev_wave_wait.py acceptance`。計算ノード実走は不要 (S2 driver 自体の実機再走は本 wave の完了判定に含めない — witness は login の実 compiler で生死確認できる)。
- **(P1) 攻撃対象 provisional 裁定**:
  - (P1-a) (a) 型 2 macro は既存機構の変更ゼロで green になる。根拠: probe 塊は指令の直前に自己完結で挿入され、元の枝の `#else` / 入れ子は評価に入らない。反証は「実 patch 適用後の transaction.cc 形で (1,1)/(0,1) が出ない入力」。
  - (P1-b) 配線先は S2 だけで足りる。根拠: 両 macro を DefineRequest で要求する production 経路は `s2_verify_calibration._require_condition_gate` のみ。
  - (P1-c) (b)(c) の 4 件は既存機構で届かず、機構変更は本 wave の scope 外 (ユーザー指示「本題の witness 追加だけ」)。plan 子がこれを反証するなら (例: 逐語が実は一意) 段 4 で再裁定する。
  - (P1-d) S2 の meaning arm は `configured_commands` 無しの 2 configure 形のまま (S3 の `_configured_define_compile_commands` 形へ揃えるのは効率化であり scope 外)。
- **模擬 / 実の差**: 単体 test は toy owner TU + fixture build (`condition_gate_test_support.install_condition_gate_build_fixture`) で実 compiler を叩く。実 patch 適用後の CCBench TU (masstree `config.h` 依存) での S2 実走は本 wave で行わない。この差は insight に明記する。
- **既存被覆 (純増)**: 1195 が 8 件、T-2294 (commit 71795fb05) が mocc 3 件、D1569/D1613 が BACKOFF_NOINLINE を追加済み。本 wave の純増 = (a) 型 2 件 + S2 配線 + (a) 型の実 compiler 正例。
- **DW-G05 成果物影響**: 放置時、S2 検証較正の admission は `unestablished_meaning_macros` = {NOREAD} / {HIGHKEY} のまま `raw-measurement` を通り続ける。採用時、同一覧が空になる (green) か、枝が選ばれていなければ red で S2 が build 前に止まる。certified 選択・レポート・台帳の値は変わらない (S2 は較正 driver)。

## 変更面 (実アンカー表、wave worktree の行番号)

| file | anchor | 変更 |
|---|---|---|
| `orchestrator/campaign/condition_meaning_gate.py` | 245 `_CONDITIONAL_BRANCH_WITNESSES = {` … 279 `"IZANAGI_BREAK_WRITE_INTENT_PTRSWAP": (` … 283 `CONDITIONAL_BRANCH_WITNESSES: Mapping` | 2 entry 追加 (`cc/silo/transaction.cc`, `#if IZANAGI_BREAK_NOREAD_VALIDATION` / `#if IZANAGI_BREAK_HIGHKEY_VALIDATION`) |
| `orchestrator/campaign/s2_verify_calibration.py` | 94 `def _require_condition_gate` / 109 `declaration=None` | `declaration=condition_meaning_gate.declare_define_runtime_meaning(request)` |
| `orchestrator/tests/test_condition_meaning_gate.py` | 32〜45 `_COMPILE_TIME_BRANCH_MACROS`; 217 `_compile_time_source_root(… owner_text=…)`; 253 `_patch_added_branch_declaration`; 972 registry 束縛 test; 1196 各 registry macro の受理 test (parametrize); 1320 `accepts_active_nested_context`; 2585 `test_v1_domain_and_claim_boundaries_are_exact` | tuple へ 2 macro 追加、(a) 型 owner_text (`#else` + 入れ子 `#if ADD_ANALYSIS`) の正例 test 追加 |
| `orchestrator/tests/test_s5_permutation_coverage.py` | 86 `test_condition_preflight_dominates_first_benchmark_build` / 89 `if module in {s3, coverage}` | s2 を factory 検査に含める |
| `orchestrator/tests/condition_gate_test_support.py` | 145 `install_condition_gate_build_fixture(root, define_spec=…)` | 変更なし (読むだけ) |

file サイズ: `condition_meaning_gate.py` 4387 行 / 181,689 bytes、`test_condition_meaning_gate.py` 2939 行 / 106,630 bytes、`s2_verify_calibration.py` 471 行、`test_s5_permutation_coverage.py` 132 行、`condition_gate_test_support.py` 209 行。
