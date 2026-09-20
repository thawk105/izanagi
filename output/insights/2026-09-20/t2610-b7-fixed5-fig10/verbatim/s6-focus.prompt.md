単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (所見ごとの採否と処置。closed 判定の基準): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/s6-adjudication.md
- レビュー A の原文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s6-review-A.md
- レビュー B の原文: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s6-review-B.md
- fix 子の最終報告: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/codex/s6-fix1.md
- fix 後の差分 (04ae82a1c → 6fbe7d017、画像 2 file を除く。fix commit e6a291d44 = 生成器 + test、図・docs commit 6fbe7d017 = 親担当): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-fig10/verbatim/fix1-diff.patch
- 生成器 (現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/tools/plotting/plot_b7_fixed5_regression.py
- test (現物): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/orchestrator/tests/test_plot_b7_fixed5_regression.py
- figures README の fig10 節 (末尾の節): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/README.md
- 着地 provenance (再生成後): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.provenance.json
- caption_source の稿: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-fig10/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

## 前置き — この依頼の性質

これは自分たちの研究用 repo の論文図生成器への fix の**焦点再レビュー**である。セキュリティ調査ではない。段 6 裁定が採用した所見 (A-1/B-2、A-2、A-3 文言、A-4、A-5 DF、B-1、B-3) が fix 差分と親の docs で閉じたか、退行が無いかを点検する。
親が実行済み: 図の再生成 (PNG bytes 不変 583e94f6…、PDF と provenance は更新)、README の caption 正文と着地 SHA-256 3 行の実値化、login での自走 harness 42/42 passed、check_docs 緑。焦点走 (計算ノード) と変異本走は並行して親が回している。
読み取り専用 sandbox なので pytest 緑は要求しない。静的検査と `python3` での値の再計算 (読むだけ) はしてよい。

# 依頼 — fix の焦点再レビュー

## 点検項目

1. 所見ごとの closed / partial / regressed の対応表 (A-1、A-2、A-3、A-4、A-5 (DF)、B-1、B-2、B-3)。closed の根拠は差分の該当 hunk と現物の行で示す。
2. 派生値の再計算: README fig10 節と provenance の caption に出る百分率 (効果 3 値、−floor 3 値)、着地 SHA-256 3 行、provenance の `authority_scope`、固定文 2・6 の逐語を、
   一次資料 (稿、certification.json、床値 JSON、現物 file) から独立に照合する。
3. 退行: fix で受理集合・provenance の key 集合・図の形が変わっていないか。境界 test 2 本が実体の関数を通し、`<` → `<=` と correctness の trace_enabled 検査の恒真化を
   それぞれ単独で検出できる形か (m13 / m14 の単一理由性)。着地 test の標本束縛が durable root 無しで動くか。
4. 親 docs の文言 (A-3: 「判定の出所は稿の転記で、述語は整合検査にだけ使う」、A-4) が実装と一致するか。

## 出力形式 (最後の節は必ず `## 総括`。`#` を 2 個。`### 総括` と書いてはならない。出力は最終メッセージ本文に全文を書く — file へは書けない)

## 対応表
所見 id | closed / partial / regressed | 根拠 (hunk・行・照合結果)。
## 派生値の照合
一致 / 不一致の表。
## 退行と残る所見
新たな must-fix があれば `F-1`〜 で採番し、放置時に成果物がどう変わるか (DW-G05 の 1 行) を書く。
## 総括
GO / NO-GO と、closed / partial / regressed の件数を 5 行以内。予算が尽きそうなら途中結論をこの形式で書いて終わること。
