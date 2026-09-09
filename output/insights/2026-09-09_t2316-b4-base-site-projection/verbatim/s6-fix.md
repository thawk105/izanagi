## 所見対応表 (F1-F4 の closed / partial / regressed)

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | closed | `arm="off"` の launcher context でも COMPUTE 射影済み ID になる独立 node を追加 |
| F2 | closed | `_has_nqsv=True` を明示し、LOGIN / SUSPECT が正確に `ExecutionGuardError` で拒否されることを固定 |
| F3 | closed | N5 に `bound_environment_contract` の完全一致検査を追加 |
| F4 | closed | N2 の contract assertion に hostname と expected_site の診断を追加 |

変異は実際には注入していませんが、各 must-fix 変異が対応する新規 assertion を失敗させることを静的に確認しました。

## 変更した file:line

- [orchestrator/tests/test_p3_b4_launcher.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py:16)
  - line 16: `ExecutionGuardError` の実体を import
  - line 366-398: off launcher context の射影検査
  - line 401-423: N2 の診断強化
  - line 426-449: LOGIN / SUSPECT の fail-close 検査
  - line 545-572: N5 の environment contract 不変検査

実装、共有 fixture、docs は変更していません。

## 追加・強化した test node

追加:

- `test_base_driver_configs_project_pegasus_compute_for_off_launch_context`
- `test_base_driver_configs_reject_unadmitted_pegasus_sites[login]`
- `test_base_driver_configs_reject_unadmitted_pegasus_sites[suspect]`

強化:

- `test_base_driver_configs_bind_resolved_contract_for_both_admitted_sites`
- `test_sort_driver_configs_remain_unprojected_on_pegasus_compute`

既存 N1からN5の検査は削除、統合、緩和していません。

## 実走した検査 (argv と nodeid と結果)

- `PYTHONPATH=. python3 orchestrator/tests/test_p3_b4_launcher.py`
  - 範囲: `orchestrator/tests/test_p3_b4_launcher.py` 全体
  - 結果: `42 passed in 10.17s`
  - N1からN5、新規 F1、F2 の2パラメータ nodeを全て実走

- `python3 -m py_compile orchestrator/tests/test_p3_b4_launcher.py`
  - 結果: rc=0

- `git diff --check -- orchestrator/tests/test_p3_b4_launcher.py`
  - 結果: rc=0

## 残った赤

ありません。対象 test file 以外の suite は実走していません。

## 波及の静的列挙

- 所有外 caller:
  - production の `_driver_configs` caller は `prepare_launch` であり、bootstrap と continuation が共有します。
  - `test_p3_b4_closed_critic.py` に直接 caller と `_marked_driver_configs` 経由 consumer があります。
  - production code は未変更なので実行時挙動への波及はありません。
- 共有 fixture:
  - `conftest.py::_declare_default_test_site` は通常 `_has_nqsv=False` にします。
  - 新規 F2 node は test body で `socket` と `_has_nqsv=True` の両方を後勝ちで差し替えます。
  - function-scope `monkeypatch` により他 node へ状態は残りません。
- consumer test:
  - launcher test file 全体は実走済みです。
  - `test_p3_b4_closed_critic.py` など別 file は未実走ですが、test-only 差分のため静的な呼出契約変更はありません。

## 総括

3件の生存変異を殺す検査と N2 の診断改善を、test file 1本への追加だけで実装しました。対象全42 nodeは緑です。commit、add、stash、branch、remote 操作は行っていません。