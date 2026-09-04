---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-04
wave: dev-wave-t2120-layer3-empty-run-acceptance
seq: 1
title: [T-2120] 層 3 の空走は受入で既に閉じていた — 3 形とも鎖の前後の hard failure で止まり、到達不能な gate は足さず「実装しない」と裁定した (docs のみ、branch worktree-dev-wave-t2120-layer3-empty-run-acceptance、実装面の差分 0)
---

## 本文

- D1460 (層 3 の空走は受入限定で閉じる) の実装 wave として着手したが、段 3 の敵対レンズが
  **受入では空走が既に 3 形とも閉じている**ことを示し、段 4 で「実装しない」と裁定した (4→7→8→9)。
  D1460 は覆していない。持ち越し項の「裁定済み → 実装待ち」は、裁定の向きが現行 tree で既に
  成立しているかを確かめずに付いた札だった。
- 受入で起こりうる空走 3 形と止まる位置。campaign 無し失敗 cell は T-2075 (D1289) の鎖後 hard failure
  (`trial_registry.py:6080-6085`)。**campaign 付き admission 失敗 cell は鎖の前**で、受入が呼ぶ
  `assert_execution_digest_chain` の腕 digest 検査 (`autonomous_trial_completeness.py:1137-1142`
  "cell admission failure projection is not exact") が止める — registered launch では必須経路で、
  producer の failure cell は descriptor・campaign identity・診断 key を持つため exact fallback と
  key 集合が異なる。zero-cell は measurement-target prepass (`trial_registry.py:5557-5561`)。
- **親 brief は結論 (3 形とも拒否) は当てたが、campaign 付き失敗 cell の因果を誤っていた。**
  「鎖まで到達し、後段の file 実在 post-check で止まる」と書いたが、実際は鎖に到達しない。
  段 2 plan の主案 (鎖が実体検証済み campaign を返し受入が全件一致を要求) も対案 (述語型) も、
  この誤りの上に立っており、現行の受入では 1 度も発火しない恒真 gate になる。変更前受理・変更後拒否の
  report 集合は空。到達させるために手前の腕 digest 検査を緩めることは、producer と standalone が
  共有する verifier の変更になり D1460 の受入限定を越えるので採らない。
- brief の誤りは他に 2 点。zero-cell の最初の拒否位置 (`:6015-6018` でなく prepass `:5557-5561`)、
  「2 production module を bytes で pin」(実際は `paper_story_a1_paired.py:167-173` に
  `trial_registry.py` だけ、方式は固定 digest でなく実行時 HEAD 追随)。いずれも段 2 plan が現物で補正した。
- 段 3 は 2 レンズ (どちらも `gpt-5.6-sol`、read-only、xhigh)。A (正しさ境界・恒真性) 所見 7 =
  real 5 / refuted 2、B (整合・実効性) 所見 8 = real 6 / refuted 2。最重要は A の所見 1 (鎖前の拒否)。
  B の所見 1 (plan の負例 fixture が producer 実在形にならない) は A1 の傍証になった。
- 編集面重複 (DW-O20): worktree 70 root 全走査 (unreadable 0)。T-524 が `trial_registry.py` を未 commit で
  編集中だったが merge-base `c6a94ec99` 基準で鎖区間 6021〜6096 は不変、hunk は `+6193` / `+6360` / `+6347`。
  実装面の差分ゼロなので統合対象は無い。
- 実装面の差分 0 なので変異 matrix は免除、Codex author は要さない。受入全走は本 commit を tip として
  `tools/dev_wave_wait.py acceptance` で投入する。その結果は本エントリには入らず、受入 receipt
  (job dir) と land の記録が正本である (受入後に commit を足すと land できないため)。
- 一次資料 (plan・2 レンズ・裁定の逐語): `output/insights/2026-09-04_t2120-layer3-empty-run-acceptance/`。
- エージェント工数: codex 子 3 本 (plan 1、consult 2)、実装子・fix 子・レビュー子 0。

## 次の一手差分

### 完了

- [T-2120] 受入の層 3 空走は 3 形とも既に閉じており (campaign 無し失敗 = T-2075 の鎖後 hard failure、
  campaign 付き admission 失敗 = 鎖前の arm-digest-chain、zero-cell = measurement-target prepass)、
  到達不能な gate を足さず「実装しない」と裁定した。D1460 は現行 tree で成立済み。
  一次資料は `output/insights/2026-09-04_t2120-layer3-empty-run-acceptance/`。
  remaining: none
  base: 2a46970f24993ac6620db0500b50ccd881937869f81f6223a22a855690264524

### 新規

- {{T:arm-digest-failure-projection-acceptance-test}} **P3・新規 (2026-09-04 [T-2120] 段 3 レンズ A の実測)**:
  受入で campaign 付き admission 失敗 cell を実際に止めている `assert_execution_digest_chain` の拒否
  "cell admission failure projection is not exact" (`autonomous_trial_completeness.py:1137-1142`) には、
  受入・単体いずれのテストも無い (`grep -rn "projection is not exact" orchestrator/tests/` 0 件)。
  stub 無しの producer 実在形 fixture (診断 key・critic count・accounting を含む) で固定するかを裁定する。
  既存機構の被覆追加であり空走の閉鎖 (D1460) とは別の変更単位。一次資料は
  `output/insights/2026-09-04_t2120-layer3-empty-run-acceptance/`。
