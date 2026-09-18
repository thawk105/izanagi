---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2484-timeout-contract
seq: 1
title: [T-2484] D2148項8のdispatch全区間timeoutと短hang撤去を実装した（コード+tests+docs、branch dev-wave-t2484-timeout-contract）
---

## 本文

- ユーザー指定のD2148項8(a-1)+(a-3)を実装。内側期限・回収・既存collection gate・規律2を維持し、区間認識watchdogや要求外gateは加えない。
- 着手時local main `7975385b5`からfresh worktreeを作り、所有面を確認した。コード・テストに重複なし。
  旧t548木の未commit M07差分は非稼働で現mainに同趣旨が反映済みだったため、非接触とした。
- 計画1・敵対相談2・author1・レビュー2・fix1・焦点1。独立レビューmust0、文書should1を処置。
  既存gate緩和、caller漏れ、walltime経路混同、local hang喪失、hold/resume弱化の疑いはrefuted。
- consumer実走で疑似dispatcherのimport時SystemExitという回帰2件を検出。fixtureのimport protocolを修復し、既存CLI本体・テスト期待値を維持した。
  初回837 passed/3 skipped/2 failedを消さず、修正file単独47 passedで閉じた。harness単独は148 passed。
- 変異はbaseline PASSED、17/17期待一致（16 KILLED、等価1 SURVIVED）、MISMATCH/PARSE_ERROR/TIMEOUT0、期待失敗node完全一致。
  wrapperの証拠回収・固定source観測・撤去も成功。数値契約の検出であり任意遅延でのhold消滅や長時間hang確率を主張しない。
- 全8worker accepted、62 model calls、CLI reported tokens 343894。一次資料は `output/insights/2026-09-19/t2484-timeout-contract/README.md` と同verbatim・変異台帳。
- 専用handoffはrepo外job dirの`HANDOFF.md`。自己改善は候補の記録だけとし、改善実装・次wave・pushは行わない。

## 次の一手差分

### 完了

- [T-2484] 全区間を計上したdispatch外側実効timeout、短hang値の外側撤去、理由付き診断とDW-M06/M07整合を完了した。内側期限・回収と既存拒否条件は維持。
  remaining: none
  base: e345dd5b8c29627f9b5ae382521317d0595c4a2aa72d81e907057d3df1547dc6
