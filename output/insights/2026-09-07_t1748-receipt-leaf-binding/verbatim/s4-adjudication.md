# 段 4 裁定 — [T-1748]

## 前提の再確認 (段 4 直前)

- 裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査。最新は 2026-09-05 付で、
  wave 開始後の新規はゼロ。取り込む更新なし。
- local main が `37cb5696b` → `442cb549c` へ前進。差分は docs のみ (fold 3 件) で、実装面・
  待ち手・launcher・runner の bytes は 1 byte も変わらない。`DW-O20` の「先に取り込む」条件は
  成立しないので、取り込みは受入直前に行う。
- 変更前の焦点走は緑 (289 passed / 76.07s、request 981683.nqsv)。対象は
  `test_s8c_acceptance_receipt.py` / `test_s8c_acceptance_receipt_v2.py` / `test_trial_registry.py`。
  変異走行の baseline 緑要件を満たす。

## 所見の裁定

### レンズ A (恒真性)

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| 1 | 提案照合は D920 型の恒真ではない | refuted (nit) | — |
| 2 | 負の対照は既存 gate に先取りされず新検査まで到達する | refuted (nit) | — |
| 3 | 正例は検査本体を通る | refuted (nit) | — |
| 4 | 新検査が発火するのは no-build と materialized build。build-failure は既存 gate が先に拒否 | refuted (nit) | — |
| 5 | 実装を current v5 に限る一方、brief は `verify_acceptance_receipt` 全体の欠陥を掲げている (射程不一致) | **real / must-fix** | **採用 (記録側で是正)** |

**所見 5 の裁定 — 実装は広げず、主張の射程を正確に書く。**

親が裏取りした事実 (`layer3_report.py:904-924`): production の唯一の consumer
`build_accepted_report` は `require_current_verified_receipt` を通し、同関数は
`verified.receipt.schema_version != SCHEMA_VERSION` を無条件に拒否する
(`s8c_acceptance_receipt.py:2043-2049`)。したがって **legacy v3/v4 の受領証はどの下流 capability
にも到達しない。** 任意 leaf を持つ v3/v4 受領証から `VerifiedAcceptanceReceipt` は得られるが、
そこから先が無い。

実装を v3/v4 へ広げない理由は 2 つ。

1. **依頼の scope 外。** 依頼は「本題の修正だけ。仮想リスク向けの gate・検査・台帳・一般化の
   追加は scope 外」。到達不能な経路への防壁追加は仮想リスク向けの一般化に当たる。
2. **過剰拒否の危険。** legacy 受領証の再導出には当時の campaign 現物が要る。readable
   compatibility は意図的に維持されているものであり (`s8c_acceptance_receipt.py:2004-2025` の
   legacy 分岐)、現物が失われた legacy 受領証を新たに読めなくするのは受理集合の不当な縮小である。

**したがって是正は記録側で行う。** 段 7 の worklog と、実装 file の docstring に射程を書く。
成立する主張は「**current v5 と、そこから伸びる下流 capability 経路について、cross-binding leaf の
発行時保証が耐久保証になった**」までであり、「`verify_acceptance_receipt` 全体で任意 leaf が
通らなくなった」とは書かない。これは追加の gate・検査・台帳ではなく、既に書く worklog と
docstring の文言なので scope 内である。

### レンズ B (過剰拒否と scope 逸脱)

must-fix ゼロ。5 所見すべて refuted で、原典 file:line 付き。とくに次の 2 つを採用する。

- **所見 1** が段 2 の発行側・検証側の式一致を独立に再導出し、親の補遺と一致した。
  `run_root` / `output_root` の復元可能性は 3 者 (親・段 2・段 3 レンズ B) が独立に確認した。
- **所見 3** が巻き添えになる既存 test を **12 node** 列挙した。`_upgrade_to_current` の呼出しは
  14 件あるが、`test_m4_downstream_capability_rejects_readable_v4_receipt` と
  `test_v4_remains_readable_without_v5_attempt_binding` は検証前に v4 へ下げるので対象外。
  この 12 件を段 6 の焦点走の必須対象にする。

**`DW-M02` により、レンズ B の所見ゼロを変異なしで緑と数えない。** 変異 matrix で裏取りする。

## プラン v2 (確定)

段 2 プランの「変更手順」1〜7 をそのまま採用する。production の計算式は変えない。加えて次を足す。

- **v2-a**: 手順 1 の module docstring 是正に、**射程の明記**を含める。current v5 の leaf だけを
  再導出すること、legacy v3/v4 は従来どおり aggregate のみであること、legacy が下流 capability へ
  到達しない理由 (`require_current_verified_receipt` が v5 のみ受理) を書く。
- **v2-b**: 手順 3 の拒否文言は、どの trial の leaf が食い違ったかを特定できる形にする
  (trial_id を含める)。診断不能な総称エラーにしない。

**採らない案** (段 2 が既に不採用としたものを追認する)。

- (P1-b) leaf を report / journal だけから作れる別 digest に置き換える — build leaf が現在束縛して
  いる 6 field を耐久保証から落とすため。
- (P1-c) leaf の preimage を sidecar として永続化する — 同一走行側の値どうしの照合になり、
  かつ新しい durable path の規約が要るため最小変更を超える。

## 不変条件 (実装子への拘束)

1. 受領証 schema (`p3-8c-trial-acceptance-receipt/v5`) の field 集合・version・canonical bytes を
   変えない。
2. `certifying=False` の構造検査と非 certifying 理由コードを変えない。
3. `trial_registry.py` の発行式と `autonomous_trial_completeness.py` の 3 mode 計算式を変えない。
4. `s8c_acceptance_receipt.py` に新しい subprocess 起動点を作らない (`test_ccbench_spawn_sites.py:230`
   の pin は `<module>._git` = 1 件)。
5. `autonomous_trial_completeness` は **関数内 import** にする。module top-level import を足さない。
6. 現行 aggregate 検査 (`s8c_acceptance_receipt.py:2004-2025`) を削除・代用しない。個別 leaf の
   再導出と aggregate の両方を残す。
7. legacy v3/v4 の受理集合を狭めない。
8. 依頼にない gate・検査・台帳・一般化・互換層を足さない。

## 変異事前登録 (`DW-M01`、実装前に登録)

段 2 の 8 件を採用する。位置はすべて `orchestrator/campaign/s8c_acceptance_receipt.py`。

| # | 変異 | 期待して殺す node |
|---|---|---|
| M1 | 新設した leaf 再導出照合の block を丸ごと削除 | `test_s8c_acceptance_receipt_v2.py::test_v5_rejects_reaggregated_single_cross_binding_leaf_substitution` |
| M2 | 期待値を再導出 digest でなく `trial.cross_binding_receipt_sha256` 自身にする (自己照合化) | 同上 |
| M3 | 照合の向きを反転 (`!=` を `==` に) | `test_s8c_acceptance_receipt_v2.py::test_v5_attempt_binding_accepts_all_predeclared_observed_units` |
| M4 | schema guard を `SCHEMA_VERSION` から `CROSS_BINDING_V2_SCHEMA_VERSION` に変え v5 で発火させない | 新設の leaf 差替え test |
| M5 | 検査 loop を `receipt.trials[:-1]` にして最後の leaf を見ない | 新設の leaf 差替え test (最後の row を改変するため) |
| M6 | 新 helper へ `events=()` を渡す | `test_trial_registry.py::test_p5_six_complete_terminal_reports_pass_acceptance` |
| M7 | `run_root` を journal の親でなく `repository_root` にする | `test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads` |
| M8 | build report を `{**report, "do_build": False}` にして常に no-build leaf を作る | 同上 (standalone 正例を追加した版) |

- **M3 が受理集合縮小 wave に要求される「承認外の過剰拒否」の正例である** — 照合を反転すると
  正当な受領証が拒否され、正例 test が赤くなる。
- 単一理由性 (`DW-M01`、F820) は実装後に各変異で確認する。前後・内側の層が同じ入力を先に拒否して
  いれば登録を取り下げ、実効 gate へ再照準する。

## gate の禁止 (署名) と通る正例

**禁止 (署名):** schema_version が `p3-8c-trial-acceptance-receipt/v5` の受領証について、
ある trial の `cross_binding_receipt_sha256` が、その trial の `report_path` / `attempt_journal_path`
の現在の bytes と、そこから到達する campaign 現物に対して `verify_s8c_cross_binding` を
実行して得られる `receipt_sha256` と一致しないなら、`verify_acceptance_receipt` は拒否する。

**通る正例 1:** `test_s8c_acceptance_receipt_v2.py` の v5 fixture (是正後)。6 trial すべて
`do_build=False` で、leaf は `_cross_binding_no_build_receipt` の実式から作る。

**通る正例 2:** `test_trial_registry.py::test_s8c_acceptance_registered_build_reports_reach_receipt_for_h1_h2_workloads`
の materialized build 受領証を track して `verify_acceptance_receipt` まで通す (段 2 手順 7)。

## 段 5 の分割

編集面が 1 module に集中し相互依存が強いので実装子は 1 本 (Codex `role=author`、D95)。
