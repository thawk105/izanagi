# 段 6 裁定 — レビュー A / B と焦点走の赤 (2026-09-21 21:5x JST)

入力: `focus-1.log` (焦点走、計算ノード 15694.nqsv、9 file: 800 passed / 4 failed / 3 skipped、36.70 s)、`codex/review-A.md` (must-fix 2 / should 1、条件付き GO)、
`codex/review-B.md` (must-fix 0 / should 2 / nit 1、GO)。対象 = wave `36fb14a3d..efd8d191d`。

## 裁定

| 所見 | 裁定 | 処置 |
|---|---|---|
| 焦点走の赤 4 件 (`test_landed_fig14_rejects_missing_or_partial_bundle`、`test_attempt2_visible_text_forbidden_claims_and_negative_control`、`test_landed_fig15_rejects_missing_or_partial_bundle`、`test_caption_fixed_literals_and_forbidden_claims`) | real (自分起因) | fix 子。`assert cond, msg` を捕まえて `str(exc) == msg` と完全一致で比べており、pytest の assert 書き換えが例外文に説明を足すので pytest 下だけ偽 (plain runner では緑)。既存 fig9 test と同じく先頭行または `startswith` で比べる。レビュー A は同型の他箇所を探して「既知 4 件だけ」 |
| A#1 / B#1 plotting README の mocc 節が Fisher p・commit 平均まで summary と照合したと読める | real (must-fix) | 親 docs で修正済み (`f2d146cd5`) |
| A#2 新節の「F36 の自己参照回避」は F36 (結果欄のプレースホルダ) と別内容 | 一部 refuted (事後に判明): F36 本文は placeholder の型だが、`docs/dev-wave/core.md` の `DW-S07` が「hash 自己参照は禁止（F36）」と引いており、fig9 節の書き方はその先例に従っていた | 親 docs で修正済み (`f2d146cd5`)。F 番号を外して理由 (相互 hash の循環を避ける) を直接書いた形は情報を失わないので維持。既存節の同じ引き方は変えない (insight に観察として記録) |
| A#3 曝露比の可視注記 2 本を描かなくても test が緑 (F623 / F653 型) | real (should) | fix 子 (mocc)。可視 `Text` に `BACK_OFF=0: on/off exposure ratio 0.8636` 型の 2 行があることを検査する test を足す。変異 M14 を fix 前に登録 (下) |
| B#2 mocc test の plain runner が `PYTHONPATH` 前提 (`from orchestrator.tests.skiputil`) | real (should) | fix 子 (mocc)。A-1 と同じ `sys.path.insert(0, str(HERE))` + `from skiputil import` に揃える |
| B#3 fig15 の layout 検査の「隣接 panel 侵入」は 1 axes 制約の下で到達不能 | real (nit) | fix 子 (mocc) で当該 4 行を削る (1 axes 制約・図外逸脱・重なり検査は残す) |

## fix の分割 (DW-S06-B)

所有は素集合 → 2 本並列。土台は直前の統合 commit `f2d146cd5` (図・README 込み。着地 test がそのまま緑になる木)。
- fix-a1 (`.codex/worktrees/figs-unit-a1`、新 branch `dev-wave-figs-unit-a1-fix1` @ `f2d146cd5`): `orchestrator/tests/test_plot_a1_sized_paired.py` の 2 件だけ。生成器は変えない。
- fix-mocc (`.codex/worktrees/figs-unit-mocc`、新 branch `dev-wave-figs-unit-mocc-fix1` @ `f2d146cd5`): test の 2 件 + A#3 の test + B#2 の import、生成器は B#3 の 4 行削除だけ。
- **既存テストの期待値を変更しない** (tracked の既存 test = base `36fb14a3d` にある 28 本)。本 wave で足した test は編集対象。反転・緩和・skip・削除をしない。

## 変異の追加登録 (DW-M01: 段 6 の real 所見は fix 前)

| # | 対象・変更 | kill 予定 test | 期待 |
|---|---|---|---|
| M14 | fig15: `make_figure` の曝露比注記 (`for i, text in enumerate(series['exposure_notes']):` と次の `fig.text(...)` の 2 行) を削除 | fix で足す曝露比の可視検査 test | KILLED |

fix 後に M0〜M14 の anchor を fix 最終 commit で再検証する (DW-M07)。
