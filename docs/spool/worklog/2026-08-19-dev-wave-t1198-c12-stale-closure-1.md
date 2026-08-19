---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1198-c12-stale-closure
seq: 1
title: '[T-1198] は既に stale と判明し carry を完了で閉じる (docs のみ、branch worktree-dev-wave-t1198-c12-stale-closure)'
---

## 本文

- [T-1198] (entry 585 原文、`docs/archive/worklog-phase3-0816-585.md`) は「C12 の
  `machine_checkable` を反転すると実 tree に対して `UNSATISFIED`/`environment-contract-consumer-absent`
  を返す、pegasus 経路で実際に走っている consumer を不在と誤診断する」という finding だった。
  着手前提の確認 (T-1379 との編集面重複チェック) の過程で、この finding は既に **stale** と
  判明した。
- 実測で分かった前提の食い違い: task 引数は C05/C07 と同型の「未活性化 (`machine_checkable: false`)
  → 反転」パターンを想定していたが、C12 は既に `machine_checkable: true` かつ `_MACHINE_EVALUATORS`
  にも登録済みだった (`orchestrator/campaign/s8c_preregistration_evidence.py`、T-327 由来)。
- 根本原因: entry 585 と同時に起票された兄弟 finding [T-1197] (到達判定 helper が同一 module 内の
  top-level 定義しか辿らず cross-module consumer を不在と誤判定する) と、より具体的な誤報事例
  [T-1202] が指すのは T-1198 と同じ症状であり、2026-08-17 の一連の commit で修正済みだった。
  - `ccb9ee65` Widen 8c preregistration reachability to cross-module — 到達判定を同一 module
    限定から cross-module (import 束縛を辿る canonical graph) へ置換。commit 本文に実測ログ
    "C12 UNSATISFIED/environment-contract-consumer-absent (誤報) -> UNSATISFIED/
    allocation-enforcement-consumer-absent (真の不在)" と明記 — T-1198 が指す症状そのものの修正。
  - `0862ac11` Harden cross-module reachability against false positives — 段6 敵対レビュー2レンズ
    独立 NO-GO・11 must-fix を3巡で解消。本文に明記の通り方向は全て受理集合を狭める側 (規律2 を
    緩めていない)。
  - `9aee98f3` [T-1167] C12 の allocation 節を実現可能な予約 binding へ縮小 (D441 択(c) の実装)。
  - `47146d74` 上記2 branch (cross-module 到達判定 / allocation 節縮小) の合成 merge。
  - `ccb9ee65`/`9aee98f3` は [T-1197]・[T-1202] を名指しで閉じたが、**同じ症状を指す [T-1198] は
    名指しされず**、carry が (586) から (684) まで機械的に持ち越され続けた。[T-1197]・[T-1202] は
    現行 `docs/worklog.md` の carry に現れず、当時の着地 wave で正しく完了節に入っていたことを
    確認した。
- 実測 (Pegasus dispatch 経由 `tools/run_tests.py --force-dispatch`、受入形ではない焦点走):
  - `test_current_repository_c12_registry_reports_unwired_allocation_consumer` +
    `test_current_repository_c12_allocation_binding_helper_reports_unwired_consumer`
    (real-repo tripwire、`current_commit_snapshot` fixture で実 HEAD を見る) = 2 passed
    (request 923939.nqsv, 13.19s)
  - `test_s8c_preregistration_predicates.py` + `_core.py` + `_invariant.py` 全体 = 574 passed,
    0 failed (request 923944.nqsv, 66.22s)
  - 現状値: C12 は `EVIDENCE_UNDEFINED`/`completion-proof-not-machine-checkable` (8c 判定器族の
    合格終端)。誤診断は再現しない。
- F35 (完了済みタスクの繰り越し) へ再発を追記した。今回は「完了節への明示漏れ」の従来型ではなく、
  「同じ症状を指す別 task ID が先に fix・完了節記入され、fix した側からは carry 台帳上の
  もう一方の ID が見えず突合せが行われなかった」という新しい発生角度である。詳細は同 fragment。
- 前例: entry 673 ([T-715]) も同型の「brief 前の実測で完了済みと判明」を codex 段2/3 を使わず
  直接記録する軽量パスで処理していた。本 wave も同じ軽量パスを踏襲した (段4「実装しない」裁定 →
  4→7→8→9、`docs/dev-wave/core.md` の凍結境界に従う)。

## 次の一手差分

### 完了

- [T-1198] C12 の `machine_checkable` 反転で誤診断が出るという finding は、2026-08-17 の
  `ccb9ee65` (到達判定の cross-module 化) / `0862ac11` (false positive 対策の harden) /
  `9aee98f3` ([T-1167] allocation 節縮小) / `47146d74` (合成 merge) で既に修正済みと実測確認した。
  real-repo tripwire test 2件 pass + s8c_preregistration 系 574 passed で健全性を確認済み。
  実装差分ゼロ、記録のみ。
  remaining: none
  base: 3867d33433bac90d3459d4af8b79e6403077704aef81b32af41929944eaa2697
