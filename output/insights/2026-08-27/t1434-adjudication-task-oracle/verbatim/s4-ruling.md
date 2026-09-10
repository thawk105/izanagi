# 段 4 裁定 — [T-1434][T-189] adjudication 層の task-specific oracle 対応

裁定時刻: 2026-08-27 07:05 JST
一次資料: `s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、
`tools/codex_reasoning_ab.py`、`orchestrator/tests/test_codex_reasoning_ab.py`、
`docs/phase3-t189-model-routing-preregistration.md`、`docs/decisions.md` (D931 / D767 / D674)

段 4 直前に裁定 inbox (`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/`) を再走査した。
2026-08-27 付の 4 件を含め、本 wave の主題 (adjudication / oracle / known_finding / T-1434 / T-189)
に触れる控えは 0 件である。local main は `dd6621397` から `a0a0cdf46` へ進んだ。取り込みは
`DW-O20` に従い受入時の post-claim merge で行う。

---

## 1. 親 brief への反証 — すべて real、すべて採用

段 3 の 2 レンズは、独立に**親 brief 自身の実測主張**を 4 件覆した。親は 4 件とも real と裁定し、
brief を訂正する。

### R1 (A1) — join 前提は誤り。real、採用

親 brief は「`_load_adjudication` は revealed mapping を読んだ後に走るので、検査時点で packet ごとの
task が同定できている」と書いた。**これは誤りである。** 実コードの順序は次のとおり。

1. `:9322-9336` verdict 行の検査ループ (`_validate_verdict_row` を呼ぶ)
2. `:9337-9341` `mapping` の辞書化
3. `:9366-9370` `slot_by_run` の構築
4. `:9371` 以降の mapping ループで初めて `packet_id -> run_id -> slot` の join が成立する

**したがって既存の検査位置へ `benchmark_task_id` を渡すことはできない。**
段 2 プランの「既存 union 検査は残し、join 後に第 2 検査を足す」を**唯一の実装方針**として確定する。

### R2 (A2) — 「真部分集合」は一般には偽。real、採用

task 別集合は union の**部分集合**であるが、常に真部分集合ではない。等しくなる場合が 3 つある。
(i) 組込み `TASK_MANIFEST` (POS/NEG が同一集合。親が実走で確認済み)、(ii) task が 1 件だけの
manifest、(iii) 対象 task が union 全体を持つ manifest。
brief・プラン・docs の全箇所を「**部分集合であり、task 間に finding 差があるときだけ真部分集合**」
へ統一する。

### R3 (A7) — 「bytes で pin する台帳・trust root は存在しない」は偽。real、採用 (文言のみ)

親が現物で裏取りした。`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` は
`tool_sha256` に `58f1176e0ff705ade85ac0cec0c15b77a26f8eaa2d75bb3f7d711519ed6657f7` を持つ。
現行 `tools/codex_reasoning_ab.py` の SHA-256 は `777840d105088a418daa6c4ae8ae747df58d511c071b4a9ed6d18106cc9a36de` で **一致しない**。
`DW-O09` / F39 の分類は **歴史記録**である。live consumer ではない。

- **結論 (更新閉包 0 件) は維持する。** この pin は追随更新しない。更新すると、過去の
  `aggregate.json` / `verify.json` がどの装置で certified だったかという参照が改変される。
- **文言だけ書き分ける:** 「現行 bytes を pin する live consumer は 0 件。旧 T-181 の
  歴史 pin は存在し、更新対象外」。

### R4 (A9 = B6) — DW-G05 の成果物影響が実コードと一致しない。real、採用

親 brief は「§8 の記述的 finding coverage の分子が誤って増える」と書いたが、**そのような分子は
実装されていない。** 親が確認したところ、`output/` に `judgments` を持つ material manifest は
1 件も存在しない。実コードで cross-task `equivalent_to` が変える値は次のとおり。

- primary の `k` は `r1_detected` だけから増える。finding の `equivalent_to` は coverage 分子に
  使われない。
- negative task で `real` かつ severity が CRITICAL / HIGH かつ `must_fix` の finding は
  false-finding count を増やし、**結果を悪化させる**方向に働く。
- 片方の reader だけが出した finding は conservative intersection から消え、統計値は変わらない。

**DW-G05 を次へ書き換える。**

> 実装しないと、仕様外 (その task の oracle 集合に無い) finding ID が raw verdict 行として
> 受理される。両 reader に残れば negative の false-finding 集計と arm 除外判断を汚染し、
> 片方だけなら統計には現れないまま材料レポートが `valid=true` のまま通る。
> 新ゲートが実際に変える値は、不正 raw row を持つ材料レポートの `valid` を `false`、
> `experiment_complete` を `false` にし、`primary_judgment_ledger` / `new_finding_ledger` /
> `decision` を null 化することである。

---

## 2. 実装 scope の裁定

### R5 (B4) — fixture は 4 slot の paired schedule にする。real、採用

段 2 プランの alpha/beta 各 1 slot は `_validate_schedule` を通らない。block は
「同一 task・stage・cache・price の 2 行が連続し、`(arm, requested_model)` の組が 2 つ異なる」
ことを要求する。schedule を packet source から省く逃げ道 (`make_packets` の scheduleless 互換経路)
は採らない — それは v3 schedule・`_replay_manifest`・実 entrypoint の配線を 1 つも証明しない。

**確定:** alpha 2 slot + beta 2 slot = 4 slot の paired schedule を作り、schedule descriptor を
packet source に含める。その fixture で **`_load_adjudication` を stub せず実物を通す**正例を
少なくとも 1 本置き、`_replay_manifest` から loader への `task_manifest` 転送が変異で赤になる
ことを確認する (M7)。

### R6 (B2) — 負例は reader 方向を parametrize する。real、採用

parent 側だけの負例では、second-reader 側の検査だけを削る変異が全テストを通る。
`reader = parent / second-reader` の parametrized 負例にし、各ケースで
(i) `append_verdicts` が union により成功すること、(ii) 使う ID が manifest union 内であること、
(iii) task-specific reason が exact に 1 件出ること、を確認する。

### R7 (B3) — 既存 aggregate ゲートの負例を新設する。real、採用

`_aggregate_verified` の `equivalent not in known_finding_ids` (`:10179-10184`) には
**負例が 1 件も無い。** 削除しても現行の全テストが緑のままである。機構の必要性を反実仮想で
確かめる観点そのものであり、本 wave で塞ぐ。外部 2-task manifest を `_aggregate_verified` へ
直接渡し、beta verdict に union 内の `alpha-finding` を置く負例を追加する (M6)。

### R8 (B5) — `oracle_kind` の負例は wrong と missing の 2 軸。real、採用

「逆値または削除のどちらか一方」では missing-field rejection を所有できない。
`verdict.get("oracle_kind", dimensions["oracle_kind"])` への変異は逆値テストを落とす一方、
欠落を受理する。parametrized で `wrong` と `missing` の 2 ケースを置く。

### R9 (A3 + B5 後半) — dimension join 失敗の負例を置く。real、採用

段 2 プランは dimension join 失敗時に明示 reason を残すと書いた。**契約にするなら負例が要る。**
reason 追加だけを削る変異が赤にならない状態を残さない。malformed-dimensions の負例を 1 本置き、
「reason 追加前の `continue` を作らない」を機械で固定する。

### R10 (A10) — aggregate の exact 比較は残すが、呼び方を正す。real、採用 (記述と実装)

A10 の指摘は正しい。live 経路では `_load_adjudication` が schedule 由来の `oracle_kind` を verdict へ
入れ、`_aggregate_verified` が同じ slots と manifest から再導出するため、**同一の authority の
再計算**であって独立照合ではない。

- **実装は残す。** `_aggregate_verified` は内部 API として replay 以外の caller からも呼ばれうる。
  R8 の直接呼び出し負例がこの層を実効 gate にする。
- **記述は正す。** 「第 2 の独立ゲート」と呼ばない。「in-memory handoff の冗長 invariant」とし、
  保証の参照数を水増ししない。

### R11 — `oracle_kind` を combined verdict の hash へ入れる件。採用

親が互換性を実測した。`output/` に `judgments` / `combined_verdict_sha256` を持つ生成済み
material manifest は **1 件も存在しない**。したがって既存の凍結成果物を 1 つも壊さない。
`row_sha` 計算より前に入れることで、記録済み judgment 行がその slot の oracle 分類へ束縛される。
プラン §5 が列挙する既存テスト 8 箇所の追随編集を許可する。

### R12 (A11) — transport の限定。real、nit、採用 (記述のみ)

「外部 v3 manifest でしかテストできない」は踏み込みすぎである。述語の単体検査は in-memory の
`_synthetic_task_manifest` dict でも成立する。外部ファイル transport が必要なのは
CLI と D931 の digest 連鎖を同時に証明する場合だけである。両方の fixture を置く。

### R13 (A4/A5/A6/A8) — 確認所見。real だが修正不要

- A4: `_validate_verdict_row` の production call は 5 箇所 (`_load_adjudication` 1、
  `append_verdicts` 2、`freeze_verdicts` 1、`reveal_mapping` 1)。**blind 境界は保存される。**
  per-task 化は post-reveal の `_load_adjudication` 内の別検査だけに限定する。
- A5: D931 の digest 連鎖は緩めていない。ただし新 fixture が `_load_adjudication` を直接呼ぶ場合、
  material manifest 自身の exact 検査はその関数では発火しない点をテストのコメントに明記する。
- A6: D767 の `unbound` は保存される。`oracle_kind` は control 分類であって semantic acceptance
  ではない。
- A8: §13 の「run 開始後は oracle を変更しない」は未発火。R3 と同様に親の主張が支持された。

---

## 3. scope 外の real 所見 — 裁定パッケージへ送る

実装しない。ユーザー裁定へ返す。

- **§8 の記述的 finding coverage が未実装である** (B6 前半)。numerator (両 reader が検出と一致した
  oracle finding 数)、denominator (oracle finding 総数)、negative control の分母除外、
  false-finding rate の別集計は、いずれも `_aggregate_verified` に存在しない。
  §8 は数式まで書いているが、装置は対応する値を 1 つも生成しない。
- **独立 oracle ledger そのものの作成・凍結** (§8.1)。本 wave は装置側の束縛だけを閉じる。
- **`apparatus-pin.json` の歴史 pin の扱い** (R3)。更新しないと裁定したが、
  「旧装置 SHA を trust root として持つ歴史記録を今後どう扱うか」は本 wave の範囲外である。

---

## 4. 到達度の裁定 (B7)

本 wave の後も **「(b) 完了」とも「実装済み」とも書かない。**

- §5.2 表の `_load_adjudication` 行 = **部分実装**。閉じるのは「現行 task manifest に記録された
  `known_finding_ids` と `oracle_kind` の post-reveal task 別束縛機構」である。
  **閉じていない面を必ず名指しする** — 独立 oracle ledger の作成・凍結、その固有 hash 契約、
  severity / must-fix / 根拠 artifact / 検出条件 / canonical identity の schema、
  task 固有 acceptance (`unbound` のまま)、§8 の coverage と negative-control 集計、
  reader 独立性、そして **組込み manifest では POS/NEG の集合が同一のため narrowing が
  発火しないこと**。
- §5.3 は **機構は着地** / **task 固有契約は未登録** / **acceptance 未束縛** の併記とする。
- **§5.3 の既存記述に 1 行足す。** 「機構は着地」は存在の主張であって発火の主張ではない。
  組込み manifest 上では per-task narrowing も `_aggregate_verified` の既存 task 別検査も恒真で、
  差が出るのは task ごとの集合が異なる外部 v3 manifest だけである。
- `append_verdicts` などが blind 段階で union を使うことは**意図した状態**として記述する。
  欠落ではない。

---

## 5. 変異事前登録 (DW-M01)

実装前に登録する。各変異は単一理由性をコードで確認済みである。

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | `_load_adjudication` の per-task 取得を union へ戻す (`benchmark_task_id=` 引数を落とす) | cross-task 負例 (parent 方向) が赤 |
| M2 | raw reader rows の検査を parent のみへ狭める | cross-task 負例 (second-reader 方向) が赤 |
| M3 | `oracle_kind` を combined verdict へ入れる行を削除 | oracle_kind 束縛の正例と hash テストが赤 |
| M4 | `verdict.get("oracle_kind")` を `verdict.get("oracle_kind", dimensions["oracle_kind"])` へ | `missing` 負例が赤、`wrong` 負例は緑 (単一理由性の確認) |
| M5 | `_aggregate_verified` の `oracle_kind` exact 比較を削除 | `wrong` と `missing` の両負例が赤 |
| M6 | `_aggregate_verified` の既存 `equivalent not in known_finding_ids` を削除 | R7 の新負例が赤 (**変異前の現状ではこの負例が存在しないため緑。機構の必要性の反実仮想**) |
| M7 | `_replay_manifest` の `task_manifest=task_manifest` を `task_manifest=TASK_MANIFEST` へ | R5 の 4-slot 実配線正例が赤 |
| M8 | dimension join 失敗時の reason 追加を削除して素通し | R9 の malformed-dimensions 負例が赤 |
| M9 | per-task 集合を `set()` へ (過剰拒否) | **正例**が赤 (`DW-M01` の「受理集合を縮小する wave では承認外の過剰拒否を検出する正例も登録する」) |

`DW-M08` の新旧両走は不要である — 本 wave は production を変える (テスト強化だけの wave ではない)。
`hang_risk` 変異は無い。

## 6. 実装単位

**実装子は 1 本。** 編集面は `tools/codex_reasoning_ab.py` と
`orchestrator/tests/test_codex_reasoning_ab.py` の 2 ファイルへ集中し、
R11 の追随編集が両ファイルへまたがるため分割しない。docs は親が書く。
