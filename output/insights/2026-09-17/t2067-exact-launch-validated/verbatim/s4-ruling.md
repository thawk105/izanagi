# 段 4 裁定 — [T-2067] `_gate_check_core` の二読 fallback 廃止

作成: 2026-09-17 01:00 JST、base = local main `1042a1bc95057fa03117d504cfa2b0fafaae60d0` (段 4 直前に inbox 再走査: main 不動、未 fold fragment なし)

## 1. 所見の判定 (real / refuted、採否、scope)

| 所見 | 判定 | 採否 | 処置 |
|---|---|---|---|
| A-1 sha 比較は独立二入力でない | refuted (plan は条件を保持) | — | `freeze_sha is None` 検査を含む既存条件と refusal を残す。「独立照合」とは書かない |
| A-2 / B-9 brief I1 が実装案より強い | real (must-fix、文言) | 採用 | I1 を「admission しない + 拒否理由の集約は継続」に訂正 (§3)。early return は足さない |
| A-3 callsite 数と race 唯一性の範囲 | real (should) | 採用 | production の core 呼出は **6 箇所 / 2 関数 / 1 module** (`gate_check` 619/632/646/655/677、`_gate_check_validated` 702)、AST 走査であり権威閉包でない。「初回失敗 → 再読成功のみ」は production 到達条件に限定 (private core の直接呼びは test にだけ実在) |
| A-4 / B-10 adapter 経由の迂回 | refuted | — | adapter 発火は定数 `HOLDOUT_RAW_SHA256` (現行 v1 freeze の bytes) に束縛。手作りの不整合 object までは保証しないと明記 |
| A-5 診断差の変異を KILL に混ぜている | real (must-fix) | 採用 | §5 で KILL 候補 (受理集合が変わる) と diagnostic sensitivity pin (拒否のまま reason / 件数だけ変わる) を分離 |
| A-6 v1 不変性の正例が不足 | real (must-fix) | 採用 | v1 document の public race node を新設し `{floor-null, budget-null}` を exact 固定 (新 refusal の不在)。過剰拒否の正例は v2 + exact token の allowed=True (node 4[both]) と、その対偶変異 M8 |
| A-7 静的整合を実行済みへ一般化しない | real (should) | 採用 | 記録で「現物確認範囲」と「未検証 (実走前)」を分ける。DW-O09 は path / hash / generator key 表で 0 件、それ以上の閉包は主張しない |
| A-8 D1984 逐語の不整合 | real (should) | 採用 | D1984 本文の「二読 fallback の択一は未裁定」は D1872 (09-09) の後に書かれた不整合。実装根拠は D1872 + 持ち越し本文 (entry 1527) + 現指示。decisions fragment に注記 |
| A-9 `ratified` 保持で弱くならない | refuted | — | P2 は §2 で親が決める |
| B-1 core `ratified` 削除は consumer 上成立 | real | 採用 | §2 P2 = 削除 |
| B-2 docstring 範囲 428〜434、comment 488〜489 | real (nit) | 採用 | author へ行単位で指示 |
| B-3 P1 維持 | refuted (懸念) | — | P1 = 再読を残す |
| B-4 sha 条件全削除 | refuted | — | 残す |
| B-5 負例が旧 code でも拒否 | refuted | — | hash 一致 fake で旧 code は allowed=True |
| B-6 tmp root で exact 固定不能 | refuted (plan 対処済み) | — | resolver 差し替え + known-axes no-op で exact 固定 |
| B-7 合成型・登録必要 | refuted | — | conftest 登録不要、shard 既定重み 1 秒/node |
| B-8 第一焦点 ≠ 全 consumer | real (should) | 採用 | 焦点走 = 代表経路 (§6)、残りは受入全走 |
| B-11 callsite 4 → 5 (→ A-3 で 6) | real (nit) | 採用 | brief 訂正 |

scope 外の real 所見: なし。裁定パッケージへ返す設計択一: なし (D1872 で実装方向まで裁定済み)。

## 2. provisional 裁定の確定

- **P1 = 再読を残す** (plan・両レンズ一致)。core の `verified` 未指定時の `_load_verified_freeze` (:458) は v1 と二読失敗の既存 refusal 集約に使われており、D1872 が名指すのは v2 の static self-load である。
- **P2 = core の `ratified` 引数を削除する** (親の provisional を維持、B-1 / A-9 で安全性は両案とも確認済み)。理由: D65 決定 (5) の趣旨は gate core への注入口を最小にすること。受理に寄与しない `RatifiedFreeze` の注入口を core に残すのは「gate が 2 通りの意味を持つ」状態の残骸であり、削除は −3 行 (signature 1 箇所 + call site 624 / 638) で新機構を作らない。plan が保持の根拠にした「core への `ratified=` 直接注入の負例」は、public `gate_check(ratified=<合成>)` + 二読 race の負例に置き換える (旧 code では allowed=True、新 code では refusal — public API 越しの観測なので証拠力は上がる)。`gate_check` の public `ratified=` / `ratified_error=` は残す (memo docstring・既存 test が依存)。
- **P3 = hash 一致の合成 `RatifiedFreeze` を返す fake** (plan・両レンズ一致)。AssertionError fake は旧 code も例外を捕捉して拒否するため受理境界の証拠にならない。

## 3. 不変条件 (訂正版)

- (I1') `_gate_check_core` は v2 document (`floor` または `budget` が non-null) を、exact type `LaunchValidatedFreeze` が無い限り **admission しない** — 必ず refusal `M` を積む。拒否理由の集約 (known-axes / floor-null / budget-null / manifest) は従来どおり継続し、early return は足さない。
- (I2) `_gate_check_core` は `s8b_ratified_freeze.load_ratified_freeze` を呼ばない。
- (I3) fallback 発火時以外の refusal 集合は不変 (v1 経路、二読失敗、`ratified_error` の `freeze-ratify:` 翻訳、正常 v2、run-block 経路)。
- (I4) `gate_check` の public signature に `launch_validated` を足さない。
- (I5) 受理集合は狭まるだけ。
- (I6) `_gate_check_core` の signature に `ratified` を持たない (`RatifiedFreeze` を単独で受け取る口が無い)。

## 4. gate の禁止 (署名) と通る正例

- 禁止 (署名): `_gate_check_core(*, freeze_path, manifest_path=None, root, t080_resolution, approved_spec, manifest_verification_error, standalone_manifest_verification, verified=None, verified_manifest=None, launch_validated=None, ratified_error=None) -> GateDecision` — 選ばれた document が v2 かつ `launch_validated is None` かつ `ratified_error is None` なら、`refusals` に `M = "v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要"` を含み `allowed is False`。
- 通る正例: document `{"floor": {}, "budget": {}, "known_axes_freeze": {"path": "known.json"}}`、`verified=VerifiedFreeze(document, sha)`、`launch_validated=LaunchValidatedFreeze(ratified=RatifiedFreeze(document, sha, …), …)` (exact type、`ratified.sha256 == sha`)、`t080_resolution=ReceiptResolution("never-issued", (), None, "a"*40)`、`s1_known_axes_freeze.verify` no-op、manifest なし → `refusals == []`、`allowed is True`。

## 5. 変異事前登録 (B-057、位置 = 実装後の code の意図位置。逐語 anchor は実装 commit の現物から作り、probe 走で観測 node を集めてから本走 spec を確定する)

KILL 候補 (受理集合または fail-closed 挙動が変わる、単一理由):

| id | 変異 | 期待 KILLED node (代表、完全集合は probe で確定) |
|---|---|---|
| M1 | v2 枝で token 欠落時に旧 code の static self-load + sha 一致受理を復活 | node 1 (public race)、node 11 (CLI) |
| M2 | `type(x) is not LaunchValidatedFreeze` → `not isinstance(x, LaunchValidatedFreeze)` | node 5 (subclass) |
| M3 | refusal `M` の append を削除 (枝は残す) | node 1, 2, 3[*], 11 |
| M4 | core signature に `ratified` を復活し call site 624 / 638 を戻し、v2 枝で `ratified.sha256 == freeze_sha` なら refusal を積まない | node 2 (public race + `ratified=` 注入)、node 12 (signature pin) |
| M5 | token 有り枝の sha 条件 (`freeze_sha is None or freeze_sha != …`) を全削除 | node 9 (hash None) |
| M8 | v2 枝で token があっても `M` を積む (過剰拒否の対偶) | node 4[both] (allowed=True の正例)、node 4[floor-only/budget-only] |
| M0 | 等価対照: v2 枝の comment 1 行だけ変更 | SURVIVED 期待 (positive) |

diagnostic sensitivity pin (拒否のまま reason / 件数だけが変わる。negative・KILLED 期待で走らせ、台帳で別枠に記録し KILL 数に算入しない):

| id | 変異 | 期待赤 node (代表) |
|---|---|---|
| M6 | core の v2 判定 `floor is None and budget is None` → `floor is None` | node 3[budget-only] (v1 枝へ倒れて `M` が消える) |
| M7 | `ratified_error` 翻訳より `M` を優先 | node 6 (`freeze-ratify:` が `M` に置換) |
| M9 | v1 枝にも `M` を常時追加 | node 10 (v1 pin) |

等価と見なす候補 (登録しない): token 有り枝の `!=` 比較だけの削除 (`is None` を残す、同一 object の自己比較)、未使用代入の増減。

## 6. 焦点走と受入

- 焦点走 (代表経路、login node の xdist): 新規 file 全 node + `test_s8b_oracle_driver.py -k "gate_check or gate_check_core or standalone_gate or nonnull_floor or private_validated_gate or v2_freeze_bytes_not_active or run_block_reuses_launch_validated or run_block_verifies_manifest_once or cli_subprocess or t080_gate_hermetic or never_issued_generator_tamper or real_freeze_gate_lists"` + `test_s1_known_axes_freeze.py::test_historical_oracle_nonadapter_reaches_current_semantics` + `test_s8b_binding_driftguards.py -k "gate_check or ratified_memo"`。
- 受入全走 (計算ノード、`dev_wave_wait.py acceptance --lease-optional`) は統合 commit 後に 1 回、記録 commit 後に land 用に 1 回。
- 変異 matrix は専用 container worktree (統合 commit 固定) で `-- python3 tools/run_tests.py orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py orchestrator/tests/test_s8b_oracle_driver.py -k <焦点集合> -q -rf --force-dispatch`。

## 7. plan v2 (author への指示の骨格)

1. production (`orchestrator/campaign/s8b_oracle_driver.py`):
   - `_gate_check_core` signature から `ratified` (412〜414 行) を削除。docstring 428〜434 行を置換 (v2 枝は exact `LaunchValidatedFreeze` を要求、`ratified_error` は `freeze-ratify:` へ翻訳、core は static loader を呼ばない、「floor/budget のいずれかが non-null」)。
   - v2 枝 (487〜505 行) を `if ratified_error is not None: freeze-ratify / elif launch_validated is None: M / elif freeze_sha is None or freeze_sha != launch_validated.ratified.sha256: freeze-not-active-generation` に置換。comment 488〜489 も実装に合わせる。
   - `gate_check` の call site 624 行 (`ratified=ratified,`) と 638 行 (`ratified=ratified,`) を削除。他の 3 call site と `_gate_check_validated`、`run_block`、CLI は不変。
2. test (新規 `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`、既存 test file は一切編集しない):
   - node 1 `test_public_reread_v2_requires_launch_validated`、node 2 `test_public_reread_v2_ignores_injected_ratified`、node 3 `test_core_v2_without_launch_validated_is_refused[both|floor-only|budget-only]`、node 4 `test_core_exact_launch_validated_preserves_predicates[both|floor-only|budget-only]`、node 5 `test_core_rejects_launch_validated_subclass`、node 6 `test_public_ratified_load_errors_preserve_refusals[RatifiedFreezeError|RuntimeError]`、node 7 `test_public_explicit_ratified_error_keeps_early_return`、node 8 `test_public_two_failed_reads_preserve_refusals`、node 9 `test_core_launch_validated_missing_hash_remains_refused`、node 10 `test_public_reread_v1_never_gets_missing_token_refusal`、node 11 `test_cli_gate_check_transports_missing_token_refusal`、node 12 `test_gate_core_signature_has_no_ratified_injection_port`。合計 17 node。
   - 合成 object は新規 file 内で `driver.s8b_ratified_freeze.RatifiedFreeze / VerifiedFloorArtifact / LaunchValidatedFreeze`、`driver._freeze_io.VerifiedFreeze`、`driver._t080_migration.ReceiptResolution` を直接構築。`_resolve_t080_receipt` を合成 resolution に差し替え、`s1_known_axes_freeze.verify` を no-op、node 10 は `s8b_holdout_freeze.verify` も no-op。exact refusal は集合と件数の両方を比較する小 helper を file 内に置く。実 repo・実 active 世代・実 submodule・subprocess・git を使わない。
