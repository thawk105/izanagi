## 総括

既定案を採用し、新しい負例を `current_commit_snapshot` の consumer に変更しました。  
共有 snapshot は読み取り専用のまま、変異版は `tmp_path` 内の別 repo に tracked bytes を複製しています。  
fixture の `yield` 中は parent read lock が保持されるため、consumer での lock 再取得は不要です。  
残る risk は Pegasus dispatch 障害により指定 3 node を実走できていないことです。commit・docs 編集はしていません。

## 変更

[test_s8c_preregistration_predicates.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:335)

```python
def test_current_repository_c04_rejects_missing_started_trial_preflight(
    tmp_path: Path,
    current_commit_snapshot: _CurrentCommitSnapshot,
) -> None:
    root, head, _, evaluated_head, _ = current_commit_snapshot
    current_head = _git(_ROOT, "rev-parse", "HEAD").decode("ascii").strip()
    _require_unchanged_head(evaluated_head, current_head)

    baseline = _result(root, head, "C04")
    assert baseline.status is core.PredicateStatus.EVIDENCE_UNDEFINED
    assert baseline.reason_code == "completion-proof-not-machine-checkable"

    workload_path = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    registry_path = "orchestrator/campaign/trial_registry.py"
    workload_source = (root / workload_path).read_bytes()
    registry_source = (root / registry_path).read_bytes()
    started_trial_call = b"""    trial_registry.reject_started_trial(
        trial_id=trial_id,
        repository_root=ROOT,
        lifecycle_path=ROOT / trial_registry.DEFAULT_LIFECYCLE_PATH,
    )
"""
    assert workload_source.count(b"trial_registry.reject_started_trial(") == 1
    assert workload_source.count(started_trial_call) == 1

    mutated_workload = workload_source.replace(started_trial_call, b"", 1)
    mark_call = b"            mark_experiment_indeterminate(\n"
    forbid_call = b"trial_registry.forbid_trial_restart("
    assert mutated_workload.count(b"trial_registry.reject_started_trial(") == 0
    assert workload_source.count(mark_call) >= 1
    assert mutated_workload.count(mark_call) == workload_source.count(mark_call)
    assert workload_source.count(forbid_call) == 1
    assert mutated_workload.count(forbid_call) == 1
    assert registry_source.count(b"def reject_started_trial(") == 1
    assert registry_source.count(b"def forbid_trial_restart(") == 1

    mutated_root = _init_repo(tmp_path, "current-snapshot-c04-mutation")
    tracked_paths = (
        _git(root, "ls-tree", "-r", "--name-only", head).decode().splitlines()
    )
    for path in tracked_paths:
        _write(mutated_root, path, (root / path).read_bytes())
    _write(mutated_root, workload_path, mutated_workload)
    mutated_head = _commit(mutated_root, "C04 reject-started preflight removed")
    result = _result(mutated_root, mutated_head, "C04")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "crash-policy-cell-partial"
```

[test_real_repo_serialization.py:260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_real_repo_serialization.py:260)

```python
"test_s8c_preregistration_predicates.py::test_current_repository_c04_rejects_missing_started_trial_preflight",
```

## 受理・拒否の含意

変更前: C04 の正負判定は成立していましたが、新 node の group 所属と fixture consumer 閉包が不一致なため collection 契約に拒否されました。  
変更後: C04 の受理集合は変えず、呼出し欠落は引き続き `UNSATISFIED / crash-policy-cell-partial`、node topology は group／consumer の双方で一致します。  
通る正例: 実 HEAD bytes に呼出しがちょうど 1 個ある状態は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` です。

## 実走結果

- `test_real_repo_group_collection_exactly_matches_canonical_nodes`: 実装済み・未実走（runner `rc=16`, `child_started=false`）。
- `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order`: 実装済み・未実走（runner `rc=16`, `child_started=false`）。
- `test_current_repository_c04_rejects_missing_started_trial_preflight`: 実装済み・未実走（3-node 一括および単独とも runner `rc=16`, `child_started=false`）。
- 原因: Pegasus の `qstat -Q` preflight が `rc=1` となり、テスト child が開始されませんでした。
- `py_compile` と `git diff --check`: `rc=0`。

## 波及

- serialization 検査は、collection の group 集合と fixture closure の双方に新 node が現れ、共有 golden に追加した同じ 4-node 集合と一致する見込みです。
- G6 は同じ `_LONG_LIVED_FIXTURE_GROUP_NODES_GOLDEN` と collection report を比較するため、同じ追加で閉じる見込みです。
- consumer は既存 3 test と今回の負例の計 4 test。fixture 本体と、その lock 寿命を検査する 2 testには変更ありません。
- `current_commit_snapshot` は `with real_repo_fixture_lock(...): yield` なので consumer 実行中も lock を所有します。再取得すると不要な同一 process lock nestingになるため削除しました。
- 4234 行の sorted 先頭は既存の `...gap_reason...` から新しい `...c04_rejects...` に変わりますが、同じ file・同じ `s8c-predicate-snapshot` group の代表 `ItemRecord` なので component／conflict-edge 検査の意味は変わりません。