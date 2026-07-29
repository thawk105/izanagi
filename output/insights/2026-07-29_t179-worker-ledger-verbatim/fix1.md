F-1〜F-12 をすべて実装し、最終検査は 91 passed / 0 failed です。docs、`tools/check_codex_output.py`、commit／stage／push には触れていません。

### F-1〜F-12 対応表

| Fix | 状態 | 実装箇所 |
|---|---|---|
| F-1 | closed | usage 5 field の型・欠損検査、bool 拒否、token 内訳公開: [codex_worker_ledger.py:153](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:153)、[test_codex_worker_ledger.py:277](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:277) |
| F-2 | closed | 中立名への改名、event count、cumulative 非単調検査: [codex_worker_ledger.py:210](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:210)、[test_codex_worker_ledger.py:361](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:361) |
| F-3 | closed | `model_calls` / `turn_contexts` 分離と docstring: [codex_worker_ledger.py:1](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:1) |
| F-4 | closed | session ID 小文字化、複数 meta・case 重複検査: [codex_worker_ledger.py:225](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:225)、[test_codex_worker_ledger.py:263](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:263) |
| F-5 | closed | 先頭非空行限定、ambiguous、focus、到達可能な fix2 author: [codex_worker_ledger.py:39](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:39)、[codex_worker_ledger.py:312](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:312) |
| F-6 | closed | root／0件 gate、非 object、選択 file 限定 issue、cwd 欠落: [codex_worker_ledger.py:660](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:660)、[test_codex_worker_ledger.py:625](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:625) |
| F-7 | closed | retry key を `(cwd, prompt_hash)` 化: [codex_worker_ledger.py:370](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:370)、[test_codex_worker_ledger.py:457](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:457) |
| F-8 | closed | validator の最小 byte・最大サイズ・fence 外総括と同値化: [codex_worker_ledger.py:328](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:328)、[test_codex_worker_ledger.py:952](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:952) |
| F-9 | closed | stage-map unknown を走査全体の ID と照合: [codex_worker_ledger.py:678](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:678)、[test_codex_worker_ledger.py:833](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:833) |
| F-10 | closed | 指定 entry 本文・fence 外だけで工数行探索: [codex_worker_ledger.py:424](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:424) |
| F-11 | closed | root／rollout path の `resolve()`: [codex_worker_ledger.py:180](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:180)、[test_codex_worker_ledger.py:1008](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:1008) |
| F-12 | closed | human／JSON totals と session stage/model/reasoning を literal oracle 化: [test_codex_worker_ledger.py:469](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:469)、[test_codex_worker_ledger.py:919](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:919) |

### pytest

- `orchestrator/tests/test_codex_worker_ledger.py`: 73 passed / 0 failed
- `orchestrator/tests/test_check_codex_output.py`: 18 passed / 0 failed
- combined: 91 passed / 0 failed
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: rc=0

途中で1件、fix2 author の旧期待が `fix` のまま残って赤になりました。裁定どおり到達可能な `author` oracle に訂正後、最終赤はありません。`ruff` は環境に未導入で実行できませんでした。

### 単一理由 fixture

- M2′: [case_duplicate.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/case_duplicate.json:1)
- M5′: [incomplete_task_only.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/incomplete_task_only.json:1)
- M6a total-only: [total_only.md](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/worklogs/total_only.md:1)
- M6b review-only: [review_only.md](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/worklogs/review_only.md:1)
- M9: [malformed_usage_type.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/malformed_usage_type.json:1)
- M10: [no_selected.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/no_selected.json:1)
- M11: [stage_hijack.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/stage_hijack.json:1)

M7 は [retry.json](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/cases/retry.json:1) を diagnostic sensitivity pin と明記。M8 は `_healthy_specs()` の strict rc=0 正例を維持しています。

### 波及可能性

- repo 内に台帳 CLI の直接 caller は見つかりませんでした。
- 外部 consumer は `turns`、`compaction_delta` から新列名へ追随が必要です。差分の符号も `cumulative - per_turn` です。
- 親 docs／insight の旧列名、実ログ期待値、stage 表は親側で更新が必要です。
- validator の private 定数・fence helper を再利用しているため、将来の validator policy 変更時は同値テストも追随します。
- 新規 fixture は未追跡状態を含むため、親統合時に取り込み漏れ確認が必要です。
- `tools/check_codex_output.py` と所有外テストは変更していません。

## 総括

F-1〜F-12 はすべて closed。指定3領域だけを変更し、commit・git add・push・docs 編集は行っていません。

親は統合後に、未追跡 fixture の取り込み、実10 session の再集計、新列名・符号の docs 追随、最終 commit 上での mutation anchor／matrix 本走を確認してください。