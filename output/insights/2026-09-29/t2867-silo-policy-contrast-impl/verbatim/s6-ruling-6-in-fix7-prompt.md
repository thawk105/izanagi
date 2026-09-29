単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl

必読事項の射影: (各 file は読めなければ即停止し、読めなかった path を報告の先頭に書いて終える)
- 段 6 裁定 5: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/artifacts/s6-ruling-5.md
- fix 1 の共通契約: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/artifacts/s6-fix1-common.md
- 段 5 の共通の契約: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/artifacts/s5-common.md
- 親の焦点走 log (赤 1 件): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/focus-6.log

## 依頼 — fix 7 子 Z (テストだけ、段 6 裁定 6)

作業 tree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z` (branch `t2867-sc-fix7-z`、fix 6 までを統合した commit の上。ここだけに書く)。
所有 path: `orchestrator/tests/test_silo_policy_contrast_round.py`、`orchestrator/tests/test_silo_policy_contrast_parent.py`。実装 file は変えない。

裁定 6 (親):
1. `test_schema_failures_consume_one_a_and_do_not_retry` の後半 (finalize で driver が構造化 JSON を返さず非 0) は、fix 5 の時点の挙動 (`auditor-schema` の却下) を期待したまま残っており、裁定 5 の P1 (構造化 JSON の無い非 0 終了は終端を書かず例外) と食い違う。この wave で足したテストなので裁定 5 の挙動へ直す: finalize が例外を出し、`opportunity-end` が増えないことを確かめる。前半 (coder が JSON として読めない → `coder-schema` の却下 1 回だけ、driver を呼ばない) は変えない。
2. 変異 m14 (親の `claude -p` argv に `--continue` を足す) が生存した。親のテスト (`test_fresh_sessions_and_429_retry_same_a` か新しい 1 本) に、各起動の argv が `--resume`・`--continue`・`-c`・`--session-id` のどれも含まないこと (1 原提案ごとに新しい session、草稿 §4.1) を確かめる assert を足す。
変更は合計 40 行以内。報告形は段 5 の共通の契約のとおり (`## 変異の位置` は不要)。
