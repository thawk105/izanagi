# [T-2610] B-7 fixed 5 µs 三 workload 退行の図 fig10 — 生成器・test・着地の開発記録

これは既存測定 (attempt `b7f5-20260919a`、稿 `docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md`) の
**図を作る開発記録**である。新しい性能測定、B-7 の要件充足の判定、certification の昇格、有意差判定は行わない (D2044 項 3、D2162)。

## 成果物と一次資料

- 図 10: `docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.{png,pdf,provenance.json}` (着地 SHA-256 は figures README の fig10 節が正本)。
- 生成器: `tools/plotting/plot_b7_fixed5_regression.py` (新規、自己完結)。test: `orchestrator/tests/test_plot_b7_fixed5_regression.py` (42 test、自走 harness 付き)。
- docs: `docs/paper-story/figures/README.md` (一覧 1 行 + fig10 節)、`tools/plotting/README.md` (節 1 つ)、`docs/paper-story/README.md` (results 行と stale 注記の「図は無い」→ 図 10)。
- 入力: 権威 bytes `output/insights/2026-09-19_t1998-b7-fixed5-three-workload/{certification.json,raw-manifest.json}`、床値 JSON
  `output/env/pegasus/calibration/between_run_noise_t48_skew0p9_{rr5,rr50,rr95}_rmw0.json` (D1639)、policy `orchestrator/campaign/paper_story_b7_fixed5_regression.v2.json`、
  durable raw 6 本 (`/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-b7-fixed5-20260919/b7f5-20260919a/jobs/<w>/raw/<cell>.json`、raw-manifest の SHA-256 で束縛)。
  5 標本は durable raw にだけあり、certification.json は median だけを持つ。
- 値の出所・限定・caption・proof chain は figures README の fig10 節と稿に置き、本 README には再掲しない。稿を caption_source とするので、図の provenance hash を稿へ逆流させない (F36)。

## 設計判断 (段 4 裁定、`verbatim/s4-adjudication.md`)

- (P1) 5 標本は durable raw から読み、tracked raw-manifest の SHA-256 で束縛する (fig6 型)。着地 closure は provenance の cells から artist / caption を再計算し durable root を要さない。
- (P2) 図に出す判定の出所は稿 §2.1 の転記 (`RECORDED_JUDGMENT`)。生成器は述語 `effect < −floor` (strict) を評価するが、転記と権威 bytes・床値 JSON との整合検査にだけ使い、
  判定の出所にはしない (fig9 の classification と同型)。D2162 が禁じる「追加 gate」(certification 経路の判定手順) ではない。レビュー A-3 の「述語照合を削れ」は不採用 —
  削ると転記誤りが図に出ても止まらない。
- (P3) 2 段構成。上段 3 panel = cell ごとの 5 標本・median・mean ± t95 CI・stock median (fig6 の描画契約)、下段 1 panel = 効果 (%)・0 線・−floor・判定 label。
- raw の correctness 記録は anomaly 件数を持たない → caption は「certified・verdict serializable (legacy 1 + performance 5)」までを書き、anomaly 0 を書かない。
- 軽量版 (DW-C00): 段 2・3 省略。段 5 Codex author 1 本、段 6 レビュー 2 本 + fix 1 本 + 焦点再レビュー 1 本。

## 経過

- 07:03 JST worktree (`worktree-dev-wave-t2610-fig10`、base local main `b7f970dfa`)。gate rc=0。
- 07:24〜07:43 段 5 author (Codex gpt-6-astra、reasoning medium、28 call、1140 s、accepted): 生成器 528 行 + test 40 本。実データ生成 rc=0、稿との全値照合一致。
- 07:46 親が login (pegasus02、計測機の外) で図生成 rc=0。commit `35bfe1cfb` (実装) と `04ae82a1c` (図 + docs)。
- 07:48 焦点走 focus1 (request 11888.nqsv、113 s): 841 passed / 3 skipped。focus2 (新 test + a2 の単独走): 127 passed / 0 skipped。skip 3 件は新 test にも a2 にも無く既存 file 由来。
- 07:53〜07:57 レビュー A (過剰・削除、NO-GO、must-fix 1 / should 3 / nit 1) と B (正しさ境界・整合、GO、should 3)。両者とも 30 標本・6 median・effects・floors・判定・caption・hash の照合は全件一致。
- 08:08 段 6 裁定 (`verbatim/s6-adjudication.md`): A-1/B-2 (caption_source の `authority_scope` が稿を判定の出所から除外していた) を must-fix で採用、A-2 (床の説明に session-median・下限・
  同一性未証明、correctness に workload argv 独立記録なし)、A-4、B-1 (着地 test で provenance の 30 標本・6 median と稿 §2.2 を束縛)、B-3 (境界 test 2 本) を採用、変異 m13 / m14 を fix 前に追加登録。
- 08:09〜08:11 fix1 (Codex author、accepted)。08:12 親が図を再生成 (PNG bytes 不変、PDF / provenance 更新)、README の caption と hash 3 行を実値化。commit `e6a291d44` (fix) と `6fbe7d017` (図 + docs)。
- 08:14 焦点走 focus3 (843 passed / 3 skipped、skip は focus1 と同じ既存 file 由来)、焦点再レビュー (GO、closed 8 / partial 0 / regressed 0)。
- 08:20 local main `efb0dee78` (T-2789 の docs 3 commit、3 blob 不変) を固定 SHA で前方 merge (`a1b4c6bff`)。

## 変異の終端

固定 anchor は `6fbe7d017f07e23f4942847f1c4ccbb62d6fedd6`、spec は `mutation-spec-v1.json` (SHA-256 `dff36ad73dcd9c2d2cdce3796f4cb8826d379184aebe7905a303e216c4dbfcca`)、
15 件 (positive 1 + negative 14。m13 / m14 は段 6 裁定で追加)。runner は `tools/mutation_harness.py --runner-mode dispatch --detached` を主 repo の登録 worktree
`.codex/worktrees/mut-t2610-fig10` (固定 commit、submodule 初期化済) に直接当て、test runner は `run_tests.py --force-dispatch orchestrator/tests/test_plot_b7_fixed5_regression.py -q -rf` (計算ノード)。
期待 node は login の自走 harness で各変異を注入 → 赤 node を記録 → `git checkout --` 復元 (HEAD blob 照合) した probe で集めた
(`verbatim/mutation-probe-login-anchor-6fbe7d017.json`。fix 前の anchor `04ae82a1c` での probe も `verbatim/` に残す)。

本走 (2026-09-20 08:22〜08:44 JST、request 11934 (baseline) と 11935〜12023): **baseline PASSED (32.6 s)、m0 SURVIVED、m1〜m14 の 14 件すべて KILLED、
期待 node 完全集合 15/15 一致、MISMATCH / PARSE_ERROR / TIMEOUT はすべて 0**。実測の正本は `mutation-results-v1.json` / `mutation-attempts-v1.json`。
m1 (tracked SHA-256 検査の恒真化) は hash drift test 4 本、m9 (layout の重なりを無視) は layout test 2 本、m10 (着地 test の全欠落 skip 復活) は全欠落・部分欠落 test 2 本、
m11 (caption の「not a performance certification」削除) は固定 literal test と着地 closure test の 2 本、他は対応 test 1 本ずつが赤になった。login probe (fix 前 / 後) と本走の
観測 node は同一。診断文字列だけの赤は無く、いずれも受理集合または fail-closed 挙動の変化で殺した。harness は `repo_head`・clean tree・flock を束縛し、走行後の変異 worktree は clean (status 0 行)。

## レビュー・変異で残った限界

- 着地 closure は provenance の標本を稿 §2.2 と結ぶが、durable raw との再照合は `validate_external_sources` (durable root が読めるときだけ) に分かれる (レビュー B-1 の残余)。
- 図の下段は −floor (−0.2〜−1.0 %) と 0 線が近接し、線としては見分けにくい。値は label に出す。
- 稿の限定 14 件のうち caption に写したのは §4 項 1〜3・6〜9・11・12 の趣旨で、機序・perf 無し・head node 推定は稿にだけある。

## 工数

codex 5 本 (author 1、review 2、fix 1、focus 1)。計算ノード job = 焦点走 3 + 変異 (baseline 1 + 15) + 受入。受入は記録 commit 後の tip に対して実行し、receipt を land へ渡す (ここでは受入完了を先書きしない)。
