# -*- coding: utf-8 -*-
"""Calibration-freeze authority fixtures を production entrypoint へ流す実行器。"""
from __future__ import annotations

import hashlib
import importlib
import json
import os
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
    declared_arguments_sha256: str
    expected_reason: str | None = None
    reason_attribute: str | None = None
    expected_result: Mapping[str, object] | None = None


_Builder = Callable[[Mapping, Mapping, Path], _Invocation]


class ExecutionDecision(str):
    """``str`` 互換の decision と、実呼出しの改変不能な証跡。"""

    evidence: Mapping[str, str]

    def __new__(cls, value: str, *, evidence: Mapping[str, str]):
        instance = super().__new__(cls, value)
        instance.evidence = MappingProxyType(dict(evidence))
        return instance


def _consume_case_declaration(
    case: Mapping,
    selected: Mapping,
    *,
    scenario: str,
    expected_decision: str,
    single_mutation: str | None = None,
) -> str:
    """Fixture の canonical scenario と独立 invocation pin を消費する。"""
    fixture_id = case.get("fixture_id")
    if type(fixture_id) is not str:
        raise ContractError("fixture_id が canonical string でない")
    prefix = f"{fixture_id}-{scenario}-sha256-"
    case_id = selected.get("case_id")
    if type(case_id) is not str or not case_id.startswith(prefix):
        raise ContractError(
            f"{fixture_id}: case_id が canonical scenario {scenario!r} を宣言していない"
        )
    declared_digest = case_id[len(prefix):]
    if (
        len(declared_digest) != 64
        or any(character not in "0123456789abcdef" for character in declared_digest)
    ):
        raise ContractError(f"{fixture_id}: case_id の invocation SHA-256 が不正")
    if selected.get("expected_decision") != expected_decision:
        raise ContractError(
            f"{fixture_id}: scenario {scenario!r} の expected_decision が不一致"
        )
    if single_mutation is None:
        if "single_mutation" in selected:
            raise ContractError(f"{fixture_id}: positive scenario に mutation がある")
    elif selected.get("single_mutation") != single_mutation:
        raise ContractError(
            f"{fixture_id}: scenario {scenario!r} の single_mutation が不一致"
        )
    return declared_digest


def _activation_invocation(
    case: Mapping,
    selected: Mapping,
    *,
    negative: bool,
) -> _Invocation:
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

    if negative:
        declared_digest = _consume_case_declaration(
            case,
            selected,
            scenario="negative-append-pegasus-g2-without-head-pin",
            expected_decision="reject",
            single_mutation="append-registered-pegasus-g2-without-updating-literal-head",
        )
        successor_rows_list = []
        changed = False
        for row in initial_rows:
            if row.env_tag != "pegasus":
                successor_rows_list.append(row)
                continue
            registered_next = next(
                (
                    entry for entry in current.GENERATIONS[row.env_tag]
                    if entry.generation == row.generation + 1
                ),
                None,
            )
            if registered_next is None:
                raise ContractError("production catalog に pegasus g2 successor が無い")
            successor = activation.ActiveContract(
                env_tag=row.env_tag,
                generation=registered_next.generation,
                contract_sha256=registered_next.contract.contract_sha256,
            )
            if not current._is_valid_activation_successor_with_artifact(
                row, successor,
            ):
                raise ContractError("production successor predicate が pegasus g1→g2 を拒否した")
            successor_rows_list.append(successor)
            changed = True
        if not changed:
            raise ContractError("active production chain に pegasus row が無い")
        second = activation.build_activation_record(
            activation_serial=current._ACTIVATION_HEAD_SERIAL + 1,
            previous_activation_state_sha256=current._ACTIVATION_HEAD_STATE_SHA256,
            active_contracts=tuple(successor_rows_list),
        )
        records += ((
            f"{current._ACTIVATION_HEAD_SERIAL + 1:08d}.json",
            activation.canonical_record_bytes(second) + b"\n",
        ),)
    else:
        declared_digest = _consume_case_declaration(
            case,
            selected,
            scenario="positive-current-production-chain",
            expected_decision="accept",
        )

    return _Invocation(
        args=(records,),
        kwargs={
            "registered_contracts": current._REGISTERED_CONTRACT_CATALOG,
            "is_valid_registered_successor": current._is_valid_activation_successor,
            "expected_head_serial": current._ACTIVATION_HEAD_SERIAL,
            "expected_head_state_sha256": current._ACTIVATION_HEAD_STATE_SHA256,
        },
        rejection_type="ActivationRecordError",
        declared_arguments_sha256=declared_digest,
        expected_reason=("activation head serial 不一致" if negative else None),
    )


def _activation_positive(
    case: Mapping, selected: Mapping, _tmp_root: Path,
) -> _Invocation:
    return _activation_invocation(case, selected, negative=False)


def _activation_negative(
    case: Mapping, selected: Mapping, _tmp_root: Path,
) -> _Invocation:
    return _activation_invocation(case, selected, negative=True)


def _protocol_invocation(
    case: Mapping,
    selected: Mapping,
    *,
    negative: bool,
) -> _Invocation:
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
        declared_digest = _consume_case_declaration(
            case,
            selected,
            scenario="negative-all-zero-contract-hash",
            expected_decision="reject",
            single_mutation="replace-current-contract-sha256-with-all-zeroes",
        )
        alternate = "0" * 64
        if alternate == contract.contract_sha256:
            alternate = "f" * 64
        document["contract_sha256"] = alternate
    else:
        declared_digest = _consume_case_declaration(
            case,
            selected,
            scenario="positive-current-contract-hash",
            expected_decision="accept",
        )
    return _Invocation(
        args=(document,),
        kwargs={},
        rejection_type="FloorCampaignError",
        declared_arguments_sha256=declared_digest,
        expected_reason=(
            "protocol.contract_sha256 と resolver が返した env 契約が不一致"
            if negative else None
        ),
    )


def _protocol_positive(
    case: Mapping, selected: Mapping, _tmp_root: Path,
) -> _Invocation:
    return _protocol_invocation(case, selected, negative=False)


def _protocol_negative(
    case: Mapping, selected: Mapping, _tmp_root: Path,
) -> _Invocation:
    return _protocol_invocation(case, selected, negative=True)


def _git(root: Path, *args: str, stdin: bytes | None = None) -> str:
    environment = os.environ.copy()
    environment.update({
        "GIT_AUTHOR_DATE": "2026-08-10T00:00:00+00:00",
        "GIT_COMMITTER_DATE": "2026-08-10T00:00:00+00:00",
    })
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        input=stdin,
        env=environment,
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
    return _canonical_bytes(document)


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
    _commit(root, f"approve g{number}", "none")
    pointer_raw = _canonical_bytes({
        "generation_number": number,
        "path": generation_path,
        "sha256": generation_sha256,
        "parent_active_sha256": parent_pointer_sha256,
        "approval_sha256": approval_sha256,
    })
    pointer_sha256 = hashlib.sha256(pointer_raw).hexdigest()
    _write(root, f"{module.ACTIVE_DIR}/{pointer_sha256}.json", pointer_raw)
    _commit(root, f"point g{number}", "none")
    return approval_sha256, pointer_sha256


def _point_without_approval(
    root: Path,
    module,
    number: int,
    generation_sha256: str,
    generation_path: str,
    parent_pointer_sha256: str,
) -> None:
    approval_raw = _canonical_bytes({
        "generation_sha256": generation_sha256,
        "approver": "user",
        "approved_at": "2026-08-10T00:00:00Z",
        "scope": "s8b-holdout",
    })
    pointer_raw = _canonical_bytes({
        "generation_number": number,
        "path": generation_path,
        "sha256": generation_sha256,
        "parent_active_sha256": parent_pointer_sha256,
        "approval_sha256": hashlib.sha256(approval_raw).hexdigest(),
    })
    pointer_sha256 = hashlib.sha256(pointer_raw).hexdigest()
    _write(root, f"{module.ACTIVE_DIR}/{pointer_sha256}.json", pointer_raw)
    _commit(root, f"point g{number} without approval", "none")


def _ratified_freeze_invocation(
    tmp_root: Path,
    *,
    scenario: str,
    declared_arguments_sha256: str,
) -> _Invocation:
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

    expected_reason = None
    expected_result: Mapping[str, object] | None = {
        "generation_number": 1,
        "generation_sha256": g1_sha,
    }
    if scenario == "mutated-g1-history":
        _write(root, g1_path, _generation_bytes(ratified, 1, "f" * 64))
        _commit(root, "mutate active g1 bytes", "codex-author")
        expected_reason = "history-mutated"
        expected_result = None
    elif scenario in {"approved-g2", "orphan-g2", "unapproved-g2-pointer"}:
        g2_sha, g2_path = _add_generation(root, ratified, 2, g1_sha)
        expected_result = {
            "generation_number": 2,
            "generation_sha256": g2_sha,
        }
        if scenario == "approved-g2":
            _approve_and_point(root, ratified, 2, g2_sha, g2_path, pointer1_sha)
        elif scenario == "unapproved-g2-pointer":
            _point_without_approval(
                root, ratified, 2, g2_sha, g2_path, pointer1_sha,
            )
            expected_reason = "pointer-approval"
            expected_result = None
        # orphan-g2 deliberately adds neither approval nor pointer.  The
        # resolver must keep returning g1, which fails the requested g2 result.
    elif scenario != "approved-g1":
        raise ContractError(f"未知の ratified freeze scenario: {scenario!r}")

    return _Invocation(
        args=(root,),
        kwargs={},
        rejection_type="RatifiedFreezeError",
        declared_arguments_sha256=declared_arguments_sha256,
        expected_reason=expected_reason,
        reason_attribute=("reason" if expected_reason is not None else None),
        expected_result=expected_result,
    )


def _freeze_history_positive(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="positive-approved-g1",
        expected_decision="accept",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="approved-g1",
        declared_arguments_sha256=declared_digest,
    )


def _freeze_history_negative(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="negative-mutate-active-g1-path",
        expected_decision="reject",
        single_mutation="replace-active-g1-path-with-different-bytes-in-later-commit",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="mutated-g1-history",
        declared_arguments_sha256=declared_digest,
    )


def _orphan_generation_positive(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="positive-approved-g2",
        expected_decision="accept",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="approved-g2",
        declared_arguments_sha256=declared_digest,
    )


def _orphan_generation_negative(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="negative-g2-record-without-approval-or-pointer",
        expected_decision="reject",
        single_mutation="add-g2-generation-record-without-approval-or-pointer",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="orphan-g2",
        declared_arguments_sha256=declared_digest,
    )


def _unapproved_generation_positive(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="positive-approved-g2",
        expected_decision="accept",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="approved-g2",
        declared_arguments_sha256=declared_digest,
    )


def _unapproved_generation_negative(
    case: Mapping, selected: Mapping, tmp_root: Path,
) -> _Invocation:
    declared_digest = _consume_case_declaration(
        case,
        selected,
        scenario="negative-g2-pointer-without-approval",
        expected_decision="reject",
        single_mutation="add-g2-pointer-without-its-approval-record",
    )
    return _ratified_freeze_invocation(
        tmp_root,
        scenario="unapproved-g2-pointer",
        declared_arguments_sha256=declared_digest,
    )


BUILDERS: Mapping[str, _Builder] = MappingProxyType({
    "activation-head-consistency-positive": _activation_positive,
    "activation-head-consistency-negative": _activation_negative,
    "environment-floor-contract-consistency-positive": _protocol_positive,
    "environment-floor-contract-consistency-negative": _protocol_negative,
    "freeze-history-immutability-positive": _freeze_history_positive,
    "freeze-history-immutability-negative": _freeze_history_negative,
    "orphan-generation-no-authority-positive": _orphan_generation_positive,
    "orphan-generation-no-authority-negative": _orphan_generation_negative,
    "unapproved-generation-no-authority-positive": _unapproved_generation_positive,
    "unapproved-generation-no-authority-negative": _unapproved_generation_negative,
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


def _fully_qualified_callable(value: Callable[..., object]) -> str:
    module_name = getattr(value, "__module__", None)
    qualified_name = getattr(value, "__qualname__", None)
    if type(module_name) is not str or type(qualified_name) is not str:
        raise ContractError(f"callable の完全修飾名を解決できない: {value!r}")
    return f"{module_name}.{qualified_name}"


def _canonical_argument(value: object) -> object:
    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        if not (float("-inf") < value < float("inf")):
            raise ContractError("invocation argument に非有限 float がある")
        return {"type": "float", "value": repr(value)}
    if isinstance(value, bytes):
        return {"type": "bytes", "hex": bytes(value).hex()}
    if isinstance(value, Path):
        if (value / ".git").is_dir():
            return {
                "type": "git-repository",
                "head": _git(value, "rev-parse", "HEAD"),
                "status": _git(
                    value, "status", "--porcelain=v1", "--untracked-files=all",
                ),
            }
        return {"type": "path", "value": value.as_posix()}
    if isinstance(value, Mapping):
        items = []
        for key, item in value.items():
            if type(key) is not str:
                raise ContractError("invocation mapping key が string でない")
            items.append((key, _canonical_argument(item)))
        return {"type": "mapping", "items": sorted(items)}
    if isinstance(value, tuple):
        return {"type": "tuple", "items": [_canonical_argument(item) for item in value]}
    if isinstance(value, list):
        return {"type": "list", "items": [_canonical_argument(item) for item in value]}
    if isinstance(value, (set, frozenset)):
        items = [_canonical_argument(item) for item in value]
        return {
            "type": "set",
            "items": sorted(
                items,
                key=lambda item: json.dumps(item, sort_keys=True, separators=(",", ":")),
            ),
        }
    if callable(value):
        return {"type": "callable", "name": _fully_qualified_callable(value)}
    raise ContractError(
        f"invocation argument を canonical 化できない: {type(value).__name__}"
    )


def _arguments_sha256(
    args: tuple[object, ...], kwargs: Mapping[str, object],
) -> str:
    preimage = {
        "args": _canonical_argument(args),
        "kwargs": _canonical_argument(kwargs),
    }
    return hashlib.sha256(_canonical_bytes(preimage)).hexdigest()


def _result_mismatch(
    result: object, expected: Mapping[str, object] | None,
) -> str | None:
    if expected is None:
        return None
    for name, expected_value in expected.items():
        if isinstance(result, Mapping):
            observed = result.get(name)
        else:
            observed = getattr(result, name, None)
        if type(observed) is not type(expected_value) or observed != expected_value:
            return f"result-mismatch:{name}"
    return None


def execute_case(case: Mapping, which: str) -> ExecutionDecision:
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
        invocation = BUILDERS[builder_name](case, selected, Path(temporary))
        arguments_sha256 = _arguments_sha256(invocation.args, invocation.kwargs)
        if arguments_sha256 != invocation.declared_arguments_sha256:
            raise ContractError(
                f"{case.get('fixture_id')}: fixture 宣言と実 invocation digest が不一致: "
                f"declared={invocation.declared_arguments_sha256} actual={arguments_sha256}"
            )
        module, entrypoint = _resolve_entrypoint(case.get("entrypoint"))
        resolved_entrypoint = _fully_qualified_callable(entrypoint)
        rejection_type = getattr(module, invocation.rejection_type)
        if not isinstance(rejection_type, type) or not issubclass(rejection_type, Exception):
            raise ContractError(
                f"entrypoint の fail-closed 型が例外 class でない: {invocation.rejection_type}"
            )
        try:
            result = entrypoint(*invocation.args, **dict(invocation.kwargs))
        except rejection_type as exc:
            observed = (
                getattr(exc, invocation.reason_attribute)
                if invocation.reason_attribute is not None
                else str(exc)
            )
            if invocation.expected_reason is not None:
                if invocation.expected_reason not in str(observed):
                    raise ContractError(
                        f"{case.get('fixture_id')}: 想定外の拒否理由: {observed!r}"
                    ) from exc
            decision = "reject"
            outcome_reason = str(observed)
        else:
            mismatch = _result_mismatch(result, invocation.expected_result)
            decision = "accept" if mismatch is None else "reject"
            outcome_reason = "accepted" if mismatch is None else mismatch
        return ExecutionDecision(
            decision,
            evidence={
                "arguments_sha256": arguments_sha256,
                "builder": builder_name,
                "case_id": selected["case_id"],
                "decision": decision,
                "entrypoint": resolved_entrypoint,
                "outcome_reason": outcome_reason,
            },
        )


def run_all_executable() -> Mapping:
    """Manifest に属する executable fixture の陽性・陰性を全件実行する。"""
    manifest = load_manifest()
    declared_ids = {
        entry["fixture_id"]
        for entry in manifest["fixtures"]["entries"]
    }
    results: dict[str, dict[str, str]] = {}
    invocations: dict[str, dict[str, Mapping[str, str]]] = {}
    for case in load_fixture_cases():
        if case["binding_state"] != "executable":
            continue
        fixture_id = case["fixture_id"]
        if fixture_id not in declared_ids:
            raise ContractError(f"manifest 外 executable fixture: {fixture_id}")
        results[fixture_id] = {}
        invocations[fixture_id] = {}
        for which in ("positive_control", "negative_case"):
            decision = execute_case(case, which)
            if type(decision) is not ExecutionDecision:
                raise ContractError(
                    f"{fixture_id}: execute_case が実呼出し証跡を返さなかった"
                )
            results[fixture_id][which] = str(decision)
            invocations[fixture_id][which] = decision.evidence
    return {
        "executed": tuple(results),
        "results": results,
        "invocations": invocations,
    }
