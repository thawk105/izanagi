---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-05
wave: dev-wave-t524-slot-experiment-unit
seq: 1
title: [T-524] 実験単位を slot 組へ改め、下流の受領証検証器で全 slot 消費を強制した (コード + テスト、branch worktree-dev-wave-t524-slot-experiment-unit、変異 matrix = baseline PASSED・KILLED 5・SURVIVED 0・MISMATCH 0・期待 node 完全一致 5/5)
---

## 本文

D1269 の最小形を実装した。設計判断は {{D:slot-unit-downstream-enforcement}} と
{{D:mutation-must-target-the-effective-gate}}、実施記録と逐語は
`output/insights/2026-09-05_t524-slot-experiment-unit/`。

- **親の段 1 brief の中心 2 前提は、段 2 が現物で反証した。** (P1)「承認 artifact = 条件凍結 artifact」は誤りで、
  条件凍結は世代番号の出所にすぎず、全 slot と個数を固定しているのは attempt registry genesis である。
  (P2)「別 manifest を N 個登録する経路が空いている」も誤りで、canonical path の create-only と
  全 ref 第二 root 検査により path 面・commit 面は変更前から閉じていた。**残っていたのは世代の意味束縛と、
  下流に検査が一切ないことの 2 点だけである。**
- **段 3 の 2 レンズが、当初プランの中心設計を否定した。** series key へ世代を入れる案は受理集合を
  広げる。発行側の全列挙 helper は既存の合成検査と重複し変異を帰属できない。両方とも採用せず、
  重心を下流の検証器へ移した ({{D:mutation-must-target-the-effective-gate}})。
- **段 6 の 2 レンズが blocker 2 件を出した。** (i) 下流の消費入口が v1〜v4 を同じ verified capability へ
  通すため、旧 schema を選ぶだけで新検査を迂回できた。**追加したテスト自身が v4 へ落とした receipt を
  verified にしていた。** (ii) 検証器が registry の自己整合性しか見ず、事前固定を証明していなかった。
  さらに (iii) 下流の履歴検査が HEAD ancestry だけで別 ref の第二 root を見逃していた。全件 real と裁定し、
  **発行側に既に在る gate を下流からも使う**形で閉じた (新機構は作っていない)。
- **fix は 3 巡かかった。** 1 巡目は焦点走の赤 5 件 (揮発分類の漏れと厳密 pin の追随、production 変更 0)。
  2 巡目は上記 blocker 対処で 13 件赤。親が現物で原因を特定した — attempt row は
  `prereg_content_commit` を持つのに receipt の `prereg_commit` と比較していた。**別種の commit である。**
  3 巡目で受領証へ内容 commit と発効 commit を既存名で束縛して閉じた。
- **子 4 者すべてがテストを実走できなかった。** 実装子・fix 子 3 者とも Pegasus への投入が
  `qstat -Q` preflight rc=1 / rc=16 / `child_started=false` で失敗した。全員が「実装済み・未実走」と
  正直に申告し、緑とは報告しなかった。**テストの実測はすべて親が行った** (焦点走 4 回)。
- **`not-consumed` を含む正例は作れないと確定した。** `report_sha256=null` が必須である一方、
  acceptance は全 report の hash 一致を無条件に要求する。到達させるには既存契約を緩める必要があるため、
  規律 2 により緩めず正例から外した。段 3 レビューが親の (P3) の該当部分を反証した形である。
- **変異 matrix は M3 を 2 つに割って登録した。** 段 6 レビュー B が「projection 再照合だけを
  無効化しても赤くなるテストが無い」と実測で示したためである。probe で観測 node を集め、
  本走は期待 node の完全集合で回した。**M3a の赤は意図した拒否ではなく `IndexError` 経由**である
  (同じ 1 行が終端欠落の拒否と添字の安全を兼ねる)。受理側へは倒れず fail-closed のままだが、
  理由が意図どおりでないことを記録する。
- **main 取り込みの合成監査で、併合後の未 commit 走行が `contract-loader-drift` で 21 件赤になった。**
  HEAD blob 束縛による既知の型で、実装の回帰ではない。merge を commit して再走し 758 passed / 0 failed。
  Codex `role=author` が合成監査と merge message を起草し、監査中に main がさらに進んでいたことも
  併せて報告した。

## 次の一手差分

### 完了

- [T-524] 実験単位を slot 組へ改める最小形を実装した。承認側は attempt registry genesis の
  schema v3 と root 単一世代、下流側は receipt v5 の独立再照合と全 unit 消費検査である。
  remaining: none
  base: 0798d60a988f3289652105985e6cf029009c16f5fad545ce2bc3170a22844f23

### 新規

- {{T:s8c-formal-genesis-producer}} **P2・新規 (段 6 レビュー B、親が現物で裏取り)**:
  `create_attempt_registry_genesis` の caller は現在すべてテストで、production は 0 件である。
  CLI にも `register` と `accept` しかない。**正式系列は out-of-band の Python 呼び出し無しには
  開始できない。** 本 wave の scope 外として実装しなかったが、8c の正式走に必要な実在の欠落である。
- {{T:s8c-notconsumed-receipt-carry}} **P3・新規 (段 6 レビュー A / B が独立に指摘)**:
  `not-consumed` は `report_sha256=null` が必須で、acceptance は全 report の hash 一致を
  無条件に要求するため、outer receipt へ運べない。運ぶかどうかは既存の report-count / status /
  hash 契約の改訂を伴うのでユーザー裁定が要る。運ばない場合、失敗側だけを台帳から落とす経路が
  受領証の層に残るかを別途評価する。
- {{T:s8c-cross-clone-best-of-n}} **P3・新規 (段 3 / 段 6 の 4 レンズすべてが一致)**:
  独立 clone / repository を跨ぐ best-of-N は、同一 repository 内の全 ref 走査では閉じない。
  閉じるには全世代を一元管理する一般化が要り、D1269 が明示的に却下している。
  実験の主張にとってこの経路を閉じる必要があるかを裁定する。
- {{T:s8c-approval-authority-semantics}} **P3・新規 (段 2 / 段 3 / 段 6 が一致)**:
  D1269 の「承認 artifact」を人間の承認権限の意味で読むなら現行 8c 設計と衝突する。
  8c は承認 record も active pointer も採らず、receipt は approval authority 不在を必須にする。
  本 wave は「P/C で固定された事前登録 artifact」と読んだ。読み替えるなら発効設計の変更になる。
