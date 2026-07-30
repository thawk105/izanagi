authority: none
default_effect: no-state-change

# T-145 — long-path serve test の固定 join 二律背反を除去

## 結論

`test_socket_roundtrip_works_beyond_108_byte_repository_path` の `thread.join(120)` を、実
`Supervisor.serve_forever()` の select 呼出だけを観測する child-local proxyと、親processの有限
containmentへ置き換えた。正常経路は wall-clock deadlineで合否を決めず、次の順序を直接検査する。

1. 実listenerと実 `SignalRelay.fileno()` を含む有限poll
2. real long-path request/responseと `RunState.COMPLETED`
3. post-exchange pollへのpark
4. shutdown Event設定、test-owned release、serve return

既知退行は専用failureへ即時帰属する。任意のscheduler starvationは論理的に正常/退行へ分類できないため、
親child ceiling到達時はgreenやKILLでなく `INFRA_TIMEOUT / NOT_EVIDENCE` とする。

production bytes、T-136の通常run limits・state/reason、T-138のcapability probe、xdist markerは不変。

## 実装境界

- test harness全体を独立Python childで実行し、親は180秒ceilingでcontainする
- timeout時はlive session leaderのprocess groupだけをTERM→bounded wait→必要時KILLし、direct
  childをreapする。nested session一般を閉じたとは主張しない
- PASS/SKIP/FAIL resultはexact 4-key schema、型、canonical field、return code、duplicate key拒否で
  fail-closedに読む
- `daemon_mod.select` と `daemon_mod.SignalRelay` のbindingはchild内だけで、同じfinallyで復元する
- parser/controlはcapability非依存、real long-path nodeはcapability環境で別に実走する

## adversarial reviewと裁定

- 段3の独立相談2本はともにNO-GO。test supplied wakeup、pre-select hang、Event混同、stdlib
  process-global patchを棄却し、module-local proxy + ordered observation + parent containmentへ改訂
- 段6初回review2本はNO-GO。unbounded in-process wait、daemon invariant欠落、reader role不足、
  exact timeout pin、cleanup ownershipを採用して第1fix
- 焦点再review 1はNO-GO。exact result envelope、実relay FD、same-group cleanupを採用。nested
  session一般、M7 telemetry、専用result FDはscope外/設計不成立として分離
- 焦点再review 2はNO-GO。stale PGID signalだけを第3fixへ採用。任意巨大outputは固定fixtureと
  M1〜M6から到達しないため、このwaveのmust-fixでなくhardening backlog
- 焦点再review 3はGO。live `process.poll()` ownershipと従来timeout cleanupをclosedと確認

逐語は同directoryの `s2-plan.md`、`s3-*.md`、`s4-adjudication-plan-v2.md`、`s5-author.md`、
`s6-*.md` に凍結した。prompt、CLI生log、patchは記録対象外。

## mutation matrix

対象nodeはすべて
`test_socket_roundtrip_works_beyond_108_byte_repository_path`。各変異はexact anchor 1件、単一tracked
diff、`-rf` failure node、外周ceiling、`git checkout --`復元、commit bytes一致を記録した。

| ID | 変異 | 変更前test | 最終test | 帰属 |
|---|---|---:|---:|---|
| M1 | request後にserveを正常return | SURVIVED、1.406s | KILLED、約1.7s | 純増検出 |
| M2 | loop predicateを`while True`化 | thread-alive赤、121.485s | diagnostic KILLED、約1.5s | 遅延/帰属改善 |
| M3 | `shutdown()`のEvent set除去 | thread-alive赤、121.508s | diagnostic KILLED、約1.6s | 遅延/帰属改善 |
| M4 | poll timeoutを3600秒化 | thread-alive赤、121.472s | diagnostic KILLED、約0.7s | semantic pin |
| M5 | fixtureを`daemon=False`化 | SURVIVED、1.655s | KILLED、約0.8s | preservation gap閉鎖 |
| M6 | foreign-call guard無効化 | NOT_APPLICABLE | diagnostic KILLED、約0.8s | harness isolation |
| M7 | primary error注入とcleanup観測 | NOT_RUN | NOT_RUN | design-invalid、KILL主張なし |

旧比較commitと並行T-143後の最終親commitで、対象test・daemon・workerのpre-T-145 blobが同一であることを
照合した。最終integration commit上でもM1〜M6を再走し、同じnode・分類と復元一致を得た。

T-136 preservationはPM1 timeout reason、PM2 deadline guard、PM3 log-limit reason、PM4v2 residual
stateを再走し、4/4 KILLED。元のT-136台帳と同一parameterized node、同一reason/state署名であり、
T-145の純増検出には数えない。

raw結果は `mutation-results-new.json`、`mutation-results-old.json`、
`preservation-results.json`、再現harnessは対応する `*_harness.py`。

## 受入

repo root・本worktree・ログインノードで実測した。

- focused: 18 passed（parser 14、real long-path 1、isolation 3）
- related: integration + isolation = 97 passed
- pre-T-143-parent full: 3598 passed / 18 skipped / 0 failed、244.41s
- final record後 full: 3688 passed / 18 skipped / 0 failed、252.17s
- mutation後は対象tracked fileをすべてcommit bytesへ復元

## 残余

- 180秒を超える任意scheduler starvationは `INFRA_TIMEOUT / NOT_EVIDENCE`。絶対的な無時間liveness
  証明ではない
- nested session一般containment、result/outputの明示byte上限、producer/parser結合controlは未実装
- M7はcleanup成功を独立観測できないため `NOT_RUN(design-invalid)`。検出済みと過大記録しない
