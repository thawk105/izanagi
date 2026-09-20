単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- fix 群の累積差分 (レビュー対象。base = 初回統合 commit 92263e53e、tip = fix 統合 commit 6dae18be1。docs fix 1 82c53b98d + pin 47e1730b7 + docs fix 2 b36da2b09 + docs fix 3 8901d6b62 + pin 6dae18be1): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/s6-fix-cumulative.diff.txt
- 初回レビュー (自分または前任の所見 1 must-fix / 所見 2 nit、NO-GO): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-review.md
- 親の段 6 裁定 (所見の採否、fix 1・fix 2・fix 3 の内容と理由): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/s6-adjudication.md
- 親の削減・追加の対応表 (fix 後に追随済み。A3 = fix 2、R10 = fix 1 の §4 縮約、R11 = fix 3。**これ自体が検査対象**): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/reduction-table.md
- 一次資料 (loss record): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/loss-record-README.md、F1034: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/verbatim/F1034.md
- Codex fix 子の報告 4 本: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-fix1.md (受理)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-fix2.unaccepted.md (未受理、余白 0 で停止)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-fix3.unaccepted.md (未受理、内容は 4 巡目が監査)、/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/codex/s6-fix4.md (受理、監査、変更 0)
- 段 7 記録の草稿 (worklog fragment。事実主張を検査): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2814-cleanup-command/worklog-fragment-draft.md
- repo 内 (fix 統合 commit 済みの wave worktree、read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2814-cleanup-command/ 配下の
  `.claude/commands/cleanup-branches.md` (最終本文 6,201 bytes)、`.agents/skills/cleanup-branches/SKILL.md` (3,060 bytes)、
  `docs/spool/failures/2026-09-21-dev-wave-t2814-cleanup-command-2.md` (F728 再発 + F1034 supersede、untracked)、
  `tools/check_docs.py` (`grep -n "CLEANUP_COMMAND_SHA256\|CODEX_CLEANUP_BRANCHES_SKILL_SHA256"` で位置を出し `sed -n` で読む)、
  `orchestrator/tests/test_check_docs.py` (`grep -n "_EXPECTED_CLEANUP_\|== 6_201\|== 6_205\|\"x\" \* 3\|非施錠\|remote branch 削除\|非 dir entry"` で位置を出し `sed -n` で読む。
  **5749 行と 5772 行は非 NFC fixture なので、その行を含む範囲を絶対に出力しない (出力すると本レビューの成果物が未受理になる)。全文 cat しない**)。

書込可能な tmp は無い。pytest 緑を要求しない。静的検査でよい。親の実測: fix 統合 commit 6dae18be1 で check_docs 違反なし、provenance 全史 12188 件違反なし、
Codex 4 巡目 (監査) 580 passed / 3 skipped、焦点走 19 file 3869 passed / 16 skipped / 1 failed (赤は untracked の spool fragment を検出する inventory test で、記録 commit 後に再走予定)。

## 依頼 — fix 後の焦点再レビュー (DW-O16): 所見ごとの closed / partial / regressed 表

初回レビューの所見 1 (must-fix: §3 の検算条件が一次資料と不一致) と所見 2 (nit: R6 は手段指定の削除) に対する fix と、fix の過程で親が足した 2 変更 (fix 2 = §2 高い条件に
「非施錠」、fix 3 = §5 の助詞 1 語削除) を検査する。差分を守らず検査する。各所見に「何が・どこで・どう壊れるか」と放置時の成果物影響 1 行を書く。

1. **所見 1 の closed 判定:** 新文「`ls-files -o` の list 数を tar の非 dir entry 数が下回れば撤去しない (F1034)」が一次資料 §4「tar の非 dir entry 数が list 数を下回れば撤去せず rc=6」と
   受理集合が一致するか (「下回れば」の向き、「非 dir」の限定、等しい・上回る場合の扱い)。SKILL.md overlay の「非 dir entry 数照合」も同じ条件を指すか。
2. **所見 2 の対応:** 対応表 R6 と worklog 草稿の「手段指定の削除 1 件」の記述が事実として正確か (本文は変えていない)。
3. **fix 2 (非施錠) の妥当性:** 「削除直前に status 空と非施錠を再確認」が (a) 一次資料 (memory の記録: 棚卸し後に /rulings session が submit-tree-pair を lock、prune は locked を
   跳ばすが dir の rm はその前に済む) の罠を塞ぐか、(b) 「§1 の」を落としたことで「status 空」の参照先が曖昧にならないか (削除直前に新規取得する status と読めるか)、
   (c) §2 安い条件の「locked … は inventory/report のみ」と二重・矛盾にならないか、(d) 「非施錠」の語が判定手段なしで読めるか (§2 安い条件と F51 の文脈)。
4. **fix 3 (助詞削除) の意味不変:** 「remote branch の削除と main の push」→「remote branch 削除と main の push」。
5. **pin 整合:** 本文 6,201 bytes = `_SYNTHETIC_CLEANUP_COMMAND` = sha c8db749b… (定数 2 箇所)、超過入力 `"x" * 3` で 6,205、SKILL 側 3,060 / 3cf0344d… が不変。
   fix 2 巡目が実測した「余白 0 は既存 test と衝突」の新事実が裁定・対応表・worklog 草稿に正しく書かれているか (test 名・理由)。
6. **regressed の探索:** fix 1〜3 で初回レビューが GO と判定した項目 (R1〜R5・R7〜R9、A1、P1〜P4、T-2601 閉鎖) が退行していないか。§4 の縮約 (R10「§1 の status と比べ」) が
   §4 の検査の意味 (cleanup 前後で surviving worktree・index・repo file に新しい差分が無い) を変えないか。
7. **記録の事実性:** failures fragment (F728 再発の本文、F1034 supersede の引用が最終本文と一致するか) と worklog 草稿の段 6 の記述 (fix 巡数、未受理の理由、T-2041 見送り追記) が
   一次資料 (fix 子の報告 4 本) と一致するか。

## 出力形式

- 見出しはすべて `##`。節: `## 所見対応表` (初回の所見 1・2 それぞれに closed / partial / regressed と根拠 1 行)、`## 新規所見` (fix 2・fix 3・記録に対する所見。番号付き、
  must-fix か nit か、放置時の成果物影響 1 行、根拠。ゼロなら「ゼロ」と何を検査したかを列挙)、`## 親裁定への反証` (あれば)、`## GO / NO-GO` (must-fix があれば NO-GO)、
  最後に `## 総括`。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終わる (無出力が最悪)。
