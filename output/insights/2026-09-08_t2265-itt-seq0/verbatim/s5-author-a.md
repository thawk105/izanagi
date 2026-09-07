## 実装した内容

- [backoff_counterfactual_analysis.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/campaign/backoff_counterfactual_analysis.py:1)
  - cohort 専用・v2 束縛成果物拒否を docstring に明記。
  - `ANALYSIS_VERSION` を `/v2` へ更新。
  - 成果物用 v1 SHA と解析文書用 v2 SHA を別定数として固定。
  - `_load_artifact` と `_validate_row` は呼出側から hash を受け取らず、v1 literal を内部使用。
  - `_run_difference` は `events[1:]` から pair、index、outcome count を再構成。
  - 0 commit 検査を残存全 event に限定。`assignment_rate_all_events` は raw event のまま。
- [test_backoff_counterfactual_analysis.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/tests/test_backoff_counterfactual_analysis.py:21)
  - v1/v2 SHA と version を test-local literal で固定。
  - rebasing、seq0 zero、seq>=1 zero、artifact 三形態、v2 file binding の各検査を追加。
  - fixture の成果物 SHA を逐語 v1へ変更。
  - 位置除外後の件数を forward 11、invert 12、outcome 47/23へ更新。
  - 既存自走 harness は維持。

## 受理集合の前後

- 変更前: `(v1 束縛成果物, v1 文書)` を受理し、raw seq 0 を推定と0 commit判定に含めた。
- 変更後: `(v1 束縛成果物, v2 文書)` を受理し、raw seq 0 を推定から除外する。
- raw seq 0 の zero は判定を止めないが、seq 1 以降に zero が1件でもあれば全体を `window_commits_zero` で inconclusive にする。
- 成果物への射影では受理集合を拡大していない。top-level・全 rowとも exact v1 SHAが必要で、v2束縛成果物は拒否する。
- v1文書と将来のv2束縛成果物は、このcohort専用解析器では意図どおり拒否される。
- schema、軸、seed、build、trace等の既存gateは変更していない。

## 実走

- `python3 tools/run_tests.py orchestrator/tests/test_backoff_counterfactual_analysis.py`
  - rc=16。`qstat -Q` preflightによるdispatch infrastructure failureで、childは未起動。
  - runnerが `output/pegasus-dispatch/.../receipt.json` を自動生成。
- `PYTHONPATH=. python3 '/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265seq0-a/orchestrator/tests/test_backoff_counterfactual_analysis.py'`
  - 初回 rc=1: 24 passed、1 failed。位置除外後に極端値がarm平均へ希釈されたため、正のfixture値を強めて修正。
  - 最終 rc=0: 対象ファイル全25 node、25 passed、0 failed、0 errors。

必須nodeを含む全ファイル範囲を実走済みです。

- `::test_seq_zero_is_excluded_before_pairing_and_membership_is_rebased`
- `::test_seq_zero_zero_commit_is_v1_inconclusive_but_v2_confirmatory`
- `::test_seq_ge_one_zero_commit_remains_inconclusive_under_v2`
- `::test_artifacts_remain_bound_to_literal_v1_preregistration_sha`
- `::test_analysis_preregistration_file_is_bound_to_literal_v2_sha256`
- `::test_public_analysis_pairs_next_window_and_uses_equal_run_clusters`

meta-test本体は射影外なので開かず、必読所見に記載された条件と、既存 `_run` / `pytest.main` / `__main__` harnessが残っていることを確認しました。新規test fileはありません。

## 波及

- 親のinline callerはv2文書と既存v1束縛成果物を組み合わせる必要がある。
- private関数 `_load_artifact` / `_validate_row` の旧hash引数形式は廃止。射影資料で確認されたlive callerは同moduleと対象testのみ。
- test-local共有fixture `_write_artifacts` は常にv1束縛成果物を生成する。
- `_synthetic_cluster` を使う既存consumer testも含め、対象全25件が通過。
- 将来producerが生成するv2束縛成果物は意図的に非対応。producer側は変更していない。
- 凍結成果物12件は開かず、実解析も行っていない。

## 総括

- must-fix: 所有範囲内には残っていない。
- 未解決: 実成果物12件の解析と最終判定は親の担当。
- docs、commit、git add、branch操作、所有外ソースの編集は行っていない。