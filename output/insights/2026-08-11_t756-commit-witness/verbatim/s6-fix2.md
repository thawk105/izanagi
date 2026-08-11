F1〜F6 はすべて実装済みです。docs・`report.py`・index は変更しておらず、commit も作成していません。

## F1〜F6 判定

| 項目 | 判定 | 根拠 |
|---|---|---|
| F1 | 満たす | S2 が pipeline の厳格 parser を共有し、欠落・重複・負数・非整数を拒否、batch 非0も verifier 前に拒否します。[s2_verify_calibration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:57)、[同:122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:122)、[同:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:129)。回帰は [test_build_site_gate.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_build_site_gate.py:103)。 |
| F2 | 満たす | 不在・非 directory・検査時 `OSError` を `_TraceDirUnavailable` に構造化し、`trace-no-commit-witness` WAL へ落とします。[pipeline.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:277)、[同:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:323)、[同:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:951)。 |
| F3 | 満たす | 残骸テストを subprocess spy 化し、呼び出し0回を固定しました。[test_campaign.py:6293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6293)。`preexisting_trace` seam の WAL reason/files/workload 検査は [同:6170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_campaign.py:6170)。 |
| F4 | 満たす | 元 nodeid と no-witness `res.certified` assert を復元し、witness 付き indeterminate node を併置しました。[test_verifier.py:609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:609)、[同:622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:622)。 |
| F5 | 満たす | `g1_serial` に witness 3 を渡し、rc `3`、`certified=false`、`indeterminate`、literal mismatch note を固定しました。[test_verifier.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:827)。 |
| F6 | 満たす | no-witness `result_to_dict` を consumer と同じ `indent=2, ensure_ascii=False` で直列化し、独立 literal bytes と完全一致させました。[test_verifier.py:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/tests/test_verifier.py:759)。 |

## 新設・復元 nodeid と変異対応

- `test_s2_run_once_accepts_unique_zero_batch_commit_witness` → [s2_verify_calibration.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:129) を `== 0` に反転すると赤。
- `test_s2_run_once_rejects_duplicate_main_commit_witness` → [pipeline.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:244) の一意性条件を緩めると赤。
- `test_s2_run_once_rejects_duplicate_batch_commit_witness` → 同じく `pipeline.py:244` を緩めると赤。
- `test_s2_run_once_rejects_missing_main_commit_witness` → [s2_verify_calibration.py:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/s2_verify_calibration.py:124) の main `None` guard を外すと赤。
- `test_s2_run_once_rejects_missing_batch_commit_witness` → 同行の batch `None` guard を外すと赤。
- `test_s2_run_once_rejects_negative_commit_witness` → `pipeline.py:244` で負数を許可すると赤。
- `test_s2_run_once_rejects_noninteger_commit_witness` → `pipeline.py:244` の十進整数検査を外すと赤。
- `test_s2_run_once_rejects_nonzero_batch_commit_witness` → `s2_verify_calibration.py:129` の batch guard を削除すると赤。
- `test_pipeline_unavailable_trace_dir_rejects_with_structured_wal` → [pipeline.py:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:951) の専用 catch を削除すると赤。
- `test_pipeline_preexisting_trace_rejects_with_structured_wal` → [pipeline.py:947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:947) の `preexisting_trace_files` を削除すると赤。
- `test_run_trace_rejects_missing_trace_dir_before_subprocess` → [pipeline.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:323) を削除すると赤。
- `test_run_trace_rejects_nondirectory_trace_dir_before_subprocess` → [pipeline.py:325](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:325) を削除すると赤。
- `test_characterization_tail_txid_gap_is_false_green`（復元）→ [model.py:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:148) の no-witness 互換節を削除すると赤。
- `test_cli_expected_commits_mismatch_is_indeterminate_json` → [cli.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/cli.py:68) の `expected_commits=` を削除すると赤。
- `test_result_to_dict_without_commit_witness_matches_frozen_json_bytes` → [report.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/report.py:44) 以降の key・値・順序を変えると赤。

既存 node `test_run_trace_rejects_preexisting_trace_files_before_subprocess` も強化済みで、[pipeline.py:334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:334) の guard を無効化すると subprocess 呼び出し回数が0でなくなり赤になります。

## 受理集合

- 正常な一意 main witness・一意 batch witness `0` は引き続き受理。
- 重複・欠落・負数・非整数・batch 非0の S2 出力は新たに verifier 起動前で拒否。
- 不在・非 directory・残骸ありの `trace_dir` は before/after とも拒否。after は汎用例外ではなく構造化 WAL。
- no-witness optional API の既存受理、integrity 連言、`certified` 条件、pipeline の拒否3種は変更なし。

したがって受理集合は緩んでおらず、F1 の破損 stdout 分だけ狭くなっています。

## 差分・検査

```text
 orchestrator/campaign/pipeline.py              | 37 ++++++++--
 orchestrator/campaign/s2_verify_calibration.py | 21 +++---
 orchestrator/tests/test_build_site_gate.py     | 80 ++++++++++++++++++++++
 orchestrator/tests/test_campaign.py            | 95 ++++++++++++++++++++++++--
 orchestrator/tests/test_verifier.py            | 80 +++++++++++++++++++++-
 5 files changed, 291 insertions(+), 22 deletions(-)
```

- `git diff --check`: 問題なし
- 変更5ファイル: AST 構文確認済み
- docs 差分なし
- `orchestrator/verifier/report.py` は差分に現れないことを確認
- index 差分なし。`git add`・commit とも未実施
- pytest: sandbox の socket 拒否条件に従い、実装済み・未実走。緑は主張しません。実測は親待ちです。

## 総括

F1〜F6 はすべて満たしています。production は fail-closed のまま、受理集合の緩和はなく、変更はコード2ファイル・テスト3ファイルだけです。