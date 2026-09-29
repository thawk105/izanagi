## 実装

[s8b_holdout_freeze.py:504](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_holdout_freeze.py:504) に `(literal, rel)` ごとの共通判定 cache を追加し、既存の memo identity・内容変化検査を通った後に再利用するようにしました。[同:522](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_holdout_freeze.py:522) では最大幅を使った窓検索を実装し、重なる literal も列挙します。列挙・読取・decode・例外経路は変更していません。

## test

[test_s8b_holdout_freeze.py:1000](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1000) に単軸の右端・JSON 左端・重なり・`.`・8192 byte 以降の等価性を追加しました。[同:1013](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1013) は memo key、[同:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1026) は共通判定回数を固定します。[同:1086](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1086) の既存比較には、局所化だけを外す段を加えました。

## 変異の確認

各変異を一時適用し、該当 node を実走してから復元しました。M1・M2・M3 は `test_localized_single_axis_matches_full_search_and_reference` の各 `ab=cd`・JSON・`aa=bb` ケースが [assert :1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1008) でそれぞれ赤。M4 は `test_prefilter_report_exactly_matches_slow_path[files]` が [assert :1121](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1121) で赤。M5 は `test_common_literal_memo_is_keyed_by_literal_and_rel` が [assert :1020](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1020) で赤。M6 は `test_common_literal_is_checked_once_per_text_per_search` が [assert :1041](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1041) で赤。いずれも個別実走では 1 node、1 理由の失敗でした。P0 の docstring 1 語変異では全 file が **168 passed、2 skipped** でした。

## 実走

[test_s8b_holdout_freeze.py 全体](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:1) は `pytest.main` 経路で **170 node 収集、168 passed、growth hold 2 skipped**。関連番人の絞り込みは **15 passed**。隣接 caller・consumer は [oracle driver:1997](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_oracle_driver.py:1997) から 2 node、[T080:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_t080_freeze_migration.py:205)、[s8c:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8c_preregistration_invariant.py:650)、[protocol builder:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_protocol_builder.py:163)、[floor evacuation:380](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_floor_evacuation.py:380) を各 1 node、計 **6 passed** です。

変更 2 file の `search_repository` 自己汚染確認は `rr80=[]、rr20=[]`。[s8b_holdout_freeze.py:634](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_holdout_freeze.py:634) `git diff --check` も通過しました。

## 波及 (所有外 caller・共有 fixture・consumer test の静的列挙)

所有外 caller は [floor campaign:5533](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_floor_campaign.py:5533)、[T080:1891](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/t080_freeze_migration.py:1891)、[ratified freeze:3680](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/campaign/s8b_ratified_freeze.py:3680)。既存の共有 fixture・consumer test は [oracle driver:2002](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_oracle_driver.py:2002)、[s8c invariant:643](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8c_preregistration_invariant.py:643)、[ratified verify:1628](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_ratified_verify.py:1628) などを確認しました。新設 7 node は [所要時間台帳:19311](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/acceptance_duration_ledger.json:19311) に未登録です。所有外なので変更していません。

## 未実走・懸念

実 repo を走査する growth hold 2 node と、列挙した所有外 caller・consumer test の全件は未実走です。[test_s8b_holdout_freeze.py:3353](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273is-impl/orchestrator/tests/test_s8b_holdout_freeze.py:3353) 性能短縮量もこの段では未計測です。

## 総括

所有 2 file のみ変更し、commit は作成していません。全 file と P0 は各 168 passed・2 skipped、M1〜M6 は登録番人で赤でした。復元後の差分は意図した 2 file のみです。