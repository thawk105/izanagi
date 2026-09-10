---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2579-recovery
seq: 1
title: [T-2579] 承認済みmodule fixtureと既存reader登録を限定回収する (branch worktree-dev-wave-t2579-recovery)
---

## 本文

- ユーザー指定D1936項43に従い、旧559bcbc29の実装3fileだけを監査回収した。旧worktree途中mergeは非接触。
  T-2273はt1259/conftestを所有外に固定済みで、他の受入関連waveにも対象3fileの未land差分はなかった。
- 別Codex authorの5hunkは回収元限定patchとbyte一致。独立plan/相談2本/review2本はrc0・出力検査rc0。
  現行schedulerでは全worker合計1回は保証されないという指摘を採用し、説明を訂正した。
  timeout解消・速度改善は未証明、CC合成の新前提にはしない。新gate/検査/台帳/一般化の実装は追加しなかった。
- 親のT1259単独走は51passed。serialization単独は遅延importが既存site中立fixtureより後になり、
  computeのlock不一致、node単独のlogin拒否を観測した。追加登録比較は通っており本変更の到達経路外。
  テスト・期待・productionを変えず既存site_policyを先読みし、56passed/1既存skipへ戻った。
  skipは既存opt-in成長testで、全件実走とは呼ばない。正式受入に先読みoptionを追加しない。
- 分類consumer3fileは271passed。すべてtools/run_tests.py経由。検査時間は性能改善の証拠にしない。
- 固定実装anchorで既存harnessを走らせ、baseline緑、3変異すべてKILLED・期待1node一致。
  R1拒否・detached負例受理・登録1件欠落の失敗本文を確認し、production含む復元とclean状態を確認した。
- 証拠は `output/insights/2026-09-10_t2579-recovery/README.md`。check_docs/check_codex_agents rc0。
  anchor全史provenanceは9444件新規違反なし（既知56件）。記録後再走は52passed。
  正式acceptance-3は22591passed/68skipped・child-green。受領証は同insightのacceptance-3.json。
  その後の並行main前進を保持し、文書競合を親が解消したため、最終統合状態の受入は再走する。
- dev-wave改善候補は、file単独走の既存site中立化とimport順序をDW-O18で明確にする案。
  専用handoffへ記録し、改善実装・次wave起動は行わない。pushは人間手番。

## 次の一手差分

### 完了

- [T-2579] D1936項43の既存実装を現行mainへ限定回収し、正負検査・独立レビュー・変異検査を完了した。
  remaining: none
  base: f10c2518c772a2ab784fec751f4b6cca03b03fd948c05898c71bcf01d04df10a
