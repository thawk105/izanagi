## 対応表

| 所見 ID | 状態 | 修正後の根拠 |
|---|---|---|
| ADM-01 | closed | grandfather は4本限定で、`class=local-ok` を維持し、実測時に変わるのは `evidence` のみと明記された。[pegasus-runbook.md:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:373)、[decision fragment:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:20) |
| FACT-01 | closed | registry と未登録 fail-closed gate の存在を認める文面へ修正された。[tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29)、[guard_bash.py:596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/hooks/guard_bash.py:596) |
| FACT-02 | closed | D175 決定2・4およびF123の旧裁定待ちについて、置換対象と現行裁定が一義的に記録された。[decision fragment:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:18) |
| TURN-01 | closed | ユーザー依頼は§7.0「記録すること」の全項目を要求し、必要項目も本文に揃っている。[pegasus-runbook.md:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:348)、[pegasus-runbook.md:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:389) |
| BYPASS-01 | partial | 規範本文は具体的な未配線面を列挙せず、抜け道利用を明示的に禁止した。[pegasus-runbook.md:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:385) 一方、worklog の既存タスク更新には閉鎖対象4系統の名称が残る。[worklog fragment:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:64) 閉じ方の検討対象を同定する台帳文脈に限られるため、残存自体は blocker としない。 |
| SPOOL-01 | closed | `diff3.patch` は2 fragmentの本文を含み、SHA-256 が現在の staged diff と一致した。fragmentを未読にする欠落はない。[decision fragment:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:1)、[worklog fragment:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:1) |
| FACT-03 | partial | 「機械強制」一般から「分類の機械強制」へ限定されたが、直後の「他の tools の分類は…止める gate は無い」は、個別の機械 gate がある2本まで含む読みに依然としてなる。[tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29) |
| REQ-01 | closed | decision fragment も§7.0「記録すること」の全項目への一義参照になった。[decision fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:14) |
| LOG-01 | closed | 「触っていない」という旧記述は削除され、敵対レビュー後に同 wave 内で是正した経緯へ書き換えられた。[worklog fragment:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:24) |

`tools/README.md` の縮約では、分類前実行の禁止、`unknown` の fail-closed、正規経路がなければ停止、変更時の再分類、文書を読まない実行面への警告は維持されている。[tools/README.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:8)、[tools/README.md:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:33)

## 新規所見

### FACT-04 / must-fix

- file:line: [tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29)
- 何が壊れるか: 「他の tools の分類は prompt 規律で、止める gate は無い」は無限定である。実際には `tools/run_tests.py` と `tools/check_ai_provenance.py` がログインノードを検出し、自動 dispatch または拒否する機械 gate を持つ。[run_tests.py:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/run_tests.py:930)、[check_ai_provenance.py:1056](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/check_ai_provenance.py:1056)、[pegasus-runbook.md:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:459)。FACT-03 の限定はまだ狭すぎ、別種の個別 gate を不存在扱いしている。
- 修正案: 主語を「三値 admission registry による包括的な分類強制」に絞る。例えば「三値 admission registry による分類強制は `tools/pegasus/` 配下に限る。他の tools を包括する分類 gate はないが、個別の site gate は存在する」とする。

### LOG-02 / must-fix

- file:line: [worklog fragment:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:47)
- 何が壊れるか: 「commit 後に再走して閉じた」と記録しているが、現在の最終4ファイルは staged 状態で、2 fragment を含む commit はまだ存在しない。canonical worklog に、未実施の将来操作を完了事実として残すことになる。
- 修正案: 「commit 後」を削り、実際に検査した差分と時点を記す。post-commit 再走は、実行後にのみ完了事実として記録する。

## 総括

1. **land 可否: NO-GO**
2. **残 must-fix: 2件** — 分類機械強制の範囲がなお不正確、worklog が未実施の post-commit 検査を完了済みと記録。
3. **確認できなかったもの:** pytest、`tools/check_docs.py`、`spool_fold.py --dry-run` の実行結果、hook の動的発火、親が報告した受入全走3回の数字、spool fold 後の生成結果、commit 後 provenance 監査。これらを緑とは判定していない。指定資料はすべて静的に読了し、`diff3.patch` と現在の staged diff の一致のみ独立確認した。