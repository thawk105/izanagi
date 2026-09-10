## 変更

- [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:313)
  - 広い候補 regex で全 execution queue 行を数える段を追加。
  - 候補が一行かつ Request ID より後方であることを確認後、既存の厳格 regex で `@nqsv` と queue 名 `gen_S` を検証。
- [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:316)
  - visibility 負例を二件追加。
- docs、fixture bytes、変更禁止 pathには触れていません。git add、commitも実行していません。

## 追加テスト

- `test_visibility_rejects_each_noncanonical_observation[M11-second-queue-other-server]`
  - 正常な実機 RUN に `Queue = other@other (Execution Queue)` を追加。
  - 候補識別を厳格 regex と再結合する弱実装 M11 を殺します。
- `test_visibility_rejects_each_noncanonical_observation[queue-count-two-other-name]`
  - 正常行に `Queue = other@nqsv (Execution Queue)` を追加。
  - 同 server の別 queue を含む二行も拒否することを固定します。

いずれも `subprocess.run` の monkeypatchから production関数 `_observe_qstat_visibility` を通します。

## 実走

次の nodeidを `tools/run_tests.py` へ渡しました。

- `orchestrator/tests/test_paper_story_a1_job_contract.py::test_real_nqsv_visibility_flows_through_acquisition_validator`
- `orchestrator/tests/test_paper_story_a1_job_contract.py::test_visibility_rejects_each_noncanonical_observation`

結果は rc=16でした。`qstat -Q` preflightが rc=1となり、`child_started=false` のため、実装済み・未実走です。

既存テストの赤は観測していません。テスト自体が開始されていないため、緑とも報告しません。`git diff --check` は成功しました。

## 静的確認

- 実機 RUN、PRR、Queued: 唯一の厳格 queue 行を持つため引き続き受理。
- 実機 RUNと別 serverの二本目: 広い候補が二行となり拒否。
- 実機 RUNと同 server別名の二本目: 広い候補が二行となり拒否。
- execution queue行ゼロ本: 候補数がゼロとなり拒否。

## 総括

候補数の検査と唯一候補の厳格書式検証を分離し、レビュー A 所見1の穴だけを修正しました。変更は対象の実装一ファイルとテスト一ファイルに限定されています。