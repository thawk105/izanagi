単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 焦点再レビュー対象 (fix 1 適用後の insight README): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/README.md
- 段 6 レビュー A の所見 15 件と訂正案 (fix 1 の根拠): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/s6-review-A.md
- 一次資料の写し (README の全数値の出所): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/ の self-startup-timeline.txt、submodule-init.log、gate-time.txt、wt_timeline.out、scan_startup.out、inspect_modules.out、inspect_links.out、t2797-setup-submit-tree.log.filtered、t2797-tree-build-mtimes.txt、ls-files-count.txt、submodule-ls-files.txt (fix 1 で追加)、probe.log
- 段 3 相談の所見と段 4 裁定: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/s3-consult-A.md、同 dir の s4-ruling.md
- 依頼の逐語: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-wave-startup-cost/output/insights/2026-09-21/wave-startup-cost/verbatim/origin.md

## 前置き — この依頼の性質

段 6 独立レビュー A は NO-GO (must-fix 5 = 所見 2・3・4・5・7、should = 所見 6・8・9・11・12・13 の表現改善) だった。親は docs-only の insight README を直接訂正した (fix 1: §冒頭の script 束縛の注記、§3.1 の残差の帰属と 9.4% の分母、§3.2 の列名と残差の説明・並行数、§3.4 の HANDOFF 標本の再整理、§3.5 の CPU 比・file 数の一次出力・store 容量・hardlink の範囲、§3.6 の木の本数と概算・S1 の扱い、§6 の +60 秒、§7 の ABA の回数と推奨文、§8 の所見集計と DW-G05、§10 の追加)。**所見ごとに closed / partial / regressed の対応表を作り、訂正後の派生値を一次資料から再計算せよ。** 訂正が新しい誤り (regressed) を生んでいないか、訂正案どおりでない書き方が残っていないかを見る。セキュリティでも攻撃でもなく、外部入力も扱わない。書込み可能 tmp が無いので静的検査でよい。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

# 依頼 — 焦点再レビュー (1 本)

1. s6-review-A.md の所見 1〜15 それぞれについて、README の該当行 (file:line) を引き、**closed / partial / regressed** と 1 行の根拠を書け。partial / regressed は残る差分を置換前→置換後の形で示せ。
2. fix 1 で新たに書いた派生値を再計算せよ: §3.1 の 79.16 / 9.4%、§3.2 の「重なりは最大 6 本」「`index` 後 15 s」、§3.4 の 8 本 / 5 例 / 38 s、§3.5 の 18.7% / 56.0% / 21.5%、405 + 790 + 245 = 1,440 (submodule-ls-files.txt)、§3.6 の 3〜6 本 / 4〜6 本 / 18〜96 s / 1.2〜9.6 分、§7 の「workers=1 が 2 走、8 が 1 走」、§8 の must-fix 6 / should 5 / 判定不能 1 / refuted 1 と、段 6 の must-fix 5 / should 6 (s6-review-A.md の所見の分類から数え直せ)。
3. §8 の「本 wave の DW-G05」の書き換えが、s3-consult-A.md 所見 13 の追加 should と s4-ruling.md 所見 13 の処置に一致するか。
4. 訂正後の README が依頼 (origin.md) の scope を超えていないか、§10 が本文と矛盾しないかを再確認せよ。

## 出力形式
- `## 対応表` (所見番号、closed/partial/regressed、file:line、根拠 1 行)、`## 再計算` (値ごとに一致/不一致)、`## 残る訂正` (置換前→置換後)、`## 総括` (必須、GO / NO-GO と残 must-fix 件数)。
