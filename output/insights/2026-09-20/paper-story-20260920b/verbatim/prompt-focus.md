単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/codex/review-out.md (1 本目の read-only レビューの出力、所見 10 件、NO-GO)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/codex/prompt-review.md (1 本目の prompt。レンズ・不変条件・出力形式の正本)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/codex/r22.py (親が当てた fix の逐語 15 件。`REPL = [(old, new), ...]`)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-20260920b/docs/paper-story/2026-09-20b.md (**fix 後の新版**、4,547 行 — 全文 `cat` 禁止。`grep -n` で位置を出し `sed -n` で 80 行以内ずつ読め)

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (出力は最終メッセージ本文に全文)。
pytest・build・測定は走らせない。予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割

**fix 後の焦点再レビュー 1 本** (`DW-O16`)。1 本目の所見ごとに、fix 後の本文で closed / partial / regressed を判定せよ。
親の裁定: 所見 1〜6 = real / must-fix、7〜8 = real / should-fix、9〜10 = refuted (レビュー自身の裁定と同じ。現状維持)。
親が当てた fix (r22.py、置換 15 件): 所見 1 = §0 項 11・§2 (a)・§8 B-1 の「限定 16 件」→「19 件」(cohort2 稿の 16 件は正しいので不変)、
所見 2 = fig8b の PDF `c5454544…` → `c5454454…` (親は job dir の `check_hashes.py` で版の 8 桁 prefix 43 件を figures / results / provenance の
現物と集合比較し、29 件一致・残り 14 件は commit sha / identity / 較正・凍結の digest)、所見 3 = 冒頭の訂正 1 と §10 (P2) の「07:14 着地
(`b664df20c`)」→「fold `45994d900` 04:42:32 (導入 commit `ad88a391c` 04:22:41)」、所見 4 = §0 第 3 幕の要約・§0 末尾・§2 (g) 冒頭と末尾・
§9 冒頭の B-5 の言い方 (「試走を投入可能にする経路 / 機構」→「共有部品の一部が着地、上限付き試走は認可済みだが投入に要る実装は残る」、
「機構 3 件」→「機構 2 件と投入へ近づける部品 1 件」)、所見 5 = §0 項 12 の「前版 (2026-09-19 版)」→「論文ストーリー 2026-09-19 版」、
所見 6 = §2 (e) 項 6 の「wire integrity」→「非 wire integrity の同一性確認」、所見 7 = §7 の verifier 項の禁止句を「正しさの判定基準が
変わった / 既存判定が変更された、と書かない。実装 bytes は変わり、照合した判定は同一」へ、所見 8 = §4 共通段落を「専用の着地テストがある
図はそのテストで照合し、fig3b は git の履歴で辿る」へ。加えて §10 の「段 6 — 本文に対する敵対レビュー」小節を完了形 (所見 10 件と裁定) で
書いた。**§10 の「焦点再レビュー」小節は、お前の完了後に親が書く。草稿の時点では「(草稿では予定形。)」であり、完了形の先取りが無いことを
確かめよ。**

## 検査項目

1. **所見ごとの closed / partial / regressed 表。** 対案どおりに直っているか、直し方が別の誤りを生んでいないか (例: 所見 1 で cohort2 稿の
   16 件まで 19 に変えていないか、所見 3 で他の箇所に「07:14」が残っていないか、所見 4 で「投入を可能にする機構 3 件」が残っていないか、
   所見 5 で他の「前版 (2026-09-19 版)」型の誤変換が無いか)。親が書いた派生値・件数 (§7 の 100 項、§0 の 13 点、19 稿、限定 19 件、5 版、
   4 か所) は原データから数え直して照合するまで closed としない。
2. **§10 の完了形のレビュー小節の記述が、review-out.md と親の fix の実体に一致するか** (所見の要旨・real/refuted・fix の対応。誇張・脱落・
   「レビューが確認した」範囲の水増しがあれば指摘)。
3. **新規所見。** fix が触った箇所の周辺と、1 本目が「未完」と自ら書いた範囲のうち、費用内で当たれる範囲 (§6・§8 の状態語、§9 表の第 6 種) を
   再点検し、新規の must-fix / should-fix / nit を出せ。**所見ごとに放置時の影響を 1 行で書け** (書けない所見は nit)。
4. 不変条件は 1 本目の prompt「守らせる不変条件」と同じ。これを緩める所見は refuted。

## 出力形式 (この見出しをそのまま使う)

## 所見ごとの対応表

| # | 親の裁定 | closed / partial / regressed | 根拠 (fix 後の本文の位置と逐語) |

## 新規所見

番号付き。`real / refuted`、`must-fix / should-fix / nit`、該当節、対案、放置時の影響。

## GO / NO-GO

## 総括

10 行以内。
