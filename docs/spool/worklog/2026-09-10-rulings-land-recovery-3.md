---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: rulings-land-recovery
seq: 3
title: rulings の main 直接commitで残した未fold記録を復旧し、共通プロンプトの終端を是正する (docsのみ)
---

## 本文

- ユーザーは未land回答に「そしたら他のdev-waveが困るのでは？」と指摘し、さらに
  「自己改善プロンプトもよろしく。二度とこんなイージーミスするな」と依頼した。
- 前セッションは `32603d385` をmainへ直接commitして終わった。文書検査とprovenance監査が
  通っていても、受入・land・foldの代用にはならない。失敗は {{F:rulings-commit-before-land}}。
- mainを巻き戻さず同commitを含む専用worktreeから復旧する。全50項の裁定内容と68IDの更新は
  変えず、今回の記録を既存2fragmentと同じ正規landでfoldする。
- 自己改善は {{D:rulings-land-terminal}}。共通commandの冒頭へ記録の着地導線と完了条件を統合。
  5599→5608 bytesで既存5623-byte予算内。新しいgate・test・権限・機械設定は足していない。
- 前のworklogにある「foldは未実施」は当該記録時点の事実である。
  本復旧の完了判定は会話の宣言でなく、landの成功応答・FOLDED receipt・canonical反映と
  未fold fragment不在の確認で行う。受入の証拠はrepo外の
  `dev-wave-jobs/dev-wave-rulings-land-recovery/` に保存する。
- 実装面の差分はゼロで、変異matrixは対象外。正式受入全走は省略しない。
  裁定に含まれる本番実装や性能測定へは本復旧の範囲を広げない。
- 正式受入1は22463 passed / 68 skippedでchild-green。landの初回argvはmain cwdとlease環境
  指定欠落でrc22になり、wave cwdと既定lease dirを明示して是正した (main変更なし)。
  その後のlandはF672再発でrc31になった。他waveの登録pathのstrict解決がEINTRで中断した。
  mainは32603d385のままで、leaseはtoolが解放した。pathの復旧を読取で確認し、
  非再試行の同requestを繰り返さず、既存手順に従って新しい受入2を取得して再試行する。

## 次の一手差分

### carry

- [T-2581]
