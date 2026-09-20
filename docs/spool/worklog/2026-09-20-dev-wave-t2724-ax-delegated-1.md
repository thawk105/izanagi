---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2724-ax-delegated
seq: 1
title: [T-2724] 凍結 v2 g1 の承認 A と active pointer X を AI が作り (13:2x 裁定、D2120 項 2 (b)・D2174 項 4 を supersede)、批准 attestation を「AI-Agent trailer ちょうど 1 行」へ改めて発効させた — 批准 loader は成功、P3 の全 gate 受理は launch validation の既存不整合 2 件で未達 (コード + docs、branch worktree-dev-wave-t2724-ax-delegated)
---

## 本文

- **ユーザー裁定 2026-09-20 13:2x** (逐語は一次資料 `verbatim/ruling-13-2x.md`): A/X は AI が作る。10:2x の控え (hook 解除 + CLI +
  構造化 ≥1) より後で狭い。同控えを引数にした先行 job 9f2d502a は着手前に譲って停止 (13:37〜13:43)。裁定の記録は {{D:t2724-ax-delegated}}。
- **成果:** 実装 commit `4114cf51b` (批准側 `_assert_user_commit` を「非 merge・AI-Agent trailer ちょうど 1 行 (逐語 none または規約適合の
  構造化 trailer)・H ancestry」へ、Codex author) → 承認 A `a3bf67a8c` → active pointer X `70e87c9c9` (record は Codex author が README §5
  手順 2/4 の形で書き、親が機械的に commit、trailer は Codex author 1 行のみ) → 帰結 commit `ca3907e57` (B-10 pin を 22 file の
  `92099c87…` へ、held 6 node の真値、tmp repo 補完 2 本) → 段 6 fix commit (standalone gate の翻訳を tmp repo で復元)。
  README §5 手順 6 の批准 loader は wave 木で成功 (JSON 1 行、generation 1、sha `7e1114…`)。**ユーザーの検証 (4) のうち loader は成立。**
- **新事実 (P3 未達):** runbook §2 P3 は g1 path で `freeze-ratify:` が消える一方、full launch validation が `journal-state-invalid`
  (`_JOURNAL_KEYS` に official run の journal event `reservation-preflight` が無い) で止まり `allowed: false`。その後ろに段階 6 の lineage
  (result 導入集合 == {G} だが実導入は X1') も控える (相談 B-2、静的)。いずれも A/X が生む差ではない既存の不整合で、launch admission
  (W-4/W-5、proof chain、規律 2 の射程) = ユーザー scope 外として本 wave では触れず、次 wave (AI 手番、設計択一 α/β/γ、推奨 α) に残す。
  v1 path は A/X 前後で exact 一致 (既知 4 拒否)。runbook §2 P2 の「2 passed」は現物 5 関数 (docs 訂正)。
- **段 3 相談 2 本** (sol / luna、rc=0): real = A-6 / A-7 / A-9 / A-12、B-1 / B-2 / B-4 / B-5 / B-6 / B-7 / B-10 / B-12 (すべて採用、B-2 は
  scope 外)。refuted = A-1〜3 / A-5 / A-13、B-8 / B-9。**段 6 レビュー 2 本** (rc=0): must-fix = RA-1 (standalone `gate_check` の検出力
  復元 → fix 子)、RB-1 / RB-2 / RB-3 / RB-8 (記録側 → 親が修正)。nit = RA-8 (README §5 例の注記、commit message の「13 値」は実物 15 値、
  docstring)。refuted = RA-2〜RA-7、RB-4〜RB-6。一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md`。
- **実測:** 焦点走 (dispatch) S1 143 passed、held 6 + 新 2 (token 付き診断) 8 passed、consumer 6 file 503 passed / 9 skipped、
  fix1 の焦点走と変異 matrix (m1〜m15 / p1 / p2 / n1、独立 clone) と pin 負例 4 件・受入全走・全史 provenance 監査は一次資料 §6。
  held 6 node の hold 登録は不変 (通常受入の所要は未検証、RB-3)。
- 工数: codex 子 8 本 (plan 1、consult 2、author 3、review 2) + fix 1。計算ノード dispatch: 焦点走 5、変異 2 系列。
- 素材: g1 の批准は AI 委任で発効した (人間 commit ではない)。論文での呼称は本決定の対象外 (10:2x の控えに「AI が自己承認した世代」の記録)。

## 次の一手差分

### 更新

- [T-2724] **P1・A/X は着地 (AI 委任)、批准 loader は成功。次は launch validation の既存不整合 2 件の解消 (AI 手番、設計択一) →
  runbook §2 P3 の全 gate 受理 → W-4 spec 承認 (T-750 P-1、ユーザー手番) → W-5**: (1) `s8b_ratified_freeze._JOURNAL_KEYS` に official
  run の journal event `reservation-preflight` (producer `s8b_floor_campaign.py` 7620 行付近、`floor_liveness.py` が読む) の key 集合を
  足す (決定台帳 25569 行付近の allowlist 方式)。(2) `_launch_validate` 段階 6 (result の導入集合 == {G}) と D2077 の一方向順序
  (result を commit → 候補 → G、V1a) の矛盾: α 段階 6 を「chain の祖先で cert C より後」へ改める (推奨) / β G を result と同 commit で
  作り直す (D2120 項 2 (b) の再裁定) / γ floor_source へ導入条件を課さない — 次 wave の 2 レンズ相談で決める。解消後に
  `_ACTIVATED_G1_REFUSALS` (held 6 node) を再実測して更新する。一次資料 `output/insights/2026-09-20/t2724-ax-delegated/README.md` §5。
  base: 0c6f498768ca9812baacfea0db13e32e92cfe22f84dcf8dcaec264b666b23923
- [T-750] **P2・裁定済み・実装済み → 実凍結 (g1) は 2026-09-20 に AI 委任で発効 (A `a3bf67a8c` / X `70e87c9c9`)。W-4 (spec 承認、
  P-1) の起動前提「P3 gate-check が active 世代で受理」は launch validation の既存不整合 2 件の解消待ち** (詳細は [T-2724])。
  package の P-1 / P-3 の残余は別管理のまま。
  base: 7ccb731998217f07c5bafb9263e267c30653da245120ba3c3ec681842c9dcb83

### 新規

- {{T:launch-validate-journal-lineage}} **P1・新規 (AI 手番)**: 凍結 v2 g1 の full launch validation を通す — `_JOURNAL_KEYS` の
  `reservation-preflight` 追随と、段階 6 lineage の設計択一 (α/β/γ) を 2 レンズ相談で決めて Codex author で実装し、runbook §2 P3 を
  g1 path で再実測する (受理集合の変更 = 規律 2 の射程、敵対レビュー + 変異必須)。前提資料は [T-2724] の一次資料 §5。
