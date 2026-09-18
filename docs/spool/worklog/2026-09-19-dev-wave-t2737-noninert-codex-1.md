---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2737-noninert-codex
seq: 1
title: [T-2737] D2148項4のSS2PL依存準備と非inert差分を接続し、phase1と計器保存を検証した
---

## 本文

- ユーザー指定のD2148項4だけを実装。着手時local main `7975385b5` からfresh worktreeを作り、
  稼働process・handoff・旧SS2PL作業木の対象差分に重複がないことを確認した。
  D95の隔離Codex authorへ実装を委任し、親は実装面を直接編集していない。
- 一次記録は `output/insights/2026-09-19/t2737-noninert-implementation/README.md`。
  patch a〜dとe維持、既存helperの関門前接続まで。inert target、軸従属、比較条件、abort所有権は不変。
  controls全体は未成立であり、Sのstock認証やruntime meaningの成立を主張しない。
- 最終実probe job9293.nqsvは1 passed (113.32秒、Elapse118秒)。BACK_OFF=1のphase1をpristineから
  production build_targetで通し、4 supply成功・meaning未宣言・raw admissionを確認した。
  S拒否を維持し、plain SのWFG不在3TUとabort所有を確認。IMPL0/1の既存C++テストと共有consumerも実build。
  旧新4TUの全200行17ハンクを独立に比較し、計器呼出し・引数・制御構造の保存を確認した。
- plan1・consult2・author1・fix2・review2・focus1。reviewの新設文字列テスト2本は取り消し、
  元のテストを保存した。焦点reviewはGO。最終関連Pythonテスト103 passed (3.77秒)。
  docs・Codex設定・diff検査は通過。anchor全史provenanceは11582件、新規違反なし・既知56件を区別した。
- 変異は既存harnessでbaseline緑の後、5 KILLED・1 SURVIVEDを確認。M1〜M4は狙った依存準備／閉包／argv差で拒否。
  M5は自動probeでは通るが、同じ全TU比較でpublish_waitの欠落1ハンクを検出・拒否した。
  M6はWFG=0のcompileで拒否され、不在validatorのkillとは数えない。復元・共有木の前後一致・teardownを確認。
  製品anchorは `0bd0895da`、検証専用private anchorは `e9409610e`。実装本体は同一で、後者のprobe/inputはmainへ入れない。
- 初回probeは通常dispatchが専用環境変数を転送せずKeyErrorで停止した。製品の転送規則を変えず、
  既存generic経由の確認とsidecar入力の通常dispatchで閉じた。private cloneの先行provenanceはcommitと重なり
  HEAD変更でrc2、commit固定後の全史再監査は11583件・新規違反なしだった。失敗走を緑へ読み替えていない。
- 受入全走は記録commit時点で未実施。専用handoffと原ログは
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2737-noninert-codex/` に保持する。
  dev-wave改善候補は「なし」。改善実装・次wave・新しいgate・一般化は追加しない。

## 次の一手差分

### 完了

- [T-2737] D2148項4のhelper接続と非inert局所修正、phase1条件・計器呼出し保存の検証を完了した。controls全体は未成立のまま、inert側の契約は変更しない。
  remaining: none
  base: 26025c5cd7c51c3e144cff72b3a2a31863e40953e922a9a17833ccb705e5c8a8
