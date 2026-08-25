# -*- coding: utf-8 -*-
"""Route-local critic invocation candidate for the P3 B-4 reflux ablation.

This module constructs one on/off controller pair around the existing
projected Claude provider.  The only role payload is the existing
``make_critic_digest`` output plus the coarse terminal ``whiteboard.result``
from separately admitted, byte-stable campaign inputs.  It does not fold
critic output into ``LoopState``, write a proposal, or derive
``reverse_recommended``.

The payload gate proves only that three exact supervisor-side identity
literals are absent in its raw, JSON-decoded, and lexically normalized path
views.  It does not close indirect identifiers such as variant labels, src
tokens, genome labels, or free text originating in the WAL.  Receipt fields
also state the separate limits around executable identity, unreported/local
tool use, logical WAL/checkpoint generations, and storage failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Mapping
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any, Literal

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

from . import ident  # noqa: E402
from .artifact_admission import (  # noqa: E402
    CampaignReadPurpose,
    require_admitted_campaign,
)
from .claude_projected_provider import ClaudeProjectedRoleProvider  # noqa: E402
from .layout import exploration_campaign_layout  # noqa: E402
from .model import CampaignConfig  # noqa: E402
from .p3_s4_loop import (  # noqa: E402
    WhiteboardEntry,
    default_cfg,
    loop_state_path,
    make_critic_digest,
    make_critic_identity_projection,
    state_from_dict,
)
from .role_session_isolation import CrossRoleSessionTracker  # noqa: E402
from .s8b_prediction_runner import (  # noqa: E402
    PredictionRunnerError,
    _canonical_json_bytes,
)


Arm = Literal["on", "off"]
EvidenceClass = Literal["certified", "test-only"]

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
ROLE_FILE = REPOSITORY_ROOT / ".claude" / "agents" / "critic.md"
PROVIDER_FILE = REPOSITORY_ROOT / "orchestrator" / "campaign" / "claude_projected_provider.py"
LOOP_FILE = REPOSITORY_ROOT / "orchestrator" / "campaign" / "p3_s4_loop.py"
DIGEST_FILE = REPOSITORY_ROOT / "orchestrator" / "critic" / "digest.py"
IDENTITY_PROJECTION_FILE = (
    REPOSITORY_ROOT / "orchestrator" / "critic" / "identity_projection.py"
)
ARTIFACT_ADMISSION_FILE = (
    REPOSITORY_ROOT / "orchestrator" / "campaign" / "artifact_admission.py"
)
PREDICTION_RUNNER_FILE = (
    REPOSITORY_ROOT / "orchestrator" / "campaign" / "s8b_prediction_runner.py"
)
ROLE_SESSION_ISOLATION_FILE = (
    REPOSITORY_ROOT / "orchestrator" / "campaign" / "role_session_isolation.py"
)
MODULE_FILE = Path(__file__).resolve()

MEDIATED_CRITIC_CONTRACT = """
Runtime capabilities are intentionally lowered to tools=[]: use only the
projected_digest and result in the JSON object on stdin. Never request or infer
filesystem data and never weaken correctness. Missing metrics must remain
uncertainty. Return JSON only, exactly:
{"attribution":"string","recommend":"string","avoid":"string","uncertainty":"string","reverse_recommended":false}
reverse_recommended must be a JSON boolean and is returned as data only. Do not
emit Markdown or extra keys.
""".strip()

_PAYLOAD_KEYS = frozenset({"projected_digest", "result"})
_RESULT_VALUES = frozenset({"success", "fail", "rejected"})
_RESPONSE_KEYS = frozenset({
    "attribution",
    "recommend",
    "avoid",
    "uncertainty",
    "reverse_recommended",
})
_INVOCATION_ID_RE = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")
_PATH_TOKEN_RE = re.compile(r"(?:[A-Za-z]:)?[\\/][^\s\"']+")
_QUOTED_PATH_RE = re.compile(
    r"(?P<quote>[\"'])(?P<path>(?:[A-Za-z]:)?[\\/].*?)(?P=quote)"
)
_PAIR_SEAL = object()
_IDENTITY_NON_GUARANTEES = (
    "indirect identifiers are not closed: variant labels, src tokens, "
    "genome labels, and WAL-originated free text",
)
_TRUST_NON_GUARANTEES = (
    "the identity of a binary found as claude on PATH is not authenticated",
    "same-process Python code can replace module globals or disable checks",
)
_CAPABILITY_NON_GUARANTEES = (
    "unreported tool events and local activity outside the reported envelope "
    "are not proved absent",
)
_SNAPSHOT_NON_GUARANTEES = (
    "byte stability does not bind the WAL and loop state to one logical "
    "generation; a newer WAL with an older stable loop state can be admitted",
)
_STORAGE_NON_GUARANTEES = (
    "a storage failure while final terminal bytes are written can leave an "
    "invalid reserved receipt; durable parent-directory persistence is not "
    "proved",
)


class B4ClosedCriticError(RuntimeError):
    """Base error for the route-local B-4 controller."""


class B4TrustRootError(B4ClosedCriticError):
    """A caller attempted to select a certified trust root."""


class B4ArmBindingError(B4ClosedCriticError):
    """The sealed factory slot and config-bound arm disagree."""


class B4SnapshotError(B4ClosedCriticError):
    """Digest and coarse result cannot be bound to one stable snapshot."""


class B4PayloadSchemaError(B4ClosedCriticError):
    """The exact two-field role payload contract was violated."""


class B4CampaignDisclosureError(B4ClosedCriticError):
    """An exact supervisor-side identity literal appeared in a checked view."""

    def __init__(self, identity_kind: str, checked_view: str) -> None:
        self.identity_kind = identity_kind
        self.checked_view = checked_view
        super().__init__(
            "B-4 critic payload contains a forbidden exact identity literal "
            f"(kind={identity_kind}, view={checked_view})"
        )


class B4CriticResponseError(B4ClosedCriticError):
    """The critic response did not match the route-local exact schema."""


class B4ReceiptError(B4ClosedCriticError):
    """A receipt could not be created or a certified pair did not validate."""


@dataclass(frozen=True)
class B4CriticDecision:
    attribution: str
    recommend: str
    avoid: str
    uncertainty: str
    reverse_recommended: bool


@dataclass(frozen=True)
class B4ClosedCriticReceipt:
    schema_version: str
    status: str
    evidence_class: EvidenceClass
    pair_id: str
    arm: Arm
    campaign_id: str
    controller_id: str
    invocation_id: str
    session_id: str
    provider_kind: str
    provider_instance_id: str
    neutral_root_identity_sha256: str
    model_snapshot: str
    role_file_sha256: str
    effective_prompt_sha256: str
    projection_sha256: str
    digest_sha256: str
    admitted_view_sha256: str
    loop_state_sha256: str
    iteration: int
    claimed_fresh_context: bool
    claimed_capability_lowering: str
    claimed_source_declared_tools: tuple[str, ...]
    claimed_declared_tools: tuple[str, ...]
    claimed_observed_tool_events: tuple[str, ...]
    evidence_executable_path: str
    evidence_executable_sha256: str
    evidence_payload_sha256: str
    evidence_raw_envelope_sha256: str
    evidence_argv_sha256: str
    evidence_num_turns: int
    evidence_permission_denials_empty: bool
    evidence_server_tool_use_all_zero: bool
    exact_identity_literals_absent_from_canonical_payload: bool
    identity_non_guarantees: tuple[str, ...]
    trust_non_guarantees: tuple[str, ...]
    capability_non_guarantees: tuple[str, ...]
    snapshot_non_guarantees: tuple[str, ...]
    storage_non_guarantees: tuple[str, ...]
    start_receipt_sha256: str


@dataclass(frozen=True)
class B4ClosedCriticInvocation:
    decision: B4CriticDecision
    receipt: B4ClosedCriticReceipt
    start_receipt_path: Path
    terminal_receipt_path: Path


@dataclass(frozen=True)
class B4ArmPairComparison:
    admitted_view_sha256_equal: bool
    loop_state_sha256_equal: bool
    iteration_equal: bool


@dataclass(frozen=True)
class _ArmBinding:
    arm: Arm
    campaign_id: str
    layout_root: Path
    pair_id: str


@dataclass(frozen=True)
class _Snapshot:
    view: Any
    wal_bytes: bytes
    loop_state_bytes: bytes
    iteration: int
    whiteboard_entry: WhiteboardEntry


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _read_bytes(path: Path, *, purpose: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError as exc:
        raise B4SnapshotError(f"B-4 {purpose} bytes are unavailable") from exc


def _write_exclusive_json(path: Path, value: Mapping[str, Any]) -> str:
    return _write_exclusive_bytes(path, _canonical_json_bytes(value))


def _write_exclusive_bytes(path: Path, data: bytes) -> str:
    if type(data) is not bytes:
        raise B4ReceiptError("exclusive receipt artifact must be exact bytes")
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise B4ReceiptError(f"receipt already exists: {path.name}") from exc
    except OSError as exc:
        raise B4ReceiptError(f"receipt exclusive create failed: {path.name}") from exc
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        raise
    return _sha256(data)


def _reserve_terminal_receipt(path: Path) -> int:
    """Exclusively reserve the terminal filename before any role query."""
    try:
        return os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError as exc:
        raise B4ReceiptError(f"receipt already exists: {path.name}") from exc
    except OSError as exc:
        raise B4ReceiptError(
            f"terminal receipt reservation failed: {path.name}"
        ) from exc


def _finish_reserved_json(fd: int, path: Path, value: Mapping[str, Any]) -> str:
    """Write the one terminal transition through its already reserved fd."""
    data = _canonical_json_bytes(value)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except OSError as exc:
        raise B4ReceiptError(
            f"reserved terminal receipt write failed: {path.name}"
        ) from exc
    return _sha256(data)


def _pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise B4CriticResponseError("critic response contains a duplicate key")
        value[key] = item
    return value


def parse_b4_critic_response(raw_response: str) -> B4CriticDecision:
    """Validate and return critic data without applying it to loop state."""
    if type(raw_response) is not str:
        raise B4CriticResponseError("critic response must be an exact str")
    try:
        value = json.loads(raw_response, object_pairs_hook=_pairs_object)
    except (json.JSONDecodeError, B4CriticResponseError) as exc:
        if isinstance(exc, B4CriticResponseError):
            raise
        raise B4CriticResponseError("critic response is not one JSON object") from exc
    if type(value) is not dict or set(value) != _RESPONSE_KEYS:
        raise B4CriticResponseError("critic response keys do not match the exact schema")
    for key in ("attribution", "recommend", "avoid", "uncertainty"):
        if type(value[key]) is not str:
            raise B4CriticResponseError(f"critic response {key} must be an exact str")
    if type(value["reverse_recommended"]) is not bool:
        raise B4CriticResponseError(
            "critic response reverse_recommended must be an exact bool"
        )
    return B4CriticDecision(
        attribution=value["attribution"],
        recommend=value["recommend"],
        avoid=value["avoid"],
        uncertainty=value["uncertainty"],
        reverse_recommended=value["reverse_recommended"],
    )


def project_b4_critic_payload(
    *, projected_digest: str, whiteboard_entry: WhiteboardEntry,
) -> dict[str, str]:
    """Project the existing digest and only the coarse whiteboard result."""
    if type(projected_digest) is not str or not projected_digest:
        raise B4PayloadSchemaError("projected_digest must be a non-empty exact str")
    if type(whiteboard_entry) is not WhiteboardEntry:
        raise B4PayloadSchemaError("whiteboard_entry must be the exact production type")
    payload = {
        "projected_digest": projected_digest,
        "result": whiteboard_entry.result,
    }
    validate_b4_critic_payload(payload)
    return payload


def validate_b4_critic_payload(payload: Mapping[str, Any]) -> None:
    """Enforce the exact two-key payload schema at its single gate."""
    if not isinstance(payload, Mapping) or set(payload) != _PAYLOAD_KEYS:
        raise B4PayloadSchemaError("B-4 critic payload keys do not match the exact schema")
    if type(payload["projected_digest"]) is not str or not payload["projected_digest"]:
        raise B4PayloadSchemaError("projected_digest must be a non-empty exact str")
    result = payload["result"]
    if type(result) is not str or result not in _RESULT_VALUES:
        raise B4PayloadSchemaError("result must be success, fail, or rejected")


def _string_leaves(value: Any) -> list[str]:
    if type(value) is str:
        return [value]
    if type(value) is list:
        return [leaf for item in value for leaf in _string_leaves(item)]
    if type(value) is dict:
        return [
            leaf
            for key, item in value.items()
            for leaf in (_string_leaves(key) + _string_leaves(item))
        ]
    return []


def _lexically_normalized_path_view(leaves: list[str]) -> str:
    """Normalize unquoted tokens and whole explicitly quoted path tokens.

    ``json.loads`` has already decoded the JSON syntax exactly once.  Residual
    ``\\uXXXX`` text in a decoded leaf is therefore descriptive literal text,
    not a second escape layer, and is deliberately not decoded again.
    """
    normalized: list[str] = []
    for leaf in leaves:
        quoted_spans: list[tuple[int, int]] = []
        for match in _QUOTED_PATH_RE.finditer(leaf):
            token = match.group("path").replace("\\", "/")
            normalized.append(posixpath.normpath(token))
            quoted_spans.append(match.span())
        for match in _PATH_TOKEN_RE.finditer(leaf):
            if any(start <= match.start() < end for start, end in quoted_spans):
                continue
            token = match.group(0).rstrip(",.;:!?)]}>`")
            token = token.replace("\\", "/")
            normalized.append(posixpath.normpath(token))
    return "\n".join(normalized)


def _unshadowed_literal_present(
    view: str, *, literal: str, all_literals: tuple[str, ...],
) -> bool:
    """Assign an overlapping occurrence only to its longest forbidden literal."""
    start = 0
    while True:
        found = view.find(literal, start)
        if found < 0:
            return False
        end = found + len(literal)
        shadowed = False
        for longer in all_literals:
            if len(longer) <= len(literal):
                continue
            longer_start = 0
            while True:
                outer = view.find(longer, longer_start)
                if outer < 0:
                    break
                if outer <= found and end <= outer + len(longer):
                    shadowed = True
                    break
                longer_start = outer + 1
            if shadowed:
                break
        if not shadowed:
            return True
        start = found + 1


def assert_no_campaign_identity(
    payload_bytes: bytes,
    *,
    campaign_path: Path,
    campaign_id: str,
    repository_root: Path | None = None,
) -> None:
    """Reject exact identity literals in raw, decoded, and normalized views."""
    if type(payload_bytes) is not bytes or not payload_bytes:
        raise B4PayloadSchemaError("canonical payload bytes must be non-empty bytes")
    trusted_root = REPOSITORY_ROOT
    if repository_root is not None:
        try:
            supplied_root = Path(repository_root).resolve(strict=True)
        except OSError as exc:
            raise B4TrustRootError("repository_root cannot be resolved") from exc
        if supplied_root != trusted_root:
            raise B4TrustRootError("repository_root differs from the module-derived root")
    campaign_path = Path(campaign_path)
    if not campaign_path.is_absolute():
        raise B4PayloadSchemaError("campaign_path must be absolute")
    try:
        campaign_path = campaign_path.resolve(strict=True)
    except OSError as exc:
        raise B4PayloadSchemaError("campaign_path cannot be resolved") from exc
    if type(campaign_id) is not str or not campaign_id:
        raise B4PayloadSchemaError("campaign_id must be a non-empty exact str")
    try:
        raw_view = payload_bytes.decode("utf-8")
        parsed = json.loads(raw_view)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise B4PayloadSchemaError("canonical payload is not valid UTF-8 JSON") from exc
    leaves = _string_leaves(parsed)
    views = (
        ("raw", raw_view),
        ("json-escape-decoded", "\n".join(leaves)),
        ("path-lexically-normalized", _lexically_normalized_path_view(leaves)),
    )
    literals_by_kind = (
        ("campaign_path", str(campaign_path)),
        ("campaign_id", campaign_id),
        ("repository_root", str(trusted_root)),
    )
    all_literals = tuple(literal for _kind, literal in literals_by_kind)
    for view_name, view in views:
        for identity_kind, literal in literals_by_kind:
            if _unshadowed_literal_present(
                view, literal=literal, all_literals=all_literals,
            ):
                raise B4CampaignDisclosureError(identity_kind, view_name)


def projection_closure_manifest() -> dict[str, Any]:
    """Return the canonical closure manifest whose hash identifies projection."""
    paths = (
        ("orchestrator/campaign/p3_b4_closed_critic.py", MODULE_FILE),
        ("orchestrator/campaign/claude_projected_provider.py", PROVIDER_FILE),
        ("orchestrator/campaign/p3_s4_loop.py", LOOP_FILE),
        ("orchestrator/campaign/artifact_admission.py", ARTIFACT_ADMISSION_FILE),
        (
            "orchestrator/campaign/s8b_prediction_runner.py",
            PREDICTION_RUNNER_FILE,
        ),
        (
            "orchestrator/campaign/role_session_isolation.py",
            ROLE_SESSION_ISOLATION_FILE,
        ),
        ("orchestrator/critic/digest.py", DIGEST_FILE),
        (
            "orchestrator/critic/identity_projection.py",
            IDENTITY_PROJECTION_FILE,
        ),
        (".claude/agents/critic.md", ROLE_FILE),
    )
    entries = {
        relative: _sha256(path.read_bytes())
        for relative, path in paths
    }
    entries["mediated-contract:utf-8"] = _sha256(
        MEDIATED_CRITIC_CONTRACT.encode("utf-8")
    )
    return {
        "schema_version": "p3-b4-projection-closure/v1",
        "entries": entries,
    }


def projection_sha256() -> str:
    return _sha256(_canonical_json_bytes(projection_closure_manifest()))


def _resolve_repository_root(repository_root: Path | None) -> Path:
    if repository_root is None:
        return REPOSITORY_ROOT
    try:
        supplied = Path(repository_root).resolve(strict=True)
    except OSError as exc:
        raise B4TrustRootError("repository_root cannot be resolved") from exc
    if supplied != REPOSITORY_ROOT:
        raise B4TrustRootError("repository_root differs from the module-derived root")
    return REPOSITORY_ROOT


def _derive_arm(
    cfg: CampaignConfig, *, expected_arm: Arm, pair_id: str,
) -> _ArmBinding:
    reflux = cfg.search_config.get("reflux")
    if reflux not in {"on", "off"}:
        raise B4ArmBindingError("cfg.search_config['reflux'] must be on or off")
    if reflux != expected_arm:
        raise B4ArmBindingError(
            f"sealed pair slot {expected_arm} disagrees with cfg.search_config['reflux']"
        )
    campaign_id = str(ident.campaign_id(cfg))
    layout = exploration_campaign_layout(campaign_id)
    return _ArmBinding(
        arm=reflux,
        campaign_id=campaign_id,
        layout_root=Path(layout.root).resolve(),
        pair_id=pair_id,
    )


def _load_stable_snapshot(binding: _ArmBinding) -> _Snapshot:
    layout = exploration_campaign_layout(binding.campaign_id)
    resolved_layout = Path(layout.root).resolve()
    if resolved_layout != binding.layout_root:
        raise B4SnapshotError("campaign layout changed after controller creation")
    wal_path = Path(layout.wal_file)
    state_path = Path(loop_state_path(layout))
    wal_before = _read_bytes(wal_path, purpose="admitted WAL prefix")
    state_before = _read_bytes(state_path, purpose="loop state")
    view = require_admitted_campaign(
        layout.root,
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    )
    wal_after = _read_bytes(wal_path, purpose="admitted WAL prefix")
    state_after = _read_bytes(state_path, purpose="loop state")
    if wal_before != wal_after or state_before != state_after:
        raise B4SnapshotError("campaign snapshot changed during admission")
    try:
        state_value = json.loads(state_before)
        state = state_from_dict(state_value)
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise B4SnapshotError("loop state is not an admissible checkpoint") from exc
    if not state.whiteboard:
        raise B4SnapshotError("loop state whiteboard is empty")
    entry = state.whiteboard[-1]
    if entry.iteration != state.iteration:
        raise B4SnapshotError("latest whiteboard entry iteration differs from loop state")
    if type(state.iteration) is not int or state.iteration < 1:
        raise B4SnapshotError("loop state iteration must be a positive exact int")
    return _Snapshot(
        view=view,
        wal_bytes=wal_before,
        loop_state_bytes=state_before,
        iteration=state.iteration,
        whiteboard_entry=entry,
    )


def _neutral_root_identity_bytes(provider: ClaudeProjectedRoleProvider) -> bytes:
    stat = provider.neutral_root.stat()
    identity = {"device": stat.st_dev, "inode": stat.st_ino}
    return _canonical_json_bytes(identity)


class B4ClosedCriticController:
    """Single-use controller whose arm is a private frozen config derivation."""

    def __init__(
        self,
        *,
        _seal: object,
        binding: _ArmBinding,
        artifact_root: Path,
        repository_root: Path,
        evidence_class: EvidenceClass,
        executable: str | os.PathLike[str],
        runner: Callable[..., Any],
        environ: Mapping[str, str] | None,
        tracker: CrossRoleSessionTracker,
        controller_id: str,
        initial_projection_sha256: str,
    ) -> None:
        if _seal is not _PAIR_SEAL:
            raise B4ArmBindingError("controllers must be made by the sealed pair factory")
        self.__binding = binding
        self.__evidence_class = evidence_class
        self.__controller_id = controller_id
        self.__initial_projection_sha256 = initial_projection_sha256
        self.__artifact_root = Path(artifact_root)
        self.__artifact_root.mkdir(parents=True, exist_ok=False)
        self.__invoked = False
        self.__provider = ClaudeProjectedRoleProvider(
            artifact_root=self.__artifact_root,
            role_file=ROLE_FILE,
            role_name="critic",
            mediated_contract=MEDIATED_CRITIC_CONTRACT,
            repository_root=repository_root,
            executable=executable,
            runner=runner,
            environ=environ,
            cross_role_session_tracker=tracker,
        )
        self.__provider_instance_id = f"python-object:{id(self.__provider):x}"
        self.__neutral_root_identity_bytes = _neutral_root_identity_bytes(
            self.__provider
        )
        self.__neutral_root_identity_sha256 = _sha256(
            self.__neutral_root_identity_bytes
        )

    def close(self) -> None:
        self.__provider.close()

    def _pair_identity(self) -> tuple[str, str]:
        return self.__provider_instance_id, self.__neutral_root_identity_sha256

    def invoke(self, *, invocation_id: str) -> B4ClosedCriticInvocation:
        """Invoke once; every started attempt receives one terminal receipt."""
        if (
            type(invocation_id) is not str
            or _INVOCATION_ID_RE.fullmatch(invocation_id) is None
        ):
            raise B4ReceiptError("invocation_id is outside the closed character set")
        if self.__invoked:
            raise B4ReceiptError("B-4 arm controller is single-use; retry is forbidden")
        self.__invoked = True
        start_path = self.__artifact_root / f"receipt_{invocation_id}_start.json"
        terminal_path = self.__artifact_root / f"receipt_{invocation_id}_terminal.json"
        terminal_fd: int | None = _reserve_terminal_receipt(terminal_path)
        start_sha256: str | None = None
        try:
            start_value = {
                "schema_version": "p3-b4-critic-start/v2",
                "status": "started",
                "evidence_class": self.__evidence_class,
                "pair_id": self.__binding.pair_id,
                "arm": self.__binding.arm,
                "campaign_id": self.__binding.campaign_id,
                "controller_id": self.__controller_id,
                "invocation_id": invocation_id,
                "started_at_ns": time.time_ns(),
            }
            start_sha256 = _write_exclusive_json(start_path, start_value)
            current_projection_sha256 = projection_sha256()
            if current_projection_sha256 != self.__initial_projection_sha256:
                raise B4ReceiptError("projection closure changed after pair creation")
            snapshot = _load_stable_snapshot(self.__binding)
            digest = make_critic_digest(
                snapshot.view,
                tag="p3-b4-closed-critic",
                reflux=(self.__binding.arm == "on"),
                identity_projection=make_critic_identity_projection(snapshot.view),
            )
            payload = project_b4_critic_payload(
                projected_digest=digest,
                whiteboard_entry=snapshot.whiteboard_entry,
            )
            payload_bytes = _canonical_json_bytes(payload)
            assert_no_campaign_identity(
                payload_bytes,
                campaign_path=self.__binding.layout_root,
                campaign_id=self.__binding.campaign_id,
            )
            layout = exploration_campaign_layout(self.__binding.campaign_id)
            if (
                _read_bytes(Path(layout.wal_file), purpose="admitted WAL prefix")
                != snapshot.wal_bytes
                or _read_bytes(Path(loop_state_path(layout)), purpose="loop state")
                != snapshot.loop_state_bytes
            ):
                raise B4SnapshotError("campaign snapshot changed before invocation")
            _write_exclusive_bytes(
                self.__artifact_root / f"admitted_view_{invocation_id}.wal",
                snapshot.wal_bytes,
            )
            _write_exclusive_bytes(
                self.__artifact_root / f"loop_state_{invocation_id}.json",
                snapshot.loop_state_bytes,
            )
            _write_exclusive_bytes(
                self.__artifact_root / f"argv_{invocation_id}.json",
                _canonical_json_bytes(list(self.__provider.argv)),
            )
            _write_exclusive_bytes(
                self.__artifact_root / f"effective_prompt_{invocation_id}.txt",
                self.__provider.effective_prompt.encode("utf-8"),
            )
            _write_exclusive_bytes(
                self.__artifact_root
                / f"neutral_root_identity_{invocation_id}.json",
                self.__neutral_root_identity_bytes,
            )
            response = self.__provider.invoke(
                invocation_id=invocation_id,
                payload=payload,
            )
            decision = parse_b4_critic_response(response.raw_response)
            envelope_path = self.__artifact_root / f"envelope_{invocation_id}.json"
            envelope_bytes = _read_bytes(envelope_path, purpose="raw envelope")
            try:
                envelope = json.loads(envelope_bytes)
            except json.JSONDecodeError as exc:  # provider already checked this
                raise B4ReceiptError("raw envelope became invalid after provider admission") from exc
            usage = envelope.get("usage")
            server_tool_use = usage.get("server_tool_use") if isinstance(usage, dict) else None
            if not isinstance(server_tool_use, dict):
                raise B4ReceiptError("raw envelope server_tool_use evidence is missing")
            provenance = response.provenance
            payload_sha256 = _sha256(payload_bytes)
            envelope_sha256 = _sha256(envelope_bytes)
            if provenance.get("payload_sha256") != payload_sha256:
                raise B4ReceiptError("provider payload evidence disagrees with canonical payload")
            if provenance.get("envelope_sha256") != envelope_sha256:
                raise B4ReceiptError("provider envelope evidence disagrees with raw envelope")
            receipt = B4ClosedCriticReceipt(
                schema_version="p3-b4-closed-critic-receipt/v2",
                status="success",
                evidence_class=self.__evidence_class,
                pair_id=self.__binding.pair_id,
                arm=self.__binding.arm,
                campaign_id=self.__binding.campaign_id,
                controller_id=self.__controller_id,
                invocation_id=invocation_id,
                session_id=provenance["child_id"],
                provider_kind=self.__provider.provider_kind,
                provider_instance_id=self.__provider_instance_id,
                neutral_root_identity_sha256=self.__neutral_root_identity_sha256,
                model_snapshot=provenance["model"],
                role_file_sha256=provenance["role_file_sha256"],
                effective_prompt_sha256=provenance["effective_prompt_sha256"],
                projection_sha256=current_projection_sha256,
                digest_sha256=_sha256(digest.encode("utf-8")),
                admitted_view_sha256=_sha256(snapshot.wal_bytes),
                loop_state_sha256=_sha256(snapshot.loop_state_bytes),
                iteration=snapshot.iteration,
                claimed_fresh_context=provenance["fresh_context"],
                claimed_capability_lowering=provenance["capability_lowering"],
                claimed_source_declared_tools=tuple(provenance["source_declared_tools"]),
                claimed_declared_tools=tuple(provenance["declared_tools"]),
                claimed_observed_tool_events=tuple(provenance["observed_tool_events"]),
                evidence_executable_path=provenance["claude_executable_path"],
                evidence_executable_sha256=provenance["claude_executable_sha256"],
                evidence_payload_sha256=payload_sha256,
                evidence_raw_envelope_sha256=envelope_sha256,
                evidence_argv_sha256=_sha256(
                    _canonical_json_bytes(list(self.__provider.argv))
                ),
                evidence_num_turns=envelope["num_turns"],
                evidence_permission_denials_empty=(
                    envelope["permission_denials"] == []
                ),
                evidence_server_tool_use_all_zero=all(
                    type(count) is int and count == 0
                    for count in server_tool_use.values()
                ),
                exact_identity_literals_absent_from_canonical_payload=True,
                identity_non_guarantees=_IDENTITY_NON_GUARANTEES,
                trust_non_guarantees=_TRUST_NON_GUARANTEES,
                capability_non_guarantees=_CAPABILITY_NON_GUARANTEES,
                snapshot_non_guarantees=_SNAPSHOT_NON_GUARANTEES,
                storage_non_guarantees=_STORAGE_NON_GUARANTEES,
                start_receipt_sha256=start_sha256,
            )
            terminal_value = {
                **asdict(receipt),
                "finished_at_ns": time.time_ns(),
            }
            assert terminal_fd is not None
            fd = terminal_fd
            terminal_fd = None
            _finish_reserved_json(fd, terminal_path, terminal_value)
            return B4ClosedCriticInvocation(
                decision=decision,
                receipt=receipt,
                start_receipt_path=start_path,
                terminal_receipt_path=terminal_path,
            )
        except BaseException as exc:
            status = (
                "timeout"
                if isinstance(exc, subprocess.TimeoutExpired)
                or isinstance(exc.__cause__, subprocess.TimeoutExpired)
                else "failure"
            )
            evidence: dict[str, Any] = {}
            for label, path in (
                ("payload", self.__artifact_root / f"payload_{invocation_id}.json"),
                ("raw_envelope", self.__artifact_root / f"envelope_{invocation_id}.json"),
            ):
                if path.is_file():
                    evidence[f"evidence_{label}_sha256"] = _sha256(path.read_bytes())
            failure_value = {
                "schema_version": "p3-b4-closed-critic-terminal/v2",
                "status": status,
                "evidence_class": self.__evidence_class,
                "pair_id": self.__binding.pair_id,
                "arm": self.__binding.arm,
                "campaign_id": self.__binding.campaign_id,
                "controller_id": self.__controller_id,
                "invocation_id": invocation_id,
                "error_type": type(exc).__name__,
                "start_receipt_sha256": start_sha256,
                "finished_at_ns": time.time_ns(),
                **evidence,
            }
            try:
                if terminal_fd is None:
                    raise B4ReceiptError(
                        "reserved terminal fd was consumed before failure transition"
                    )
                fd = terminal_fd
                terminal_fd = None
                _finish_reserved_json(fd, terminal_path, failure_value)
            except BaseException as terminal_exc:
                raise B4ReceiptError(
                    "invocation failed and terminal receipt creation also failed"
                ) from terminal_exc
            raise
        finally:
            if terminal_fd is not None:
                try:
                    os.close(terminal_fd)
                except OSError:
                    pass


class B4ClosedCriticPair:
    """Sealed owner of the two simultaneously created arm controllers."""

    def __init__(
        self,
        *,
        _seal: object,
        on: B4ClosedCriticController,
        off: B4ClosedCriticController,
    ) -> None:
        if _seal is not _PAIR_SEAL:
            raise B4ArmBindingError("B-4 pairs must be made by the sealed factory")
        self.on = on
        self.off = off

    def close(self) -> None:
        self.on.close()
        self.off.close()

    def __enter__(self) -> "B4ClosedCriticPair":
        return self

    def __exit__(self, _exc_type, _exc, _tb) -> None:
        self.close()


def _prepare_b4_closed_critic_pair(
    *,
    on_cfg: CampaignConfig,
    off_cfg: CampaignConfig,
    artifact_root: Path,
) -> tuple[
    _ArmBinding,
    _ArmBinding,
    Path,
    CrossRoleSessionTracker,
    str,
]:
    pair_id = f"b4-pair-{os.urandom(16).hex()}"
    on_binding = _derive_arm(on_cfg, expected_arm="on", pair_id=pair_id)
    off_binding = _derive_arm(off_cfg, expected_arm="off", pair_id=pair_id)
    root = Path(artifact_root)
    try:
        root.mkdir(parents=True, exist_ok=False)
    except FileExistsError as exc:
        raise B4ReceiptError("pair artifact root must not already exist") from exc
    tracker = CrossRoleSessionTracker()
    closure_sha256 = projection_sha256()
    return on_binding, off_binding, root, tracker, closure_sha256


def _seal_b4_closed_critic_pair(
    on_controller: B4ClosedCriticController,
    off_controller: B4ClosedCriticController,
) -> B4ClosedCriticPair:
    if on_controller._pair_identity() == off_controller._pair_identity():
        on_controller.close()
        off_controller.close()
        raise B4ReceiptError("sealed factory reused provider or neutral root identity")
    return B4ClosedCriticPair(
        _seal=_PAIR_SEAL,
        on=on_controller,
        off=off_controller,
    )


def create_b4_closed_critic_pair(
    *,
    on_cfg: CampaignConfig,
    off_cfg: CampaignConfig,
    artifact_root: Path,
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> B4ClosedCriticPair:
    """Create a certified pair with no runner or executable injection seam."""
    trusted_root = _resolve_repository_root(repository_root)
    resolved = shutil.which("claude")
    if resolved is None:
        raise B4TrustRootError("certified executable name claude is not on PATH")
    try:
        certified_executable = str(Path(resolved).resolve(strict=True))
    except OSError as exc:
        raise B4TrustRootError(
            "certified executable name claude cannot be resolved"
        ) from exc
    on_binding, off_binding, root, tracker, closure_sha256 = (
        _prepare_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
        )
    )
    on_controller: B4ClosedCriticController | None = None
    try:
        on_controller = B4ClosedCriticController(
            _seal=_PAIR_SEAL,
            binding=on_binding,
            artifact_root=root / "on",
            repository_root=trusted_root,
            evidence_class="certified",
            executable=certified_executable,
            runner=subprocess.run,
            environ=environ,
            tracker=tracker,
            controller_id=f"b4-on-{os.urandom(16).hex()}",
            initial_projection_sha256=closure_sha256,
        )
        off_controller = B4ClosedCriticController(
            _seal=_PAIR_SEAL,
            binding=off_binding,
            artifact_root=root / "off",
            repository_root=trusted_root,
            evidence_class="certified",
            executable=certified_executable,
            runner=subprocess.run,
            environ=environ,
            tracker=tracker,
            controller_id=f"b4-off-{os.urandom(16).hex()}",
            initial_projection_sha256=closure_sha256,
        )
    except BaseException:
        if on_controller is not None:
            on_controller.close()
        raise
    return _seal_b4_closed_critic_pair(on_controller, off_controller)


def create_b4_closed_critic_pair_for_test(
    *,
    on_cfg: CampaignConfig,
    off_cfg: CampaignConfig,
    artifact_root: Path,
    executable: str | os.PathLike[str],
    runner: Callable[..., Any],
    repository_root: Path | None = None,
    environ: Mapping[str, str] | None = None,
) -> B4ClosedCriticPair:
    """Create explicitly test-only receipts through injected process inputs."""
    trusted_root = _resolve_repository_root(repository_root)
    on_binding, off_binding, root, tracker, closure_sha256 = (
        _prepare_b4_closed_critic_pair(
            on_cfg=on_cfg,
            off_cfg=off_cfg,
            artifact_root=artifact_root,
        )
    )
    on_controller: B4ClosedCriticController | None = None
    try:
        on_controller = B4ClosedCriticController(
            _seal=_PAIR_SEAL,
            binding=on_binding,
            artifact_root=root / "on",
            repository_root=trusted_root,
            evidence_class="test-only",
            executable=executable,
            runner=runner,
            environ=environ,
            tracker=tracker,
            controller_id=f"b4-on-{os.urandom(16).hex()}",
            initial_projection_sha256=closure_sha256,
        )
        off_controller = B4ClosedCriticController(
            _seal=_PAIR_SEAL,
            binding=off_binding,
            artifact_root=root / "off",
            repository_root=trusted_root,
            evidence_class="test-only",
            executable=executable,
            runner=runner,
            environ=environ,
            tracker=tracker,
            controller_id=f"b4-off-{os.urandom(16).hex()}",
            initial_projection_sha256=closure_sha256,
        )
    except BaseException:
        if on_controller is not None:
            on_controller.close()
        raise
    return _seal_b4_closed_critic_pair(on_controller, off_controller)


_RECEIPT_TUPLE_FIELDS = frozenset({
    "claimed_source_declared_tools",
    "claimed_declared_tools",
    "claimed_observed_tool_events",
    "identity_non_guarantees",
    "trust_non_guarantees",
    "capability_non_guarantees",
    "snapshot_non_guarantees",
    "storage_non_guarantees",
})
_START_RECEIPT_KEYS = frozenset({
    "schema_version",
    "status",
    "evidence_class",
    "pair_id",
    "arm",
    "campaign_id",
    "controller_id",
    "invocation_id",
    "started_at_ns",
})
_SUCCESS_TERMINAL_KEYS = frozenset(
    field.name for field in fields(B4ClosedCriticReceipt)
) | {"finished_at_ns"}


def _receipt_pairs_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise B4ReceiptError("receipt evidence contains a duplicate key")
        value[key] = item
    return value


def _read_json_object(path: Path, *, canonical: bool) -> tuple[bytes, dict[str, Any]]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw, object_pairs_hook=_receipt_pairs_object)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise B4ReceiptError(f"receipt evidence is not readable JSON: {path.name}") from exc
    if type(value) is not dict:
        raise B4ReceiptError(f"receipt evidence must be one JSON object: {path.name}")
    if canonical and raw != _canonical_json_bytes(value):
        raise B4ReceiptError(f"receipt evidence is not canonical JSON: {path.name}")
    return raw, value


def _assert_sha256_field(value: Any, field_name: str) -> str:
    if (
        type(value) is not str
        or re.fullmatch(r"[0-9a-f]{64}", value) is None
    ):
        raise B4ReceiptError(f"receipt hash field is invalid: {field_name}")
    return value


def _artifact_for(terminal_path: Path, stem: str, invocation_id: str) -> Path:
    return terminal_path.parent / f"{stem}_{invocation_id}"


def _read_verified_terminal_receipt(
    terminal_receipt_path: str | os.PathLike[str],
) -> B4ClosedCriticReceipt:
    """Re-read one terminal receipt and independently bind all hashed bytes."""
    if isinstance(terminal_receipt_path, B4ClosedCriticReceipt):
        raise B4ReceiptError("pair validation requires terminal receipt file paths")
    try:
        terminal_path = Path(terminal_receipt_path).resolve(strict=True)
    except (TypeError, OSError) as exc:
        raise B4ReceiptError("terminal receipt path is not a readable file") from exc
    terminal_bytes, terminal = _read_json_object(terminal_path, canonical=True)
    del terminal_bytes
    if set(terminal) != _SUCCESS_TERMINAL_KEYS:
        raise B4ReceiptError("terminal success receipt keys do not match exact schema")
    if (
        terminal.get("schema_version") != "p3-b4-closed-critic-receipt/v2"
        or terminal.get("status") != "success"
    ):
        raise B4ReceiptError("pair validation requires a success terminal receipt")
    evidence_class = terminal.get("evidence_class")
    if (
        type(evidence_class) is not str
        or evidence_class not in {"certified", "test-only"}
    ):
        raise B4ReceiptError("terminal receipt evidence_class is invalid")
    if type(terminal.get("finished_at_ns")) is not int:
        raise B4ReceiptError("terminal receipt finished_at_ns must be an exact int")

    converted = dict(terminal)
    converted.pop("finished_at_ns")
    for field_name in _RECEIPT_TUPLE_FIELDS:
        if type(converted.get(field_name)) is not list or any(
            type(item) is not str for item in converted[field_name]
        ):
            raise B4ReceiptError(f"terminal receipt tuple field is invalid: {field_name}")
        converted[field_name] = tuple(converted[field_name])
    try:
        receipt = B4ClosedCriticReceipt(**converted)
    except TypeError as exc:
        raise B4ReceiptError("terminal receipt cannot construct the exact schema") from exc

    if (
        type(receipt.invocation_id) is not str
        or _INVOCATION_ID_RE.fullmatch(receipt.invocation_id) is None
        or terminal_path.name
        != f"receipt_{receipt.invocation_id}_terminal.json"
    ):
        raise B4ReceiptError("terminal receipt path and invocation_id disagree")
    if receipt.arm not in {"on", "off"}:
        raise B4ReceiptError("terminal receipt arm is invalid")
    for field_name in (
        "pair_id",
        "campaign_id",
        "controller_id",
        "session_id",
        "provider_kind",
        "provider_instance_id",
        "model_snapshot",
        "evidence_executable_path",
    ):
        if type(getattr(receipt, field_name)) is not str or not getattr(
            receipt, field_name
        ):
            raise B4ReceiptError(f"terminal receipt string field is invalid: {field_name}")
    if type(receipt.iteration) is not int or receipt.iteration < 1:
        raise B4ReceiptError("terminal receipt iteration must be a positive exact int")
    for field_name in (
        "neutral_root_identity_sha256",
        "role_file_sha256",
        "effective_prompt_sha256",
        "projection_sha256",
        "digest_sha256",
        "admitted_view_sha256",
        "loop_state_sha256",
        "evidence_executable_sha256",
        "evidence_payload_sha256",
        "evidence_raw_envelope_sha256",
        "evidence_argv_sha256",
        "start_receipt_sha256",
    ):
        _assert_sha256_field(getattr(receipt, field_name), field_name)

    start_path = terminal_path.parent / f"receipt_{receipt.invocation_id}_start.json"
    start_bytes, start = _read_json_object(start_path, canonical=True)
    if set(start) != _START_RECEIPT_KEYS:
        raise B4ReceiptError("start receipt keys do not match exact schema")
    if start.get("schema_version") != "p3-b4-critic-start/v2" or start.get(
        "status"
    ) != "started":
        raise B4ReceiptError("start receipt schema or status is invalid")
    for field_name in (
        "evidence_class",
        "pair_id",
        "arm",
        "campaign_id",
        "controller_id",
        "invocation_id",
    ):
        if start.get(field_name) != getattr(receipt, field_name):
            raise B4ReceiptError(f"start and terminal receipt differ: {field_name}")
    if type(start.get("started_at_ns")) is not int:
        raise B4ReceiptError("start receipt started_at_ns must be an exact int")
    if terminal["finished_at_ns"] < start["started_at_ns"]:
        raise B4ReceiptError("terminal receipt precedes its start receipt")
    if _sha256(start_bytes) != receipt.start_receipt_sha256:
        raise B4ReceiptError("start receipt hash does not match its bytes")

    payload_path = _artifact_for(
        terminal_path, "payload", f"{receipt.invocation_id}.json"
    )
    payload_bytes, payload = _read_json_object(payload_path, canonical=True)
    validate_b4_critic_payload(payload)
    if _sha256(payload_bytes) != receipt.evidence_payload_sha256:
        raise B4ReceiptError("payload hash does not match its bytes")
    if _sha256(payload["projected_digest"].encode("utf-8")) != receipt.digest_sha256:
        raise B4ReceiptError("digest hash does not match the sent digest bytes")

    layout = exploration_campaign_layout(receipt.campaign_id)
    assert_no_campaign_identity(
        payload_bytes,
        campaign_path=Path(layout.root).resolve(),
        campaign_id=receipt.campaign_id,
    )
    admitted_path = _artifact_for(
        terminal_path, "admitted_view", f"{receipt.invocation_id}.wal"
    )
    loop_state_artifact = _artifact_for(
        terminal_path, "loop_state", f"{receipt.invocation_id}.json"
    )
    admitted_bytes = _read_bytes(admitted_path, purpose="receipt admitted WAL")
    loop_state_bytes = _read_bytes(
        loop_state_artifact, purpose="receipt loop state"
    )
    if _sha256(admitted_bytes) != receipt.admitted_view_sha256:
        raise B4ReceiptError("admitted view hash does not match its bytes")
    if _sha256(loop_state_bytes) != receipt.loop_state_sha256:
        raise B4ReceiptError("loop state hash does not match its bytes")
    try:
        state = state_from_dict(json.loads(loop_state_bytes))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise B4ReceiptError("receipt loop state is not an admissible checkpoint") from exc
    if (
        not state.whiteboard
        or state.iteration != receipt.iteration
        or state.whiteboard[-1].iteration != receipt.iteration
    ):
        raise B4ReceiptError("receipt iteration does not match loop state bytes")

    argv_path = _artifact_for(
        terminal_path, "argv", f"{receipt.invocation_id}.json"
    )
    argv_bytes = _read_bytes(argv_path, purpose="receipt argv")
    try:
        argv = json.loads(argv_bytes)
    except json.JSONDecodeError as exc:
        raise B4ReceiptError("receipt argv is not JSON") from exc
    if (
        argv_bytes != _canonical_json_bytes(argv)
        or type(argv) is not list
        or not argv
        or any(type(item) is not str for item in argv)
    ):
        raise B4ReceiptError("receipt argv bytes are not one canonical string list")
    if _sha256(argv_bytes) != receipt.evidence_argv_sha256:
        raise B4ReceiptError("argv hash does not match its canonical bytes")
    if argv[0] != receipt.evidence_executable_path:
        raise B4ReceiptError("argv executable differs from executable evidence")

    executable_path = Path(receipt.evidence_executable_path)
    if not executable_path.is_absolute():
        raise B4ReceiptError("receipt executable evidence path is not absolute")
    executable_bytes = _read_bytes(executable_path, purpose="receipt executable")
    if _sha256(executable_bytes) != receipt.evidence_executable_sha256:
        raise B4ReceiptError("executable hash does not match its bytes")
    if _sha256(ROLE_FILE.read_bytes()) != receipt.role_file_sha256:
        raise B4ReceiptError("role file hash does not match current role bytes")
    prompt_path = _artifact_for(
        terminal_path, "effective_prompt", f"{receipt.invocation_id}.txt"
    )
    if _sha256(_read_bytes(prompt_path, purpose="effective prompt")) != (
        receipt.effective_prompt_sha256
    ):
        raise B4ReceiptError("effective prompt hash does not match its bytes")
    neutral_path = _artifact_for(
        terminal_path,
        "neutral_root_identity",
        f"{receipt.invocation_id}.json",
    )
    neutral_bytes, neutral = _read_json_object(neutral_path, canonical=True)
    if set(neutral) != {"device", "inode"} or any(
        type(neutral[key]) is not int for key in neutral
    ):
        raise B4ReceiptError("neutral root identity schema is invalid")
    if _sha256(neutral_bytes) != receipt.neutral_root_identity_sha256:
        raise B4ReceiptError("neutral root identity hash does not match its bytes")
    if projection_sha256() != receipt.projection_sha256:
        raise B4ReceiptError("projection closure hash does not match current bytes")

    envelope_path = _artifact_for(
        terminal_path, "envelope", f"{receipt.invocation_id}.json"
    )
    envelope_bytes, envelope = _read_json_object(envelope_path, canonical=False)
    if _sha256(envelope_bytes) != receipt.evidence_raw_envelope_sha256:
        raise B4ReceiptError("raw envelope hash does not match its bytes")
    if (
        envelope.get("type") != "result"
        or envelope.get("subtype") != "success"
        or envelope.get("is_error") is not False
        or envelope.get("session_id") != receipt.session_id
    ):
        raise B4ReceiptError("raw envelope is not a successful result")
    if (
        type(receipt.evidence_num_turns) is not int
        or type(envelope.get("num_turns")) is not int
        or envelope.get("num_turns") != receipt.evidence_num_turns
    ):
        raise B4ReceiptError("raw envelope num_turns differs from receipt")
    permission_empty = envelope.get("permission_denials") == []
    usage = envelope.get("usage")
    server_tool_use = usage.get("server_tool_use") if isinstance(usage, dict) else None
    if not isinstance(server_tool_use, dict):
        raise B4ReceiptError("raw envelope server_tool_use evidence is missing")
    all_zero = all(
        type(count) is int and count == 0 for count in server_tool_use.values()
    )
    if permission_empty != receipt.evidence_permission_denials_empty:
        raise B4ReceiptError("permission denial evidence differs from raw envelope")
    if all_zero != receipt.evidence_server_tool_use_all_zero:
        raise B4ReceiptError("server tool use evidence differs from raw envelope")
    parse_b4_critic_response(envelope.get("result"))
    model_usage = envelope.get("modelUsage")
    if not isinstance(model_usage, dict):
        raise B4ReceiptError("raw envelope modelUsage evidence is missing")
    opus_slugs = [
        slug
        for slug in model_usage
        if type(slug) is str and slug.startswith("claude-opus-")
    ]
    if opus_slugs != [receipt.model_snapshot]:
        raise B4ReceiptError("raw envelope model differs from receipt")
    model_record = model_usage[receipt.model_snapshot]
    if not isinstance(model_record, dict) or any(
        type(model_record.get(key)) is not int or model_record[key] <= 0
        for key in ("inputTokens", "outputTokens")
    ):
        raise B4ReceiptError("raw envelope model token evidence is invalid")

    if (
        receipt.provider_kind != "claude-headless-projected"
        or receipt.claimed_fresh_context is not True
        or receipt.claimed_capability_lowering != "projection-only-tools-empty"
        or receipt.claimed_declared_tools != ()
        or receipt.claimed_observed_tool_events != ()
        or receipt.evidence_num_turns != 1
        or receipt.evidence_permission_denials_empty is not True
        or receipt.evidence_server_tool_use_all_zero is not True
        or receipt.exact_identity_literals_absent_from_canonical_payload is not True
        or any(type(item) is not str for item in receipt.claimed_source_declared_tools)
    ):
        raise B4ReceiptError("terminal success invariants are not all satisfied")
    if receipt.identity_non_guarantees != _IDENTITY_NON_GUARANTEES:
        raise B4ReceiptError("identity non-guarantees differ from the route contract")
    if receipt.trust_non_guarantees != _TRUST_NON_GUARANTEES:
        raise B4ReceiptError("trust non-guarantees differ from the route contract")
    if receipt.capability_non_guarantees != _CAPABILITY_NON_GUARANTEES:
        raise B4ReceiptError("capability non-guarantees differ from the route contract")
    if receipt.snapshot_non_guarantees != _SNAPSHOT_NON_GUARANTEES:
        raise B4ReceiptError("snapshot non-guarantees differ from the route contract")
    if receipt.storage_non_guarantees != _STORAGE_NON_GUARANTEES:
        raise B4ReceiptError("storage non-guarantees differ from the route contract")
    return receipt


def assert_b4_arm_pair(
    on_terminal_receipt_path: str | os.PathLike[str],
    off_terminal_receipt_path: str | os.PathLike[str],
) -> B4ArmPairComparison:
    """Re-read and structurally validate one same-class terminal pair."""
    on = _read_verified_terminal_receipt(on_terminal_receipt_path)
    off = _read_verified_terminal_receipt(off_terminal_receipt_path)
    if (on.arm, off.arm) != ("on", "off"):
        raise B4ReceiptError("pair receipts must be ordered on then off")
    if on.evidence_class != off.evidence_class:
        raise B4ReceiptError("pair receipts have different evidence_class values")
    if on.pair_id != off.pair_id:
        raise B4ReceiptError("pair receipts have different pair_id commitments")
    common_fields = (
        "provider_kind",
        "model_snapshot",
        "role_file_sha256",
        "effective_prompt_sha256",
        "projection_sha256",
        "evidence_executable_path",
        "evidence_executable_sha256",
        "claimed_capability_lowering",
        "claimed_source_declared_tools",
        "claimed_declared_tools",
    )
    for field_name in common_fields:
        if getattr(on, field_name) != getattr(off, field_name):
            raise B4ReceiptError(f"pair common field differs: {field_name}")
    distinct_fields = (
        "campaign_id",
        "controller_id",
        "session_id",
    )
    for field_name in distinct_fields:
        if getattr(on, field_name) == getattr(off, field_name):
            raise B4ReceiptError(f"pair separation field was reused: {field_name}")
    if (
        on.provider_instance_id == off.provider_instance_id
        or on.neutral_root_identity_sha256 == off.neutral_root_identity_sha256
    ):
        raise B4ReceiptError("pair reused provider instance or neutral root identity")
    return B4ArmPairComparison(
        admitted_view_sha256_equal=(
            on.admitted_view_sha256 == off.admitted_view_sha256
        ),
        loop_state_sha256_equal=(on.loop_state_sha256 == off.loop_state_sha256),
        iteration_equal=(on.iteration == off.iteration),
    )


def main(
    argv: list[str] | None = None,
    *,
    pair_factory: Callable[..., B4ClosedCriticPair] | None = None,
) -> int:
    """Thin sanctioned CLI; it intentionally does not wire the stage-4 driver."""
    parser = argparse.ArgumentParser(description="P3 B-4 closed critic pair invocation")
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--on-invocation-id", required=True)
    parser.add_argument("--off-invocation-id", required=True)
    args = parser.parse_args(argv)
    factory = create_b4_closed_critic_pair if pair_factory is None else pair_factory
    try:
        with factory(
            on_cfg=default_cfg(reflux=True),
            off_cfg=default_cfg(reflux=False),
            artifact_root=args.artifact_root,
        ) as pair:
            on = pair.on.invoke(invocation_id=args.on_invocation_id)
            off = pair.off.invoke(invocation_id=args.off_invocation_id)
            comparison = assert_b4_arm_pair(
                on.terminal_receipt_path,
                off.terminal_receipt_path,
            )
        print(_canonical_json_bytes({
            "schema_version": "p3-b4-closed-critic-cli/v1",
            "on_terminal_receipt": str(on.terminal_receipt_path),
            "off_terminal_receipt": str(off.terminal_receipt_path),
            "pair_comparison": asdict(comparison),
        }).decode("utf-8"))
        return 0
    except (B4ClosedCriticError, PredictionRunnerError) as exc:
        print(f"B-4 closed critic invocation failed: {type(exc).__name__}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
