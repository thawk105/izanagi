# T-145 段 6 焦点再レビュー 1 裁定

## 採用する所見

- structured result envelope は real must-fix。exact key set、field type、outcome ごとの canonical
  invariant、exit code の対応を親で fail-closed に検証する。stdout prefix 1 本という channel は
  child が test 専用かつ stdout を親だけが読むため維持し、専用 FD への再設計は scope 外とする
- relay reader identity は real must-fix。`daemon_mod.SignalRelay` の child-local binding を wrapper
  で観測し、実生成された relay instance の `fileno()` と `select` reader を束縛する。標準 module
  や pytest worker へ patch を波及させない
- capability 非依存 control を追加し、canonical PASS/SKIP/FAIL と malformed envelope がそれぞれ
  所定の受理/拒否になることを tracked test で確認する

成果物影響: envelope/relay identity を閉じない場合、最小偽 PASS や signal relay を poll しない
production mutationを対象 nodeが受理し、mutation台帳の KILL/SURVIVE が誤る。

## 一部採用・記録で閉じる所見

- timeout 時の descendant containment は generic blocker ではあるが、T-145 の M2〜M4 は exchange と
  terminal state 観測後の serve-loop に停止を注入するため active worker を持たない。success fixture
  も grandchild を起動しない。通常 worker/fake child は各 direct parent に
  `PR_SET_PDEATHSIG(SIGKILL)` を設定する。したがって T-145 の対象受入を止める must-fix には
  しない
- ただし親は timeout 時に harness child の process group へ TERM/KILL を送り、直下 child と同じ
  group の descendant を閉じる。nested session を跨ぐ一般 process-tree containment は T-145 の
  KILL として過大主張せず、unexpected pre-terminal timeout を常に
  `INFRA_TIMEOUT/NOT_EVIDENCE` とする
- `KeyboardInterrupt` / `SystemExit` は child boundary の payload に元 type/args/traceback を保存する。
  親 pytest process で再送出すると test session 自体を制御例外で中断するため再構築しない。
  「cleanup が primary の type/args を書き換えない」という child 内契約と、外部 structured failure
  の帰属を区別する
- M7 は現 fixture では cleanup 成功を独立観測できないという所見を採用する。M7 を KILL/SURVIVE
  証拠から外し `NOT_RUN(design-invalid)` とする。T-145 の本体で cleanup telemetry を増設しない

## 不採用・scope 外

- +411/-26 の縮小は nit。今回さらに state machine を再設計すると検出面を変え、real long-path
  nodeの shadow contract を別物にする。第2修正は envelope、relay identity、group signal、
  capability非依存 control に限定する
- environment canonicalization と専用 result FD は hardening backlog。具体的な現 consumerの偽緑を
  示しておらず、追加 review wave を起動しない

## 第2修正の終了条件

1. production/docs/output は触らず、tracked code は
   `orchestrator/tests/test_dev_waves_integration.py` のみ
2. exact structured schema と outcome/returncode invariantを helper へ分離し、malformed payloadを
   `INFRA_ABNORMAL` として拒否する
3. real `SignalRelay.fileno()` identityを child-local wrapperで束縛し、restore ownershipを一つの
   `finally` に置く
4. timeout cleanup は harness process groupへ bounded TERM→wait→KILL→reapを行う。nested session
   全体を KILL したとは記録しない
5. capability 非依存の focused parser/control と isolation meta-testを実走する。real long-pathが
   capability skipなら NOT_RUN のまま記録する
6. これを第2/最大3巡の fix とし、再レビューで新しい scope 拡張 nitだけなら変異へ進む
