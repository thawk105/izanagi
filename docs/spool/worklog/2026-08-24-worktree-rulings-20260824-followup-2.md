---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-24
wave: worktree-rulings-20260824-followup
seq: 2
title: rulings 推奨8件を裁定し、既存D730を文書予算残件へ適用した
---

## 本文

- ユーザー裁定「推奨通りで。main landまで頼む」を、直前の `$rulings all 説明付き` が提示した
  8件すべてへの採用として記録した。新しい設計判断は
  {{D:t139-pilot-remains-forbidden-until-operational-closure}}、
  {{D:shard-receipt-completeness-deferral-maintained}}、
  {{D:trace0-identity-gaps-close-before-formal-measurement}}、
  {{D:post-fold-targeted-preland-validation}}、
  {{D:codex-skill-real-repo-growth-hold-maintained}}、
  {{D:cleanup-branches-codex-safety-reductions-maintained}}。
- 文書予算の裁定待ち3 ID と、未 land cleanup branch の未採番候補には D730 を適用した。
  一般予算を引き上げず、別種の実害を「同型3例」と合算せず、例外基準を満たさない項を終端する。
  D730 の例外基準を満たす既存項の所有は T-1595 が継続する。
- local main は裁定時点のローカル追跡情報で `origin/main` より103 commit先行していた。
  ユーザーは通常の非 force push を行う推奨も採用したが、push は AI が行わない境界を維持し、
  local main land 後の人間アクションとして残す。
- T-1477 の enforcement closure 批准追記は既に承認済みで、今回の裁定対象ではない。
  AI が批准を代行しない境界と人間アクション待ちは不変である。
- 記録 commit `ba966c9c` に対し、fold 焦点走は166 passed、Codex agent検査成功、docs検査は
  違反なし、全史 provenance 監査は新規違反なし (既知53件) だった。canonical acceptance 1回目は
  tested main `618c9236` / tested tip `ba966c9c` で `child-green`、赤0・flake0。
  本 fragment へ結果を吸収して専用 handoff を削除し、最終tipを再度 acceptance へ送る。

## 次の一手差分

### 完了

- [T-1583] D730 を適用し、一般予算引き上げ・memory の正式逃がし先化・一括圧縮を行わない。
  5件の候補は同型実害3例の例外を満たさないため、本項の残件はない。
  remaining: none
  base: c868a90001c0d4a617c2c5dd3d217d21883c314e0494cc9320fc7d25400a4168
- [T-1591] D730 を適用する。3件は別種の手順知見であり同型3例には数えず、一般予算を上げずに終端する。
  D730 の例外を満たす個別項は T-1595 が所有する。
  remaining: none
  base: 5678cfe44d45ce37dcb168647a9cbe363806ad79394cb960520bb4a365df14c2
- [T-1613] `test_real_repo_clean` の growth hold を維持し、Skill一致は必須の `check_docs.py` で担保する。
  追加実装は行わない。
  remaining: none
  base: 0ea5e05fdd453129874d2405930e88c62ce9de23ef75cc9d08999121eed08a45
- [T-1616] Codex cleanup-branches の安全縮退7面を維持し、Claude版と同じ削除結果へ揃えない。
  追加実装は行わない。
  remaining: none
  base: e436e37b3b2160b550a93d6c8d68a44625f10cda5d402ee4a2861b674a277596
- [T-1617] D730 を適用する。H2見出しは実害1例、変異中のtree並行読取は2例で例外基準を満たさず、
  一般予算を引き上げずに終端する。
  remaining: none
  base: bb2984d127346439a7546401a69a76bda6ec3108caa376ee30c68b8652714aaf

### 更新

- [T-139] **P2・裁定済み / pilot禁止維持**: private gate は実装済みだが、sealed series / receipt-set、
  production consumer、公開API、PBS driver、collectorを閉じてから pilot 解禁を再提示する。
  本走禁止と公表昇格禁止は維持する。決定 = {{D:t139-pilot-remains-forbidden-until-operational-closure}}。
  base: 8c1e14120e568d0fdcfea015bc986d9b1a6819ac084855fce1d17456bc2799ab
- [T-1515] **P3・裁定済み / T-1570と同時見送り**: red-check receipt の schema 変更は行わない。
  分割取りこぼしまたは空結果受理の実害1件で T-1570 と同時に再訪する。
  決定 = {{D:shard-receipt-completeness-deferral-maintained}}。
  base: 3f3eac0c76f8b846f641b180ab37b7b088948a52d4b293aafc2e4ae063fc93de
- [T-1570] **P2・裁定済み / 見送り維持**: 既定 K=2 である事実を踏まえても、受領証レベルの
  shard完全性証明は実害が出るまで作らない。実行器内部の完全性検査は維持する。
  決定 = {{D:shard-receipt-completeness-deferral-maintained}}。
  base: 14d7e9512587cc74958524eac1ca7b4767c318a6f4494e19f5d3422e56913a0d
- [T-1584] **P1・裁定済み → 正式TRACE=0計測前の実装待ち**: 間接供給・macro include・
  report自己矛盾の3穴を同一waveで修理し、各穴の負の対照を置く。
  決定 = {{D:trace0-identity-gaps-close-before-formal-measurement}}。
  base: c8645a0ace276d1d0f5c3897afecb9739d2ba6885c9f65b5211d447d9bf24e9b
- [T-1600] **P1・裁定済み → 実装待ち**: fold dry-run適用後の隔離treeへ、実コーパス依存テストだけを
  land前に掛ける。全走を2回にしない。決定 = {{D:post-fold-targeted-preland-validation}}。
  base: 7a4a0f5a55a33cd14ac1080167e7aa558ad6a7f8be9bf2c02a692b0512b11be0
