# [T-1302] 非帰属受理の flake 別集合化と runner 束縛 — 材料

wave `dev-wave-t1302-r2-nonattrib` / 2026-08-17 / 実装 commit `4906e063` / base main `e58f4533`

裁定パッケージ #2 (`output/insights/2026-08-17_t1116-nonattrib-checker/ruling-package.md`) の
択 (c) を実装した wave の逐語と変異台帳。設計判断の正本は decisions 台帳、経緯の正本は worklog。

## 構成

- `verbatim/brief.md` — 段 1 brief v2 (親)。`DW-O13` 巻き戻し後の版。
- `verbatim/s2-plan.md` — 段 2 プラン (codex, plan, max)。
- `verbatim/s3-lensA.md` / `s3-lensB.md` — 段 3 敵対相談 (codex, consult, max, sol/luna)。
- `verbatim/s4-adjudication.md` — 段 4 裁定 (親)。gate の署名と変異事前登録を含む。
- `verbatim/s5-author.md` — 段 5 実装 (codex, author, high)。
- `verbatim/s6-revA.md` / `s6-revB.md` — 段 6 敵対レビュー (codex, review, high)。
- `verbatim/s6-fix.md` — 段 6 fix (codex, fix, high)。
- `verbatim/s6-focus.md` — 段 6 焦点再レビュー (codex, focus, high)。
- `verbatim/s6-merge-resolution.md` — main 取り込みの競合解消 (codex, fix, high)。
- `verbatim/s6-merge-synthesis.md` — 取り込み後の合成是正 (codex, fix, high)。
- `mutation-spec.json` — 本走の変異 spec (13 件、期待 node 完全集合)。
- `mutation-results.json` — 最終 anchor `dc0204ab` での結果
  (13/13 KILLED、MISMATCH 0、SURVIVED 0)。実装 commit `4906e063` でも同じ結果を取っている。
- `mutation-probe.json` — 初回 probe (全件 SURVIVED 期待で観測 node を収集した回)。
  P01 だけは差し替え後に単独 probe を回したため、この file の P01 は差し替え前の版である。

## 変異走の条件

- anchor: `dc0204ab` (main 取り込みと合成是正の後の最終 tip)。`--runner-mode dispatch`、runner argv は
  `python3 tools/run_tests.py --force-dispatch` に焦点 3 test file と `-q -rf`。
- baseline を緑にするため、本変更前から main で赤い
  `orchestrator/tests/test_dev_wave_land.py::test_exploration_external_root_keeps_wave_clean`
  を `--deselect` で外した。この赤は login ノードでも計算ノードでも再現し、本 wave の差分は
  到達しない (worklog に新規項目として起票済み)。

## 読み方の注意

段 2・3 は一度やり直している。`DW-O13` (gate 入力の実在) を段 2 前に読んでいなかったため、
段 4 で新 gate 候補が判明した時点で入口の巻き戻し規則に従い最初の版を invalidate した。
ここに残しているのは**やり直した後の版**である。破棄した版は後続の子へ渡していない。
