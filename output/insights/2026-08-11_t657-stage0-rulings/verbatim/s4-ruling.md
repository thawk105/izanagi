# 段 4 裁定 — [T-657] 段 0 残余 3 束

段 3 の 2 レンズ (sol / luna) はいずれも NO-GO。blocker 5 件のうち 1 件は両レンズが独立に
同じものを指した (revocation schema の越権)。以下、所見ごとに real/refuted と採否を確定する。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | 理由 |
|---|---|---|---|
| SOL-02 / LUNA-01 revocation schema 越権 | **real** | **不採用 (実装しない)** | 裁定は「失効後に下位 authority へ fallback しない」だけ。namespace・schema・commit topology は設計正本 §12.3 が「親が決めない」と明記した項目に残っており、複数成立する形から親が 1 つ選ぶのは越権。**裁定パッケージへ返す (R1)** |
| SOL-01 段 0 完了の受理集合が空 | **real・新事実** | **返す (R2)** | `_applicable_unresolved_count` は先送り確定の `CFAB-S-SEAL` と `CFAB-B-SIDE-EFFECT` を数える (contract module の同関数で確認)。束 3 (a) を実施しても段 0 は構造的に閉じられない。§8-2 の applicability を段 0 status へも及ぼすかは受理集合を変える択一であり、親が決めない |
| SOL-03 段集合の自己申告 | **real** | **部分採用** | 段→fixture の実体対応は現行 fixture repo に存在しない (case は設計 row に対応し段を持たない)。導出は `CFAB-STAGES...-FIXTURE-ASSIGNMENT` gate (pending、owner = 後続 wave) 自身の仕事。**「宣言であって導出ではない」と設計正本へ明記し**、docs の段集合と gate ID literal の drift を機械束縛する (LUNA-08 と同じ手当) |
| SOL-04 段 6 gate の既成事実化 | **real** | **採用 (P2 を撤回)** | 設計正本は「段 6 の判定式は段 0 と段 5 の裁定後に書く」としか言っておらず、新しいユーザー択一が存在するとは書いていない。**新 gate を作らない。** 段 6 は既存の fixture assignment gate (pending) の scope に留め、扱いを **裁定パッケージへ返す (R3)** |
| LUNA-02 gate pin の二者化 | **real** | **採用** | module 内 sha pin を独立 pin として追加し、並べ替え + manifest hash 再計算を拒否する。author と親は別入力から算出する |
| LUNA-03 gate status に証拠が無い | real | **記録のみ** | 3-key schema に証拠欄は無く、module 側 pin が唯一の防壁である事実を insights へ記録。新 gate を作らない裁定 (SOL-04) により、本 wave では悪化しない |
| LUNA-04 設計表と enum の drift | **real** | **採用** | §8.1 の「許容 selection」列を抽出し `_SELECTION_ENUMS` と exact 照合する検査を新設 |
| LUNA-05 §11.2 row 抽出の穴 | **real・本 wave 由来でない** | **backlog** | 既存の抽出器の限界。単発事例であり `DW-G03` に従い族一般化しない。裁定候補として記録 (R4) |
| LUNA-06 selection に実行時 consumer が無い | **real** | **記録のみ** | 段 0 は帳簿の段であり resolver は段 1 以降。**「policy を実装した」と主張しない**ことを worklog と insights へ明記 (R5) |
| LUNA-07 変異の先取り | **real** | **採用** | 下記 §3 の事前登録で、先取りされる組合せを登録しない・再照準する |
| LUNA-08 docs と gate ID の drift | **real** | **採用** | §10 の宣言済み段集合を抽出し gate ID literal と exact 照合する検査を新設 |
| SOL 弱い懸念 (取得済み authority object) | real | **触らない** | B (副作用境界) の裁定境界。先送り維持 |

**親の provisional の帰結:** (P1) は撤回 (schema を land しない)。(P2) は撤回 (段 6 gate を作らない)。
(P3) は段 2 の代案を採用 (owner literal でなく gate ID で段集合を表し、宣言であることを明記)。
(P4) は維持。

## 2. plan v2 (実装するもの)

### 2.1 docs (親が編集)

`docs/calibration-freeze-authority-bundle-design.md` のみ。規則の正本は一意にする。

| 裁定 | 正本節 | 内容 |
|---|---|---|
| U-A1 = activation window | §7.2 `CFAB-7.2-01` | 下位承認の期限は A_f から X_f までだけ検査し、X_f 後は期限で失効させない。発効後 lease と 19 consumer の再検査は書かない |
| rollback = forward compensating generation | §5.1 | 祖先世代の参照へ戻す操作を rollback として受理しない。両成分と上位束を新しい世代番号で前進させる |
| revocation = fallback しない | §7.5 + §1 | **振る舞いのみ。** 上位が一度発効した後に解決不能になった場合、下位 authority へ降格せず fail-closed。「一度も上位 X が無い HEAD」とは区別する。**namespace・schema・commit topology は引き続き定めない**と明記し、裁定待ちの理由を R1 として書く |
| 下位 X_f は上位 X の後 | §5.2 | 段 3 consumer 移行の完了後、かつ上位 X の後 (同一 commit と上位 X より前を拒否) |
| 段 5 除外 | §10 + §10.2 | 段 0 が固定する fixture 閉包を段 1〜4・6〜8 とする。**この段集合は宣言であって、段→fixture の実体からの導出ではない**と明記する。導出は fixture assignment gate の仕事 |

§12 は索引だけを更新する (規則本文を再掲しない)。§12.3 には R1・R2・R3 を残す。
§8 (先送り 3 件) は変更しない。

### 2.2 実装 (Codex author)

- `ruling-profile.v1.json`: 4 ID を `resolved` へ。selection literal は
  `forward-compensating-generation` / `no-lower-fallback-fail-closed` /
  `after-upper-activation` / `activation-window`。順序・12 ID・先送り 3 ID は不変。
- `manifest.v1.json`: `required_gates` を 8 entry のまま更新する (**新 gate を作らない**)。
  4 gate (`CFAB-Q3-REVOCATION` / `-ROLLBACK` / `-XF-POSITION` / `CFAB-S8-S10-CONTRADICTION`) と
  `FREEZE-U-A1` を `resolved` へ = 計 5 件。`CFAB-STAGE-FIXTURE-ASSIGNMENT` を
  `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` へ改名 (owner・status は不変)。
  `entries_sha256` を再計算。top-level `status` は `incomplete` のまま。
  `fixtures` / `row_coverage` / `pending_count=5` / case raw hash は一切触らない。
- `calibration_freeze_authority_contract.py`:
  - `_SELECTION_ENUMS` へ Q3 3 ID の singleton enum を追加。`FREEZE-U-A1` を
    `{"activation-window"}` へ縮める。B の enum は追加しない。
  - `_EXPECTED_RULING_STATES` (独立 pin) を追加。裁定済み 4 ID の exact `(status, selection)` と、
    先送り 3 ID の `("unresolved", None)` を固定する。
  - `_EXPECTED_REQUIRED_GATES` を更新し、`_EXPECTED_REQUIRED_GATES_ENTRIES_SHA256` を独立 pin
    として追加する。
  - `_validate_ruling_profile` に state pin 照合を追加 (applicability 検査の後)。
  - required gate 検査に module sha pin 照合を追加 (manifest literal / parsed entries 再計算 /
    module pin の三者)。
  - **新設検査 1**: §8.1 の表から「許容 selection」列の literal を抽出し `_SELECTION_ENUMS` と
    exact 照合する。
  - **新設検査 2**: §10 が宣言する段集合を抽出し、fixture assignment gate ID の literal と
    exact 照合する。
  - status 算出ロジックは変更しない。
- テスト node (**名前は下記を exact に使う**。変異事前登録が名前で束縛するため):
  - 陽性 `test_adjudicated_ruling_and_gate_projection_is_exact`
  - 陽性 `test_required_gate_entries_have_independent_module_sha_pin`
  - 陰性 `test_adjudicated_rollback_cannot_regress_to_unresolved`
  - 陰性 `test_adjudicated_revocation_cannot_regress_to_unresolved`
  - 陰性 `test_adjudicated_xf_position_cannot_regress_to_unresolved`
  - 陰性 `test_adjudicated_u_a1_cannot_regress_to_unresolved`
  - 陰性 `test_deferred_seal_ruling_cannot_be_resolved`
  - 陰性 `test_rejected_post_activation_lease_is_rejected`
  - 陰性 `test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected`
  - 陰性 `test_design_selection_column_matches_selection_enums`
  - 陰性 `test_design_stage_scope_matches_fixture_assignment_gate_id`
  - 既存 node の期待値更新: `unresolved_count` 6 → 2、`blocking_gates` の件数、
    gate ID を index でなく ID 検索で選ぶよう修正。**期待値を裁定に合わせて緩めない** —
    いずれも「落ちる入力が増える」方向であることを各 node の docstring に 1 行で書く。

### 2.3 実装しないもの

- revocation record の namespace / schema / commit topology (R1)。
- 段 6 用の新 gate (R3)。
- 段 0 status の applicability 変更 (R2)。**先送り 3 件は `unresolved` のまま。**
- production (`orchestrator/campaign/**`, `tools/**`, `output/**`) と case file 10 件。
- [T-139] の凍結。

## 3. 変異事前登録 (DW-M01)

対象は `orchestrator/tests/calibration_freeze_authority_contract.py` と設計正本。
各変異は「同じ入力を拒否する層が前後に無い」ことを確認済み。

| ID | category | 変異 | expected | 単一理由性の確認 |
|---|---|---|---|---|
| M1 | negative | `_validate_ruling_profile` の state pin 照合を無効化 | KILLED (regression 4 node + `test_deferred_seal_ruling_cannot_be_resolved`) | 4 ID の `resolved→unresolved` は schema・enum・applicability のいずれにも触れない。SEAL の `S1` 化も enum・applicability を通る。よって state pin が唯一の層 |
| M2 | negative | required gate の module sha pin 照合を無効化 | KILLED (`test_required_gate_reorder_with_refreshed_manifest_hash_is_rejected`, `test_required_gate_entries_have_independent_module_sha_pin`) | 並べ替えは semantic frozenset を変えず、manifest literal も再計算済みのため一致する。module pin が唯一の層 |
| M3 | negative | `_SELECTION_ENUMS["FREEZE-U-A1"]` を wave 前の 2 値へ戻す | **SURVIVED** (expected_nodes は空) | **先取りの実測記録。** enum を広げても state pin が `("resolved","activation-window")` を要求するため `post-activation-lease` は state pin で落ちる。enum の縮小に独立した検出力が無いことを台帳へ残す (memory「変異は wave 前の実コードの形を必ず含める」の履行) |
| M4 | negative | 新設検査 1 (§8.1 選択列 ↔ enum) の照合を無効化 | KILLED (`test_design_selection_column_matches_selection_enums`) | 新設層であり前後に同じ入力を拒否する層は無い (`_extract_ruling_ids` は ID しか読まない) |
| M5 | negative | 新設検査 2 (§10 段集合 ↔ gate ID) の照合を無効化 | KILLED (`test_design_stage_scope_matches_fixture_assignment_gate_id`) | 同上。gate ID は他のどの検査でも意味を読まれない |
| M6 | positive | state pin を「全 12 ID が resolved であること」へ強める | KILLED (`test_real_repository_contract_is_consistent_but_incomplete`) | **受理集合を縮小する wave の過剰拒否検出正例** (DW-M01)。先送り 3 件を残す正当な repository が落ちることを検出する |

## 4. 裁定パッケージへ返すもの (実装しない real 所見)

- **R1 — revocation record の namespace・schema・commit topology。** 裁定は fallback の可否だけを
  決めた。設計正本 §12.3 は namespace/schema を「親が決めない」に置いている。段 2 案
  (`revocations/<bundle_digest>.json`・exact 7 key・bundle 当たり 0/1 件) と、sol が示した
  同じく成立する代案 (`revocations/<record raw sha256>.json`・承認 record 単位・RFC 3339) の
  両方を提示して返す。
- **R2 — 段 0 完了の受理集合が空である。** 束 3 (a) を実施しても、§10.2 の第 1 条件が先送り確定の
  `CFAB-S-SEAL` と `CFAB-B-SIDE-EFFECT` を数えるため、段 0 は S/B の裁定なしに閉じられない。
  §8-2 の applicability (「その分岐で適用される項目だけ」) を段 0 status にも及ぼすか、
  それとも段 0 の完了自体を S/B の裁定後まで待つか。**裁定時点で未見の新事実である。**
- **R3 — 段 6 の完了 predicate の扱い。** 段 6 も除外するか、構造部分と policy 依存部分へ分割するか。
  本 wave では gate を作らず現状 (fixture assignment gate の pending scope 内) を維持した。
- **R4 — 設計 §11.2 の row 抽出が宣言形しか拾わない** (`row ID = \`CFAB-11.2-xx\`.` の行のみ)。
  表形式で足した行は fixture 閉包から抜ける。既存の穴であり本 wave 由来ではない。
- **R5 — 記録上の注意。** 本 wave は帳簿 (profile / gate / 設計正本) だけを裁定へ整合させた。
  selection literal を読む resolver は存在せず、**policy を実装したのではない。**

## 5. 追加で処理するもの

`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-11-t657-stage0-followups.md` §1 の
[T-772] への 1 行追記 (peer の帰属実測: [T-665]/[T-662] の wave は原因でなく発火確率の増加要因)。
docs fragment 1 行で台帳を正確にする。同ファイル §2 (docs 予算の裁定 3 択) は**未裁定**であり、
本 wave では触らない。
