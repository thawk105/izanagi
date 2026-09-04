---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: human-turns-delegation-20260905
seq: 1
title: 人間手番 5 件と値 2 件をユーザーが AI へ委任した — 値 2 件と床値の担当・計画を裁定として記録し、実施を 4 つの実装 wave へ分けた (docs のみ、branch worktree-human-turns-delegation-20260905、実装面の差分 0)
---

## 本文

- **ユーザーが、残っていた人間手番と値待ちの実施を AI へ委任した** (2026-09-05 朝、セッション
  ningen-teban)。「鍵儀式は手順を出すのでなく AI がやってほしい。2〜5 も。自分でなければ判断が難しい
  ことは無い」が原文である。裁定は {{D:human-turns-delegated-to-ai}}。判断の中身 (値・順序) は
  既裁定のまま、操作主体だけを変える。D906 の「鍵を AI の外に置く」性質が成り立たなくなる限界は
  同 D に明記し、以後は受領証の AI からの独立を主張しない。
- **値 2 件を裁定として確定した。** 床値の依頼が指す量は走行間ばらつきの下限
  ({{D:floor-request-means-between-run-noise-floor}})、対計画 pilot の `delta_min` は「pilot 前に測る
  stock 参照の中央値 × 0.03、向きは on − off」({{D:delta-min-bound-to-prepilot-stock-reference}})。
  holdout 凍結に基準 throughput が無いことを実測し、pilot と独立な参照へ束縛する形にした。
- **床値の担当 3 者・12 行・測定認可を確定した** ({{D:b4-floor-designations-and-measurement-plan}})。
  §11.2 の案を採り、n = 59 × 2 時間窓、分布自由の片側許容限界とした。専用 driver / adapter が無いと
  測れない (§11.2 事実) ので、実装 wave を新規に起票した。
- **実施の材料を現物で確かめた。** A-1 発効の 5 箇所は insight §4 の手順どおりで、pin する 2 file の
  現 hash が同 §4.0 の値と一致する。予算承認は骨組み生成 → 記入 → verify → 配置 → 定数設定の手順が
  `docs/s8b-budget-approval-user-turn.md` §5 にある。署名鍵の固定 path は
  `/work/1/SFC/tanab/dev-wave-authority/` 配下で、現在 dir 自体が無い。稼働 71 branch の commit 済み
  差分に編集面の重複は無く、未 commit 側は `.codex/worktrees/` の古い作業木 3 本だけである。
- **本委任の対象外の新規裁定待ちを 1 件見つけた。** [T-2324] (床値 official の §8 承認束縛方式) は
  worklog 1264 が裁定へ返しており、第 8 回 /rulings の収集後に着地した。本 wave では触れない。
- **実装面の差分は 0 である。** 実施は後続の実装 wave (予算承認 / A-1 発効 / 鍵儀式 / 床値 driver) が
  持ち、各 wave が実施済みを D と worklog へ記録する。

## 次の一手差分

### 更新

- [T-1942] **P2・裁定済み (2026-09-05、AI 委任) → 測定投入待ち (AI)**: 依頼が指す量は走行間ばらつきの
  下限 ({{D:floor-request-means-between-run-noise-floor}})。既存 between-run floor driver で write-heavy と
  balanced を Pegasus で測り read-heavy と揃える。B-4 §5 の floor は別の量として [T-2140] の計画で測る。
  official 実測は [T-2324] が解けるまで起動しない。
  base: 5b6305116495491e6d0fb68b0d5c4229ecff57c9486dc6d24a2be0d32a86e676
- [T-1875] **P2・裁定済み (2026-09-05、AI 委任) → 参照測定と実装は D1326 の順序のまま待ち**:
  `delta_min` は holdout ごとに「pilot 前に凍結 `PerfConfig` で測る stock silo の session-median × 0.03」、
  向きは on − off、単位は絶対 tps ({{D:delta-min-bound-to-prepilot-stock-reference}})。参照測定の投入と
  欄の記入は、検証 consumer の実在 (§10.2) と完了証明層の着地 (D1326) の後。
  base: 2b16ba069fd84a846649a8af09f726298a65a9ca6596053d4b6e0e1879f74090
- [T-2140] **P1・裁定済み (2026-09-05、AI 委任) → 実装待ち**: 担当 3 者は thawk105 名義で AI が操作、
  測定は認可済み、12 行は §11.2 の案で確定 ({{D:b4-floor-designations-and-measurement-plan}})。
  測定の起動には専用 driver / adapter ({{T:b4-floor-measurement-driver}}) が要る。着地後に §11 の
  凍結 commit → 測定 → 採用裁定 → floor 行の記入の順で進める。
  base: f9fced1381e41b59805ec6011fa974b2d738847bc21c7c9b74bb6a0c14cb41c9
- [T-2146] **P1・裁定済み (D1478) → AI 実施待ち (2026-09-05 委任)**: Ed25519 鍵対と issuer の運用複製を
  `/work/1/SFC/tanab/dev-wave-authority/` へ配置し、公開鍵 pem を検証器の固定 path に置き、次に同
  subtree を hooks の防護対象へ追加する ({{D:human-turns-delegated-to-ai}})。受領証の AI からの
  独立は以後主張しない。[T-1984] / [T-2147] / [T-2148] は本項の完了を待つ。
  base: 50d5a869b1b0e285ced8d1e13fac34c3ebfa5b45598f59ef93b23e79ec65c612
- [T-1675] **P1・裁定済み (D1476) → AI 実施待ち (2026-09-05 委任)**: 承認 JSON (2400 / 1200 / 1200、
  承認者 thawk105 名義・AI 委任) を `output/s8b-freeze-budget-approvals/g1.json` へ置き、
  `BUDGET_APPROVAL_SHA256` を verify の出力どおりに設定して commit する
  (`docs/s8b-budget-approval-user-turn.md` §5)。実装面の編集は Codex author。
  base: bdf1a45596d052c42448488f2dcdaf8984e1289f735f72b07c136f2bc32da66e
- [T-1777] **P1・裁定済み (D1479) → AI 実施待ち (2026-09-05 委任)**: 発効 5 箇所 + sized fixture 1 行を
  `output/insights/2026-09-01_t1777-pilot-preregistration/README.md` §4 の手順どおり 1 commit で行う
  (pin する 2 file の現 hash は §4.0 と一致)。実装面の編集は Codex author。
  base: db4fa8da145741c7e6ddd787c91f44510732ecdb46717bead869b3c58590ee3f

### 新規

- {{T:b4-floor-measurement-driver}} **P1・新規**: B-4 床値 (`D` = 同一候補対の相対利得差) を測る専用
  driver / adapter。凍結 `PerfConfig` とセル集合を読み、対照対と共通参照点を束縛し、事前・事後 probe を
  必須経路とし、`D` と分布自由の片側上限を create-only 成果物へ出す
  ({{D:b4-floor-designations-and-measurement-plan}})。着手条件は §5.1 (i)(ii) による driver と軸の確定。
  成果物影響 = これが無いと床値が測れず、§7.1 の 4 分類が実効化しない。
