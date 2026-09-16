# 段 4 裁定 (親、2026-09-17 01:10 JST) — [T-2153] (a) 型 2 macro の意味 witness

略号: G = `orchestrator/campaign/condition_meaning_gate.py`、S2 = `orchestrator/campaign/s2_verify_calibration.py`、TG = `orchestrator/tests/test_condition_meaning_gate.py`、T5 = `orchestrator/tests/test_s5_permutation_coverage.py`。行番号は変更前 (base 1042a1bc9)。

## §1 所見の裁定 (real / refuted、採用 / 不採用)

### 段 2 plan の補正 (採用)
- **TG:1488 `test_compile_time_factory_keeps_unregistered_macro_unestablished` が NOREAD を未登録 macro として使う** → real、採用。`IZANAGI_BREAK_TRIGGER_MISATTR` へ差し替える (期待値 `None` / `unestablished`・`meaning-witness-undeclared` は維持)。
- **registry 追加で 2 macro が供給側の共有 build root 分岐 (G:1879〜1888、G:2499〜2504) に入る** → real、採用 (brief 訂正)。I4 は「S2 の supply 呼出しと configure 引数は不変」の意味で維持。内部の一時 root 配置と evidence 内 command は既存 8+3 CXX_FLAGS macro と同形へ変わる。
- **S2 consumer test (S5 の monkeypatch 型と同形) の追加** → 採用。仕様は §4-2。

### レンズ A (正しさ境界と検出力)
- A1 real 採用: P1-a を「所有 TU の前処理が成功する場合、元の `#else` / 入れ子は marker の選択条件に入らない」に限定して記録する。
- A2 refuted (現 pin で false-green/red の位置は無い)、A3 refuted (一意性は stock 0 件 + S2 の個別 `applied` + `assert_pinned_clean` で根拠あり)、A4 refuted (生死実験の形は忠実。呼び名は「実 patch の前処理構造を模した toy TU」に統一)。
- A5 refuted: S2 後段 (`gate3` / `all_pass`) は witness green を読まない。主張は「枝選択確立」と「positive control の実走成功」を分けて書く。
- A6 real 採用: 受理集合の説明を **meaning arm 単独 (unestablished → green/red、狭まる向きだけ)** と **family 全体 (supply 側の実行形が共有 root へ変わる)** に分ける。A7 plausible (共有 root の cache 残留で supply red → green): 新機構は足さず、既存の供給回帰 (TG の共有 command 群) と受入全走で確認した範囲を記録する。A8 refuted (集合所属だけで green にはならない)。A9 real 採用 (「挙動不変」は factory / meaning の状態に限定)。
- A10 real 採用: **`source_rel` 変異は登録しない** (TG:232 の helper assert が factory より先に赤を出し、単一理由性が無い、DW-M01)。A11 real 採用: S2 配線変異の主 killer は新 consumer node と明記。A12 real 採用: 既存被覆の変異 3 件は「既存被覆」と別記。
- A13 real 採用: (b)(c) の証拠は「toy 実測 + 実 patch の静的対応付け」と書く (MISATTR は外側条件が有効なら (1,1)/(1,1)、無効なら (0,0)/(0,0))。
- A14 real 採用: CLI 自動追随 (G:4163 / 4181 / 4196) を影響範囲に追記。I2 は「旧宣言型と CLI の `--meaning-case` 経路は BACKOFF_FIXED 固定」へ訂正。
- A15 real 採用 (TG:1488 漏れ、行番号 nit)。A16 real 採用: 完了判定を分ける (§3)。A17 plausible: masstree `config.h` は未検証事項として維持、実機成功を報告しない。
- 裁定パッケージ候補 (新 gate / 一般機構): 留保。本 wave では出さない。

### レンズ B (整合と実効性)
- B1 real 採用: 「両 macro を要求する production 経路は S2 だけ」→「**追加配線が必要な専用 driver は S2。CLI は既配線 (factory 自動)、screening は route 不一致で admission 前拒否**」。B2 real 採用: screening の拒否理由は `screening-build-route-mismatch` (裸 `-D` 不在) であって既定 0 ではない。
- B3 real 採用: 縮小の観測箇所 = `output/env/linux-baremetal/calibration/s2_verify_<…>.json → condition_gates[i].admission.unestablished_meaning_macros` (保存されるのは preflight の結果、`_broken_build_and_verify` の再検査結果は捨てられる S2:309)。機械 consumer は検索範囲で未発見。
- B4 real 採用: 現行 gate 下で S2 が実機で走った証拠は無い (最終走行 2026-07-06、`condition_gates` を持たない JSON)。brief の「通っている状態」→「供給が green なら未確立を許容するコード上の状態」。
- B5 plausible: masstree `config.h` は supply にも共通の実行上の懸念 (S2 は依存供給先を渡さない、S2 PIN `dff0f1e` でも build 時生成)。未検証事項として記録、toy の成功を実機 admission へ読み替えない。
- B6 plausible 採用 (表現): P1-d は「既存の独立 configure 経路を維持し、供給 / 意味間の共有 command の保証は主張しない」。S3 形への変更は必須化しない。
- B7 real 採用 (A6 と同じ)。
- B8 real 採用: consumer test は **実 factory を包む spy** が (request, 返却 object) を保存し、evaluator stub で `kwargs["request"] is request` と `kwargs["declaration"] is spy_return` の両方を検査する。capture stub は `configure_args` に `-DCCBENCH_TRACE=1` を含むことと、両 evaluator へ同じ captured object が渡ることも検査する。
- B9 real 採用: stub consumer の主張は「factory 戻り値の伝達と admission 結果の転送」に限定。実 family の一覧縮小は toy fixture 上の実 evaluator + 実 family で示す (§4-1 の正例に `require_condition_gate_family` まで通す)。
- B10 refuted (HIGHKEY の `+#if ADD_ANALYSIS` は束縛 helper を乱さない)。B11 real 採用 (TG:1488)。B12 refuted (literal 件数 pin なし。旧 insight・過去 receipt は書き換えない)。
- B13 real 採用: 件数は「意味 witness 対応集合 13、未対応 25。1195 の残り 13 件のうち現在未対応 12 件、本 wave 後 10 件」。B14 real 採用 (I2 の訂正、期待組は今回の要求 1 / 既定 0 に限る)。B15 refuted ((c) は 2・2・12 で完全一致、逃げ道なし)。B16 refuted (アンカーは一致)。
- B17 refuted: (a) への絞り込みは機構上の拒否 (一意性・所有 TU・`#ifdef` の非識別) を主根拠にする。依頼の「(a)(b)(c) から取る」を「全型から 1 件ずつ」とは読まない。
- B18 (裁定候補: 完了主張の範囲) → **親が決める (運用系、可逆)**: 本 wave の完了は registry + S2 配線 + toy 生死確認 + toy fixture 上の実 family 規則まで。実機 S2 走行による JSON の縮小は**未検証**と insight / worklog に明記し、持ち越し (S2 を現行 gate 下で実機再走する件は T-2153 の carry に「未確認事項」として書く)。理由: ユーザー指示「本題の witness 追加だけ」、S2 の実機再走は condition gate 導入後 1 度も無く依存供給の設計 (D2059 と同型) を伴う別変更単位。

## §2 scope (確定)

- 変更 file は 4 つに固定: G、S2、TG、T5。他の file (`DEFINE_SPECS`、`screening_driver`、docs、`acceptance_duration_ledger.json`、`patches/**`、`output/**`) は触らない。
- 機構変更なし。(b)(c)(d)(e)(f) は本 wave の対象外。

## §3 完了判定 (訂正版)

1. registry に 2 entry、`_COMPILE_TIME_BRANCH_MACROS` に同順で 2 macro、TG:1488 の差し替え、T5 の s2 追加、S2 配線、S2 consumer test、(a) 型正例 — すべて Codex author が書き、親が焦点走で緑を実測。
2. (a) 型正例は toy fixture 上で **実 supply + 実 meaning + 実 family** を通し、`admitted is True` かつ `unestablished_meaning_macros == ()` を要求する (要求 1 → (1,1)、既定 0 → (0,1))。
3. 変異 matrix: baseline 緑、§5 の負例が期待 node で KILLED、等価変異 M0 が SURVIVED。
4. 実機 S2 走行による JSON の縮小は本 wave の完了判定に**含めない** (未検証として記録)。

## §4 plan v2 (実装仕様)

### §4-1 G / TG
- G:281 の `IZANAGI_BREAK_WRITE_INTENT_PTRSWAP` entry の直後に、次の順で 2 entry を追加:
  `"IZANAGI_BREAK_NOREAD_VALIDATION": ("cc/silo/transaction.cc", "#if IZANAGI_BREAK_NOREAD_VALIDATION")`、
  `"IZANAGI_BREAK_HIGHKEY_VALIDATION": ("cc/silo/transaction.cc", "#if IZANAGI_BREAK_HIGHKEY_VALIDATION")`。
- TG:44 の後に同順で 2 macro を追加 (TG:975 は tuple 等値なので順序一致が必須)。
- TG:1488 の `_compile_time_request("IZANAGI_BREAK_NOREAD_VALIDATION")` を `"IZANAGI_BREAK_TRIGGER_MISATTR"` へ。期待値は不変。
- 新 test (TG:1337 付近、`accepts_active_nested_context` の後): `test_compile_time_branch_selection_accepts_else_with_nested_analysis`、2 macro で parametrize。`owner_text` は実 patch の前処理構造を模す:
  - NOREAD: `#if M` / 本文 / `#else` / `#if ADD_ANALYSIS` / 本文 / `#endif` / 本文 / `#endif` (関数と `if (...) {` の内側に置く)。
  - HIGHKEY: `#if M` / 本文 / `if (...) {` / `#if ADD_ANALYSIS` / 本文 / `#endif` / 本文 / `}` / `#else` / `#if ADD_ANALYSIS` / 本文 / `#endif` / 本文 / `#endif`。
  - 実 `capture_define_inputs`、実 factory、実 `evaluate_define_supply_effectuation` (configured_commands 無し、S2 と同形)、実 `evaluate_define_runtime_meaning` (同)、実 `require_condition_gate_family(use_class="raw-measurement")`。
  - assert: supply `("green", "requested-default-preprocess-different")`、meaning `("green", "declared-compile-time-branch-selection-observed")`、requested (1,1)・default (0,1)、define_value "1"/"0"、`admission.admitted is True`、`admission.unestablished_meaning_macros == ()`。
  - `ADD_ANALYSIS` は fixture で未定義 (0 と評価)。この test は「ADD_ANALYSIS 未定義の正例」であり ADD_ANALYSIS=1 の実測とは記録しない。両枝の本文を異なる識別子にして supply の前処理 bytes が要求 / 既定で異なるようにする。
- TG:2585 の domain test は式の変更不要 (route 22/16 不変)。

### §4-2 S2 / T5
- S2:109 `declaration=None` → `declaration=condition_meaning_gate.declare_define_runtime_meaning(request)`。他は不変 (`configured_commands` は渡さない)。
- T5:89 `if module in {s3, coverage}:` → `{s2, s3, coverage}`。
- T5 に S2 consumer test を追加 (`test_condition_gate_rejection_stops_s5_before_build` の後、2 macro で parametrize、admit / reject の 2 分岐):
  - `capture_define_inputs` を stub: `configure_args` kwarg に `"-DCCBENCH_TRACE=1"` が含まれることを assert し、sentinel `captured` を返す。
  - `make_define_request` は実物 (request は `DefineRequest`)。
  - `declare_define_runtime_meaning` は実 factory を包む spy: 呼ばれた request と返却 object を記録して返す。
  - `evaluate_define_supply_effectuation` stub: 第 1 引数 (captured) が sentinel、`request` が同一 object であることを assert。
  - `evaluate_define_runtime_meaning` stub: `kwargs["request"] is request`、`kwargs["declaration"] is spy_return`、captured が sentinel を assert。
  - `require_condition_gate_family` stub: supply / meaning の両 record と `use_class="raw-measurement"` を受けることを assert し、admit 分岐では `admitted=True` を返す → 返却 dict に supply / meaning / admission の canonical JSON が載ることを assert。reject 分岐では `admitted=False` → `RuntimeError` (reason code 文字列を含む) を assert。
  - spy_return が `ConditionalBranchMeaningDeclaration` で、macro・`source_rel == "cc/silo/transaction.cc"`・`start_directive == f"#if {macro}"` を assert。
  - compiler 呼出しは 0。

### §4-3 書かない物
- `DEFINE_SPECS`、旧 `MeaningWitnessDeclaration` / CLI、一意性検査、非識別検査、完了 marker 要求、factory の要求 1 / 既定 0 条件、`screening_driver`、docs、台帳。
- (b)(c) へ届かせる機構、S3 形 (`_configured_define_compile_commands`) への S2 の変更。

## §5 変異事前登録 (production 側だけ、DW-M01)

| # | 対象 | 変異 | 期待 KILLED (主 killer → 補助) | 被覆の由来 |
|---|---|---|---|---|
| M0 | G registry 直前の comment | comment 行を 1 行追加 (等価) | SURVIVED 期待 | 対照 |
| M1 | G の NOREAD entry の指令逐語 | 末尾に `_X` を付ける | `TG::…accepts_each_registry_macro[IZANAGI_BREAK_NOREAD_VALIDATION]`、`TG::…accepts_else_with_nested_analysis[IZANAGI_BREAK_NOREAD_VALIDATION]`、`TG::…registry_and_fixtures_are_bound_to_real_patches` | 既存 test の対象拡張 + 新規 |
| M2 | G の HIGHKEY entry の指令逐語 | 同上 | 同型の HIGHKEY node 3 つ | 同上 |
| M3 | S2:109 の配線 | `declaration=None` へ戻す | `T5::<新 S2 consumer>[…]` (主)、`T5::test_condition_preflight_dominates_first_benchmark_build[…s2_verify_calibration]` (補助) | 本 wave の新規 |
| M4 | G:286〜288 `MEANING_SUPPORTED_MACROS` の導出 | 2 新 macro を除外する形 (例: `*tuple(CONDITIONAL_BRANCH_WITNESSES)[:12]`) | `TG::…accepts_else_with_nested_analysis[*]` (green record の `admission-contract-invalid`)、`TG::…accepts_each_registry_macro[NOREAD/HIGHKEY]`、`TG::test_v1_domain_and_claim_boundaries_are_exact` | 新規 + 既存 |
| M5 | G:2934 一意性 | `!= 1` → `< 1` | `TG::…rejects_duplicate_start_directive` | 既存被覆 |
| M6 | G:967 factory 条件 | `requested != "1"` → `requested not in {"0", "1"}` | `TG::…factory_rejects_nonpaired_values[0-0]` | 既存被覆 |
| M7 | G:3288〜3294 非識別検査 | 除去 | `TG::…rejects_non_discriminating_observation` (reason 契約) | 既存被覆 (reason の契約であり誤受理防止の独立層ではない、1195 insight を継承) |

- `source_rel` 変異は登録しない (helper assert が先に赤を出す)。test 側変異 (T5:89 の条件を戻す) は登録しない。
- 期待 node は author 後の行番号・nodeid で確定し、probe 走 (全件 SURVIVED 期待) で観測 node を集めてから本走を登録する (1195 wave と同手順)。
- 過剰拒否の正例 (受理集合を縮小する wave の義務): `accepts_each_registry_macro[*]` 全 14 件と新正例 2 件が baseline 緑であること。

## §6 焦点テスト集合 (親が実走)
1. TG 全体 (`orchestrator/tests/test_condition_meaning_gate.py`)、T5 全体。
2. 直接 consumer: `test_mocc_proof_surface.py`、`test_build_site_gate.py`、`test_ccbench_spawn_sites.py`、`test_s1_direct_comparison.py`、`test_screening_driver.py`、`test_t2228_driver_gate_liveness_probe.py`、`test_paper_story_a2_certification.py`。
3. 受入全走 (`tools/dev_wave_wait.py acceptance`) で間接 consumer を覆う。

## §7 記録に書く境界
- 主張: 「所有 TU においてその define の値が宣言した枝の選択を決めている」(D1490) を 2 macro に拡張。前処理成功時に限る。動的到達性・positive control の実行時発火・枝本文は主張しない。
- 実測範囲: toy TU (実 patch の前処理構造を模す) + fixture build、実 compiler。実 patch 適用後の CCBench TU (masstree `config.h` 依存) と実機 S2 走行は未検証。
- 件数: 対応集合 13 → 15、未対応 25 → 23。1195 の残り 13 件のうち現在未対応 12 → 本 wave 後 10。
- 影響範囲: S2 (専用 driver、要配線)、CLI (既配線、自動追随)、screening (route 不一致で不変)。

## §8 段 6 裁定 (親、01:32 JST)

- レビュー A (`s6-a.md`) / B (`s6-b.md`): must-fix 0。real nit = (A1/B2) 拒否分岐の reason code 未検査、(A2) M3 の最初の失敗が `IndexError`、(A3) M0 の anchor は現物に無い comment を指す、(B1) S2:109 の 1 行 138 文字。M4 の置換形 (集合差) を採用。
- **親の consumer 回帰 f2 (688 passed / 1 failed)**: `test_build_site_gate.py::test_m11_coverage_configure_gates_are_independent` — S2 の `_broken_build_and_verify` が site gate の前に `_require_condition_gate` を呼び (S2:309)、配線後は meaning arm の configure (prefix `izanagi_compile_time_branch_`) が代役の素通し条件に無く `SimpleNamespace` に `stderr` が無い `AttributeError`。**real must-fix (放置すると受入全走が赤)。** 代役の素通し集合に prefix を足す 1 行が fix (repo 外 probe `probe_m11_s2.py` で fix 無し = 再現、fix 有り = `BuildError` かつ非素通し call 0 件を実測)。production は変えない。
- fix 子 1 本 (`s6-fix-prompt.md`、impl worktree、S05 契約継承): fix 1 = m11 代役の prefix 追加 (`test_build_site_gate.py`)、fix 2 = S2 分行、fix 3 = consumer test に `len(calls) == 1` 先行 assert + 拒否分岐の reason code assert。一枚岩の理由: 3 編集とも数行で、所有 file 2 + consumer test 1 行、並列化の意味がない。
- 変異 §5 の更新: M0 は `old = "_CONDITIONAL_BRANCH_WITNESSES = {\n"`、`new = "# equivalent mutation control (comment only)\n_CONDITIONAL_BRANCH_WITNESSES = {\n"`。M4 は導出文全体を `frozenset({"BACKOFF_FIXED", *CONDITIONAL_BRANCH_WITNESSES} - {"IZANAGI_BREAK_NOREAD_VALIDATION", "IZANAGI_BREAK_HIGHKEY_VALIDATION"})` へ。M3 の anchor は fix 2 後の分行形 (`        declaration=condition_meaning_gate.declare_define_runtime_meaning(request),\n`) → `        declaration=None,\n`。期待 node は probe 走で確定。
- 記録の境界に追加: S2 の `_broken_build_and_verify` 内の再検査 (S2:309) でも meaning arm が走るようになる (preflight 4 configure + 再検査 4 configure → 各 8)。実機の所要増分は未計測。
