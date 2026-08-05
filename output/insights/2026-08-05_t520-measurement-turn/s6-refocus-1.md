## 対応表

| 前回所見 ID | 状態 | 根拠 |
|---|---|---|
| ADM-01 | closed | grandfather 4本は `class=local-ok` を維持し、未実測なのは `evidence` であること、実測時に変わるのは evidence のみであることが明記された。[pegasus-runbook.md:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:373)、[decision fragment:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:19) |
| FACT-01 | partial | registry と fail-closed gate の存在自体は訂正されたが、「機械強制は `tools/pegasus/` 配下だけ」という新たな過大限定が入り、runbook が記録する他の機械 gate と矛盾する。[tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29)、[pegasus-runbook.md:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:459) |
| FACT-02 | closed | D175 決定4・F123の測定経路裁定待ちと、D175 決定2の grandfather 裁定待ちについて、置換対象と現行裁定が明記された。[decision fragment:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:19) |
| TURN-01 | partial | runbook の依頼手順は全項目を列挙して閉じたが、decision fragment の決定本文には `memory.max`・測定日などが欠けたままで、同じ決定の正本候補同士が不一致である。[pegasus-runbook.md:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:389)、[decision fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:14) |
| BYPASS-01 | partial | runbook の新規規範は未配線・解析不能な実行面を抽象化し、抜け道利用を禁止した。[pegasus-runbook.md:385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:385) 一方、worklog の既存台帳 item には4系統の分類が残る。[worklog fragment:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:45) |
| SPOOL-01 | closed | `diff2.patch` は両 fragment の本文を収録しており、現在の staged diff と byte-for-byte 一致した。[diff2.patch:45](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t520-measurement-turn/diff2.patch:45)、[diff2.patch:95](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t520-measurement-turn/diff2.patch:95) |

BYPASS-01 の部分採用判断は妥当と判断する。残った記述は既存台帳 item の remediation 入力として閉鎖対象を保持するもので、利用方法や実行手順ではなく、全系統を閉じ方の検討対象にする文脈に限定されている。新規の規範本文へ再列挙しないという境界も守られている。したがって残存は land blocker としない。

`tools/README.md` の縮約では、分類前実行の禁止、`unknown` の fail-closed、sanctioned 経路がなければ停止、変更時の再分類という安全義務は維持されている。[tools/README.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:8) 警告も、新規重量処理が検査を通過し得ること、および文書を読まない実行面が止まらないことまで残っている。[tools/README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:24)

grandfather も4本だけの例外であり、他 entry は未実測なら `unknown` に倒して停止するため、「未実測一般を許可できる」とは読めない。[pegasus-runbook.md:373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:373)、[pegasus-runbook.md:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:389)

## 新規所見

### FACT-03 / must-fix

- file:line: [tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29)
- 何が壊れるか: 「機械強制は `tools/pegasus/` 配下だけ」は分類 admission に限定されておらず、`tools/run_tests.py` と `tools/check_ai_provenance.py` の login-node 拒否・自動 dispatch という機械 gate が存在する事実と矛盾する。[pegasus-runbook.md:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:459) FACT-01の不存在記述を、別方向の過大限定へ置き換えている。
- 修正案: 主語を「**資源分類 admission registry の機械強制**は `tools/pegasus/` 配下に限られる」と限定する。後続の「他は prompt 規律」も「他の tools の資源分類」に限定する。

### REQ-01 / must-fix

- file:line: [decision fragment:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/decisions/2026-08-05-dev-wave-t520-measurement-turn-1.md:14)
- 何が壊れるか: decision fragment が測定依頼を `commit / argv / 入力 bytes・件数 / 繰り返し数` と定義し、`memory.max`、測定日、各回の観測ピークを落としている。runbook 上部の記録契約と手番手順は完全だが、fold 後に decision だけを引いたセッションは不完全な依頼を作れる。
- 修正案: [pegasus-runbook.md:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/pegasus-runbook.md:348) の全項目を列挙するか、「§7.0『記録すること』の全項目」と一義的に参照する。

### LOG-01 / must-fix

- file:line: [worklog fragment:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/docs/spool/worklog/2026-08-05-dev-wave-t520-measurement-turn-2.md:24)
- 何が壊れるか: fragment は FACT-01 を「scope 外・実装せず・`tools/README.md` に触っていない」と記録しているが、今回の staged diff は同ファイルを実際に修正している。[tools/README.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t520-measurement-turn/tools/README.md:29) land 後の canonical worklog が変更内容について虚偽になる。
- 修正案: この bullet を、敵対レビューの FACT-01 を採用して同 wave 内で是正した記録へ更新する。将来タスクへ送ったという記述は削る。

## 総括

1. **land 可否: NO-GO**
2. **残 must-fix: 3件** — 機械強制範囲の過大限定、decision fragment の依頼項目不足、worklog fragment の「未修正」という旧記述。
3. **確認できなかったもの:** pytest その他の動的テスト、hook の実発火、fragment が主張する過去のテスト結果、spool fold 後の生成結果、commit 後 provenance 監査。これらを緑とは判断していない。静的には全指定資料を読了し、`diff2.patch` と staged diff の一致および `git diff --check` 成功を確認した。