# 段 4 裁定 + plan v2 — [T-244]

親が段 2 プランと段 3 レンズ A/B の所見を real/refuted・採用/不採用・scope 内/外に裁定する。
判定はすべて親自身がコードで裏取りした事実に基づく。

## 0. 親 brief の訂正 (子の指摘を親が実測で確認した)

| brief の前提 | 判定 | 実測した事実 |
|---|---|---|
| 前提 8「既存テストに受理集合検査が無い」 | **誤り (訂正)** | `test_p3_autonomous_workload_trial.py:130-154` が `generations=3` を受理させて planner-invalid 停止を固定している。正確には「**明示の exact-value / boundary テストが無い**」 |
| 前提 9「role md に byte pin 無し」 | **誤り (訂正)** | `orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256` が `planner-v4` / `coder-v4-autonomous-trigger-gating` / `auditor` / `critic` の exact SHA を pin 済み。親の `grep` が `.md` パス文字列で探したため見落とした (pin は role 名で key を張る) |
| DW-G05「値でなく受理集合と台帳の有効性が変わる」 | **不正確 (訂正)** | `generation_budget` は `_campaign_for` の `search_config` に入り (`:413`)、`ident.canonical_preimage` の対象 (`ident.py:76-92`)。よって CLI 既定値 2→1 は **flag 省略時の campaign ID・report・journal の実値を変える** |
| 前提 5「粗い失敗カテゴリの還流が既に存在する」 | **過大一般化 (訂正)** | producer は 3 literal を使うが、`state_from_dict` は key 集合と `delta_pct` だけ検査し `result` の値を無検証で格納する (`p3_s4_loop.py:389-404`)。閉 enum ではない。role-invalid / auditor-invalid / dry-pass は whiteboard result にならない |

前提 1〜4・6・7 は両レンズとも「正しい」で一致。

## 1. 所見の裁定

### real・採用・scope 内

- **R1 (A/B 共通・致命): S1 は cross-generation 不変条件を機械化しない。**
  同一 `trial_id`/config で `--run-root` だけ変えて 1 generation build を連結すると、
  campaign root は共有 (`:631-634`、ID preimage に run_root は入らない) で
  `_whiteboard()` が過去 state を読む (`:474-476` → `:666-676`)。scalar gate だけでは
  「宣言された禁止の機械化」と名乗れない。
  → **採用。freshness gate を S1 に含める。**
- **R2 (A・致命): `_run_workload()` 直呼びが validator を素通りする。**
  module-level callable で `generations` をそのまま `range()` に使う (`:614-620`, `:655`)。
  先頭 underscore はアクセス制御ではない。
  → **採用。`_run_workload()` にも validator を置く。**
- **R3 (段 2・A・B 共通): (P2)「CLI だけ塞ぐ」は refuted。**
  D106 決定 6 の programmatic carve-out は残余 1 には無く、禁止対象は「運転」である。
  `run_trial()` は公開名で `do_build=True` と `generations=2..10` を受理し WAL COMMIT へ到達しうる。
  → **(P2) を破棄し、共通 validator を採用。**
- **R4 (A): 既存 `generations=3` テストを `1` にすると role-invalid の `break` 検出力を失う。**
  → **採用。承認上限をテスト内で monkeypatch して 3 を通し、検出力を保持する。**
- **R5 (A・F69): `MAX_APPROVED_GENERATIONS` 導入で値ベース positive control が無力化しうる。**
  境界テストが `MAX_APPROVED + 1` を渡す形だと、定数を 2 にする変異でテストも動いて緑のまま。
  `default=MAX_APPROVED_GENERATIONS` への同値 refactor も全値テストが緑。
  → **採用。境界テストは 1/2 を literal 固定し、既定値は AST で `ast.Constant(1)` を pin する。**
- **R6 (A/B): 保証名を過大に書いてはならない。**
  → **採用。新 D・runbook・worklog に「T-244 解決」「規律 3 還流を閉じた」と書かない。**

### real・不採用 (scope 外) → 裁定パッケージへ

- **X1 (A): `drive` / `providers` / `preview` の注入 seam。**
  `run_trial(generations=1, drive=multi_drive)` は 1 callable 内で複数 iteration を回せる。
  production API から注入を外すのは interface 変更で、既存テスト 4 本が依存する。
  → 実装しない。新 D に「任意注入経路は機械保証の対象外」と明記し、裁定パッケージへ。
- **X2 (A): driver 層 (`p3_s4_loop_trigger_gating.drive_iteration`) の反復。**
  他の正当な human-supervised loop が resume を仕様として使う (`test_p3_s4_loop_trigger_gating.py`)。
  ここに承認上限を置くと無関係な loop を壊す。→ 実装しない。裁定パッケージへ。
- **X3 (B-03): `state_from_dict` が `direction`/`magnitude`/`result` の値を無検証で通す。**
  閉 enum 化と origin binding が要る。規律 6 の信頼境界問題で real。→ 裁定パッケージへ。
- **X4 (B-04): planner の `current_perf` 絶対 throughput と coder の `baseline`。**
  `delta_pct≡None` は planner 全体の性能リーク防壁ではない。recipient matrix の明示裁定が要る。
  → 裁定パッケージへ。**あわせて `cache_miss_rate_pct` / `abort_rate_pct` に 0..1 の率が入る一方
  planner-v4 の例示は percent 表記という 100 倍の単位ずれ**も real defect として同送する。
- **X5 (A): `WhiteboardEntry.result` の閉 enum 化、role-invalid / infrastructure failure を
  粗分類へ含めるか。** → 裁定パッケージへ。

### refuted

- **F1 (段 2 プランの示唆): planner の `justification` が coder へ届く。**
  → refuted。coder payload は `axis/direction/magnitude` の 3 field だけ (`:702-708`)。レンズ B も refuted と判定。
- **F2: 複数 workload 間で whiteboard が共有される。**
  → refuted。workload 名が campaign config に入り ID が分かれる (`:400-429`)。
  ただし provider instance と wall budget は共有 — scope に明記する (レンズ A も must-fix ではないと判定)。
- **F3: 「1 generation でも還流する」は D106 残余 1 を失効させる新事実である。**
  → **refuted。既知事実である。** D106 残余 3 (`decisions.md:4876-4879`) が同じ経路を逐語で記録済み。
  レンズ B が明示的にこう判定し、親も原文を照合して確認した。
  **したがって D106 残余 1 を独断で失効させない** (DW-S04)。本 wave は残余 1 の禁止を
  「より広い範囲で機械化する」方向にだけ動き、許可条件 (1 generation/cell) を広げない。

## 2. S2 (還流設計) の裁定

**実装しない。** 段 4 で「実装しない」と裁定したのは S2 のみで、S1 は実装するため
段 5・6 は通常どおり実行する。S2 について確定した内容:

- **候補 A (現状維持)** は規律 3 の設計解ではなく封じ込め策である。かつ freshness gate 無しでは
  「1 generation だから欠陥不発」という許可根拠自体が成立しない (R1)。
  → 「設計候補」ではなく「封じ込め」として位置づけを変える。
- **候補 B (planner-only 4-class)** は不採用。`direction × magnitude` の 9 記号 =
  `log2(9) ≈ 3.17 bit/世代` が 4-class = 2 bit を一世代で coder へ運ぶ。recipient separation は
  情報フロー分離になっていない。D45 は自然文 lint を唯一防壁にしない決定済み。
- **候補 C (window 集約)** は不採用。planner が window 構成を選べる限り、既知 class の padding
  2 件 + 対象 1 件で 2-bit class を一 window で完全復元できる。
- **候補 D (planner/coder 双方)** は不採用。D39 が排除した勝ち筋逆算経路の直結。

**裁定パッケージには、段 2 が挙げなかった設計軸を第一候補として載せる:**
(i) trusted machine が failure を単調な safety constraint へ変換し generator は理由を見ない、
(ii) failure を post-run auditor だけへ戻し auditor は機械検証可能な veto/obligation だけ返す、
(iii) verifier feedback 前の候補 batch 凍結、
(iv) campaign-global な disclosure / query budget (`--max-generations` でなく総 iteration を束縛)。
各候補に「誰がどの field を見るか / 一世代あたり最大何 bit / query 総予算 / producer は
trusted machine か外部 role か / origin binding / proof chain へ何を残すか / 再開条件」を必須項目とする。

## 3. plan v2 (S1 の実装内容)

編集面 = `orchestrator/campaign/p3_autonomous_workload_trial.py` と
`orchestrator/tests/test_p3_autonomous_workload_trial.py` の 2 ファイルのみ。

1. 定数 (`:88-92` 付近): `MAX_APPROVED_GENERATIONS = 1` を追加。`MAX_GENERATIONS = 10` は
   実装上の絶対上限として残す。解除は本定数と境界テストの同時変更だけで行う。
   環境変数・隠し flag・provider 別例外は作らない。
2. `_validate_generation_budget(generations)` を `AutonomousTrialError` 定義直後に新設。
   判定順: (a) bool / 非 int / `1..MAX_GENERATIONS` 外 → 既存契約違反、
   (b) `> MAX_APPROVED_GENERATIONS` → D106 残余 1 の未裁定運転として拒否。
   メッセージは定数から生成し上限を直書きしない。
3. `_assert_fresh_campaign_state(layout)` を新設。`loop_core.load_loop_state(layout)` が
   `None` でなければ `AutonomousTrialError`。`_run_workload` の layout 確定直後
   (`:631-635` の直後)、**最初の provider 呼び出しより前**に置く。
4. 呼び出し点 3 箇所: `main()` の `parse_args` 直後 (競合 process 検査・checkout より前)、
   `run_trial()` の既存 range 判定を置換 (`:859-860`、`run_root.mkdir()` より前)、
   `_run_workload()` の冒頭。
5. CLI 既定値 (`:1017`) を `default=2` → **literal `1`**。`MAX_APPROVED_GENERATIONS` に
   連動させない (将来の上限解除が flag 省略運転まで自動で変えるのを防ぐ)。
6. テスト (新規 8 本 + 既存 2 本更新)。詳細は下記変異事前登録の期待 node に一致させる。
   `test_invalid_role_is_single_attempt_and_stops_cell` は `monkeypatch.setattr(A,
   "MAX_APPROVED_GENERATIONS", 3)` で `generations=3` を通し、`break` 検出力を保持する。

docs は親が段 7 で書く (実装子は触らない): 新 D の起票、runbook の「機械 gate は無い」3 箇所の
置換、phase3.md 8c 節の追随、D106 への supersede 追記。

## 4. 変異事前登録 (DW-M01)

各変異について「その位置より前に同じ入力を拒否する検査が無いこと」「無効化時の赤理由が
一つに絞れること」を親がコードで確認した。受理集合を**縮小する** wave なので、
過剰拒否を検出する**正例**も登録する (DW-M01)。

### 負例 (gate の削除・弱体化 → kill 期待)

| ID | 変異 | 期待 node | 単一理由性の確認 |
|---|---|---|---|
| V1 | `main()` の validator 呼び出し削除 | `test_main_rejects_unapproved_budget_before_build_preparation` | validator より前に generations を見る検査は無い。削除 site を exact anchor で 1 箇所に固定 |
| V2 | `run_trial()` の validator 呼び出し削除 | `test_run_trial_rejects_unapproved_budget_before_artifact_creation` | `run_root.mkdir()` より前。helper 定義でなく call site だけを消す |
| V3 | `_run_workload()` の validator 呼び出し削除 | `test_run_workload_direct_call_rejects_unapproved_budget` | 直呼び経路には他に検査が無い |
| V4 | freshness gate 呼び出し削除 | `test_run_workload_rejects_existing_campaign_state` | 既存 state を拒否する検査は他に無い |
| V5 | 承認上限判定 `>` → `>=` | `test_generation_budget_boundary_at_ratified_launch` | 1 が拒否される。過剰決定を避けるため boundary node を単独走行で確認 |
| V6 | CLI 既定値 `1` → `2` | `test_main_default_generation_budget_is_one` (+ 既存 accept 3 本) | validator が sentinel より前に発火。期待 node 4 件すべてを台帳へ記録 |
| V7 | `MAX_APPROVED_GENERATIONS` `1` → `2` | `test_generation_budget_boundary_at_ratified_launch` | 境界テストが 1/2 を **literal** で持つため定数変異に追随しない (F69 対策) |
| V8 | `default=1` → `default=MAX_APPROVED_GENERATIONS` | `test_cli_default_is_literal_one_by_ast` | 値は同一のため値テストでは検出不能。AST で `ast.Constant(1)` を pin する (F69 exact 再演の遮断) |
| V9 | bool 拒否削除 | `test_generation_budget_rejects_bool` | `True == 1` のため値テストでは緑。専用負例が要る |
| V10 | 下限・非 int 拒否削除 | `test_generation_budget_rejects_zero_and_non_int` | 0 は空 run、1.0 は後段の素の `TypeError` (F68 型) になる |
| V11 | freshness gate を planner 呼び出し後へ移動 | `test_run_workload_rejects_existing_campaign_state` | provider が呼ばれたら失敗する monkeypatch で順序を固定 |
| V12 | role-invalid の `break` 削除 | `test_invalid_role_is_single_attempt_and_stops_cell` | 承認上限を 3 に monkeypatch した状態で 1 世代停止を固定 (R4) |

### 正例 (過剰拒否 → kill 期待)

| ID | 変異 | 期待 node | 狙い |
|---|---|---|---|
| P1 | 承認上限判定を `generations >= MAX_APPROVED_GENERATIONS` で拒否 | `test_generation_budget_boundary_at_ratified_launch` | 1 まで拒否する過剰拒否の検出 |
| P2 | freshness gate を無条件拒否に変更 | `test_run_workload_accepts_fresh_campaign_state` | fresh state を拒否する過剰拒否の検出 |
| P3 | validator を「全 int 拒否」に変更 | 既存 accept 3 本 + boundary | 正当な既定運転を塞ぐ過剰拒否の検出 |

harness 契約: DW-M04/M05 に従い exact anchor で置換一意性を assert、`read_text()` 一致で復元検査、
`flock` 単一走行。DW-M08 に従い `-rf` で失敗 node を記録し、**`rc != 0` かつ failed node 0 件は
KILL でなく MISMATCH** に倒す (F65)。pytest rc=4 (nodeid 不在) を KILL に数えない。
本走は統合 commit 後 (DW-O19)。

## 5. 保証名 (これ以上のことを書かない)

本 wave が達成するのは次だけである。

- CLI・`run_trial()`・`_run_workload()` の 3 層で、承認上限 (現在 1) を超える generation 予算を
  build 準備・artifact 作成より前に fail-closed 拒否する。
- generation 1 の provider 呼び出し前に、既存 campaign state を fail-closed 拒否する。
- CLI 既定値を承認済み側 (1) にする。

達成しないこと (worklog・新 D に明記する):
- T-244 本体 (規律 3 の還流設計) は**未解決**のまま。
- `drive`/`providers`/`preview` の注入経路、driver 層の直接反復は機械保証の**対象外**。
- 「cross-generation 還流を機械的に禁止した」とは名乗らない。名乗れるのは
  「宣言済み禁止のうち、generation 予算と campaign state freshness の 2 つを機械化した」まで。
