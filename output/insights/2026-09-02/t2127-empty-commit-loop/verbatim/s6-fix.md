## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| P-01 | `partial` — 実装済み・未実走 | [test_layer3_report.py:284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_layer3_report.py:284) |
| RA-01 | `partial` — 実装済み・未実走 | [test_artifact_admission.py:1736](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_artifact_admission.py:1736) |
| RB-01 | `partial` — 実装済み・未実走 | [artifact_admission.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:331)、[artifact_admission.py:1370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/artifact_admission.py:1370) |

## P-01 の直し方と根拠

`_certifying_campaign` が campaign lock の `environment_contract_sha256` を解決し、その contract の `env_tag` を commit record へ渡すよう修正した。

[wal.py:1511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/wal.py:1511) は `record.env_tag == resolved.contract.env_tag` を要求する。fixture の lock は既定で `linux-baremetal` を認可するため、以下はすべて `linux-baremetal == linux-baremetal` になる。

- `test_accepted_report_requires_e1_and_records_epoch`: fixture commit `linux-baremetal`、WAL contract `linux-baremetal`。
- `test_certified_report_omits_current_verifier_conformance`: fixture commit `linux-baremetal`、WAL contract `linux-baremetal`。
- `test_render_accepted_persists_certifying_report`: fixture commit `linux-baremetal`、WAL contract `linux-baremetal`。
- `test_render_and_render_accepted_race_rejects_second_writer[render]`: fixture commit `linux-baremetal`、WAL contract `linux-baremetal`。
- `test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`: fixture commit `linux-baremetal`、WAL contract `linux-baremetal`。

## RA-01 の直し方と単一理由性

loop を廃止し、次の独立 node に分割した。

- `test_certified_view_rejects_non_exact_commit_count`: `IntSubclass(0)`
- `test_certified_view_rejects_bool_commit_count`: `False`

M4 で exact int 検査を削除すると、いずれも snapshot 件数 `0` と数値的に一致するため、後段の件数不一致 `ValueError` は発生しない。constructor が通過し、各 node は `_pytest.outcomes.Failed: DID NOT RAISE <class 'TypeError'>` で落ちる。

したがって赤理由は「exact 型検査の削除により非 exact int が受理された」の一つだけになる。従来の `True` による後段 `ValueError` との混同はなくした。

## RB-01 の文面

両 docstring に以下を明記した。

- 件数は共通 admission 入口による WAL snapshot の投影である。
- 件数は各 commit が証拠検査を通ったことを独立に証明しない。
- helper は投影件数の非ゼロによる存在保証だけを与える。

## 受理集合を変えていない理由

production の実行述語は変更していない。

- `artifact_admission.py` は docstring だけの変更。
- P-01 は test fixture の commit `env_tag` を、lock が指定する契約値へ一致させただけ。
- RA-01 は test node の分割と入力整理だけで、期待する `TypeError` は維持している。
- token、gate、exact 型拒否、証拠検査、件数検査には触れていない。

## 未実走の明記と親が走らせる nodeid

pytest は実走しておらず、緑は主張しない。`git diff --check` と対象 3 ファイルの AST 構文解析のみ成功した。

親が走らせる nodeid:

```text
orchestrator/tests/test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch
orchestrator/tests/test_layer3_report.py::test_certified_report_omits_current_verifier_conformance
orchestrator/tests/test_layer3_report.py::test_render_accepted_persists_certifying_report
orchestrator/tests/test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render]
orchestrator/tests/test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render_accepted]
orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_non_exact_commit_count
orchestrator/tests/test_artifact_admission.py::test_certified_view_rejects_bool_commit_count
```

`test_accepted_report_rejects_no_commit_campaign` は裁定どおり未変更で、修正対象に含めていない。duration ledger も編集していない。

## 裁定との食い違い

食い違いはない。

## 総括

指定された P-01、RA-01、RB-01 だけを修正した。許可された 3 ファイルのみが変更状態で、commit、add、stash、checkout、reset、branch 操作は行っていない。