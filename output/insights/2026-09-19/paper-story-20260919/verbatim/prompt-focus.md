単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/codex/review-out.md (**1 本目のレビューの所見 9 件**。お前はこれの焦点再レビューである)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/2026-09-19.md (**fix 反映後の新版**、3,298 行 — **全文 `cat` しないこと**。`grep -n` と `sed -n` で 80 行以内ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-story-2026-09-19/docs/paper-story/README.md (変更なし)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260919/brief-s1.md (親の段 1 brief)

**巨大 file の扱い:** `docs/decisions.md` (5.6 MB) は `grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。
`docs/paper-story/2026-09-17.md` (前版、309 KB) も同じ。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (read-only sandbox では `-o` の
file を書けない)。pytest・build・測定は走らせない。予算が尽きそうなら途中までの結論を下記の出力形式どおりに書いて終われ。

## 親が当てた fix (所見番号は review-out.md と同じ)

1. 受理集合 — §9 運用方法論 1 つ目、§0 前進 8、§2 第 1 幕の [T-2731] 段落、§2 (e) 項 1 の 4 箇所を「既存 silo 8 genome の
   pre-image は旧版 / 新版で byte 一致、`#if TRACE` 内の指令も差分素材になるため `_trace_pair_diff` の受理集合は狭まる向きに
   変わる (D2108)」へ。`grep -n "狭まる向き"` で当たる。
2. 完了形の先取り — §10 に段 1・段 6 (1 本目の所見 9 件と裁定・照合範囲) を書き、冒頭の完了形を真にした。§10 の「fix 後の
   焦点再レビュー」小節はお前の完了後に親が書く (草稿では「これから通す」と書いてある。これは意図した形)。
3. 前版由来の「この版で」 — §2 (c) 8c の `n`、§2 (c) と §8 B-4 の「較正だけではない」、§2 (d) の撤去要求、§2 第 2 幕の高域、
   §2 (f) の [T-1998] 再現、§5 の規律 7、§2 (c) 床値四段の見出し、§7 の「この版の更新」18 項 → 「前版で」「2026-09-15 に確定し
   前版へ反映」「前版の更新: … / この版の更新: …」へ。
4. 訂正対象の版 — §1・§2 (c)・§3・§5・§7・§8 A-4 の「前版は…と書いた (冒頭の訂正 N)」→「2026-09-14 版まで…と書いていた
   (前版の冒頭の訂正 N)」へ。`grep -n "冒頭の訂正"` で全箇所が「前版の冒頭の訂正 N」形であることを確かめよ。
5. §7 層3 の項 → 「前版の更新: screening … / この版の更新: 機序仮説層 v3 は K2 2 巡目で初適用、非 certifying の二次 view、
   機序の証拠ではない (D2143)」へ。
6. pin 前進の認可状態 — §6 の「言えること」、§0 前進 3、§1 のスコープ段落、§8 C-1 の 4 箇所 → 「探索・軸採用は未解禁。pin 前進は
   D2150 項 1 の手順で承認済みだが未実施、pin は `511c9538`」へ。[T-2772] wave 時点の「未解禁」は同 wave 時点の言葉として限定。
7. §8 B-4 の「spec の非保証欄と D に残す」→ D2138 項 9 の記録先訂正を引いて「D と insight に残す。spec に非保証欄は無い」へ。
8. [T-2774] の 5 arm — §8 C-1 (i) を因子 1 つずつの鎖 (`p058-plain` 058d0c4e X/P なし → `e9-plain-nowit` X/P なし → `e9-instr-nowit`
   → `e9-instr-wit` → `e9-diag-wit`) に書き直し、§2 第 1 幕と §5 の「観測 3 件は e9e477ca + 計装 patch」の注記を「[T-2779] /
   [T-2780] の全 arm と [T-2774] の後段 3 arm は計装あり、先頭 2 arm は X/P 無し」へ。
9. §4 Fig 8 — 検算範囲を `figures/README.md` fig8 節の逐語 (平均 2 種・変動係数 2 種・abort 率の標本標準偏差だけ照合、CI と
   端点比は再計算のみ) へ、hash の出所を「PNG / PDF は provenance の `outputs[].sha256`、provenance 自身は着地 file の SHA-256」へ。

## お前の仕事

- **所見ごとの closed / partial / regressed の対応表を作れ (DW-O16)。** 各行に、fix が当たった箇所を `grep` で実測した行番号と、
  一次資料 (D2108 / D2138 項 9 / D2150 項 1 / D2143 / T-2774 insight §4 / figures README fig8 節) との照合結果を書け。
- **fix による退行 (regressed) を探せ。** 特に、(a) 「狭まる向き」の追記が「既存 identity は動いていない」「記録済み測定は無効化
  しない (規律 7)」と両立して書かれているか、(b) [T-2772] の「未解禁」限定と D2150 項 1 の「承認済み・未実施」が §0・§1・§6・§8 で
  食い違っていないか、(c) 5 arm 鎖の書き直しで検出数の順序 (2/40・3/40・2/40・0/40・0/40) が arm と対応しているか、(d) §7 の
  「前版の更新 / この版の更新」の分割で、恒久 (規律) の語が落ちていないか、(e) §10 の所見要約が review-out.md の所見と食い違って
  いないか (件数・分類・対案)。
- **1 本目が「未完の範囲」とした §5〜§8 の置換箇所の意味上の脱落と、残る「この版で」「前版」の時点ずれを、時間の許す限り
  追加で拾え。** 新規所見は must-fix / should-fix / nit と real / refuted を付けよ。
- 守らせる不変条件 (これを緩める所見は refuted): 凍結物不変、旧判定の不取消、protocol status は成否宣告でない、B-10 は §4.5 の
  固定表現、「A-1 の値がある」「B-10 を閉じた」「mocc は第 2 成功例」と書かない、稼働中 wave の内容を書かない。

## 出力形式 (この見出しをそのまま使う)

## 対応表

| # | 所見 | 判定 (closed / partial / regressed) | 実測した箇所 (行番号) | 根拠 |

## 新規所見

番号付き。real / refuted、must-fix / should-fix / nit、該当節、一次資料、対案、放置の影響 1 行。無ければ「なし」。

## GO / NO-GO

## 総括

10 行以内。
