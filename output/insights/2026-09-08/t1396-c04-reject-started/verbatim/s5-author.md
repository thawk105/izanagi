## 総括

R1〜R4を指定2ファイルだけに実装し、C04の受理集合を狭化しました。  
契約JSON、invariant、既存期待値、negative-control IDは変更していません。  
AST解析と `git diff --check` は `rc=0`、変更ファイル集合も指定2件のみです。  
Pegasus dispatch障害によりpytest子は起動せず、テストは実装済み・未実走です。commitも作成していません。

## 変更

[s8c_preregistration_evidence.py:2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:2065)

```python
for target in (
    (workload_path, "mark_experiment_indeterminate"),
    (registry_path, "forbid_trial_restart"),
    (registry_path, "reject_started_trial"),
)
```

registry側の `_functions` 検査とreason codeは変更していません。

[test_s8c_preregistration_predicates.py:835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:835)

```python
TOKEN_ONLY_C04 = """
from .trial_registry import forbid_trial_restart
from .trial_registry import reject_started_trial
def launch_cells(): pass
def mark_experiment_indeterminate(): pass
def run_trial():
    reject_started_trial()
    try:
        launch_cells()
    except Exception:
        mark_experiment_indeterminate()
        forbid_trial_restart()
def main():
    return run_trial()
"""
```

[test_s8c_preregistration_predicates.py:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1256)

```python
registry: (
    "def forbid_trial_restart(): pass\n"
    "def reject_started_trial(): pass\n"
),
```

[test_s8c_preregistration_predicates.py:335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:335) に実repo負例を追加しました。既存 `_snapshot_current_commit` の `git archive` 経路を再利用し、既存と同じ以下の作法に従っています。

```python
@pytest.mark.xdist_group("s8c-predicate-snapshot")
...
with real_repo_fixture_lock("read", None):
```

変更前の実HEAD C04を `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` と確認後、唯一の `trial_registry.reject_started_trial(` 呼出しを除去します。ほか2呼出しとregistryの両定義が残ることをassertし、変更後は以下を要求します。

```python
assert result.status is core.PredicateStatus.UNSATISFIED
assert result.reason_code == "crash-policy-cell-partial"
```

[test_s8c_preregistration_predicates.py:3187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:3187) にtoken-only負例を追加しました。

```python
preflight_call = "    reject_started_trial()\n"
assert source.count(preflight_call) == 1

mutated_source = source.replace(preflight_call, "", 1)
assert mutated_source.count(preflight_call) == 0
...
assert result.status is core.PredicateStatus.UNSATISFIED
assert result.reason_code == "crash-policy-cell-partial"
```

## 受理・拒否の含意

変更前は、`reject_started_trial` 呼出しがなくても、既存2対象と `run_trial` が到達可能ならC04は `EVIDENCE_UNDEFINED` まで通過しました。  
変更後は3対象すべてが必須となり、`reject_started_trial` 呼出しだけが欠ける入力を `UNSATISFIED / crash-policy-cell-partial` で拒否します。  
通る正例は、3呼出しとregistry定義を含む現HEAD snapshotおよび拡張後の `TOKEN_ONLY_C04` baselineです。

## 実走結果

- 新規2 nodeid:

  - `...::test_current_repository_c04_rejects_missing_started_trial_preflight`
  - `...::test_c04_rejects_missing_started_trial_preflight`

  `tools/run_tests.py` 親は `rc=16`。`qstat -Q preflight rc=1` により `child_started=false` で、実装済み・未実走です。

- 上記2 nodeidと `test_plain_runner_coverage.py` のcollect-onlyも `rc=16`、pytest子未起動です。
- `python3 -m orchestrator.campaign.queue_state`: `rc=0`、queue状態は観測不能。
- 2編集ファイルのAST parse: `rc=0`。
- `git diff --check`: `rc=0`。
- 裁定記載の6-file焦点走および変更test file全体: 未実走。
- pytest子が起動していないため、`contract-loader-drift` は観測されていません。統合commit後の親実走が必要です。

## 波及

- 所有外caller: `s8c_preregistration.py` のevaluator loader／`evaluate_all`、および `campaign_lock.py` のHEAD blob束縛。
- 共有fixture: `TOKEN_ONLY_C04`、`_negative_control_case("nc_c04_partial_crash_survives")`、それを読む既存parametrize群。
- consumer test: `test_s8c_preregistration_predicates.py`、`test_s8c_preregistration_core.py`、`test_artifact_admission.py`、`test_t671_source_binding.py`、間接consumerの `test_campaign_lock_codec.py` と `test_s8c_preregistration_invariant.py`。
- test-file列挙メタテストは `test_plain_runner_coverage.py`。今回は新規fileではないためallowlist変更は不要ですが、実走は未完了です。