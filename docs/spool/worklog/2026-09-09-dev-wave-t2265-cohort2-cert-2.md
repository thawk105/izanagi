---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-09
wave: dev-wave-t2265-cohort2-cert
seq: 2
title: [T-2265] cohort 2 の seed 別実行体 10 本と 24 スレッド条件を認証し、費用対効果を理由にユーザー裁定で打ち切った (コード + 実測 + docs、branch worktree-dev-wave-t2265-cohort2-cert、変異 9/10 KILLED + 登録 SURVIVED 1・期待 node 完全一致)
---

## 本文

- ユーザーが 312 job の認証走行を指示した。これは {{D:cert-seed-thread-axes-cost-only-supersede}} の
  とおり D1852 の費用判断だけを上書きするものとして扱った。
- **285 件 certified / 11 group 受領証発行まで進んだ時点で、ユーザーが費用対効果を理由に停止を指示した。**
  親は次を根拠に同意し、残作業を投入しなかった。
  - 認証した実行体は試験データを出した実行体ではない
    ({{D:certified-build-is-not-the-trial-build}})。完走しても「cohort 2 を認証した」とは書けない。
  - backoff は Silo の validation 経路に触れないので、13 通りの設定を認証しても第三者が受け取る
    保証は 1 通りとほとんど変わらない。同じプロトコルを違うスケジュールで再サンプリングする形になる。
  - 効果量 (推奨方向の実用優越 +4.900%) に対して 312 job は釣り合わない (絶対規律 4)。
  - 停止手順: 待ち手を停止し、queue の自分の認証 job 19 件を qdel。停止後の実測でキュー内 0 件。
    波 3 (policy 2 x 12 seed x 24 threads、288 job) は 1 件も投入していない。
- **段 3 の実行可能性レンズが、投入前に実機 blocker を見つけた。** 認証は束縛する performance
  成果物の `repo_head` がその走行の HEAD と一致することを要求する。前 wave の成果物は別 commit で、
  そのまま投入すれば 312 job 全件が build 前に落ちた。既存検査は緩めず、本 wave の commit で
  trace-disabled の束縛用成果物を 12 本作り直して解いた。投入前に login node で offline に
  identity を確認している。
- **段 6 のレビューが、親が書いた投入 script の欠陥 4 件を見つけた。** 特に performance 走行の
  grid に `none` と stock control が必須である点を親が落としており、そのままなら 12 job 全部が
  落ちていた。他に古い成果物の再利用、pilot の引数契約、再投入時の結果分類。
- **段 4 裁定 R6(a) を段 6 で撤回した** ({{D:no-unmeasured-predicate-on-build-identity}})。
  実測が撤回の正しさを裏づけた — 1 group 24 row の `binary_sha256` はすべて異なる。
- **変異 probe が二層 mask を暴いた。** p2 seed の membership 検査が `CertificationAxes` と
  `_certification_contract` の両方にあり、片方だけの変異では殺せなかった。実効 gate へ再照準し、
  片側と両層同時の 2 通りを本走で KILLED 確認した。初回の SURVIVED は本走 spec にも残してある。
- 逐語・受領証集計・変異 spec / report は `output/insights/2026-09-09_t2265-cohort2-cert/`。

## 次の一手差分

### 更新

- [T-2265] **P1**: 直列性認証の受理形へ cell 別 thread 閉表と policy 2 の compile seed 閉表を
  足し、**11 group を認証した** — policy 1 の 24 threads 1 group と policy 2 の seed 別実行体
  10 本 (48 threads)。いずれも 24/24 certified serializable・anomaly 0 件・group receipt complete。
  11 group の genome はすべて異なり、seed が実際に効いていることを確認した。
  **ただし認証した実行体は cohort 2 が走らせた実行体ではない** — 認証は `BACKOFF_TRACE=0` かつ
  terminal define なしの build、試験は計装ありの build である
  ({{D:certified-build-is-not-the-trial-build}})。したがって「cohort 2 を認証した」とは書けない。
  費用対効果を理由にユーザーが打ち切ったので、**未認証のまま残るのは** policy 2 の seed slot
  10 / 11 (48 threads)、policy 2 の 24 threads 全 12 seed、policy 0 の全条件である。
  次に正しさへ資源を使うなら、サンプルを増やす方向ではなく
  {{T:backoff-patch-validation-isolation}} を勧める。
  D1515 の再訪条件はなお未充足。
  base: 4945d307aebfa2d8fd3d4040b593a0526a070051eb27c8dc291c61fd9f5485b9

### 新規

- {{T:backoff-patch-validation-isolation}} **P1・新規**: backoff の patch が Silo の validation
  経路に触れていないことをコードで示す。認証のサンプルを増やすより、第三者にとっての保証が強く、
  計算 job を要しない。触れていない場合は既存の 1 group 認証で足りる根拠になり、
  触れている場合は認証の対象をそこへ絞れる。
- {{T:certify-instrumented-genome}} **P2・新規**: 計装入り genome
  (`BACKOFF_TRACE=1` + terminal define) を直列性認証の対象にできるようにする。
  受理形・claim・絶対規律 1 の解釈すべてに関わるため、着手前にユーザー裁定を要する。
  これを閉じない限り、認証の射程は常に「試験の隣」である
  ({{D:certified-build-is-not-the-trial-build}})。
