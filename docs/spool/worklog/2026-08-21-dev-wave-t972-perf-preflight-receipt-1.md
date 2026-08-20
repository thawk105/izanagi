---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t972-perf-preflight-receipt
seq: 1
title: '[T-972] build_cells前にperf preflight receiptをjournalへcreate-only永続化し、resume classifierを安全拡張した (コード+テスト、branch worktree-dev-wave-t972-perf-preflight-receipt、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 段3 敵対相談 2 レンズ (sol=正しさ境界、luna=整合/scope) と段6 敵対レビュー 2 本が、当初 brief
  の想定 (s8b_floor_campaign.py 1 箇所への追記) を超える scope 拡大を発見した:
  perf-preflight journal event が resume classifier (classify_journal_resume_state) の
  L/M-prestart 判定を壊す regression になると判明し、s8b_floor_contract.py の安全な拡張が
  必須になった。設計は {{D:t972-perf-preflight-resume-allowlist}}。
- 親の当初仮説 (「resume 呼び出しに perf_preflight_fn 未指定 → 実環境 perf 依存で赤」) は
  段3・段6 の独立レンズがいずれも REFUTED と判定した。実測の真因は
  `_make_measure_fn` の既定値 `use_perf=True` と初回の `use_perf=False` の不一致であり、
  親の推測とは異なる正確な原因究明に至った (敵対検証が機能した実例)。
- 段6 敵対レビューが、manifest に perf_preflight キー不在時の resume 検証が sentinel 経由で
  一致確認をスキップし fail-closed でなくなる穴 (旧 manifest + 偽装 event の受理余地) を
  独立に発見し fix した。
- DW-O26 の焦点走で `test_official_perf_closure.py` (呼び出しグラフの exhaustive inventory
  test) が新規呼び出し関係の未登録により赤になり、追加 fix (1エントリ追加) で解消した。
  trace-enabled 経路との比較は技術的に不可能と判断し実装しなかった: {{D:t972-trace-lane-closure-unrealizable}}。
- セッション運用の異常 3 件を {{F:dev-wave-author-prompt-missing-total-heading}}、
  {{F:mutation-harness-orphan-hold-dual-sidecar}}、{{F:focused-run-concurrent-dispatch-false-red}}
  に記録した。
- 一次資料: `/work/SFC/tanab/dev-wave-jobs/dev-wave-t972-perf-preflight-receipt/handoff.md`
  (段1〜6 の裁定経緯全文)、同ディレクトリの `mutation-spec.json`/`mutation-out.json`
  (変異事前登録と結果)。

## 次の一手差分

### 完了

- [T-972] build_cells 前に perf preflight receipt を journal へ create-only 永続化する設計と
  最小実装を検証し、resume classifier の安全な拡張込みで実装・敵対レビュー・変異matrixを完了した。
  remaining: none
  base: 1efac57c72f235d98d915f60c43b8ba834ae963c2ec7a43d3c5d560eee8c8f3d

### 新規

- {{T:reservation-preflight-resume-classifier-gap}} **P2・新規**: journal の
  `reservation-preflight` イベントも `perf-preflight` と同型の resume classifier 未対応問題
  (L/M-prestart 判定が許容しない) を抱えている。T-972 は scope 外としたが、official mode
  解禁後に発火しうる既存の欠陥として次 wave の候補にする。
