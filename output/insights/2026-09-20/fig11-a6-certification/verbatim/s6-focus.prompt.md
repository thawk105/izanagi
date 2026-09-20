単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (所見ごとの採否と対応。この表が閉じたかを判定する): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/s6-adjudication.md
- レビュー A の本文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/review-A.md
- レビュー B の本文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/review-B.md
- fix 子の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/codex/fix1.md
- fix 差分 (レビュー時点 wave tip ffcee706b → 現 tip 02fa41e25 の 4 file。画像除く。commit 済み): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/verbatim/focus-diff.patch
- 生成器 (現 tip): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/tools/plotting/plot_a2_certification.py
- test (現 tip): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/orchestrator/tests/test_plot_a2_certification.py
- figures README の fig11 節 (末尾の節): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/README.md
- 着地 provenance (再生成後): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json
- caption_source の稿: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig11-a6-certification/docs/paper-story/results/2026-09-18-a6-certification-reject.md
- 変異 spec (probe、m0〜m9 の 11 件。現在計算ノードで実走中): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig11-a6-certification/mutation-spec-v1-probe.json

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

段 6 の設計レビュー 2 本 (A: 過剰・削除、B: 正しさ境界・整合) の所見に fix を当てた後の**焦点再レビュー**である。セキュリティ調査ではない。
親が実行済み: fix 差分の統合 commit (bdc6e8401)、fig11 の再生成 (login、rc=0、PNG bytes 不変・PDF/provenance 更新)、README fig11 節の編集 (02fa41e25)、
local main d4af98f15 の取り込み (merge 33db2ed88、図の README 末尾に fig10 の追補が入り、その後ろに fig11 節)、焦点走 111 passed、全史 provenance 監査 違反なし。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査でよい。

# 依頼 — 所見ごとに closed / partial / regressed を判定する

## 点検項目

1. 段 6 裁定の表の各行 (A-1/B-4、A-2、A-3/B-3、A-4/B-5、B-1、B-2、B の対応表 2 点、A の削除候補) について、裁定の「対応」欄が実装・文書で実際に閉じたかを、
   差分・現 tip・provenance の caption・README の本文で確かめる。親が書いた派生値 (README の SHA-256 3 行、caption の値、稿 §4 限定の番号、file 数、cell 数) は
   原データ (provenance JSON、稿、certification.json) から再計算・再照合するまで closed としない。
2. fix による退行: A-2 (fig5 / fig6 / fig7) の caption・provenance 射影が不変か (fix 差分に A-2 枝の変更が無いこと)、受理集合が変わっていないこと、
   既存 test の期待値が変わっていないこと (fix 差分で変更された test は段 6 裁定が名指す新設 test の固定文と着地 test の追加だけか)。
3. 新 caption (再生成後の provenance) を稿 §0 / §2.3 / §4 限定 1〜12 と再照合し、B の対応表で「欠落」「不一致」とされた行が解消したか、新しい過剰主張が入っていないか。
4. README fig11 節の書き換え (A-4 / B-5、closure の射程、作図規約への適合の短縮、正しさの限定) が実装と一致し、fig5 節の「作図規約への適合」を指す記述が正しいか。
5. 変異 spec v1-probe の 11 件: old 逐語が現 tip に 1 箇所ずつ存在するか、m6a / m6b の分割が段 6 裁定と一致するか、単一理由性が疑わしいものが残るか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く)

## 所見ごとの対応表
段 6 裁定の各行 (と B の対応表の 2 点) について closed / partial / regressed と根拠 (file・関数・節・照合した値) を 1 行ずつ。
## 新規所見
fix で入った新しい問題があれば `F-1`〜 で採番し、種別と DW-G05 の 1 行。無ければ「無し」。
## 総括
GO / NO-GO と、残る partial / regressed の要旨を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること (無出力が最悪)。
