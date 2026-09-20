単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (所見の採否と fix1 の仕様): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/s6-adjudication.md
- レビュー A 逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-review-A.md
- レビュー B 逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-review-B.md
- fix1 の報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-fix1.md
- fix1 の patch (レビュー対象の差分): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/codex/s6-fix1.patch
- 生成器 (fix1 統合後の現物、commit 7debd680c): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/plot_k2_loop_flow.py
- 流れ JSON (同): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/tools/plotting/k2_loop_flow_2026-09-20.json
- test (同): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/orchestrator/tests/test_plot_k2_loop_flow.py
- fix1 後に実データで生成した provenance (drawn_items・arrows・caption の現物): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-k2-loop-fig12/scratch/fig12_k2_manual_loop_dataflow.provenance.json
- caption_source の稿: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-k2-loop-fig12/docs/paper-story/results/2026-09-20-k2-manual-loop-three-rounds.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。書込可能 tmp が無いので pytest 緑は要求しない — 静的検査でよい。テスト実測は親が行う (fix1 後の親の自走 harness は 104 passed / 1 failed (未着地 T9) 13.07 s)。予算が尽きそうなら途中結論を出力形式どおり書いて終われ。

## 前置き — この依頼の性質

研究用 repo の論文用説明図 (matplotlib の模式図) の生成器・入力 JSON・単体 test に対する fix1 の焦点再レビューである。セキュリティでも攻撃でもない。生成器は凍結済みの稿から人が JSON へ写した「3 巡のデータフロー」を描くだけで、判定・値・認証を再計算しない。性能値は図のどこにも出ない。

# 依頼 — 焦点再レビュー: 段 6 裁定の各所見が fix1 で閉じたか (closed / partial / regressed) と、fix1 が持ち込んだ回帰

1. 段 6 裁定「所見の裁定」表の**全行** (A-M1、B-M1、B-M2、B-M3、A-S1、A-S2、A-S3/P1、A-S4/B-S3、B-S1、B-S2、B 表の負例不足、A-nit1、A 削除候補、親の目視 8 項) について、fix1 統合後の現物 (file:line) を根拠に closed / partial / regressed を判定する。fix1 の報告を鵜呑みにせず現物で確かめる。
2. fix1 の報告が挙げた仕様差 (実測の還流「2 回」に対し measurement-reflux の矢印は m1 / m2a / m2b の 3 本; caption は「還流元の評価で数えて twice」「描画経路は three times」を生成) を検査する: caption の実文 (provenance の `caption`) が稿 §0.1 (実測の還流 2 回、診断の還流 1 回) と矛盾しないか、読み手に「還流 3 回」と読めないか。矛盾・誤読の余地があれば must-fix。
3. 新しい表示文字列 (drawn_items の 50 件、特に `data boundary: none detected`、`synthesizes one backoff literal`、`backoff literal <v> known / not known`、列見出し、副題、凡例 legend-r6) と caption の固定文 7・8 を稿と照合し、稿に無い主張・誤読の余地を挙げる。
4. fix1 の回帰: 生成器の受理集合が裁定の意図を超えて広がっていないか (typed discipline6 の bool true を受理する設計は裁定どおり)、test の期待値の緩和・skip・xfail が無いか、M7 fixture が単一理由か (文字列不変で `_drawn_items` が通る)、`test_t6_publish_runs_layout_check` の 3 種が publisher を通るか、`test_t7_arrows_bind_artists_and_caption` が JSON から独立に期待を組むか。
5. 変異登録 (裁定末尾 + fix1 報告の M11a / M11b) の各変異について、位置が一箇所か、kill する nodeid が現物に存在するか、mask する層が無いか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。見出しはすべて H2)

## 対応表
所見ごとに closed / partial / regressed、根拠 (file:line と引用 1〜2 行)。
## caption の回数語の判定
2 の結論と根拠。
## 所見 (must-fix)
番号付き。file:line、根拠、放置時の成果物への影響 1 行、推奨 fix 1 行。
## 所見 (should)
同上。
## 所見 (nit)
同上、短く。
## 変異の単一理由性
M1〜M11b の判定と根拠。
## 総括
GO / NO-GO と must-fix の件数、closed / partial / regressed の件数、根拠を 5 行以内。
