単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl

必読事項の射影: (各 file は読めなければ即停止し、読めなかった path を報告の先頭に書いて終える)
- 焦点再レビュー 2 巡目: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/codex/s6-focus-2/out.md (新しい所見 1・2)
- fix 1 の共通契約: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/artifacts/s6-fix1-common.md
- 段 5 の共通の契約: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2867-silo-contrast-impl/artifacts/s5-common.md
- 事前登録の草稿 §3 (A だけを消費するもの) と §5.5: /work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z/docs/silo-policy-generator-contrast-preregistration.md

## 依頼 — fix 5 子 Z (段 6 裁定 4)

作業 tree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2867-sc-author-z` (branch `t2867-sc-fix5-z`、fix 4 までを統合した commit の上。ここだけに書く)。
所有 path: `tools/silo_policy_contrast_round.py`、`tools/pegasus/silo_policy_contrast_parent.py`、`orchestrator/tests/test_silo_policy_contrast_round.py`、`orchestrator/tests/test_silo_policy_contrast_parent.py`。

裁定 4 (親、焦点 2 巡目の所見 1・2 は real、所見 3 は裁定 3 の N5 と同じで refuted):
1. **所見 1 (must-fix):** round の `check` と `finalize` で、coder・auditor の出力が JSON として読めない・閉じた schema に合わない・driver の preview が構造化 JSON を返さず非 0 で終わった場合は、例外で落とさず **A を 1 消費する却下** として同じ a の `opportunity-end rejected` を 1 度だけ記録する (`reject_subtype` は `coder-schema` か `auditor-schema`、`reject_rule_id` は driver の stderr の最初の行か `invalid-json` のような短い識別子)。driver の preview の既存の構造化拒否 (`passed=false`) の扱いは変えない。親はこの結果を役割の異常終了として数えない (round が `rejected` を返すので終端が確定する)。
2. **所見 2 (should-fix):** 親は `out` に既に `attempt-NNNN` があれば、最大の番号の次から数える (別プロセスで再開しても dir が衝突しない)。失敗回数の数え方 (追加 2 回まで) は、その a の既存 attempt の `exit.json` を数えて引き継ぐ。
各 1〜2 本のテスト。**既存テストの期待値を変更しない。** 変更は合計 120 行以内。報告形は段 5 の共通の契約のとおり (`## 変異の位置` は不要)。
