---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1486-attempt-binding-siblings
seq: 1
title: '[T-1486] s8b_oracle_report.py の committed attempt 束縛を build_done/bench_done/abort/commit へ展開した (コード+テスト、branch worktree-dev-wave-t1486-attempt-binding-siblings、変異matrix = baseline PASSED・M1-M6 6/6 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

[T-1476] (commit 67d7a7fa) が `verify_done` にだけ実装した committed-attempt
(`build_attempt_id`) 束縛を、同 wave の段3 敵対相談 (sol) が `build_done`/`bench_done`/
`abort`/`commit` にも同型の脆弱性が残ると指摘していた follow-up。本 wave (段2 codex plan、
段3 敵対相談2レンズ sol/luna、段4裁定、段5 Codex author、段6 敵対レビュー2本+fix+変異matrix+
焦点再レビュー) で全4 stage へ展開した。

段3 sol/luna は独立に「build_done 単独の回帰テストが無いと mutation-kill gap になる」と収束
指摘し、段4 でテスト4本目 (`test_build_done_attempt_id_mismatch_is_a_protocol_violation`) を
追加する裁定をした。段6 review-b は変異事前登録 m6 (positive control) の期待値が
`expected_attempt_id is None` の ID-less fixture では成立しないと指摘 (`None != None` で
不一致検出されないため surviving mutation になる) し、fix で
`test_stray_attempt_id_without_committed_binding_is_not_flagged` (build_start ID-less・
bench_done だけ stray な非 None ID) を追加して m6 を訂正した。焦点再レビューで GO 判定
(review-a/review-b とも closed、regression なし)。

親が実走: 対象6テスト 6 passed、consumer 10ファイル (test_s8b_oracle_report.py 本体含む)
658 passed/19 skipped (rc=0、skip は既存 t080 freeze-verification-hold で無関係)。
`check_ai_provenance.py` full-history 監査 4973件・新規違反なし。変異matrix
baseline PASSED・M1〜M6 6/6 KILLED・matching=6・SURVIVED 0・MISMATCH 0。

Pegasus 計算 queue が実測で数時間規模 (待ち70+件) まで滞留する状況下での実行だった。
`preclaim-history-provenance` gate の300秒timeout SIGKILLがPBS jobを孤児化させる別バグが
他 wave 経由で報告され、修正が入るまで `dev_wave_wait.py acceptance` の新規投入を控えるよう
要請があったため、本 fragment の時点で受入はまだ未投入。

段3 luna が scope 外として指摘した follow-up 候補 (次 wave 候補、未起票):
`orchestrator/campaign/s1_report.py` (別 report generator、s1_report.py:314-322,467-482,903-925)
に同型の attempt_id 不問リスクがある。`orchestrator/campaign/pipeline.py` の `_abort()` は
`build_attempt_id` の後に `**(extra or {})` を展開するため、将来 extra が同名キーを渡すと
上書きされうる (現状 active な callsite は無い)。raw WAL 消費者
(`wal.py::records_by_stage()`、`screening_driver.py`, `backoff_repro.py`,
`p2_2_report.py`, `s1_known_axes_freeze.py`, `critic/digest.py` の variant-wide fallback)
の一部は attempt 未束縛だが、用途 (historical/freeze read 等) が 8b official judge と異なり
一括判定はできない。

一次資料: /work/SFC/tanab/dev-wave-jobs/dev-wave-t1486-attempt-binding-siblings/handoff.md
(段1-6 全経緯)、同ディレクトリの out-plan.md, out-consult-sol.md, out-consult-luna.md,
out-author.md, out-review-a.md, out-review-b.md, out-fix1.md, out-refocus.md,
mutation-spec.json, mutation-out.json, parent-focus-run-5.log, parent-focus-run-consumers.log。

## 次の一手差分

### 完了

- [T-1486] `orchestrator/campaign/s8b_oracle_report.py::_assess_window` の
  build_done/bench_done/abort/commit payload へ committed attempt 束縛を展開し、
  段6敵対レビュー・変異matrix (6/6 KILLED)・焦点再レビュー (GO) まで完了した。
  remaining: none
  base: 6e562398c37117480ec02d392bfc92c49efcfae27d3cd29e514c6a13543a2f27
