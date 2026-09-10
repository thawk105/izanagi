## 総括

D1292 に従い、`_evaluate_c04` の到達対象を `mark_experiment_indeterminate`、`forbid_trial_restart`、`reject_started_trial` の 3 件へ狭化する。  
正例は既存の実 HEAD snapshot と C04 reason snapshot が担い、token-only fixture を正例根拠には使わない。  
負例は既存 C04 control の baseline を再利用し、3 件目の呼出しだけを消す専用テストとして追加する。  
既存 reason 期待値は変えず、dirty worktree 中の `contract-loader-drift` は統合 commit 後に解消させる。  
ただし repo-wide test 列挙に必要な `campaign_lock.py` と他 test file は射影外なので、その部分だけは親による補完が必要である。

## プラン

1. [_evaluate_c04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence.py:2056) を次の逐語へ変更する。

```python
def _evaluate_c04(probe: _ConditionProbe) -> core.PredicateResult:
    workload_path = probe.requirement("workload_supervisor").path
    tree = probe.python_kind("workload_supervisor")
    if tree is None:
        return _result(probe, core.PredicateStatus.EVIDENCE_UNDEFINED, ReasonCode.WORKLOAD_SUPERVISOR_ABSENT)
    graph = _ReachabilityExplorer(probe).walk((workload_path, "main"))
    if (workload_path, "run_trial") not in graph.functions:
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRASH_POLICY_CELL_PARTIAL)
    registry_path = probe.requirement("trial_registry").path
    if not all(
        _declared_call(probe, graph, target)
        for target in (
            (workload_path, "mark_experiment_indeterminate"),
            (registry_path, "forbid_trial_restart"),
            (registry_path, "reject_started_trial"),
        )
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.CRASH_POLICY_CELL_PARTIAL)
    registry = probe.python_kind("trial_registry")
    if registry is None or not all(
        function_name in _functions(registry)
        for function_name in ("forbid_trial_restart", "reject_started_trial")
    ):
        return _result(probe, core.PredicateStatus.UNSATISFIED, ReasonCode.RESTART_GUARD_ABSENT)
    return _result(
        probe,
        core.PredicateStatus.EVIDENCE_UNDEFINED,
        ReasonCode.COMPLETION_PROOF_NOT_MACHINE_CHECKABLE,
    )
```

契約の 3 本目は [condition 4 の `reachable_from`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:154) のうち、176 行目の `run_trial preflight -> reject_started_trial` に対応する。契約 JSON は変更しない。

reason code は新設しない。

- 到達辺の欠落は、既存の他 2 辺と同じく C04 policy の部分実装なので `crash-policy-cell-partial` が適切。
- registry capability の定義欠落は既存の `restart-guard-absent` を再利用できる。
- ただし resolver は対象関数が `_functions(module_path)` に存在しない呼出しを graph call にしないため、通常の「定義ごと欠落」は先の `crash-policy-cell-partial` で捕捉される。後段の存在検査は既存構造に合わせた防御的確認であり、新 reason を必要とする根拠にはならない。

2. [TOKEN_ONLY_C04](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:784) は拡張が必要。拡張しないと、変更後 evaluator に対する既存 baseline が 3 本目を欠き、`EVIDENCE_UNDEFINED` ではなく `UNSATISFIED` になる。変更後の逐語は次とする。

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

`reject_started_trial()` は `run_trial` の `try` より前に置き、契約の “preflight” を明示する。既存 import と別行にすることで、[test-only target の文字列置換](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2407) を壊さない。

3. [_negative_control_case の C04 branch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1203) では registry stub にも新関数を足す。

```python
    if identifier == "nc_c04_partial_crash_survives":
        sources = {
            p3: TOKEN_ONLY_C04,
            registry: (
                "def forbid_trial_restart(): pass\n"
                "def reject_started_trial(): pass\n"
            ),
        }
        return sources, p3, TOKEN_ONLY_C04.replace(
            "        mark_experiment_indeterminate()",
            "        keep_completed_cells_certifying()",
            1,
        )
```

既存 mutation は引き続き 1 本目だけを落とす。`nc_c04_partial_crash_survives` の意味と契約上の ID は変更しない。

4. [既存 token-only negative test の直後](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:3125) に、3 本目だけを落とす次の専用負例を置く。

```python
def test_c04_rejects_missing_started_trial_preflight(
    tmp_path: Path,
) -> None:
    sources, _, _ = _negative_control_case(
        "nc_c04_partial_crash_survives"
    )
    root, _, _ = _terminal_result(
        tmp_path,
        "c04-reject-started-baseline",
        "C04",
        sources,
    )
    p3 = "orchestrator/campaign/p3_autonomous_workload_trial.py"
    source = sources[p3]
    assert isinstance(source, str)
    preflight_call = "    reject_started_trial()\n"
    assert source.count(preflight_call) == 1

    _write(root, p3, source.replace(preflight_call, "", 1))
    head = _commit(root, "C04 reject-started preflight removed")
    result = _result(root, head, "C04")
    assert result.status is core.PredicateStatus.UNSATISFIED
    assert result.reason_code == "crash-policy-cell-partial"
```

この mutation は import、registry 定義、`mark_experiment_indeterminate()`、`forbid_trial_restart()` を残し、3 本目の reachable call だけを消す。

`NEGATIVE_CONTROL_CASES` に別 ID は加えない。契約は C04 に 1 個の `negative_control_id` だけを持ち、[exact-set 検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2910) が一対一対応を要求するためである。新テストは既存 control の「別 mutation axis」として置く。

5. 変更前 evaluator では新負例が検出できないことは、親が次の順序で示す。

- test file 側の fixture・stub・新テストだけを一時的に反映する。
- 新 nodeid を `tools/run_tests.py` 経由で焦点実行する。
- mutation 後も旧 evaluator は `reject_started_trial` を見ないため、実測上は `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` となり、`UNSATISFIED` assertion で赤くなることを記録する。
- evaluator の 3 本目を実装後、同じ nodeid を再実行する。

本回答ではテストを実走していないので、緑とは報告しない。

6. 実 production の正例は新設不要。既存の次の組合せが担う。

- [current_commit_snapshot 構築](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:153) は 162–189 行で現 HEAD の commit blob を評価・archive し、stub fixture を使わない。
- [snapshot と HEAD の同値検査](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:251) は HEAD 不変と評価結果同値を確認する。
- [C04 reason snapshot](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:282) の 310–313 行は C04 が `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` まで到達したことを要求する。変更後 evaluator では 3 本の `_declared_call` と両 registry 定義を通らなければこの結果にならない。

実体の経路は次のとおり。

- [`main` から `run_trial`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/p3_autonomous_workload_trial.py:5201)
- [`run_trial` の登録済み trial preflight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/p3_autonomous_workload_trial.py:4598) から 4602 行目の `_reject_registered_lifecycle_duplicate`
- [helper 本体](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/p3_autonomous_workload_trial.py:1430) から 1432 行目の `trial_registry.reject_started_trial`
- [registry の実定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/campaign/trial_registry.py:4796)

token-only baseline も `EVIDENCE_UNDEFINED` になるが、[token-only fixtures never satisfy](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:3089) が明示するとおり、それは production 正例ではない。実 HEAD 検査とは入力経路が分離されているため、両層 stub だけで production 正例が通る形ではない。

## 波及範囲

`TOKEN_ONLY_C04` からの全波及は次のとおり。

- 直接の読者は [_negative_control_case](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1156) の C04 branch。
- その baseline を読む `_terminal_result` は [1353–1368 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1353)。
- parametrize 経由の読者は以下。
  - [reachable-consumer absence shapes](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2163)
  - [production entrypoint cut](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2351)
  - [test-only target](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2383)
  - [unimported same-name decoy](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2437)
  - [noop/token-only fixtures](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:3089)
- 直接 generator を使う [reachability-limit reason test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:2807) にも baseline stub の拡張が必要。
- [`NEGATIVE_CONTROL_CASES`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:1309)、machine-checkable 表と exact-set 検査 2910–2931、C04 reason 表 3112–3125 は期待値を変更しない。
- C04 reason snapshot 282–331 も、親の probe と実経路から期待値変更不要。
- absence-matrix metadata 2482–2503 も fixture を読まないため変更不要。

焦点走として確定できる test file は、変更対象 module を 24 行目で直接 import する [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1396-c04-reject-started/orchestrator/tests/test_s8c_preregistration_predicates.py:24) 全体。

HEAD blob 束縛の分類は次のとおり。

- 未 commit 中だけ赤いもの: `campaign_lock` の contract-loader/enforcement source 検査を通るテスト。worktree の evaluator bytes と HEAD blob が異なるため `contract-loader-drift` になる。期待値変更ではなく、統合 commit 前の偽赤なので commit 後に走らせる。
- 実際に期待値が変わる既存テスト: 射影済み test file 内にはない。C04 current snapshot、既存 negative control、reason 表はすべて据え置ける。追加する専用負例だけが新規期待集合である。

ただし、単独段 dispatch の射影には `campaign_lock.py` とそれを参照する他 test file が含まれていない。このため、repo-wide の「赤くなる test 名」と `rg -l 's8c_preregistration_evidence' orchestrator/tests/` の完全な結果は本段では列挙不能。親は射影外読取が可能な段で同 grep を実行し、上記確定 file に返却された全 test file を加える必要がある。名前を推測して補うべきではない。

## 判断が割れる点

- **P1-a: 同意。** 3 件目は `(registry_path, "reject_started_trial")` が契約と production 実体に一致する。registry 定義検査も追加し、既存 2 reason を再利用する。ただし定義欠落は通常、先行する call 解決で `crash-policy-cell-partial` になる点は明記すべき。
- **P1-b: 同意。** `reject_started_trial()` を `run_trial` の `try` より前へ置く形が “preflight” の最小で明確な fixture 表現。既存 import 置換を守るため import は別行にする。
- **P1-c: 同意。** HEAD blob を archive する `current_commit_snapshot` と C04 reason snapshot の組合せが実 repo 経路を検査しており、token-only stub とは分離されている。新しい実 repo 正例は不要。