## fix

- [test_p3_b4_floor_artifact_issuer.py:532](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix2/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:532)
  - 権威成果物 `non_guarantees` の固定 prefix 3 件を、test 側の逐語で pin。
  - module 定数は期待値に使用していない。
- [test_p3_b4_material_report.py:954](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix2/orchestrator/tests/test_p3_b4_material_report.py:954)
  - preregistration、authority loader、present 射影を通し、3 件が `certification_scope.not_guaranteed` と `provenance.report_non_guarantees` に伝播することを逐語で pin。
- production 2 file、既存テストの期待値、共有 fixture は未変更。
- 静的波及:
  - 所有外 caller: `issue_authoritative_floor`、`resolve_preregistered_authoritative_floor`、`_apply_authoritative_floor_projection` を呼ぶだけで契約変更なし。
  - 共有 test support: `_synthetic_source`、`_write_floor_preregistration`、`test_floor_pair_driver` の helper に依存するが変更なし。
  - consumer test: node golden のみ更新が必要。

## 追加した nodeid

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_authority_non_guarantees_pin_required_verbatim_limitations`
- `orchestrator/tests/test_p3_b4_material_report.py::test_present_floor_projects_required_verbatim_non_guarantees`

## 実走した検査

- 上記 2 node: `tools/run_tests.py` を起動したが `rc=16`。
  - `qstat -Q preflight rc=1`
  - `child_started=false`
  - **未実走**
- `test_real_repo_serialization.py --collect-only`: `rc=16`、同じく未実走。
- 変更 2 file の Python 構文検査: `rc=0`
- `git diff --check`: `rc=0`

## node golden の更新要否

必要です。[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix2/orchestrator/tests/test_real_repo_serialization.py) の、対象 test file の exact nodeid 集合を保持する既存 node-golden 定数へ、上記 2 nodeid を追加してください。

定数名は必読射影外のため、同 file を直接読まず未確認です。

## 総括

test 2 件を追加し、3 つの非保証を定数から独立した逐語で固定しました。  
否定表現「照合していない」も完全一致により保護されています。  
production file は変更していません。  
pytest は dispatch infrastructure の `rc=16` で未実走のため、`closed` とは申告しません。