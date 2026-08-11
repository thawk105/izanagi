`report.py` を段5前へ完全復元し、依存テストを既存 schema の観測点へ移しました。production の正しさ判定は変更していません。

## 変更内容

- `orchestrator/verifier/report.py`
  - `integrity.commit_witness` の挿入を削除。
  - `render_text` の witness 専用行を削除。
  - `git diff --exit-code -- orchestrator/verifier/report.py`: `rc=0`
  - 現在の SHA-256: `e604cef0b06dc36dd8e236b8ade92eb452231a5f32b7926405b402f038e9d8a2`
  - worktree/HEAD の Git blob ID はともに `9265f39fa069890dd80c12f715652f5c5667bfb0`

- `orchestrator/verifier/__init__.py`
  - report schema に依存せず、`expected_commits` 公開 API の説明なので維持。

- `orchestrator/campaign/pipeline.py`
  - 編集なし。
  - `verify_payload["commit_witness"]` と各 abort payload の構造化 witness を維持。

## 書き換えたテスト

- `orchestrator/tests/test_verifier.py::test_commit_count_witness_result_is_structured`
  - `notes` の完全一致・1本だけ、`clean is False`、`certified is False` を固定。
  - [core.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/core.py:39) の delta 生成行を壊すと赤。

- `orchestrator/tests/test_verifier.py::test_commit_witness_partial_state_is_unclean_without_report_schema_change`
  - 部分 witness が新 schema key を生やさず、fail-closed になることを固定。
  - [model.py:161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/model.py:161) の `and commit_witness_clean` を外すと赤。

- `orchestrator/tests/test_verifier.py::test_result_to_dict_commit_witness_changes_notes_without_new_keys`
  - witness 有無で全 dict key 集合が同一、新しい `commit_witness` key がなく、witness 値は `notes` だけに現れることを固定。派生ゲート値の `clean/certified/verdict` は別途検査。
  - [report.py:70](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/verifier/report.py:70) の notes 投影行を壊すと赤。

- `orchestrator/tests/test_campaign.py::test_pipeline_tail_loss_witness_reaches_verifier`
  - abort 側の `notes/clean/certified` と、`STAGE_VERIFY_DONE.commit_witness` の構造化経路を固定。
  - [pipeline.py:1006](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t756-trace-v2/orchestrator/campaign/pipeline.py:1006) の witness 格納行を壊すと赤。

## 受理集合

Before / After ともに同一です。

```text
accepted =
  commit witness が有効
  ∧ batch witness == 0
  ∧ serializable
  ∧ Integrity.clean()
```

`Integrity.clean()` の `observed_commits == expected_commits` 条件と、`certified` の integrity 必須条件は維持されています。不一致時は `indeterminate`、`clean=False`、`certified=False` のままです。変わったのは report の出力投影だけです。

## 差分確認

`git diff --stat`:

```text
orchestrator/campaign/p3_s4_red.py                 |  12 +-
orchestrator/campaign/pipeline.py                  | 132 +++++++++++-
orchestrator/campaign/s2_verify_calibration.py     |   9 +-
orchestrator/campaign/s8b_abort_reason_contract.py |   3 +
orchestrator/campaign/silo_ladder_rung1.py         |  20 ++
orchestrator/critic/digest.py                      |  23 ++-
orchestrator/tests/test_build_site_gate.py         |  27 +++
orchestrator/tests/test_campaign.py                | 226 +++++++++++++++++++--
orchestrator/tests/test_critic.py                  |  52 +++++
orchestrator/tests/test_s1_direct_comparison.py    |  17 +-
orchestrator/tests/test_s8b_oracle_driver.py       |  16 +-
orchestrator/tests/test_s8b_oracle_report.py       |  15 ++
.../tests/test_silo_ladder_rung1_driver.py         |  30 ++-
.../tests/test_silo_ladder_rung1_evidence.py       |  15 ++
orchestrator/tests/test_verifier.py                | 195 ++++++++++++++++--
orchestrator/verifier/__init__.py                  |   5 +-
orchestrator/verifier/cli.py                       |  22 +-
orchestrator/verifier/core.py                      |  23 ++-
orchestrator/verifier/model.py                     |  13 +-
19 files changed, 795 insertions(+), 60 deletions(-)
```

これは親の段5差分を含む worktree 全体です。`report.py` は stat から消え、個別 diff も空です。docs 差分・staged 差分ともにありません。`git diff --check` と対象3ファイルの AST parse は成功しました。

pytest は sandbox の socket 拒否により実行していません。したがって状態は「実装済み・未実走」であり、緑は主張しません。

## 総括

凍結 evidence と一致する `report.py` を復元しつつ、witness 不一致の fail-closed 判定、診断 notes、pipeline の機械可読 witness 経路を維持しました。commit・`git add`・docs 編集は行っていません。