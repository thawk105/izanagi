## 総括

指定された2件だけを最小差分で修正しました。

- [check_ai_provenance.py:104](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:104): `CorrectionAudit.exact` を「raw candidateがexact 1件、かつfindingなし」の連言へ変更。candidate 0件では単独利用しても必ず`False`になります。
- [test_check_ai_provenance.py:1279](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/orchestrator/tests/test_check_ai_provenance.py:1279): empty auditの`exact=False`を明示的に固定。既存のvalid=`True`、invalid=`False`テストも維持しています。
- [check_ai_provenance.py:744](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-ai-provenance-forward-fix/tools/check_ai_provenance.py:744): candidate診断を「prospective parent ancestry 全体」に修正。
- 通常childとmerge-sideの双方で、新しい診断文言を期待するようテストを更新しました。

実走結果:

- `pytest`: **116 passed in 5.85s**
- `py_compile`: rc=0
- `git diff --check`: rc=0
- `check_codex_agents.py`: rc=0
- `check_docs.py`: rc=0、違反なし

未達はありません。commit・push・docs・output・handoff・その他ファイルの編集は行っていません。作業開始時から存在した未追跡のwave outputはそのまま残し、指定されたcheckerとtestの2ファイルだけを編集しました。fix2前snapshotとの差分も監査し、今回の2所見に対応する変更以外が混入していないことを確認済みです。