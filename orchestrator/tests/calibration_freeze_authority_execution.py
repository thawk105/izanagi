# -*- coding: utf-8 -*-
"""Calibration-freeze authority fixtures を production entrypoint へ流す実行器。"""
from __future__ import annotations

import hashlib
import importlib
import json
import subprocess
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from orchestrator.tests.calibration_freeze_authority_contract import (
    ContractError,
    load_fixture_cases,
    load_manifest,
)


@dataclass(frozen=True)
class _Invocation:
    args: tuple[object, ...]
    kwargs: Mapping[str, object]
    rejection_type: str
    expected_reason: str | None = None
    reason_attribute: str | None = None


_Builder = Callable[[Mapping, Path], _Invocation]


def _activation_invocation(*, negative: bool) -> _Invocation:
    from orchestrator.campaign import env_contract as current
    from orchestrator.campaign import env_contract_activation as activation

    repo_root = Path(current.__file__).resolve().parents[2]
    records = activation.read_activation_record_files(
        repo_root / current._ACTIVATION_DIRECTORY
    )
    terminal = json.loads(records[-1][1].decode("utf-8"))
    initial_rows = tuple(
        activation.ActiveContract(
            env_tag=row["env_tag"],
            generation=row["generation"],
            contract_sha256=row["contract_sha256"],
        )
        for row in terminal["active_contracts"]
    )

    successor_rows_list = []
    synthetic_successors: dict[str, tuple[int, str]] = {}
    for row in initial_rows:
        next_generation = row.generation + 1
        registered_sequence = current.GENERATIONS[row.env_tag]
        registered_next = next(
            (entry for entry in registered_sequence if entry.generation == next_generation),
            None,
        )
        next_hash = (
            registered_next.contract.contract_sha256
            if registered_next is not None
            else hashlib.sha256(
                f"cfab-successor:{row.env_tag}:g{next_generation}".encode("ascii")
            ).hexdigest()
        )
        successor_rows_list.append(activation.ActiveContract(
            env_tag=row.env_tag,
            generation=next_generation,
            contract_sha256=next_hash,
        ))
        if registered_next is None:
            synthetic_successors[row.env_tag] = (next_generation, next_hash)
    successor_rows = tuple(successor_rows_list)
    second = activation.build_activation_record(
        activation_serial=current._ACTIVATION_HEAD_SERIAL + 1,
        previous_activation_state_sha256=current._ACTIVATION_HEAD_STATE_SHA256,
        active_contracts=successor_rows,
    )

    if negative:
        records += ((
            f"{current._ACTIVATION_HEAD_SERIAL + 1:08d}.json",
            activation.canonical_record_bytes(second) + b"\n",
        ),)

    registered_contracts = {
        env_tag: (
            tuple(
                (entry.generation, entry.contract.contract_sha256)
                for entry in sequence
            )
            + ((synthetic_successors[env_tag],) if env_tag in synthetic_successors else ())
        )
        for env_tag, sequence in current.GENERATIONS.items()
    }
    valid_successors = {
        (
            env_tag,
            before.generation,
            before.contract.contract_sha256,
            after.generation,
            after.contract.contract_sha256,
        )
        for env_tag, sequence in current.GENERATIONS.items()
        for before, after in zip(sequence, sequence[1:])
    }
    valid_successors.update({
        (
            before.env_tag,
            before.generation,
            before.contract_sha256,
            after.generation,
            after.contract_sha256,
        )
        for before, after in zip(initial_rows, successor_rows)
    })

    def is_valid_registered_successor(before, after) -> bool:
        return (
            before.env_tag,
            before.generation,
            before.contract_sha256,
            after.generation,
            after.contract_sha256,
        ) in valid_successors

    return _Invocation(
        args=(records,),
        kwargs={
            "registered_contracts": registered_contracts,
            "is_valid_registered_successor": is_valid_registered_successor,
            "expected_head_serial": current._ACTIVATION_HEAD_SERIAL,
            "expected_head_state_sha256": current._ACTIVATION_HEAD_STATE_SHA256,
        },
        rejection_type="ActivationRecordError",
        expected_reason=("activation head serial 不一致" if negative else None),
    )


def _activation_positive(_case: Mapping, _tmp_root: Path) -> _Invocation:
    return _activation_invocation(negative=False)


def _activation_negative(_case: Mapping, _tmp_root: Path) -> _Invocation:
    return _activation_invocation(negative=True)


def _protocol_invocation(*, negative: bool) -> _Invocation:
    from orchestrator.campaign import env_contract
    from orchestrator.campaign import s8b_floor_campaign as floor

    env_tag = sorted(env_contract.REGISTRY)[0]
    contract = env_contract.lookup(env_tag)
    document = {
        "schema": floor.PROTOCOL_SCHEMA,
        "formula": floor.s8b_floor_stats.FORMULA_ID,
        "env_tag": env_tag,
        "contract_sha256": contract.contract_sha256,
        "ccbench_pin": "0" * 40,
        "freeze": {"path": "output/fixture_freeze.json", "sha256": "0" * 64},
        "stock_configuration": "Silo",
        "n_sessions": floor._APPROVED_N_SESSIONS,
        "reps": floor.s8b_approved.APPROVED_REPS,
        "master_seed": "cfab-fixture-seed",
        "schedule_algorithm": floor.SCHEDULE_ALGORITHM,
        "extime_s": floor.s8b_approved.APPROVED_EXTIME_S,
        "wired_min_rel_floor": 0.05,
        "retry_slots_per_cell": floor._APPROVED_RETRY_SLOTS,
        "session_cv_max": floor._APPROVED_SESSION_CV_MAX,
        "cell_cv_max": floor._APPROVED_CELL_CV_MAX,
        "scale_adequacy_rel_tolerance": floor._APPROVED_SCALE_ADEQUACY,
        "allowed_excluded_reasons": list(floor._APPROVED_REASONS),
    }
    if negative:
        alternate = "0" * 64
        if alternate == contract.contract_sha256:
            alternate = "f" * 64
        document["contract_sha256"] = alternate
    return _Invocation(
        args=(document,),
        kwargs={},
        rejection_type="FloorCampaignError",
        expected_reason=(
            "protocol.contract_sha256 と resolver が返した env 契約が不一致"
            if negative else None
        ),
    )


def _protocol_positive(_case: Mapping, _tmp_root: Path) -> _Invocation:
    return _protocol_invocation(negative=False)


def _protocol_negative(_case: Mapping, _tmp_root: Path) -> _Invocation:
    return _protocol_invocation(negative=True)


def _git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        input=stdin,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    ).stdout.decode("utf-8").strip()


def _write(root: Path, relative: str, raw: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)


def _commit(root: Path, subject: str, ai_agent: str) -> None:
    _git(root, "add", "-A")
    _git(
        root,
        "commit",
        "-q",
        "-F",
        "-",
        stdin=f"{subject}\n\nAI-Agent: {ai_agent}".encode("utf-8"),
    )


def _canonical_bytes(document: Mapping) -> bytes:
    return json.dumps(
        document,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _generation_bytes(module, number: int, supersedes: str) -> bytes:
    document = {key: "x" for key in module.V2_TOP_LEVEL_KEYS}
    document["schema_version"] = "8b-holdout-freeze/v2"
    document["generation_number"] = number
    document["supersedes_sha256"] = supersedes
    document["measurement_closure"] = []
    return json.dumps(document, ensure_ascii=False).encode("utf-8")


def _add_generation(root: Path, module, number: int, supersedes: str) -> tuple[str, str]:
    relative = f"output/s8b-freeze/holdout_freeze.v2.g{number}.json"
    raw = _generation_bytes(module, number, supersedes)
    _write(root, relative, raw)
    _commit(root, f"candidate g{number}", "codex-author")
    return hashlib.sha256(raw).hexdigest(), relative


def _approve_and_point(
    root: Path,
    module,
    number: int,
    generation_sha256: str,
    generation_path: str,
    parent_pointer_sha256: str | None,
) -> tuple[str, str]:
    approval_raw = _canonical_bytes({
        "generation_sha256": generation_sha256,
        "approver": "user",
        "approved_at": "2026-08-10T00:00:00Z",
        "scope": "s8b-holdout",
    })
    approval_sha256 = hashlib.sha256(approval_raw).hexdigest()
    _write(
        root,
        f"{module.APPROVAL_DIR}/{generation_sha256}.json",
        approval_raw,
    )
    pointer_raw = _canonical_bytes({
        "generation_number": number,
        "path": generation_path,
        "sha256": generation_sha256,
        "parent_active_sha256": parent_pointer_sha256,
        "approval_sha256": approval_sha256,
    })
    pointer_sha256 = hashlib.sha256(pointer_raw).hexdigest()
    _write(root, f"{module.ACTIVE_DIR}/{pointer_sha256}.json", pointer_raw)
    _commit(root, f"approve g{number}", "none")
    return approval_sha256, pointer_sha256


def _ratified_freeze_invocation(tmp_root: Path, *, negative: bool) -> _Invocation:
    from orchestrator.campaign import s8b_ratified_freeze as ratified

    root = tmp_root / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "cfab fixture")
    _git(root, "config", "user.email", "cfab-fixture@example.invalid")
    _git(root, "config", "commit.gpgsign", "false")
    (root / "README.md").write_text("fixture\n", encoding="utf-8")
    real_v1 = Path(ratified.ROOT) / ratified.V1_FREEZE_PATH
    if real_v1.is_file():
        _write(root, ratified.V1_FREEZE_PATH, real_v1.read_bytes())
    _commit(root, "base", "codex-author")

    g1_sha, g1_path = _add_generation(root, ratified, 1, ratified.V1_FREEZE_SHA256)
    _approval1_sha, pointer1_sha = _approve_and_point(
        root, ratified, 1, g1_sha, g1_path, None,
    )
    g2_sha, g2_path = _add_generation(root, ratified, 2, g1_sha)
    _approval2_sha, _pointer2_sha = _approve_and_point(
        root, ratified, 2, g2_sha, g2_path, pointer1_sha,
    )
    if negative:
        (root / ratified.APPROVAL_DIR / f"{g2_sha}.json").unlink()
        _commit(root, "remove only g2 approval", "none")

    return _Invocation(
        args=(root,),
        kwargs={},
        rejection_type="RatifiedFreezeError",
        expected_reason=("pointer-approval" if negative else None),
        reason_attribute=("reason" if negative else None),
    )


def _ratified_freeze_positive(_case: Mapping, tmp_root: Path) -> _Invocation:
    return _ratified_freeze_invocation(tmp_root, negative=False)


def _ratified_freeze_negative(_case: Mapping, tmp_root: Path) -> _Invocation:
    return _ratified_freeze_invocation(tmp_root, negative=True)


BUILDERS: Mapping[str, _Builder] = MappingProxyType({
    "activation-head-consistency-positive": _activation_positive,
    "activation-head-consistency-negative": _activation_negative,
    "environment-floor-contract-consistency-positive": _protocol_positive,
    "environment-floor-contract-consistency-negative": _protocol_negative,
    "unapproved-generation-no-authority-positive": _ratified_freeze_positive,
    "unapproved-generation-no-authority-negative": _ratified_freeze_negative,
})


def _resolve_entrypoint(specification: object) -> tuple[object, Callable[..., object]]:
    if type(specification) is not str or specification.count(":") != 1:
        raise ContractError(f"entrypoint が <module>:<callable> でない: {specification!r}")
    module_name, callable_name = specification.split(":")
    module = importlib.import_module(module_name)
    entrypoint = getattr(module, callable_name)
    if not callable(entrypoint):
        raise ContractError(f"entrypoint が callable でない: {specification}")
    return module, entrypoint


def execute_case(case: Mapping, which: str) -> str:
    """Fixture の一方を実 entrypoint へ渡し、``accept`` / ``reject`` を返す。"""
    if which not in {"positive_control", "negative_case"}:
        raise ContractError(f"未知の fixture case selector: {which!r}")
    if not isinstance(case, Mapping):
        raise ContractError("fixture case が Mapping でない")
    selected = case.get(which)
    if not isinstance(selected, Mapping):
        raise ContractError(f"{case.get('fixture_id')}: {which} が executable case でない")
    builder_name = selected.get("builder")
    if type(builder_name) is not str or builder_name not in BUILDERS:
        raise ContractError(f"未登録 builder: {builder_name!r}")

    with tempfile.TemporaryDirectory(prefix="cfab-execution-") as temporary:
        invocation = BUILDERS[builder_name](case, Path(temporary))
        module, entrypoint = _resolve_entrypoint(case.get("entrypoint"))
        rejection_type = getattr(module, invocation.rejection_type)
        if not isinstance(rejection_type, type) or not issubclass(rejection_type, Exception):
            raise ContractError(
                f"entrypoint の fail-closed 型が例外 class でない: {invocation.rejection_type}"
            )
        try:
            entrypoint(*invocation.args, **dict(invocation.kwargs))
        except rejection_type as exc:
            if invocation.expected_reason is not None:
                observed = (
                    getattr(exc, invocation.reason_attribute)
                    if invocation.reason_attribute is not None
                    else str(exc)
                )
                if invocation.expected_reason not in str(observed):
                    raise ContractError(
                        f"{case.get('fixture_id')}: 想定外の拒否理由: {observed!r}"
                    ) from exc
            return "reject"
    return "accept"


def run_all_executable() -> Mapping:
    """Manifest に属する executable fixture の陽性・陰性を全件実行する。"""
    manifest = load_manifest()
    declared_ids = {
        entry["fixture_id"]
        for entry in manifest["fixtures"]["entries"]
    }
    results: dict[str, dict[str, str]] = {}
    for case in load_fixture_cases():
        if case["binding_state"] != "executable":
            continue
        fixture_id = case["fixture_id"]
        if fixture_id not in declared_ids:
            raise ContractError(f"manifest 外 executable fixture: {fixture_id}")
        results[fixture_id] = {
            "positive_control": execute_case(case, "positive_control"),
            "negative_case": execute_case(case, "negative_case"),
        }
    return {"executed": tuple(results), "results": results}
