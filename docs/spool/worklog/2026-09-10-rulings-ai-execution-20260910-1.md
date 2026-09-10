---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: rulings-ai-execution-20260910
seq: 1
title: rulings 項1・2の人間専任を解除し、正式比較と実行場所分類を AI 担当へ移す (docsのみ、branch worktree-rulings-ai-execution-20260910)
---

## 本文

- ユーザー発話は「1, 2は私がわざわざやることではないと思う」。直前の索引の
  balanced 正式比較と実行場所分類の実測について、人間専任解除・AI 実行委任として受領した。
- 決定は {{D:ai-execution-delegation}}。D1936項48/49とD1677/D233決定4の担当制限を名指しで変更する。
  正式比較の認可、事前登録、資源・正しさの条件は保つ。測定本体の完了とは記録しない。
- この変更は裁定記録と手順書の整合だけ。新runner・hook変更・実測・分類値の更新は行わない。
  docs-onlyとして実装子・変異matrixを省略し、独立レビュー済みとは主張しない。
- 作業木checkout中にmainが進み、開始gateは未同期とsubmodule未初期化を検出した。
  checkout終端後に固定SHAへffしsubmoduleを再初期化、fresh gateはrc0。
  同期中に開始していたprovenance監査はHEAD変化でrc2。監査結果に数えず、commit後に固定HEADでやり直す。

- 関連test_check_docsをrun_tests.py経由で計算ノード991392.nqsvへ投入し、rc0で回収した。
  check_codex_agents、check_docs、git diff --check、spool_fold --dry-runも通過。
  最終受入全走はこの記録時点では未実施。

## 次の一手差分

### 更新

- [T-1998] **P2・AI実行待ち・人間専任解除 (2026-09-10)**: D1874の正式測定認可と事前登録を保ち、
  既存balanced1job submitterでの計算ノード投入・結果回収・既存consumerでの解析をAIが担当する。
  事前登録前の生値は主張へ混ぜない。T-2557と同一の実行手番。決定 = {{D:ai-execution-delegation}}。
  base: 94de61e5256b82c75dd3adcc4a14453bee7ec273516f141cb7b48666c83a46e1
- [T-2557] **P2・AI実行待ち・人間専任解除 (2026-09-10)**: T-1998と同じbalanced正式比較の
  投入・回収・解析をAIが担当する。D1936項48の人間専任だけを変更し、D1874の認可条件と
  既存consumerを保つ。測定本体は未完。決定 = {{D:ai-execution-delegation}}。
  base: c995c11b4a31c6e266be7f1f6629a97cf31795199f42c27aa81e9dcd4c860034
- [T-2267] **P2・AI実測待ち・人間専任解除 (2026-09-10)**: 実行場所分類の対象・入力・
  実行条件確認と実測・記録をAIが担当する。D1677/D233決定4/D1936項49のユーザー端末専任を
  変更した。既存の上限付き実行経路、専用cgroupのcharged memoryと記録条件を保ち、
  hook拒否を迂回しない。未実測をunknownのまま扱い、担当変更だけで分類を昇格しない。
  決定 = {{D:ai-execution-delegation}}、手順 = docs/pegasus-runbook.md §7.0。
  base: 5a5785fc4351d97a0c6ca8bb2f3d4109043aa9cc624bb8c0ce399cdbfd387076
