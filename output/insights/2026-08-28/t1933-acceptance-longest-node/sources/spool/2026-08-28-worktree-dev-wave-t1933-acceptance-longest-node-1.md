---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: worktree-dev-wave-t1933-acceptance-longest-node
seq: 1
title: [T-1933] 現行mainで最長node短縮を再裁定し、安全かつ実効的な共有境界なしとして0 byteで閉じた (docs-only、branch worktree-dev-wave-t1933-acceptance-longest-node、変異matrix免除)
---

## 本文

- 前waveのoptional rules注入案とplan/consultを流用せず、main現物から段1〜4を再実行した。T-1934は実装面0 byteで受入green後のstale-main停止、T-1938の稼働実体なしで、対象2 test fileとの直接overlapは0だった。
- duration ledgerの全体最長はscope外140秒へ移っていた。固定4 nodeの変更前baselineはPegasus request `954274.nqsv`、child rc=0、4 passed / 147.55秒。node順durationはfloor snapshot 4.18秒、T-080 single-defect 86.57秒、draft-finalize 51.93秒、T-080 snapshot 2.61秒で、ledgerのsnapshot 79/50秒は再現しなかった。
- 段2初回はbaseline追記とのTOCTOUで無効化し、immutable入力から再実行した。plan v2と段3の正しさ・実効性2レンズはすべてCodex出力検査greenで、実装0 byteを支持した。
- 安全化可能性と実益を分離した。無変更区間snapshot再利用やT-080分岐前prefixは構造候補だが、前者の効果上限は固定slice6.79秒の一部、後者とCoW cloneは安全境界・効果が未証明で、production履歴走査も残る。D104の跨worker/session cache、optional rules、値源共有、grouping、case/assertion変更は再導入しなかった。
- 段4は「scope内で安全かつ実効的な最長短縮案なし」と裁定した。「最長短縮を達成」とは主張しない。実装面0 byteなので段5/6と変異matrixは免除し、受理集合・assertion・独立oracle・proof chainを不変に保った。
- 一次資料は `output/insights/2026-08-28_t1933-acceptance-longest-node/`。baseline前のstale orphan holdはrequest `953511.nqsv`不在とclean HEADを確認後、回復契約どおり互換markerとrequest別ledgerだけを削除した。テスト未起動の2試行はgreenや性能値に数えていない。
- 段8は、T-1934開始inventoryが既存T-1933 ownerを落としたnear missをF606の再発へroutingした。既存恒久対応がrepo外job directoryを含む走査を既に要求するため、dev-wave referenceの重複強化は行わなかった。

## 次の一手差分

### 完了

- [T-1933] 現行mainでscope内候補を再検証し、安全性と実益を同時に満たす共有境界なしとして実装0 byteで終端した。
  remaining: none
  base: 9bbe0554008ba25e21f3643030def27979f83361e0b704685aa96986863df9db
