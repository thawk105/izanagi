## 差し替え

[p3_b4_floor_artifact_issuer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix4/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:49)

- 定数名: `D1699_VERSION_LIMITATION` → `FREEZE_TIMING_NOT_PROVEN`
- 旧: `その版が D1699 適合をまだ満たしていない。`
- 新: `凍結が測定の結果を見る前に行われたことを証明しない。`
- `NON_GUARANTEES` は3件を維持。他の2件は未変更。
- 冒頭 docstring の旧 D1699 前提も同じ事実関係へ整合。

## test の追随

- [test_p3_b4_floor_artifact_issuer.py:568](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix4/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:568)
  - `test_authority_non_guarantees_pin_required_verbatim_limitations` の literal を更新。
  - 定数参照も `FREEZE_TIMING_NOT_PROVEN` へ追随。
- [test_p3_b4_material_report.py:989](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix4/orchestrator/tests/test_p3_b4_material_report.py:989)
  - `test_present_floor_projects_required_verbatim_non_guarantees` の literal を更新。
- 新 test node は追加していない。

## 実走した検査

以下3 nodeid を標準 runner で起動したが、dispatch infrastructure の `qstat -Q preflight rc=1` により child は開始されず、すべて未実走。

- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_authority_issue_is_create_only_exact_and_loadable` — 未実走、runner rc=16
- `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py::test_authority_non_guarantees_pin_required_verbatim_limitations` — 未実走、runner rc=16
- `orchestrator/tests/test_p3_b4_material_report.py::test_present_floor_projects_required_verbatim_non_guarantees` — 未実走、runner rc=16

所有3ファイルの AST parse と旧定数名・旧逐語の不在検査は rc=0。

## 波及可能性

射影範囲での静的な波及先は次のとおり。

- 所有外 caller: [p3_b4_material_report.py:990](/work/1/SFC/tanab/izanagi/.codex/worktrees/b4floor-fix4/orchestrator/campaign/p3_b4_material_report.py:990) が authority の非保証を certification scope と provenance に射影するため、生成 report の逐語が変わる。
- 共有 helper: `_synthetic_source` が発行 test の authority を構成し、`_write_floor_preregistration` は `NON_GUARANTEES` から material-report fixture を生成する。
- Consumer test: `test_authority_issue_is_create_only_exact_and_loadable`、`test_m9_four_authority_and_assembly_states_project_exactly`、上記2本の逐語 pin test が影響範囲。
- `floor_pair_driver.py` と `p3_b4_material_report.py` は編集していない。

## 総括

偽になった D1699 版非保証を、結果確認前の凍結時点が未証明である旨へ差し替えた。  
固定非保証は3件のままで、他の2件と schema・導出・値域検査には触れていない。  
実装と静的構文検査は完了したが、pytest は infrastructure rc=16 のため未実走。  
したがって状態は「実装済み・未実走」であり、`closed` とは申告しない。