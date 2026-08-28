---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t1817-a1-estimand-prereg-codex-resume
seq: 1
title: [T-1817] headline estimand 別 studyを現mainへ適合させ事前登録した
---

## 本文

- D1027どおり既存A-1を変更せず、headline estimandの別 studyを事前登録した。studyは
  `formal=false`、`promotion_prohibited=true`、`result_observed=false`、`runtime_wired=false`で、
  単独では論文§8 A-1を閉じない。
- current main再監査で、既存A-1非接触testの旧base誤帰属、replay receipt入出力の親symlink / swap、
  final rcと公開pathの不一致をrealと裁定した。held dirfd、nofollow、temp write/fsync/close、
  no-replace公開、requested parent inode再照合へ修正し、source-separated replayを再実走して
  certificate不変のままreceipt / README / mirror hash chainを再束縛した。
- final verifier SHAは`248835d4d7f295a3caa928efe0aa823ff7cc6cdbb895161ca8a33d00ab46ad94`、
  replay receiptは`269f070b4603e93b42ebc6433d0f8deb370a021be6afcd452320a63e9a9f0ff3`。
  関連2 test fileは72 passed、Codex agents / docs / provenanceは新規違反0。
- 変異はbroad 9 KILLED / 1 MISMATCHを保持し、M06を観測2 nodeの完全集合へ再登録して1 KILLED。
  実効10/10 KILLED、SURVIVED / TIMEOUT / PARSE_ERROR 0。逐語とraw ledgerは
  `output/insights/2026-08-27_paper-story-a1-headline-estimand-preregistration/MUTATION.md`。
- dispatch queue timeoutでorphan-holdが発火したが、F185 / F529の規律どおり変異hangと誤認せず、
  request終端確認、source復元、3 sidecar除去後にresumeした。F185とF453へ再発を記録する。
- Codex subprocessはreview / focus 4本、author / fix 7本。親はmain取込、real/refuted裁定、artifact再生成、
  変異、検査、記録を担当した。

## 次の一手差分

### 完了

- [T-1817] 現行A-1は凍結どおり据え置き、論文採用estimandを別studyとして事前登録した。
  remaining: none
  base: 86d39c5e527d6afc430ae9c5aff4dcb3c319c763e2f169c1c7d1028f08cc2d95

### 新規

- {{T:mutation-timeout-child-start}} **P2・新規**: dispatch変異のtimeoutをqueue / Pre-runningと
  child実行に分離し、child開始前の混雑でsource変異を残したorphan-holdへ倒れない実行機構を設計する。
