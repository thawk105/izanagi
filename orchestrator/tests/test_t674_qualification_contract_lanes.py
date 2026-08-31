# -*- coding: utf-8 -*-
"""D246 の campaign WAL / qualification event ledger 分離を固定する。"""
from __future__ import annotations

import ast
import json
import sys
from collections import Counter
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_ORCH.parent))

import test_campaign as campaign_fixtures  # noqa: E402
import test_execution_guard as guard_fixtures  # noqa: E402
from orchestrator.campaign import env_contract, execution_guard, pipeline, wal  # noqa: E402
from orchestrator.campaign.layout import CampaignLayout  # noqa: E402
from orchestrator.campaign.model import (  # noqa: E402
    COMMIT_CONTRACT_SHA256_KEY,
    Genome,
    STAGE_COMMIT,
)
from orchestrator.qualification.artifacts import (  # noqa: E402
    QualificationEventSink,
    QualificationRoot,
    create_attempt,
    load_jsonl_strict,
)


def _campaign_layout(tmp_path: Path) -> CampaignLayout:
    layout = CampaignLayout(root=str(tmp_path / "campaign")).ensure()
    campaign_fixtures._write_certified_lock(
        layout, campaign_fixtures._bound(campaign_fixtures._cfg()),
    )
    return layout


def _qualification_lane(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    root = QualificationRoot(repo)
    capability = root.issue()
    layout = create_attempt(
        root,
        capability,
        series_id="a" * 64,
        attempt_id="b" * 64,
    )
    sink = QualificationEventSink(
        capability, layout, round_index=1, role="subject",
        source_lock_identity_sha256="e" * 64,
    )
    policy = pipeline.QualificationPipelinePolicy.t126_pegasus(sink)
    authorization = env_contract.authorize("pegasus")
    perf = pipeline.PerfConfig(
        records=1_000_000,
        threads=48,
        workload={
            "ycsb_zipf_skew": "0.9",
            "ycsb_rratio": "95",
            "ycsb_rmw": "0",
            "ycsb_max_ope": "10",
        },
        extime=3,
        reps=5,
    )
    return layout, policy, authorization, perf


@pytest.mark.parametrize("do_bench", [False, True], ids=["no-bench", "bench"])
def test_campaign_wal_commit_binds_the_exact_authorized_contract(
        tmp_path: Path, do_bench: bool):
    """WAL lane の両 COMMIT 口が、その実行の authorization と値一致する。"""
    layout = _campaign_layout(tmp_path)
    authorization = env_contract.authorize("linux-baremetal")
    contract = authorization.contract

    with campaign_fixtures._mock_pipeline(certified=True):
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}),
            layout,
            contract.env_tag,
            "deadbeef",
            pipeline.PerfConfig(records=1000, threads=2),
            contract.clocks_per_us,
            numactl=contract.numactl,
            do_bench=do_bench,
            authorization_contract=authorization,
            build_context=campaign_fixtures._BUILD_CONTEXT,
            log=lambda *_args: None,
        )

    commits = [
        record for record in wal.read_records(layout)
        if record.stage == STAGE_COMMIT
    ]
    assert result.certified and len(commits) == 1
    assert (
        commits[0].payload[COMMIT_CONTRACT_SHA256_KEY]
        == authorization.contract.contract_sha256
    )


def test_qualification_bench_commit_omits_campaign_contract_key(tmp_path: Path):
    """到達可能な qualification COMMIT は campaign WAL の hash key を持たない。"""
    layout, policy, authorization, perf = _qualification_lane(tmp_path)
    contract = authorization.contract

    with campaign_fixtures._mock_pipeline(certified=True):
        result = pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}),
            layout,
            contract.env_tag,
            "deadbeef",
            perf,
            contract.clocks_per_us,
            numactl=contract.numactl,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload()),
            ],
            do_bench=True,
            do_settle=True,
            src_token="stock",
            cache_root=str(tmp_path / "cache"),
            bench_max_rounds=1,
            env_contract=contract,
            authorization_contract=authorization,
            record_rep_returncodes=True,
            qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
            log=lambda *_args: None,
        )

    records = load_jsonl_strict(
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    )
    commits = [
        row for row in records
        if row["evaluation_stage"] == "qualification_evaluation_terminal"
    ]
    assert result.certified and len(commits) == 1
    payload = json.loads(commits[0]["payload"]["canonical_json"])
    assert COMMIT_CONTRACT_SHA256_KEY not in payload
    assert not (layout.attempt_dir / "runs/wal.jsonl").exists()


def test_qualification_no_bench_is_rejected_before_any_sink_write(tmp_path: Path):
    """qualification の no-bench 口は現契約では入口 shape gate により到達不能。"""
    layout, policy, authorization, perf = _qualification_lane(tmp_path)
    contract = authorization.contract

    with pytest.raises(ValueError, match="qualification opt-in evaluation shape mismatch"):
        pipeline.evaluate(
            Genome("silo", {"BACK_OFF": 1}),
            layout,
            contract.env_tag,
            "deadbeef",
            perf,
            contract.clocks_per_us,
            numactl=contract.numactl,
            extra_correctness=[
                (pipeline.S2_TAG, pipeline.s2_correctness_workload()),
            ],
            do_bench=False,
            do_settle=True,
            src_token="stock",
            bench_max_rounds=1,
            env_contract=contract,
            authorization_contract=authorization,
            record_rep_returncodes=True,
            qualification_policy=policy,
            build_context=campaign_fixtures._BUILD_CONTEXT,
            log=lambda *_args: None,
        )

    assert not (
        layout.attempt_dir / "rounds/0001/subject/evaluation-events.jsonl"
    ).exists()


def _attribute_path(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = _attribute_path(node.value)
        return None if prefix is None else f"{prefix}.{node.attr}"
    return None


def _module_level_commit_stage_names(module: ast.Module) -> set[str]:
    """STAGE_COMMIT と、それを直接・連鎖的に指す module alias を返す。"""
    names = {"STAGE_COMMIT"}
    assignments: list[tuple[list[ast.expr], ast.AST]] = []
    for statement in module.body:
        if isinstance(statement, ast.ImportFrom):
            for imported in statement.names:
                if imported.name == "STAGE_COMMIT":
                    names.add(imported.asname or imported.name)
        elif isinstance(statement, ast.Assign):
            assignments.append((statement.targets, statement.value))
        elif isinstance(statement, ast.AnnAssign):
            assignments.append(([statement.target], statement.value))

    changed = True
    while changed:
        changed = False
        for targets, value in assignments:
            if not isinstance(value, ast.Name) or value.id not in names:
                continue
            for target in targets:
                if isinstance(target, ast.Name) and target.id not in names:
                    names.add(target.id)
                    changed = True
    return names


def _is_commit_stage(node: ast.AST | None, stage_names: set[str]) -> bool:
    return isinstance(node, ast.Name) and node.id in stage_names


def _keyword_node(call: ast.Call, name: str) -> ast.AST | None:
    matches = [keyword.value for keyword in call.keywords if keyword.arg == name]
    assert len(matches) <= 1, (
        f"call at line {call.lineno} has duplicate {name!r} keywords"
    )
    return matches[0] if matches else None


def _stage_node(call: ast.Call) -> ast.AST | None:
    keyword = _keyword_node(call, "stage")
    if keyword is not None:
        return keyword
    return call.args[2] if len(call.args) >= 3 else None


def _commit_calls_in(module: ast.Module) -> list[ast.Call]:
    stage_names = _module_level_commit_stage_names(module)
    all_calls = [
        node for node in ast.walk(module) if isinstance(node, ast.Call)
    ]
    return [
        call for call in all_calls
        if _is_commit_stage(_stage_node(call), stage_names)
    ]


def _payload_node(call: ast.Call) -> ast.AST:
    payload = _keyword_node(call, "payload")
    if payload is not None:
        return payload
    assert len(call.args) >= 5, (
        f"STAGE_COMMIT call at line {call.lineno} has no unique payload"
    )
    return call.args[4]


def _mentions_contract_key(node: ast.AST) -> bool:
    return any(
        (isinstance(part, ast.Name)
         and part.id == "COMMIT_CONTRACT_SHA256_KEY")
        or (isinstance(part, ast.Constant)
            and part.value == COMMIT_CONTRACT_SHA256_KEY)
        for part in ast.walk(node)
    )


def test_evaluate_all_commit_calls_preserve_wal_qualification_separation():
    """受理: certified capability、sole writer、2 lane、全 caller を一体で固定する。

    拒否: 未知 writer/caller と WAL key の qualification 混入を閉集合外にする。
    既知限界: 動的に計算・注入される stage 値は静的 census の対象外。
    """
    tree = ast.parse(
        Path(pipeline.__file__).read_text(encoding="utf-8"),
        filename=pipeline.__file__,
    )
    function_nodes = [
        node for node in tree.body if isinstance(node, ast.FunctionDef)
    ]
    target_function_counts = Counter(
        node.name for node in function_nodes
        if node.name in {"_prepare_evaluation_core", "_commit_prepared"}
    )
    assert target_function_counts == Counter({
        "_prepare_evaluation_core": 1,
        "_commit_prepared": 1,
    })
    functions = {node.name: node for node in function_nodes}
    prepare_node = functions["_prepare_evaluation_core"]
    commit_node = functions["_commit_prepared"]
    parents: dict[ast.AST, ast.AST] = {}
    for parent in ast.walk(tree):
        for child in ast.iter_child_nodes(parent):
            parents[child] = parent

    # writer/function 名を見ず、module alias と positional/keyword stage を正規化する。
    commit_calls = _commit_calls_in(tree)
    assert len(commit_calls) == 2

    by_writer = Counter(_attribute_path(call.func) for call in commit_calls)
    assert by_writer == Counter({
        "wal.log": 1,
        "prepared.qualification_policy.event_sink.emit": 1,
    })
    for call in commit_calls:
        owner = parents.get(call)
        while owner is not None and not isinstance(
                owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = parents.get(owner)
        assert owner is commit_node, (
            f"COMMIT call at line {call.lineno} is outside _commit_prepared"
        )

    # _PreparedEvaluation is the sole commit capability.  It is created only
    # on the top-level path after the verification loop certifies the result.
    prepared_calls = [
        call for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and isinstance(call.func, ast.Name)
        and call.func.id == "_PreparedEvaluation"
    ]
    assert len(prepared_calls) == 1
    prepared_call = prepared_calls[0]
    prepared_owner = parents[prepared_call]
    while not isinstance(prepared_owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
        prepared_owner = parents[prepared_owner]
    assert prepared_owner is prepare_node
    prepared_return = parents[prepared_call]
    while parents.get(prepared_return) is not prepare_node:
        prepared_return = parents[prepared_return]
    assert isinstance(prepared_return, ast.Return)

    verify_loops = [
        statement for statement in prepare_node.body
        if isinstance(statement, ast.For)
        and any(
            isinstance(call, ast.Call)
            and isinstance(call.func, ast.Name)
            and call.func.id == "_run_one_pass"
            for call in ast.walk(statement)
        )
    ]
    certified_assignments = [
        statement for statement in ast.walk(prepare_node)
        if isinstance(statement, ast.Assign)
        and len(statement.targets) == 1
        and ast.unparse(statement.targets[0]) == "res.certified"
        and isinstance(statement.value, ast.Constant)
        and statement.value.value is True
    ]
    assert len(verify_loops) == 1
    assert len(certified_assignments) == 1
    assert (
        prepare_node.body.index(verify_loops[0])
        < prepare_node.body.index(certified_assignments[0])
        < prepare_node.body.index(prepared_return)
    )

    # The certified/non-aborted rejection is a top-level guard before the one
    # exact WAL/qualification split, so it dominates both terminal writers.
    commit_guards = [
        statement for statement in commit_node.body
        if isinstance(statement, ast.If)
        and ast.unparse(statement.test) == "not res.certified or res.aborted"
        and len(statement.body) == 1
        and isinstance(statement.body[0], ast.Raise)
    ]
    assert len(commit_guards) == 1
    writer_splits = [
        statement for statement in commit_node.body
        if isinstance(statement, ast.If)
        and ast.unparse(statement.test) == "prepared.qualification_policy is None"
    ]
    assert len(writer_splits) == 1
    writer_split = writer_splits[0]
    assert commit_node.body.index(commit_guards[0]) < commit_node.body.index(writer_split)
    assert all(call in list(ast.walk(writer_split)) for call in commit_calls)

    wal_call = next(call for call in commit_calls if _attribute_path(call.func) == "wal.log")
    qualification_call = next(
        call for call in commit_calls
        if _attribute_path(call.func) == "prepared.qualification_policy.event_sink.emit"
    )
    assert wal_call in list(ast.walk(ast.Module(body=writer_split.body, type_ignores=[])))
    assert qualification_call in list(
        ast.walk(ast.Module(body=writer_split.orelse, type_ignores=[]))
    )
    assert ast.unparse(_payload_node(wal_call)) == "wal_payload"
    wal_payload_assignments = [
        statement for statement in writer_split.body
        if isinstance(statement, ast.Assign)
        and any(ast.unparse(target) == "wal_payload" for target in statement.targets)
    ]
    assert len(wal_payload_assignments) == 1
    assert _mentions_contract_key(wal_payload_assignments[0].value)
    assert ast.unparse(_payload_node(qualification_call)) == "commit_payload"
    assert not _mentions_contract_key(_payload_node(qualification_call))
    commit_payload_assignments = [
        assignment for assignment in ast.walk(commit_node)
        if isinstance(assignment, ast.Assign)
        and any(
            ast.unparse(target) == "commit_payload"
            for target in assignment.targets
        )
    ]
    assert len(commit_payload_assignments) == 2
    assert all(
        not _mentions_contract_key(assignment.value)
        for assignment in commit_payload_assignments
    )

    helper_calls = [
        call for call in ast.walk(tree)
        if isinstance(call, ast.Call)
        and (
            (isinstance(call.func, ast.Name) and call.func.id == "_commit_prepared")
            or (isinstance(call.func, ast.Attribute)
                and call.func.attr == "_commit_prepared")
        )
    ]
    helper_callers = Counter()
    for call in helper_calls:
        owner = parents[call]
        while not isinstance(owner, (ast.FunctionDef, ast.AsyncFunctionDef)):
            owner = parents[owner]
        helper_callers[owner.name] += 1
    assert helper_callers == Counter({
        "evaluate": 1,
        "_run_balanced_schedule": 1,
    })


def test_commit_census_includes_keyword_stage_without_writer_prefilter():
    """module alias・helper・未知 writer の COMMIT sink も census が捕捉する。"""
    tree = ast.parse(
        """
COMMIT = STAGE_COMMIT

def evaluate():
    positional_sink(layout, variant, STAGE_COMMIT, env_tag, {})

def helper():
    newly_added_sink(stage=COMMIT, payload={})
    unrelated_sink(stage=STAGE_BUILD_DONE, payload={})
"""
    )

    commit_calls = _commit_calls_in(tree)
    assert [_attribute_path(call.func) for call in commit_calls] == [
        "positional_sink",
        "newly_added_sink",
    ]


def test_v2_receipt_is_rejected_by_none_mode():
    """既存3象限に対する純増: 有効な v2 でも none 契約には使えない。"""
    contract, verified = guard_fixtures._required_binding()
    receipt = execution_guard.attest_and_build_receipt(
        contract,
        verified,
        probe_fn=lambda: guard_fixtures._observed(
            verified.attestation_profile
        ),
        now_fn=lambda: "2026-07-18T00:00:00Z",
    )
    assert receipt["schema"] == execution_guard.RECEIPT_SCHEMA_V2
    assert not execution_guard.receipt_matches_contract(
        receipt,
        env_tag=contract.env_tag,
        contract_sha256=contract.contract_sha256,
        attestation_mode="none",
        verified_calibration=verified,
    )


def _run() -> int:
    """新規ファイルを repository の plain-runner 契約へ含める。"""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
