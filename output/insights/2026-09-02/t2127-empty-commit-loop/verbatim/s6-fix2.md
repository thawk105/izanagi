## 変更した箇所

[test_layer3_report.py:246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/tests/test_layer3_report.py:246) で `_certifying_campaign` の `build_start` record を作り、`env_tag` を `linux-baremetal` へ上書きしました。

`_record()` の既定値 `test-env` は変更していません。

## 緑になる理由

[layer3_report.py:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2127-empty-commit-loop/orchestrator/campaign/layer3_report.py:620) は WAL 全 record の `env_tag` 集合が一意、つまり要素数 1 であることを要求します。

今回の fixture では全 record が `linux-baremetal` になります。

- `build_start`: 明示的に上書き
- `build_done`: `start.env_tag` を継承
- `verify_done`: `start.env_tag` を継承
- commit: environment contract から解決した `linux-baremetal`

したがって集合は `{"linux-baremetal"}` となり、対象 5 test の `campaign WAL の env_tag が一意でない` は解消するはずです。

## 受理集合を変えていない理由

変更したのは test fixture の `_certifying_campaign` だけです。production code、既存の期待値、skip・xfail 条件には触れておらず、受理集合は変更していません。

## 未実走の明記と親が走らせる nodeid

実装済み・pytest 未実走です。AST 構文検査のみ成功しました。

親が走らせる nodeid:

- `orchestrator/tests/test_layer3_report.py::test_accepted_report_requires_e1_and_records_epoch`
- `orchestrator/tests/test_layer3_report.py::test_certified_report_omits_current_verifier_conformance`
- `orchestrator/tests/test_layer3_report.py::test_render_accepted_persists_certifying_report`
- `orchestrator/tests/test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render]`
- `orchestrator/tests/test_layer3_report.py::test_render_and_render_accepted_race_rejects_second_writer[render_accepted]`

## 総括

P-01 の追加修正を fixture 内だけへ実装しました。commit その他の git 操作は行っていません。状態は「実装済み・未実走」です。