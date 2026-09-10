結論は **NO-GO** です。pytest、checker 実走、編集、commit、ファイル生成は行っていません。以下は静的レビュー結果です。

## Findings

1. **must-fix — merge 前後で D95 の path 意味論が一致しない**

   履歴側は通常 `diff-tree` を使うため merge commit の path が空になりますが、message-file 側は index と first parent の差を使い、second parent から来た既存実装をすべて新規変更として扱います。[tools/check_ai_provenance.py:415](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:415) [tools/check_ai_provenance.py:422](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:422) [tools/check_ai_provenance.py:657](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:657)

   実 target では通常 `diff-tree` は空、combined name-status は docs 3 path、per-parent union は `tools/` と `orchestrator/tests/` を含みました。この偽赤は既に T-186 handoff で実測されています。[T-186 handoff:64](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t173-codex-cleanup-branches-skill.md:64) [T-186 handoff:99](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t173-codex-cleanup-branches-skill.md:99)

   `MERGE_HEAD` 中の preflight と commit 後監査が同じ merge-path 定義を使うか、競合なし merge 専用の明示フローを定義する必要があります。虚偽の Codex author trailer で通してはいけません。

   放置すると: T-145/T-146/T-186 の main 再統合が preflight では偽赤、commit 後には緑となり、D95 と O17 が不整合になります。

2. **must-fix — selected-set 契約が `OLD_HEAD..HEAD` 監査と両立しない**

   checker は correction が選択範囲にあり target が範囲外なら必ず拒否します。[tools/check_ai_provenance.py:542](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:542) これは `C^!` を赤にする裁定どおりです。[s1-brief.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-brief.md:14) [s4-adjudication-plan-v2.md:35](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:35)

   しかし target を既に持つ長寿命 branch が corrected main を初めて merge すると、`OLD_HEAD..HEAD` は correction を含み target を除外します。したがって delta audit は赤、full audit は緑になります。これは現在停止中の3 branchすべてに起き得ます。[T-145 handoff:32](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t145-resume-main-reconciliation.md:32) [T-146 handoff:59](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t146-probe-cleanup.md:59) [T-186 handoff:83](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t173-codex-cleanup-branches-skill.md:83)

   target ancestry を selected membership の代わりに認めるのか、correction 検出時だけ target-inclusive range へ展開するのか、裁定を戻して決める必要があります。

   放置すると: 推奨する `OLD_HEAD..HEAD/full audit` の両方を green にできず、停止中 consumer が恒久的に再開不能になります。

3. **must-fix — 再発防止の運用変更が必須 plan に入っていない**

   現行 O17 は一般的な message-file と post-commit audit だけで、`merge --no-commit`、`commit -F`、OLD_HEAD、競合時停止を定義していません。[docs/dev-wave/operations.md:89](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/dev-wave/operations.md:89) plan の親 docs 一覧にも operations/handoff 更新がなく、O17 改訂は handoff の「段8候補」に留まっています。[s4-adjudication-plan-v2.md:39](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:39) [wave handoff:36](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-ai-provenance-forward-fix.md:36)

   また brief/handoff は T-173 しか停止 consumer として挙げませんが、T-145 と T-146 も同じ欠落で停止しています。[s1-brief.md:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-brief.md:18) [T-145 handoff:24](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t145-resume-main-reconciliation.md:24) [T-146 handoff:56](/home/SFC/tanab/github/izanagi/docs/handoff/2026-07-29-t146-probe-cleanup.md:56)

   F25/F37 の単純な「再発」とするか、新しい「auto-merge が preflight/post-checkpoint を迂回」の型とするかも routing が必要です。F25 は trailer block 組立ミス、F37 は pipeline rc 喪失が現行定義です。[docs/failures.md:314](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/failures.md:314) [docs/failures.md:625](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/failures.md:625)

   放置すると: checker は過去1件だけを救済しますが、次の自動 merge を止める既存 consumer がなく、「恒久対策」という記録がコードだけの空証明になります。

4. **must-fix — 830行の test が実 target の normal finding 集合を固定していない**

   production pin は SHA、2-parent、message 欠落だけを確認します。[test_check_ai_provenance.py:1052](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1052) 実 target を `_normal_commit_audit` して「missing 1件だけ、D95/CAB findingなし」とは検査していません。全 acceptance test は synthetic target へ singleton を monkeypatch します。[test_check_ai_provenance.py:101](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:101) [tools/check_ai_provenance.py:457](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:457)

   実 target の `CommitAudit.normal_findings` を exact 1件で固定し、target-specific D95 前提を production control に含めるべきです。

   放置すると: synthetic tests が green でも、実 correction commit 後の default history が追加 D95/CAB finding で赤のままという失敗を検出できません。

5. **must-fix — M1〜M11 は独立 kill matrix になっていない**

   `DW-M03` は診断文字列だけの赤を kill と数えず、`DW-M08` は構造化 signal pin を別枠に要求します。[docs/dev-wave/mutation.md:17](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/dev-wave/mutation.md:17) [docs/dev-wave/mutation.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/dev-wave/mutation.md:49)

   現 prereg には少なくとも次の問題があります。

   - M10 は stdout status だけなので明白な diagnostic sensitivity pin です。[s4-adjudication-plan-v2.md:60](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:60)
   - M8 は normal-green 条件を外しても correction commit 自身の finding が残り、rc=1 のままです。[tools/check_ai_provenance.py:564](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:564)
   - M5 は raw finding を消しても `CorrectionAudit.exact` の raw exact 比較が残ります。[tools/check_ai_provenance.py:100](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:100) [tools/check_ai_provenance.py:245](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:245)
   - M11 の body+valid fixture は multiplicity finding以外にも、raw 1行条件、`.exact`、selected-set cardinalityで過剰決定されています。[tools/check_ai_provenance.py:235](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:235) [tools/check_ai_provenance.py:523](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:523)

   M8/M10等を diagnostic pin に移し、M3/M5/M11は意味上の全 enforcement siteを明示した combined mutant にするか、単一理由 fixtureへ再照準する必要があります。

   放置すると: mutation ledger が診断差を「KILLED」と過大計上し、Stage 6 acceptance artifact が `DW-M03/M08` 違反になります。

6. **should-fix — singleton incident に対して test/abstraction が過大**

   変更量は checker 314追加/24削除、test 830追加です。`ForwardCorrectionSpec.key` は固定値なのにフィールド化され、test側の `CorrectionHistory.root` は使用されません。[tools/check_ai_provenance.py:70](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:70) [test_check_ai_provenance.py:90](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:90)

   既存 validator が個別に覆う missing/format/scope/CAB/Codex-author を、新規 matrix が「別 commit」と「correction commit」で5種ずつ再構築しています。[test_check_ai_provenance.py:1433](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1433) [test_check_ai_provenance.py:1504](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1504) parser alias testも共有 parser の既存検査と重複しています。[test_check_ai_provenance.py:1236](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1236)

   production control、merge pre/post parity、correction propagation rangeを追加する代わりに、重複 matrixと未使用フィールドを削れる余地があります。

   放置すると: test consumer の実行コストと内部表現への結合が増え、singleton 契約の将来撤去・変更が不必要に高コストになります。

7. **should-fix — 「combined resolution 3 path」は用語を狭めるべき**

   target は `git merge main --no-edit` により約5秒後に自動生成された2-parent objectで、手動 conflict resolution の証拠はありません。[s1-recovery-evidence.md:8](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-recovery-evidence.md:8) combined name-status の docs 3 pathは「両 parent と異なる path集合」であり、そのまま手動 resolution を意味しません。

   新 D では、通常 `diff-tree` 空集合、combined-diff docs 3 path、per-parent union の実装 pathを分離し、role=integrator は merge前の採否判断を根拠にするべきです。[s1-recovery-evidence.md:14](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-recovery-evidence.md:14)

   放置すると: 新 decision が「mergeは通常path空だからD95非適用」という一般則へ誤読され、将来の実装 conflict resolution を無検査にする根拠になります。

8. **refuted — 復元 payload に evidence との不一致や後知恵 scope 混入はない**

   evidence は model/effort の raw fieldと、role の行為裁定を分離し、`scope` を後日分類として明示的に除外しています。[s1-recovery-evidence.md:6](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-recovery-evidence.md:6) [s1-recovery-evidence.md:18](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s1-recovery-evidence.md:18) production literalも完全一致します。[tools/check_ai_provenance.py:79](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:79)

   放置すると: この点では consumer/artifact の不整合はありません。

9. **refuted — stdout/exit code 自体は識別可能**

   history は correction 適用を full SHA付きで stdout に出し、違反があれば stderrとrc=1、実行不能ならrc=2です。[tools/check_ai_provenance.py:676](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:676) [tools/check_ai_provenance.py:681](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:681) correction message-file は「preflight限定」「commit後監査必須」を明示します。[tools/check_ai_provenance.py:690](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:690)

   通常子として作る実 correction message は既存 `commit -F` / `--message-file` consumer で検査可能です。ただし実 message artifact はまだ無いため、Stage 7 の pre/post 実走は未確認です。merge consumer の問題は findings 1〜3です。

   放置すると: rcを正しく見る consumerには曖昧さはありません。rcをパイプで失う運用だけはF37再発になります。

10. **refuted（限定）— docs byte cap と task ID の接続点は明確**

   `docs/ai-provenance.md` は現在8,832 bytesで、9,000-byte独立上限と9,001-byte負例が既に機械化されています。[tools/check_docs.py:163](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_docs.py:163) [test_check_docs.py:441](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_docs.py:441) planも例を縮約して上限内に置くと明記しています。[s4-adjudication-plan-v2.md:40](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:40)

   task ID も land時再走査を明記し、D70の並行 branch 非予約契約と一致します。[s4-adjudication-plan-v2.md:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/output/insights/2026-07-29_ai-provenance-forward-fix-wave/s4-adjudication-plan-v2.md:19) [docs/decisions.md:2702](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/docs/decisions.md:2702)

   放置すると: byte cap/task ID単体の不整合はありません。ただし停止 consumer 全件の handoff反映は finding 3 の必須作業です。

## 総括

**NO-GO。blocker は5件です。**

- merge preflightと履歴監査のD95 path意味論を一致させる
- correction初回伝播時の `OLD_HEAD..HEAD` 契約を再裁定する
- O17・failure・全停止handoffを任意のStage 8候補でなく必須成果物へ昇格する
- 実 production target の normal finding 集合をテストで固定する
- M8/M10等をdiagnostic pinへ分離し、M3/M5/M11の単一理由性を再登録する

payload、normal-child correctionのstdout/rc、byte cap、land時task IDは blocker ではありません。pytest green は主張しません。