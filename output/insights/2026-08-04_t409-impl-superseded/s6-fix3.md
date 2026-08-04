H-1〜H-3 をすべて静的に closed としました。既存の correctness-red 不変条件や admission gate は緩めていません。

| 項目 | 状態 | 対応 |
|---|---|---|
| H-1 | closed | report 専用の診断付き admitted view を追加。record は共有 admission で検証済みのものだけを採用し、`line_issues` と `truncated_tail` を復元 |
| H-2 | closed | immutable view の tuple/Mapping を JSON の list/dict へ戻してから T-080・execution receipt を厳密検証 |
| H-3 | closed | axis 名だけでは未束縛、明示 materialization で束縛、既存競合値は上書きせず拒否、の3点へ更新 |
| regressed | 0 | 静的確認上なし |

変更ファイル:

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/artifact_admission.py:452)
- [s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/campaign/s8b_oracle_report.py:128)
- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_artifact_admission.py:381)
- [test_s8b_oracle_report.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_s8b_oracle_report.py:76)
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t409-impl-trigger-grammar/orchestrator/tests/test_campaign.py:288)

期待値を変更した既存 node は承認済みの次の1件だけです。

- `orchestrator/tests/test_campaign.py::test_trigger_axis_identity_binds_language_without_overwriting_conflict`

H-1 の既存期待値は変更していません。診断付き admitted view の production 経路を検査する新規 parametrized node を追加しました。

検査結果:

- pytest: **0件**（Pegasus ログインノードのため未実行）
- `python3 -m py_compile`: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0

通常の `require_admitted_campaign()` は厳格なままです。診断付き API も malformed frame を record として採用せず、report の最終状態は `protocol_violation` のままなので、受理集合の無承認拡大はありません。report source bytes が変わったため、次回実 campaign 前の oracle manifest 再発行要件は残ります。

## 総括

- closed/partial/regressed = **3/0/0**（静的判定、pytest 未実測）。
- H-1 の診断復元と admitted-record authority を両立した。
- H-2 は T-080・execution receipt の immutable JSON 型変換も閉じた。
- 親は request 888402 の H-1 10 node、H-2 の2 node、H-3 の1 nodeを再実測すること。
- 新規 `test_diagnostic_admitted_view_keeps_only_shared_validated_records` も実測対象。
- 残リスクは計算ノードでの pytest 未実走と oracle manifest 再発行。