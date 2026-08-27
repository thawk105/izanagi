---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t2018-condition-meaning-gate-codex-resume
seq: 1
title: [T-2018] 要求した define の供給と実行側の意味を独立 gate へ分離した (コード + docs、branch worktree-dev-wave-t2018-condition-meaning-gate-codex-resume、変異 matrix = baseline PASSED・KILLED 8・SURVIVED 0・MISMATCH 0)
---

## 本文

- Claude 段1の他 AI 作業物を内容監査して Codex resume worktreeへ移し、段2から再開した。
  元worktreeはtip 8d014c748、tracked clean、T-2018 live process 0、未追跡2 fileだけだった。
- 段3で初版をNO-GOとした。候補defineは9でなく8、集合比較はcontext入替を通す、
  supply名集合はcache-to-TU route/valueを証明しない、fixture-only JSONは実在入力でないと確定した。
- wave中にD1198がlandし、T-1999は裁定済み・実装待ちへ変わった。ユーザーの本wave明示scopeは
  広げず、driver接続0のまま、supply armとmeaning armを別public function/evidence/reasonにした
  ({{D:condition-meaning-independent-arms}})。
- meaning armは適用後sourceのdecoderをstandalone TUで実compiler評価し、start 1/2を
  canonical float64 bitsでpointwise比較する。actual target TU、dynamic reachability、
  exact build inputは証明しない。driver_integration=noneで現行1000点は未保護。
- F707 fixtureは供給表を非空に保ちBACKOFF_FIXED mappingだけを欠かせ、
  F718 fixtureはsupply緑のままexpected 1000.0 / observed 0.0をmeaningだけで拒否する。
- Codex authorの初回報告は実装済みだったがF43 fragmentでvalidator rc=1。
  別author再監査後accepted。段6はreview2本、fix2巡、focus2巡を行い、最終focusはGO/blocker 0。
- 焦点走は29 passed / 7.02s、共有consumer 5 passed / 4.09s、meta-test 4 passed / 40.35s。
  commit前後provenanceは新規違反なし。
- 変異probeはbaseline PASSED・8 MISMATCHをerratumとして残し、finalはbaseline PASSED、
  KILLED 8、SURVIVED 0、MISMATCH 0、expected node完全一致8/8。
  共有primaryのraceでrc125になった2走は不受理とし、独立clone sourceで
  shared_snapshot_matches=true / teardown_completed=true / child rc=0を取り直した。
- 実装commitは13f9c1b5067bda82b19861127a53d90b79a9e207。pushは行っていない。

## 次の一手差分

### 完了

- [T-2018] BACKOFF_FIXEDの供給と意味を独立したcall-scoped gate・負例へ分離した。
  driver群への義務接続、patch/ledger/freeze、符号化/格子変更は本項へ混ぜず、裁定済みT-1999等へ残した。
  remaining: none
  base: 8ac66a07fc1c8618b337efba5a888caef188e2ccc7cc663ea1ea8972d8f13333
