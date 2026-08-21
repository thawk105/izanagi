---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t972-perf-preflight-receipt
seq: 1
title: '[T-972] build_cells前にperf preflight receiptをjournalへcreate-only永続化し、resume classifierとs8b_ratified_freezeのjournal検証を安全拡張した (コード+テスト、branch worktree-dev-wave-t972-perf-preflight-receipt、変異matrix = baseline PASSED・M01-M04 4/4 KILLED・SURVIVED 0・MISMATCH 0)'
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
- 受入全走2回目で、resume classifier (`s8b_floor_contract.py`) とは完全に独立した
  もう1つの journal 検証機構 (`s8b_ratified_freeze.py._JOURNAL_KEYS` の event 種別ごと
  exact key allowlist) が perf-preflight event を未知として拒否する regression を発見し
  fix3 で解消した (allowlist へエントリ追加 + inner receipt 再検証)。DW-O26 の consumer
  探索では grep でヒットしていたが具体的識別子での絞り込みで誤って除外していた:
  {{F:t972-independent-journal-validator-missed-by-consumer-search}}。
- fix3 の新設呼び出し (`_validate_journal`→`validate_perf_preflight_receipt`) が
  closure inventory drift を再発させ (fix2 で解消したのとは別の未登録呼び出し)、
  fix4 (1エントリ追加) で解消した。同じ closure drift が同一 wave 内で2回発生した:
  {{F:t972-closure-drift-recurred-twice-same-wave}}。
- 変異事前登録に M04 (`s8b_ratified_freeze.py` の `if key == "perf-preflight":` 無効化) を
  fix3 後に追加。M01-M04 全4件 + baseline を実測し、baseline PASSED・4/4 KILLED・
  matches_expectation=true を確認した。
- 受入全走3回目 (attempt=3) が `owned-path-overlap` (T-1444 が `s8b_floor_campaign.py` を
  含む3 commit を先に main へ land 済み) で終端した。`git merge-tree` で機械的 conflict が
  0件であることを確認した上で main を取り込み (DW-O18 の「並行 wave が自分の編集 file を
  所有するなら main を取り込んだ木で既存走行へ相乗りさせる」に従う)、影響ファイルの
  焦点走 493 passed, 2 skipped を確認して受入全走4回目 (attempt=4) を投入した。
- セッション運用の異常を {{F:dev-wave-author-prompt-missing-total-heading}}、
  {{F:mutation-harness-orphan-hold-dual-sidecar}}、{{F:focused-run-concurrent-dispatch-false-red}}、
  {{F:t972-independent-journal-validator-missed-by-consumer-search}}、
  {{F:t972-closure-drift-recurred-twice-same-wave}} に記録した。
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
