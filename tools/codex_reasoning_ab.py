#!/usr/bin/env python3
"""T-181 の凍結 benchmark と Codex run を read-only に検査・集計する。

このツールは reasoning の既定値を変更しない。機械層が返す R-1 は候補だけであり、
primary endpoint は arm 情報を隠した親の意味裁定である。
"""
from __future__ import annotations

import argparse
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_EVEN, localcontext
import glob
import hashlib
import importlib.util
import json
import math
import os
import re
import secrets
import signal
import shutil
import stat
import subprocess
import sys
import time
import types
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


_ROOT = Path(__file__).resolve().parents[1]
_LEDGER_PATH = Path(__file__).with_name("codex_worker_ledger.py")
_LEDGER_SPEC = importlib.util.spec_from_file_location(
    "codex_worker_ledger_for_reasoning_ab", _LEDGER_PATH
)
if _LEDGER_SPEC is None or _LEDGER_SPEC.loader is None:
    raise ImportError(f"ledger を import できない: {_LEDGER_PATH}")
LEDGER = importlib.util.module_from_spec(_LEDGER_SPEC)
_ORIGINAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
try:
    sys.dont_write_bytecode = True
    _LEDGER_SPEC.loader.exec_module(LEDGER)
finally:
    sys.dont_write_bytecode = _ORIGINAL_DONT_WRITE_BYTECODE


_PRICE_SNAPSHOT_TOOL_PATH = Path(__file__).with_name("t189_price_snapshot.py")
_PRICE_SNAPSHOT_MODULE_NAME = (
    f"t189_price_snapshot_for_reasoning_ab_{uuid.uuid4().hex}"
)
_PRICE_SNAPSHOT_SPEC = importlib.util.spec_from_file_location(
    _PRICE_SNAPSHOT_MODULE_NAME, _PRICE_SNAPSHOT_TOOL_PATH
)
if _PRICE_SNAPSHOT_SPEC is None or _PRICE_SNAPSHOT_SPEC.loader is None:
    raise ImportError(
        f"price snapshot verifier を import できない: {_PRICE_SNAPSHOT_TOOL_PATH}"
    )
PRICE_SNAPSHOT = importlib.util.module_from_spec(_PRICE_SNAPSHOT_SPEC)
sys.modules[_PRICE_SNAPSHOT_MODULE_NAME] = PRICE_SNAPSHOT
try:
    _ORIGINAL_DONT_WRITE_BYTECODE = sys.dont_write_bytecode
    try:
        sys.dont_write_bytecode = True
        _PRICE_SNAPSHOT_SPEC.loader.exec_module(PRICE_SNAPSHOT)
    finally:
        sys.dont_write_bytecode = _ORIGINAL_DONT_WRITE_BYTECODE
except BaseException:
    if sys.modules.get(_PRICE_SNAPSHOT_MODULE_NAME) is PRICE_SNAPSHOT:
        sys.modules.pop(_PRICE_SNAPSHOT_MODULE_NAME, None)
    raise


_WIRING_SLICE_TOOL_PATH = Path(__file__).with_name("t189_oracle_wiring_slice.py")
_WIRING_SLICE_TOOL_SHA256 = (
    "5a9edd483e91c176083331df3ee37fdce9a7c563f7d7489fb9127742ebd7d469"
)
WIRING_SLICE_PROFILE = "t189-oracle-wiring-slice-v1"
_WIRING_SLICE_MANIFEST_KIND = "t189-task-oracle-wiring-slice"
_WIRING_SLICE_MANIFEST_RAW_SHA256 = (
    "96a39ee259f985525df0a1206665dd331eb23b24e365b84e4558bfe115e75767"
)


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        metadata.st_dev,
        metadata.st_ino,
        stat.S_IFMT(metadata.st_mode),
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


def _load_pinned_wiring_slice_module(path: Path) -> types.ModuleType:
    """Compile and execute the verifier bytes authenticated by this parent."""
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ImportError(
            f"oracle wiring slice verifier is unavailable or unsafe: {path}"
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ImportError(
                f"oracle wiring slice verifier is not a regular file: {path}"
            )
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
        if _file_identity(before) != _file_identity(after):
            raise ImportError(
                f"oracle wiring slice verifier changed while reading: {path}"
            )
    finally:
        os.close(descriptor)
    if hashlib.sha256(raw).hexdigest() != _WIRING_SLICE_TOOL_SHA256:
        raise ImportError("oracle wiring slice verifier SHA-256 pin mismatch")

    module_name = f"t189_oracle_wiring_slice_for_reasoning_ab_{uuid.uuid4().hex}"
    module = types.ModuleType(module_name)
    module.__file__ = os.fspath(path)
    module.__package__ = "tools"
    sys.modules[module_name] = module
    try:
        code = compile(raw, os.fspath(path), "exec")
        original_dont_write_bytecode = sys.dont_write_bytecode
        try:
            sys.dont_write_bytecode = True
            exec(code, module.__dict__)
        finally:
            sys.dont_write_bytecode = original_dont_write_bytecode
    except BaseException:
        if sys.modules.get(module_name) is module:
            sys.modules.pop(module_name, None)
        raise
    return module


WIRING_SLICE = _load_pinned_wiring_slice_module(_WIRING_SLICE_TOOL_PATH)
if (
    WIRING_SLICE.SLICE_KIND != _WIRING_SLICE_MANIFEST_KIND
    or WIRING_SLICE.SLICE_SHA256 != _WIRING_SLICE_MANIFEST_RAW_SHA256
):
    raise ImportError("oracle wiring slice verifier constants mismatch parent pins")


LEGACY_SCHEMA_VERSION = 2
TASK_MANIFEST_SCHEMA_VERSION = 3
SCHEDULE_SCHEMA_VERSION = 3
# Existing snapshot/receipt serializers remain v2 until their owning waves add
# an explicit v3 serializer.  The manifest and normalized schedule have their
# own version so that a v2 artifact is never compared as a v3 artifact.
SCHEMA_VERSION = LEGACY_SCHEMA_VERSION
STAGE2_REPLAYER_SCHEMA_VERSION = 1
STAGE2_REPLAYER_MAX_MODEL_CALLS = 250
STAGE2_REPLAYER_DEFAULT_WALL_CLOCK_TIMEOUT_S = 300.0
STAGE2_REPLAYER_MAX_WALL_CLOCK_TIMEOUT_S = 3_600.0
STAGE2_REPLAYER_VERSION_PROBE_TIMEOUT_S = 10.0
STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION = 2
STAGE5_AUTHOR_REPLAYER_MAX_FIX_PASSES = 3
STAGE5_AUTHOR_REPLAYER_GIT_TIMEOUT_S = 30.0
STAGE5_AUTHOR_REPLAYER_VERSION_PROBE_TIMEOUT_S = 10.0
BASE_COMMIT = "8c8dc5e0a337677e213b4ebabbeff5ea188111ae"
INTEGRATED_COMMIT = "9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec"
ARTIFACT_COMMIT = "08a7e5f2fc08d57309a86ef70d00e9b050ebec9c"
BRANCH = "codex/dev-wave-t153e-t15423"
MODEL = "gpt-5.6-sol"
FROZEN_PRICE_SNAPSHOT_PATH = (
    "output/t189-routing-preregistration/price-snapshot-v1.json"
)
FROZEN_PRICE_SNAPSHOT_SHA256 = (
    "a0b2c71654d2ba1c58ca2184f903c856e269de5d46f3a64a6148ec035db8b3b1"
)
FROZEN_PRICE_VERSION = (
    "openai-pricing-standard-short-context:sha256:"
    "fca40df4ec205375f6751fb59d9770f9aa8234c25968a758a8b6b70c34e97675"
)
FROZEN_PRICE_EXCERPT_PATH = (
    "output/t189-routing-preregistration/price-standard-table-excerpt.html"
)
FROZEN_PRICE_EXCERPT_SHA256 = (
    "32d016abae45142697ed608fb56f43e35483e43715965fb7b935bdf7dc6a78d4"
)
OLD_ROOT = (
    "/home/SFC/tanab/github/izanagi/.codex/worktrees/"
    "dev-wave-t153e-t15423"
)
ARTIFACT_DIR = "output/insights/2026-07-29_t153e-t15423-review-verbatim"

_LEGACY_SESSION_IDS = {
    "POS": "019faca2-6e1f-7601-bfc7-be27edcfb4ba",
    "NEG": "019facbe-9584-7642-aa30-37f1c77e6c5f",
    "fix2": "019facb2-7ddb-7102-814d-eeddcb1102ed",
    "author": "019fac6b-4f74-7a03-aa4d-8a9de22b352c",
    "fix1": "019fac91-8cde-7f73-bce1-77a9d63b4269",
}
_LEGACY_ROLLOUT_SHA256 = {
    "POS": "9b90d51079e6a2be4603b366d77283950fff79535f59dbb8b4f4eecb1374032b",
    "NEG": "40a14e9089c2a9931b661023d104dcde2d965452e7c5ce3c630dbd2662ff4012",
    "fix2": "b07581b4f0e6ef9935549e9b9783a8ebb6877d87a10265ac7916a7d4a89c880a",
    "author": "e1ffc1e5b5e6d354701798d41a97a5e6da622423214531f356db3f1bb3ce6cbe",
    "fix1": "f210f2e135f6cfdb2e6c2a40e81b784a2a8f4ac51135c353cf859365e17fb475",
}
_LEGACY_PROMPT_SOURCE = {
    "POS": {
        "sha256": "511941738fd39a20ac9fb41ce2f4c3ed0039c35fca637ded0fa2fb6679667829",
        "chars": 2000,
        "bytes": 2706,
        "replacements": 9,
    },
    "NEG": {
        "sha256": "7735616ef7817b991cb196df1faa313a3a38b917646cb45ef4dd9fbb0f7fafc3",
        "chars": 2767,
        "bytes": 3779,
        "replacements": 13,
    },
}

TRACKED_PATHS = (
    "docs/ai-provenance.md",
    "docs/decisions.md",
    "orchestrator/tests/test_check_ai_provenance.py",
    "orchestrator/tests/test_check_docs.py",
    "tools/check_ai_provenance.py",
    "tools/check_docs.py",
)
PATCH_PATHS = (
    "tools/check_ai_provenance.py",
    "orchestrator/tests/test_check_ai_provenance.py",
)
TRACKED_HASHES = {
    "docs/ai-provenance.md": "f00a045ba8d7e4a655b5a5e18beec94972291fb4c416b9bfcae6aeab97a75059",
    "docs/decisions.md": "16bc9b74fce0548c42e21a5d5076c9694bf2115b7d2d561f4522768366b3330e",
    "tools/check_docs.py": "707f8f369086fe80cec9d296be8e9b3fad26a82ea08b7cc69149ec662e533195",
    "orchestrator/tests/test_check_docs.py": "38675b065a56230f8998b653d5da7e14d1d505f1c289ca0e84d5b5b2103b3e83",
}
ARTIFACT_HASHES = {
    "brief.md": "821634ecef736dfbbde4b9288126f37b8ea0917b893b4e7596e6efe4b821b452",
    "adjudication-plan-v2.md": "9e8208325ed27979f75b7d1c4b20b90a9220fa286f6a47fe5e81ef7bad45e7b5",
    "review-a.md": "beea33ee7bb10acc583db30ef32252683c41fa3fe0ac3626db426103f5f102cc",
    "review-b.md": "04bbe6fc8feedca29b67f7ea9c29587e60539538592f8b9efe6db3f46f770f8c",
    "fix1.md": "e581c63399f20dbda51f223b05fbf4dadcf5e38961c9650dad2aca3756a39997",
    "fix2.md": "ffdff13cbe4d98aa56fe4502be63beb0a5acfb36c35a818b76462bb6f6d847cd",
    "focus1.md": "901ad02256524bac35c56ae4e3a2b7c5fbc01a618670182885040c6912b82771",
}
_LEGACY_CASE_ARTIFACTS = {
    "POS": ("review-a.md", "review-b.md", "fix1.md"),
    "NEG": (
        "brief.md",
        "adjudication-plan-v2.md",
        "review-a.md",
        "review-b.md",
        "focus1.md",
        "fix2.md",
    ),
}
_LEGACY_CASE_HASHES = {
    "POS": {
        **TRACKED_HASHES,
        "tools/check_ai_provenance.py": "bc3f5f95f5c9c3f44955bbd1b2e3affbbafb6e62fda8e836173e1b9d5998c3af",
        "orchestrator/tests/test_check_ai_provenance.py": "ed3f93d196e7c43c8ba61c83f91f065d3fc829f0d12bdc4d9ead31b2ec3d57ed",
        **{
            f"{ARTIFACT_DIR}/{name}": ARTIFACT_HASHES[name]
            for name in _LEGACY_CASE_ARTIFACTS["POS"]
        },
    },
    "NEG": {
        **TRACKED_HASHES,
        "tools/check_ai_provenance.py": "0bc510b4e239394524aad209bd1c01ec4ff3d3d34938dec432c211bf8964970f",
        "orchestrator/tests/test_check_ai_provenance.py": "c4f5f04b8a06c03f4c7e85900e54a2c34a9ea65873e37a340f81b926df098e74",
        **{
            f"{ARTIFACT_DIR}/{name}": ARTIFACT_HASHES[name]
            for name in _LEGACY_CASE_ARTIFACTS["NEG"]
        },
    },
}
_LEGACY_CASE_NUMSTAT = {
    "POS": (
        (3, 3, "docs/ai-provenance.md"),
        (45, 0, "docs/decisions.md"),
        (693, 0, "orchestrator/tests/test_check_ai_provenance.py"),
        (37, 0, "orchestrator/tests/test_check_docs.py"),
        (123, 10, "tools/check_ai_provenance.py"),
        (9, 1, "tools/check_docs.py"),
    ),
    "NEG": (
        (3, 3, "docs/ai-provenance.md"),
        (45, 0, "docs/decisions.md"),
        (764, 0, "orchestrator/tests/test_check_ai_provenance.py"),
        (37, 0, "orchestrator/tests/test_check_docs.py"),
        (126, 10, "tools/check_ai_provenance.py"),
        (9, 1, "tools/check_docs.py"),
    ),
}
LEGACY_EXPECTED_SCHEDULE = {
    ("POS", "max"): 3,
    ("POS", "high"): 3,
    ("NEG", "max"): 2,
    ("NEG", "high"): 2,
}
_LEGACY_KNOWN_FINDINGS = {
    "A-1", "A-2", "A-3", "A-4",
    "B-1", "B-2", "B-3", "B-4", "B-5", "B-6", "R-1",
}


def _manifest_task_entry(
    benchmark_task_id: str, *, oracle_kind: str
) -> dict[str, Any]:
    """Build one manifest entry from the frozen v2 provenance values.

    The old constants are kept in private staging names only while this
    literal manifest is assembled.  Public legacy aliases below are derived
    from the manifest, so callers cannot accidentally acquire a second source
    of truth for POS/NEG provenance.
    """
    return {
        "benchmark_task_id": benchmark_task_id,
        "legacy_case": benchmark_task_id,
        "task_type": "t181-frozen",
        "stage": None,
        "oracle_kind": oracle_kind,
        "provenance": {
            "session_id": _LEGACY_SESSION_IDS[benchmark_task_id],
            "rollout_sha256": _LEGACY_ROLLOUT_SHA256[benchmark_task_id],
            "prompt_source": dict(_LEGACY_PROMPT_SOURCE[benchmark_task_id]),
        },
        "snapshot": {
            "artifact_names": list(_LEGACY_CASE_ARTIFACTS[benchmark_task_id]),
            "hashes": dict(_LEGACY_CASE_HASHES[benchmark_task_id]),
            "numstat": [list(row) for row in _LEGACY_CASE_NUMSTAT[benchmark_task_id]],
        },
        "known_finding_ids": sorted(_LEGACY_KNOWN_FINDINGS),
    }


TASK_MANIFEST: dict[str, Any] = {
    "schema_version": TASK_MANIFEST_SCHEMA_VERSION,
    "manifest_kind": "t181-task-manifest",
    "tasks": {
        "POS": _manifest_task_entry("POS", oracle_kind="positive"),
        "NEG": _manifest_task_entry("NEG", oracle_kind="negative"),
    },
    "shared_provenance": {
        "auxiliary_sessions": {
            role: {
                "session_id": _LEGACY_SESSION_IDS[role],
                "rollout_sha256": _LEGACY_ROLLOUT_SHA256[role],
            }
            for role in ("fix1", "fix2", "author")
        },
        "tracked_hashes": dict(TRACKED_HASHES),
        "artifact_hashes": dict(ARTIFACT_HASHES),
    },
}

# These aliases are deliberately derived from TASK_MANIFEST.  They preserve
# the v2 API and byte-level values while making the manifest the only POS/NEG
# provenance definition.
SESSION_IDS = {
    **{
        task["legacy_case"]: task["provenance"]["session_id"]
        for task in TASK_MANIFEST["tasks"].values()
    },
    **{
        role: row["session_id"]
        for role, row in TASK_MANIFEST["shared_provenance"][
            "auxiliary_sessions"
        ].items()
    },
}
ROLLOUT_SHA256 = {
    **{
        task["legacy_case"]: task["provenance"]["rollout_sha256"]
        for task in TASK_MANIFEST["tasks"].values()
    },
    **{
        role: row["rollout_sha256"]
        for role, row in TASK_MANIFEST["shared_provenance"][
            "auxiliary_sessions"
        ].items()
    },
}
PROMPT_SOURCE = {
    task["legacy_case"]: dict(task["provenance"]["prompt_source"])
    for task in TASK_MANIFEST["tasks"].values()
}
CASE_ARTIFACTS = {
    task["legacy_case"]: tuple(task["snapshot"]["artifact_names"])
    for task in TASK_MANIFEST["tasks"].values()
}
CASE_HASHES = {
    task["legacy_case"]: dict(task["snapshot"]["hashes"])
    for task in TASK_MANIFEST["tasks"].values()
}
CASE_NUMSTAT = {
    task["legacy_case"]: tuple(tuple(row) for row in task["snapshot"]["numstat"])
    for task in TASK_MANIFEST["tasks"].values()
}
# The public name remains a v2 compatibility alias for the downstream legacy
# validator.  New schedule consumers must call expected_schedule_from_manifest
# so their expected set comes from the manifest/schedule rows.
EXPECTED_SCHEDULE = dict(
    {
        (task_id, arm): count
        for (task_id, arm), count in LEGACY_EXPECTED_SCHEDULE.items()
    }
)
KNOWN_FINDINGS = {
    finding_id
    for task in TASK_MANIFEST["tasks"].values()
    for finding_id in task["known_finding_ids"]
}
ZERO_COMPONENT_TOTAL_ONLY = "zero_component_total_only"
_ZERO_COMPONENT_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)

RC_SNAPSHOT = 20
RC_SESSION = 21
RC_ROUTING = 22
RC_SCORE = 23
RC_AGGREGATE = 24
RC_RECEIPT = 25

_GIT_FSCK_MAX_WORKERS = 8


class ValidationError(Exception):
    """安定した failure reason を持つ検査失敗。"""

    def __init__(self, reasons: str | Iterable[str], rc: int = 2):
        if isinstance(reasons, str):
            reasons = [reasons]
        self.reasons = tuple(str(reason) for reason in reasons)
        self.rc = rc
        super().__init__("; ".join(self.reasons))


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        + b"\n"
    )


def _json_lines(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows: list[dict[str, Any]] = []
    issues: list[str] = []
    try:
        stream = path.open("rb")
    except OSError as exc:
        return [], [f"cannot read JSONL {path}: {exc}"]
    with stream:
        for line_number, line in enumerate(stream, 1):
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                issues.append(f"{path}:{line_number}: malformed JSON")
                continue
            if not isinstance(value, dict):
                issues.append(f"{path}:{line_number}: JSON value is not an object")
                continue
            rows.append(value)
    return rows, issues


def _session_meta_rows(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    try:
        stream = path.open("rb")
    except OSError:
        return rows
    with stream:
        for line in stream:
            if not (
                b'"session_meta"' in line
                or b"\\u00" in line  # ASCII character JSON Unicode escape
                or b"\x00" in line  # UTF-16/UTF-32 accepted by json.loads
            ):
                continue
            try:
                value = json.loads(line)
            except (json.JSONDecodeError, UnicodeDecodeError):
                continue
            if isinstance(value, dict) and value.get("type") == "session_meta":
                rows.append(value)
    return rows


def _run(
    argv: Sequence[str],
    *,
    cwd: Path,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    completed = subprocess.run(
        list(argv),
        cwd=cwd,
        input=input_bytes,
        capture_output=True,
        check=False,
        env=_clean_environment({"HOME": "/nonexistent"}),
    )
    if check and completed.returncode != 0:
        detail = completed.stderr.decode("utf-8", "replace").strip()
        raise ValidationError(
            f"command failed rc={completed.returncode}: {' '.join(argv)}: {detail}",
            RC_SNAPSHOT,
        )
    return completed


def _git(repo: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    return _run(("git", *args), cwd=repo, input_bytes=input_bytes).stdout


def _rollout_matches_session(path: Path, target_session_id: str) -> bool:
    owns_target = False
    first_owns_target = False
    declares_target = False
    saw_determinable = False
    for row in _session_meta_rows(path):
        if row.get("type") != "session_meta":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue

        if "id" not in payload:
            own_candidate = payload.get("session_id")
        else:
            own_candidate = payload.get("id")
        own_session_id = (
            own_candidate
            if isinstance(own_candidate, str) and own_candidate
            else None
        )
        if own_session_id is None:
            continue

        if own_session_id == target_session_id:
            owns_target = True
            if not saw_determinable:
                first_owns_target = True
        saw_determinable = True
        if (
            own_session_id != target_session_id
            and payload.get("session_id") == target_session_id
        ):
            declares_target = True

    return owns_target and (first_owns_target or not declares_target)


def _find_rollout(
    sessions_root: Path,
    target_session_id: str,
    *,
    pinned_label: str | None = None,
    pinned_sha256: str | None = None,
) -> Path:
    if pinned_sha256 is not None:
        expected_sha256 = pinned_sha256
        eligible = (
            pinned_label is not None
            and isinstance(target_session_id, str)
            and bool(target_session_id)
            and isinstance(expected_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None
        )
    else:
        expected_sha256 = ROLLOUT_SHA256.get(pinned_label or "")
        eligible = (
            pinned_label is not None
            and SESSION_IDS.get(pinned_label) == target_session_id
            and isinstance(expected_sha256, str)
            and re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is not None
        )
    if eligible:
        candidate: Path | None = None
        try:
            assert pinned_label is not None
            separators = (os.sep,) if os.altsep is None else (os.sep, os.altsep)
            if not any(separator in target_session_id for separator in separators):
                escaped = glob.escape(target_session_id)
                candidates = sorted(
                    sessions_root.rglob(f"rollout-*-{escaped}.jsonl"),
                    key=os.fspath,
                )
                if len(candidates) == 1:
                    candidate = candidates[0]
        except Exception:
            pass

        if candidate is not None and _rollout_matches_session(
            candidate, target_session_id
        ):
            try:
                resolved = candidate.resolve()
                assert pinned_label is not None
                _verify_rollout_sha(
                    resolved,
                    pinned_label,
                    expected_sha256=expected_sha256,
                )
            except (OSError, ValidationError):
                pass
            else:
                return resolved

    matches: list[Path] = []
    for path in sorted(sessions_root.rglob("rollout-*.jsonl"), key=os.fspath):
        if _rollout_matches_session(path, target_session_id):
            matches.append(path.resolve())
    if len(matches) != 1:
        raise ValidationError(
            f"session {target_session_id} rollout count is {len(matches)}, expected 1",
            RC_SESSION,
        )
    return matches[0]


def _verify_rollout_sha(
    path: Path,
    label: str,
    *,
    expected_sha256: str | None = None,
) -> None:
    expected = (
        expected_sha256
        if expected_sha256 is not None
        else ROLLOUT_SHA256[label]
    )
    actual = _sha256(path.read_bytes())
    if actual != expected:
        raise ValidationError(
            f"{label} rollout sha mismatch: {actual} != {expected}", RC_SNAPSHOT
        )


def _extract_apply_patches(path: Path) -> list[str]:
    rows, issues = _json_lines(path)
    if issues:
        raise ValidationError(issues, RC_SNAPSHOT)
    patches: list[str] = []
    for row in rows:
        if row.get("type") != "response_item":
            continue
        payload = row.get("payload")
        if not isinstance(payload, dict):
            continue
        if payload.get("type") == "custom_tool_call" and payload.get("name") == "apply_patch":
            patch = payload.get("input")
            if not isinstance(patch, str):
                raise ValidationError("apply_patch input is not a string", RC_SNAPSHOT)
            patches.append(patch)
    return patches


def _normalize_patch_path(raw: str, allowed: Iterable[str]) -> str:
    normalized = raw.replace("\\", "/")
    candidates = [path for path in allowed if normalized == path or normalized.endswith("/" + path)]
    if len(candidates) != 1 or ".." in Path(raw).parts:
        raise ValidationError(f"patch path is outside allowlist: {raw}", RC_SNAPSHOT)
    return candidates[0]


def _patch_updates(
    patch: str, allowed: Iterable[str]
) -> list[tuple[str, list[tuple[str | None, list[str]]]]]:
    lines = patch.splitlines()
    if not lines or lines[0] != "*** Begin Patch" or lines[-1] != "*** End Patch":
        raise ValidationError("invalid apply_patch envelope", RC_SNAPSHOT)
    updates: list[tuple[str, list[tuple[str | None, list[str]]]]] = []
    index = 1
    while index < len(lines) - 1:
        header = lines[index]
        if not header.startswith("*** Update File: "):
            if header.startswith(("*** Add File:", "*** Delete File:", "*** Move to:")):
                raise ValidationError(f"unsupported patch operation: {header}", RC_SNAPSHOT)
            raise ValidationError(f"unexpected patch line: {header}", RC_SNAPSHOT)
        path = _normalize_patch_path(header.removeprefix("*** Update File: "), allowed)
        index += 1
        hunks: list[tuple[str | None, list[str]]] = []
        while index < len(lines) - 1 and not lines[index].startswith("*** Update File: "):
            if lines[index].startswith("*** "):
                raise ValidationError(f"unsupported patch marker: {lines[index]}", RC_SNAPSHOT)
            if not lines[index].startswith("@@"):
                raise ValidationError("patch hunk is missing @@ marker", RC_SNAPSHOT)
            marker_line = lines[index]
            anchor = (
                marker_line[3:]
                if marker_line.startswith("@@ ") and marker_line[3:]
                else None
            )
            index += 1
            hunk: list[str] = []
            while (
                index < len(lines) - 1
                and not lines[index].startswith("@@")
                and not lines[index].startswith("*** Update File: ")
            ):
                line = lines[index]
                if line == "*** End of File":
                    index += 1
                    continue
                if not line or line[0] not in " +-":
                    raise ValidationError(f"invalid hunk line: {line!r}", RC_SNAPSHOT)
                hunk.append(line)
                index += 1
            if not hunk:
                raise ValidationError("empty patch hunk", RC_SNAPSHOT)
            hunks.append((anchor, hunk))
        updates.append((path, hunks))
    return updates


def _replace_once(
    lines: list[str], before: list[str], after: list[str], *, min_start: int
) -> tuple[list[str], int]:
    positions = [
        index
        for index in range(min_start, len(lines) - len(before) + 1)
        if lines[index : index + len(before)] == before
    ]
    if not positions:
        raise ValidationError(
            "strict patch context not found in hunk order", RC_SNAPSHOT
        )
    start = positions[0]
    return (
        lines[:start] + after + lines[start + len(before) :],
        start + len(after),
    )


def _apply_update_bytes(
    data: bytes,
    hunks: list[tuple[str | None, list[str]]],
    *,
    reverse: bool,
) -> bytes:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"patch target is not UTF-8: {exc}", RC_SNAPSHOT) from exc
    had_newline = text.endswith("\n")
    current = text.splitlines()
    cursor = 0
    for anchor, hunk in hunks:
        before_prefixes = " +" if reverse else " -"
        after_prefixes = " -" if reverse else " +"
        before = [line[1:] for line in hunk if line[0] in before_prefixes]
        after = [line[1:] for line in hunk if line[0] in after_prefixes]
        if anchor is not None:
            before.insert(0, anchor)
            after.insert(0, anchor)
        current, cursor = _replace_once(
            current, before, after, min_start=cursor
        )
    result = "\n".join(current)
    if had_newline:
        result += "\n"
    return result.encode("utf-8")


def _apply_patch_set(
    files: Mapping[str, bytes],
    patches: Iterable[str],
    *,
    reverse: bool = False,
    parse_allowed: Iterable[str] | None = None,
) -> dict[str, bytes]:
    result = dict(files)
    for patch in patches:
        for path, hunks in _patch_updates(patch, parse_allowed or result):
            if path in result:
                result[path] = _apply_update_bytes(
                    result[path], hunks, reverse=reverse
                )
    return result


def _apply_update_bytes_independent(
    data: bytes,
    hunks: list[tuple[str | None, list[str]]],
    *,
    reverse: bool,
) -> bytes:
    """Byte-preserving decoder used only by golden route B."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"patch target is not UTF-8: {exc}", RC_SNAPSHOT) from exc
    had_newline = text.endswith("\n")
    current = text[:-1].split("\n") if had_newline else text.split("\n")
    cursor = 0
    for anchor, hunk in hunks:
        removed = " +" if reverse else " -"
        added = " -" if reverse else " +"
        before = [line[1:] for line in hunk if line[0] in removed]
        after = [line[1:] for line in hunk if line[0] in added]
        if anchor is not None:
            before = [anchor, *before]
            after = [anchor, *after]
        match = next(
            (
                index
                for index in range(cursor, len(current) - len(before) + 1)
                if current[index : index + len(before)] == before
            ),
            None,
        )
        if match is None:
            raise ValidationError(
                "independent patch context not found in hunk order", RC_SNAPSHOT
            )
        current[match : match + len(before)] = after
        cursor = match + len(after)
    rendered = "\n".join(current) + ("\n" if had_newline else "")
    return rendered.encode("utf-8")


def _patch_updates_independent(
    patch: str, allowed: Iterable[str]
) -> list[tuple[str, list[tuple[str | None, list[str]]]]]:
    """Route B parser intentionally shares no envelope/hunk parser with route A."""
    records = patch.split("\n")
    if records[-1] == "":
        records.pop()
    if records[:1] != ["*** Begin Patch"] or records[-1:] != ["*** End Patch"]:
        raise ValidationError("independent patch envelope mismatch", RC_SNAPSHOT)
    index = 1
    updates: list[tuple[str, list[tuple[str | None, list[str]]]]] = []
    while index < len(records) - 1:
        prefix = "*** Update File: "
        if not records[index].startswith(prefix):
            raise ValidationError(
                f"independent patch operation unsupported: {records[index]}",
                RC_SNAPSHOT,
            )
        path = _normalize_patch_path(records[index][len(prefix) :], allowed)
        index += 1
        hunks: list[tuple[str | None, list[str]]] = []
        while index < len(records) - 1 and not records[index].startswith(prefix):
            marker = records[index]
            if not marker.startswith("@@"):
                raise ValidationError(
                    "independent patch hunk marker missing", RC_SNAPSHOT
                )
            anchor = marker[3:] if marker.startswith("@@ ") and marker[3:] else None
            index += 1
            body: list[str] = []
            while (
                index < len(records) - 1
                and not records[index].startswith("@@")
                and not records[index].startswith(prefix)
            ):
                record = records[index]
                index += 1
                if record == "*** End of File":
                    continue
                if not record or record[0] not in {" ", "+", "-"}:
                    raise ValidationError(
                        f"independent patch line invalid: {record!r}",
                        RC_SNAPSHOT,
                    )
                body.append(record)
            if not body:
                raise ValidationError("independent patch hunk empty", RC_SNAPSHOT)
            hunks.append((anchor, body))
        updates.append((path, hunks))
    return updates


def _apply_patch_set_independent(
    files: Mapping[str, bytes],
    patches: Iterable[str],
    *,
    reverse: bool = False,
    parse_allowed: Iterable[str] | None = None,
) -> dict[str, bytes]:
    result = dict(files)
    for patch in patches:
        for path, hunks in _patch_updates_independent(
            patch, parse_allowed or result
        ):
            if path in result:
                result[path] = _apply_update_bytes_independent(
                    result[path], hunks, reverse=reverse
                )
    return result


def _compare_golden_routes(
    route_a: Mapping[str, bytes], route_b: Mapping[str, bytes]
) -> dict[str, bytes]:
    reasons = [
        f"independent golden mismatch for {path}"
        for path in PATCH_PATHS
        if route_a.get(path) != route_b.get(path)
    ]
    if reasons:
        raise ValidationError(reasons, RC_SNAPSHOT)
    return dict(route_a)


def derive_independent_golden(
    repo: Path,
    sessions_root: Path,
    *,
    verify_source_sha: bool = True,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, bytes]:
    _validate_materialized_task_manifest(task_manifest)
    shared = task_manifest["shared_provenance"]
    auxiliary = shared["auxiliary_sessions"]
    paths = {
        label: _find_rollout(
            sessions_root,
            auxiliary[label]["session_id"],
            pinned_label=label,
            pinned_sha256=auxiliary[label]["rollout_sha256"],
        )
        for label in ("author", "fix1", "fix2")
    }
    if verify_source_sha:
        for label, path in paths.items():
            _verify_rollout_sha(
                path,
                label,
                expected_sha256=auxiliary[label]["rollout_sha256"],
            )
    fix2_patches = _extract_apply_patches(paths["fix2"])
    if len(fix2_patches) != 1:
        raise ValidationError(
            f"fix2 apply_patch count is {len(fix2_patches)}, expected 1", RC_SNAPSHOT
        )
    route_a = {
        path: _git(repo, "show", f"{INTEGRATED_COMMIT}:{path}")
        for path in PATCH_PATHS
    }
    route_a = _apply_patch_set(route_a, fix2_patches, reverse=True)

    route_b = {
        path: _git(repo, "show", f"{BASE_COMMIT}:{path}") for path in PATCH_PATHS
    }
    route_b = _apply_patch_set_independent(
        route_b,
        (
            patch
            for label in ("author", "fix1")
            for patch in _extract_apply_patches(paths[label])
            if any(
                raw_path in patch
                for raw_path in PATCH_PATHS
            )
        ),
        parse_allowed=TRACKED_PATHS,
    )
    return _compare_golden_routes(route_a, route_b)


def _snapshot_spec(
    case: str,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    try:
        task = _manifest_task(case=case, manifest=task_manifest)
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_SNAPSHOT) from exc
    legacy_case = task["legacy_case"]
    snapshot = task["snapshot"]
    hashes = dict(snapshot["hashes"])
    return {
        "case": legacy_case,
        "benchmark_task_id": task["benchmark_task_id"],
        "legacy_case": legacy_case,
        "head": BASE_COMMIT,
        "branch": BRANCH,
        "tracked_paths": list(TRACKED_PATHS),
        "hashes": hashes,
        "numstat": [list(row) for row in snapshot["numstat"]],
        "untracked": [
            f"{ARTIFACT_DIR}/{name}" for name in snapshot["artifact_names"]
        ],
        "modes": {path: stat.S_IFREG | 0o644 for path in hashes},
        "forbidden": (
            [f"{ARTIFACT_DIR}/focus1.md", f"{ARTIFACT_DIR}/focus2.md"]
            if legacy_case == "POS"
            else [f"{ARTIFACT_DIR}/focus2.md"]
        ),
    }


def _init_submodules_from_local_source(source: Path, snapshot: Path) -> None:
    preflight_cache: dict[Path, tuple[str, ...]] = {}

    def initialize_pair(source_repo: Path, snapshot_repo: Path) -> None:
        entries = {
            relative: (mode, object_id)
            for mode, object_id, _, relative in _index_stage_entries(source_repo)
        }
        initialized: list[tuple[str, str, Path]] = []
        for name, relative in _direct_submodules(source_repo):
            mode_and_id = entries.get(relative)
            if mode_and_id is None or mode_and_id[0] != "160000":
                raise ValidationError(
                    f"{source_repo}: .gitmodules path is not a gitlink: {relative}",
                    RC_SNAPSHOT,
                )
            state, local = _submodule_worktree_state(
                source_repo,
                name,
                relative,
                mode_and_id[1],
                source,
                require_admin_within_snapshot=False,
                preflight_cache=preflight_cache,
                allow_builder_transport=True,
            )
            if state == "initialized":
                repository_reasons = preflight_cache.get(local, ())
                if repository_reasons:
                    raise ValidationError(repository_reasons, RC_SNAPSHOT)
                initialized.append((name, relative, local))

        for name, relative, local in initialized:
            _git(
                snapshot_repo,
                "config",
                f"submodule.{name}.url",
                os.fspath(local),
            )
            _run(
                (
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "update",
                    "--init",
                    "--no-fetch",
                    "--",
                    relative,
                ),
                cwd=snapshot_repo,
            )
            initialize_pair(local, (snapshot_repo / relative).resolve())

    initialize_pair(source, snapshot)


def _git_dir(repo: Path) -> Path:
    raw = _git(
        repo, "--no-replace-objects", "rev-parse", "--absolute-git-dir"
    ).decode().strip()
    return Path(raw).resolve()


def _remove_git_object_info_caches(git_dir: Path) -> None:
    """Remove clone/repack-derived metadata after the object store is pruned."""
    object_info = git_dir / "objects" / "info"
    if not _path_lexists(object_info):
        return
    metadata = object_info.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError(
            f"git objects/info is not a non-symlink directory: {object_info}",
            RC_SNAPSHOT,
        )
    for path in object_info.iterdir():
        path_metadata = path.lstat()
        if stat.S_ISDIR(path_metadata.st_mode) and not stat.S_ISLNK(
            path_metadata.st_mode
        ):
            shutil.rmtree(path)
        else:
            path.unlink()


def _seal_one_git_closure(repo: Path, expected_ref: str | None) -> None:
    refs = _git(repo, "for-each-ref", "--format=%(refname)").decode().splitlines()
    for ref in refs:
        if ref != expected_ref:
            _git(repo, "update-ref", "-d", ref)
    for remote in _git(repo, "remote").decode().splitlines():
        _git(repo, "remote", "remove", remote)
    _run(
        ("git", "reflog", "expire", "--expire=now", "--expire-unreachable=now", "--all"),
        cwd=repo,
    )
    _run(("git", "repack", "-Ad"), cwd=repo)
    _run(("git", "prune-packed"), cwd=repo)
    _run(("git", "prune", "--expire=now"), cwd=repo)

    git_dir = _git_dir(repo)
    # A transferred object store can carry a commit-graph whose entries outlive
    # the commits just pruned above.  All objects/info entries are derived
    # metadata (including monolithic/split commit-graphs and the dumb-transport
    # packs cache), so rebuild none of them for this sealed, local-only snapshot.
    _remove_git_object_info_caches(git_dir)
    if expected_ref is not None:
        loose_ref = git_dir / expected_ref
        loose_ref.parent.mkdir(parents=True, exist_ok=True)
        loose_ref.write_text(_git(repo, "rev-parse", "HEAD").decode().strip() + "\n")
    packed_refs = git_dir / "packed-refs"
    if packed_refs.exists():
        packed_refs.unlink()
    logs = git_dir / "logs"
    if logs.exists():
        shutil.rmtree(logs)
    for relative in (
        "refs/remotes",
        "refs/tags",
        "refs/replace",
        "refs/original",
    ):
        directory = git_dir / relative
        if directory.exists():
            shutil.rmtree(directory)
    alternates = git_dir / "objects" / "info" / "alternates"
    if alternates.exists():
        alternates.unlink()
    http_alternates = git_dir / "objects" / "info" / "http-alternates"
    if http_alternates.exists():
        http_alternates.unlink()
    grafts = git_dir / "info" / "grafts"
    if grafts.exists():
        grafts.unlink()
    for path in git_dir.iterdir():
        if path.is_file() and (
            path.name.endswith("_HEAD")
            or path.name
            in {"MERGE_HEAD", "BISECT_HEAD", "REVERT_HEAD", "CHERRY_PICK_HEAD"}
        ):
            path.unlink()


def _direct_submodules(repository: Path) -> list[tuple[str, str]]:
    modules_file = repository / ".gitmodules"
    if not modules_file.exists() and not modules_file.is_symlink():
        return []
    metadata = modules_file.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValidationError(
            f"{repository}: .gitmodules is not a regular file", RC_SNAPSHOT
        )
    modules = _run(
        (
            "git",
            "--no-replace-objects",
            "config",
            "-f",
            ".gitmodules",
            "--get-regexp",
            r"^submodule\..*\.path$",
        ),
        cwd=repository,
        check=False,
    )
    if modules.returncode == 1 and not modules.stdout:
        return []
    if modules.returncode != 0:
        raise ValidationError(
            f"cannot enumerate .gitmodules in {repository}", RC_SNAPSHOT
        )
    submodules: list[tuple[str, str]] = []
    for line in modules.stdout.decode("utf-8").splitlines():
        fields = line.split(None, 1)
        if len(fields) != 2:
            raise ValidationError(
                f"cannot parse .gitmodules path: {line}", RC_SNAPSHOT
            )
        key, relative = fields
        name = key.removeprefix("submodule.").removesuffix(".path")
        if not name:
            raise ValidationError(
                f"cannot parse .gitmodules name: {line}", RC_SNAPSHOT
            )
        submodules.append((name, relative))
    names = [name for name, _ in submodules]
    paths = [relative for _, relative in submodules]
    if len(names) != len(set(names)):
        raise ValidationError(
            f"duplicate .gitmodules name in {repository}", RC_SNAPSHOT
        )
    if len(paths) != len(set(paths)):
        raise ValidationError(
            f"duplicate .gitmodules path in {repository}", RC_SNAPSHOT
        )
    return sorted(submodules, key=lambda row: row[1])


def _direct_submodule_paths(repository: Path) -> list[str]:
    return [relative for _, relative in _direct_submodules(repository)]


def _path_lexists(path: Path) -> bool:
    try:
        path.lstat()
    except FileNotFoundError:
        return False
    return True


def _submodule_worktree_state(
    repository: Path,
    name: str,
    relative: str,
    gitlink_commit: str,
    snapshot: Path,
    *,
    require_admin_within_snapshot: bool = True,
    preflight_cache: dict[Path, tuple[str, ...]] | None = None,
    allow_builder_transport: bool = False,
) -> tuple[str, Path]:
    snapshot = snapshot.resolve()
    repository = repository.resolve()
    raw_relative = Path(relative)
    if raw_relative.is_absolute():
        raise ValidationError(
            f"absolute submodule path is forbidden: {relative}", RC_SNAPSHOT
        )
    candidate_path = repository / raw_relative
    candidate = candidate_path.resolve()
    if repository not in candidate.parents or snapshot not in candidate.parents:
        raise ValidationError(f"submodule escapes snapshot: {relative}", RC_SNAPSHOT)

    modules_root = _git_dir(repository) / "modules"
    admin_path = modules_root / name
    admin_dir = admin_path.resolve()
    if admin_dir != modules_root.resolve() and modules_root.resolve() not in admin_dir.parents:
        raise ValidationError(
            f"submodule administrative path escapes object store: {name}",
            RC_SNAPSHOT,
        )
    candidate_exists = _path_lexists(candidate_path)
    admin_exists = _path_lexists(admin_dir)
    marker_exists = (
        _path_lexists(candidate_path / ".git") if candidate_exists else False
    )

    if candidate_exists:
        metadata = candidate_path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValidationError(
                f"submodule worktree is not a directory: "
                f"{candidate.relative_to(snapshot).as_posix()}",
                RC_SNAPSHOT,
            )
        if marker_exists and admin_exists:
            if preflight_cache is None:
                repository_reasons = tuple(
                    _repository_preflight_reasons(
                        snapshot,
                        candidate,
                        allow_builder_transport=allow_builder_transport,
                    )
                )
            else:
                repository_reasons = preflight_cache.get(candidate)
                if repository_reasons is None:
                    repository_reasons = tuple(
                        _repository_preflight_reasons(
                            snapshot,
                            candidate,
                            allow_builder_transport=allow_builder_transport,
                        )
                    )
                    preflight_cache[candidate] = repository_reasons
            if repository_reasons:
                if preflight_cache is None:
                    raise ValidationError(repository_reasons, RC_SNAPSHOT)
                return "initialized", candidate
        probe = _run(
            ("git", "--no-replace-objects", "rev-parse", "--show-toplevel"),
            cwd=candidate_path,
            check=False,
        )
        if (
            probe.returncode == 0
            and Path(probe.stdout.decode().strip()).resolve() == candidate
        ):
            label = candidate.relative_to(snapshot).as_posix()
            head_probe = _run(
                ("git", "--no-replace-objects", "rev-parse", "HEAD"),
                cwd=candidate_path,
                check=False,
            )
            if head_probe.returncode != 0:
                raise ValidationError(
                    f"initialized submodule HEAD cannot be resolved: {label}",
                    RC_SNAPSHOT,
                )
            head = head_probe.stdout.decode().strip()
            if head != gitlink_commit:
                raise ValidationError(
                    f"initialized submodule HEAD/gitlink mismatch: "
                    f"{candidate.relative_to(snapshot).as_posix()}: "
                    f"{head} != {gitlink_commit}",
                    RC_SNAPSHOT,
                )
            marker = candidate_path / ".git"
            try:
                marker_metadata = marker.lstat()
            except OSError as exc:
                raise ValidationError(
                    f"initialized submodule git marker cannot be inspected: "
                    f"{label}: {exc}",
                    RC_SNAPSHOT,
                ) from exc
            if stat.S_ISLNK(marker_metadata.st_mode) or not stat.S_ISREG(
                marker_metadata.st_mode
            ):
                raise ValidationError(
                    f"initialized submodule git marker is not a non-symlink "
                    f"regular file: {label}",
                    RC_SNAPSHOT,
                )
            try:
                admin_relative = admin_path.relative_to(snapshot)
            except ValueError:
                if require_admin_within_snapshot:
                    raise ValidationError(
                        f"initialized submodule administrative path escapes "
                        f"snapshot: {label}",
                        RC_SNAPSHOT,
                    )
                cursor = Path(admin_path.anchor)
                admin_components = admin_path.parts[1:]
            else:
                cursor = snapshot
                admin_components = admin_relative.parts
            for component in admin_components:
                cursor /= component
                try:
                    component_metadata = cursor.lstat()
                except OSError as exc:
                    raise ValidationError(
                        f"initialized submodule administrative path cannot be "
                        f"inspected: {label}: {exc}",
                        RC_SNAPSHOT,
                    ) from exc
                if stat.S_ISLNK(component_metadata.st_mode):
                    raise ValidationError(
                        f"initialized submodule administrative path contains "
                        f"a symlink: {label}",
                        RC_SNAPSHOT,
                    )

            admin_probe = _run(
                (
                    "git",
                    "--no-replace-objects",
                    "rev-parse",
                    "--absolute-git-dir",
                ),
                cwd=candidate_path,
                check=False,
            )
            common_probe = _run(
                (
                    "git",
                    "--no-replace-objects",
                    "rev-parse",
                    "--git-common-dir",
                ),
                cwd=candidate_path,
                check=False,
            )
            if admin_probe.returncode != 0 or common_probe.returncode != 0:
                raise ValidationError(
                    f"initialized submodule gitdir/common-dir cannot be "
                    f"inspected: {label}",
                    RC_SNAPSHOT,
                )

            def resolved_git_path(payload: bytes) -> Path:
                path = Path(os.fsdecode(payload.strip()))
                if not path.is_absolute():
                    path = candidate_path / path
                return path.resolve()

            if resolved_git_path(admin_probe.stdout) != admin_dir:
                raise ValidationError(
                    f"initialized submodule gitdir/admin mismatch: {label}",
                    RC_SNAPSHOT,
                )
            if resolved_git_path(common_probe.stdout) != admin_dir:
                raise ValidationError(
                    f"initialized submodule common-dir/admin mismatch: {label}",
                    RC_SNAPSHOT,
                )
            return "initialized", candidate

    nonempty = candidate_exists and any(candidate_path.iterdir())
    if marker_exists or admin_exists or nonempty:
        raise ValidationError(
            f"submodule object store cannot be inspected: "
            f"{candidate.relative_to(snapshot).as_posix()}",
            RC_SNAPSHOT,
        )
    return "uninitialized", candidate


def _submodule_inventory(
    snapshot: Path,
    *,
    preflight_cache: dict[Path, tuple[str, ...]] | None = None,
    allow_builder_transport: bool = False,
) -> tuple[list[Path], list[dict[str, str]]]:
    snapshot = snapshot.resolve()
    repositories: list[Path] = []
    rows: list[dict[str, str]] = []
    seen = {snapshot}

    def visit(repository: Path) -> None:
        entries = _index_stage_entries(repository)
        gitlinks = {
            relative: object_id
            for mode, object_id, _, relative in entries
            if mode == "160000"
        }
        declared = _direct_submodules(repository)
        declared_paths = {relative for _, relative in declared}
        if set(gitlinks) != declared_paths:
            label = (
                "."
                if repository == snapshot
                else repository.relative_to(snapshot).as_posix()
            )
            raise ValidationError(
                f"{label}: gitlink/.gitmodules mismatch: "
                f"{sorted(gitlinks)} != {sorted(declared_paths)}",
                RC_SNAPSHOT,
            )
        for name, relative in declared:
            state, candidate = _submodule_worktree_state(
                repository,
                name,
                relative,
                gitlinks[relative],
                snapshot,
                preflight_cache=preflight_cache,
                allow_builder_transport=allow_builder_transport,
            )
            manifest_path = candidate.relative_to(snapshot).as_posix()
            if candidate in seen:
                raise ValidationError(
                    f"duplicate or cyclic submodule repository: {manifest_path}",
                    RC_SNAPSHOT,
                )
            seen.add(candidate)
            rows.append(
                {
                    "path": manifest_path,
                    "gitlink_commit": gitlinks[relative],
                    "initialization": state,
                }
            )
            if state == "initialized":
                repositories.append(candidate)
                if not (
                    preflight_cache is not None
                    and preflight_cache.get(candidate)
                ):
                    visit(candidate)

    visit(snapshot)
    return repositories, rows


def _submodule_manifest_sha256(rows: Sequence[Mapping[str, str]]) -> str:
    return _sha256(_canonical_bytes(list(rows)))


def _assert_submodule_manifest_sha256(
    rows: Sequence[Mapping[str, str]], expected_sha256: Any
) -> None:
    actual = _submodule_manifest_sha256(rows)
    if actual != expected_sha256:
        raise ValidationError(
            "scheduled submodule initialization or gitlink state mismatch",
            RC_SNAPSHOT,
        )


def _submodule_repositories(snapshot: Path) -> list[Path]:
    return _submodule_inventory(snapshot)[0]


def _preflight_snapshot_relocation(base: Path) -> None:
    base = base.resolve()
    for repository in _submodule_repositories(base):
        marker = repository / ".git"
        try:
            metadata = marker.lstat()
        except OSError as exc:
            raise ValidationError(
                f"submodule git marker cannot be inspected: {marker}: {exc}",
                RC_SNAPSHOT,
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ValidationError(
                f"submodule git marker is not a regular file: {marker}",
                RC_SNAPSHOT,
            )
        try:
            raw_marker = marker.read_bytes()
        except OSError as exc:
            raise ValidationError(
                f"submodule git marker cannot be read: {marker}: {exc}",
                RC_SNAPSHOT,
            ) from exc
        prefix = b"gitdir: "
        payload = (
            raw_marker[len(prefix) :].strip()
            if raw_marker.startswith(prefix)
            else b""
        )
        if not payload or b"\n" in payload or b"\r" in payload:
            raise ValidationError(
                f"submodule git marker is malformed: {marker}", RC_SNAPSHOT
            )
        if Path(os.fsdecode(payload)).is_absolute():
            raise ValidationError(
                f"absolute submodule gitdir is not relocatable: {marker}",
                RC_SNAPSHOT,
            )

        worktree = _run(
            ("git", "config", "--get", "core.worktree"),
            cwd=repository,
            check=False,
        )
        if worktree.returncode == 1 and not worktree.stdout:
            continue
        if worktree.returncode != 0:
            raise ValidationError(
                f"submodule core.worktree cannot be inspected: {repository}",
                RC_SNAPSHOT,
            )
        values = worktree.stdout.decode("utf-8").splitlines()
        if len(values) != 1 or not values[0]:
            raise ValidationError(
                f"submodule core.worktree is malformed: {repository}",
                RC_SNAPSHOT,
            )
        if Path(values[0]).is_absolute():
            raise ValidationError(
                f"absolute submodule core.worktree is not relocatable: {repository}",
                RC_SNAPSHOT,
            )


def _seal_git_object_closure(snapshot: Path) -> None:
    repositories, _ = _submodule_inventory(
        snapshot, allow_builder_transport=True
    )
    _seal_one_git_closure(snapshot, f"refs/heads/{BRANCH}")
    for repository in repositories:
        _seal_one_git_closure(repository, None)
    for repository in (snapshot, *repositories):
        config_probe = _run(
            ("git", "config", "--name-only", "--get-regexp", r"^submodule\."),
            cwd=repository,
            check=False,
        )
        config_rows = config_probe.stdout.decode().splitlines()
        sections = sorted({".".join(row.split(".")[:2]) for row in config_rows})
        for section in sections:
            _run(
                ("git", "config", "--remove-section", section),
                cwd=repository,
                check=False,
            )


def _scandir_entries(directory: Path, *, purpose: str) -> list[os.DirEntry[str]]:
    """Enumerate one directory without collapsing an operational failure."""
    try:
        with os.scandir(directory) as iterator:
            return list(iterator)
    except OSError as exc:
        raise ValidationError(
            f"{purpose} directory enumeration failed at {directory}: "
            f"{type(exc).__name__}: {exc}",
            RC_SNAPSHOT,
        ) from exc


def _metadata_paths(root: Path) -> list[Path]:
    paths: list[Path] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        directories: list[Path] = []
        for entry in _scandir_entries(directory, purpose="metadata"):
            path = Path(entry.path)
            paths.append(path)
            try:
                is_directory = entry.is_dir(follow_symlinks=False)
            except OSError as exc:
                raise ValidationError(
                    f"metadata entry inspection failed at {path}: "
                    f"{type(exc).__name__}: {exc}",
                    RC_SNAPSHOT,
                ) from exc
            if is_directory:
                directories.append(path)
        pending.extend(reversed(directories))
    return paths


def _metadata_manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    paths = sorted(
        _metadata_paths(root),
        key=lambda item: item.relative_to(root).as_posix(),
    )
    for path in paths:
        relative = path.relative_to(root).as_posix()
        try:
            metadata = path.lstat()
            mode = stat.S_IFMT(metadata.st_mode) | stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                kind = "directory"
                digest = None
            elif stat.S_ISLNK(metadata.st_mode):
                kind = "symlink"
                digest = _sha256(os.readlink(path).encode("utf-8"))
            elif stat.S_ISREG(metadata.st_mode):
                kind = "file"
                digest = _sha256(path.read_bytes())
            else:
                kind = "other"
                digest = None
        except OSError as exc:
            raise ValidationError(
                f"metadata inspection failed at {path}: "
                f"{type(exc).__name__}: {exc}",
                RC_SNAPSHOT,
            ) from exc
        rows.append(
            {
                "path": relative,
                "kind": kind,
                "st_mode": mode,
                "sha256": digest,
            }
        )
    return rows


def _filesystem_file_set(snapshot: Path) -> set[str]:
    """Return non-directory paths observed in a static snapshot tree.

    On a readable, static tree this preserves the former ``Path.rglob`` file
    set.  The walk is not atomic if the tree changes while it is in progress.
    A real directory named ``.git`` directly below the root is pruned after an
    ``lstat``; symlink entries are included but their targets are never walked.
    Directory enumeration and entry ``lstat`` failures are rejected rather
    than being interpreted as an empty subtree.
    """
    found: set[str] = set()
    pending = [snapshot]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = list(iterator)
        except OSError as exc:
            raise ValidationError(
                f"filesystem directory enumeration failed at {directory}: "
                f"{type(exc).__name__}: {exc}",
                RC_SNAPSHOT,
            ) from exc

        directories: list[Path] = []
        for entry in entries:
            path = Path(entry.path)
            try:
                metadata = path.lstat()
            except OSError as exc:
                raise ValidationError(
                    f"filesystem entry lstat failed at {path}: "
                    f"{type(exc).__name__}: {exc}",
                    RC_SNAPSHOT,
                ) from exc
            if stat.S_ISDIR(metadata.st_mode):
                if directory == snapshot and entry.name == ".git":
                    continue
                directories.append(path)
            else:
                found.add(path.relative_to(snapshot).as_posix())

        pending.extend(reversed(directories))
    return found


@dataclass
class _SnapshotFilesystemFiles:
    """One lazily evaluated filesystem observation bound to one snapshot."""

    snapshot: Path
    _files: set[str] | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self.snapshot = self.snapshot.resolve()

    def read(self, snapshot: Path) -> set[str]:
        candidate = snapshot.resolve()
        if candidate != self.snapshot:
            raise ValidationError(
                "filesystem observation snapshot mismatch: "
                f"{candidate} != {self.snapshot}",
                RC_SNAPSHOT,
            )
        if self._files is None:
            self._files = _filesystem_file_set(self.snapshot)
        return self._files


def _index_stage_entries(repository: Path) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    raw = _git(
        repository,
        "--no-replace-objects",
        "ls-files",
        "--stage",
        "-z",
    )
    for record in raw.split(b"\0"):
        if not record:
            continue
        try:
            metadata, path_bytes = record.split(b"\t", 1)
            mode_bytes, object_id, stage_bytes = metadata.split(b" ")
        except ValueError as exc:
            raise ValidationError(
                f"cannot parse ls-files --stage row in {repository}",
                RC_SNAPSHOT,
            ) from exc
        if (
            not re.fullmatch(rb"[0-7]{6}", mode_bytes)
            or not re.fullmatch(rb"[0-9a-f]+", object_id)
            or not stage_bytes.isdigit()
        ):
            raise ValidationError(
                f"invalid ls-files --stage metadata in {repository}",
                RC_SNAPSHOT,
            )
        mode = mode_bytes.decode("ascii")
        stage = stage_bytes.decode("ascii")
        relative = os.fsdecode(path_bytes)
        if mode not in {"100644", "100755", "120000", "160000"}:
            raise ValidationError(
                f"unsupported index mode in {repository}: {mode} {relative}",
                RC_SNAPSHOT,
            )
        if stage != "0":
            raise ValidationError(
                f"non-zero index stage in {repository}: {stage} {relative}",
                RC_SNAPSHOT,
            )
        entries.append((mode, object_id.decode("ascii"), stage, relative))
    return entries


_LOCAL_CONFIG_STATIC_KEYS = frozenset(
    {
        "core.bare",
        "core.filemode",
        "core.ignorecase",
        "core.logallrefupdates",
        "core.precomposeunicode",
        "core.repositoryformatversion",
        "core.symlinks",
        "core.worktree",
    }
)
_LOCAL_CONFIG_DYNAMIC_KEYS = (
    re.compile(r"branch\..+\.(?:merge|remote)\Z"),
    re.compile(r"remote\..+\.(?:fetch|url)\Z"),
    re.compile(
        r"submodule\..+\."
        r"(?:active|branch|fetchrecursesubmodules|ignore|update|url)\Z"
    ),
    re.compile(r"user\.(?:email|name)\Z"),
)


def _repository_label(snapshot: Path, repository: Path) -> str:
    if repository == snapshot:
        return "."
    try:
        return repository.relative_to(snapshot).as_posix()
    except ValueError:
        return "<outside-snapshot>"


def _local_config_allowlist_reasons(
    snapshot: Path,
    repositories: Sequence[Path],
    *,
    allow_builder_transport: bool = False,
) -> list[str]:
    reasons: list[str] = []
    for repository in repositories:
        label = _repository_label(snapshot, repository)
        try:
            probe = _run(
                (
                    "git",
                    "--no-replace-objects",
                    "config",
                    "--local",
                    "--name-only",
                    "--null",
                    "--list",
                ),
                cwd=repository,
                check=False,
            )
            if probe.returncode != 0:
                reasons.append(
                    f"snapshot repository local config cannot be inspected: "
                    f"{label}"
                )
                continue
            keys = sorted(
                {
                    os.fsdecode(raw).lower()
                    for raw in probe.stdout.split(b"\0")
                    if raw
                }
            )
            forbidden = [
                key
                for key in keys
                if key not in _LOCAL_CONFIG_STATIC_KEYS
                and not (
                    allow_builder_transport
                    and any(
                        pattern.fullmatch(key)
                        for pattern in _LOCAL_CONFIG_DYNAMIC_KEYS
                    )
                )
            ]
            if forbidden:
                reasons.append(
                    f"snapshot repository local config is not allowlisted: "
                    f"{label}: {forbidden}"
                )
        except Exception as exc:
            reasons.append(
                f"snapshot repository local config cannot be inspected: "
                f"{label}: {type(exc).__name__}"
            )
    return reasons


def _raw_blob_object_id(payload: bytes) -> str:
    header = f"blob {len(payload)}\0".encode("ascii")
    return hashlib.sha1(header + payload).hexdigest()


def _submodule_non_directory_files(
    repository: Path, gitlinks: set[str]
) -> set[str]:
    found: set[str] = set()

    def fail_walk(error: OSError) -> None:
        raise error

    for current, directories, files in os.walk(
        repository, followlinks=False, onerror=fail_walk
    ):
        current_path = Path(current)
        current_relative = current_path.relative_to(repository)
        retained: list[str] = []
        for name in directories:
            path = current_path / name
            relative = (current_relative / name).as_posix()
            metadata = path.lstat()
            if current_relative == Path() and name == ".git":
                continue
            if relative in gitlinks:
                continue
            if stat.S_ISLNK(metadata.st_mode):
                found.add(relative)
                continue
            retained.append(name)
        directories[:] = retained
        for name in files:
            found.add((current_relative / name).as_posix())
    return found


def _one_submodule_content_identity_reasons(
    snapshot: Path, repository: Path
) -> list[str]:
    label = _repository_label(snapshot, repository)
    diff = _run(
        (
            "git",
            "--no-replace-objects",
            "diff-index",
            "--cached",
            "--quiet",
            "--ignore-submodules=none",
            "HEAD",
            "--",
        ),
        cwd=repository,
        check=False,
    )
    if diff.returncode == 1:
        return [f"initialized submodule index/HEAD tree mismatch: {label}"]
    if diff.returncode != 0:
        return [
            f"initialized submodule content cannot be inspected: {label}: "
            f"diff-index exited {diff.returncode}"
        ]

    entries = _index_stage_entries(repository)
    indexed_files: set[str] = set()
    gitlinks: set[str] = set()
    for mode, object_id, _, relative in entries:
        raw_relative = Path(relative)
        if (
            raw_relative.is_absolute()
            or not raw_relative.parts
            or any(part in {"", ".", ".."} for part in raw_relative.parts)
        ):
            return [
                f"initialized submodule tracked path is unsafe: "
                f"{label}: {relative}"
            ]
        cursor = repository
        for component in raw_relative.parts[:-1]:
            cursor /= component
            try:
                metadata = cursor.lstat()
            except OSError:
                return [
                    f"initialized submodule tracked path cannot be inspected: "
                    f"{label}: {relative}"
                ]
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(
                metadata.st_mode
            ):
                return [
                    f"initialized submodule tracked path crosses unsafe "
                    f"component: {label}: {relative}"
                ]
        path = repository / raw_relative
        if mode == "160000":
            gitlinks.add(relative)
            if _path_lexists(path):
                metadata = path.lstat()
                if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(
                    metadata.st_mode
                ):
                    return [
                        f"initialized submodule worktree/index mode mismatch: "
                        f"{label}: {relative}"
                    ]
            continue
        indexed_files.add(relative)
        try:
            metadata = path.lstat()
        except OSError:
            return [
                f"initialized submodule worktree/index mismatch: "
                f"{label}: {relative}"
            ]
        if mode == "120000":
            if not stat.S_ISLNK(metadata.st_mode):
                return [
                    f"initialized submodule worktree/index mode mismatch: "
                    f"{label}: {relative}"
                ]
            payload = os.fsencode(os.readlink(path))
        else:
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(
                metadata.st_mode
            ):
                return [
                    f"initialized submodule worktree/index mode mismatch: "
                    f"{label}: {relative}"
                ]
            executable = bool(metadata.st_mode & stat.S_IXUSR)
            if executable != (mode == "100755"):
                return [
                    f"initialized submodule worktree/index mode mismatch: "
                    f"{label}: {relative}"
                ]
            payload = path.read_bytes()
        if _raw_blob_object_id(payload) != object_id:
            return [
                f"initialized submodule worktree/index mismatch: "
                f"{label}: {relative}"
            ]

    actual_files = _submodule_non_directory_files(repository, gitlinks)
    expected_files = indexed_files | {".git"}
    if actual_files != expected_files:
        extra = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        return [
            f"initialized submodule worktree file-set mismatch: {label}: "
            f"extra={extra}, missing={missing}"
        ]
    return []


def _repository_preflight_reasons(
    snapshot: Path,
    repository: Path,
    *,
    allow_builder_transport: bool = False,
) -> list[str]:
    snapshot = snapshot.resolve()
    repository = repository.resolve()
    reasons: list[str] = []
    label = _repository_label(snapshot, repository)
    try:
        probe = _run(
            (
                "git",
                "--no-replace-objects",
                "rev-parse",
                "--show-object-format",
            ),
            cwd=repository,
            check=False,
        )
        object_format = probe.stdout.decode("ascii").strip()
        if probe.returncode != 0:
            reasons.append(
                f"snapshot repository object format cannot be inspected: "
                f"{label}"
            )
        elif object_format != "sha1":
            reasons.append(
                f"snapshot repository object format is not sha1: "
                f"{label}: {object_format}"
            )
    except Exception as exc:
        reasons.append(
            f"snapshot repository object format cannot be inspected: "
            f"{label}: {type(exc).__name__}"
        )
    if not reasons:
        reasons.extend(
            _local_config_allowlist_reasons(
                snapshot,
                (repository,),
                allow_builder_transport=allow_builder_transport,
            )
        )
    return reasons


def _cached_repository_preflight_reasons(
    snapshot: Path,
    repository: Path,
    cache: dict[Path, tuple[str, ...]],
    *,
    allow_builder_transport: bool = False,
) -> tuple[str, ...]:
    repository = repository.resolve()
    cached = cache.get(repository)
    if cached is None:
        cached = tuple(
            _repository_preflight_reasons(
                snapshot,
                repository,
                allow_builder_transport=allow_builder_transport,
            )
        )
        cache[repository] = cached
    return cached


def _submodule_content_identity_reasons(
    snapshot: Path,
    repositories: Sequence[Path],
    *,
    preflight_cache: dict[Path, tuple[str, ...]] | None = None,
) -> list[str]:
    try:
        snapshot = snapshot.resolve()
        repositories = [repository.resolve() for repository in repositories]
    except Exception as exc:
        return [
            f"initialized submodule content cannot be inspected: "
            f"{type(exc).__name__}"
        ]
    if any(snapshot not in repository.parents for repository in repositories):
        return [
            "initialized submodule repository escapes snapshot: "
            "<outside-snapshot>"
        ]
    cache = preflight_cache if preflight_cache is not None else {}
    reasons = list(
        _cached_repository_preflight_reasons(snapshot, snapshot, cache)
    )
    for repository in repositories:
        repository_preflight = _cached_repository_preflight_reasons(
            snapshot, repository, cache
        )
        if repository_preflight:
            reasons.extend(repository_preflight)
            continue
        try:
            reasons.extend(
                _one_submodule_content_identity_reasons(snapshot, repository)
            )
        except Exception as exc:
            reasons.append(
                f"initialized submodule content cannot be inspected: "
                f"{_repository_label(snapshot, repository)}: "
                f"{type(exc).__name__}"
            )
    return reasons


def _expected_filesystem_files(
    snapshot: Path,
    untracked: Iterable[str],
    initialized: Sequence[Path] | None = None,
) -> set[str]:
    snapshot = snapshot.resolve()
    if initialized is None:
        initialized, _ = _submodule_inventory(snapshot)
    repositories = [snapshot, *initialized]
    tracked: set[str] = set()
    for repository in repositories:
        prefix = (
            Path()
            if repository == snapshot
            else repository.relative_to(snapshot)
        )
        entries = _index_stage_entries(repository)
        for mode, _, _, relative in entries:
            if mode != "160000":
                tracked.add((prefix / relative).as_posix())
        if repository != snapshot:
            tracked.add((prefix / ".git").as_posix())
    return tracked | set(untracked)


def _stderr_first_line(completed: subprocess.CompletedProcess[bytes]) -> str:
    lines = completed.stderr.decode("utf-8", "replace").splitlines()
    return lines[0].strip() if lines else "<empty stderr>"


def _git_fsck_reasons(
    label: str, completed: subprocess.CompletedProcess[bytes]
) -> list[str]:
    reasons: list[str] = []
    if completed.returncode != 0:
        reasons.append(
            f"{label}: git fsck exited {completed.returncode}: "
            f"{_stderr_first_line(completed)}"
        )
    unreachable = [
        line
        for line in completed.stdout.decode("utf-8", "replace").splitlines()
        if line.strip()
    ]
    if unreachable:
        reasons.append(
            f"{label}: git object store contains unreachable objects "
            f"({len(unreachable)})"
        )
    return reasons


def _commit_graph_manifest(
    repository: Path,
    label: str,
    metadata: Sequence[Mapping[str, Any]],
) -> tuple[list[str], dict[str, Any]]:
    paths = [
        dict(row)
        for row in metadata
        if row.get("path") == "objects/info/commit-graph"
        or str(row.get("path", "")).startswith("objects/info/commit-graphs/")
        or row.get("path") == "objects/info/commit-graphs"
    ]
    if not paths:
        return [], {
            "present": False,
            "valid": None,
            "paths": [],
            "verify_returncode": None,
            "verify_stderr_first_line": None,
        }
    verify = _run(
        ("git", "commit-graph", "verify"),
        cwd=repository,
        check=False,
    )
    first_line = (
        _stderr_first_line(verify) if verify.returncode != 0 else None
    )
    reasons = []
    if verify.returncode != 0:
        reasons.append(
            f"{label}: git commit-graph verify exited {verify.returncode}: "
            f"{first_line}"
        )
    return reasons, {
        "present": True,
        "valid": verify.returncode == 0,
        "paths": paths,
        "verify_returncode": verify.returncode,
        "verify_stderr_first_line": first_line,
    }


@dataclass
class _GitClosureState:
    repository: Path
    label: str
    reasons: list[str]
    refs: list[str]
    git_dir: Path
    commit_graph: dict[str, Any]
    metadata: list[dict[str, Any]]


@dataclass
class _GitFsckPair:
    order: int
    state: _GitClosureState
    future: Future[subprocess.CompletedProcess[bytes]]
    fsck_reasons: list[str] | None = None
    failure: Exception | None = None


def _prepare_one_git_closure(
    snapshot: Path,
    repository: Path,
    expected_refs: list[str],
) -> _GitClosureState:
    reasons: list[str] = []
    refs = _git(repository, "for-each-ref", "--format=%(refname)").decode().splitlines()
    label = "." if repository == snapshot else repository.relative_to(snapshot).as_posix()
    if refs != expected_refs:
        reasons.append(f"{label}: git ref closure mismatch: {refs}")
    if _git(repository, "remote").decode().splitlines():
        reasons.append(f"{label}: git remote closure is not empty")
    git_dir = _git_dir(repository)
    try:
        git_dir.relative_to(snapshot)
    except ValueError:
        reasons.append(f"{label}: git dir escapes snapshot: {git_dir}")
    closure_paths = {
        "reflog": git_dir / "logs",
        "replace refs": git_dir / "refs" / "replace",
        "alternates": git_dir / "objects" / "info" / "alternates",
        "http alternates": git_dir / "objects" / "info" / "http-alternates",
        "grafts": git_dir / "info" / "grafts",
        "packed-refs": git_dir / "packed-refs",
        "shallow": git_dir / "shallow",
    }
    for closure_label, path in closure_paths.items():
        try:
            metadata = path.stat()
        except FileNotFoundError:
            continue
        except OSError as exc:
            raise ValidationError(
                f"git closure path inspection failed at {path}: "
                f"{type(exc).__name__}: {exc}",
                RC_SNAPSHOT,
            ) from exc
        if stat.S_ISDIR(metadata.st_mode):
            if _scandir_entries(path, purpose="git closure"):
                reasons.append(f"{label}: {closure_label} closure is not empty")
        elif metadata.st_size:
            reasons.append(f"{label}: {closure_label} closure is not empty")
    pseudo_refs: list[str] = []
    for entry in _scandir_entries(git_dir, purpose="git pseudo-ref"):
        path = Path(entry.path)
        try:
            metadata = entry.stat(follow_symlinks=True)
        except FileNotFoundError:
            # Preserve Path.is_file() semantics for broken symlinks.
            continue
        except OSError as exc:
            raise ValidationError(
                f"git pseudo-ref entry inspection failed at {path}: "
                f"{type(exc).__name__}: {exc}",
                RC_SNAPSHOT,
            ) from exc
        if stat.S_ISREG(metadata.st_mode) and (
            entry.name.endswith("_HEAD")
            or entry.name
            in {"MERGE_HEAD", "BISECT_HEAD", "REVERT_HEAD", "CHERRY_PICK_HEAD"}
        ):
            pseudo_refs.append(entry.name)
    pseudo_refs.sort()
    if pseudo_refs:
        reasons.append(f"{label}: pseudo refs are present: {pseudo_refs}")
    metadata = _metadata_manifest(git_dir)
    commit_graph_reasons, commit_graph = _commit_graph_manifest(
        repository, label, metadata
    )
    reasons.extend(commit_graph_reasons)
    return _GitClosureState(
        repository=repository,
        label=label,
        reasons=reasons,
        refs=refs,
        git_dir=git_dir,
        commit_graph=commit_graph,
        metadata=metadata,
    )


def _finish_one_git_closure(
    snapshot: Path,
    state: _GitClosureState,
    fsck_reasons: Sequence[str],
) -> tuple[list[str], dict[str, Any]]:
    reasons = [*state.reasons, *fsck_reasons]
    return reasons, {
        "repository": state.label,
        "git_dir": state.git_dir.relative_to(snapshot).as_posix()
        if snapshot == state.git_dir or snapshot in state.git_dir.parents
        else os.fspath(state.git_dir),
        "head": _git(state.repository, "rev-parse", "HEAD").decode().strip(),
        "refs": state.refs,
        "commit_graph": state.commit_graph,
        "metadata": state.metadata,
    }


def _one_git_closure_reasons(
    snapshot: Path,
    repository: Path,
    expected_refs: list[str],
) -> tuple[list[str], dict[str, Any]]:
    """Synchronous compatibility wrapper for one repository closure."""
    state = _prepare_one_git_closure(snapshot, repository, expected_refs)
    fsck = _run(
        ("git", "fsck", "--unreachable", "--no-reflogs"),
        cwd=repository,
        check=False,
    )
    return _finish_one_git_closure(
        snapshot, state, _git_fsck_reasons(state.label, fsck)
    )


def _git_fsck_failure_reason(
    state: _GitClosureState, exc: Exception, *, phase: str
) -> str:
    return (
        f"{state.label}: git fsck {phase} failed for {state.repository}: "
        f"{type(exc).__name__}: {exc}"
    )


def _parallel_git_closure_reasons(
    snapshot: Path,
    work: Sequence[tuple[Path, list[str]]],
) -> tuple[list[str], list[dict[str, Any]]]:
    states = [
        _prepare_one_git_closure(snapshot, repository, expected_refs)
        for repository, expected_refs in work
    ]
    pairs: list[_GitFsckPair] = []
    submit_failure: tuple[int, _GitClosureState, Exception] | None = None
    try:
        with ThreadPoolExecutor(
            max_workers=min(_GIT_FSCK_MAX_WORKERS, len(states))
        ) as executor:
            for order, state in enumerate(states):
                try:
                    future = executor.submit(
                        _run,
                        ("git", "fsck", "--unreachable", "--no-reflogs"),
                        cwd=state.repository,
                        check=False,
                    )
                except Exception as exc:
                    submit_failure = (order, state, exc)
                    break
                pairs.append(_GitFsckPair(order, state, future))

            for pair in pairs:
                try:
                    completed = pair.future.result()
                except Exception as exc:
                    pair.failure = exc
                else:
                    pair.fsck_reasons = _git_fsck_reasons(
                        pair.state.label, completed
                    )
    except Exception as exc:
        raise ValidationError(
            f"git fsck executor failed for {snapshot}: "
            f"{type(exc).__name__}: {exc}",
            RC_SNAPSHOT,
        ) from exc

    failures = [
        (pair.order, pair.state, pair.failure, "worker")
        for pair in pairs
        if pair.failure is not None
    ]
    if submit_failure is not None:
        order, state, failure = submit_failure
        failures.append((order, state, failure, "submit"))
    if failures:
        failures.sort(key=lambda row: row[0])
        diagnostic_reasons: list[str] = []
        for pair in pairs:
            diagnostic_reasons.extend(pair.state.reasons)
            if pair.fsck_reasons is not None:
                diagnostic_reasons.extend(pair.fsck_reasons)
        for _, failed_state, failure, phase in failures:
            if failure is None:
                raise ValidationError(
                    f"{failed_state.label}: git fsck {phase} failure is missing "
                    f"for {failed_state.repository}",
                    RC_SNAPSHOT,
                )
            diagnostic_reasons.append(
                _git_fsck_failure_reason(failed_state, failure, phase=phase)
            )
        diagnostic_reasons.extend(
            reason
            for state in states[len(pairs) :]
            for reason in state.reasons
        )
        first_failure = failures[0][2]
        if first_failure is None:
            raise ValidationError(diagnostic_reasons, RC_SNAPSHOT)
        raise ValidationError(
            diagnostic_reasons, RC_SNAPSHOT
        ) from first_failure

    reasons: list[str] = []
    manifests: list[dict[str, Any]] = []
    for pair in pairs:
        if pair.fsck_reasons is None:
            raise ValidationError(
                f"{pair.state.label}: git fsck result was not collected for "
                f"{pair.state.repository}",
                RC_SNAPSHOT,
            )
        repository_reasons, manifest = _finish_one_git_closure(
            snapshot, pair.state, pair.fsck_reasons
        )
        reasons.extend(repository_reasons)
        manifests.append(manifest)
    return reasons, manifests


def _git_closure_reasons(
    snapshot: Path,
    untracked: Iterable[str],
    *,
    inventory: tuple[list[Path], list[dict[str, str]]] | None = None,
    preflight_cache: dict[Path, tuple[str, ...]] | None = None,
    filesystem_observation: _SnapshotFilesystemFiles | None = None,
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, str]]]:
    if inventory is None:
        initialized, submodules = _submodule_inventory(snapshot)
    else:
        initialized, submodules = inventory
    work = [(snapshot, [f"refs/heads/{BRANCH}"])]
    for repository in initialized:
        if preflight_cache is not None and preflight_cache.get(repository):
            continue
        work.append((repository, []))
    if len(work) == 1:
        reasons, root_manifest = _one_git_closure_reasons(
            snapshot, snapshot, [f"refs/heads/{BRANCH}"]
        )
        manifests = [root_manifest]
    else:
        reasons, manifests = _parallel_git_closure_reasons(snapshot, work)
    reasons.extend(
        _submodule_content_identity_reasons(
            snapshot,
            initialized,
            preflight_cache=preflight_cache,
        )
    )
    for forbidden in (INTEGRATED_COMMIT, ARTIFACT_COMMIT):
        probe = _run(("git", "cat-file", "-e", forbidden), cwd=snapshot, check=False)
        if probe.returncode == 0:
            reasons.append(f"forbidden git object is reachable: {forbidden}")
    for focus in ("focus1.md", "focus2.md"):
        relative = f"{ARTIFACT_DIR}/{focus}"
        history = _git(snapshot, "log", "--all", "--format=%H", "--", relative)
        if history.strip():
            reasons.append(f"focus history is reachable: {relative}")
    for relative in untracked:
        path = snapshot / relative
        if not path.is_file():
            continue
        object_id = _git(snapshot, "hash-object", "--no-filters", "--", relative).decode().strip()
        probe = _run(("git", "cat-file", "-e", object_id), cwd=snapshot, check=False)
        if probe.returncode == 0:
            reasons.append(f"untracked artifact entered git object store: {relative}")
    preflight_failed = bool(
        preflight_cache is not None
        and any(preflight_cache.get(repository) for repository in initialized)
    )
    if not preflight_failed:
        actual_files = (
            filesystem_observation.read(snapshot)
            if filesystem_observation is not None
            else _filesystem_file_set(snapshot)
        )
        expected_files = _expected_filesystem_files(
            snapshot, untracked, initialized
        )
        extra = sorted(actual_files - expected_files)
        missing = sorted(expected_files - actual_files)
        if extra:
            reasons.append(f"filesystem allowlist has extra files: {extra}")
        if missing:
            reasons.append(f"filesystem allowlist has missing files: {missing}")
    return reasons, manifests, submodules


def _resolve_snapshot_destination(repo: Path, snapshot: Path) -> tuple[Path, Path]:
    repo = repo.resolve()
    snapshot = snapshot.resolve()
    if snapshot.exists():
        raise ValidationError(f"snapshot already exists: {snapshot}", RC_SNAPSHOT)
    if snapshot == repo or repo in snapshot.parents:
        raise ValidationError(
            "snapshot must be outside the source repository", RC_SNAPSHOT
        )
    return repo, snapshot


def _manifest_tasks(manifest: Mapping[str, Any]) -> Mapping[str, Any]:
    if not isinstance(manifest, Mapping):
        raise ValidationError("task manifest is not an object", RC_ROUTING)
    tasks = manifest.get("tasks")
    if not isinstance(tasks, Mapping) or not tasks:
        raise ValidationError("task manifest.tasks is required", RC_ROUTING)
    return tasks


def _task_ids_for_alias(
    alias: str, manifest: Mapping[str, Any]
) -> set[str]:
    matches: set[str] = set()
    for key, raw_task in _manifest_tasks(manifest).items():
        if not isinstance(key, str) or not isinstance(raw_task, Mapping):
            continue
        aliases = (
            key,
            raw_task.get("benchmark_task_id"),
            raw_task.get("legacy_case"),
        )
        if any(isinstance(candidate, str) and candidate == alias for candidate in aliases):
            matches.add(key)
    return matches


def resolve_benchmark_task_id(
    benchmark_task_id: str | None = None,
    *,
    case: str | None = None,
    legacy_case: str | None = None,
    manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> str:
    """Resolve the canonical benchmark identifier and reject alias conflicts."""
    supplied = (
        ("benchmark_task_id", benchmark_task_id),
        ("case", case),
        ("legacy_case", legacy_case),
    )
    candidates: set[str] | None = None
    supplied_names: list[str] = []
    for name, value in supplied:
        if value is None:
            continue
        supplied_names.append(name)
        if not isinstance(value, str) or not value:
            raise ValidationError(f"{name} must be a non-empty string", RC_ROUTING)
        matches = _task_ids_for_alias(value, manifest)
        if not matches:
            raise ValidationError(f"unknown benchmark task alias: {value}", RC_ROUTING)
        candidates = matches if candidates is None else candidates & matches
    if not supplied_names:
        raise ValidationError(
            "benchmark_task_id or legacy case alias is required", RC_ROUTING
        )
    if not candidates:
        raise ValidationError(
            "benchmark_task_id and legacy case aliases conflict", RC_ROUTING
        )
    if len(candidates) != 1:
        raise ValidationError(
            "benchmark task alias is ambiguous", RC_ROUTING
        )
    task_id = next(iter(candidates))
    task = _manifest_tasks(manifest)[task_id]
    if not isinstance(task, Mapping):
        raise ValidationError(f"manifest task is not an object: {task_id}", RC_ROUTING)
    if task.get("benchmark_task_id") != task_id:
        raise ValidationError(
            f"manifest task key does not match benchmark_task_id: {task_id}",
            RC_ROUTING,
        )
    return task_id


def _manifest_task(
    benchmark_task_id: str | None = None,
    *,
    case: str | None = None,
    legacy_case: str | None = None,
    manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> Mapping[str, Any]:
    task_id = resolve_benchmark_task_id(
        benchmark_task_id,
        case=case,
        legacy_case=legacy_case,
        manifest=manifest,
    )
    task = _manifest_tasks(manifest)[task_id]
    if not isinstance(task, Mapping):
        raise ValidationError(f"manifest task is not an object: {task_id}", RC_ROUTING)
    if not isinstance(task.get("legacy_case"), str) or not task["legacy_case"]:
        raise ValidationError(
            f"manifest task legacy_case is invalid: {task_id}", RC_ROUTING
        )
    return task


_resolve_benchmark_task_id = resolve_benchmark_task_id


def _validate_task_manifest(
    manifest: Mapping[str, Any] = TASK_MANIFEST,
    *,
    profile: str | None = None,
) -> None:
    """Validate the v3 manifest envelope without validating live artifacts."""
    if not isinstance(manifest, Mapping):
        raise ValidationError("task manifest is not an object", RC_ROUTING)
    schema_version = manifest.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version != TASK_MANIFEST_SCHEMA_VERSION
    ):
        raise ValidationError("task manifest schema_version must be 3", RC_ROUTING)
    manifest_kind = manifest.get("manifest_kind")
    if profile is not None and profile != WIRING_SLICE_PROFILE:
        raise ValidationError("task manifest profile mismatch", RC_ROUTING)
    if profile == WIRING_SLICE_PROFILE:
        if manifest_kind != _WIRING_SLICE_MANIFEST_KIND:
            raise ValidationError(
                "task manifest kind downgrade from oracle wiring slice",
                RC_ROUTING,
            )
        try:
            WIRING_SLICE.validate_wiring_slice(manifest)
        except WIRING_SLICE.WiringSliceError as exc:
            raise ValidationError(str(exc), RC_ROUTING) from exc
        return
    if manifest_kind != "t181-task-manifest":
        raise ValidationError("task manifest kind mismatch", RC_ROUTING)
    tasks = _manifest_tasks(manifest)
    for key, task in tasks.items():
        if not isinstance(key, str) or not isinstance(task, Mapping):
            raise ValidationError("task manifest task row is malformed", RC_ROUTING)
        required = (
            "benchmark_task_id",
            "legacy_case",
            "task_type",
            "stage",
            "oracle_kind",
            "provenance",
            "snapshot",
            "known_finding_ids",
        )
        missing = [field for field in required if field not in task]
        if missing:
            raise ValidationError(
                f"task manifest task {key} missing fields: {missing}", RC_ROUTING
            )
        if task["benchmark_task_id"] != key:
            raise ValidationError(
                f"task manifest task key mismatch: {key}", RC_ROUTING
            )
        if not isinstance(task["legacy_case"], str) or not task["legacy_case"]:
            raise ValidationError(
                f"task manifest legacy_case is invalid: {key}", RC_ROUTING
            )
        if key in {"POS", "NEG"} and task["legacy_case"] != key:
            raise ValidationError(
                f"frozen task legacy_case mismatch: {key}", RC_ROUTING
            )
        if not isinstance(task["provenance"], Mapping):
            raise ValidationError(
                f"task manifest provenance is invalid: {key}", RC_ROUTING
            )
        if not isinstance(task["snapshot"], Mapping):
            raise ValidationError(
                f"task manifest snapshot is invalid: {key}", RC_ROUTING
            )
        finding_ids = task["known_finding_ids"]
        if not isinstance(finding_ids, (list, tuple, set, frozenset)) or not all(
            isinstance(value, str) and value for value in finding_ids
        ):
            raise ValidationError(
                f"task manifest known_finding_ids is invalid: {key}", RC_ROUTING
            )
    shared = manifest.get("shared_provenance")
    if not isinstance(shared, Mapping):
        raise ValidationError(
            "task manifest shared_provenance is required", RC_ROUTING
        )
    auxiliary = shared.get("auxiliary_sessions")
    if not isinstance(auxiliary, Mapping):
        raise ValidationError(
            "task manifest auxiliary_sessions is required", RC_ROUTING
        )
    for role in ("fix1", "fix2", "author"):
        row = auxiliary.get(role)
        if (
            not isinstance(row, Mapping)
            or "session_id" not in row
            or "rollout_sha256" not in row
        ):
            raise ValidationError(
                f"auxiliary session provenance is incomplete: {role}", RC_ROUTING
            )


def _validate_materialized_task_manifest(
    manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> None:
    """Validate an in-memory manifest after its transport boundary was checked."""
    profile = (
        WIRING_SLICE_PROFILE
        if isinstance(manifest, Mapping)
        and manifest.get("manifest_kind") == _WIRING_SLICE_MANIFEST_KIND
        else None
    )
    _validate_task_manifest(manifest, profile=profile)


validate_task_manifest = _validate_task_manifest


def _read_profile_manifest_bytes(path: Path) -> bytes:
    flags = os.O_RDONLY | os.O_CLOEXEC | os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValidationError(
            f"cannot read profiled task manifest {path}: unsafe or unavailable",
            RC_ROUTING,
        ) from exc
    try:
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode):
            raise ValidationError(
                "profiled task manifest must be a non-symlink regular file",
                RC_ROUTING,
            )
        with os.fdopen(os.dup(descriptor), "rb") as stream:
            raw = stream.read()
        after = os.fstat(descriptor)
        if _file_identity(before) != _file_identity(after):
            raise ValidationError(
                "profiled task manifest changed while reading",
                RC_ROUTING,
            )
        return raw
    finally:
        os.close(descriptor)


def _load_task_manifest(
    path: Path, *, profile: str | None = None,
) -> dict[str, Any]:
    """Load one strict UTF-8 JSON task-manifest envelope."""
    if profile is not None and profile != WIRING_SLICE_PROFILE:
        raise ValidationError("task manifest profile mismatch", RC_ROUTING)
    if profile == WIRING_SLICE_PROFILE:
        raw = _read_profile_manifest_bytes(path)
    else:
        try:
            raw = path.read_bytes()
        except OSError as exc:
            raise ValidationError(
                f"cannot read task manifest {path}: {exc}", RC_ROUTING
            ) from exc
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ValidationError(
            f"task manifest is not strict UTF-8: {exc}", RC_ROUTING
        ) from exc

    def object_from_pairs(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError(f"duplicate JSON key: {key}")
            value[key] = item
        return value

    def reject_constant(value: str) -> None:
        raise ValueError(f"non-finite JSON number: {value}")

    try:
        value = json.loads(
            text,
            object_pairs_hook=object_from_pairs,
            parse_constant=reject_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValidationError(
            f"task manifest JSON is invalid: {exc}", RC_ROUTING
        ) from exc
    if not isinstance(value, dict):
        raise ValidationError("task manifest is not an object", RC_ROUTING)
    _validate_task_manifest(value, profile=profile)
    if (
        profile == WIRING_SLICE_PROFILE
        and raw != _canonical_bytes(value)
    ):
        raise ValidationError(
            "oracle wiring slice bytes must be sorted compact UTF-8 "
            "with exactly one LF",
            RC_ROUTING,
        )
    if (
        profile == WIRING_SLICE_PROFILE
        and hashlib.sha256(raw).hexdigest()
        != _WIRING_SLICE_MANIFEST_RAW_SHA256
    ):
        raise ValidationError(
            "oracle wiring slice raw SHA-256 pin mismatch",
            RC_ROUTING,
        )
    return value


def _require_task_manifest_command(
    task_manifest: Mapping[str, Any], command: str, *, profile: str | None = None,
) -> None:
    if (
        profile == WIRING_SLICE_PROFILE
        and command not in WIRING_SLICE.SUPPORTED_COMMANDS
    ):
        raise ValidationError(
            f"oracle wiring slice command is not allowed: {command}",
            RC_ROUTING,
        )


def _with_wiring_slice_status(
    result: Mapping[str, Any],
    task_manifest: Mapping[str, Any] | None = None,
    *,
    profile: str | None = None,
) -> dict[str, Any]:
    output = dict(result)
    is_wiring_slice = profile == WIRING_SLICE_PROFILE or (
        task_manifest is not None
        and task_manifest.get("manifest_kind") == _WIRING_SLICE_MANIFEST_KIND
    )
    if is_wiring_slice:
        output.update(
            {
                "task_acceptance_status": "unbound",
                "fix_gate_eligible": False,
                "routing_evidence_eligible": False,
                "routing_evidence_status": "inconclusive",
            }
        )
        if output.get("valid") is False:
            output["experiment_complete"] = False
            output["decision"] = None
    return output


def _task_manifest_sha256(
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> str:
    _validate_materialized_task_manifest(task_manifest)
    try:
        canonical = _canonical_bytes(task_manifest)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            f"task manifest is not canonical JSON: {exc}", RC_ROUTING
        ) from exc
    return _sha256(canonical)


def _require_task_manifest_sha256(
    artifact: Mapping[str, Any],
    task_manifest: Mapping[str, Any],
    label: str,
    *,
    rc: int,
) -> str:
    expected = _task_manifest_sha256(task_manifest)
    actual = artifact.get("task_manifest_sha256")
    if actual is None:
        raise ValidationError(
            f"{label} task_manifest_sha256 mismatch: artifact predates "
            "task-manifest digest binding and must be regenerated",
            rc,
        )
    if actual != expected:
        raise ValidationError(
            f"{label} task_manifest_sha256 mismatch", rc
        )
    return expected


def _validate_cache_condition(normalized: dict[str, Any], schema_version: int) -> None:
    field = "cache_condition"
    if field not in normalized:
        if schema_version == LEGACY_SCHEMA_VERSION:
            normalized[field] = None
        else:
            raise ValidationError(
                f"schedule slot missing required field: {field}", RC_ROUTING
            )
    value = normalized[field]
    if value is not None and not isinstance(value, str):
        raise ValidationError(
            f"schedule slot {field} must be a string or null", RC_ROUTING
        )
    if value == "":
        raise ValidationError(
            f"schedule slot {field} must be non-empty when present", RC_ROUTING
        )
    if value is not None:
        raise ValidationError(
            f"schedule slot {field} non-null values are not supported without attestation",
            RC_ROUTING,
        )


def _validate_price_version(
    normalized: dict[str, Any],
    schema_version: int,
    expected_price_version: str | None,
) -> None:
    field = "price_version"
    if field not in normalized:
        if schema_version == LEGACY_SCHEMA_VERSION:
            normalized[field] = None
        else:
            raise ValidationError(
                f"schedule slot missing required field: {field}", RC_ROUTING
            )
    value = normalized[field]
    if value is not None and not isinstance(value, str):
        raise ValidationError(
            f"schedule slot {field} must be a string or null", RC_ROUTING
        )
    if value == "":
        raise ValidationError(
            f"schedule slot {field} must be non-empty when present", RC_ROUTING
        )
    if value is None:
        return
    if expected_price_version is None:
        raise ValidationError(
            f"schedule slot {field} non-null values are not supported without attestation",
            RC_ROUTING,
        )
    if (
        schema_version != SCHEDULE_SCHEMA_VERSION
        or expected_price_version != FROZEN_PRICE_VERSION
        or value != expected_price_version
        or value != FROZEN_PRICE_VERSION
    ):
        raise ValidationError(
            "schedule slot price_version does not match the frozen price binding",
            RC_ROUTING,
        )


def validate_nullable_dimensions(
    slot: Mapping[str, Any],
    *,
    schema_version: int = TASK_MANIFEST_SCHEMA_VERSION,
    expected_price_version: str | None = None,
) -> dict[str, Any]:
    """Validate nullable dimensions and return a non-mutating normalized row.

    v3 requires both keys to be present.  A v2 row may omit them and receives
    explicit nulls only in the normalized copy.  Cache remains null-only;
    price accepts only the caller-provided, repository-frozen v3 binding.

    The live _validate_schedule path uses this helper through the schedule
    normalizer before supervisor or replay consumers receive a slot.
    """
    if not isinstance(slot, Mapping):
        raise ValidationError("schedule slot is not an object", RC_ROUTING)
    if schema_version not in (LEGACY_SCHEMA_VERSION, TASK_MANIFEST_SCHEMA_VERSION):
        raise ValidationError(
            f"unsupported schedule schema_version: {schema_version}", RC_ROUTING
        )
    normalized = dict(slot)
    _validate_cache_condition(normalized, schema_version)
    _validate_price_version(
        normalized, schema_version, expected_price_version
    )
    return normalized


_validate_nullable_dimensions = validate_nullable_dimensions


def _normalize_schedule_slot(
    slot: Mapping[str, Any],
    *,
    schema_version: int,
    manifest: Mapping[str, Any],
    expected_price_version: str | None = None,
) -> dict[str, Any]:
    if not isinstance(slot, Mapping):
        raise ValidationError("schedule slot is not an object", RC_ROUTING)
    normalized = dict(slot)
    task_id = resolve_benchmark_task_id(
        normalized.get("benchmark_task_id"),
        case=normalized.get("case"),
        legacy_case=normalized.get("legacy_case"),
        manifest=manifest,
    )
    task = _manifest_task(task_id, manifest=manifest)
    normalized["benchmark_task_id"] = task_id
    normalized.setdefault("legacy_case", task["legacy_case"])
    if normalized.get("legacy_case") != task["legacy_case"]:
        raise ValidationError(
            "schedule legacy_case does not match benchmark task", RC_ROUTING
        )
    normalized.setdefault("case", task["legacy_case"])
    return validate_nullable_dimensions(
        normalized,
        schema_version=schema_version,
        expected_price_version=expected_price_version,
    )


def normalize_legacy_schedule(
    schedule: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] = TASK_MANIFEST,
    expected_price_version: str | None = None,
) -> dict[str, Any]:
    """Convert a v2 schedule to a v3 view without changing its source bytes.

    The live _validate_schedule path calls this compatibility normalizer before
    supervisor or replay consumers receive a slot.
    """
    _validate_materialized_task_manifest(manifest)
    if (
        not isinstance(schedule, Mapping)
        or schedule.get("schema_version") != LEGACY_SCHEMA_VERSION
    ):
        raise ValidationError("legacy schedule schema_version must be 2", RC_ROUTING)
    slots = schedule.get("slots")
    if not isinstance(slots, list):
        raise ValidationError("legacy schedule.slots is not an array", RC_ROUTING)
    normalized = dict(schedule)
    normalized["schema_version"] = TASK_MANIFEST_SCHEMA_VERSION
    normalized["manifest_kind"] = "t181-task-manifest"
    normalized["slots"] = [
        _normalize_schedule_slot(
            row,
            schema_version=LEGACY_SCHEMA_VERSION,
            manifest=manifest,
            expected_price_version=expected_price_version,
        )
        for row in slots
    ]
    return normalized


def normalize_schedule(
    schedule: Mapping[str, Any],
    *,
    manifest: Mapping[str, Any] = TASK_MANIFEST,
    expected_price_version: str | None = None,
) -> dict[str, Any]:
    """Return the canonical v3 schedule view, dispatching v2 explicitly.

    The live _validate_schedule path calls this normalizer before supervisor or
    replay consumers receive a slot.
    """
    _validate_materialized_task_manifest(manifest)
    if not isinstance(schedule, Mapping):
        raise ValidationError("schedule is not an object", RC_ROUTING)
    version = schedule.get("schema_version")
    if version == LEGACY_SCHEMA_VERSION:
        return normalize_legacy_schedule(
            schedule,
            manifest=manifest,
            expected_price_version=expected_price_version,
        )
    if version != TASK_MANIFEST_SCHEMA_VERSION:
        raise ValidationError(
            f"unsupported schedule schema_version: {version}", RC_ROUTING
        )
    slots = schedule.get("slots")
    if not isinstance(slots, list):
        raise ValidationError("schedule.slots is not an array", RC_ROUTING)
    normalized = dict(schedule)
    normalized["slots"] = [
        _normalize_schedule_slot(
            row,
            schema_version=TASK_MANIFEST_SCHEMA_VERSION,
            manifest=manifest,
            expected_price_version=expected_price_version,
        )
        for row in slots
    ]
    return normalized


_normalize_legacy_schedule = normalize_legacy_schedule
_normalize_schedule = normalize_schedule


def expected_schedule_from_manifest(
    manifest: Mapping[str, Any] = TASK_MANIFEST,
    schedule: Mapping[str, Any] | Sequence[Mapping[str, Any]] | None = None,
    *,
    expected_price_version: str | None = None,
) -> dict[tuple[str, str], int]:
    """Derive task/arm counts from a schedule, retaining v2 counts as a gate."""
    source: Mapping[str, Any]
    if schedule is None:
        candidate = manifest.get("schedule")
        if isinstance(candidate, Mapping):
            source = candidate
        else:
            candidate = manifest.get("slots")
            if isinstance(candidate, list):
                source = {
                    "schema_version": TASK_MANIFEST_SCHEMA_VERSION,
                    "slots": candidate,
                }
            else:
                return {}
    elif isinstance(schedule, Mapping):
        source = schedule
    else:
        source = {
            "schema_version": TASK_MANIFEST_SCHEMA_VERSION,
            "slots": list(schedule),
        }
    if source.get("schema_version") == LEGACY_SCHEMA_VERSION:
        normalize_legacy_schedule(
            source,
            manifest=manifest,
            expected_price_version=expected_price_version,
        )
        return dict(LEGACY_EXPECTED_SCHEDULE)
    normalized = normalize_schedule(
        source,
        manifest=manifest,
        expected_price_version=expected_price_version,
    )
    counts: dict[tuple[str, str], int] = {}
    for row in normalized["slots"]:
        arm = row.get("arm")
        if not isinstance(arm, str) or not arm:
            raise ValidationError(
                "schedule slot arm must be a non-empty string", RC_ROUTING
            )
        key = (row["benchmark_task_id"], arm)
        counts[key] = counts.get(key, 0) + 1
    return counts


_expected_schedule_from_manifest = expected_schedule_from_manifest


def known_finding_ids_for_manifest(
    manifest: Mapping[str, Any] = TASK_MANIFEST,
    *,
    benchmark_task_id: str | None = None,
    case: str | None = None,
) -> set[str]:
    tasks = _manifest_tasks(manifest)
    if benchmark_task_id is None and case is None:
        selected = tasks.values()
    else:
        selected = (
            _manifest_task(
                benchmark_task_id,
                case=case,
                manifest=manifest,
            ),
        )
    finding_ids: set[str] = set()
    for task in selected:
        if not isinstance(task, Mapping):
            raise ValidationError("task manifest task row is malformed", RC_ROUTING)
        values = task.get("known_finding_ids")
        if not isinstance(values, (list, tuple, set, frozenset)):
            raise ValidationError("known_finding_ids must be an array", RC_ROUTING)
        finding_ids.update(values)
    return finding_ids


_known_finding_ids_for_manifest = known_finding_ids_for_manifest


def _adjudication_known_finding_ids_for_task(
    task_manifest: Mapping[str, Any], benchmark_task_id: str,
) -> set[str]:
    """OR-M6 diagnostic anchor: narrow revealed verdicts to their task."""
    return known_finding_ids_for_manifest(
        task_manifest,
        benchmark_task_id=benchmark_task_id,
    )


def _aggregate_known_finding_ids_for_task(
    task_manifest: Mapping[str, Any], benchmark_task_id: str,
) -> set[str]:
    """OR-M6 correctness anchor: independently narrow aggregate inputs."""
    return known_finding_ids_for_manifest(
        task_manifest,
        benchmark_task_id=benchmark_task_id,
    )


def _prepare_snapshot_case(
    repo: Path,
    sessions_root: Path,
    case: str,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, bytes]:
    try:
        task = _manifest_task(case=case, manifest=task_manifest)
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_SNAPSHOT) from exc
    if not isinstance(task.get("snapshot"), Mapping) or not isinstance(
        task["snapshot"].get("hashes"), Mapping
    ):
        raise ValidationError(f"unknown case: {case}", RC_SNAPSHOT)
    return (
        derive_independent_golden(
            repo, sessions_root, task_manifest=task_manifest
        )
        if task["oracle_kind"] == "positive"
        else {}
    )


def _build_snapshot_base(repo: Path, base: Path) -> Path:
    repo, base = _resolve_snapshot_destination(repo, base)
    parent = _git(repo, "rev-parse", f"{INTEGRATED_COMMIT}^").decode().strip()
    parents = _git(repo, "show", "-s", "--format=%P", INTEGRATED_COMMIT).decode().split()
    if parent != BASE_COMMIT or parents != [BASE_COMMIT]:
        raise ValidationError("integrated commit parent topology mismatch", RC_SNAPSHOT)

    _run(("git", "init", "--quiet", os.fspath(base)), cwd=repo)
    pack = _git(
        repo,
        "pack-objects",
        "--revs",
        "--stdout",
        input_bytes=(BASE_COMMIT + "\n").encode("ascii"),
    )
    _git(base, "index-pack", "--stdin", "--fix-thin", input_bytes=pack)
    _git(base, "update-ref", f"refs/heads/{BRANCH}", BASE_COMMIT)
    try:
        _git(base, "checkout", "-B", BRANCH, BASE_COMMIT)
        _init_submodules_from_local_source(repo, base)
        _seal_git_object_closure(base)
        diff = _git(repo, "diff", "--binary", BASE_COMMIT, INTEGRATED_COMMIT, "--", *TRACKED_PATHS)
        _run(("git", "apply", "--whitespace=nowarn", "-"), cwd=base, input_bytes=diff)
        return base
    except Exception:
        # 作成途中の snapshot base は診断用に残す。再実行時の上書きも禁止する。
        raise


def _finish_snapshot_case(
    repo: Path,
    snapshot: Path,
    case: str,
    golden: Mapping[str, bytes],
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    try:
        task = _manifest_task(case=case, manifest=task_manifest)
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_SNAPSHOT) from exc
    legacy_case = task["legacy_case"]
    if task["oracle_kind"] == "positive":
        for path, data in golden.items():
            target = snapshot / path
            target.write_bytes(data)
            target.chmod(0o644)
    for name in task["snapshot"]["artifact_names"]:
        relative = f"{ARTIFACT_DIR}/{name}"
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_git(repo, "show", f"{ARTIFACT_COMMIT}:{relative}"))
        target.chmod(0o644)
    return verify_snapshot(
        snapshot, legacy_case, task_manifest=task_manifest
    )


def _derive_snapshot_from_base(
    repo: Path,
    base: Path,
    snapshot: Path,
    sessions_root: Path,
    case: str,
    *,
    prepared_golden: Mapping[str, bytes] | None = None,
    prepared_destination: tuple[Path, Path] | None = None,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    if prepared_destination is None:
        repo, snapshot = _resolve_snapshot_destination(repo, snapshot)
    else:
        prepared_repo, prepared_snapshot = prepared_destination
        if repo.resolve() != prepared_repo or snapshot.resolve() != prepared_snapshot:
            raise ValidationError(
                "prepared snapshot destination does not match derivation",
                RC_SNAPSHOT,
            )
        repo, snapshot = prepared_repo, prepared_snapshot
    try:
        _manifest_task(case=case, manifest=task_manifest)
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_SNAPSHOT) from exc
    golden = (
        _prepare_snapshot_case(
            repo, sessions_root, case, task_manifest=task_manifest
        )
        if prepared_golden is None
        else prepared_golden
    )
    base = base.resolve()
    if snapshot == base or base in snapshot.parents or snapshot in base.parents:
        raise ValidationError(
            "snapshot base and destination must be independent directories",
            RC_SNAPSHOT,
        )
    _preflight_snapshot_relocation(base)
    shutil.copytree(
        base,
        snapshot,
        symlinks=True,
        copy_function=shutil.copy2,
    )
    _preflight_snapshot_relocation(snapshot)
    return _finish_snapshot_case(
        repo,
        snapshot,
        case,
        golden,
        task_manifest=task_manifest,
    )


def build_snapshot(
    repo: Path,
    snapshot: Path,
    sessions_root: Path,
    case: str,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    repo, snapshot = _resolve_snapshot_destination(repo, snapshot)
    golden = _prepare_snapshot_case(
        repo, sessions_root, case, task_manifest=task_manifest
    )
    _build_snapshot_base(repo, snapshot)
    return _finish_snapshot_case(
        repo,
        snapshot,
        case,
        golden,
        task_manifest=task_manifest,
    )


def _parse_numstat(raw: bytes) -> list[list[Any]]:
    rows: list[list[Any]] = []
    for line in raw.decode("utf-8").splitlines():
        added, deleted, path = line.split("\t", 2)
        rows.append([int(added), int(deleted), path])
    return rows


def _status_sets(snapshot: Path) -> tuple[list[str], list[str]]:
    raw = _git(
        snapshot,
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
    )
    tracked: list[str] = []
    untracked: list[str] = []
    entries = raw.split(b"\0")
    index = 0
    while index < len(entries):
        entry = entries[index]
        index += 1
        if not entry:
            continue
        text = entry.decode("utf-8")
        code, path = text[:2], text[3:]
        if code == "??":
            untracked.append(path)
        else:
            tracked.append(path)
        if code[0] in "RC" or code[1] in "RC":
            index += 1
    return sorted(tracked), sorted(untracked)


def verify_snapshot(
    snapshot: Path,
    case: str,
    *,
    spec: Mapping[str, Any] | None = None,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    snapshot = snapshot.resolve()
    filesystem_observation = _SnapshotFilesystemFiles(snapshot)
    expected = dict(
        spec or _snapshot_spec(case, task_manifest=task_manifest)
    )
    reasons: list[str] = []
    inventory: tuple[list[Path], list[dict[str, str]]] | None = None
    preflight_cache: dict[Path, tuple[str, ...]] = {}
    git_dir = snapshot / ".git"
    try:
        git_metadata = git_dir.lstat()
    except OSError as exc:
        reasons.append(f"self-contained .git directory is missing: {exc}")
    else:
        if stat.S_ISLNK(git_metadata.st_mode) or not stat.S_ISDIR(
            git_metadata.st_mode
        ):
            reasons.append(".git is not a non-symlink directory")
        else:
            root_preflight_reasons = _cached_repository_preflight_reasons(
                snapshot, snapshot, preflight_cache
            )
            if root_preflight_reasons:
                raise ValidationError(
                    root_preflight_reasons, RC_SNAPSHOT
                )
            inventory = _submodule_inventory(
                snapshot, preflight_cache=preflight_cache
            )
    try:
        head = _git(snapshot, "rev-parse", "HEAD").decode().strip()
        branch_result = _run(
            ("git", "symbolic-ref", "--short", "HEAD"), cwd=snapshot, check=False
        )
        branch = (
            branch_result.stdout.decode().strip()
            if branch_result.returncode == 0
            else None
        )
        staged = _git(snapshot, "diff", "--cached", "--name-only").decode().splitlines()
        tracked, untracked = _status_sets(snapshot)
        numstat = _parse_numstat(_git(snapshot, "diff", "--numstat"))
    except (OSError, UnicodeDecodeError, ValidationError) as exc:
        raise ValidationError(f"snapshot git oracle failed: {exc}", RC_SNAPSHOT) from exc
    if head != expected["head"]:
        reasons.append(f"HEAD mismatch: {head} != {expected['head']}")
    if branch != expected["branch"]:
        reasons.append(f"symbolic HEAD mismatch: {branch!r} != {expected['branch']!r}")
    if staged:
        reasons.append(f"index is not empty: {staged}")
    if tracked != sorted(expected["tracked_paths"]):
        reasons.append(f"dirty set mismatch: {tracked}")
    if untracked != sorted(expected["untracked"]):
        reasons.append(f"untracked allowlist mismatch: {untracked}")
    if numstat != list(expected["numstat"]):
        reasons.append(f"numstat mismatch: {numstat}")

    file_rows: dict[str, Any] = {}
    snapshot_prefix = os.fspath(snapshot) + os.sep
    for relative, expected_hash in sorted(expected["hashes"].items()):
        path = snapshot / relative
        try:
            metadata = path.lstat()
        except OSError as exc:
            reasons.append(f"input missing: {relative}: {exc}")
            continue
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            reasons.append(f"input is not a non-symlink regular file: {relative}")
            continue
        mode = stat.S_IFMT(metadata.st_mode) | stat.S_IMODE(metadata.st_mode)
        if mode != expected["modes"][relative]:
            reasons.append(
                f"st_mode mismatch {relative}: {oct(mode)} != "
                f"{oct(expected['modes'][relative])}"
            )
        try:
            resolved = os.fspath(path.resolve(strict=True))
        except OSError as exc:
            reasons.append(f"realpath failed {relative}: {exc}")
            continue
        if not resolved.startswith(snapshot_prefix):
            reasons.append(f"realpath escapes snapshot: {relative}")
        digest = _sha256(path.read_bytes())
        if digest != expected_hash:
            reasons.append(f"sha mismatch {relative}: {digest} != {expected_hash}")
        file_rows[relative] = {"sha256": digest, "st_mode": mode}
    for relative in expected["forbidden"]:
        if (snapshot / relative).exists() or (snapshot / relative).is_symlink():
            reasons.append(f"forbidden focus artifact exists: {relative}")
    enforce_closure = expected.get("git_object_closure", True)
    git_manifests: list[dict[str, Any]] = []
    submodule_manifest: list[dict[str, str]] = []
    if enforce_closure:
        closure_reasons, git_manifests, submodule_manifest = _git_closure_reasons(
            snapshot,
            expected["untracked"],
            inventory=inventory,
            preflight_cache=preflight_cache,
            filesystem_observation=filesystem_observation,
        )
        reasons.extend(closure_reasons)
    else:
        if inventory is None:
            inventory = _submodule_inventory(snapshot)
        initialized, submodule_manifest = inventory
        reasons.extend(
            _submodule_content_identity_reasons(
                snapshot,
                initialized,
                preflight_cache=preflight_cache,
            )
        )
    submodule_manifest_sha256 = _submodule_manifest_sha256(submodule_manifest)
    for row in submodule_manifest:
        if row["initialization"] != "initialized":
            reasons.append(f"submodule is not initialized: {row['path']}")
    expected_submodule_manifest = expected.get("submodule_manifest_sha256")
    if (
        expected_submodule_manifest is not None
        and submodule_manifest_sha256 != expected_submodule_manifest
    ):
        reasons.append(
            "pinned submodule initialization or gitlink state mismatch"
        )
    if reasons:
        raise ValidationError(reasons, RC_SNAPSHOT)
    oracle = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": _task_manifest_sha256(task_manifest),
        "case": case,
        "snapshot": os.fspath(snapshot),
        "head": head,
        "branch": branch,
        "dirty": tracked,
        "untracked": untracked,
        "numstat": numstat,
        "files": file_rows,
        "submodules": submodule_manifest,
        "submodule_manifest_sha256": submodule_manifest_sha256,
        "git_object_closure": {
            "base_only": bool(enforce_closure),
            "forbidden_objects": [INTEGRATED_COMMIT, ARTIFACT_COMMIT],
            "ref": f"refs/heads/{BRANCH}",
            "repositories": git_manifests,
        },
        "filesystem_files": sorted(filesystem_observation.read(snapshot)),
    }
    oracle["manifest_sha256"] = _sha256(_canonical_bytes(oracle))
    return oracle


def extract_user_message(rollout: Path) -> str:
    rows, issues = _json_lines(rollout)
    if issues:
        raise ValidationError(issues, RC_SNAPSHOT)
    messages = [
        payload["message"]
        for row in rows
        if row.get("type") == "event_msg"
        and isinstance((payload := row.get("payload")), dict)
        and payload.get("type") == "user_message"
        and isinstance(payload.get("message"), str)
    ]
    if len(messages) != 1:
        raise ValidationError(
            f"user_message count is {len(messages)}, expected 1", RC_SNAPSHOT
        )
    return messages[0]


def _assert_arm_neutral_paths(paths: Iterable[str | os.PathLike[str]]) -> None:
    leaked: list[str] = []
    for raw in paths:
        text = os.fspath(raw)
        if re.search(r"(^|[/_.-])(max|high)(?=$|[/_.-])", text.casefold()):
            leaked.append(text)
    if leaked:
        raise ValidationError(
            f"arm value leaked into path: {sorted(leaked)}", RC_ROUTING
        )


def _assert_agent_visible_paths_neutral(
    paths: Iterable[str | os.PathLike[str]],
) -> None:
    leaked = [
        os.fspath(raw)
        for raw in paths
        if re.search(
            r"(^|[/_.-])(?:max|high|arm|slots?|blocks?|attempts?)"
            r"(?=$|[/_.-])",
            os.fspath(raw).casefold(),
        )
    ]
    if leaked:
        raise ValidationError(
            f"schedule metadata leaked into agent-visible path: {sorted(leaked)}",
            RC_ROUTING,
        )


def render_prompt(
    sessions_root: Path,
    case: str,
    new_root: Path,
    *,
    verify_source: bool = True,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
    snapshot_oracle: Mapping[str, Any] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    try:
        task = _manifest_task(case=case, manifest=task_manifest)
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_SNAPSHOT) from exc
    legacy_case = task["legacy_case"]
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    if snapshot_oracle is None:
        if task_manifest_sha256 != _task_manifest_sha256(TASK_MANIFEST):
            raise ValidationError(
                "external task manifest prompt requires a snapshot oracle binding",
                RC_SNAPSHOT,
            )
    else:
        _require_task_manifest_sha256(
            snapshot_oracle,
            task_manifest,
            "prompt snapshot oracle",
            rc=RC_SNAPSHOT,
        )
        if snapshot_oracle.get("case") != legacy_case:
            raise ValidationError(
                "prompt snapshot oracle case mismatch", RC_SNAPSHOT
            )
    provenance = task["provenance"]
    pin = provenance["prompt_source"]
    rollout = _find_rollout(
        sessions_root,
        provenance["session_id"],
        pinned_label=legacy_case,
        pinned_sha256=provenance["rollout_sha256"],
    )
    if verify_source:
        _verify_rollout_sha(
            rollout,
            legacy_case,
            expected_sha256=provenance["rollout_sha256"],
        )
    message = extract_user_message(rollout)
    source = message.encode("utf-8")
    reasons: list[str] = []
    if verify_source:
        if _sha256(source) != pin["sha256"]:
            reasons.append("source prompt sha mismatch")
        if len(message) != pin["chars"] or len(source) != pin["bytes"]:
            reasons.append("source prompt size mismatch")
        if message.endswith(("\n", "\r")):
            reasons.append("source prompt unexpectedly ends in newline")
    new = os.fspath(new_root.resolve())
    _assert_arm_neutral_paths([new])
    count = message.count(OLD_ROOT)
    if verify_source and count != pin["replacements"]:
        reasons.append(f"replacement count mismatch: {count} != {pin['replacements']}")
    rendered = message.replace(OLD_ROOT, new)
    sentinel = "\0T181_ROOT\0"
    if message.replace(OLD_ROOT, sentinel) != rendered.replace(new, sentinel):
        reasons.append("path-neutral prompt identity mismatch")
    if OLD_ROOT in rendered:
        reasons.append("old root remains after rendering")
    rooted_paths = {
        match.rstrip(".,:;)]}")
        for match in re.findall(re.escape(new) + r"/[^\s'\"`)>]+", rendered)
    }
    requested_untracked = {
        os.path.relpath(path, new)
        for path in rooted_paths
        if os.path.relpath(path, new).startswith(ARTIFACT_DIR + os.sep)
    }
    expected_untracked = {
        f"{ARTIFACT_DIR}/{name}"
        for name in task["snapshot"]["artifact_names"]
    }
    if requested_untracked != expected_untracked:
        reasons.append(
            "prompt/snapshot untracked path set mismatch: "
            f"{sorted(requested_untracked)} != {sorted(expected_untracked)}"
        )
    if reasons:
        raise ValidationError(reasons, RC_SNAPSHOT)
    data = rendered.encode("utf-8")
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "case": legacy_case,
        "source_session_id": provenance["session_id"],
        "source_rollout_sha256": _sha256(rollout.read_bytes()),
        "source_prompt_sha256": _sha256(source),
        "rendered_prompt_sha256": _sha256(data),
        "replacement_count": count,
        "new_root": new,
        "absolute_paths": sorted(rooted_paths),
        "untracked_paths": sorted(requested_untracked),
    }
    if snapshot_oracle is not None:
        receipt["snapshot_manifest_sha256"] = _sha256(
            _canonical_bytes(snapshot_oracle)
        )
    return data, receipt


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


ENV_ALLOWLIST = {
    "CODEX_HOME",
    "HOME",
    "LANG",
    "LC_ALL",
    "PATH",
    "TERM",
    "TZ",
}
PACKET_MTIME_NS = 946684800_000_000_000
MAX_SCHEDULE_GAP_MS = 60_000
# A live inter-block snapshot-oracle/pre-launch cycle took 350,980 ms.
# 900,000 ms leaves about 2.56x headroom without weakening the 60 s arm-pair gate.
MAX_INTER_BLOCK_GAP_MS = 900_000


def _is_intra_block_arm_transition(
    previous: Mapping[str, Any], current: Mapping[str, Any]
) -> bool:
    return (
        previous.get("block_id") == current.get("block_id")
        and previous.get("attempt") == current.get("attempt")
        and previous.get("block_order") == 1
        and current.get("block_order") == 2
    )


def _clean_environment(
    additions: Mapping[str, str] | None = None,
) -> dict[str, str]:
    """Build the only environment inherited by Git, bwrap, and Codex."""
    environment = {
        key: value
        for key in ENV_ALLOWLIST
        if isinstance((value := os.environ.get(key)), str)
    }
    environment.update(additions or {})
    for key in tuple(environment):
        if key.startswith("GIT_") or key not in ENV_ALLOWLIST:
            environment.pop(key)
    return environment


def _read_json_value(path: Path) -> Any:
    try:
        return json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"cannot read JSON {path}: {exc}", RC_RECEIPT) from exc


def _write_frozen_json(path: Path, value: Any, *, rc: int = RC_RECEIPT) -> None:
    if path.exists() or path.is_symlink():
        raise ValidationError(f"frozen artifact already exists: {path}", rc)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(_canonical_bytes(value))


def _regular_file_state(path: Path, label: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValidationError(f"{label} is not a regular file", RC_RECEIPT)
    return {
        "path": os.fspath(path.resolve()),
        "inode": metadata.st_ino,
        "size": metadata.st_size,
        "mtime_ns": metadata.st_mtime_ns,
    }


MODEL_ALLOWLIST = frozenset((MODEL, "gpt-5.6-luna"))


def _exec_argv_model(argv: Sequence[str]) -> str:
    if isinstance(argv, (str, bytes)):
        raise ValidationError("actual argv must be an array", RC_ROUTING)
    try:
        values = list(argv)
    except TypeError as exc:
        raise ValidationError("actual argv must be an array", RC_ROUTING) from exc
    if not all(isinstance(value, str) for value in values):
        raise ValidationError("actual argv contains a non-string value", RC_ROUTING)
    positions = [index for index, value in enumerate(values) if value == "-m"]
    if len(positions) != 1:
        raise ValidationError(
            "actual argv must contain one -m model option", RC_ROUTING
        )
    position = positions[0]
    if position + 1 >= len(values):
        raise ValidationError("actual argv -m model value is missing", RC_ROUTING)
    model = values[position + 1]
    if model not in MODEL_ALLOWLIST:
        raise ValidationError(
            f"actual argv model is not allowed: {model}", RC_ROUTING
        )
    model_positions = [
        index for index, value in enumerate(values) if value in MODEL_ALLOWLIST
    ]
    if model_positions != [position + 1]:
        raise ValidationError(
            "actual argv contains duplicate or misplaced model values", RC_ROUTING
        )
    return model


def _normalized_exec_argv(
    argv: Sequence[str],
    requested_model: str | None,
    effort: str | None = None,
) -> list[str]:
    # Keep the two-argument form as a read-only compatibility shim for the
    # legacy receipt validator.  New callers must provide the model explicitly.
    if effort is None:
        effort = requested_model
        requested_model = None
    actual_model = _exec_argv_model(argv)
    if requested_model is None:
        requested_model = actual_model
    if not isinstance(requested_model, str) or requested_model not in MODEL_ALLOWLIST:
        raise ValidationError(
            f"requested model is not allowed: {requested_model}", RC_ROUTING
        )
    if requested_model != actual_model:
        raise ValidationError(
            "requested model does not match the -m argv value", RC_ROUTING
        )
    expected = f'model_reasoning_effort="{effort}"'
    alternatives = {expected, f"model_reasoning_effort={effort}"}
    positions = [index for index, value in enumerate(argv) if value in alternatives]
    if len(positions) != 1:
        raise ValidationError(
            "actual argv must contain one model_reasoning_effort field", RC_ROUTING
        )
    position = positions[0]
    for index, value in enumerate(argv):
        if index != position and value.casefold() in {"max", "high"}:
            raise ValidationError("effort appears outside its argv field", RC_ROUTING)
    normalized = list(argv)
    normalized[position] = 'model_reasoning_effort="<EFFORT>"'
    return normalized


def _replace_identity_paths(value: Any, replacements: Mapping[str, str]) -> Any:
    if isinstance(value, str):
        rendered = value
        for old, new in sorted(replacements.items(), key=lambda item: -len(item[0])):
            rendered = rendered.replace(old, new)
        return rendered
    if isinstance(value, list):
        return [_replace_identity_paths(item, replacements) for item in value]
    if isinstance(value, dict):
        return {
            key: _replace_identity_paths(item, replacements)
            for key, item in value.items()
        }
    return value


def _launch_identity_value(receipt: Mapping[str, Any]) -> str:
    events = receipt.get("events")
    done = receipt.get("done")
    prompt = receipt.get("prompt")
    oracle = receipt.get("snapshot_oracle")
    if not all(isinstance(value, dict) for value in (events, done, prompt, oracle)):
        raise ValidationError("launch identity path state missing", RC_RECEIPT)
    requested_model = receipt.get("requested_model")
    actual_model = _exec_argv_model(receipt.get("argv", []))
    if requested_model is None:
        requested_model = actual_model
        # _supervise_one writes the launch receipt immediately after computing
        # this identity.  Populate the schema field before that frozen write;
        # loaded legacy receipts remain readable through the derived value.
        if isinstance(receipt, dict):
            receipt["requested_model"] = requested_model
    elif requested_model != actual_model:
        raise ValidationError(
            "launch receipt requested model does not match argv", RC_ROUTING
        )
    if not isinstance(requested_model, str) or requested_model not in MODEL_ALLOWLIST:
        raise ValidationError(
            f"launch receipt requested model is not allowed: {requested_model}",
            RC_ROUTING,
        )
    replacements = {
        str(receipt.get("run_dir")): "<RUN_DIR>",
        str(receipt.get("agent_workspace")): "<AGENT_WORKSPACE>",
        str(receipt.get("output_path")): "<OUTPUT>",
        str(receipt.get("stderr_path")): "<STDERR>",
        str(receipt.get("codex_home")): "<CODEX_HOME>",
        str(events.get("path")): "<EVENTS>",
        str(done.get("path")): "<DONE>",
        str(prompt.get("path")): "<PROMPT>",
        str(oracle.get("path")): "<SNAPSHOT_ORACLE>",
        f"model_reasoning_effort={receipt.get('arm')}":
            'model_reasoning_effort="<EFFORT>"',
        f'model_reasoning_effort="{receipt.get("arm")}"':
            'model_reasoning_effort="<EFFORT>"',
    }
    identity = {
        "case": receipt.get("case"),
        "requested_model": requested_model,
        "prompt_sha256": prompt.get("sha256"),
        "snapshot_oracle_sha256": oracle.get("sha256"),
        "codex_config_sha256": receipt.get("codex_config_sha256"),
        "codex_auth_sha256": receipt.get("codex_auth_sha256"),
        "cli_binary": receipt.get("cli_binary"),
        "cli_binary_sha256": receipt.get("cli_binary_sha256"),
        "cli_version": receipt.get("cli_version"),
        "bwrap_binary_sha256": receipt.get("bwrap_binary_sha256"),
        "bwrap_version": receipt.get("bwrap_version"),
        "normalized_argv": receipt.get("normalized_argv"),
        "bwrap_argv": receipt.get("bwrap_argv"),
        "actual_process_argv_normalized": receipt.get(
            "actual_process_argv_normalized"
        ),
        "environment": receipt.get("environment"),
        "sandbox": receipt.get("sandbox"),
        "world_state": receipt.get("world_state"),
        "schedule_sha256": receipt.get("schedule_sha256"),
        "dry_run": receipt.get("dry_run"),
    }
    return _sha256(
        _canonical_bytes(_replace_identity_paths(identity, replacements))
    )


def _append_jsonl(path: Path, value: Mapping[str, Any]) -> None:
    row = value if isinstance(value, dict) else dict(value)
    launch_receipt = row.get("launch_receipt")
    if row.get("phase") == "completed" and isinstance(launch_receipt, str):
        try:
            launch = _read_json_value(Path(launch_receipt))
        except ValidationError:
            launch = None
        if isinstance(launch, dict) and isinstance(
            launch.get("requested_model"), str
        ):
            row["requested_model"] = launch["requested_model"]
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, _canonical_bytes(dict(row)))
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _attempt_ledger_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows, issues = _json_lines(path)
    if issues:
        raise ValidationError(issues, RC_RECEIPT)
    return rows


def _copy_identity_file(
    source: Path,
    target: Path,
    label: str,
    *,
    mode: int = 0o600,
) -> str:
    """Copy an identity file with create-only, restrictive file creation.

    The source is read once between two lstat checks and the destination is
    created with ``O_EXCL``.  In particular, auth/config files are born as
    ``0600``; they are never briefly exposed through a permissive copy mode.
    """
    source = source.resolve(strict=True)
    try:
        before = source.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} source is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} source is not a regular file", RC_RECEIPT)
    try:
        data = source.read_bytes()
        after = source.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} source cannot be read: {exc}", RC_RECEIPT) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
    ):
        raise ValidationError(f"{label} source changed while it was read", RC_RECEIPT)
    target.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(target, flags, mode)
    except FileExistsError as exc:
        raise ValidationError(f"{label} target already exists", RC_RECEIPT) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            target.unlink()
        except OSError:
            pass
        raise
    target_data = target.read_bytes()
    source_sha = _sha256(data)
    if _sha256(target_data) != source_sha:
        raise ValidationError(f"{label} copy sha mismatch", RC_RECEIPT)
    return source_sha


def _codex_exec_argv(
    codex_binary: Path,
    requested_model: str,
    arm: str | Path,
    snapshot: Path | None = None,
    output: Path | None = None,
) -> list[str]:
    # Accept the old four-positional-argument form until the supervisor wave
    # passes slot.requested_model directly.  The generated argv is model-aware
    # in both forms, while new callers are explicit about the treatment model.
    if output is None:
        legacy_arm = requested_model
        legacy_snapshot = arm
        legacy_output = snapshot
        requested_model = MODEL
        arm = legacy_arm
        snapshot = legacy_snapshot  # type: ignore[assignment]
        output = legacy_output
    if not isinstance(requested_model, str) or requested_model not in MODEL_ALLOWLIST:
        raise ValidationError(
            f"requested model is not allowed: {requested_model}", RC_ROUTING
        )
    if not isinstance(arm, str) or not isinstance(snapshot, Path) or not isinstance(
        output, Path
    ):
        raise ValidationError(
            "codex argv construction arguments are malformed", RC_ROUTING
        )
    return [
        os.fspath(codex_binary),
        "exec",
        "-m",
        requested_model,
        "-c",
        f"model_reasoning_effort={arm}",
        "-s",
        "read-only",
        "-C",
        os.fspath(snapshot),
        "--json",
        "-o",
        os.fspath(output),
        "-",
    ]


def _bwrap_exec_argv(
    bwrap_binary: Path,
    codex_argv: Sequence[str],
    snapshot: Path,
    codex_home: Path,
    output: Path,
    stdout_path: Path,
    stderr_path: Path,
    environment: Mapping[str, str],
) -> list[str]:
    argv = [
        os.fspath(bwrap_binary),
        "--die-with-parent",
        "--new-session",
        "--unshare-pid",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/home",
        "--tmpfs",
        "/tmp",
    ]
    destination_paths = [
        snapshot,
        codex_home,
        output,
        stdout_path,
        stderr_path,
        Path(codex_argv[0]).resolve(),
    ]
    parent_directories: set[Path] = set()
    for destination in destination_paths:
        current = destination if destination.is_dir() else destination.parent
        while current != Path("/"):
            parent_directories.add(current)
            current = current.parent
    for directory in sorted(
        parent_directories, key=lambda value: (len(value.parts), os.fspath(value))
    ):
        argv.extend(("--dir", os.fspath(directory)))
    argv.extend(("--dir", "/tmp/t181-home"))
    for required in ("/usr", "/bin", "/lib", "/lib64"):
        path = Path(required)
        if path.exists():
            argv.extend(("--ro-bind", required, required))
    cli_binary = Path(codex_argv[0]).resolve()
    if not any(
        cli_binary == Path(root) or Path(root) in cli_binary.parents
        for root in ("/usr", "/bin", "/lib", "/lib64")
    ):
        argv.extend(
            ("--ro-bind", os.fspath(cli_binary), os.fspath(cli_binary))
        )
    for required in (
        "/etc/ssl",
        "/etc/resolv.conf",
        "/etc/hosts",
        "/etc/nsswitch.conf",
        "/etc/passwd",
    ):
        path = Path(required)
        if path.exists():
            argv.extend(("--ro-bind", required, required))
    argv.extend(
        (
            "--ro-bind",
            os.fspath(snapshot),
            os.fspath(snapshot),
            "--bind",
            os.fspath(codex_home),
            os.fspath(codex_home),
            "--bind",
            os.fspath(output),
            os.fspath(output),
            "--bind",
            os.fspath(stdout_path),
            os.fspath(stdout_path),
            "--bind",
            os.fspath(stderr_path),
            os.fspath(stderr_path),
            "--chdir",
            os.fspath(snapshot),
            "--clearenv",
        )
    )
    for key, value in sorted(environment.items()):
        argv.extend(("--setenv", key, value))
    argv.extend(("--", *codex_argv))
    return argv


@dataclass(frozen=True)
class Stage2PlanReplayerContract:
    """The immutable registration consumed by the stage2 replay driver."""

    schema_version: int
    contract_kind: str
    stage: str
    downstream_role: str
    source_plan_path: str
    plan_input: dict[str, Any]
    plan_input_hash: str
    requested_model: str
    requested_effort: str
    fix_pass_limit: int
    acceptance_condition: dict[str, Any]
    apparatus_pin: dict[str, Any]
    task_acceptance_status: str = "unbound"
    fix_gate_eligible: bool = False
    routing_evidence_eligible: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_kind": self.contract_kind,
            "stage": self.stage,
            "downstream_role": self.downstream_role,
            "source_plan_path": self.source_plan_path,
            "plan_input": dict(self.plan_input),
            "plan_input_hash": self.plan_input_hash,
            "requested_model": self.requested_model,
            "requested_effort": self.requested_effort,
            "fix_pass_limit": self.fix_pass_limit,
            "acceptance_condition": dict(self.acceptance_condition),
            "apparatus_pin": dict(self.apparatus_pin),
            "task_acceptance_status": self.task_acceptance_status,
            "fix_gate_eligible": self.fix_gate_eligible,
            "routing_evidence_eligible": self.routing_evidence_eligible,
        }


class _Stage2ReplayResult(dict[str, Any]):
    """Stage2 result schema with an in-memory legacy-read compatibility alias.

    ``cap_exhausted`` is the serialized field.  The old ``cap_exceeded`` read
    is supplied only through ``__missing__`` for callers that still index the
    Python return value; it is not a result/schema field and must not be read
    as evidence that an extra model call occurred.
    """

    def __missing__(self, key: str) -> Any:
        if key == "cap_exceeded":
            return self["cap_exhausted"]
        raise KeyError(key)


_STAGE2_CONTRACT_KIND = "stage2-plan-replayer"
_STAGE2_INTEGRITY_KIND = "stage2-plan-replayer-integrity"
_STAGE2_RESULT_KIND = "stage2-plan-replayer-result"
_STAGE2_RECEIPT_KIND = "stage2-execution-receipt"
_STAGE2_ACCEPTANCE_KINDS = frozenset({"execution-receipt", "unbound"})
_STAGE2_EFFORTS = frozenset({"max", "high"})
_STAGE2_DESCRIPTOR_KEYS = frozenset(
    {"path", "sha256", "bytes", "device", "inode"}
)
_STAGE2_APPARATUS_KEYS = frozenset(
    {
        "snapshot",
        "config",
        "auth",
        "binary",
        "snapshot_sha256",
        "config_sha256",
        "auth_sha256",
        "binary_sha256",
        "binary_version",
    }
)
_STAGE2_CONTRACT_KEYS = frozenset(
    {
        "schema_version",
        "contract_kind",
        "stage",
        "downstream_role",
        "source_plan_path",
        "plan_input",
        "plan_input_hash",
        "requested_model",
        "requested_effort",
        "fix_pass_limit",
        "acceptance_condition",
        "apparatus_pin",
        "task_acceptance_status",
        "fix_gate_eligible",
        "routing_evidence_eligible",
    }
)
_STAGE2_INTEGRITY_KEYS = frozenset(
    {
        "schema_version",
        "integrity_kind",
        "contract_path",
        "contract_sha256",
        "plan_input",
        "plan_input_hash",
        "apparatus_pin",
    }
)
_STAGE2_FIX_HEADER = b"STAGE2_REPLAYER_FIX_INPUT_V1\n"


def _stage2_path_below(path: Path, root: Path, label: str) -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(
            f"{label} is outside the stage2 run root", RC_RECEIPT
        ) from exc
    return resolved_path


def _stage2_absolute_path(path: Path) -> Path:
    """Make an absolute path without following its final symlink."""
    return Path(os.path.abspath(os.fspath(path)))


def _stage2_file_descriptor(path: Path, label: str) -> dict[str, Any]:
    candidate = Path(path)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} is not a regular file", RC_RECEIPT)
    try:
        data = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_RECEIPT) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    return {
        "path": os.fspath(candidate.resolve()),
        "sha256": _sha256(data),
        "bytes": len(data),
        "device": before.st_dev,
        "inode": before.st_ino,
    }


def _stage2_read_regular_bytes(path: Path, label: str) -> tuple[os.stat_result, bytes]:
    candidate = Path(path)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} is not a regular file", RC_RECEIPT)
    try:
        data = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_RECEIPT) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    return before, data


def _stage2_snapshot_entries(
    root: Path, label: str
) -> tuple[list[dict[str, Any]], int]:
    root = Path(root)
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ValidationError(f"{label} is not a directory", RC_RECEIPT)
    entries: list[dict[str, Any]] = []
    total_bytes = 0

    def visit(directory: Path, relative_directory: Path) -> None:
        nonlocal total_bytes
        try:
            with os.scandir(directory) as entries_stream:
                children = sorted(entries_stream, key=lambda entry: entry.name)
        except OSError as exc:
            raise ValidationError(
                f"{label} cannot be inspected: {exc}", RC_RECEIPT
            ) from exc
        for child in children:
            child_path = Path(child.path)
            relative = (relative_directory / child.name).as_posix()
            try:
                metadata = child_path.lstat()
            except OSError as exc:
                raise ValidationError(
                    f"{label} entry cannot be inspected: {relative}: {exc}",
                    RC_RECEIPT,
                ) from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a symlink: {relative}", RC_RECEIPT
                )
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                entries.append(
                    {"path": relative, "kind": "directory", "mode": mode}
                )
                visit(child_path, relative_directory / child.name)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a non-regular entry: {relative}",
                    RC_RECEIPT,
                )
            _, data = _stage2_read_regular_bytes(child_path, f"{label} entry {relative}")
            total_bytes += len(data)
            entries.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": mode,
                    "bytes": len(data),
                    "sha256": _sha256(data),
                }
            )

    visit(root, Path())
    try:
        final_root_metadata = root.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} changed while it was read: {exc}", RC_RECEIPT) from exc
    if (
        root_metadata.st_dev != final_root_metadata.st_dev
        or root_metadata.st_ino != final_root_metadata.st_ino
        or root_metadata.st_mtime_ns != final_root_metadata.st_mtime_ns
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    return entries, total_bytes


def _stage2_snapshot_descriptor(path: Path, label: str) -> dict[str, Any]:
    candidate = Path(path)
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError(f"{label} is not a directory", RC_RECEIPT)
    entries, total_bytes = _stage2_snapshot_entries(candidate, label)
    return {
        "path": os.fspath(candidate.resolve()),
        "sha256": _sha256(_canonical_bytes({"entries": entries})),
        "bytes": total_bytes,
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


def _stage2_copy_frozen_file(
    source: Path,
    target: Path,
    label: str,
    *,
    mode: int,
    expected_source_descriptor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_descriptor = _stage2_file_descriptor(source, label)
    if (
        expected_source_descriptor is not None
        and source_descriptor != expected_source_descriptor
    ):
        raise ValidationError(f"{label} changed before it was frozen", RC_RECEIPT)
    _, data = _stage2_read_regular_bytes(Path(source_descriptor["path"]), label)
    if _sha256(data) != source_descriptor["sha256"]:
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    _stage2_create_only_bytes(target, data, mode=mode)
    target_descriptor = _stage2_file_descriptor(target, f"frozen {label}")
    if (
        target_descriptor["sha256"] != source_descriptor["sha256"]
        or target_descriptor["bytes"] != source_descriptor["bytes"]
    ):
        raise ValidationError(f"frozen {label} copy sha mismatch", RC_RECEIPT)
    return target_descriptor


def _stage2_copy_frozen_snapshot(
    source: Path,
    target: Path,
    label: str,
    *,
    expected_source_descriptor: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = _stage2_absolute_path(Path(source))
    source_descriptor = _stage2_snapshot_descriptor(source, label)
    if (
        expected_source_descriptor is not None
        and source_descriptor != expected_source_descriptor
    ):
        raise ValidationError(f"{label} changed before it was frozen", RC_RECEIPT)
    if target.exists() or target.is_symlink():
        raise ValidationError(f"frozen {label} already exists: {target}", RC_RECEIPT)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.mkdir(mode=stat.S_IMODE(source.stat().st_mode), exist_ok=False)
    target.chmod(stat.S_IMODE(source.stat().st_mode))

    def copy_directory(source_directory: Path, target_directory: Path) -> None:
        try:
            with os.scandir(source_directory) as entries_stream:
                children = sorted(entries_stream, key=lambda entry: entry.name)
        except OSError as exc:
            raise ValidationError(
                f"{label} cannot be copied: {exc}", RC_RECEIPT
            ) from exc
        for child in children:
            source_path = Path(child.path)
            target_path = target_directory / child.name
            metadata = source_path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a symlink: {source_path}", RC_RECEIPT
                )
            if stat.S_ISDIR(metadata.st_mode):
                target_path.mkdir(mode=stat.S_IMODE(metadata.st_mode), exist_ok=False)
                target_path.chmod(stat.S_IMODE(metadata.st_mode))
                copy_directory(source_path, target_path)
            elif stat.S_ISREG(metadata.st_mode):
                _, data = _stage2_read_regular_bytes(source_path, f"{label} entry")
                _stage2_create_only_bytes(
                    target_path, data, mode=stat.S_IMODE(metadata.st_mode)
                )
            else:
                raise ValidationError(
                    f"{label} contains a non-regular entry: {source_path}",
                    RC_RECEIPT,
                )

    copy_directory(source, target)
    if _stage2_snapshot_descriptor(source, label)["sha256"] != source_descriptor["sha256"]:
        raise ValidationError(f"{label} changed while it was copied", RC_RECEIPT)
    target_descriptor = _stage2_snapshot_descriptor(target, f"frozen {label}")
    if (
        target_descriptor["sha256"] != source_descriptor["sha256"]
        or target_descriptor["bytes"] != source_descriptor["bytes"]
    ):
        raise ValidationError(f"frozen {label} copy sha mismatch", RC_RECEIPT)
    return target_descriptor


def _stage2_check_snapshot_descriptor(
    descriptor: Mapping[str, Any], root: Path, label: str
) -> None:
    if set(descriptor) != _STAGE2_DESCRIPTOR_KEYS:
        raise ValidationError(f"{label} descriptor keys are invalid", RC_RECEIPT)
    path_value = descriptor.get("path")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValidationError(f"{label} path is not absolute", RC_RECEIPT)
    candidate = Path(path_value)
    _stage2_path_below(candidate, root, label)
    current = _stage2_snapshot_descriptor(candidate, label)
    for field in ("path", "sha256", "bytes", "device", "inode"):
        if current.get(field) != descriptor.get(field):
            raise ValidationError(f"{label} {field} changed", RC_RECEIPT)


def _stage2_create_only_bytes(path: Path, data: bytes, *, mode: int = 0o600) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, mode)
    except FileExistsError as exc:
        raise ValidationError(
            f"stage2 frozen artifact already exists: {path}", RC_RECEIPT
        ) from exc
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        try:
            path.unlink()
        except OSError:
            pass
        raise


def _stage2_version_probe(binary: Path, *, cwd: Path, label: str) -> str:
    """Probe a frozen executable with a finite timeout and fail closed."""
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            [os.fspath(binary), "--version"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_clean_environment({"HOME": "/nonexistent"}),
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(
                timeout=STAGE2_REPLAYER_VERSION_PROBE_TIMEOUT_S
            )
        except subprocess.TimeoutExpired as exc:
            _stage2_stop_process_tree(process)
            raise ValidationError(
                f"{label} version probe timed out", RC_ROUTING
            ) from exc
        if process.returncode != 0:
            detail = stderr.decode("utf-8", "replace").strip()
            raise ValidationError(
                f"{label} version probe failed"
                + (f": {detail}" if detail else ""),
                RC_ROUTING,
            )
        version = stdout.decode("utf-8", "replace").strip()
        if not version:
            raise ValidationError(f"{label} version output is empty", RC_ROUTING)
        return version
    finally:
        if process is not None and process.poll() is None:
            _stage2_stop_process_tree(process)


def _stage2_create_only_json(path: Path, value: Mapping[str, Any]) -> None:
    _stage2_create_only_bytes(path, _canonical_bytes(dict(value)))


def _stage2_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationError(f"{label} is not a sha256", RC_RECEIPT)
    return value


def _stage2_check_descriptor(
    descriptor: Mapping[str, Any],
    root: Path,
    label: str,
) -> bytes:
    if set(descriptor) != _STAGE2_DESCRIPTOR_KEYS:
        raise ValidationError(f"{label} descriptor keys are invalid", RC_RECEIPT)
    path_value = descriptor.get("path")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValidationError(f"{label} path is not absolute", RC_RECEIPT)
    candidate = Path(path_value)
    _stage2_path_below(candidate, root, label)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} is not a regular file", RC_RECEIPT)
    if candidate.resolve() != Path(path_value):
        raise ValidationError(f"{label} path was replaced", RC_RECEIPT)
    try:
        data = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_RECEIPT) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    if before.st_dev != descriptor.get("device"):
        raise ValidationError(f"{label} device changed", RC_RECEIPT)
    if before.st_ino != descriptor.get("inode"):
        raise ValidationError(f"{label} inode changed", RC_RECEIPT)
    if before.st_size != descriptor.get("bytes"):
        raise ValidationError(f"{label} byte count changed", RC_RECEIPT)
    if _sha256(data) != descriptor.get("sha256"):
        raise ValidationError(f"{label} hash mismatch", RC_RECEIPT)
    _stage2_digest(descriptor.get("sha256"), f"{label} hash")
    return data


def _stage2_contract_bytes(contract: Mapping[str, Any]) -> bytes:
    """Serialize only the stage2 contract namespace, never the legacy schema."""
    return _canonical_bytes(dict(contract))


def _stage2_result_bytes(result: Mapping[str, Any]) -> bytes:
    """Serialize only stage2 replay results under the dedicated schema."""
    if result.get("schema_version") != STAGE2_REPLAYER_SCHEMA_VERSION:
        raise ValidationError("stage2 result schema version mismatch", RC_RECEIPT)
    return _canonical_bytes(dict(result))


def _stage2_integrity_path(contract_path: Path) -> Path:
    return contract_path.with_name(contract_path.name + ".integrity.json")


def _stage2_apparatus_pin(
    snapshot: Path,
    config: Path,
    auth: Path,
    codex_binary: Path,
) -> dict[str, Any]:
    snapshot_descriptor = _stage2_snapshot_descriptor(snapshot, "frozen snapshot")
    config_descriptor = _stage2_file_descriptor(config, "Codex config")
    auth_descriptor = _stage2_file_descriptor(auth, "Codex auth")
    binary_descriptor = _stage2_file_descriptor(codex_binary, "Codex binary")
    binary_version = _stage2_version_probe(
        codex_binary.resolve(),
        cwd=codex_binary.resolve().parent,
        label="Codex binary",
    )
    return {
        "snapshot": snapshot_descriptor,
        "config": config_descriptor,
        "auth": auth_descriptor,
        "binary": binary_descriptor,
        "snapshot_sha256": snapshot_descriptor["sha256"],
        "config_sha256": config_descriptor["sha256"],
        "auth_sha256": auth_descriptor["sha256"],
        "binary_sha256": binary_descriptor["sha256"],
        "binary_version": binary_version,
    }


def _stage2_validate_apparatus_pin(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE2_APPARATUS_KEYS:
        raise ValidationError("stage2 apparatus pin keys are invalid", RC_ROUTING)
    normalized = dict(value)
    snapshot = normalized["snapshot"]
    if not isinstance(snapshot, dict) or set(snapshot) != _STAGE2_DESCRIPTOR_KEYS:
        raise ValidationError("snapshot pin is malformed", RC_ROUTING)
    _stage2_digest(snapshot.get("sha256"), "snapshot pin hash")
    for field, label in (
        ("config", "Codex config"),
        ("auth", "Codex auth"),
        ("binary", "Codex binary"),
    ):
        descriptor = normalized[field]
        if not isinstance(descriptor, dict):
            raise ValidationError(f"{label} pin is malformed", RC_ROUTING)
        descriptor_keys = _STAGE2_DESCRIPTOR_KEYS
        if set(descriptor) != descriptor_keys:
            raise ValidationError(f"{label} pin keys are invalid", RC_ROUTING)
        _stage2_digest(descriptor.get("sha256"), f"{label} pin hash")
    for field, descriptor_field in (
        ("snapshot_sha256", "snapshot"),
        ("config_sha256", "config"),
        ("auth_sha256", "auth"),
        ("binary_sha256", "binary"),
    ):
        expected = normalized[field]
        descriptor = normalized[descriptor_field]
        _stage2_digest(expected, f"apparatus {field}")
        if expected != descriptor.get("sha256"):
            raise ValidationError(f"apparatus {field} does not match pin", RC_ROUTING)
    version = normalized["binary_version"]
    if not isinstance(version, str) or not version.strip():
        raise ValidationError("Codex binary version pin is malformed", RC_ROUTING)
    return normalized


def _stage2_validate_acceptance_condition(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {"kind", "reason"}:
        raise ValidationError("stage2 acceptance condition keys are invalid", RC_ROUTING)
    kind = value.get("kind")
    reason = value.get("reason")
    if kind not in _STAGE2_ACCEPTANCE_KINDS:
        raise ValidationError("stage2 acceptance kind is not allowed", RC_ROUTING)
    if not isinstance(reason, str) or not reason.strip():
        raise ValidationError("stage2 acceptance reason is required", RC_ROUTING)
    return {"kind": kind, "reason": reason}


def _stage2_validate_contract(
    value: Any,
    *,
    run_root: Path,
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE2_CONTRACT_KEYS:
        raise ValidationError("stage2 contract keys are invalid", RC_ROUTING)
    if value.get("schema_version") != STAGE2_REPLAYER_SCHEMA_VERSION:
        raise ValidationError("stage2 contract schema version mismatch", RC_ROUTING)
    if value.get("contract_kind") != _STAGE2_CONTRACT_KIND:
        raise ValidationError("stage2 contract kind mismatch", RC_ROUTING)
    if value.get("stage") != "stage2":
        raise ValidationError("stage2 contract stage mismatch", RC_ROUTING)
    if value.get("downstream_role") != "author":
        raise ValidationError("stage2 downstream role mismatch", RC_ROUTING)
    source_plan_path = value.get("source_plan_path")
    if not isinstance(source_plan_path, str) or not source_plan_path:
        raise ValidationError("stage2 source plan path is missing", RC_ROUTING)
    plan_input = value.get("plan_input")
    if not isinstance(plan_input, dict):
        raise ValidationError("stage2 plan descriptor is malformed", RC_ROUTING)
    _stage2_check_descriptor(plan_input, run_root, "frozen stage2 plan")
    _stage2_digest(value.get("plan_input_hash"), "stage2 plan input hash")
    if value["plan_input_hash"] != plan_input["sha256"]:
        raise ValidationError("stage2 plan input hash does not match descriptor", RC_ROUTING)
    requested_model = value.get("requested_model")
    if requested_model not in MODEL_ALLOWLIST:
        raise ValidationError("stage2 requested model is not allowed", RC_ROUTING)
    if value.get("requested_effort") not in _STAGE2_EFFORTS:
        raise ValidationError("stage2 requested effort is not allowed", RC_ROUTING)
    fix_pass_limit = value.get("fix_pass_limit")
    if (
        isinstance(fix_pass_limit, bool)
        or not isinstance(fix_pass_limit, int)
        or not 0 <= fix_pass_limit <= STAGE2_REPLAYER_MAX_MODEL_CALLS - 1
    ):
        raise ValidationError("stage2 fix pass limit is outside the cap", RC_ROUTING)
    acceptance = _stage2_validate_acceptance_condition(
        value.get("acceptance_condition")
    )
    apparatus = _stage2_validate_apparatus_pin(value.get("apparatus_pin"))
    if value.get("task_acceptance_status") != "unbound":
        raise ValidationError("stage2 task acceptance must remain unbound", RC_ROUTING)
    if value.get("fix_gate_eligible") is not False:
        raise ValidationError("stage2 fix gate eligibility must remain false", RC_ROUTING)
    if value.get("routing_evidence_eligible") is not False:
        raise ValidationError(
            "stage2 routing evidence eligibility must remain false", RC_ROUTING
        )
    contract = dict(value)
    contract["plan_input"] = dict(plan_input)
    contract["acceptance_condition"] = acceptance
    contract["apparatus_pin"] = apparatus
    return contract


def freeze_stage2_plan_replayer(
    plan_input: Path,
    output: Path,
    requested_model: str,
    requested_effort: str,
    fix_pass_limit: int,
    *,
    snapshot: Path,
    acceptance_kind: str = "unbound",
    acceptance_reason: str | None = None,
    config_source: Path,
    auth_source: Path,
    codex_binary: Path,
) -> dict[str, Any]:
    """Freeze raw plan bytes and every replay apparatus before launch.

    The downstream ``author`` label is a prompt role only; it does not request
    workspace-write access.  Its output is supervisor-observed stdout text.
    Snapshot, config, auth, and binary are all copied below ``run_root`` with
    create-only semantics.  Replay never falls back to a live or ambient path.
    """
    if any(
        value is None
        for value in (snapshot, config_source, auth_source, codex_binary)
    ):
        raise ValidationError(
            "stage2 snapshot, config, auth, and binary are required", RC_ROUTING
        )
    requested_contract_path = _stage2_absolute_path(Path(output))
    if requested_contract_path.exists() or requested_contract_path.is_symlink():
        raise ValidationError(
            f"stage2 frozen artifact already exists: {requested_contract_path}",
            RC_ROUTING,
        )
    run_root = requested_contract_path.parent.resolve()
    contract_path = run_root / requested_contract_path.name
    integrity_path = _stage2_integrity_path(contract_path)
    frozen_plan_path = run_root / "stage2-plan-input"
    frozen_snapshot_path = run_root / "stage2-snapshot"
    apparatus_root = run_root / "stage2-apparatus"
    frozen_config_path = apparatus_root / "config.toml"
    frozen_auth_path = apparatus_root / "auth.json"
    frozen_binary_path = apparatus_root / "codex"
    for candidate in (
        contract_path,
        integrity_path,
        frozen_plan_path,
        frozen_snapshot_path,
        apparatus_root,
    ):
        if candidate.exists() or candidate.is_symlink():
            raise ValidationError(
                f"stage2 frozen artifact already exists: {candidate}", RC_ROUTING
            )
    source_descriptor = _stage2_file_descriptor(Path(plan_input), "plan input")
    _, source_bytes = _stage2_read_regular_bytes(
        Path(source_descriptor["path"]), "plan input"
    )
    if _stage2_file_descriptor(Path(plan_input), "plan input") != source_descriptor:
        raise ValidationError("plan input changed before it was frozen", RC_RECEIPT)
    source_snapshot = _stage2_absolute_path(Path(snapshot))
    if (
        source_snapshot == run_root
        or run_root in source_snapshot.parents
        or source_snapshot == requested_contract_path
    ):
        raise ValidationError("stage2 snapshot must be outside the run root", RC_ROUTING)
    source_snapshot_descriptor = _stage2_snapshot_descriptor(source_snapshot, "snapshot")
    config_source_descriptor = _stage2_file_descriptor(config_source, "Codex config")
    auth_source_descriptor = _stage2_file_descriptor(auth_source, "Codex auth")
    binary_source_descriptor = _stage2_file_descriptor(codex_binary, "Codex binary")
    staged_paths: list[Path] = []
    try:
        _stage2_path_below(frozen_plan_path, run_root, "frozen stage2 plan")
        staged_paths.append(frozen_plan_path)
        _stage2_create_only_bytes(frozen_plan_path, source_bytes)
        frozen_descriptor = _stage2_file_descriptor(
            frozen_plan_path, "frozen stage2 plan"
        )
        if frozen_descriptor["sha256"] != source_descriptor["sha256"]:
            raise ValidationError("frozen stage2 plan hash mismatch", RC_RECEIPT)
        staged_paths.append(frozen_snapshot_path)
        _stage2_copy_frozen_snapshot(
            source_snapshot,
            frozen_snapshot_path,
            "snapshot",
            expected_source_descriptor=source_snapshot_descriptor,
        )
        apparatus_root.mkdir(mode=0o700, exist_ok=False)
        staged_paths.append(apparatus_root)
        _stage2_copy_frozen_file(
            config_source,
            frozen_config_path,
            "Codex config",
            mode=0o600,
            expected_source_descriptor=config_source_descriptor,
        )
        _stage2_copy_frozen_file(
            auth_source,
            frozen_auth_path,
            "Codex auth",
            mode=0o600,
            expected_source_descriptor=auth_source_descriptor,
        )
        frozen_binary_descriptor = _stage2_copy_frozen_file(
            codex_binary,
            frozen_binary_path,
            "Codex binary",
            mode=0o700,
            expected_source_descriptor=binary_source_descriptor,
        )
        if frozen_binary_descriptor["sha256"] != binary_source_descriptor["sha256"]:
            raise ValidationError("frozen Codex binary hash mismatch", RC_RECEIPT)
        reason = acceptance_reason
        if reason is None:
            reason = (
                "task-specific oracle is not bound; only supervisor execution facts "
                "are recorded"
            )
        contract = Stage2PlanReplayerContract(
            schema_version=STAGE2_REPLAYER_SCHEMA_VERSION,
            contract_kind=_STAGE2_CONTRACT_KIND,
            stage="stage2",
            downstream_role="author",
            source_plan_path=source_descriptor["path"],
            plan_input=frozen_descriptor,
            plan_input_hash=frozen_descriptor["sha256"],
            requested_model=requested_model,
            requested_effort=requested_effort,
            fix_pass_limit=fix_pass_limit,
            acceptance_condition={"kind": acceptance_kind, "reason": reason},
            apparatus_pin=_stage2_apparatus_pin(
                frozen_snapshot_path,
                frozen_config_path,
                frozen_auth_path,
                frozen_binary_path,
            ),
        ).as_dict()
        contract = _stage2_validate_contract(contract, run_root=run_root)
        contract_bytes = _stage2_contract_bytes(contract)
        integrity = {
            "schema_version": STAGE2_REPLAYER_SCHEMA_VERSION,
            "integrity_kind": _STAGE2_INTEGRITY_KIND,
            "contract_path": os.fspath(contract_path),
            "contract_sha256": _sha256(contract_bytes),
            "plan_input": dict(contract["plan_input"]),
            "plan_input_hash": contract["plan_input_hash"],
            "apparatus_pin": dict(contract["apparatus_pin"]),
        }
        staged_paths.append(contract_path)
        _stage2_create_only_bytes(contract_path, contract_bytes)
        staged_paths.append(integrity_path)
        _stage2_create_only_json(integrity_path, integrity)
        return contract
    except BaseException:
        for path in reversed(staged_paths):
            try:
                metadata = path.lstat()
                if stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(metadata.st_mode):
                    shutil.rmtree(path)
                else:
                    path.unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass
        raise


def _stage2_read_json_file(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    descriptor = _stage2_file_descriptor(path, label)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{label} is not valid JSON: {exc}", RC_RECEIPT) from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} is not a JSON object", RC_RECEIPT)
    if descriptor["sha256"] != _sha256(raw):
        raise ValidationError(f"{label} hash changed while reading", RC_RECEIPT)
    if _stage2_file_descriptor(path, label) != descriptor:
        raise ValidationError(f"{label} changed while reading", RC_RECEIPT)
    return value, raw


def _stage2_load_integrity(
    contract_path: Path,
    contract: Mapping[str, Any],
    contract_raw: bytes,
    run_root: Path,
) -> dict[str, Any]:
    integrity_path = _stage2_integrity_path(contract_path)
    integrity, _ = _stage2_read_json_file(integrity_path, "stage2 integrity record")
    if set(integrity) != _STAGE2_INTEGRITY_KEYS:
        raise ValidationError("stage2 integrity record keys are invalid", RC_RECEIPT)
    if integrity.get("schema_version") != STAGE2_REPLAYER_SCHEMA_VERSION:
        raise ValidationError("stage2 integrity schema version mismatch", RC_RECEIPT)
    if integrity.get("integrity_kind") != _STAGE2_INTEGRITY_KIND:
        raise ValidationError("stage2 integrity kind mismatch", RC_RECEIPT)
    if integrity.get("contract_path") != os.fspath(contract_path):
        raise ValidationError("stage2 contract path integrity mismatch", RC_RECEIPT)
    _stage2_digest(integrity.get("contract_sha256"), "stage2 contract hash")
    if integrity["contract_sha256"] != _sha256(contract_raw):
        raise ValidationError("stage2 contract hash mismatch", RC_RECEIPT)
    if integrity.get("plan_input") != contract.get("plan_input"):
        raise ValidationError("stage2 plan integrity descriptor mismatch", RC_RECEIPT)
    if integrity.get("plan_input_hash") != contract.get("plan_input_hash"):
        raise ValidationError("stage2 plan input hash integrity mismatch", RC_RECEIPT)
    if integrity.get("apparatus_pin") != contract.get("apparatus_pin"):
        raise ValidationError("stage2 apparatus integrity mismatch", RC_RECEIPT)
    _stage2_check_descriptor(
        integrity["plan_input"], run_root, "frozen stage2 plan"
    )
    _stage2_validate_apparatus_pin(integrity["apparatus_pin"])
    return integrity


def _load_stage2_plan_replayer_contract(
    contract_path: Path,
    *,
    run_root: Path | None = None,
) -> dict[str, Any]:
    """Load a create-only contract and its independent integrity record."""
    requested_contract_path = _stage2_absolute_path(Path(contract_path))
    contract_descriptor = _stage2_file_descriptor(
        requested_contract_path, "stage2 contract"
    )
    contract_path = Path(contract_descriptor["path"])
    root = Path(run_root).resolve() if run_root is not None else contract_path.parent
    _stage2_path_below(contract_path, root, "stage2 contract")
    contract, raw = _stage2_read_json_file(contract_path, "stage2 contract")
    contract = _stage2_validate_contract(contract, run_root=root)
    _stage2_load_integrity(contract_path, contract, raw, root)
    return contract


def _stage2_guard(
    contract_path: Path,
    run_root: Path,
) -> tuple[dict[str, Any], str, bytes]:
    requested_contract_path = _stage2_absolute_path(Path(contract_path))
    contract_descriptor = _stage2_file_descriptor(
        requested_contract_path, "stage2 contract"
    )
    contract_path = Path(contract_descriptor["path"])
    _stage2_path_below(contract_path, run_root, "stage2 contract")
    contract, raw = _stage2_read_json_file(contract_path, "stage2 contract")
    contract = _stage2_validate_contract(contract, run_root=run_root)
    _stage2_load_integrity(contract_path, contract, raw, run_root)
    plan_bytes = _stage2_check_descriptor(
        contract["plan_input"], run_root, "frozen stage2 plan"
    )
    return contract, _sha256(raw), plan_bytes


def _stage2_resolve_apparatus(
    contract: Mapping[str, Any],
    config_source: Path | None,
    auth_source: Path | None,
    codex_binary: Path | None,
    *,
    run_root: Path,
) -> tuple[Path, Path, Path, Path]:
    """Resolve only the create-only apparatus registered in the contract.

    The source arguments remain as a compatibility-shaped API surface, but
    are intentionally ignored.  Ambient defaults and live caller paths are
    never allowed to become replay inputs.
    """
    del config_source, auth_source, codex_binary
    pin = _stage2_validate_apparatus_pin(contract["apparatus_pin"])
    resolved: dict[str, Path] = {}
    for field in ("config", "auth", "binary"):
        descriptor = pin[field]
        _stage2_check_descriptor(descriptor, run_root, f"stage2 frozen {field}")
        candidate = Path(descriptor["path"])
        if field == "binary" and not (candidate.stat().st_mode & stat.S_IXUSR):
            raise ValidationError("stage2 frozen binary is not executable", RC_ROUTING)
        resolved[field] = candidate
    snapshot_descriptor = pin["snapshot"]
    _stage2_check_snapshot_descriptor(
        snapshot_descriptor, run_root, "stage2 frozen snapshot"
    )
    frozen_snapshot = Path(snapshot_descriptor["path"])
    binary_version = _stage2_version_probe(
        resolved["binary"],
        cwd=resolved["binary"].parent,
        label="stage2 Codex binary",
    )
    if binary_version != pin["binary_version"]:
        raise ValidationError("stage2 Codex binary version pin mismatch", RC_ROUTING)
    return resolved["config"], resolved["auth"], resolved["binary"], frozen_snapshot


def _stage2_exec_argv(
    codex_binary: Path,
    requested_model: str,
    requested_effort: str,
    snapshot: Path,
    output: Path,
) -> list[str]:
    argv = _codex_exec_argv(
        codex_binary, requested_model, requested_effort, snapshot, output
    )
    try:
        exec_position = argv.index("exec")
    except ValueError as exc:
        raise ValidationError("stage2 Codex argv has no exec command", RC_ROUTING) from exc
    argv[exec_position + 1 : exec_position + 1] = ["--skip-git-repo-check"]
    return argv


def _stage2_fix_input(plan_bytes: bytes, previous_output: bytes, pass_index: int) -> bytes:
    if pass_index == 0:
        return plan_bytes
    return (
        _STAGE2_FIX_HEADER
        + str(len(plan_bytes)).encode("ascii")
        + b"\n"
        + plan_bytes
        + b"\n"
        + str(len(previous_output)).encode("ascii")
        + b"\n"
        + previous_output
    )


def _stage2_stop_process_tree(
    process: subprocess.Popen[bytes],
) -> tuple[bytes, bytes]:
    def signal_group(number: int) -> None:
        try:
            os.killpg(process.pid, number)
        except (ProcessLookupError, PermissionError):
            try:
                if number == signal.SIGTERM:
                    process.terminate()
                else:
                    process.kill()
            except ProcessLookupError:
                pass

    signal_group(signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=1.0)
        return stdout or b"", stderr or b""
    except subprocess.TimeoutExpired:
        signal_group(signal.SIGKILL)
    try:
        stdout, stderr = process.communicate(timeout=2.0)
        return stdout or b"", stderr or b""
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=2.0)
            return stdout or b"", stderr or b""
        except subprocess.TimeoutExpired:
            return b"", b"stage2 process termination timed out"


def _stage2_output_state(path: Path) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except OSError:
        return {"path": os.fspath(path.resolve()), "regular": False, "bytes": 0}
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        return {
            "path": os.fspath(path.resolve()),
            "regular": False,
            "bytes": metadata.st_size,
        }
    try:
        data = path.read_bytes()
        after = path.lstat()
    except OSError:
        return {"path": os.fspath(path.resolve()), "regular": False, "bytes": 0}
    if metadata.st_ino != after.st_ino or metadata.st_size != after.st_size:
        return {"path": os.fspath(path.resolve()), "regular": False, "bytes": 0}
    return {
        "path": os.fspath(path.resolve()),
        "regular": True,
        "bytes": len(data),
        "sha256": _sha256(data),
    }


def _stage2_receipt_status(
    receipt: Mapping[str, Any],
    *,
    contract_sha256: str,
    plan_sha256: str,
    expected_model: str | None = None,
    expected_effort: str | None = None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if receipt.get("contract_sha256") != contract_sha256:
        reasons.append("execution receipt contract hash mismatch")
    if receipt.get("plan_sha256") != plan_sha256:
        reasons.append("execution receipt plan hash mismatch")
    if receipt.get("timed_out"):
        reasons.append("execution receipt timed out")
    if receipt.get("exit_code") != 0:
        reasons.append("execution receipt exit code is non-zero")
    if expected_model is not None or expected_effort is not None:
        actual_argv = receipt.get("argv")
        try:
            if not isinstance(actual_argv, list):
                raise ValidationError("execution receipt argv is not an array", RC_RECEIPT)
            if expected_model is None or expected_effort is None:
                raise ValidationError("execution receipt argv expectations are incomplete", RC_RECEIPT)
            _normalized_exec_argv(actual_argv, expected_model, expected_effort)
            exec_position = actual_argv.index("exec")
            if actual_argv[exec_position + 1] != "--skip-git-repo-check":
                raise ValidationError("stage2 argv skip flag is misplaced", RC_ROUTING)
        except (ValidationError, ValueError) as exc:
            reasons.extend(exc.reasons if isinstance(exc, ValidationError) else [str(exc)])
    output = receipt.get("output")
    if not isinstance(output, Mapping) or output.get("regular") is not True:
        reasons.append("execution receipt output is not a regular file")
    else:
        output_bytes = output.get("bytes")
        output_hash = output.get("sha256")
        if not isinstance(output_bytes, int) or output_bytes <= 0:
            reasons.append("execution receipt output is empty")
        if not isinstance(output_hash, str):
            reasons.append("execution receipt output hash is missing")
        elif receipt.get("output_sha256") != output_hash:
            reasons.append("execution receipt output hash mismatch")
    return ("valid" if not reasons else "invalid"), reasons


def _stage2_acceptance(
    receipt: Mapping[str, Any],
    acceptance_condition: Mapping[str, Any] | None = None,
    *,
    expected_contract_sha256: str | None = None,
    expected_plan_sha256: str | None = None,
    expected_model: str | None = None,
    expected_effort: str | None = None,
) -> dict[str, Any]:
    """Separate mechanical receipt facts from the permanently unbound task state."""
    condition = _stage2_validate_acceptance_condition(
        dict(
            acceptance_condition
            or {
                "kind": "execution-receipt",
                "reason": "supervisor execution facts only",
            }
        )
    )
    receipt_status, reasons = _stage2_receipt_status(
        receipt,
        contract_sha256=(
            expected_contract_sha256
            if expected_contract_sha256 is not None
            else str(receipt.get("contract_sha256", ""))
        ),
        plan_sha256=(
            expected_plan_sha256
            if expected_plan_sha256 is not None
            else str(receipt.get("plan_sha256", ""))
        ),
        expected_model=expected_model,
        expected_effort=expected_effort,
    )
    return {
        "receipt_status": receipt_status,
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
        "acceptance_condition_kind": condition["kind"],
        "failure_reasons": reasons,
    }


def _stage2_replay_one(
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    plan_bytes: bytes,
    plan_sha256: str,
    pass_index: int,
    previous_output: bytes,
    run_root: Path,
    snapshot: Path,
    config_source: Path,
    auth_source: Path,
    codex_binary: Path,
    wall_clock_timeout_s: float,
) -> dict[str, Any]:
    pass_label = f"pass-{pass_index + 1:03d}"
    pass_root = run_root / "stage2-passes" / pass_label
    pass_root.mkdir(parents=True, exist_ok=False)
    output = pass_root / "output.txt"
    stdout_path = pass_root / "stdout.txt"
    stderr_path = pass_root / "stderr.txt"
    home = pass_root / "home"
    home.mkdir(mode=0o700, exist_ok=False)
    (home / ".codex").mkdir(mode=0o700, exist_ok=False)
    process: subprocess.Popen[bytes] | None = None
    try:
        pin = _stage2_validate_apparatus_pin(contract["apparatus_pin"])
        _stage2_check_snapshot_descriptor(
            pin["snapshot"], run_root, "stage2 frozen snapshot"
        )
        pass_snapshot = pass_root / "snapshot"
        pass_snapshot_descriptor = _stage2_copy_frozen_snapshot(
            snapshot, pass_snapshot, "stage2 pass snapshot"
        )
        if pass_snapshot_descriptor["sha256"] != pin["snapshot_sha256"]:
            raise ValidationError("stage2 snapshot pin mismatch before launch", RC_RECEIPT)
        config_target = home / ".codex" / "config.toml"
        auth_target = home / ".codex" / "auth.json"
        pass_binary = pass_root / "codex"
        config_sha256 = _copy_identity_file(
            config_source, config_target, "stage2 Codex config", mode=0o600
        )
        auth_sha256 = _copy_identity_file(
            auth_source, auth_target, "stage2 Codex auth", mode=0o600
        )
        binary_sha256 = _copy_identity_file(
            codex_binary, pass_binary, "stage2 Codex binary", mode=0o700
        )
        if config_sha256 != pin["config_sha256"]:
            raise ValidationError("stage2 config apparatus pin mismatch before launch", RC_RECEIPT)
        if auth_sha256 != pin["auth_sha256"]:
            raise ValidationError("stage2 auth apparatus pin mismatch before launch", RC_RECEIPT)
        if binary_sha256 != pin["binary_sha256"]:
            raise ValidationError("stage2 binary apparatus pin mismatch before launch", RC_RECEIPT)
        # Known residual risk: a same-UID replacement can still occur between
        # hash validation and Popen; FD-based exec would be needed to close it.
        # This is local single-operator research tooling, not a hostile multi-tenant target.
        stdin_bytes = _stage2_fix_input(plan_bytes, previous_output, pass_index)
        argv = _stage2_exec_argv(
            pass_binary,
            str(contract["requested_model"]),
            str(contract["requested_effort"]),
            pass_snapshot,
            output,
        )
        environment = dict(os.environ)
        environment["HOME"] = os.fspath(home)
        environment["CODEX_HOME"] = os.fspath(home / ".codex")
        started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        start_ns = time.monotonic_ns()
        stdout_bytes = b""
        stderr_bytes = b""
        exit_code: int | None = None
        timed_out = False
        process_started = False
        process_error: str | None = None
        try:
            process = subprocess.Popen(
                argv,
                cwd=pass_snapshot,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=environment,
                start_new_session=True,
            )
            process_started = True
            try:
                stdout_bytes, stderr_bytes = process.communicate(
                    input=stdin_bytes,
                    timeout=wall_clock_timeout_s,
                )
            except subprocess.TimeoutExpired:
                timed_out = True
                stdout_bytes, stderr_bytes = _stage2_stop_process_tree(process)
            exit_code = process.returncode
        except OSError as exc:
            process_error = str(exc)
        exit_ns = time.monotonic_ns()
        _stage2_create_only_bytes(stdout_path, stdout_bytes or b"")
        _stage2_create_only_bytes(stderr_path, stderr_bytes or b"")
        output_state = _stage2_output_state(output)
        receipt: dict[str, Any] = {
            "schema_version": STAGE2_REPLAYER_SCHEMA_VERSION,
            "receipt_kind": _STAGE2_RECEIPT_KIND,
            "pass_index": pass_index,
            "started_at": started_at,
            "process_started": process_started,
            "process_start_monotonic_ns": start_ns,
            "process_exit_monotonic_ns": exit_ns,
            "process_wall_ms": round((exit_ns - start_ns) / 1_000_000),
            "exit_code": exit_code,
            "timed_out": timed_out,
            "wall_clock_timeout_s": wall_clock_timeout_s,
            "contract_sha256": contract_sha256,
            "plan_sha256": plan_sha256,
            "stdin_sha256": _sha256(stdin_bytes),
            "stdin_bytes": len(stdin_bytes),
            "stdin_is_raw_plan": pass_index == 0,
            "requested_model": contract["requested_model"],
            "requested_effort": contract["requested_effort"],
            "apparatus_pin": dict(contract["apparatus_pin"]),
            "downstream_role": "author",
            "argv": argv,
            "snapshot_sha256": pin["snapshot_sha256"],
            "binary_sha256": binary_sha256,
            "output": output_state,
            "output_sha256": output_state.get("sha256"),
            "stdout_path": os.fspath(stdout_path.resolve()),
            "stderr_path": os.fspath(stderr_path.resolve()),
            "home": os.fspath(home.resolve()),
            "config_sha256": config_sha256,
            "auth_sha256": auth_sha256,
        }
        if process_error is not None:
            receipt["failure_reasons"] = [f"downstream launch failed: {process_error}"]
        if timed_out:
            receipt["failure_reasons"] = ["downstream wall timeout consumed this pass"]
        receipt.update(
            _stage2_acceptance(
                receipt,
                contract["acceptance_condition"],
                expected_contract_sha256=contract_sha256,
                expected_plan_sha256=plan_sha256,
                expected_model=str(contract["requested_model"]),
                expected_effort=str(contract["requested_effort"]),
            )
        )
        return receipt
    finally:
        termination_error: BaseException | None = None
        try:
            if process is not None and process.poll() is None:
                _stage2_stop_process_tree(process)
            if process is not None and process.poll() is None:
                process.wait(timeout=2.0)
        except BaseException as exc:
            termination_error = exc
        try:
            shutil.rmtree(home)
        except OSError as exc:
            termination_error = termination_error or exc
        if home.exists() or home.is_symlink():
            termination_error = termination_error or RuntimeError(
                "stage2 dedicated HOME remained after cleanup"
            )
        if termination_error is not None:
            raise ValidationError(
                f"stage2 process/HOME cleanup failed: {termination_error}", RC_RECEIPT
            ) from termination_error


def replay_stage2_plan(
    contract_path: Path,
    run_root: Path,
    result_path: Path,
    snapshot: Path,
    config_source: Path | None = None,
    auth_source: Path | None = None,
    codex_binary: Path | None = None,
    *,
    bwrap_binary: Path | None = None,
    dry_run: bool = False,
    wall_clock_timeout_s: float = STAGE2_REPLAYER_DEFAULT_WALL_CLOCK_TIMEOUT_S,
) -> tuple[dict[str, Any], int]:
    """Replay frozen plan bytes with a bounded direct Codex process.

    ``downstream_role="author"`` is only a prompt role label and does not ask
    for workspace-write.  The output is supervisor-observed stdout text.  This
    deliberately inherits the ambient environment with a dedicated HOME and
    copies auth/config there; T-181's hermetic bwrap apparatus is not used
    because F13 established that this mechanism needs the live ambient network.
    The compatibility-shaped ``snapshot`` and apparatus arguments are ignored:
    the contract's run-root copies are the only replay inputs.  The optional
    ``bwrap_binary`` argument is likewise retained only for old Python callers;
    this direct stage2 verb has no bwrap dispatch.  ``dry_run`` is recorded as
    metadata and does not suppress the bounded downstream launch.
    """
    del bwrap_binary
    del snapshot
    run_root = Path(run_root).resolve()
    requested_contract_path = _stage2_absolute_path(Path(contract_path))
    contract_descriptor = _stage2_file_descriptor(
        requested_contract_path, "stage2 contract"
    )
    contract_path = Path(contract_descriptor["path"])
    _stage2_path_below(contract_path, run_root, "stage2 contract")
    requested_result_path = _stage2_absolute_path(Path(result_path))
    if requested_result_path.exists() or requested_result_path.is_symlink():
        raise ValidationError("stage2 result already exists", RC_RECEIPT)
    result_path = requested_result_path.parent.resolve() / requested_result_path.name
    if isinstance(wall_clock_timeout_s, bool) or not isinstance(
        wall_clock_timeout_s, (int, float)
    ) or not math.isfinite(float(wall_clock_timeout_s)) or not (
        0 < float(wall_clock_timeout_s) <= STAGE2_REPLAYER_MAX_WALL_CLOCK_TIMEOUT_S
    ):
        raise ValidationError(
            "stage2 wall timeout must be finite, positive, and within the bound",
            RC_ROUTING,
        )
    _stage2_path_below(result_path, run_root, "stage2 result")
    contract, contract_raw = _stage2_read_json_file(
        contract_path, "stage2 contract"
    )
    contract = _stage2_validate_contract(contract, run_root=run_root)
    _stage2_load_integrity(contract_path, contract, contract_raw, run_root)
    initial_contract_sha256 = _sha256(contract_raw)
    config, auth, binary, frozen_snapshot = _stage2_resolve_apparatus(
        contract,
        config_source,
        auth_source,
        codex_binary,
        run_root=run_root,
    )
    ledger_path = run_root / "stage2-attempt-ledger.jsonl"
    if ledger_path.exists() or ledger_path.is_symlink():
        raise ValidationError("stage2 attempt ledger already exists", RC_RECEIPT)
    attempts: list[dict[str, Any]] = []
    previous_output = b""
    final_receipt: dict[str, Any] | None = None
    cap = int(contract["fix_pass_limit"]) + 1
    for pass_index in range(cap):
        current_contract, current_sha256, plan_bytes = _stage2_guard(
            contract_path, run_root
        )
        if current_sha256 != initial_contract_sha256 or current_contract != contract:
            raise ValidationError("stage2 contract changed during replay", RC_RECEIPT)
        config, auth, binary, frozen_snapshot = _stage2_resolve_apparatus(
            contract,
            config,
            auth,
            binary,
            run_root=run_root,
        )
        receipt = _stage2_replay_one(
            contract=contract,
            contract_sha256=current_sha256,
            plan_bytes=plan_bytes,
            plan_sha256=contract["plan_input"]["sha256"],
            pass_index=pass_index,
            previous_output=previous_output,
            run_root=run_root,
            snapshot=frozen_snapshot,
            config_source=config,
            auth_source=auth,
            codex_binary=binary,
            wall_clock_timeout_s=float(wall_clock_timeout_s),
        )
        try:
            post_contract, post_sha256, post_plan_bytes = _stage2_guard(
                contract_path, run_root
            )
            if (
                post_sha256 != current_sha256
                or post_contract != contract
                or post_plan_bytes != plan_bytes
            ):
                raise ValidationError("stage2 input changed after downstream", RC_RECEIPT)
        except ValidationError as exc:
            receipt["receipt_status"] = "invalid"
            receipt["task_acceptance_status"] = "unbound"
            receipt["fix_gate_eligible"] = False
            receipt["routing_evidence_eligible"] = False
            receipt["failure_reasons"] = sorted(
                set(receipt.get("failure_reasons", [])) | set(exc.reasons)
            )
            _append_jsonl(ledger_path, receipt)
            attempts.append(receipt)
            raise
        _append_jsonl(ledger_path, receipt)
        attempts.append(receipt)
        final_receipt = receipt
        if receipt["receipt_status"] == "valid":
            break
        output_path = Path(receipt["output"]["path"])
        try:
            if output_path.is_file() and not output_path.is_symlink():
                previous_output = output_path.read_bytes()
        except OSError:
            previous_output = b""
    if final_receipt is None:
        raise ValidationError("stage2 replay did not produce a receipt", RC_RECEIPT)
    success = final_receipt["receipt_status"] == "valid"
    failure_reasons = list(final_receipt.get("failure_reasons", []))
    if not success:
        failure_reasons.append("stage2 fix pass cap exhausted")
    result: dict[str, Any] = _Stage2ReplayResult({
        "schema_version": STAGE2_REPLAYER_SCHEMA_VERSION,
        "result_kind": _STAGE2_RESULT_KIND,
        "contract_sha256": initial_contract_sha256,
        "contract_path": os.fspath(contract_path),
        "plan_input": dict(contract["plan_input"]),
        "plan_input_hash": contract["plan_input_hash"],
        "requested_model": contract["requested_model"],
        "requested_effort": contract["requested_effort"],
        "apparatus_pin": dict(contract["apparatus_pin"]),
        "downstream_role": "author",
        "fix_pass_limit": contract["fix_pass_limit"],
        "model_calls": len(attempts),
        # The canonical fact is exhaustion: the bounded loop stopped after
        # exactly 1 + fix_pass_limit calls.
        "cap_exhausted": not success,
        "receipt_status": final_receipt["receipt_status"],
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
        "output_sha256": final_receipt.get("output_sha256"),
        "output": final_receipt.get("output"),
        "attempts": attempts,
        "failure_reasons": sorted(set(failure_reasons)),
        "dry_run": dry_run,
    })
    _stage2_create_only_bytes(result_path, _stage2_result_bytes(result))
    return result, 0 if success else RC_RECEIPT


@dataclass(frozen=True)
class Stage5AuthorReplayerContract:
    """Create-only registration for deterministic stage5 author replay."""

    schema_version: int
    contract_kind: str
    stage: str
    source_descriptors: dict[str, Any]
    frozen_plan: dict[str, Any]
    plan_input_hash: str
    frozen_author_output: dict[str, Any]
    application_target: dict[str, Any]
    author_output_hash: str
    application_apparatus: dict[str, Any]
    downstream_pins: dict[str, Any]
    fix_pass_limit: int
    receipt_policy: dict[str, Any]
    task_acceptance_status: str = "unbound"
    fix_gate_eligible: bool = False
    routing_evidence_eligible: bool = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "contract_kind": self.contract_kind,
            "stage": self.stage,
            "source_descriptors": dict(self.source_descriptors),
            "frozen_plan": dict(self.frozen_plan),
            "plan_input_hash": self.plan_input_hash,
            "frozen_author_output": dict(self.frozen_author_output),
            "application_target": dict(self.application_target),
            "author_output_hash": self.author_output_hash,
            "application_apparatus": dict(self.application_apparatus),
            "downstream_pins": dict(self.downstream_pins),
            "fix_pass_limit": self.fix_pass_limit,
            "receipt_policy": dict(self.receipt_policy),
            "task_acceptance_status": self.task_acceptance_status,
            "fix_gate_eligible": self.fix_gate_eligible,
            "routing_evidence_eligible": self.routing_evidence_eligible,
        }


_STAGE5_CONTRACT_KIND = "stage5-author-replayer-contract"
_STAGE5_INTEGRITY_KIND = "stage5-author-replayer-integrity"
_STAGE5_APPLICATION_RECEIPT_KIND = "stage5-author-application-validation-receipt"
_STAGE5_DOWNSTREAM_RECEIPT_KIND = "stage5-downstream-receipt"
_STAGE5_EFFORTS = frozenset({"max", "high"})
_STAGE5_FORBIDDEN_CORRECTNESS_KEYS = frozenset({"accepted", "success", "passed"})
_STAGE5_CONTRACT_KEYS = frozenset(
    {
        "schema_version",
        "contract_kind",
        "stage",
        "source_descriptors",
        "frozen_plan",
        "plan_input_hash",
        "frozen_author_output",
        "application_target",
        "author_output_hash",
        "application_apparatus",
        "downstream_pins",
        "fix_pass_limit",
        "receipt_policy",
        "task_acceptance_status",
        "fix_gate_eligible",
        "routing_evidence_eligible",
    }
)
_STAGE5_AUTHOR_OUTPUT_KEYS = frozenset({"artifact", "format"})
_STAGE5_APPLICATION_TARGET_KEYS = frozenset(
    {"snapshot", "relative_root", "pre_application_tree_sha256"}
)
_STAGE5_GIT_PIN_KEYS = frozenset(
    {"git", "git_sha256", "git_version", "check_argv", "apply_argv"}
)
_STAGE5_ROLE_PIN_KEYS = frozenset({"requested_model", "requested_effort"})
_STAGE5_DESCRIPTOR_KEYS = frozenset(
    {"path", "kind", "mode", "sha256", "bytes", "device", "inode"}
)
_STAGE5_SOURCE_DESCRIPTOR_KEYS = frozenset(
    {"plan", "author_output", "snapshot", "git"}
)
_STAGE5_DOWNSTREAM_OUTPUT_KEYS = frozenset({"regular", "bytes", "sha256"})
_STAGE5_RECEIPT_POLICY_KEYS = frozenset(
    {
        "version",
        "receipt_kind",
        "argv_match",
        "stdin_match",
        "output_match",
        "previous_receipt_match",
        "role_argv",
    }
)
_STAGE5_APPLICATION_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "receipt_kind",
        "contract_sha256",
        "plan_input_hash",
        "author_output_hash",
        "application_target_sha256",
        "pre_tree_sha256",
        "post_tree_sha256",
        "git_sha256",
        "git_version",
        "check_argv",
        "apply_argv",
        "check_exit_code",
        "apply_exit_code",
        "timed_out",
        "receipt_status",
        "task_acceptance_status",
        "fix_gate_eligible",
        "routing_evidence_eligible",
    }
)
_STAGE5_DOWNSTREAM_RECEIPT_KEYS = frozenset(
    {
        "schema_version",
        "receipt_kind",
        "contract_sha256",
        "role",
        "pass_index",
        "author_output_hash",
        "application_target_sha256",
        "requested_model",
        "requested_effort",
        "argv",
        "stdin_sha256",
        "output",
        "output_sha256",
        "previous_receipt_sha256",
        "exit_code",
        "timed_out",
        "receipt_status",
        "task_acceptance_status",
        "fix_gate_eligible",
        "routing_evidence_eligible",
    }
)
_STAGE5_INTEGRITY_KEYS = frozenset(
    {
        "schema_version",
        "integrity_kind",
        "contract_path",
        "contract_sha256",
        "source_plan",
        "source_author_output",
        "source_snapshot",
        "source_git",
        "plan_input_hash",
        "author_output_hash",
        "frozen_snapshot_sha256",
        "git_sha256",
        "application_target_sha256",
        "task_acceptance_status",
        "fix_gate_eligible",
        "routing_evidence_eligible",
    }
)


def _stage5_reject_generic_correctness_keys(value: Any, label: str) -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if isinstance(key, str) and key.casefold() in _STAGE5_FORBIDDEN_CORRECTNESS_KEYS:
                raise ValidationError(
                    f"{label} contains forbidden correctness key: {key}", RC_ROUTING
                )
            _stage5_reject_generic_correctness_keys(item, label)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _stage5_reject_generic_correctness_keys(item, label)


def _stage5_absolute_path(path: Path) -> Path:
    """Make an absolute stage5 path without following its final symlink."""
    return Path(os.path.abspath(os.fspath(path)))


def _stage5_path_below(path: Path, root: Path, label: str) -> Path:
    resolved_path = path.resolve()
    resolved_root = root.resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValidationError(
            f"{label} is outside the stage5 run root", RC_RECEIPT
        ) from exc
    return resolved_path


def _stage5_read_regular_bytes(
    path: Path, label: str
) -> tuple[os.stat_result, bytes]:
    candidate = Path(path)
    try:
        before = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISREG(before.st_mode):
        raise ValidationError(f"{label} is not a regular file", RC_RECEIPT)
    try:
        data = candidate.read_bytes()
        after = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_RECEIPT) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    return before, data


def _stage5_file_descriptor(path: Path, label: str) -> dict[str, Any]:
    candidate = Path(path)
    metadata, data = _stage5_read_regular_bytes(candidate, label)
    return {
        "path": os.fspath(candidate.resolve()),
        "kind": "file",
        "mode": stat.S_IMODE(metadata.st_mode),
        "sha256": _sha256(data),
        "bytes": len(data),
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


def _stage5_snapshot_entries(
    root: Path, label: str
) -> tuple[list[dict[str, Any]], int]:
    root = Path(root)
    try:
        root_metadata = root.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(root_metadata.st_mode) or not stat.S_ISDIR(root_metadata.st_mode):
        raise ValidationError(f"{label} is not a directory", RC_RECEIPT)
    entries: list[dict[str, Any]] = []
    total_bytes = 0

    def visit(directory: Path, relative_directory: Path) -> None:
        nonlocal total_bytes
        try:
            with os.scandir(directory) as entries_stream:
                children = sorted(entries_stream, key=lambda entry: entry.name)
        except OSError as exc:
            raise ValidationError(
                f"{label} cannot be inspected: {exc}", RC_RECEIPT
            ) from exc
        for child in children:
            child_path = Path(child.path)
            relative = (relative_directory / child.name).as_posix()
            try:
                metadata = child_path.lstat()
            except OSError as exc:
                raise ValidationError(
                    f"{label} entry cannot be inspected: {relative}: {exc}",
                    RC_RECEIPT,
                ) from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a symlink: {relative}", RC_RECEIPT
                )
            mode = stat.S_IMODE(metadata.st_mode)
            if stat.S_ISDIR(metadata.st_mode):
                entries.append(
                    {"path": relative, "kind": "directory", "mode": mode}
                )
                visit(child_path, relative_directory / child.name)
                continue
            if not stat.S_ISREG(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a non-regular entry: {relative}",
                    RC_RECEIPT,
                )
            _, data = _stage5_read_regular_bytes(
                child_path, f"{label} entry {relative}"
            )
            total_bytes += len(data)
            entries.append(
                {
                    "path": relative,
                    "kind": "file",
                    "mode": mode,
                    "bytes": len(data),
                    "sha256": _sha256(data),
                }
            )

    visit(root, Path())
    try:
        final_root_metadata = root.lstat()
    except OSError as exc:
        raise ValidationError(
            f"{label} changed while it was read: {exc}", RC_RECEIPT
        ) from exc
    if (
        root_metadata.st_dev != final_root_metadata.st_dev
        or root_metadata.st_ino != final_root_metadata.st_ino
        or root_metadata.st_mtime_ns != final_root_metadata.st_mtime_ns
    ):
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    return entries, total_bytes


def _stage5_snapshot_descriptor(path: Path, label: str) -> dict[str, Any]:
    candidate = Path(path)
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise ValidationError(f"{label} is missing: {exc}", RC_RECEIPT) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise ValidationError(f"{label} is not a directory", RC_RECEIPT)
    entries, total_bytes = _stage5_snapshot_entries(candidate, label)
    return {
        "path": os.fspath(candidate.resolve()),
        "kind": "directory",
        "mode": stat.S_IMODE(metadata.st_mode),
        "sha256": _sha256(_canonical_bytes({"entries": entries})),
        "bytes": total_bytes,
        "device": metadata.st_dev,
        "inode": metadata.st_ino,
    }


@dataclass(frozen=True)
class _Stage5OwnedPath:
    path: Path
    device: int
    inode: int
    directory: bool


def _stage5_owned_identity(
    path: Path, metadata: os.stat_result, *, directory: bool
) -> _Stage5OwnedPath:
    expected = stat.S_ISDIR(metadata.st_mode) if directory else stat.S_ISREG(
        metadata.st_mode
    )
    if not expected:
        raise ValidationError(
            f"stage5 created artifact has an invalid type: {path}", RC_RECEIPT
        )
    return _Stage5OwnedPath(
        path=Path(path),
        device=metadata.st_dev,
        inode=metadata.st_ino,
        directory=directory,
    )


def _stage5_create_owned_directory(path: Path, *, mode: int) -> _Stage5OwnedPath:
    path = Path(path)
    path.mkdir(mode=mode, exist_ok=False)
    metadata = path.lstat()
    owned = _stage5_owned_identity(path, metadata, directory=True)
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
        try:
            opened = os.fstat(descriptor)
            if opened.st_dev != owned.device or opened.st_ino != owned.inode:
                raise ValidationError(
                    f"stage5 created directory identity changed: {path}", RC_RECEIPT
                )
            os.fchmod(descriptor, mode)
        finally:
            os.close(descriptor)
    except BaseException:
        _stage5_rollback_owned_paths([owned])
        raise
    return owned


def _stage5_copy_frozen_file(
    source: Path,
    target: Path,
    label: str,
    *,
    mode: int,
    expected_source_descriptor: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], list[_Stage5OwnedPath]]:
    source_descriptor = _stage5_file_descriptor(source, label)
    if (
        expected_source_descriptor is not None
        and source_descriptor != expected_source_descriptor
    ):
        raise ValidationError(f"{label} changed before it was frozen", RC_RECEIPT)
    _, data = _stage5_read_regular_bytes(Path(source_descriptor["path"]), label)
    if _sha256(data) != source_descriptor["sha256"]:
        raise ValidationError(f"{label} changed while it was read", RC_RECEIPT)
    owned: list[_Stage5OwnedPath] = []
    try:
        owned.append(_stage5_create_only_bytes(target, data, mode=mode))
        target_descriptor = _stage5_file_descriptor(target, f"frozen {label}")
        if (
            target_descriptor["sha256"] != source_descriptor["sha256"]
            or target_descriptor["bytes"] != source_descriptor["bytes"]
        ):
            raise ValidationError(f"frozen {label} copy sha mismatch", RC_RECEIPT)
        return target_descriptor, owned
    except BaseException:
        _stage5_rollback_owned_paths(owned)
        raise


def _stage5_copy_frozen_snapshot(
    source: Path,
    target: Path,
    label: str,
    *,
    expected_source_descriptor: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], list[_Stage5OwnedPath]]:
    source = _stage5_absolute_path(Path(source))
    source_descriptor = _stage5_snapshot_descriptor(source, label)
    if (
        expected_source_descriptor is not None
        and source_descriptor != expected_source_descriptor
    ):
        raise ValidationError(f"{label} changed before it was frozen", RC_RECEIPT)
    if target.exists() or target.is_symlink():
        raise ValidationError(f"frozen {label} already exists: {target}", RC_RECEIPT)
    owned: list[_Stage5OwnedPath] = []
    owned.append(
        _stage5_create_owned_directory(
            target, mode=stat.S_IMODE(source.stat().st_mode)
        )
    )

    def copy_directory(source_directory: Path, target_directory: Path) -> None:
        try:
            with os.scandir(source_directory) as entries_stream:
                children = sorted(entries_stream, key=lambda entry: entry.name)
        except OSError as exc:
            raise ValidationError(
                f"{label} cannot be copied: {exc}", RC_RECEIPT
            ) from exc
        for child in children:
            source_path = Path(child.path)
            target_path = target_directory / child.name
            metadata = source_path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise ValidationError(
                    f"{label} contains a symlink: {source_path}", RC_RECEIPT
                )
            if stat.S_ISDIR(metadata.st_mode):
                owned.append(
                    _stage5_create_owned_directory(
                        target_path, mode=stat.S_IMODE(metadata.st_mode)
                    )
                )
                copy_directory(source_path, target_path)
            elif stat.S_ISREG(metadata.st_mode):
                _, data = _stage5_read_regular_bytes(
                    source_path, f"{label} entry"
                )
                owned.append(
                    _stage5_create_only_bytes(
                        target_path, data, mode=stat.S_IMODE(metadata.st_mode)
                    )
                )
            else:
                raise ValidationError(
                    f"{label} contains a non-regular entry: {source_path}",
                    RC_RECEIPT,
                )

    try:
        copy_directory(source, target)
        if _stage5_snapshot_descriptor(source, label)["sha256"] != source_descriptor[
            "sha256"
        ]:
            raise ValidationError(f"{label} changed while it was copied", RC_RECEIPT)
        target_descriptor = _stage5_snapshot_descriptor(target, f"frozen {label}")
        if (
            target_descriptor["sha256"] != source_descriptor["sha256"]
            or target_descriptor["bytes"] != source_descriptor["bytes"]
        ):
            raise ValidationError(f"frozen {label} copy sha mismatch", RC_RECEIPT)
        return target_descriptor, owned
    except BaseException:
        _stage5_rollback_owned_paths(owned)
        raise


def _stage5_create_only_bytes(
    path: Path, data: bytes, *, mode: int = 0o600
) -> _Stage5OwnedPath:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags, mode)
    except FileExistsError as exc:
        raise ValidationError(
            f"stage5 frozen artifact already exists: {path}", RC_RECEIPT
        ) from exc
    try:
        owned = _stage5_owned_identity(
            path, os.fstat(descriptor), directory=False
        )
    except BaseException:
        os.close(descriptor)
        raise
    try:
        with os.fdopen(descriptor, "wb") as stream:
            os.fchmod(stream.fileno(), mode)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        _stage5_rollback_owned_paths([owned])
        raise
    return owned


def _stage5_create_only_json(
    path: Path, value: Mapping[str, Any]
) -> _Stage5OwnedPath:
    return _stage5_create_only_bytes(path, _canonical_bytes(dict(value)))


def _stage5_check_descriptor(
    descriptor: Mapping[str, Any], root: Path, label: str
) -> bytes:
    if not isinstance(descriptor, Mapping) or set(descriptor) != _STAGE5_DESCRIPTOR_KEYS:
        raise ValidationError(f"{label} descriptor keys are invalid", RC_RECEIPT)
    path_value = descriptor.get("path")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValidationError(f"{label} path is not absolute", RC_RECEIPT)
    candidate = Path(path_value)
    _stage5_path_below(candidate, root, label)
    before, data = _stage5_read_regular_bytes(candidate, label)
    if candidate.resolve() != Path(path_value):
        raise ValidationError(f"{label} path was replaced", RC_RECEIPT)
    current = {
        "path": os.fspath(candidate.resolve()),
        "kind": "file",
        "mode": stat.S_IMODE(before.st_mode),
        "sha256": _sha256(data),
        "bytes": before.st_size,
        "device": before.st_dev,
        "inode": before.st_ino,
    }
    for field in _STAGE5_DESCRIPTOR_KEYS:
        if current[field] != descriptor.get(field):
            raise ValidationError(f"{label} {field} changed", RC_RECEIPT)
    _stage5_digest(descriptor.get("sha256"), f"{label} hash")
    return data


def _stage5_check_snapshot_descriptor(
    descriptor: Mapping[str, Any], root: Path, label: str
) -> None:
    if not isinstance(descriptor, Mapping) or set(descriptor) != _STAGE5_DESCRIPTOR_KEYS:
        raise ValidationError(f"{label} descriptor keys are invalid", RC_RECEIPT)
    path_value = descriptor.get("path")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValidationError(f"{label} path is not absolute", RC_RECEIPT)
    candidate = Path(path_value)
    _stage5_path_below(candidate, root, label)
    current = _stage5_snapshot_descriptor(candidate, label)
    for field in _STAGE5_DESCRIPTOR_KEYS:
        if current.get(field) != descriptor.get(field):
            raise ValidationError(f"{label} {field} changed", RC_RECEIPT)


def _stage5_digest(value: Any, label: str) -> str:
    if not isinstance(value, str) or re.fullmatch(r"[0-9a-f]{64}", value) is None:
        raise ValidationError(f"{label} is not a sha256", RC_RECEIPT)
    return value


def _stage5_stop_process_tree(
    process: subprocess.Popen[bytes],
) -> tuple[bytes, bytes]:
    def signal_group(number: int) -> None:
        try:
            os.killpg(process.pid, number)
        except (ProcessLookupError, PermissionError):
            try:
                if number == signal.SIGTERM:
                    process.terminate()
                else:
                    process.kill()
            except ProcessLookupError:
                pass

    signal_group(signal.SIGTERM)
    try:
        stdout, stderr = process.communicate(timeout=1.0)
        return stdout or b"", stderr or b""
    except subprocess.TimeoutExpired:
        signal_group(signal.SIGKILL)
    try:
        stdout, stderr = process.communicate(timeout=2.0)
        return stdout or b"", stderr or b""
    except subprocess.TimeoutExpired:
        try:
            process.kill()
        except ProcessLookupError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=2.0)
            return stdout or b"", stderr or b""
        except subprocess.TimeoutExpired:
            return b"", b"stage5 process termination timed out"


def _stage5_version_probe(binary: Path, *, cwd: Path, label: str) -> str:
    process: subprocess.Popen[bytes] | None = None
    try:
        process = subprocess.Popen(
            [os.fspath(binary), "--version"],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=_clean_environment({"HOME": "/nonexistent"}),
            start_new_session=True,
        )
        try:
            stdout, stderr = process.communicate(
                timeout=STAGE5_AUTHOR_REPLAYER_VERSION_PROBE_TIMEOUT_S
            )
        except subprocess.TimeoutExpired as exc:
            _stage5_stop_process_tree(process)
            raise ValidationError(
                f"{label} version probe timed out", RC_ROUTING
            ) from exc
        if process.returncode != 0:
            raise ValidationError(
                f"{label} version probe failed; exit_code={process.returncode}; "
                f"stderr_bytes={len(stderr)}; stderr_sha256={_sha256(stderr)}",
                RC_ROUTING,
            )
        version = stdout.decode("utf-8", "replace").strip()
        if not version:
            raise ValidationError(f"{label} version output is empty", RC_ROUTING)
        return version
    finally:
        if process is not None and process.poll() is None:
            _stage5_stop_process_tree(process)


def _stage5_relative_root(value: Any) -> str:
    if not isinstance(value, str) or not value or value in {"."}:
        raise ValidationError("stage5 application root is empty or dot", RC_ROUTING)
    if value.startswith("/") or "\\" in value or "\x00" in value:
        raise ValidationError("stage5 application root is not POSIX relative", RC_ROUTING)
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValidationError("stage5 application root can escape the snapshot", RC_ROUTING)
    return value


def _stage5_application_root(snapshot: Path, relative_root: str) -> Path:
    relative_root = _stage5_relative_root(relative_root)
    candidate = snapshot.joinpath(*relative_root.split("/"))
    try:
        candidate.resolve().relative_to(snapshot.resolve())
    except ValueError as exc:
        raise ValidationError(
            "stage5 application root can escape the frozen snapshot", RC_ROUTING
        ) from exc
    current = snapshot
    for part in relative_root.split("/"):
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise ValidationError(
                f"stage5 application root is missing: {relative_root}: {exc}",
                RC_ROUTING,
            ) from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
            raise ValidationError(
                "stage5 application root contains a symlink or non-directory",
                RC_ROUTING,
            )
    return current


def _stage5_git_argv(git_binary: Path, *, check: bool) -> list[str]:
    argv = [os.fspath(git_binary), "apply"]
    if check:
        argv.append("--check")
    argv.extend(("--whitespace=nowarn", "-"))
    return argv


def _stage5_expected_downstream_argv(
    role: str, pin: Mapping[str, Any]
) -> list[str]:
    if role not in {"review", "fix"}:
        raise ValidationError("stage5 downstream role is invalid", RC_ROUTING)
    argv = [
        "codex",
        "exec",
        "-m",
        str(pin["requested_model"]),
        "-c",
        f"model_reasoning_effort={pin['requested_effort']}",
        "-s",
        "read-only",
        "--json",
    ]
    _normalized_exec_argv(
        argv, str(pin["requested_model"]), str(pin["requested_effort"])
    )
    return argv


def _stage5_validate_role_pin(value: Any, role: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE5_ROLE_PIN_KEYS:
        raise ValidationError(f"stage5 {role} pin keys are invalid", RC_ROUTING)
    model = value.get("requested_model")
    effort = value.get("requested_effort")
    if model not in MODEL_ALLOWLIST:
        raise ValidationError(f"stage5 {role} model is not allowed", RC_ROUTING)
    if effort not in _STAGE5_EFFORTS:
        raise ValidationError(f"stage5 {role} effort is not allowed", RC_ROUTING)
    return {"requested_model": model, "requested_effort": effort}


def _stage5_receipt_policy(pins: Mapping[str, Mapping[str, Any]]) -> dict[str, Any]:
    return {
        "version": 1,
        "receipt_kind": _STAGE5_DOWNSTREAM_RECEIPT_KIND,
        "argv_match": "exact",
        "stdin_match": "sha256",
        "output_match": "regular-nonempty-sha256",
        "previous_receipt_match": "sha256",
        "role_argv": {
            role: _stage5_expected_downstream_argv(role, pins[role])
            for role in ("review", "fix")
        },
    }


def _stage5_validate_receipt_policy(
    value: Any, pins: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE5_RECEIPT_POLICY_KEYS:
        raise ValidationError("stage5 receipt policy keys are invalid", RC_ROUTING)
    expected = _stage5_receipt_policy(pins)
    if value != expected:
        raise ValidationError("stage5 receipt policy does not match pins", RC_ROUTING)
    return dict(value)


def _stage5_validate_acceptance(value: Mapping[str, Any], label: str) -> None:
    if value.get("task_acceptance_status") != "unbound":
        raise ValidationError(f"{label} task acceptance must remain unbound", RC_ROUTING)
    if value.get("fix_gate_eligible") is not False:
        raise ValidationError(f"{label} fix gate eligibility must remain false", RC_ROUTING)
    if value.get("routing_evidence_eligible") is not False:
        raise ValidationError(
            f"{label} routing evidence eligibility must remain false", RC_ROUTING
        )


def _stage5_validate_git_pin(value: Any, run_root: Path) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE5_GIT_PIN_KEYS:
        raise ValidationError("stage5 Git pin keys are invalid", RC_ROUTING)
    git_descriptor = value.get("git")
    if not isinstance(git_descriptor, dict):
        raise ValidationError("stage5 Git descriptor is malformed", RC_ROUTING)
    _stage5_check_descriptor(git_descriptor, run_root, "stage5 frozen Git binary")
    _stage5_digest(value.get("git_sha256"), "stage5 Git hash")
    if value["git_sha256"] != git_descriptor.get("sha256"):
        raise ValidationError("stage5 Git hash does not match descriptor", RC_ROUTING)
    version = value.get("git_version")
    if not isinstance(version, str) or not version.strip():
        raise ValidationError("stage5 Git version is missing", RC_ROUTING)
    git_path = Path(str(git_descriptor["path"]))
    if value.get("check_argv") != _stage5_git_argv(git_path, check=True):
        raise ValidationError("stage5 Git check argv mismatch", RC_ROUTING)
    if value.get("apply_argv") != _stage5_git_argv(git_path, check=False):
        raise ValidationError("stage5 Git apply argv mismatch", RC_ROUTING)
    return dict(value)


def _stage5_validate_contract(value: Any, *, run_root: Path) -> dict[str, Any]:
    _stage5_reject_generic_correctness_keys(value, "stage5 contract")
    if not isinstance(value, dict) or set(value) != _STAGE5_CONTRACT_KEYS:
        raise ValidationError("stage5 contract keys are invalid", RC_ROUTING)
    if value.get("schema_version") != STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION:
        raise ValidationError("stage5 contract schema version mismatch", RC_ROUTING)
    if value.get("contract_kind") != _STAGE5_CONTRACT_KIND:
        raise ValidationError("stage5 contract kind mismatch", RC_ROUTING)
    if value.get("stage") != "stage5-author":
        raise ValidationError("stage5 contract stage mismatch", RC_ROUTING)
    sources_value = value.get("source_descriptors")
    if (
        not isinstance(sources_value, dict)
        or set(sources_value) != _STAGE5_SOURCE_DESCRIPTOR_KEYS
    ):
        raise ValidationError("stage5 source descriptor keys are invalid", RC_ROUTING)
    sources = {
        name: _stage5_validate_source_descriptor(
            sources_value[name], f"stage5 source {name}"
        )
        for name in _STAGE5_SOURCE_DESCRIPTOR_KEYS
    }
    for name, expected_kind in {
        "plan": "file",
        "author_output": "file",
        "snapshot": "directory",
        "git": "file",
    }.items():
        if sources[name]["kind"] != expected_kind:
            raise ValidationError(
                f"stage5 source {name} kind mismatch", RC_ROUTING
            )
    plan = value.get("frozen_plan")
    if not isinstance(plan, dict):
        raise ValidationError("stage5 frozen plan descriptor is malformed", RC_ROUTING)
    _stage5_check_descriptor(plan, run_root, "stage5 frozen plan")
    _stage5_digest(value.get("plan_input_hash"), "stage5 plan input hash")
    if value["plan_input_hash"] != plan.get("sha256"):
        raise ValidationError("stage5 plan input hash mismatch", RC_ROUTING)
    author = value.get("frozen_author_output")
    if not isinstance(author, dict) or set(author) != _STAGE5_AUTHOR_OUTPUT_KEYS:
        raise ValidationError("stage5 author output keys are invalid", RC_ROUTING)
    if author.get("format") != "git-diff-v1" or not isinstance(author.get("artifact"), dict):
        raise ValidationError("stage5 author output format is invalid", RC_ROUTING)
    _stage5_check_descriptor(author["artifact"], run_root, "stage5 frozen author output")
    _stage5_digest(value.get("author_output_hash"), "stage5 author output hash")
    if value["author_output_hash"] != author["artifact"].get("sha256"):
        raise ValidationError("stage5 author output hash mismatch", RC_ROUTING)
    target = value.get("application_target")
    if not isinstance(target, dict) or set(target) != _STAGE5_APPLICATION_TARGET_KEYS:
        raise ValidationError("stage5 application target keys are invalid", RC_ROUTING)
    snapshot = target.get("snapshot")
    if not isinstance(snapshot, dict):
        raise ValidationError("stage5 snapshot descriptor is malformed", RC_ROUTING)
    _stage5_check_snapshot_descriptor(snapshot, run_root, "stage5 frozen snapshot")
    target_root = _stage5_application_root(
        Path(str(snapshot["path"])), _stage5_relative_root(target.get("relative_root"))
    )
    _stage5_digest(
        target.get("pre_application_tree_sha256"), "stage5 pre-application tree hash"
    )
    observed_pre = _stage5_snapshot_descriptor(
        target_root, "stage5 application target"
    )["sha256"]
    if observed_pre != target["pre_application_tree_sha256"]:
        raise ValidationError("stage5 application target tree hash mismatch", RC_ROUTING)
    apparatus = _stage5_validate_git_pin(value.get("application_apparatus"), run_root)
    pins_value = value.get("downstream_pins")
    if not isinstance(pins_value, dict) or set(pins_value) != {"review", "fix"}:
        raise ValidationError("stage5 downstream pin roles are invalid", RC_ROUTING)
    pins = {
        role: _stage5_validate_role_pin(pins_value[role], role)
        for role in ("review", "fix")
    }
    limit = value.get("fix_pass_limit")
    if (
        isinstance(limit, bool)
        or not isinstance(limit, int)
        or not 0 <= limit <= STAGE5_AUTHOR_REPLAYER_MAX_FIX_PASSES
    ):
        raise ValidationError("stage5 fix pass limit is outside the cap", RC_ROUTING)
    policy = _stage5_validate_receipt_policy(value.get("receipt_policy"), pins)
    _stage5_validate_acceptance(value, "stage5 contract")
    normalized = dict(value)
    normalized["source_descriptors"] = sources
    normalized["frozen_plan"] = dict(plan)
    normalized["frozen_author_output"] = dict(author)
    normalized["application_target"] = dict(target)
    normalized["application_apparatus"] = apparatus
    normalized["downstream_pins"] = pins
    normalized["receipt_policy"] = policy
    return normalized


def _stage5_run_git_apply(
    argv: Sequence[str], *, cwd: Path, patch_bytes: bytes, label: str
) -> None:
    process: subprocess.Popen[bytes] | None = None
    environment = _clean_environment({"HOME": "/nonexistent"})
    environment.update(
        {"GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": "/dev/null"}
    )
    try:
        process = subprocess.Popen(
            list(argv),
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=environment,
            start_new_session=True,
        )
        try:
            _stdout, stderr = process.communicate(
                patch_bytes, timeout=STAGE5_AUTHOR_REPLAYER_GIT_TIMEOUT_S
            )
        except subprocess.TimeoutExpired as exc:
            _stage5_stop_process_tree(process)
            raise ValidationError(f"stage5 {label} timed out", RC_RECEIPT) from exc
        if process.returncode != 0:
            raise ValidationError(
                f"stage5 {label} failed; exit_code={process.returncode}; "
                f"stderr_bytes={len(stderr)}; stderr_sha256={_sha256(stderr)}",
                RC_RECEIPT,
            )
    finally:
        if process is not None and process.poll() is None:
            _stage5_stop_process_tree(process)


def _stage5_apply_frozen_patch(
    *,
    run_root: Path,
    snapshot_descriptor: Mapping[str, Any],
    relative_root: str,
    patch_bytes: bytes,
    git_binary: Path,
) -> dict[str, Any]:
    clone = run_root / f".stage5-application-{uuid.uuid4().hex}"
    try:
        _stage5_copy_frozen_snapshot(
            Path(str(snapshot_descriptor["path"])),
            clone,
            "stage5 application snapshot",
            expected_source_descriptor=snapshot_descriptor,
        )
        clone.chmod(0o700)
        target = _stage5_application_root(clone, relative_root)
        pre = _stage5_snapshot_descriptor(target, "stage5 validation target")["sha256"]
        check_argv = _stage5_git_argv(git_binary, check=True)
        apply_argv = _stage5_git_argv(git_binary, check=False)
        _stage5_run_git_apply(
            check_argv, cwd=target, patch_bytes=patch_bytes, label="Git apply check"
        )
        if _stage5_snapshot_descriptor(target, "stage5 validation target")["sha256"] != pre:
            raise ValidationError("stage5 Git check changed the target tree", RC_RECEIPT)
        _stage5_run_git_apply(
            apply_argv, cwd=target, patch_bytes=patch_bytes, label="Git apply"
        )
        post = _stage5_snapshot_descriptor(target, "stage5 validation target")["sha256"]
        _stage5_check_snapshot_descriptor(
            snapshot_descriptor, run_root, "stage5 frozen snapshot"
        )
        return {
            "pre_tree_sha256": pre,
            "post_tree_sha256": post,
            "check_argv": check_argv,
            "apply_argv": apply_argv,
        }
    finally:
        try:
            shutil.rmtree(clone)
        except FileNotFoundError:
            pass


def _stage5_integrity_path(contract_path: Path) -> Path:
    return contract_path.with_name(contract_path.name + ".integrity.json")


def _stage5_rollback_owned_paths(paths: Sequence[_Stage5OwnedPath]) -> None:
    """Remove only identities created successfully by this invocation."""
    for owned in reversed(paths):
        try:
            metadata = owned.path.lstat()
        except OSError:
            continue
        observed_directory = stat.S_ISDIR(metadata.st_mode) and not stat.S_ISLNK(
            metadata.st_mode
        )
        if (
            metadata.st_dev != owned.device
            or metadata.st_ino != owned.inode
            or observed_directory != owned.directory
        ):
            continue
        try:
            if owned.directory:
                owned.path.rmdir()
            else:
                owned.path.unlink()
        except OSError:
            pass


def freeze_stage5_author_replayer(
    plan_input: Path,
    author_output: Path,
    output: Path,
    *,
    snapshot: Path,
    application_root: str,
    git_binary: Path,
    review_model: str,
    review_effort: str,
    fix_model: str,
    fix_effort: str,
    fix_pass_limit: int,
) -> dict[str, Any]:
    """Register frozen stage5 inputs after isolated Git-patch validation."""
    contract_path = _stage5_absolute_path(Path(output))
    run_root = contract_path.parent.resolve()
    integrity_path = _stage5_integrity_path(contract_path)
    frozen_plan_path = run_root / "stage5-plan-input"
    frozen_author_path = run_root / "stage5-author-output.patch"
    frozen_snapshot_path = run_root / "stage5-snapshot"
    apparatus_root = run_root / "stage5-apparatus"
    frozen_git_path = apparatus_root / "git"
    candidates = (
        contract_path,
        integrity_path,
        frozen_plan_path,
        frozen_author_path,
        frozen_snapshot_path,
        apparatus_root,
    )
    for candidate in candidates:
        if candidate.exists() or candidate.is_symlink():
            raise ValidationError(
                f"stage5 frozen artifact already exists: {candidate}", RC_ROUTING
            )
    relative_root = _stage5_relative_root(application_root)
    plan_source = _stage5_file_descriptor(plan_input, "stage5 plan input")
    author_source = _stage5_file_descriptor(author_output, "stage5 author output")
    snapshot_source = _stage5_snapshot_descriptor(snapshot, "stage5 snapshot")
    git_source = _stage5_file_descriptor(git_binary, "stage5 Git binary")
    _, author_bytes = _stage5_read_regular_bytes(
        Path(str(author_source["path"])), "stage5 author output"
    )
    if not author_bytes:
        raise ValidationError("stage5 author output is empty", RC_ROUTING)
    _stage5_application_root(Path(str(snapshot_source["path"])), relative_root)
    owned: list[_Stage5OwnedPath] = []
    try:
        frozen_plan, created = _stage5_copy_frozen_file(
            plan_input,
            frozen_plan_path,
            "stage5 plan input",
            mode=0o600,
            expected_source_descriptor=plan_source,
        )
        owned.extend(created)
        frozen_author, created = _stage5_copy_frozen_file(
            author_output,
            frozen_author_path,
            "stage5 author output",
            mode=0o600,
            expected_source_descriptor=author_source,
        )
        owned.extend(created)
        frozen_snapshot, created = _stage5_copy_frozen_snapshot(
            snapshot,
            frozen_snapshot_path,
            "stage5 snapshot",
            expected_source_descriptor=snapshot_source,
        )
        owned.extend(created)
        owned.append(_stage5_create_owned_directory(apparatus_root, mode=0o700))
        frozen_git, created = _stage5_copy_frozen_file(
            git_binary,
            frozen_git_path,
            "stage5 Git binary",
            mode=0o700,
            expected_source_descriptor=git_source,
        )
        owned.extend(created)
        git_version = _stage5_version_probe(
            frozen_git_path, cwd=apparatus_root, label="stage5 Git binary"
        )
        target = _stage5_application_root(frozen_snapshot_path, relative_root)
        pre_tree = _stage5_snapshot_descriptor(
            target, "stage5 application target"
        )["sha256"]
        observation = _stage5_apply_frozen_patch(
            run_root=run_root,
            snapshot_descriptor=frozen_snapshot,
            relative_root=relative_root,
            patch_bytes=author_bytes,
            git_binary=frozen_git_path,
        )
        if observation["pre_tree_sha256"] != pre_tree:
            raise ValidationError("stage5 validation pre-tree hash mismatch", RC_RECEIPT)
        pins = {
            "review": _stage5_validate_role_pin(
                {"requested_model": review_model, "requested_effort": review_effort},
                "review",
            ),
            "fix": _stage5_validate_role_pin(
                {"requested_model": fix_model, "requested_effort": fix_effort},
                "fix",
            ),
        }
        apparatus = {
            "git": frozen_git,
            "git_sha256": frozen_git["sha256"],
            "git_version": git_version,
            "check_argv": _stage5_git_argv(frozen_git_path, check=True),
            "apply_argv": _stage5_git_argv(frozen_git_path, check=False),
        }
        contract = Stage5AuthorReplayerContract(
            schema_version=STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
            contract_kind=_STAGE5_CONTRACT_KIND,
            stage="stage5-author",
            source_descriptors={
                "plan": plan_source,
                "author_output": author_source,
                "snapshot": snapshot_source,
                "git": git_source,
            },
            frozen_plan=frozen_plan,
            plan_input_hash=frozen_plan["sha256"],
            frozen_author_output={"artifact": frozen_author, "format": "git-diff-v1"},
            application_target={
                "snapshot": frozen_snapshot,
                "relative_root": relative_root,
                "pre_application_tree_sha256": pre_tree,
            },
            author_output_hash=frozen_author["sha256"],
            application_apparatus=apparatus,
            downstream_pins=pins,
            fix_pass_limit=fix_pass_limit,
            receipt_policy=_stage5_receipt_policy(pins),
        ).as_dict()
        contract = _stage5_validate_contract(contract, run_root=run_root)
        contract_bytes = _canonical_bytes(contract)
        integrity = {
            "schema_version": STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
            "integrity_kind": _STAGE5_INTEGRITY_KIND,
            "contract_path": os.fspath(contract_path),
            "contract_sha256": _sha256(contract_bytes),
            "source_plan": plan_source,
            "source_author_output": author_source,
            "source_snapshot": snapshot_source,
            "source_git": git_source,
            "plan_input_hash": frozen_plan["sha256"],
            "author_output_hash": frozen_author["sha256"],
            "frozen_snapshot_sha256": frozen_snapshot["sha256"],
            "git_sha256": frozen_git["sha256"],
            "application_target_sha256": _sha256(
                _canonical_bytes(contract["application_target"])
            ),
            "task_acceptance_status": "unbound",
            "fix_gate_eligible": False,
            "routing_evidence_eligible": False,
        }
        _stage5_reject_generic_correctness_keys(integrity, "stage5 integrity")
        owned.append(_stage5_create_only_bytes(contract_path, contract_bytes))
        owned.append(_stage5_create_only_json(integrity_path, integrity))
        return contract
    except BaseException:
        _stage5_rollback_owned_paths(owned)
        raise


def _stage5_read_json_file(path: Path, label: str) -> tuple[dict[str, Any], bytes]:
    descriptor = _stage5_file_descriptor(path, label)
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(f"{label} is not valid JSON: {exc}", RC_RECEIPT) from exc
    if not isinstance(value, dict):
        raise ValidationError(f"{label} is not a JSON object", RC_RECEIPT)
    if descriptor["sha256"] != _sha256(raw):
        raise ValidationError(f"{label} hash changed while reading", RC_RECEIPT)
    if _stage5_file_descriptor(path, label) != descriptor:
        raise ValidationError(f"{label} changed while reading", RC_RECEIPT)
    return value, raw


def _stage5_validate_source_descriptor(
    value: Any, label: str
) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != _STAGE5_DESCRIPTOR_KEYS:
        raise ValidationError(f"{label} is malformed", RC_RECEIPT)
    path_value = value.get("path")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        raise ValidationError(f"{label} path is not absolute", RC_RECEIPT)
    if value.get("kind") not in {"file", "directory"}:
        raise ValidationError(f"{label} kind is invalid", RC_RECEIPT)
    mode = value.get("mode")
    if type(mode) is not int or not 0 <= mode <= 0o7777:
        raise ValidationError(f"{label} mode is invalid", RC_RECEIPT)
    _stage5_digest(value.get("sha256"), f"{label} hash")
    for field in ("bytes", "device", "inode"):
        field_value = value.get(field)
        if type(field_value) is not int or field_value < 0:
            raise ValidationError(
                f"{label} {field} is not a nonnegative integer", RC_RECEIPT
            )
    return dict(value)


def _stage5_validate_integrity(
    value: Any,
    *,
    contract_path: Path,
    contract: Mapping[str, Any],
    contract_raw: bytes,
) -> None:
    _stage5_reject_generic_correctness_keys(value, "stage5 integrity")
    if not isinstance(value, dict) or set(value) != _STAGE5_INTEGRITY_KEYS:
        raise ValidationError("stage5 integrity keys are invalid", RC_RECEIPT)
    if value.get("schema_version") != STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION:
        raise ValidationError("stage5 integrity schema version mismatch", RC_RECEIPT)
    if value.get("integrity_kind") != _STAGE5_INTEGRITY_KIND:
        raise ValidationError("stage5 integrity kind mismatch", RC_RECEIPT)
    if value.get("contract_path") != os.fspath(contract_path):
        raise ValidationError("stage5 integrity contract path mismatch", RC_RECEIPT)
    if value.get("contract_sha256") != _sha256(contract_raw):
        raise ValidationError("stage5 integrity contract hash mismatch", RC_RECEIPT)
    source_bindings = {
        "source_plan": (
            contract["source_descriptors"]["plan"],
            contract["frozen_plan"],
        ),
        "source_author_output": (
            contract["source_descriptors"]["author_output"],
            contract["frozen_author_output"]["artifact"],
        ),
        "source_snapshot": (
            contract["source_descriptors"]["snapshot"],
            contract["application_target"]["snapshot"],
        ),
        "source_git": (
            contract["source_descriptors"]["git"],
            contract["application_apparatus"]["git"],
        ),
    }
    for field, (registered_descriptor, frozen_descriptor) in source_bindings.items():
        descriptor = _stage5_validate_source_descriptor(
            value.get(field), f"stage5 integrity {field}"
        )
        for leaf in _STAGE5_DESCRIPTOR_KEYS:
            if descriptor[leaf] != registered_descriptor.get(leaf):
                raise ValidationError(
                    f"stage5 integrity {field} {leaf} mismatch", RC_RECEIPT
                )
        for leaf in ("sha256", "bytes"):
            if descriptor[leaf] != frozen_descriptor.get(leaf):
                raise ValidationError(
                    f"stage5 integrity {field} {leaf} mismatch", RC_RECEIPT
                )
    expected = {
        "plan_input_hash": contract["plan_input_hash"],
        "author_output_hash": contract["author_output_hash"],
        "frozen_snapshot_sha256": contract["application_target"]["snapshot"]["sha256"],
        "git_sha256": contract["application_apparatus"]["git_sha256"],
        "application_target_sha256": _sha256(
            _canonical_bytes(contract["application_target"])
        ),
    }
    for field, expected_value in expected.items():
        _stage5_digest(value.get(field), f"stage5 integrity {field}")
        if value[field] != expected_value:
            raise ValidationError(f"stage5 integrity {field} mismatch", RC_RECEIPT)
    _stage5_validate_acceptance(value, "stage5 integrity")


def _load_stage5_author_replayer_contract(
    contract_path: Path, run_root: Path
) -> tuple[dict[str, Any], bytes]:
    run_root = Path(run_root).resolve()
    contract_path = _stage5_absolute_path(Path(contract_path))
    _stage5_path_below(contract_path, run_root, "stage5 contract")
    contract, raw = _stage5_read_json_file(contract_path, "stage5 contract")
    contract = _stage5_validate_contract(contract, run_root=run_root)
    integrity, _ = _stage5_read_json_file(
        _stage5_integrity_path(contract_path), "stage5 integrity"
    )
    _stage5_validate_integrity(
        integrity,
        contract_path=contract_path,
        contract=contract,
        contract_raw=raw,
    )
    return contract, raw


def _stage5_validate_application_receipt(
    value: Any,
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    expected_post_tree_sha256: str,
) -> dict[str, Any]:
    _stage5_reject_generic_correctness_keys(value, "stage5 application receipt")
    if not isinstance(value, dict) or set(value) != _STAGE5_APPLICATION_RECEIPT_KEYS:
        raise ValidationError("stage5 application receipt keys are invalid", RC_RECEIPT)
    expected = {
        "schema_version": STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": _STAGE5_APPLICATION_RECEIPT_KIND,
        "contract_sha256": contract_sha256,
        "plan_input_hash": contract["plan_input_hash"],
        "author_output_hash": contract["author_output_hash"],
        "application_target_sha256": _sha256(
            _canonical_bytes(contract["application_target"])
        ),
        "pre_tree_sha256": contract["application_target"]["pre_application_tree_sha256"],
        "post_tree_sha256": expected_post_tree_sha256,
        "git_sha256": contract["application_apparatus"]["git_sha256"],
        "git_version": contract["application_apparatus"]["git_version"],
        "check_argv": contract["application_apparatus"]["check_argv"],
        "apply_argv": contract["application_apparatus"]["apply_argv"],
        "check_exit_code": 0,
        "apply_exit_code": 0,
        "timed_out": False,
        "receipt_status": "mechanically-valid",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise ValidationError(
                f"stage5 application receipt {field} mismatch", RC_RECEIPT
            )
    _stage5_digest(value.get("post_tree_sha256"), "stage5 post-application tree hash")
    return dict(value)


def validate_stage5_author_application(
    *, contract_path: Path, run_root: Path, receipt_path: Path
) -> dict[str, Any]:
    run_root = Path(run_root).resolve()
    receipt_path = _stage5_absolute_path(Path(receipt_path))
    _stage5_path_below(receipt_path, run_root, "stage5 application receipt")
    if receipt_path.exists() or receipt_path.is_symlink():
        raise ValidationError(
            f"stage5 application receipt already exists: {receipt_path}", RC_RECEIPT
        )
    contract, raw = _load_stage5_author_replayer_contract(contract_path, run_root)
    git_pin = contract["application_apparatus"]
    git_binary = Path(git_pin["git"]["path"])
    observed_version = _stage5_version_probe(
        git_binary, cwd=git_binary.parent, label="stage5 frozen Git binary"
    )
    if observed_version != git_pin["git_version"]:
        raise ValidationError("stage5 Git version changed", RC_RECEIPT)
    patch_bytes = _stage5_check_descriptor(
        contract["frozen_author_output"]["artifact"],
        run_root,
        "stage5 frozen author output",
    )
    observation = _stage5_apply_frozen_patch(
        run_root=run_root,
        snapshot_descriptor=contract["application_target"]["snapshot"],
        relative_root=contract["application_target"]["relative_root"],
        patch_bytes=patch_bytes,
        git_binary=git_binary,
    )
    receipt = {
        "schema_version": STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": _STAGE5_APPLICATION_RECEIPT_KIND,
        "contract_sha256": _sha256(raw),
        "plan_input_hash": contract["plan_input_hash"],
        "author_output_hash": contract["author_output_hash"],
        "application_target_sha256": _sha256(
            _canonical_bytes(contract["application_target"])
        ),
        "pre_tree_sha256": observation["pre_tree_sha256"],
        "post_tree_sha256": observation["post_tree_sha256"],
        "git_sha256": git_pin["git_sha256"],
        "git_version": git_pin["git_version"],
        "check_argv": observation["check_argv"],
        "apply_argv": observation["apply_argv"],
        "check_exit_code": 0,
        "apply_exit_code": 0,
        "timed_out": False,
        "receipt_status": "mechanically-valid",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    receipt = _stage5_validate_application_receipt(
        receipt,
        contract=contract,
        contract_sha256=_sha256(raw),
        expected_post_tree_sha256=observation["post_tree_sha256"],
    )
    _stage5_create_only_json(receipt_path, receipt)
    return receipt


def _stage5_bounded_path(path: Path, run_root: Path, label: str) -> Path:
    candidate = _stage5_absolute_path(Path(path))
    _stage5_path_below(candidate, run_root, label)
    return candidate


def _stage5_bounded_regular_bytes(
    path: Path,
    run_root: Path,
    label: str,
    *,
    nonempty: bool,
) -> tuple[Path, bytes]:
    candidate = _stage5_bounded_path(path, run_root, label)
    _, data = _stage5_read_regular_bytes(candidate, label)
    if nonempty and not data:
        raise ValidationError(f"{label} is empty", RC_RECEIPT)
    return candidate, data


def _stage5_validate_role_pass(
    role: Any,
    pass_index: Any,
    limit: int,
    label: str,
) -> tuple[str, int]:
    if role not in {"review", "fix"}:
        raise ValidationError(f"{label} role is invalid", RC_RECEIPT)
    if isinstance(pass_index, bool) or not isinstance(pass_index, int):
        raise ValidationError(f"{label} pass index is invalid", RC_RECEIPT)
    if role == "review":
        if pass_index != 0:
            raise ValidationError(
                f"{label} review pass index must be zero", RC_RECEIPT
            )
    elif not 1 <= pass_index <= limit:
        raise ValidationError(
            f"{label} fix pass index exceeds cap", RC_RECEIPT
        )
    return role, pass_index


def _stage5_validate_downstream_receipt_record(
    value: Any,
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    expected_role: str,
    expected_pass_index: int,
    stdin_sha256: str,
    output_bytes: int,
    output_sha256: str,
    previous_receipt_sha256: str,
) -> dict[str, Any]:
    _stage5_reject_generic_correctness_keys(value, "stage5 downstream receipt")
    if not isinstance(value, dict) or set(value) != _STAGE5_DOWNSTREAM_RECEIPT_KEYS:
        raise ValidationError("stage5 downstream receipt keys are invalid", RC_RECEIPT)
    pin = contract["downstream_pins"][expected_role]
    expected = {
        "schema_version": STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION,
        "receipt_kind": _STAGE5_DOWNSTREAM_RECEIPT_KIND,
        "contract_sha256": contract_sha256,
        "role": expected_role,
        "pass_index": expected_pass_index,
        "author_output_hash": contract["author_output_hash"],
        "application_target_sha256": _sha256(
            _canonical_bytes(contract["application_target"])
        ),
        "requested_model": pin["requested_model"],
        "requested_effort": pin["requested_effort"],
        "argv": contract["receipt_policy"]["role_argv"][expected_role],
        "stdin_sha256": stdin_sha256,
        "output": {
            "regular": True,
            "bytes": output_bytes,
            "sha256": output_sha256,
        },
        "output_sha256": output_sha256,
        "previous_receipt_sha256": previous_receipt_sha256,
        "exit_code": 0,
        "timed_out": False,
        "receipt_status": "mechanically-valid",
        "task_acceptance_status": "unbound",
        "fix_gate_eligible": False,
        "routing_evidence_eligible": False,
    }
    for field, expected_value in expected.items():
        if value.get(field) != expected_value:
            raise ValidationError(
                f"stage5 downstream receipt {field} mismatch", RC_RECEIPT
            )
    _stage5_validate_acceptance(value, "stage5 downstream receipt")
    return dict(value)


def _stage5_validate_previous_receipt(
    value: Any,
    raw: bytes,
    *,
    contract: Mapping[str, Any],
    contract_sha256: str,
    role: str,
    pass_index: int,
) -> str:
    previous_sha256 = _sha256(raw)
    if role == "review":
        if not isinstance(value, dict) or value.get("receipt_kind") != (
            _STAGE5_APPLICATION_RECEIPT_KIND
        ):
            raise ValidationError(
                "stage5 previous receipt topology mismatch", RC_RECEIPT
            )
        post_sha256 = _stage5_digest(
            value.get("post_tree_sha256"), "stage5 previous application post tree"
        )
        _stage5_validate_application_receipt(
            value,
            contract=contract,
            contract_sha256=contract_sha256,
            expected_post_tree_sha256=post_sha256,
        )
        return previous_sha256

    previous_role = "review" if pass_index == 1 else "fix"
    previous_pass_index = 0 if pass_index == 1 else pass_index - 1
    if not isinstance(value, dict) or value.get("receipt_kind") != (
        _STAGE5_DOWNSTREAM_RECEIPT_KIND
    ):
        raise ValidationError("stage5 previous receipt topology mismatch", RC_RECEIPT)
    output = value.get("output")
    if not isinstance(output, dict) or set(output) != _STAGE5_DOWNSTREAM_OUTPUT_KEYS:
        raise ValidationError(
            "stage5 previous downstream output descriptor is invalid", RC_RECEIPT
        )
    output_bytes = output.get("bytes")
    if (
        output.get("regular") is not True
        or isinstance(output_bytes, bool)
        or not isinstance(output_bytes, int)
        or output_bytes <= 0
    ):
        raise ValidationError(
            "stage5 previous downstream output is not regular and nonempty",
            RC_RECEIPT,
        )
    stdin_sha256 = _stage5_digest(
        value.get("stdin_sha256"), "stage5 previous downstream stdin"
    )
    output_sha256 = _stage5_digest(
        output.get("sha256"), "stage5 previous downstream output"
    )
    nested_previous_sha256 = _stage5_digest(
        value.get("previous_receipt_sha256"),
        "stage5 previous downstream previous receipt",
    )
    _stage5_validate_downstream_receipt_record(
        value,
        contract=contract,
        contract_sha256=contract_sha256,
        expected_role=previous_role,
        expected_pass_index=previous_pass_index,
        stdin_sha256=stdin_sha256,
        output_bytes=output_bytes,
        output_sha256=output_sha256,
        previous_receipt_sha256=nested_previous_sha256,
    )
    return previous_sha256


def validate_stage5_downstream_receipt(
    *,
    contract_path: Path,
    run_root: Path,
    receipt_path: Path,
    expected_role: str,
    expected_pass_index: int,
    stdin_path: Path,
    output_path: Path,
    previous_receipt_path: Path,
) -> dict[str, Any]:
    run_root = Path(run_root).resolve()
    receipt_path = _stage5_bounded_path(
        receipt_path, run_root, "stage5 downstream receipt"
    )
    stdin_path, stdin_bytes = _stage5_bounded_regular_bytes(
        stdin_path, run_root, "stage5 downstream stdin", nonempty=True
    )
    output_path, output_bytes = _stage5_bounded_regular_bytes(
        output_path, run_root, "stage5 downstream output", nonempty=True
    )
    previous_receipt_path = _stage5_bounded_path(
        previous_receipt_path, run_root, "stage5 previous receipt"
    )
    contract, contract_raw = _load_stage5_author_replayer_contract(
        contract_path, run_root
    )
    role, pass_index = _stage5_validate_role_pass(
        expected_role,
        expected_pass_index,
        contract["fix_pass_limit"],
        "stage5 expected downstream",
    )
    receipt, _ = _stage5_read_json_file(receipt_path, "stage5 downstream receipt")
    if receipt.get("role") != role:
        raise ValidationError("stage5 downstream receipt role mismatch", RC_RECEIPT)
    if receipt.get("pass_index") != pass_index:
        raise ValidationError(
            "stage5 downstream receipt pass_index mismatch", RC_RECEIPT
        )
    previous_receipt, previous_raw = _stage5_read_json_file(
        previous_receipt_path, "stage5 previous receipt"
    )
    previous_sha256 = _stage5_validate_previous_receipt(
        previous_receipt,
        previous_raw,
        contract=contract,
        contract_sha256=_sha256(contract_raw),
        role=role,
        pass_index=pass_index,
    )
    return _stage5_validate_downstream_receipt_record(
        receipt,
        contract=contract,
        contract_sha256=_sha256(contract_raw),
        expected_role=role,
        expected_pass_index=pass_index,
        stdin_sha256=_sha256(stdin_bytes),
        output_bytes=len(output_bytes),
        output_sha256=_sha256(output_bytes),
        previous_receipt_sha256=previous_sha256,
    )


def _supervise_one(
    *,
    run_id: str,
    slot: Mapping[str, Any],
    attempt: int,
    parent_run_id: str | None,
    schedule_sha256: str,
    run_root: Path,
    snapshot: Path,
    prompt: Path,
    config_source: Path,
    auth_source: Path,
    codex_binary: Path,
    bwrap_binary: Path,
    dry_run: bool,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    slot_id = str(slot["slot_id"])
    case = str(slot["case"])
    arm = str(slot["arm"])
    requested_model = str(slot.get("requested_model", MODEL))
    attempt_dir = run_root / "attempts" / f"run-{run_id}"
    _assert_arm_neutral_paths((run_root, attempt_dir, snapshot, prompt))
    attempt_dir.mkdir(parents=True, exist_ok=False)
    agent_workspace = (
        run_root / "agent-workspaces" / f"worker-{secrets.token_hex(16)}"
    )
    agent_workspace.mkdir(parents=True, exist_ok=False)
    codex_home = agent_workspace / "codex-home"
    codex_home.mkdir()
    config = codex_home / "config.toml"
    auth = codex_home / "auth.json"
    config_sha = _copy_identity_file(config_source, config, "Codex config")
    auth_sha = _copy_identity_file(auth_source, auth, "Codex auth")
    events = agent_workspace / "events.jsonl"
    done = attempt_dir / ".done"
    output = agent_workspace / "answer.md"
    stderr = agent_workspace / "stderr.log"
    events.write_bytes(b"")
    done.write_bytes(b"")
    output.write_bytes(b"")
    stderr.write_bytes(b"")
    _assert_agent_visible_paths_neutral(
        (snapshot, agent_workspace, codex_home, output, events, stderr)
    )
    event_state = _regular_file_state(events, "events.jsonl")
    done_state = _regular_file_state(done, ".done")
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    oracle_before = verify_snapshot(
        snapshot, case, task_manifest=task_manifest
    )
    oracle_before_path = attempt_dir / "snapshot-before.json"
    _write_frozen_json(oracle_before_path, oracle_before)

    actual_cli = codex_binary.resolve(strict=True)
    actual_bwrap = bwrap_binary.resolve(strict=True)
    cli_version = _stage2_version_probe(
        actual_cli, cwd=attempt_dir, label="CLI"
    )
    bwrap_version = _stage2_version_probe(
        actual_bwrap, cwd=attempt_dir, label="bwrap"
    )
    environment = _clean_environment(
        {
            "CODEX_HOME": os.fspath(codex_home),
            "HOME": "/tmp/t181-home",
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "TZ": "UTC",
        }
    )
    if any(key.startswith("GIT_") for key in environment):
        raise ValidationError("GIT_* survived supervisor environment scrub", RC_ROUTING)
    codex_argv = _codex_exec_argv(
        actual_cli, requested_model, arm, snapshot, output
    )
    normalized_argv = _normalized_exec_argv(
        codex_argv, requested_model, arm
    )
    bwrap_argv = _bwrap_exec_argv(
        actual_bwrap,
        codex_argv,
        snapshot,
        codex_home,
        output,
        events,
        stderr,
        environment,
    )
    actual_process_argv = codex_argv if dry_run else bwrap_argv
    normalized_process_argv = (
        normalized_argv
        if dry_run
        else _replace_identity_paths(
            bwrap_argv,
            {
                f"model_reasoning_effort={arm}": 'model_reasoning_effort="<EFFORT>"'
            },
        )
    )
    effort_positions = {
        index
        for index, value in enumerate(codex_argv)
        if value == f"model_reasoning_effort={arm}"
    }
    _assert_arm_neutral_paths(
        [
            value
            for index, value in enumerate(codex_argv)
            if index not in effort_positions
        ]
        + list(environment.values())
    )
    prompt_bytes = prompt.read_bytes()
    started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    start_monotonic_ns = time.monotonic_ns()
    with events.open("wb") as stdout_stream, stderr.open("wb") as stderr_stream:
        process = subprocess.Popen(
            actual_process_argv,
            cwd=snapshot,
            stdin=subprocess.PIPE,
            stdout=stdout_stream,
            stderr=stderr_stream,
            env=environment,
        )
        launch = {
            "schema_version": SCHEMA_VERSION,
            "task_manifest_sha256": task_manifest_sha256,
            "run_id": run_id,
            "slot_id": slot_id,
            "attempt": attempt,
            "parent_run_id": parent_run_id,
            "case": case,
            "arm": arm,
            "requested_model": requested_model,
            "created_at": started_at,
            "process_start_monotonic_ns": start_monotonic_ns,
            "process_pid": process.pid,
            "events": event_state,
            "done": done_state,
            "prompt": {
                "path": os.fspath(prompt.resolve()),
                "sha256": _sha256(prompt_bytes),
            },
            "snapshot_oracle": {
                "path": os.fspath(oracle_before_path.resolve()),
                "sha256": _sha256(oracle_before_path.read_bytes()),
            },
            "run_dir": os.fspath(attempt_dir.resolve()),
            "agent_workspace": os.fspath(agent_workspace.resolve()),
            "output_path": os.fspath(output.resolve()),
            "stderr_path": os.fspath(stderr.resolve()),
            "codex_home": os.fspath(codex_home.resolve()),
            "codex_config": os.fspath(config.resolve()),
            "codex_config_sha256": config_sha,
            "codex_auth": os.fspath(auth.resolve()),
            "codex_auth_sha256": auth_sha,
            "cli_binary": os.fspath(actual_cli),
            "cli_binary_sha256": _sha256(actual_cli.read_bytes()),
            "cli_version": cli_version,
            "argv": codex_argv,
            "normalized_argv": normalized_argv,
            "bwrap_binary": os.fspath(actual_bwrap),
            "bwrap_binary_sha256": _sha256(actual_bwrap.read_bytes()),
            "bwrap_version": bwrap_version,
            "bwrap_argv": bwrap_argv,
            "actual_process_argv": actual_process_argv,
            "actual_process_argv_normalized": normalized_process_argv,
            "environment": dict(sorted(environment.items())),
            "sandbox": {
                "snapshot_mount": "read-only",
                "home_masked": True,
                "tmp_masked": True,
                "pid_namespace": True,
                "proc_mount": "fresh",
                "writable_binds": [
                    "codex-home",
                    "output",
                    "stdout",
                    "stderr",
                ],
                "attempt_receipts_bound": False,
            },
            "world_state": {
                "snapshot_verified_before": True,
                "git_environment_cleared": True,
            },
            "schedule_sha256": schedule_sha256,
            "dry_run": dry_run,
        }
        launch["treatment_identity_sha256"] = _launch_identity_value(launch)
        launch_path = attempt_dir / "launch.json"
        _write_frozen_json(launch_path, launch)
        if process.stdin is None:
            raise ValidationError("supervisor stdin pipe is unavailable", RC_RECEIPT)
        process.stdin.write(prompt_bytes)
        process.stdin.close()
        exit_code = process.wait()
    exit_monotonic_ns = time.monotonic_ns()
    exited_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    done.write_bytes(
        _canonical_bytes(
            {
                "exit_code": exit_code,
                "exited_at": exited_at,
                "process_exit_monotonic_ns": exit_monotonic_ns,
            }
        )
    )
    post_oracle_reasons: list[str] = []
    try:
        oracle_after = verify_snapshot(
            snapshot, case, task_manifest=task_manifest
        )
    except ValidationError as exc:
        post_oracle_reasons.extend(exc.reasons)
        oracle_after = {
            "schema_version": SCHEMA_VERSION,
            "case": case,
            "snapshot": os.fspath(snapshot),
            "valid": False,
            "failure_reasons": list(exc.reasons),
        }
    oracle_after_path = attempt_dir / "snapshot-after.json"
    _write_frozen_json(oracle_after_path, oracle_after)
    snapshot_unchanged = (
        not post_oracle_reasons
        and _canonical_bytes(oracle_before) == _canonical_bytes(oracle_after)
    )
    completion = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "phase": "completed",
        "run_id": run_id,
        "slot_id": slot_id,
        "block_id": slot["block_id"],
        "block_order": slot["block_order"],
        "attempt": attempt,
        "parent_run_id": parent_run_id,
        "case": case,
        "arm": arm,
        "launch_receipt": os.fspath(launch_path.resolve()),
        "launch_receipt_sha256": _sha256(launch_path.read_bytes()),
        "process_start_monotonic_ns": start_monotonic_ns,
        "process_exit_monotonic_ns": exit_monotonic_ns,
        "process_wall_ms": round((exit_monotonic_ns - start_monotonic_ns) / 1_000_000),
        "exit_code": exit_code,
        "snapshot_before_sha256": _sha256(oracle_before_path.read_bytes()),
        "snapshot_after_sha256": _sha256(oracle_after_path.read_bytes()),
        "snapshot_unchanged": snapshot_unchanged,
    }
    if not snapshot_unchanged:
        completion["supervisor_failure"] = (
            "snapshot changed during process"
            + (
                ": " + "; ".join(post_oracle_reasons)
                if post_oracle_reasons
                else ""
            )
        )
    return completion


def supervise_pair(
    *,
    schedule_path: Path,
    run_root: Path,
    block_id: str,
    attempt: int,
    snapshot: Path,
    prompt: Path,
    config_source: Path,
    auth_source: Path,
    codex_binary: Path,
    bwrap_binary: Path,
    dry_run: bool = False,
    max_gap_ms: int = MAX_SCHEDULE_GAP_MS,
    max_inter_block_gap_ms: int = MAX_INTER_BLOCK_GAP_MS,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    if isinstance(attempt, bool) or not isinstance(attempt, int) or not 1 <= attempt <= 3:
        raise ValidationError("attempt must be in 1..3", RC_ROUTING)
    if (
        max_gap_ms != MAX_SCHEDULE_GAP_MS
        or max_inter_block_gap_ms != MAX_INTER_BLOCK_GAP_MS
    ):
        raise ValidationError("schedule gap bounds are frozen", RC_ROUTING)
    run_root = run_root.resolve()
    snapshot = snapshot.resolve()
    if (
        run_root == snapshot
        or run_root in snapshot.parents
        or snapshot in run_root.parents
    ):
        raise ValidationError("run root and snapshot must be disjoint", RC_ROUTING)
    _assert_arm_neutral_paths((run_root, snapshot, prompt, config_source, auth_source))
    if run_root.exists() and not (run_root / "attempt-ledger.jsonl").exists():
        raise ValidationError("first supervisor run root is not fresh", RC_RECEIPT)
    run_root.mkdir(parents=True, exist_ok=True)
    attempts_root = run_root / "attempts"
    attempts_root.mkdir(exist_ok=True)
    frozen_schedule = run_root / "schedule.json"
    source_schedule_bytes = schedule_path.read_bytes()
    if frozen_schedule.exists():
        schedule_bytes = frozen_schedule.read_bytes()
        if schedule_bytes != source_schedule_bytes:
            raise ValidationError("run-root schedule bytes changed", RC_ROUTING)
    else:
        frozen_schedule.write_bytes(source_schedule_bytes)
        schedule_bytes = frozen_schedule.read_bytes()
    schedule_sha = _sha256(schedule_bytes)
    schedule = _load_json_object(frozen_schedule, data=schedule_bytes)
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    _require_task_manifest_sha256(
        schedule,
        task_manifest,
        "schedule",
        rc=RC_ROUTING,
    )
    slots, schedule_reasons = _validate_schedule(
        schedule, task_manifest=task_manifest
    )
    if schedule_reasons:
        raise ValidationError(schedule_reasons, RC_ROUTING)
    block_slots = [row for row in slots if row.get("block_id") == block_id]
    if len(block_slots) != 2:
        raise ValidationError("supervisor block must contain two slots", RC_ROUTING)
    block_slots.sort(key=lambda row: int(row["block_order"]))
    if len({row["case"] for row in block_slots}) != 1:
        raise ValidationError("supervisor block case mismatch", RC_ROUTING)
    oracle_probe = verify_snapshot(
        snapshot,
        str(block_slots[0]["case"]),
        task_manifest=task_manifest,
    )
    _assert_submodule_manifest_sha256(
        oracle_probe["submodules"],
        block_slots[0].get("submodule_manifest_sha256"),
    )
    if _sha256(_canonical_bytes(oracle_probe)) != block_slots[0].get(
        "snapshot_manifest_sha256"
    ):
        raise ValidationError("scheduled snapshot manifest sha mismatch", RC_SNAPSHOT)
    if _sha256(prompt.read_bytes()) != block_slots[0].get("prompt_sha256"):
        raise ValidationError("scheduled prompt sha mismatch", RC_ROUTING)

    ledger_path = run_root / "attempt-ledger.jsonl"
    ledger_rows = _attempt_ledger_rows(ledger_path)
    completions = [row for row in ledger_rows if row.get("phase") == "completed"]
    existing_launches = {
        path.resolve() for path in attempts_root.rglob("launch.json")
    }
    recorded_launches = {
        Path(row["launch_receipt"]).resolve()
        for row in completions
        if isinstance(row.get("launch_receipt"), str)
    }
    if existing_launches != recorded_launches:
        raise ValidationError(
            "run-root launch receipt closure mismatch before supervisor launch",
            RC_RECEIPT,
        )
    block_order = list(dict.fromkeys(str(row["block_id"]) for row in slots))
    completed_blocks = list(
        dict.fromkeys(str(row.get("block_id")) for row in completions)
    )
    if attempt == 1:
        expected_next = block_order[len(completed_blocks)] if len(completed_blocks) < len(block_order) else None
        if block_id != expected_next:
            raise ValidationError("block is not the next scheduled block", RC_ROUTING)
    else:
        if not completed_blocks or completed_blocks[-1] != block_id:
            raise ValidationError("retry block is not adjacent to its failed generation", RC_ROUTING)
    previous_by_slot: dict[str, list[dict[str, Any]]] = {}
    for row in completions:
        previous_by_slot.setdefault(str(row.get("slot_id")), []).append(row)
    prior_counts = {
        slot["slot_id"]: len(previous_by_slot.get(str(slot["slot_id"]), []))
        for slot in block_slots
    }
    if set(prior_counts.values()) != {attempt - 1}:
        raise ValidationError("pair members are not in the same attempt generation", RC_ROUTING)
    parent_by_slot = {
        str(slot["slot_id"]): (
            previous_by_slot[str(slot["slot_id"])][-1]["run_id"]
            if attempt > 1
            else None
        )
        for slot in block_slots
    }
    for slot in block_slots:
        _append_jsonl(
            ledger_path,
            {
                "schema_version": SCHEMA_VERSION,
                "task_manifest_sha256": task_manifest_sha256,
                "phase": "reserved",
                "slot_id": slot["slot_id"],
                "block_id": block_id,
                "attempt": attempt,
                "parent_run_id": parent_by_slot[str(slot["slot_id"])],
            },
        )
    completed: list[dict[str, Any]] = []
    for slot_index, slot in enumerate(block_slots):
        run_id = uuid.uuid4().hex
        supervision_started_ns = time.monotonic_ns()
        try:
            row = _supervise_one(
                run_id=run_id,
                slot=slot,
                attempt=attempt,
                parent_run_id=parent_by_slot[str(slot["slot_id"])],
                schedule_sha256=schedule_sha,
                run_root=run_root,
                snapshot=snapshot.resolve(),
                prompt=prompt.resolve(),
                config_source=config_source,
                auth_source=auth_source,
                codex_binary=codex_binary,
                bwrap_binary=bwrap_binary,
                dry_run=dry_run,
                task_manifest=task_manifest,
            )
        except Exception as exc:
            failed_at_ns = time.monotonic_ns()
            failure = {
                "kind": "prelaunch-exception",
                "exception_type": type(exc).__name__,
                "message": str(exc),
            }
            row = {
                "schema_version": SCHEMA_VERSION,
                "task_manifest_sha256": task_manifest_sha256,
                "phase": "completed",
                "run_id": run_id,
                "slot_id": slot["slot_id"],
                "block_id": slot["block_id"],
                "block_order": slot["block_order"],
                "attempt": attempt,
                "parent_run_id": parent_by_slot[str(slot["slot_id"])],
                "case": slot["case"],
                "arm": slot["arm"],
                "process_started": False,
                "not_launched": True,
                "supervision_start_monotonic_ns": supervision_started_ns,
                "supervision_end_monotonic_ns": failed_at_ns,
                "supervision_wall_ms": round(
                    (failed_at_ns - supervision_started_ns) / 1_000_000
                ),
                "input_tokens": 0,
                "cached_input_tokens": 0,
                "output_tokens": 0,
                "reasoning_output_tokens": 0,
                "cli_reported": 0,
                "model_calls": 0,
                "turn_protocol": "single-turn-required",
                "wall_clock_ms": round(
                    (failed_at_ns - supervision_started_ns) / 1_000_000
                ),
                "rate_limited": False,
                "retry": attempt > 1,
                "compaction_observed": False,
                "failure_class": "technical-invalid",
                "failure_classes": ["technical-invalid"],
                "treatment_started": False,
                "prelaunch_failure": failure,
                "supervisor_failure": (
                    f"prelaunch {failure['exception_type']}: {failure['message']}"
                ),
            }
            _append_jsonl(ledger_path, row)
            completed.append(row)
            for mate in block_slots[slot_index + 1 :]:
                mate_run_id = uuid.uuid4().hex
                mate_row = {
                    "schema_version": SCHEMA_VERSION,
                    "task_manifest_sha256": task_manifest_sha256,
                    "phase": "completed",
                    "run_id": mate_run_id,
                    "slot_id": mate["slot_id"],
                    "block_id": mate["block_id"],
                    "block_order": mate["block_order"],
                    "attempt": attempt,
                    "parent_run_id": parent_by_slot[str(mate["slot_id"])],
                    "case": mate["case"],
                    "arm": mate["arm"],
                    "process_started": False,
                    "not_launched": True,
                    "supervision_start_monotonic_ns": failed_at_ns,
                    "supervision_end_monotonic_ns": failed_at_ns,
                    "supervision_wall_ms": 0,
                    "input_tokens": 0,
                    "cached_input_tokens": 0,
                    "output_tokens": 0,
                    "reasoning_output_tokens": 0,
                    "cli_reported": 0,
                    "model_calls": 0,
                    "turn_protocol": "single-turn-required",
                    "wall_clock_ms": 0,
                    "rate_limited": False,
                    "retry": attempt > 1,
                    "compaction_observed": False,
                    "failure_class": "pair-invalidated",
                    "failure_classes": ["pair-invalidated"],
                    "individual_failure_class": None,
                    "treatment_started": False,
                    "pair_invalidation": {
                        "block_id": block_id,
                        "generation": attempt,
                        "technical_run_ids": [run_id],
                    },
                    "supervisor_failure": (
                        f"mate not launched after prelaunch failure {run_id}"
                    ),
                }
                _append_jsonl(ledger_path, mate_row)
                completed.append(mate_row)
            break
        previous_process = (
            completed[-1]
            if completed
            else next(
                (
                    previous
                    for previous in reversed(completions)
                    if isinstance(
                        previous.get("process_exit_monotonic_ns"), int
                    )
                ),
                None,
            )
        )
        current_start = int(row["process_start_monotonic_ns"])
        previous_exit = (
            int(previous_process["process_exit_monotonic_ns"])
            if previous_process is not None
            else current_start
        )
        gap_ms = round((current_start - previous_exit) / 1_000_000)
        row["previous_exit_to_start_gap_ms"] = gap_ms
        gap_limit_ms = (
            max_gap_ms
            if previous_process is not None
            and _is_intra_block_arm_transition(previous_process, row)
            else max_inter_block_gap_ms
        )
        if current_start < previous_exit:
            row["supervisor_failure"] = "process overlap or reverse order"
        elif gap_ms > gap_limit_ms:
            row["supervisor_failure"] = "schedule gap exceeds bound"
        _append_jsonl(ledger_path, row)
        completed.append(row)
    failures = [
        str(row["supervisor_failure"])
        for row in completed
        if isinstance(row.get("supervisor_failure"), str)
    ]
    if failures:
        raise ValidationError(failures, RC_RECEIPT)
    return {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "run_root": os.fspath(run_root),
        "attempt_ledger": os.fspath(ledger_path),
        "block_id": block_id,
        "attempt": attempt,
        "runs": completed,
    }


def _thread_id_from_events(path: Path) -> str:
    rows, issues = _json_lines(path)
    if issues:
        raise ValidationError(issues, RC_SESSION)
    ids = [
        row.get("thread_id")
        for row in rows
        if row.get("type") == "thread.started"
        and isinstance(row.get("thread_id"), str)
    ]
    if len(ids) != 1:
        raise ValidationError(
            f"thread.started.thread_id count is {len(ids)}, expected 1", RC_SESSION
        )
    return ids[0]


def _verify_launch_receipt(
    launch_path: Path,
    launch: Mapping[str, Any],
    arm: str,
    requested_model: str,
) -> list[str]:
    reasons: list[str] = []
    if (
        not isinstance(launch.get("argv"), list)
        or not all(isinstance(value, str) for value in launch.get("argv", []))
        or not isinstance(launch.get("bwrap_argv"), list)
        or not all(isinstance(value, str) for value in launch.get("bwrap_argv", []))
        or not isinstance(launch.get("sandbox"), dict)
        or not isinstance(launch.get("world_state"), dict)
        or not isinstance(launch.get("cli_version"), str)
        or not launch.get("cli_version")
        or not isinstance(launch.get("bwrap_version"), str)
        or not launch.get("bwrap_version")
        or not isinstance(launch.get("actual_process_argv"), list)
        or not isinstance(launch.get("actual_process_argv_normalized"), list)
        or not all(
            isinstance(launch.get(field), str) and launch.get(field)
            for field in ("agent_workspace", "output_path", "stderr_path")
        )
        or not isinstance(launch.get("schedule_sha256"), str)
        or len(launch.get("schedule_sha256", "")) != 64
    ):
        reasons.append("launch receipt attestation schema mismatch")
    try:
        if launch.get("normalized_argv") != _normalized_exec_argv(
            launch.get("argv", []), requested_model, arm
        ):
            reasons.append("launch normalized argv mismatch")
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    environment = launch.get("environment")
    if (
        not isinstance(environment, dict)
        or set(environment) - ENV_ALLOWLIST
        or any(str(key).startswith("GIT_") for key in environment)
    ):
        reasons.append("launch environment allowlist mismatch")
    elif environment.get("CODEX_HOME") != launch.get("codex_home"):
        reasons.append("launch CODEX_HOME mismatch")
    try:
        _assert_arm_neutral_paths(
            [
                str(launch.get(field))
                for field in (
                    "run_dir",
                    "agent_workspace",
                    "output_path",
                    "stderr_path",
                    "codex_home",
                    "codex_config",
                    "cli_binary",
                )
            ]
            + [
                str(value.get("path"))
                for value in (
                    launch.get("events", {}),
                    launch.get("done", {}),
                    launch.get("prompt", {}),
                    launch.get("snapshot_oracle", {}),
                )
                if isinstance(value, dict)
            ]
        )
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    try:
        if launch.get("treatment_identity_sha256") != _launch_identity_value(launch):
            reasons.append("launch treatment identity mismatch")
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    for path_field, sha_field in (
        ("cli_binary", "cli_binary_sha256"),
        ("codex_config", "codex_config_sha256"),
        ("codex_auth", "codex_auth_sha256"),
        ("bwrap_binary", "bwrap_binary_sha256"),
    ):
        try:
            path = Path(str(launch.get(path_field))).resolve(strict=True)
            digest = _sha256(path.read_bytes())
        except OSError as exc:
            reasons.append(f"launch {path_field} cannot be re-read: {exc}")
        else:
            if digest != launch.get(sha_field):
                reasons.append(f"launch {path_field} sha mismatch")
    bwrap_argv = launch.get("bwrap_argv", [])
    required_bwrap = {
        "--unshare-pid",
        "--proc",
        "--tmpfs",
        "--ro-bind",
        "--clearenv",
    }
    if not required_bwrap <= set(bwrap_argv):
        reasons.append("launch bwrap isolation contract missing")
    bind_pairs = {
        (bwrap_argv[index + 1], bwrap_argv[index + 2])
        for index, value in enumerate(bwrap_argv[:-2])
        if value == "--bind"
    }
    expected_writable = {
        (str(launch.get(field)), str(launch.get(field)))
        for field in ("codex_home", "output_path", "stderr_path")
    }
    events_state = launch.get("events")
    if isinstance(events_state, dict):
        expected_writable.add(
            (str(events_state.get("path")), str(events_state.get("path")))
        )
    if bind_pairs != expected_writable:
        reasons.append("agent writable bind set is not minimal")
    run_dir = str(launch.get("run_dir"))
    if any(run_dir in pair for pair in bind_pairs):
        reasons.append("attempt receipt directory is visible in sandbox")
    try:
        workspace = Path(str(launch.get("agent_workspace"))).resolve()
        if not all(
            workspace in Path(str(launch.get(field))).resolve().parents
            for field in ("codex_home", "output_path", "stderr_path")
        ):
            reasons.append("agent-visible paths escape opaque workspace")
        if (
            not isinstance(events_state, dict)
            or workspace
            not in Path(str(events_state.get("path"))).resolve().parents
        ):
            reasons.append("agent stdout path escapes opaque workspace")
        resolved_run_dir = Path(run_dir).resolve()
        if (
            workspace == resolved_run_dir
            or workspace in resolved_run_dir.parents
            or resolved_run_dir in workspace.parents
        ):
            reasons.append("agent workspace is nested in attempt receipt directory")
        _assert_agent_visible_paths_neutral(
            (
                workspace,
                Path(str(launch.get("codex_home"))),
                Path(str(launch.get("output_path"))),
                Path(str(launch.get("stderr_path"))),
                Path(str(events_state.get("path")))
                if isinstance(events_state, dict)
                else "",
            )
        )
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    except OSError as exc:
        reasons.append(f"agent workspace paths cannot be resolved: {exc}")
    sandbox = launch.get("sandbox", {})
    if (
        sandbox.get("attempt_receipts_bound") is not False
        or sandbox.get("writable_binds")
        != ["codex-home", "output", "stdout", "stderr"]
    ):
        reasons.append("sandbox writable-bind attestation mismatch")
    snapshot_path = launch.get("snapshot_oracle", {})
    if isinstance(snapshot_path, dict):
        try:
            oracle = _load_json_object(Path(str(snapshot_path.get("path"))))
        except ValidationError as exc:
            reasons.extend(exc.reasons)
        else:
            snapshot = str(oracle.get("snapshot"))
            try:
                _assert_agent_visible_paths_neutral((snapshot,))
            except ValidationError as exc:
                reasons.extend(exc.reasons)
            ro_bind_pairs = {
                (bwrap_argv[index + 1], bwrap_argv[index + 2])
                for index, value in enumerate(bwrap_argv[:-2])
                if value == "--ro-bind"
            }
            if (snapshot, snapshot) not in ro_bind_pairs:
                reasons.append("snapshot is not the recorded read-only bind")
            try:
                expected_bwrap = _bwrap_exec_argv(
                    Path(str(launch.get("bwrap_binary"))),
                    [str(value) for value in launch.get("argv", [])],
                    Path(snapshot),
                    Path(str(launch.get("codex_home"))),
                    Path(str(launch.get("output_path"))),
                    Path(str(launch.get("events", {}).get("path"))),
                    Path(str(launch.get("stderr_path"))),
                    {
                        str(key): str(value)
                        for key, value in environment.items()
                    }
                    if isinstance(environment, dict)
                    else {},
                )
            except (OSError, ValidationError) as exc:
                reasons.append(f"launch bwrap argv cannot be reconstructed: {exc}")
            else:
                if bwrap_argv != expected_bwrap:
                    reasons.append("launch bwrap argv is not supervisor canonical")
    if launch.get("dry_run") is False and launch.get("actual_process_argv") != bwrap_argv:
        reasons.append("actual process argv is not recorded bwrap argv")
    try:
        launch_mtime_ns = launch_path.stat().st_mtime_ns
        for label in ("events", "done"):
            state = launch.get(label)
            if not isinstance(state, dict):
                reasons.append(f"launch {label} state missing")
                continue
            current_mtime = Path(str(state.get("path"))).stat().st_mtime_ns
            if launch_mtime_ns > current_mtime:
                reasons.append(f"launch receipt was frozen after {label}")
    except OSError as exc:
        reasons.append(f"launch freshness metadata cannot be read: {exc}")
    return reasons


def _verify_postlaunch_file(path: Path, frozen: Mapping[str, Any], label: str) -> os.stat_result:
    state = _regular_file_state(path, label)
    if state["path"] != frozen.get("path") or state["inode"] != frozen.get("inode"):
        raise ValidationError(f"{label} path/inode changed after launch", RC_RECEIPT)
    if frozen.get("size") != 0:
        raise ValidationError(f"{label} prelaunch size was not zero", RC_RECEIPT)
    if state["mtime_ns"] < int(frozen.get("mtime_ns", -1)):
        raise ValidationError(f"{label} mtime moved backwards", RC_RECEIPT)
    return path.stat()


def _read_done(path: Path, frozen: Mapping[str, Any], start_monotonic_ns: int) -> tuple[int, int, str]:
    _verify_postlaunch_file(path, frozen, ".done")
    value = _read_json_value(path)
    if not isinstance(value, dict):
        raise ValidationError(".done is not a JSON object", RC_RECEIPT)
    exit_code = value.get("exit_code")
    exit_ns = value.get("process_exit_monotonic_ns")
    exited_at = value.get("exited_at")
    if (
        isinstance(exit_code, bool)
        or not isinstance(exit_code, int)
        or isinstance(exit_ns, bool)
        or not isinstance(exit_ns, int)
        or exit_ns < start_monotonic_ns
        or _parse_timestamp(exited_at) is None
    ):
        raise ValidationError(".done process exit receipt is malformed", RC_RECEIPT)
    return exit_code, round((exit_ns - start_monotonic_ns) / 1_000_000), exited_at


def _rollout_details(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    rows, parser_issues = _json_lines(path)
    ledger_record, ledger_issues = LEDGER._stream_rollout(path)
    issues = list(parser_issues)
    for category, details in sorted(ledger_issues.items()):
        issues.extend(f"ledger:{category}:{detail}" for detail in sorted(details))
    return rows, issues


def _event_payloads(rows: Iterable[dict[str, Any]], event_type: str) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    result: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for row in rows:
        if row.get("type") != "event_msg":
            continue
        payload = row.get("payload")
        if isinstance(payload, dict) and payload.get("type") == event_type:
            result.append((row, payload))
    return result


def _external_reference_hits(
    rows: Iterable[dict[str, Any]], snapshot: Path
) -> list[str]:
    root = os.fspath(snapshot.resolve())
    hits: set[str] = set()

    def strings(value: Any) -> Iterable[str]:
        if isinstance(value, str):
            yield value
        elif isinstance(value, dict):
            for child in value.values():
                yield from strings(child)
        elif isinstance(value, list):
            for child in value:
                yield from strings(child)

    for row in rows:
        if row.get("type") != "response_item":
            continue
        for value in strings(row.get("payload")):
            for match in re.findall(r"/home/[^\s'\"`)\]}>,;]+", value):
                candidate = match.rstrip(".:")
                if candidate != root and not candidate.startswith(root + os.sep):
                    hits.add(candidate)
    return sorted(hits)


def _is_zero_component_total_only(
    usage: Any, validated: Mapping[str, int] | None
) -> bool:
    """Classify only the observed shape; do not assign a cause."""
    if validated is None or validated["total_tokens"] <= 0:
        return False
    if any(validated[field] != 0 for field in _ZERO_COMPONENT_FIELDS):
        return False
    cache_write = usage.get("cache_write_input_tokens")
    return type(cache_write) is int and cache_write == 0


def collect_run(
    *,
    run_id: str,
    case: str,
    requested_effort: str,
    events: Path,
    done: Path,
    output: Path,
    prompt: Path,
    sessions_root: Path,
    snapshot: Path,
    launch_receipt: Path,
    expected_requested_model: str,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[dict[str, Any], int]:
    reasons: list[str] = []
    launch = _load_json_object(launch_receipt)
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    if launch.get("task_manifest_sha256") != task_manifest_sha256:
        reasons.append("launch receipt task_manifest_sha256 mismatch")
    for field, expected_value in (
        ("run_id", run_id),
        ("case", case),
        ("arm", requested_effort),
    ):
        if launch.get(field) != expected_value:
            reasons.append(f"launch receipt {field} mismatch")
    reasons.extend(
        _verify_launch_receipt(
            launch_receipt,
            launch,
            requested_effort,
            expected_requested_model,
        )
    )
    before = _parse_timestamp(launch.get("created_at"))
    start_monotonic_ns = launch.get("process_start_monotonic_ns")
    if (
        before is None
        or isinstance(start_monotonic_ns, bool)
        or not isinstance(start_monotonic_ns, int)
    ):
        raise ValidationError("invalid frozen launch receipt", RC_RECEIPT)
    event_frozen = launch.get("events")
    done_frozen = launch.get("done")
    if not isinstance(event_frozen, dict) or not isinstance(done_frozen, dict):
        raise ValidationError("launch receipt file state missing", RC_RECEIPT)
    launch_prompt = launch.get("prompt")
    if not isinstance(launch_prompt, dict):
        launch_prompt = {}
        reasons.append("launch receipt prompt state missing")
    if launch_prompt.get("path") != os.fspath(prompt.resolve()):
        reasons.append("launch receipt prompt path mismatch")
    if launch_prompt.get("sha256") != _sha256(prompt.read_bytes()):
        reasons.append("launch receipt prompt sha mismatch")
    try:
        _verify_postlaunch_file(events, event_frozen, "events.jsonl")
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    try:
        thread_id = _thread_id_from_events(events)
    except ValidationError as exc:
        thread_id = None
        reasons.extend(exc.reasons)
    try:
        exit_code, process_wall_ms, exited_at_raw = _read_done(
            done, done_frozen, start_monotonic_ns
        )
    except ValidationError as exc:
        exit_code = None
        process_wall_ms = None
        exited_at_raw = None
        reasons.extend(exc.reasons)
    after = _parse_timestamp(exited_at_raw)
    if after is None or after < before:
        reasons.append("process launch/exit timestamp envelope invalid")

    rollout: Path | None = None
    rows: list[dict[str, Any]] = []
    ledger_record: dict[str, Any] | None = None
    session_id: str | None = None
    rollout_inode: int | None = None
    session_timestamp: str | None = None
    zero_component_total_only_indexes: list[int] = []
    if thread_id is not None:
        try:
            rollout = _find_rollout(sessions_root, thread_id)
            rollout_inode = rollout.stat().st_ino
            rows, rollout_issues = _rollout_details(rollout)
            reasons.extend(rollout_issues)
            ledger_record, _ = LEDGER._stream_rollout(rollout)
        except ValidationError as exc:
            reasons.extend(exc.reasons)
    if rollout is not None:
        meta = [
            row.get("payload")
            for row in rows
            if row.get("type") == "session_meta"
            and isinstance(row.get("payload"), dict)
        ]
        if len(meta) != 1:
            reasons.append(f"session_meta count is {len(meta)}, expected 1")
        else:
            session_id = meta[0].get("session_id")
            session_timestamp = next(
                (
                    row.get("timestamp") or row["payload"].get("timestamp")
                    for row in rows
                    if row.get("type") == "session_meta"
                    and isinstance(row.get("payload"), dict)
                ),
                None,
            )
            parsed_session_time = _parse_timestamp(session_timestamp)
            if (
                parsed_session_time is None
                or after is None
                or not before <= parsed_session_time <= after
            ):
                reasons.append("session timestamp outside launch envelope")
            if not (
                meta[0].get("id")
                == meta[0].get("session_id")
                == thread_id
            ):
                reasons.append("session id/session_id/thread_id mismatch")
            if meta[0].get("cwd") != os.fspath(snapshot.resolve()):
                reasons.append("session_meta cwd mismatch")
            git_meta = meta[0].get("git")
            if not isinstance(git_meta, dict) or git_meta.get("commit_hash") != BASE_COMMIT:
                reasons.append("session_meta git commit mismatch")
            if meta[0].get("cli_version") in (None, ""):
                reasons.append("session_meta cli_version missing")

        context_rows = [
            row
            for row in rows
            if row.get("type") == "turn_context"
            and isinstance(row.get("payload"), dict)
        ]
        contexts = [row["payload"] for row in context_rows]
        if not contexts:
            reasons.append("turn_context count is 0")
        if any(
            not isinstance(value.get("turn_id"), str) or not value.get("turn_id")
            for value in contexts
        ):
            reasons.append("turn_context turn_id missing/empty")
        context_tuples = {
            (
                value.get("turn_id"),
                value.get("cwd"),
                value.get("model"),
                value.get("effort"),
            )
            for value in contexts
        }
        if len(context_tuples) > 1:
            reasons.append("turn_context values changed within run")
        effective_effort = (
            contexts[0].get("effort") if contexts else None
        )
        turn_id = contexts[0].get("turn_id") if contexts else None
        if contexts and effective_effort != requested_effort:
            reasons.append("requested/effective effort mismatch")
        if contexts and contexts[0].get("model") != expected_requested_model:
            reasons.append("model mismatch")
        if contexts and contexts[0].get("cwd") != os.fspath(snapshot.resolve()):
            reasons.append("turn_context cwd mismatch")

        token_events = _event_payloads(rows, "token_count")
        valid_info = [
            payload.get("info")
            for _, payload in token_events
            if isinstance(payload.get("info"), dict)
        ]
        if not token_events:
            reasons.append("token_count count is 0")
        if not valid_info:
            reasons.append("all token_count.info values are null/non-object")
        if token_events and not isinstance(token_events[-1][1].get("info"), dict):
            reasons.append("final token_count.info is null/non-object")
        for index, info in enumerate(valid_info, 1):
            for usage_name in ("total_token_usage", "last_token_usage"):
                usage = info.get(usage_name)
                (
                    validated,
                    usage_errors,
                    cached_exceeds_input,
                ) = LEDGER._validated_usage(
                    usage, location=f"token[{index}].{usage_name}"
                )
                reasons.extend(usage_errors)
                reasons.extend(cached_exceeds_input)
                if isinstance(usage, dict) and "reasoning_output_tokens" not in usage:
                    reasons.append(
                        f"token[{index}].{usage_name}.reasoning_output_tokens missing"
                    )
                if validated is not None:
                    if validated["cached_input_tokens"] > validated["input_tokens"]:
                        reasons.append(
                            f"token[{index}].{usage_name} cached exceeds input"
                        )
                    identity_mismatch = validated["total_tokens"] != (
                        validated["input_tokens"] + validated["output_tokens"]
                    )
                    if (
                        usage_name == "last_token_usage"
                        and identity_mismatch
                        and _is_zero_component_total_only(usage, validated)
                    ):
                        zero_component_total_only_indexes.append(index)
                    elif identity_mismatch:
                        # total_token_usage remains fatal, including the same
                        # shape at the final cumulative cli_reported source.
                        reasons.append(
                            f"token[{index}].{usage_name} total token identity mismatch"
                        )

        prompts = _event_payloads(rows, "user_message")
        prompt_bytes = prompt.read_bytes()
        if len(prompts) != 1:
            reasons.append(f"user_message count is {len(prompts)}, expected 1")
        elif str(prompts[0][1].get("message", "")).encode("utf-8") != prompt_bytes:
            reasons.append("rollout user_message/prompt bytes mismatch")

        starts = _event_payloads(rows, "task_started")
        completes = _event_payloads(rows, "task_complete")
        aborted = _event_payloads(rows, "turn_aborted")
        related_types = {
            "task_started",
            "user_message",
            "token_count",
            "agent_message",
            "task_complete",
            "turn_aborted",
        }
        related: list[tuple[int, datetime | None, str]] = []
        for row_index, row in enumerate(rows):
            payload = row.get("payload")
            if row.get("type") == "turn_context":
                related.append(
                    (row_index, _parse_timestamp(row.get("timestamp")), "turn_context")
                )
            elif (
                row.get("type") == "event_msg"
                and isinstance(payload, dict)
                and payload.get("type") in related_types
            ):
                related.append(
                    (
                        row_index,
                        _parse_timestamp(row.get("timestamp")),
                        str(payload.get("type")),
                    )
                )
        if any(timestamp is None for _, timestamp, _ in related):
            reasons.append("related event timestamp missing/malformed")
        else:
            related_times = [timestamp for _, timestamp, _ in related]
            if related_times != sorted(related_times):
                reasons.append("related event timestamp order mismatch")
            if after is not None and any(
                not before <= timestamp <= after
                for timestamp in related_times
                if timestamp is not None
            ):
                reasons.append("related event timestamp outside process envelope")
        related_names = [name for _, _, name in related]
        if related_names:
            if related_names[0] != "task_started":
                reasons.append("related event sequence does not start with task_started")
            terminal = "turn_aborted" if aborted else "task_complete"
            if related_names[-1] != terminal:
                reasons.append("related event sequence has wrong terminal event")
            try:
                start_position = related_names.index("task_started")
                context_position = related_names.index("turn_context")
                user_position = related_names.index("user_message")
                agent_position = related_names.index("agent_message")
                terminal_position = related_names.index(terminal)
            except ValueError:
                reasons.append("related event sequence is incomplete")
            else:
                if not (
                    start_position
                    < context_position
                    < user_position
                    < agent_position
                    < terminal_position
                ):
                    reasons.append("related event sequence order mismatch")
        if aborted:
            reasons.append("turn_aborted observed")
        if any(
            not isinstance(payload.get("turn_id"), str) or not payload.get("turn_id")
            for _, payload in (*starts, *completes, *aborted)
        ):
            reasons.append("task turn_id missing/empty")
        if len(starts) != 1:
            reasons.append(f"task_started count is {len(starts)}, expected 1")
        if len(completes) != 1:
            marker = " after task_started" if starts else ""
            reasons.append(
                f"task_complete missing{marker}"
                if not completes
                else f"task_complete count is {len(completes)}, expected 1"
            )
        start_time = _parse_timestamp(starts[0][0].get("timestamp")) if len(starts) == 1 else None
        complete_time = (
            _parse_timestamp(completes[0][0].get("timestamp"))
            if len(completes) == 1
            else None
        )
        task_wall_ms: int | None = None
        duration_ms: int | None = None
        if start_time is None or complete_time is None or complete_time < start_time:
            reasons.append("task timestamp order/schema mismatch")
        else:
            task_wall_ms = round((complete_time - start_time).total_seconds() * 1000)
            if after is None or not (before <= start_time <= complete_time <= after):
                reasons.append("task timestamp outside launch envelope")
        if len(starts) == len(completes) == 1:
            if starts[0][1].get("turn_id") != completes[0][1].get("turn_id"):
                reasons.append("task start/complete turn_id mismatch")
            if turn_id != starts[0][1].get("turn_id"):
                reasons.append("turn_context/task turn_id mismatch")
            duration = completes[0][1].get("duration_ms")
            if isinstance(duration, int) and not isinstance(duration, bool):
                duration_ms = duration
                if task_wall_ms is not None and abs(duration_ms - task_wall_ms) > 1000:
                    reasons.append("task duration differs from wall clock by >1000ms")
            else:
                reasons.append("task_complete.duration_ms missing/non-int")
        if exit_code not in (None, 0):
            marker = " after task_started" if starts else ""
            reasons.append(f"process exit{marker}: {exit_code}")

        try:
            output_bytes = output.read_bytes()
        except OSError as exc:
            output_bytes = b""
            reasons.append(f"output: cannot read output: {exc}")
        agent_messages = _event_payloads(rows, "agent_message")
        final_message = (
            str(agent_messages[-1][1].get("message", "")).encode("utf-8")
            if agent_messages
            else None
        )
        if final_message != output_bytes:
            reasons.append("output: output bytes/final agent message mismatch")
        positive_tokens = sum(
            int(ledger_record.get(field) or 0)
            for field in ("input_tokens", "output_tokens", "reasoning_output_tokens")
        ) if ledger_record else 0
        if prompt_bytes and output_bytes and positive_tokens <= 0:
            reasons.append("token usage is all zero for non-empty prompt/output")
        ledger_outcome = (
            LEDGER._classify_outcome(ledger_record) if ledger_record else None
        )
        if ledger_outcome == "fragment":
            reasons.append("ledger fragment outcome observed")
        logical_turn_ids = {
            value
            for value in [
                *(payload.get("turn_id") for _, payload in starts),
                *(payload.get("turn_id") for _, payload in completes),
                *(context.get("turn_id") for context in contexts),
            ]
            if isinstance(value, str) and value
        }
        if len(logical_turn_ids) > 1:
            reasons.append("single-turn protocol contains multiple turn ids")
        serialized_rows = json.dumps(rows, ensure_ascii=False).casefold()
        rate_limited = bool(
            re.search(r"\b429\b|rate[- ]limit|rate_limit", serialized_rows)
        )
        compaction_observed = bool(
            re.search(r"context[_ -]?compact|compaction", serialized_rows)
        )
    else:
        effective_effort = None
        turn_id = None
        task_wall_ms = None
        duration_ms = None
        output_bytes = output.read_bytes() if output.exists() else b""
        starts = []
        completes = []
        aborted = []
        token_events = []
        agent_messages = []
        ledger_outcome = None
        rate_limited = False
        compaction_observed = False

    reasons = sorted(set(reasons))
    treatment_started = bool(starts or token_events or agent_messages or aborted)
    failure_class = (
        "post-treatment"
        if reasons and treatment_started
        else "technical-invalid"
        if reasons
        else None
    )
    classes = [failure_class] if failure_class else []
    primary_rc = 0
    if reasons:
        if any("thread" in reason or "session id" in reason or "rollout count" in reason for reason in reasons):
            primary_rc = RC_SESSION
        elif any(
            marker in reason
            for reason in reasons
            for marker in ("effort", "model mismatch", "cwd mismatch", "git commit")
        ):
            primary_rc = RC_ROUTING
        else:
            primary_rc = RC_RECEIPT
    receipt = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "run_id": run_id,
        "case": case,
        "arm": requested_effort,
        "thread_id": thread_id,
        "session_id": session_id,
        "turn_id": turn_id,
        "requested_effort": requested_effort,
        "effective_effort": effective_effort,
        "model": ledger_record.get("model") if ledger_record else None,
        "ledger_outcome": (
            ledger_outcome
        ),
        "cli_version": (
            next(
                (
                    row["payload"].get("cli_version")
                    for row in rows
                    if row.get("type") == "session_meta"
                    and isinstance(row.get("payload"), dict)
                ),
                None,
            )
            if rows
            else None
        ),
        "rollout_sha256": _sha256(rollout.read_bytes()) if rollout else None,
        "prompt_sha256": _sha256(prompt.read_bytes()),
        "snapshot_manifest_sha256": launch.get("snapshot_oracle", {}).get("sha256"),
        "launch_receipt_sha256": _sha256(launch_receipt.read_bytes()),
        "launch_receipt": os.fspath(launch_receipt.resolve()),
        "events_inode": event_frozen.get("inode"),
        "done_inode": done_frozen.get("inode"),
        "events_initial_size": event_frozen.get("size"),
        "done_initial_size": done_frozen.get("size"),
        "rollout_path": os.fspath(rollout.resolve()) if rollout else None,
        "rollout_inode": rollout_inode,
        "session_timestamp": session_timestamp,
        "output_sha256": _sha256(output_bytes),
        "model_calls": ledger_record.get("model_calls") if ledger_record else 0,
        "turn_protocol": "single-turn-required",
        "input_tokens": ledger_record.get("input_tokens") if ledger_record else 0,
        "cached_input_tokens": (
            ledger_record.get("cached_input_tokens") if ledger_record else 0
        ),
        "output_tokens": ledger_record.get("output_tokens") if ledger_record else 0,
        "reasoning_output_tokens": (
            ledger_record.get("reasoning_output_tokens") if ledger_record else 0
        ),
        "cli_reported": ledger_record.get("cli_reported") if ledger_record else 0,
        "token_usage_observations": {
            ZERO_COMPONENT_TOTAL_ONLY: {
                "usage": "last_token_usage",
                "count": len(zero_component_total_only_indexes),
                "indexes": zero_component_total_only_indexes,
            }
        },
        "wall_clock_ms": process_wall_ms,
        "task_wall_clock_ms": task_wall_ms,
        "duration_ms": duration_ms,
        "process_exit": exit_code,
        "failure_reasons": reasons,
        "failure_classes": classes,
        "failure_class": failure_class,
        "treatment_started": treatment_started,
        "rate_limited": rate_limited,
        "retry": int(launch.get("attempt", 1)) > 1,
        "parent_run_id": launch.get("parent_run_id"),
        "compaction_observed": compaction_observed,
        "valid": not reasons,
        "primary_rc": primary_rc,
        "external_reference_audit": {
            "scope": (
                "明白な snapshot 外参照の検出であり、非参照の証明ではない"
            ),
            "hits": _external_reference_hits(rows, snapshot),
        },
    }
    return receipt, primary_rc


_FENCE_OPEN = re.compile(r"^(?P<indent> {0,3})(?P<marker>`{3,}|~{3,})(?P<info>.*)$")
_HEADING = re.compile(r"^(#{1,6})[ \t]+(.+?)\s*$")


def without_fenced_code(text: str) -> str:
    kept: list[str] = []
    marker: str | None = None
    width = 0
    for line in text.splitlines(keepends=True):
        logical = line.rstrip("\r\n")
        if marker is None:
            opening = _FENCE_OPEN.fullmatch(logical)
            if opening:
                token = opening.group("marker")
                if token[0] == "`" and "`" in opening.group("info"):
                    kept.append(line)
                else:
                    marker, width = token[0], len(token)
                    kept.append("\n" if line.endswith(("\n", "\r")) else "")
            else:
                kept.append(line)
            continue
        if re.fullmatch(rf" {{0,3}}{re.escape(marker)}{{{width},}}[ \t]*", logical):
            marker = None
            width = 0
        kept.append("\n" if line.endswith(("\n", "\r")) else "")
    return "".join(kept)


def _heading_sections(text: str) -> list[tuple[int, str, str]]:
    lines = text.splitlines(keepends=True)
    found: list[tuple[int, int, int, str]] = []
    offset = 0
    for line in lines:
        logical = line.rstrip("\r\n")
        match = _HEADING.fullmatch(logical)
        if match:
            found.append((offset, len(match.group(1)), len(line), match.group(2)))
        offset += len(line)
    sections: list[tuple[int, str, str]] = []
    for index, (start, level, line_length, title) in enumerate(found):
        end = len(text)
        for next_start, next_level, _, _ in found[index + 1 :]:
            if next_level <= level:
                end = next_start
                break
        sections.append((level, title, text[start + line_length : end]))
    return sections


def _normalize_inline_emphasis(text: str) -> str:
    """Remove inline Markdown delimiters before applying decision grammar."""
    return re.sub(r"(?<!\\)(?:\*{1,3}|_{1,3}|`+)", "", text)


_DECISION_OPENING_RE = re.compile(
    r"(?:[ \t]*\r?\n)*[ \t]*"
    r"(?:結論[ \t]*は[ \t]*)?(NO-GO|GO)"
    r"[ \t]*(?:です)?[ \t]*[。.!！]"
)
_DECISION_TOKEN_RE = re.compile(
    r"(?<![A-Za-z-])(NO-GO|GO)(?![A-Za-z一-龯ぁ-んァ-ヶ-])"
)
_DECISION_ASSERTION_RE = re.compile(
    r"(?<![A-Za-z-])(NO-GO|GO)(?![A-Za-z-])"
    r"(?:"
    r"[ \t]*(?:です|だ|である|でもある)?[ \t]*[。.!！]|"
    r"[ \t]*と[ \t]*(?:判断|結論|裁定)|"
    r"[ \t]*の?[ \t]*結論"
    r")"
)


def score_text(text: str) -> dict[str, Any]:
    visible = without_fenced_code(text)
    reasons: list[str] = []
    summaries = [
        body for level, title, body in _heading_sections(visible)
        if level == 2 and title.strip() == "総括"
    ]
    if len(summaries) != 1:
        reasons.append(f"score: summary count is {len(summaries)}, expected 1")
        summary = ""
    else:
        summary = summaries[0]
        summary_section = "## 総括\n" + summary
        if len(summary_section.encode("utf-8")) < 500:
            reasons.append("score: summary section is shorter than 500 bytes")
    normalized_summary = _normalize_inline_emphasis(summary)
    first_sentence = re.match(
        r"^\s*[^。.!！]*[。.!！]", normalized_summary
    )
    decision_match = (
        _DECISION_OPENING_RE.fullmatch(first_sentence.group(0))
        if first_sentence is not None
        else None
    )
    opening_decision = (
        decision_match.group(1) if decision_match is not None else None
    )
    extracted_decisions = set(_DECISION_TOKEN_RE.findall(normalized_summary))
    asserted_decisions = {
        match.group(1)
        for match in _DECISION_ASSERTION_RE.finditer(normalized_summary)
    }
    claimed_decisions = extracted_decisions | asserted_decisions
    decision_disclaimed = bool(
        re.search(
            r"(?:NO-GO|GO)\s*(?:ではない|でない|とは言えない|を否定)|"
            r"(?:未裁定|未決定|判断保留|判定保留|結論保留)|"
            r"(?:判断|判定|結論)(?:は|を)?\s*保留(?:する|した)?|"
            r"(?:これ|それ)(?:は)?(?:最終)?(?:判断|判定|結論)"
            r"(?:ではない|でない)|"
            r"(?:決めかねる|断定しない|確定しない)|"
            r"(?:NO-GO|GO).{0,30}(?:説|判定|判断).{0,10}"
            r"(?:refuted|反証(?:済み|された)?)|"
            r"(?:NO-GO|GO)\s*(?:か|または|若しくは)",
            normalized_summary,
            re.IGNORECASE,
        )
    )
    if (
        opening_decision is None
        or claimed_decisions != {opening_decision}
        or decision_disclaimed
    ):
        reasons.append("score: summary does not start with one GO/NO-GO decision")
        decision = None
    else:
        decision = opening_decision

    finding_sections: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for level, title, body in _heading_sections(visible):
        matches = re.findall(r"(?<![A-Za-z0-9])R-(\d+)(?!\d)", title)
        for number in matches:
            finding_id = f"R-{int(number)}"
            if finding_id in seen_ids:
                reasons.append(f"score: duplicate finding heading {finding_id}")
            seen_ids.add(finding_id)
            finding_sections.append(
                {
                    "id": finding_id,
                    "heading": title,
                    "level": level,
                    "sha256": _sha256(body.encode("utf-8")),
                    "_body": body,
                }
            )
    r1 = next((item for item in finding_sections if item["id"] == "R-1"), None)
    r1_candidate = False
    evidence: dict[str, bool] = {}
    candidate_blocks = (
        [(r1["heading"] + "\n" + r1["_body"])] if r1 is not None else
        [title + "\n" + body for _, title, body in _heading_sections(visible)]
    )
    for candidate_block in candidate_blocks:
        lowered = candidate_block.casefold()
        negated = bool(
            re.search(
                r"pre[- ]policy\s*では.{0,40}(?:canonical|正式な).{0,30}"
                r"(?:parser|reader).{0,20}(?:実行されない|走らない)|"
                r"rc\s*=\s*0.{0,20}rc\s*=\s*2\s*(?:に|へ)"
                r"(?:なることはない|ならない|変わらない)|"
                r"(?:この|当該).{0,30}(?:no-go|must-fix).{0,30}(?:refuted|反証)",
                lowered,
            )
        )
        evidence = {
            "pre_policy": bool(
                re.search(r"pre[- ]policy|policy\s*導入前|規則導入以前", lowered)
            ),
            "canonical_parser": bool(
                re.search(
                    r"(?:canonical|正式な).{0,20}(?:cab|parser|reader)|"
                    r"(?:cab|parser|reader).{0,20}(?:canonical|正式な)",
                    lowered,
                )
            ),
            "acceptance_shrinks": bool(
                (
                    re.search(r"rc\s*=\s*0", lowered)
                    and re.search(r"rc\s*=\s*2", lowered)
                )
                or re.search(r"従来(?:の)?成功.{0,30}(?:内部エラー|失敗).{0,10}(?:終了|へ)", lowered)
            ),
            "must_fix": bool(
                re.search(r"must-fix|no-go|release blocker|リリース阻止", lowered)
            ),
            "negated": negated,
        }
        if all(value for key, value in evidence.items() if key != "negated") and not negated:
            r1_candidate = True
            break
    public_findings = [
        {key: value for key, value in item.items() if key != "_body"}
        for item in finding_sections
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "input_sha256": _sha256(text.encode("utf-8")),
        "valid": not reasons,
        "failure_reasons": sorted(set(reasons)),
        "decision": decision,
        "summary_bytes": (
            len(("## 総括\n" + summary).encode("utf-8")) if summaries else 0
        ),
        "candidate_findings": public_findings,
        "r1_candidate": r1_candidate,
        "r1_evidence": evidence,
        "machine_layer": "candidate_only",
    }


def score_run(path: Path, run_id: str | None = None) -> tuple[dict[str, Any], int]:
    try:
        raw = path.read_bytes()
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "run_id": run_id,
            "valid": False,
            "failure_reasons": [f"score: cannot read UTF-8 output: {exc}"],
            "machine_layer": "candidate_only",
        }
        return result, RC_SCORE
    result = score_text(text)
    result["run_id"] = run_id
    return result, 0 if result["valid"] else RC_SCORE


def _apply_score_failure(
    receipt: Mapping[str, Any], score: Mapping[str, Any]
) -> dict[str, Any]:
    joined = dict(receipt)
    if not score.get("valid", False):
        joined["failure_class"] = "post-treatment"
        joined["failure_classes"] = ["post-treatment"]
        joined["valid"] = False
        joined["failure_reasons"] = sorted(
            set(receipt.get("failure_reasons", []))
            | set(score.get("failure_reasons", []))
        )
    return joined


def _load_json_object(path: Path, *, data: bytes | None = None) -> dict[str, Any]:
    """data は同じ操作で path から読んだ bytes でなければならない。"""
    try:
        value = json.loads(path.read_bytes() if data is None else data)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"cannot read JSON object {path}: {exc}", RC_AGGREGATE) from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON artifact is not an object: {path}", RC_AGGREGATE)
    return value


def _load_json_object_with_sha256(path: Path) -> tuple[dict[str, Any], str]:
    try:
        data = path.read_bytes()
        value = json.loads(data)
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(
            f"cannot read JSON object {path}: {exc}", RC_AGGREGATE
        ) from exc
    if not isinstance(value, dict):
        raise ValidationError(
            f"JSON artifact is not an object: {path}", RC_AGGREGATE
        )
    return value, _sha256(data)


def _resolve_artifact(manifest_path: Path, value: Any) -> Path:
    if not isinstance(value, str) or not value:
        raise ValidationError("manifest artifact path missing", RC_AGGREGATE)
    path = Path(value)
    if not path.is_absolute():
        path = manifest_path.parent / path
    return path.resolve()


def _artifact_path(
    manifest_path: Path,
    descriptor: Any,
    label: str,
    *,
    root: Path | None = None,
) -> Path:
    if not isinstance(descriptor, dict):
        raise ValidationError(f"{label} descriptor missing", RC_AGGREGATE)
    path = _resolve_artifact(manifest_path, descriptor.get("path"))
    if root is not None:
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValidationError(f"{label} escapes artifact root", RC_AGGREGATE) from exc
    expected_sha = descriptor.get("sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValidationError(f"{label} sha256 missing", RC_AGGREGATE)
    try:
        actual_sha = _sha256(path.read_bytes())
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_AGGREGATE) from exc
    if actual_sha != expected_sha:
        raise ValidationError(
            f"{label} sha mismatch: {actual_sha} != {expected_sha}", RC_AGGREGATE
        )
    return path


def _artifact_path_with_bytes(
    manifest_path: Path,
    descriptor: Any,
    label: str,
    *,
    root: Path | None = None,
) -> tuple[Path, bytes]:
    if not isinstance(descriptor, dict):
        raise ValidationError(f"{label} descriptor missing", RC_AGGREGATE)
    path = _resolve_artifact(manifest_path, descriptor.get("path"))
    if root is not None:
        try:
            path.relative_to(root.resolve())
        except ValueError as exc:
            raise ValidationError(f"{label} escapes artifact root", RC_AGGREGATE) from exc
    expected_sha = descriptor.get("sha256")
    if not isinstance(expected_sha, str) or len(expected_sha) != 64:
        raise ValidationError(f"{label} sha256 missing", RC_AGGREGATE)
    try:
        data = path.read_bytes()
        actual_sha = _sha256(data)
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_AGGREGATE) from exc
    if actual_sha != expected_sha:
        raise ValidationError(
            f"{label} sha mismatch: {actual_sha} != {expected_sha}", RC_AGGREGATE
        )
    return path, data


def _scan_session_rows(
    sessions_root: Path, not_before: datetime, not_after: datetime
) -> list[tuple[str, int, str, str, str]]:
    found: list[tuple[str, int, str, str, str]] = []
    for path in sorted(sessions_root.rglob("rollout-*.jsonl"), key=os.fspath):
        rows, _ = _json_lines(path)
        for row in rows:
            payload = row.get("payload")
            if row.get("type") != "session_meta" or not isinstance(payload, dict):
                continue
            raw_timestamp = row.get("timestamp") or payload.get("timestamp")
            timestamp = _parse_timestamp(raw_timestamp)
            if timestamp is None or not not_before <= timestamp <= not_after:
                continue
            session_id = payload.get("session_id")
            identity = payload.get("id")
            if not isinstance(identity, str) or not isinstance(session_id, str):
                continue
            found.append(
                (
                    os.fspath(path.resolve()),
                    path.stat().st_ino,
                    identity,
                    session_id,
                    str(raw_timestamp),
                )
            )
    return found


def _read_frozen_repo_file(relative_path: str, label: str) -> bytes:
    relative = Path(relative_path)
    if (
        relative.is_absolute()
        or "\\" in relative_path
        or not relative.parts
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValidationError(f"{label} path is not repository-relative", RC_ROUTING)
    candidate = _ROOT
    try:
        for index, component in enumerate(relative.parts):
            candidate /= component
            metadata = candidate.lstat()
            final = index == len(relative.parts) - 1
            if stat.S_ISLNK(metadata.st_mode):
                raise ValidationError(f"{label} path contains a symlink", RC_ROUTING)
            if final:
                if not stat.S_ISREG(metadata.st_mode):
                    raise ValidationError(
                        f"{label} is not a regular file", RC_ROUTING
                    )
            elif not stat.S_ISDIR(metadata.st_mode):
                raise ValidationError(
                    f"{label} parent is not a directory", RC_ROUTING
                )
        before = candidate.lstat()
        data = candidate.read_bytes()
        after = candidate.lstat()
    except ValidationError:
        raise
    except OSError as exc:
        raise ValidationError(f"{label} cannot be read: {exc}", RC_ROUTING) from exc
    if (
        before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ValidationError(f"{label} changed while it was read", RC_ROUTING)
    return data


def _validate_frozen_price_snapshot_record(
    record: Any,
) -> tuple[str, dict[str, Any]]:
    if not isinstance(record, dict):
        raise ValidationError("price_snapshot must be an object", RC_ROUTING)
    if set(record) != {"path", "sha256"}:
        raise ValidationError("price_snapshot field set mismatch", RC_ROUTING)
    if record["path"] != FROZEN_PRICE_SNAPSHOT_PATH:
        raise ValidationError("price_snapshot path mismatch", RC_ROUTING)
    if record["sha256"] != FROZEN_PRICE_SNAPSHOT_SHA256:
        raise ValidationError("price_snapshot sha256 mismatch", RC_ROUTING)

    snapshot_bytes = _read_frozen_repo_file(
        FROZEN_PRICE_SNAPSHOT_PATH, "frozen price snapshot"
    )
    actual_snapshot_sha256 = _sha256(snapshot_bytes)
    if actual_snapshot_sha256 != FROZEN_PRICE_SNAPSHOT_SHA256:
        raise ValidationError(
            "frozen price snapshot bytes sha256 mismatch", RC_ROUTING
        )
    try:
        snapshot_value = json.loads(snapshot_bytes)
        validated = PRICE_SNAPSHOT.validate_price_snapshot(snapshot_value)
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        PRICE_SNAPSHOT.PriceSnapshotError,
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationError(
            f"frozen price snapshot validation failed: {exc}", RC_ROUTING
        ) from exc
    if validated.get("price_table_version") != FROZEN_PRICE_VERSION:
        raise ValidationError("frozen price version mismatch", RC_ROUTING)
    excerpt = validated.get("excerpt")
    if not isinstance(excerpt, dict):
        raise ValidationError("frozen price excerpt record missing", RC_ROUTING)
    if excerpt.get("path") != FROZEN_PRICE_EXCERPT_PATH:
        raise ValidationError("frozen price excerpt path mismatch", RC_ROUTING)
    if excerpt.get("sha256") != FROZEN_PRICE_EXCERPT_SHA256:
        raise ValidationError("frozen price excerpt sha256 mismatch", RC_ROUTING)
    excerpt_bytes = _read_frozen_repo_file(
        FROZEN_PRICE_EXCERPT_PATH, "frozen price excerpt"
    )
    if _sha256(excerpt_bytes) != FROZEN_PRICE_EXCERPT_SHA256:
        raise ValidationError(
            "frozen price excerpt bytes sha256 mismatch", RC_ROUTING
        )
    if len(excerpt_bytes) != excerpt.get("byte_length"):
        raise ValidationError(
            "frozen price excerpt byte length mismatch", RC_ROUTING
        )
    return FROZEN_PRICE_VERSION, validated


def _schedule_expected_price_version(
    schedule: Mapping[str, Any],
) -> tuple[str | None, dict[str, Any] | None]:
    slots = schedule.get("slots")
    if not isinstance(slots, list):
        return None, None
    non_null_versions = [
        row.get("price_version")
        for row in slots
        if isinstance(row, Mapping) and row.get("price_version") is not None
    ]
    if not non_null_versions:
        return None, None
    schema_version = schedule.get("schema_version")
    if (
        type(schema_version) is not int
        or schema_version != SCHEDULE_SCHEMA_VERSION
    ):
        return None, None
    if any(value != FROZEN_PRICE_VERSION for value in non_null_versions):
        return None, None
    return _validate_frozen_price_snapshot_record(schedule.get("price_snapshot"))


class _ValidatedScheduleSlots(list[dict[str, Any]]):
    """Validated schedule rows plus the exact trees observed while validating."""

    def __init__(
        self,
        rows: Iterable[dict[str, Any]] = (),
        *,
        price_snapshot: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(rows)
        self.price_snapshot = price_snapshot
        self.has_material_schedule_descriptor: bool | None = None
        self.material_manifest_sha256: str | None = None


def _validated_slots_price_version(
    slots: Sequence[Mapping[str, Any]],
    reasons: list[str] | None = None,
) -> str | None:
    versions = {slot.get("price_version") for slot in slots}
    if not versions or versions == {None}:
        return None
    if versions == {FROZEN_PRICE_VERSION}:
        return FROZEN_PRICE_VERSION
    reason = "schedule price_version concentration must be all null or all frozen"
    if reasons is not None:
        reasons.append(reason)
        return None
    raise ValidationError(reason, RC_ROUTING)


def _slot_dimensions(
    slot: Mapping[str, Any],
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
    expected_price_version: str | None = None,
) -> dict[str, Any]:
    """Return the canonical task/stage/model/cache dimensions for one slot."""
    if not isinstance(slot, Mapping):
        raise ValidationError("schedule slot is not an object", RC_ROUTING)
    task_id = resolve_benchmark_task_id(
        slot.get("benchmark_task_id"),
        case=slot.get("case"),
        legacy_case=slot.get("legacy_case"),
        manifest=task_manifest,
    )
    task = _manifest_task(task_id, manifest=task_manifest)
    legacy_case = slot.get("legacy_case", task["legacy_case"])
    case = slot.get("case", task["legacy_case"])
    if legacy_case != task["legacy_case"]:
        raise ValidationError(
            "schedule legacy_case does not match benchmark task", RC_ROUTING
        )
    slot_stage = slot.get("stage", task.get("stage"))
    task_stage = task.get("stage")
    if (
        expected_price_version is not None
        and type(slot_stage) is not type(task_stage)
    ):
        raise ValidationError(
            "bound schedule stage type does not match benchmark task manifest",
            RC_ROUTING,
        )
    if slot_stage != task_stage:
        raise ValidationError(
            "schedule stage does not match benchmark task manifest", RC_ROUTING
        )
    requested_model = slot.get("requested_model", MODEL)
    if requested_model is None:
        raise ValidationError("schedule requested_model must not be null", RC_ROUTING)
    if not isinstance(requested_model, str) or requested_model not in MODEL_ALLOWLIST:
        raise ValidationError(
            f"schedule requested_model is not allowed: {requested_model}",
            RC_ROUTING,
        )
    cache_condition = slot.get("cache_condition")
    if cache_condition is not None:
        raise ValidationError(
            "schedule slot cache_condition non-null values are not supported without attestation",
            RC_ROUTING,
        )
    price_version = slot.get("price_version")
    if price_version is not None:
        if not isinstance(price_version, str):
            raise ValidationError(
                "schedule slot price_version must be a string or null", RC_ROUTING
            )
        if not price_version:
            raise ValidationError(
                "schedule slot price_version must be non-empty when present",
                RC_ROUTING,
            )
        if (
            expected_price_version is None
            or expected_price_version != FROZEN_PRICE_VERSION
            or price_version != expected_price_version
            or price_version != FROZEN_PRICE_VERSION
        ):
            raise ValidationError(
                "schedule slot price_version does not match the frozen price binding",
                RC_ROUTING,
            )
    oracle_kind = task.get("oracle_kind")
    if oracle_kind not in {"positive", "negative"}:
        raise ValidationError(
            f"task manifest oracle_kind is invalid: {task_id}", RC_ROUTING
        )
    arm = slot.get("arm")
    if not isinstance(arm, str) or not arm:
        raise ValidationError("schedule slot arm must be a non-empty string", RC_ROUTING)
    return {
        "benchmark_task_id": task_id,
        "stage": task.get("stage"),
        "requested_model": requested_model,
        "cache_condition": slot.get("cache_condition"),
        "price_version": slot.get("price_version"),
        "oracle_kind": oracle_kind,
        "legacy_case": legacy_case,
        "case": case,
        "arm": arm,
    }


def _legacy_schedule_view(schedule: Mapping[str, Any]) -> dict[str, Any]:
    """Return a non-mutating v2-compatible view of a legacy schedule."""
    source_schedule = dict(schedule)
    source_schedule.setdefault("schema_version", LEGACY_SCHEMA_VERSION)
    return source_schedule


def _validate_schedule(
    schedule: Mapping[str, Any],
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[list[dict[str, Any]], list[str]]:
    reasons: list[str] = []
    if not isinstance(schedule, Mapping):
        return [], ["schedule is not an object"]

    # Existing schedule.json files omit schema_version.  Treat that omission as
    # a v2 compatibility view without changing the caller's source mapping.
    source_schedule = _legacy_schedule_view(schedule)
    try:
        expected_price_version, price_snapshot = _schedule_expected_price_version(
            source_schedule
        )
        normalized_schedule = normalize_schedule(
            source_schedule,
            manifest=task_manifest,
            expected_price_version=expected_price_version,
        )
    except ValidationError as exc:
        return [], list(exc.reasons)
    slots_value = normalized_schedule.get("slots")
    if not isinstance(slots_value, list):
        return [], ["schedule.slots is not an array"]

    slots = _ValidatedScheduleSlots(price_snapshot=price_snapshot)
    counts: dict[tuple[str, str], int] = {}
    seen: set[str] = set()
    blocks: dict[str, list[dict[str, Any]]] = {}
    for index, raw_row in enumerate(slots_value):
        if not isinstance(raw_row, dict) or not isinstance(
            raw_row.get("slot_id"), str
        ):
            reasons.append("schedule slot row malformed")
            continue
        row = dict(raw_row)
        slot_id = row["slot_id"]
        try:
            dimensions = _slot_dimensions(
                row,
                task_manifest=task_manifest,
                expected_price_version=expected_price_version,
            )
        except ValidationError as exc:
            reasons.extend(f"{slot_id}: {reason}" for reason in exc.reasons)
            dimensions = {}
        else:
            row.update(dimensions)
            counts[(dimensions["benchmark_task_id"], dimensions["arm"])] = (
                counts.get(
                    (dimensions["benchmark_task_id"], dimensions["arm"]), 0
                )
                + 1
            )
        try:
            _assert_arm_neutral_paths([slot_id, str(row.get("block_id", ""))])
        except ValidationError as exc:
            reasons.extend(exc.reasons)
        if slot_id in seen:
            reasons.append(f"duplicate slot_id: {slot_id}")
        seen.add(slot_id)
        for field in (
            "prompt_sha256",
            "snapshot_manifest_sha256",
            "submodule_manifest_sha256",
        ):
            if not isinstance(row.get(field), str) or len(row[field]) != 64:
                reasons.append(f"{slot_id}: {field} missing")
        block_id = row.get("block_id")
        if not isinstance(block_id, str):
            reasons.append(f"{slot_id}: block_id missing")
        else:
            blocks.setdefault(block_id, []).append({**row, "_index": index})
        block_order = row.get("block_order")
        if expected_price_version is not None and type(block_order) is not int:
            reasons.append(
                f"{slot_id}: bound schedule block_order must be an exact integer"
            )
        if block_order not in {1, 2}:
            reasons.append(f"{slot_id}: block_order must be 1 or 2")
        slots.append(row)

    try:
        expected_counts = expected_schedule_from_manifest(
            task_manifest,
            source_schedule,
            expected_price_version=expected_price_version,
        )
    except ValidationError as exc:
        reasons.extend(exc.reasons)
        expected_counts = {}
    if counts != expected_counts:
        reasons.append(f"logical slot cardinality mismatch: {counts}")

    for block_id, rows in blocks.items():
        dimension_pairs = {
            (
                row.get("benchmark_task_id"),
                row.get("stage"),
                row.get("cache_condition"),
                row.get("price_version"),
            )
            for row in rows
        }
        arm_model_pairs = {
            (row.get("arm"), row.get("requested_model")) for row in rows
        }
        if (
            len(rows) != 2
            or len(dimension_pairs) != 1
            or len(arm_model_pairs) != 2
            or [row.get("block_order") for row in rows] != [1, 2]
            or rows[1]["_index"] != rows[0]["_index"] + 1
        ):
            reasons.append(f"sequential crossover block mismatch: {block_id}")

    task_ids = {
        row.get("benchmark_task_id")
        for row in slots
        if isinstance(row.get("benchmark_task_id"), str)
    }
    for task_id in sorted(task_ids):
        task_rows = [
            row for row in slots if row.get("benchmark_task_id") == task_id
        ]
        for field in ("prompt_sha256", "snapshot_manifest_sha256"):
            if len({row.get(field) for row in task_rows}) != 1:
                reasons.append(f"{task_id}: {field} concentration is not 1")
    submodule_states = {
        row.get("submodule_manifest_sha256") for row in slots
    }
    if len(submodule_states) != 1:
        reasons.append(
            "POS/NEG submodule initialization and gitlink state mismatch"
        )
    _validated_slots_price_version(slots, reasons)
    return slots, reasons


def _load_adjudication(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    slots: Sequence[Mapping[str, Any]],
    final_attempts: Mapping[str, Mapping[str, Any]],
    *,
    snapshot_verified_run_ids: set[str],
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[dict[str, dict[str, Any]], list[str]]:
    reasons: list[str] = []
    try:
        packet_state_path = _artifact_path(
            manifest_path, manifest.get("packet_state"), "packet_state"
        )
        verdict_log_path = _artifact_path(
            manifest_path, manifest.get("verdict_log"), "verdict_log"
        )
        freeze_path = _artifact_path(
            manifest_path, manifest.get("verdict_freeze"), "verdict_freeze"
        )
        map_path = _artifact_path(
            manifest_path, manifest.get("revealed_map"), "revealed_map"
        )
        packet_state = _load_json_object(packet_state_path)
        freeze = _load_json_object(freeze_path)
        revealed = _load_json_object(map_path)
    except ValidationError as exc:
        return {}, list(exc.reasons)
    expected_task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    for label, artifact in (
        ("packet state", packet_state),
        ("verdict freeze", freeze),
        ("revealed mapping", revealed),
    ):
        if artifact.get("task_manifest_sha256") != expected_task_manifest_sha256:
            reasons.append(f"{label} task_manifest_sha256 mismatch")
    verdict_rows, verdict_issues = _json_lines(verdict_log_path)
    reasons.extend(verdict_issues)
    if (
        packet_state.get("mask_strength") != "same-owner-advisory"
        or revealed.get("mask_strength") != "same-owner-advisory"
    ):
        reasons.append("label-mask residual strength field mismatch")
    verdict_file_sha = _sha256(verdict_log_path.read_bytes())
    if freeze.get("verdict_log_sha256") != verdict_file_sha:
        reasons.append("verdict freeze does not bind append-only verdict bytes")
    if revealed.get("verdict_freeze_sha256") != _sha256(freeze_path.read_bytes()):
        reasons.append("revealed map predates or mismatches verdict freeze")
    if not (
        packet_state_path.stat().st_mtime_ns
        <= verdict_log_path.stat().st_mtime_ns
        <= freeze_path.stat().st_mtime_ns
        <= map_path.stat().st_mtime_ns
    ):
        reasons.append("adjudication artifact freshness order mismatch")
    packet_rows = packet_state.get("packets")
    map_rows = revealed.get("mapping")
    if not all(isinstance(value, list) for value in (packet_rows, verdict_rows, map_rows)):
        return {}, [*reasons, "adjudication arrays missing"]
    try:
        current_packet_digests = _packet_digests(
            packet_state_path, packet_rows
        )
    except ValidationError as exc:
        current_packet_digests = {}
        reasons.extend(exc.reasons)
    frozen_packet_digests = freeze.get("packet_sha256_at_freeze")
    if (
        not isinstance(frozen_packet_digests, dict)
        or frozen_packet_digests != current_packet_digests
    ):
        reasons.append("adjudication freeze/current packet digest mismatch")
    packets = {
        row.get("packet_id"): row
        for row in packet_rows
        if isinstance(row, dict) and isinstance(row.get("packet_id"), str)
    }
    if any(
        not isinstance(row, dict)
        or set(row) != {"packet_id", "filename"}
        for row in packet_rows
    ):
        reasons.append("evaluator packet state contains join metadata")
    verdict_by_packet: dict[str, dict[str, dict[str, Any]]] = {}
    for row in verdict_rows:
        if not isinstance(row, dict) or not isinstance(row.get("packet_id"), str):
            reasons.append("verdict log row malformed")
            continue
        try:
            _validate_verdict_row(
                row, set(packets), task_manifest=task_manifest
            )
        except ValidationError as exc:
            reasons.extend(exc.reasons)
        reader = row.get("reader")
        if reader not in {"parent", "second-reader"}:
            reasons.append(f"{row.get('packet_id')}: verdict reader invalid")
            continue
        verdict_by_packet.setdefault(row["packet_id"], {})[str(reader)] = row
    mapping = {
        row.get("packet_id"): row
        for row in map_rows
        if isinstance(row, dict) and isinstance(row.get("packet_id"), str)
    }
    if not (
        len(packets) == len(packet_rows)
        and all(set(rows) == {"parent", "second-reader"} for rows in verdict_by_packet.values())
        and len(verdict_rows) == len(packet_rows) * 2
        and len(mapping) == len(map_rows)
        and set(packets) == set(verdict_by_packet) == set(mapping)
        and {row.get("run_id") for row in mapping.values()} == {
            attempt.get("run_id") for attempt in final_attempts.values()
        }
    ):
        reasons.append("packet/verdict/revealed mapping is not bijective")
    joined: dict[str, dict[str, Any]] = {}
    judgment_rows = manifest.get("judgments")
    if not isinstance(judgment_rows, list):
        return {}, [*reasons, "manifest.judgments is not an array"]
    judgments = {
        row.get("slot_id"): row
        for row in judgment_rows
        if isinstance(row, dict) and isinstance(row.get("slot_id"), str)
    }
    if len(judgments) != len(judgment_rows) or set(judgments) != {
        str(row.get("slot_id")) for row in slots
    }:
        reasons.append("judgment/logical slot set mismatch")
    slot_by_run = {
        final_attempts[row["slot_id"]].get("run_id"): row
        for row in slots
        if row.get("slot_id") in final_attempts
    }
    slot_dimensions = _slot_dimension_map(
        slots, reasons, task_manifest=task_manifest
    )
    for packet_id, mapping_row in mapping.items():
        run_id = mapping_row.get("run_id")
        if run_id not in snapshot_verified_run_ids:
            reasons.append(
                f"{packet_id}: material packet source run lacks replayed "
                f"snapshot evidence: {run_id}"
            )
        slot = slot_by_run.get(run_id)
        attempt = next(
            (
                value
                for value in final_attempts.values()
                if value.get("run_id") == run_id
            ),
            None,
        )
        if slot is None or attempt is None:
            reasons.append(f"{packet_id}: run_id join failed")
            continue
        slot_id = str(slot["slot_id"])
        dimensions = slot_dimensions.get(slot_id)
        if dimensions is None:
            reasons.append(
                f"{packet_id}: schedule slot dimension join failed: {slot_id}"
            )
            continue
        packet = packets.get(packet_id, {})
        reader_rows = verdict_by_packet.get(packet_id, {})
        parent_verdict = reader_rows.get("parent", {})
        second_verdict = reader_rows.get("second-reader", {})
        try:
            known_finding_ids = _adjudication_known_finding_ids_for_task(
                task_manifest,
                dimensions["benchmark_task_id"],
            )
        except ValidationError as exc:
            reasons.extend(f"{packet_id}: {reason}" for reason in exc.reasons)
            continue
        for reader, raw_verdict in reader_rows.items():
            for finding in raw_verdict.get("findings", []):
                if isinstance(finding, dict):
                    equivalent = finding.get("equivalent_to")
                    if (
                        equivalent is not None
                        and equivalent not in known_finding_ids
                    ):
                        reasons.append(
                            f"{packet_id}: {reader} finding equivalent_to "
                            "is unknown "
                            f"for benchmark task {dimensions['benchmark_task_id']}: "
                            f"{equivalent}"
                        )
        agreement = parent_verdict.get("r1_detected") == second_verdict.get(
            "r1_detected"
        )
        finding_keys: dict[
            tuple[Any, Any, Any, Any], dict[str, dict[str, Any]]
        ] = {}
        for reader, verdict in reader_rows.items():
            for finding in verdict.get("findings", []):
                if not isinstance(finding, dict):
                    continue
                key = (
                    finding.get("equivalent_to"),
                    finding.get("root_cause"),
                    finding.get("severity"),
                    finding.get("must_fix"),
                )
                finding_keys.setdefault(key, {})[reader] = finding
        conservative_findings = [
            parent_finding
            for reader_findings in finding_keys.values()
            if set(reader_findings) == {"parent", "second-reader"}
            and (parent_finding := reader_findings["parent"]).get("real") is True
            and reader_findings["second-reader"].get("real") is True
        ]
        verdict = {
            "oracle_kind": dimensions["oracle_kind"],
            "r1_detected": (
                parent_verdict.get("r1_detected") is True
                and second_verdict.get("r1_detected") is True
            ),
            "findings": conservative_findings,
            "reader_agreement": agreement,
            "reader_rows_sha256": _sha256(
                _canonical_bytes(
                    [reader_rows[key] for key in ("parent", "second-reader")]
                )
            ),
        }
        output_sha = attempt.get("output_sha256")
        if any(
            row.get("packet_sha256_at_read") != output_sha
            for row in reader_rows.values()
        ):
            reasons.append(
                f"{packet_id}: verdict read-time packet/output sha mismatch"
            )
        if (
            not isinstance(frozen_packet_digests, dict)
            or frozen_packet_digests.get(packet_id) != output_sha
        ):
            reasons.append(f"{packet_id}: frozen packet/output sha mismatch")
        row_sha = _sha256(_canonical_bytes(verdict))
        judgment = judgments.get(str(slot["slot_id"]), {})
        required = {
            "packet_id": packet_id,
            "score_input_sha256": output_sha,
            "combined_verdict_sha256": row_sha,
            "r1_detected": verdict.get("r1_detected"),
            "reader_agreement": verdict.get("reader_agreement"),
        }
        for field, expected in required.items():
            if judgment.get(field) != expected:
                reasons.append(f"{slot['slot_id']}: adjudication {field} mismatch")
        if (
            mapping_row.get("packet_sha256") != output_sha
            or mapping_row.get("score_input_sha256") != output_sha
        ):
            reasons.append(f"{packet_id}: revealed packet/output sha mismatch")
        filename = packet.get("filename")
        if not isinstance(filename, str) or not re.fullmatch(
            r"packet-[0-9a-f]{32}\.md", filename
        ):
            reasons.append(f"{packet_id}: packet filename is not uniform")
        else:
            packet_path = packet_state_path.parent / filename
            try:
                packet_bytes = packet_path.read_bytes()
            except OSError as exc:
                reasons.append(f"{packet_id}: packet cannot be read: {exc}")
            else:
                if _sha256(packet_bytes) != output_sha:
                    reasons.append(f"{packet_id}: packet body is not exact output")
        joined[slot["slot_id"]] = verdict
    return joined, reasons


def _apply_pair_invalidations(
    attempts: Sequence[dict[str, Any]],
) -> None:
    """Invalidate the mate of a technical failure without dropping resources."""
    generations: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for row in attempts:
        block_id = row.get("block_id")
        attempt = row.get("attempt")
        if isinstance(block_id, str) and isinstance(attempt, int):
            generations.setdefault((block_id, attempt), []).append(row)
    for (block_id, generation), rows in generations.items():
        technical = [
            row
            for row in rows
            if row.get("failure_class") == "technical-invalid"
        ]
        if not technical:
            continue
        triggers = sorted(
            str(row.get("run_id"))
            for row in technical
            if isinstance(row.get("run_id"), str)
        )
        for row in rows:
            if row.get("failure_class") in {
                "technical-invalid",
                "pair-invalidated",
            }:
                continue
            row["individual_failure_class"] = row.get("failure_class")
            row["failure_class"] = "pair-invalidated"
            row["failure_classes"] = ["pair-invalidated"]
            row["valid"] = False
            row["pair_invalidation"] = {
                "block_id": block_id,
                "generation": generation,
                "technical_run_ids": triggers,
            }


def _retry_lineage_reasons(
    grouped: Mapping[str, Sequence[Mapping[str, Any]]],
) -> list[str]:
    reasons: list[str] = []
    for slot_id, rows in grouped.items():
        ordered = sorted(rows, key=lambda item: int(item["attempt"]))
        numbers = [int(item["attempt"]) for item in ordered]
        if numbers != list(range(1, len(numbers) + 1)):
            reasons.append(f"{slot_id}: attempt sequence is not contiguous")
        for index, previous in enumerate(ordered[:-1]):
            if previous.get("failure_class") not in {
                "technical-invalid",
                "pair-invalidated",
            }:
                reasons.append(
                    f"{slot_id}: retry parent was not pair-invalidated/"
                    "technical-invalid"
                )
            if ordered[index + 1].get("parent_run_id") != previous.get("run_id"):
                reasons.append(f"{slot_id}: retry parent_run_id mismatch")
    return reasons


_AXIS_FIELDS = (
    "benchmark_task_id",
    "stage",
    "requested_model",
    "cache_condition",
    "price_version",
)

_COST_TOKEN_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
_COST_QUANTUM = Decimal("0.00000001")
_COST_DENOMINATOR = Decimal(1_000_000)
_COST_PAIR_UNIT_STATUSES = ("observed", "unavailable", "not-incurred")


def _cost_rounding() -> dict[str, Any]:
    return {
        "decimal_places": 8,
        "mode": "ROUND_HALF_EVEN",
    }


def _load_frozen_price_snapshot_for_cost() -> dict[str, Any]:
    """Read, pin, and validate the cost snapshot from one byte observation."""
    try:
        snapshot_bytes = _read_frozen_repo_file(
            FROZEN_PRICE_SNAPSHOT_PATH, "frozen price snapshot for cost"
        )
    except ValidationError as exc:
        raise ValidationError(exc.reasons, RC_AGGREGATE) from exc
    if _sha256(snapshot_bytes) != FROZEN_PRICE_SNAPSHOT_SHA256:
        raise ValidationError(
            "frozen price snapshot bytes sha256 mismatch for cost",
            RC_AGGREGATE,
        )
    try:
        snapshot_value = json.loads(snapshot_bytes)
        validated = PRICE_SNAPSHOT.validate_price_snapshot(snapshot_value)
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        PRICE_SNAPSHOT.PriceSnapshotError,
        TypeError,
        ValueError,
    ) as exc:
        raise ValidationError(
            f"frozen price snapshot cost validation failed: {exc}",
            RC_AGGREGATE,
        ) from exc
    if validated.get("price_table_version") != FROZEN_PRICE_VERSION:
        raise ValidationError(
            "frozen price version mismatch for cost", RC_AGGREGATE
        )
    return validated


def _format_cost_amount(amount: Decimal) -> str:
    with localcontext() as context:
        context.prec = 64
        rounded = amount.quantize(_COST_QUANTUM, rounding=ROUND_HALF_EVEN)
    return format(rounded, ".8f")


def _not_launched_accounting_reason(attempt: Mapping[str, Any]) -> str | None:
    nonzero_or_malformed = [
        field
        for field in _COST_TOKEN_FIELDS
        if type(attempt.get(field)) is not int or attempt.get(field) != 0
    ]
    if nonzero_or_malformed:
        return (
            "not-launched token fields must be exact integer zeroes: "
            + ", ".join(nonzero_or_malformed)
        )
    if type(attempt.get("model_calls")) is not int or attempt.get("model_calls") != 0:
        return "not-launched model_calls must be exact integer zero"
    return None


def _cost_token_availability(
    attempt: Mapping[str, Any],
) -> tuple[str, str | None]:
    prelaunch_failure = attempt.get("prelaunch_failure") is not None
    paired_not_launched = (
        attempt.get("failure_class") == "pair-invalidated"
        and attempt.get("individual_failure_class") is None
        and attempt.get("treatment_started") is False
    )
    if prelaunch_failure or paired_not_launched:
        malformed_reason = _not_launched_accounting_reason(attempt)
        if malformed_reason is not None:
            raise ValidationError(malformed_reason, RC_AGGREGATE)
        return (
            "not-incurred",
            "attempt failed before launch"
            if prelaunch_failure
            else "paired attempt was not launched",
        )
    failure_reasons = attempt.get("failure_reasons")
    if isinstance(failure_reasons, list) and any(
        str(reason).startswith("replay failed:") for reason in failure_reasons
    ):
        return "unavailable", "receipt replay failed"

    values: list[int] = []
    for field in _COST_TOKEN_FIELDS:
        value = attempt.get(field)
        if type(value) is not int:
            raise ValidationError(
                f"normalized cost {field} is missing or not an exact integer",
                RC_AGGREGATE,
            )
        if value < 0:
            raise ValidationError(
                f"normalized cost {field} is negative", RC_AGGREGATE
            )
        values.append(value)
    if not any(values):
        # Prelaunch rows are populated with exact integer zeroes.  With no
        # independent observation marker, four zeroes cannot prove observed
        # zero usage and must not enter a cost denominator.
        return "unavailable", "all token fields are zero without observation evidence"
    return "observed", None


def _normalized_cost_metadata(
    *,
    requested_model: str,
    price_version: str,
    price_snapshot: Mapping[str, Any],
) -> tuple[dict[str, Any], Mapping[str, Any]]:
    if not isinstance(price_version, str) or price_version != FROZEN_PRICE_VERSION:
        raise ValidationError(
            "normalized cost price_version does not match the frozen version",
            RC_AGGREGATE,
        )
    if price_snapshot.get("price_table_version") != price_version:
        raise ValidationError(
            "normalized cost snapshot/version mismatch", RC_AGGREGATE
        )
    sku_mapping = price_snapshot.get("sku_mapping")
    if not isinstance(sku_mapping, Mapping) or requested_model not in sku_mapping:
        raise ValidationError(
            f"normalized cost requested model has no frozen SKU: {requested_model}",
            RC_AGGREGATE,
        )
    sku = sku_mapping[requested_model]
    if not isinstance(sku, Mapping):
        raise ValidationError(
            "normalized cost frozen SKU is malformed", RC_AGGREGATE
        )
    prices = sku.get("prices")
    if not isinstance(prices, Mapping):
        raise ValidationError(
            "normalized cost frozen price table is missing", RC_AGGREGATE
        )
    unknown = price_snapshot.get("unknown_token_categories")
    if not isinstance(unknown, list):
        raise ValidationError(
            "normalized cost unaccounted category list is missing",
            RC_AGGREGATE,
        )
    metadata = {
        "currency": price_snapshot.get("currency"),
        "price_unit": price_snapshot.get("price_unit"),
        "unit_prices": {str(key): str(value) for key, value in prices.items()},
        "price_version": price_version,
        "unaccounted_token_categories": list(unknown),
        "coverage_status": "partial",
        "certification_status": "not-certified",
        "reasoning_output_tokens_accounting": price_snapshot.get(
            "reasoning_output_tokens_accounting"
        ),
    }
    return metadata, sku


def _normalized_cost_comparability(
    *,
    dimensions: Mapping[str, Any],
    metadata: Mapping[str, Any],
    material_manifest_sha256: str | None,
    attempt_count: int,
    unavailable_count: int,
    not_incurred_count: int,
    scheduled_attempt_count: int,
    pair_units_by_status: Mapping[str, Iterable[tuple[str, int]]],
) -> dict[str, Any]:
    """Build deterministic, non-gating metadata for partial cost totals."""
    rule = (
        "basis_key and accounted_total_key must both match exactly to compare "
        "partial accounted component totals; this does not establish "
        "comparability of per-attempt averages, complete costs, or actual "
        "billed amounts"
    )
    if material_manifest_sha256 is None:
        rule += (
            "; when comparison_universe.material_manifest_sha256 is null, "
            "comparison is limited to rows in the same aggregate result"
        )
    return {
        "rule": rule,
        "basis_key": {
            "comparison_scope": {
                "benchmark_task_id": dimensions.get("benchmark_task_id"),
                "stage": dimensions.get("stage"),
                "cache_condition": dimensions.get("cache_condition"),
            },
            "comparison_universe": {
                "material_manifest_sha256": material_manifest_sha256,
            },
            "accounting_basis": {
                "price_version": metadata.get("price_version"),
                "currency": metadata.get("currency"),
                "price_unit": metadata.get("price_unit"),
                "unaccounted_token_categories": list(
                    metadata.get("unaccounted_token_categories", [])
                ),
                "coverage_status": metadata.get("coverage_status"),
                "reasoning_output_tokens_accounting": metadata.get(
                    "reasoning_output_tokens_accounting"
                ),
                "rounding": _cost_rounding(),
            },
        },
        "accounted_total_key": {
            "attempt_count": attempt_count,
            "unavailable_count": unavailable_count,
            "not_incurred_count": not_incurred_count,
            "scheduled_attempt_count": scheduled_attempt_count,
            "pair_units_by_status": {
                status: [
                    {"block_id": block_id, "attempt": attempt}
                    for block_id, attempt in sorted(
                        set(pair_units_by_status.get(status, ()))
                    )
                ]
                for status in _COST_PAIR_UNIT_STATUSES
            },
        },
    }


def _normalized_cost_for_attempt(
    attempt: Mapping[str, Any],
    *,
    requested_model: str,
    price_version: str,
    price_snapshot: Mapping[str, Any],
) -> dict[str, Any]:
    metadata, sku = _normalized_cost_metadata(
        requested_model=requested_model,
        price_version=price_version,
        price_snapshot=price_snapshot,
    )
    availability, failure_reason = _cost_token_availability(attempt)
    if availability != "observed":
        return {
            "status": availability,
            "token_availability": availability,
            **metadata,
            "failure_reason": failure_reason,
        }

    tokens = {field: int(attempt[field]) for field in _COST_TOKEN_FIELDS}
    if tokens["cached_input_tokens"] > tokens["input_tokens"]:
        raise ValidationError(
            "normalized cost cached_input_tokens exceeds input_tokens",
            RC_AGGREGATE,
        )
    if tokens["reasoning_output_tokens"] > tokens["output_tokens"]:
        raise ValidationError(
            "normalized cost reasoning_output_tokens exceeds output_tokens",
            RC_AGGREGATE,
        )

    mapping = sku.get("receipt_token_mapping")
    prices = sku.get("prices")
    if not isinstance(mapping, Mapping) or not isinstance(prices, Mapping):
        raise ValidationError(
            "normalized cost frozen SKU accounting is missing", RC_AGGREGATE
        )
    components: dict[str, Any] = {}
    total = Decimal(0)
    with localcontext() as context:
        context.prec = 64
        for category, raw_rule in mapping.items():
            assert isinstance(category, str)
            assert isinstance(raw_rule, Mapping)
            operation = raw_rule.get("operation")
            fields = raw_rule.get("receipt_fields")
            # PRICE_SNAPSHOT.validate_price_snapshot is the upstream authority
            # for the closed operation/field grammar, exclusion of reasoning
            # tokens from mappings, and finite positive decimal price strings.
            if operation is None:
                assert fields == []
                continue
            if operation == "identity":
                assert isinstance(fields, list) and len(fields) == 1
                component_tokens = tokens[fields[0]]
            elif operation == "input_tokens-minus-cached_input_tokens":
                assert isinstance(fields, list) and len(fields) == 2
                component_tokens = tokens[fields[0]] - tokens[fields[1]]
            else:  # unreachable after the upstream snapshot validator
                raise AssertionError("validated receipt mapping operation")
            unit_price = str(prices[category])
            amount = Decimal(component_tokens) * Decimal(unit_price) / (
                _COST_DENOMINATOR
            )
            total += amount
            components[category] = {
                "tokens": component_tokens,
                "unit_price": unit_price,
                "amount": _format_cost_amount(amount),
            }
    return {
        "status": "partial",
        "token_availability": "observed",
        **metadata,
        "accounted_amount": _format_cost_amount(total),
        "components": components,
        "rounding": _cost_rounding(),
    }


def _aggregate_normalized_costs(
    attempts: Sequence[Mapping[str, Any]],
    slot_dimensions: Mapping[str, Mapping[str, Any]],
    reasons: list[str],
    *,
    price_version: str,
    price_snapshot: Mapping[str, Any],
    material_manifest_sha256: str | None = None,
) -> tuple[list[dict[str, Any] | None], list[dict[str, Any]]]:
    per_attempt: list[dict[str, Any] | None] = []
    axes: dict[tuple[Any, ...], dict[str, Any]] = {}
    axis_pair_units: dict[
        tuple[Any, ...], dict[str, set[tuple[str, int]]]
    ] = {}
    for attempt in attempts:
        run_id = str(attempt.get("run_id"))
        dimensions = slot_dimensions.get(str(attempt.get("slot_id")))
        if dimensions is None:
            per_attempt.append(None)
            continue
        try:
            cost = _normalized_cost_for_attempt(
                attempt,
                requested_model=str(dimensions["requested_model"]),
                price_version=price_version,
                price_snapshot=price_snapshot,
            )
        except ValidationError as exc:
            metadata, _ = _normalized_cost_metadata(
                requested_model=str(dimensions["requested_model"]),
                price_version=price_version,
                price_snapshot=price_snapshot,
            )
            detail = "; ".join(exc.reasons)
            cost = {
                "status": "unavailable",
                "token_availability": "unavailable",
                **metadata,
                "failure_reason": detail,
            }
            reasons.extend(
                f"{run_id}: normalized cost unavailable: {reason}"
                for reason in exc.reasons
            )
        key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
            dimensions["arm"],
        )
        axis = axes.get(key)
        if axis is None:
            axis = {
                **{
                    field: key[index]
                    for index, field in enumerate(_AXIS_FIELDS)
                },
                "arm": key[-1],
                "accounted_amount": "0.00000000",
                "attempt_count": 0,
                "unavailable_count": 0,
                "not_incurred_count": 0,
                "scheduled_attempt_count": 0,
                "currency": cost["currency"],
                "price_unit": cost["price_unit"],
                "unit_prices": dict(cost["unit_prices"]),
                "price_version": cost["price_version"],
                "unaccounted_token_categories": list(
                    cost["unaccounted_token_categories"]
                ),
                "coverage_status": "partial",
                "certification_status": "not-certified",
                "reasoning_output_tokens_accounting": cost[
                    "reasoning_output_tokens_accounting"
                ],
            }
            axes[key] = axis
            axis_pair_units[key] = {
                status: set() for status in _COST_PAIR_UNIT_STATUSES
            }
        axis["scheduled_attempt_count"] += 1
        availability = cost.get("token_availability")
        block_id = attempt.get("block_id")
        attempt_number = attempt.get("attempt")
        pair_unit = (
            (block_id, attempt_number)
            if isinstance(block_id, str) and type(attempt_number) is int
            else None
        )
        per_attempt_pair_units = {
            status: (
                {pair_unit}
                if status == availability and pair_unit is not None
                else set()
            )
            for status in _COST_PAIR_UNIT_STATUSES
        }
        if availability in axis_pair_units[key] and pair_unit is not None:
            axis_pair_units[key][availability].add(pair_unit)
        per_attempt_counts = {
            "attempt_count": int(availability == "observed"),
            "unavailable_count": int(availability == "unavailable"),
            "not_incurred_count": int(availability == "not-incurred"),
            "scheduled_attempt_count": 1,
        }
        cost["comparability"] = _normalized_cost_comparability(
            dimensions=dimensions,
            metadata=cost,
            material_manifest_sha256=material_manifest_sha256,
            **per_attempt_counts,
            pair_units_by_status=per_attempt_pair_units,
        )
        per_attempt.append(cost)
        if availability == "unavailable":
            axis["unavailable_count"] += 1
            continue
        if availability == "not-incurred":
            axis["not_incurred_count"] += 1
            continue
        if availability != "observed":
            raise AssertionError("normalized cost token availability")
        axis["accounted_amount"] = _format_cost_amount(
            Decimal(axis["accounted_amount"])
            + Decimal(str(cost["accounted_amount"]))
        )
        axis["attempt_count"] += 1
    for key, axis in axes.items():
        axis["comparability"] = _normalized_cost_comparability(
            dimensions=axis,
            metadata=axis,
            material_manifest_sha256=material_manifest_sha256,
            attempt_count=int(axis["attempt_count"]),
            unavailable_count=int(axis["unavailable_count"]),
            not_incurred_count=int(axis["not_incurred_count"]),
            scheduled_attempt_count=int(axis["scheduled_attempt_count"]),
            pair_units_by_status=axis_pair_units[key],
        )
    return per_attempt, list(axes.values())


def _slot_dimension_map(
    slots: Sequence[Mapping[str, Any]],
    reasons: list[str],
    *,
    task_manifest: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    dimensions: dict[str, dict[str, Any]] = {}
    expected_price_version = _validated_slots_price_version(slots, reasons)
    for slot in slots:
        slot_id = str(slot.get("slot_id"))
        try:
            dimensions[slot_id] = _slot_dimensions(
                slot,
                task_manifest=task_manifest,
                expected_price_version=expected_price_version,
            )
        except ValidationError as exc:
            reasons.extend(f"{slot_id}: {reason}" for reason in exc.reasons)
    return dimensions


def _attempt_slot_dimensions(
    attempt: Mapping[str, Any],
    slot_dimensions: Mapping[str, Mapping[str, Any]],
    reasons: list[str],
    *,
    task_manifest: Mapping[str, Any],
) -> Mapping[str, Any] | None:
    run_id = str(attempt.get("run_id"))
    slot_id = str(attempt.get("slot_id"))
    dimensions = slot_dimensions.get(slot_id)
    if dimensions is None:
        try:
            dimensions = _slot_dimensions(
                attempt, task_manifest=task_manifest
            )
        except ValidationError as exc:
            reasons.extend(f"{run_id}: {reason}" for reason in exc.reasons)
            return None
    for field in (
        *_AXIS_FIELDS,
        "oracle_kind",
        "legacy_case",
        "case",
        "arm",
    ):
        if field in attempt and attempt.get(field) != dimensions.get(field):
            reasons.append(
                f"{run_id}: attempt {field} does not match scheduled slot"
            )
    return dimensions


def _axis_row(
    dimensions: Mapping[str, Any],
    *,
    arm: str | None = None,
    **values: Any,
) -> dict[str, Any]:
    row = {field: dimensions.get(field) for field in _AXIS_FIELDS}
    row["oracle_kind"] = dimensions.get("oracle_kind")
    if arm is not None:
        row["arm"] = arm
    row.update(values)
    return row


def _is_legacy_projection(
    slot_dimensions: Mapping[str, Mapping[str, Any]],
) -> bool:
    task_ids = {row.get("benchmark_task_id") for row in slot_dimensions.values()}
    shared_dimensions = {
        tuple(row.get(field) for field in _AXIS_FIELDS[1:])
        for row in slot_dimensions.values()
    }
    scheduled_arms = {row.get("arm") for row in slot_dimensions.values()}
    return (
        bool(task_ids)
        and task_ids <= {"POS", "NEG"}
        and len(shared_dimensions) == 1
        and scheduled_arms <= {"max", "high"}
    )


def _aggregate_token_usage_observations(
    attempts: Sequence[Mapping[str, Any]],
    reasons: list[str],
    *,
    slots: Sequence[Mapping[str, Any]] | None = None,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
    slot_dimensions: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    if slot_dimensions is None:
        slot_dimensions = {}
        if slots is not None:
            slot_dimensions = _slot_dimension_map(
                slots, reasons, task_manifest=task_manifest
            )
    by_arm_case: dict[str, dict[str, int]] = {}
    by_axis: dict[tuple[Any, ...], int] = {}
    for dimensions in slot_dimensions.values():
        arm = str(dimensions["arm"])
        case = str(dimensions["case"])
        by_arm_case.setdefault(arm, {}).setdefault(case, 0)
    total_count = 0
    for attempt in attempts:
        if attempt.get("prelaunch_failure") is not None:
            continue
        failure_reasons = attempt.get("failure_reasons")
        if (
            isinstance(failure_reasons, list)
            and any(
                str(reason).startswith("replay failed:")
                for reason in failure_reasons
            )
        ):
            continue
        run_id = str(attempt.get("run_id"))
        observations = attempt.get("token_usage_observations")
        classified = (
            observations.get(ZERO_COMPONENT_TOTAL_ONLY)
            if isinstance(observations, Mapping)
            else None
        )
        if not isinstance(classified, Mapping):
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} receipt observation missing"
            )
            continue
        if classified.get("usage") != "last_token_usage":
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} usage source mismatch"
            )
            continue
        count = classified.get("count")
        indexes = classified.get("indexes")
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} count missing/non-int"
            )
            continue
        if (
            not isinstance(indexes, list)
            or any(
                isinstance(index, bool) or not isinstance(index, int) or index < 1
                for index in indexes
            )
            or indexes != sorted(set(indexes))
            or count != len(indexes)
        ):
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} count/index mismatch"
            )
            continue
        dimensions = _attempt_slot_dimensions(
            attempt,
            slot_dimensions,
            reasons,
            task_manifest=task_manifest,
        )
        if dimensions is None:
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} arm/case missing"
            )
            continue
        arm = str(dimensions["arm"])
        case = str(dimensions["case"])
        by_arm_case.setdefault(arm, {}).setdefault(case, 0)
        by_arm_case[arm][case] += count
        axis_key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
            arm,
        )
        by_axis[axis_key] = by_axis.get(axis_key, 0) + count
        total_count += count
    axis_rows = [
        {
            **{
                field: key[index] for index, field in enumerate(_AXIS_FIELDS)
            },
            "arm": key[-1],
            "count": count,
        }
        for key, count in by_axis.items()
    ]
    observation = {
        "total_count": total_count,
        "by_axis": axis_rows,
    }
    if _is_legacy_projection(slot_dimensions):
        observation["by_arm_case"] = by_arm_case
    return {ZERO_COMPONENT_TOTAL_ONLY: observation}


def _aggregate_verified(
    manifest_path: Path,
    slots: Sequence[Mapping[str, Any]],
    attempts: Sequence[Mapping[str, Any]],
    verdicts: Mapping[str, Mapping[str, Any]],
    reasons: list[str],
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
    has_schedule_descriptor: bool | None = None,
    validated_price_snapshot: Mapping[str, Any] | None = None,
    material_manifest_sha256: str | None = None,
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = {
        str(slot["slot_id"]): [] for slot in slots
    }
    for attempt in attempts:
        grouped.setdefault(str(attempt.get("slot_id")), []).append(attempt)
    slot_dimensions = _slot_dimension_map(
        slots, reasons, task_manifest=task_manifest
    )
    for attempt in attempts:
        _attempt_slot_dimensions(
            attempt,
            slot_dimensions,
            reasons,
            task_manifest=task_manifest,
        )
    normalized_costs: list[dict[str, Any] | None] | None = None
    normalized_cost_axis_ledger: list[dict[str, Any]] | None = None
    aggregate_price_version = _validated_slots_price_version(slots, reasons)
    if has_schedule_descriptor is None:
        has_schedule_descriptor = getattr(
            slots, "has_material_schedule_descriptor", False
        )
    if validated_price_snapshot is None:
        validated_price_snapshot = getattr(slots, "price_snapshot", None)
    if material_manifest_sha256 is None:
        material_manifest_sha256 = getattr(
            slots, "material_manifest_sha256", None
        )
    if (
        aggregate_price_version == FROZEN_PRICE_VERSION
        and has_schedule_descriptor
    ):
        if validated_price_snapshot is None:
            reasons.append(
                "bound schedule validated price snapshot tree is unavailable"
            )
        else:
            (
                normalized_costs,
                normalized_cost_axis_ledger,
            ) = _aggregate_normalized_costs(
                attempts,
                slot_dimensions,
                reasons,
                price_version=aggregate_price_version,
                price_snapshot=validated_price_snapshot,
                material_manifest_sha256=material_manifest_sha256,
            )
    token_usage_observations = _aggregate_token_usage_observations(
        attempts,
        reasons,
        slots=slots,
        task_manifest=task_manifest,
        slot_dimensions=slot_dimensions,
    )
    final_attempts = {
        slot_id: sorted(rows, key=lambda row: int(row["attempt"]))[-1]
        for slot_id, rows in grouped.items()
        if rows
    }
    primary_axes: dict[tuple[Any, ...], dict[str, Any]] = {}
    false_finding_axes: dict[tuple[Any, ...], int] = {}
    axis_oracle_kinds: dict[tuple[Any, ...], str] = {}
    novel_by_root: dict[str, dict[str, Any]] = {}
    novel_by_axis: dict[tuple[Any, ...], dict[str, Any]] = {}
    for slot in slots:
        slot_id = str(slot["slot_id"])
        dimensions = slot_dimensions.get(slot_id)
        if dimensions is None:
            continue
        verdict = verdicts.get(slot_id, {})
        if verdict.get("oracle_kind") != dimensions["oracle_kind"]:
            reasons.append(
                f"{slot_id}: adjudication oracle_kind does not match scheduled slot"
            )
        axis_key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
            dimensions["arm"],
        )
        axis_oracle_kinds[axis_key] = str(dimensions["oracle_kind"])
        if dimensions["oracle_kind"] == "positive":
            primary_row = primary_axes.setdefault(
                axis_key,
                _axis_row(dimensions, arm=dimensions["arm"], k=0, n=0),
            )
            primary_row["n"] += 1
            if (
                bool(verdict.get("r1_detected"))
                and final_attempts.get(slot_id, {}).get("failure_class") is None
            ):
                primary_row["k"] += 1
        for finding in verdict.get("findings", []) if isinstance(verdict.get("findings"), list) else []:
            if not isinstance(finding, dict):
                continue
            equivalent = finding.get("equivalent_to")
            known_finding_ids = _aggregate_known_finding_ids_for_task(
                task_manifest,
                dimensions["benchmark_task_id"],
            )
            if equivalent is not None and equivalent not in known_finding_ids:
                reasons.append(f"{slot_id}: unknown equivalent finding id")
            if finding.get("real") is not True:
                continue
            if (
                dimensions["oracle_kind"] == "negative"
                and finding.get("severity") in {"CRITICAL", "HIGH"}
                and finding.get("must_fix") is True
            ):
                false_finding_axes[axis_key] = (
                    false_finding_axes.get(axis_key, 0) + 1
                )
            root_cause = finding.get("root_cause")
            if equivalent is None and isinstance(root_cause, str) and root_cause:
                novel_by_root.setdefault(
                    root_cause,
                    {
                        "root_cause": root_cause,
                        "occurrences": [],
                        "real_source": "label-masked verdict",
                    },
                )["occurrences"].append(slot_id)
                novel_key = (root_cause, axis_key)
                novel_by_axis.setdefault(
                    novel_key,
                    {
                        **_axis_row(dimensions, arm=dimensions["arm"]),
                        "root_cause": root_cause,
                        "occurrences": [],
                        "real_source": "label-masked verdict",
                    },
                )["occurrences"].append(slot_id)

    for axis_key, oracle_kind in axis_oracle_kinds.items():
        if oracle_kind == "negative":
            false_finding_axes.setdefault(axis_key, 0)
    reliability_axes: dict[tuple[Any, ...], int] = {}
    for dimensions in slot_dimensions.values():
        axis_key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
            dimensions["arm"],
        )
        reliability_axes.setdefault(axis_key, 0)
    for attempt in attempts:
        dimensions = _attempt_slot_dimensions(
            attempt,
            slot_dimensions,
            reasons,
            task_manifest=task_manifest,
        )
        if dimensions is None:
            continue
        if (
            attempt.get("failure_class") == "post-treatment"
            or attempt.get("individual_failure_class") == "post-treatment"
        ):
            axis_key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
                dimensions["arm"],
            )
            reliability_axes[axis_key] = reliability_axes.get(axis_key, 0) + 1

    expected_slot_ids = {str(slot["slot_id"]) for slot in slots}
    experiment_complete = (
        not reasons
        and set(final_attempts) == expected_slot_ids
        and all(
            row.get("failure_class")
            not in {"technical-invalid", "pair-invalidated"}
            for row in final_attempts.values()
        )
    )
    axis_primary_rows = list(primary_axes.values())
    axis_false_finding_rows = [
        {
            **{
                field: key[index] for index, field in enumerate(_AXIS_FIELDS)
            },
            "arm": key[-1],
            "oracle_kind": axis_oracle_kinds.get(key),
            "count": count,
        }
        for key, count in false_finding_axes.items()
    ]
    axis_reliability_rows = [
        {
            **{
                field: key[index] for index, field in enumerate(_AXIS_FIELDS)
            },
            "arm": key[-1],
            "oracle_kind": axis_oracle_kinds.get(key),
            "post_treatment": count,
        }
        for key, count in reliability_axes.items()
    ]
    legacy_projection = _is_legacy_projection(slot_dimensions)
    positive_primary = {
        row["arm"]: {"k": row["k"], "n": row["n"]}
        for row in axis_primary_rows
        if row.get("oracle_kind") == "positive"
    }
    negative_false_findings: dict[str, int] = {}
    for row in axis_false_finding_rows:
        if row.get("oracle_kind") != "negative":
            continue
        arm = str(row["arm"])
        negative_false_findings[arm] = (
            negative_false_findings.get(arm, 0) + int(row["count"])
        )
    positive_arms = list(positive_primary)
    reference_arm = positive_arms[0] if positive_arms else None
    reference_passes = (
        reference_arm is not None
        and positive_primary[reference_arm]["k"]
        == positive_primary[reference_arm]["n"]
    )
    pos_eligibility = {
        arm: reference_passes
        and values["k"] == values["n"]
        for arm, values in positive_primary.items()
    }
    excluded_arms = sorted(
        arm for arm, count in negative_false_findings.items() if count > 0
    )
    reliability: dict[str, int] = {
        str(row["arm"]): 0
        for row in axis_primary_rows
        if row.get("oracle_kind") == "positive"
    }
    for row in axis_reliability_rows:
        reliability[str(row["arm"])] = reliability.get(str(row["arm"]), 0) + int(
            row["post_treatment"]
        )
    decision: dict[str, Any] = {"by_axis": []}
    if legacy_projection and positive_primary:
        if all(values["k"] == values["n"] for values in positive_primary.values()):
            quality = "この6 runでは劣化を観測しなかった"
        elif reference_passes and reference_arm == "max":
            quality = "highはzero-miss安全条件を満たさない"
        elif not reference_passes and any(
            values["k"] == values["n"] for values in positive_primary.values()
        ):
            quality = "benchmarkまたはmax基準が不安定"
        else:
            quality = "品質判断不能"
        decision: dict[str, Any] = {
            "row": (
                "NEG_ADJUDICATED_FALSE_FINDING"
                if excluded_arms
                else "POS_PRIMARY"
            ),
            "reason": (
                f"label-masked R-1 judgment max={positive_primary.get('max', {'k': 0})['k']}/"
                f"{positive_primary.get('max', {'n': 0})['n']} high="
                f"{positive_primary.get('high', {'k': 0})['k']}/"
                f"{positive_primary.get('high', {'n': 0})['n']}; "
                f"NEG real false finding occurrence={negative_false_findings}"
            ),
            "quality_decision": quality,
            "pos_adoption_eligibility": pos_eligibility,
            "neg_excluded_arms": excluded_arms,
            "adoption_eligibility": {
                arm: pos_eligibility.get(arm, False)
                and arm not in excluded_arms
                for arm in positive_arms
            },
        }
    else:
        conditions: dict[tuple[Any, ...], dict[str, Any]] = {}
        for row in axis_primary_rows:
            condition_key = tuple(row.get(field) for field in _AXIS_FIELDS)
            condition = conditions.setdefault(
                condition_key,
                {
                    **{
                        field: row.get(field) for field in _AXIS_FIELDS
                    },
                    "oracle_kind": row.get("oracle_kind"),
                    "arms": {},
                },
            )
            condition["arms"][row["arm"]] = {
                "k": row["k"],
                "n": row["n"],
            }
        for row in axis_false_finding_rows:
            condition_key = tuple(row.get(field) for field in _AXIS_FIELDS)
            condition = conditions.setdefault(
                condition_key,
                {
                    **{
                        field: row.get(field) for field in _AXIS_FIELDS
                    },
                    "oracle_kind": "negative",
                    "arms": {},
                },
            )
            condition.setdefault("false_findings", {})[row["arm"]] = row[
                "count"
            ]
        decision = {"by_axis": list(conditions.values())}

    resources = []
    for attempt_index, attempt in enumerate(attempts):
        dimensions = _attempt_slot_dimensions(
            attempt,
            slot_dimensions,
            reasons,
            task_manifest=task_manifest,
        )
        resource = {
            key: attempt.get(key)
            for key in (
                "run_id", "slot_id", "attempt", "case", "arm",
                "block_id", "block_order",
                "input_tokens", "cached_input_tokens", "output_tokens",
                "reasoning_output_tokens", "cli_reported", "model_calls",
                "token_usage_observations",
                "turn_protocol", "wall_clock_ms", "rate_limited", "retry",
                "compaction_observed", "failure_class",
                "individual_failure_class", "pair_invalidation",
            )
        }
        if dimensions is not None:
            resource.update(
                {
                    field: dimensions.get(field)
                    for field in (
                        "benchmark_task_id",
                        "stage",
                        "requested_model",
                        "cache_condition",
                        "price_version",
                        "oracle_kind",
                        "legacy_case",
                    )
                }
            )
            resource["case"] = dimensions["case"]
            resource["arm"] = dimensions["arm"]
        if normalized_costs is not None:
            normalized_cost = normalized_costs[attempt_index]
            if normalized_cost is not None:
                resource["normalized_cost"] = normalized_cost
        resources.append(resource)

    agreement_by_axis: list[dict[str, Any]] = []
    agreement_groups: dict[tuple[Any, ...], list[bool]] = {}
    for slot_id, verdict in verdicts.items():
        dimensions = slot_dimensions.get(str(slot_id))
        if dimensions is None:
            continue
        key = tuple(dimensions.get(field) for field in _AXIS_FIELDS) + (
            dimensions["arm"],
        )
        agreement_groups.setdefault(key, []).append(
            verdict.get("reader_agreement") is True
        )
    for key, values in agreement_groups.items():
        agreement_by_axis.append(
            {
                **{
                    field: key[index] for index, field in enumerate(_AXIS_FIELDS)
                },
                "arm": key[-1],
                "agreed": sum(values),
                "total": len(values),
                "rate": sum(values) / len(values) if values else None,
            }
        )

    if reasons:
        experiment_complete = False
    if experiment_complete:
        if not legacy_projection:
            decision = {"by_axis": list(decision.get("by_axis", []))}
    if not experiment_complete:
        primary_output = None
        findings_output = None
        reliability_output = None
        escalation_output = None
        decision_output = None
        agreement_output = None
    else:
        primary_output = (
            {
                str(arm): {"k": row["k"], "n": row["n"]}
                for arm, row in positive_primary.items()
            }
            if legacy_projection
            else axis_primary_rows
        )
        findings_output = sorted(
            novel_by_root.values(), key=lambda row: row["root_cause"]
        )
        reliability_output = (
            reliability if legacy_projection else axis_reliability_rows
        )
        escalation_output = (
            reliability.get("high", 0) > 0
            if legacy_projection
            else any(row["post_treatment"] > 0 for row in axis_reliability_rows)
        )
        decision_output = decision
        agreement_output = {
            "agreed": sum(
                verdict.get("reader_agreement") is True
                for verdict in verdicts.values()
            ),
            "total": len(verdicts),
            "rate": (
                sum(
                    verdict.get("reader_agreement") is True
                    for verdict in verdicts.values()
                )
                / len(verdicts)
                if verdicts
                else None
            ),
            "disagreement_policy": "conservative-miss",
        }
    result = {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": (
            material_manifest_sha256
            if material_manifest_sha256 is not None
            else _sha256(manifest_path.read_bytes())
        ),
        "valid": not reasons,
        "failure_reasons": sorted(set(reasons)),
        "experiment_complete": experiment_complete,
        "primary_judgment_ledger": primary_output,
        "primary_judgment_axis_ledger": axis_primary_rows,
        "new_finding_ledger": findings_output,
        "new_finding_axis_ledger": list(novel_by_axis.values()),
        "resource_ledger": resources,
        "token_usage_observations": token_usage_observations,
        "turn_accounting": {
            "protocol": "single-turn-required",
            "comparative_metric": "model_calls",
            "logical_turns_reported": False,
        },
        "post_treatment_reliability": reliability_output,
        "post_treatment_reliability_axis_ledger": axis_reliability_rows,
        "online_max_escalation_candidate": escalation_output,
        "reader_agreement": agreement_output,
        "reader_agreement_axis_ledger": agreement_by_axis,
        "decision": decision_output,
    }
    if normalized_cost_axis_ledger is not None:
        result["normalized_cost_axis_ledger"] = normalized_cost_axis_ledger
    return _with_wiring_slice_status(result, task_manifest)


def _validate_supervisor_ledger(
    rows: Sequence[Mapping[str, Any]],
    slots: Sequence[Mapping[str, Any]],
    attempts_raw: Sequence[Mapping[str, Any]],
    attempts_root: Path,
    max_gap_ms: int,
    max_inter_block_gap_ms: int,
) -> tuple[list[Mapping[str, Any]], list[str]]:
    reasons: list[str] = []
    reserved = [row for row in rows if row.get("phase") == "reserved"]
    completed = [row for row in rows if row.get("phase") == "completed"]
    if len(reserved) != len(completed):
        reasons.append("attempt ledger reservation/completion cardinality mismatch")
    reserved_keys = [
        (row.get("slot_id"), row.get("attempt"), row.get("block_id"))
        for row in reserved
    ]
    completed_keys = [
        (row.get("slot_id"), row.get("attempt"), row.get("block_id"))
        for row in completed
    ]
    if sorted(reserved_keys) != sorted(completed_keys):
        reasons.append("attempt ledger reservation/completion set mismatch")
    manifest_keys = {
        (row.get("slot_id"), row.get("attempt"), row.get("run_id"))
        for row in attempts_raw
        if isinstance(row, Mapping)
    }
    completed_manifest_keys = {
        (row.get("slot_id"), row.get("attempt"), row.get("run_id"))
        for row in completed
    }
    if manifest_keys != completed_manifest_keys:
        reasons.append("manifest attempts do not equal supervisor completion ledger")
    slot_by_id = {str(row["slot_id"]): row for row in slots}
    previous_process_end: int | None = None
    previous_process_row: Mapping[str, Any] | None = None
    for row in completed:
        slot = slot_by_id.get(str(row.get("slot_id")))
        if slot is None:
            reasons.append("supervisor ledger references unknown slot")
            continue
        for field in ("block_id", "block_order", "case", "arm"):
            if row.get(field) != slot.get(field):
                reasons.append(
                    f"{row.get('run_id')}: supervisor ledger {field} mismatch"
                )
        process_started = row.get("process_started") is not False
        if not process_started:
            start = row.get("supervision_start_monotonic_ns")
            end = row.get("supervision_end_monotonic_ns")
            failure_class = row.get("failure_class")
            if (
                row.get("not_launched") is not True
                or failure_class
                not in {"technical-invalid", "pair-invalidated"}
                or isinstance(start, bool)
                or not isinstance(start, int)
                or isinstance(end, bool)
                or not isinstance(end, int)
                or end < start
                or row.get("supervision_wall_ms")
                != round((end - start) / 1_000_000)
            ):
                reasons.append(
                    f"{row.get('run_id')}: prelaunch completion malformed"
                )
            if failure_class == "technical-invalid":
                failure = row.get("prelaunch_failure")
                if (
                    not isinstance(failure, dict)
                    or failure.get("kind") != "prelaunch-exception"
                    or not isinstance(failure.get("exception_type"), str)
                    or not isinstance(failure.get("message"), str)
                ):
                    reasons.append(
                        f"{row.get('run_id')}: prelaunch failure schema mismatch"
                    )
            else:
                if (
                    row.get("individual_failure_class") is not None
                    or not isinstance(row.get("pair_invalidation"), dict)
                ):
                    reasons.append(
                        f"{row.get('run_id')}: unlaunched mate schema mismatch"
                    )
            if row.get("launch_receipt") is not None:
                reasons.append(
                    f"{row.get('run_id')}: prelaunch completion has launch receipt"
                )
            accounting_reason = _not_launched_accounting_reason(row)
            if accounting_reason is not None:
                reasons.append(
                    f"{row.get('run_id')}: {accounting_reason}"
                )
            continue
        launch_path = Path(str(row.get("launch_receipt"))).resolve()
        try:
            launch_path.relative_to(attempts_root)
        except ValueError:
            reasons.append(f"{row.get('run_id')}: launch receipt is outside run root")
        if (
            not launch_path.is_file()
            or _sha256(launch_path.read_bytes()) != row.get("launch_receipt_sha256")
        ):
            reasons.append(f"{row.get('run_id')}: launch receipt ledger sha mismatch")
        else:
            launch = _load_json_object(launch_path)
            done_state = launch.get("done")
            done_path = (
                Path(str(done_state.get("path")))
                if isinstance(done_state, dict)
                else Path("")
            )
            try:
                done_value = _load_json_object(done_path)
            except ValidationError as exc:
                reasons.extend(exc.reasons)
            else:
                if (
                    launch.get("run_id") != row.get("run_id")
                    or launch.get("slot_id") != row.get("slot_id")
                    or launch.get("attempt") != row.get("attempt")
                    or launch.get("parent_run_id") != row.get("parent_run_id")
                    or launch.get("process_start_monotonic_ns")
                    != row.get("process_start_monotonic_ns")
                    or done_value.get("process_exit_monotonic_ns")
                    != row.get("process_exit_monotonic_ns")
                    or done_value.get("exit_code") != row.get("exit_code")
                ):
                    reasons.append(
                        f"{row.get('run_id')}: supervisor ledger/OS receipt mismatch"
                    )
        start = row.get("process_start_monotonic_ns")
        end = row.get("process_exit_monotonic_ns")
        if (
            isinstance(start, bool)
            or not isinstance(start, int)
            or isinstance(end, bool)
            or not isinstance(end, int)
            or end < start
        ):
            reasons.append(f"{row.get('run_id')}: supervisor timing malformed")
        elif row.get("process_wall_ms") != round((end - start) / 1_000_000):
            reasons.append(f"{row.get('run_id')}: supervisor wall-clock mismatch")
        if row.get("snapshot_unchanged") is not True:
            reasons.append(f"{row.get('run_id')}: snapshot changed during run")
        if previous_process_end is not None and isinstance(start, int):
            gap_ms = round((start - previous_process_end) / 1_000_000)
            gap_limit_ms = (
                max_gap_ms
                if previous_process_row is not None
                and _is_intra_block_arm_transition(
                    previous_process_row, row
                )
                else max_inter_block_gap_ms
            )
            if start < previous_process_end:
                reasons.append("actual process schedule overlaps or reverses")
            if gap_ms > gap_limit_ms:
                reasons.append("actual process schedule gap exceeds bound")
        if isinstance(end, int):
            previous_process_end = end
            previous_process_row = row
    if len(completed) % 2:
        reasons.append("supervisor completion ledger has a one-sided pair")
    groups: list[tuple[str, int]] = []
    for index in range(0, len(completed), 2):
        pair = completed[index : index + 2]
        if len(pair) != 2:
            continue
        keys = {(str(row.get("block_id")), int(row.get("attempt", 0))) for row in pair}
        if len(keys) != 1 or [row.get("block_order") for row in pair] != [1, 2]:
            reasons.append("pair members are not adjacent in one attempt generation")
            continue
        groups.append(next(iter(keys)))
    schedule_blocks = list(dict.fromkeys(str(row["block_id"]) for row in slots))
    first_attempt_blocks = [block for block, attempt in groups if attempt == 1]
    if first_attempt_blocks != schedule_blocks[: len(first_attempt_blocks)]:
        reasons.append("actual first-attempt block order differs from schedule")
    last_group_for_block: dict[str, tuple[int, int]] = {}
    for group_index, (block, generation) in enumerate(groups):
        previous = last_group_for_block.get(block)
        if previous is None and generation != 1:
            reasons.append(f"{block}: first pair generation is not 1")
        if previous is not None:
            previous_generation, previous_index = previous
            if generation != previous_generation + 1:
                reasons.append(f"{block}: pair attempt sequence is not contiguous")
            if group_index != previous_index + 1:
                reasons.append(f"{block}: retry pair is not adjacent")
        last_group_for_block[block] = (generation, group_index)
    generations: dict[str, dict[str, set[int]]] = {}
    for row in completed:
        generations.setdefault(str(row.get("block_id")), {}).setdefault(
            str(row.get("slot_id")), set()
        ).add(int(row.get("attempt", 0)))
    for block, members in generations.items():
        if len(members) != 2 or len({tuple(sorted(values)) for values in members.values()}) != 1:
            reasons.append(f"{block}: pair members have different attempt generations")
    return completed, reasons


def _replay_manifest(
    manifest_path: Path,
    sessions_root: Path,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    manifest_path = manifest_path.resolve()
    manifest, material_manifest_sha256 = _load_json_object_with_sha256(
        manifest_path
    )
    reasons: list[str] = []
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    _require_task_manifest_sha256(
        manifest,
        task_manifest,
        "material manifest",
        rc=RC_AGGREGATE,
    )
    schedule_path, schedule_bytes = _artifact_path_with_bytes(
        manifest_path, manifest.get("schedule"), "schedule"
    )
    schedule = _load_json_object(schedule_path, data=schedule_bytes)
    _require_task_manifest_sha256(
        schedule,
        task_manifest,
        "schedule",
        rc=RC_AGGREGATE,
    )
    slots, schedule_reasons = _validate_schedule(
        schedule, task_manifest=task_manifest
    )
    if isinstance(slots, _ValidatedScheduleSlots):
        slots.has_material_schedule_descriptor = manifest.get("schedule") is not None
        slots.material_manifest_sha256 = material_manifest_sha256
    reasons.extend(schedule_reasons)
    schedule_sha = _sha256(schedule_bytes)
    if manifest.get("schedule_sha256") != schedule_sha:
        reasons.append("manifest schedule_sha256 mismatch")
    attempts_raw = manifest.get("attempts")
    if not isinstance(attempts_raw, list):
        raise ValidationError("manifest.attempts is not an array", RC_AGGREGATE)
    run_root_value = manifest.get("run_root")
    if not isinstance(run_root_value, str) or not run_root_value:
        raise ValidationError("manifest.run_root is required", RC_AGGREGATE)
    run_root = _resolve_artifact(manifest_path, run_root_value)
    if schedule_path != run_root / "schedule.json":
        reasons.append("manifest schedule is not the supervisor-frozen schedule")
    try:
        _assert_arm_neutral_paths([run_root])
    except ValidationError as exc:
        reasons.extend(exc.reasons)
    attempts_root_value = manifest.get("attempts_root")
    if not isinstance(attempts_root_value, str) or not attempts_root_value:
        reasons.append("manifest attempts_root missing")
        attempts_root = run_root / "attempts"
    else:
        attempts_root = _resolve_artifact(manifest_path, attempts_root_value)
        try:
            _assert_arm_neutral_paths([os.fspath(attempts_root)])
        except ValidationError as exc:
            reasons.extend(exc.reasons)
    if attempts_root != run_root / "attempts":
        reasons.append("attempts_root is not the unique run-root attempts directory")
    try:
        ledger_path = _artifact_path(
            manifest_path,
            manifest.get("attempt_ledger"),
            "attempt_ledger",
            root=run_root,
        )
        ledger_rows, ledger_issues = _json_lines(ledger_path)
        reasons.extend(ledger_issues)
        if any(
            row.get("phase") in {"reserved", "completed"}
            and row.get("task_manifest_sha256") != task_manifest_sha256
            for row in ledger_rows
        ):
            reasons.append("attempt ledger task_manifest_sha256 mismatch")
        if manifest.get("max_schedule_gap_ms") != MAX_SCHEDULE_GAP_MS:
            reasons.append("manifest intra-block schedule gap bound mismatch")
        if (
            manifest.get("max_inter_block_gap_ms")
            != MAX_INTER_BLOCK_GAP_MS
        ):
            reasons.append("manifest inter-block schedule gap bound mismatch")
        supervisor_completions, ledger_reasons = _validate_supervisor_ledger(
            ledger_rows,
            slots,
            [row for row in attempts_raw if isinstance(row, dict)],
            attempts_root,
            MAX_SCHEDULE_GAP_MS,
            MAX_INTER_BLOCK_GAP_MS,
        )
        reasons.extend(ledger_reasons)
    except (ValidationError, TypeError, ValueError) as exc:
        reasons.append(f"attempt ledger replay failed: {exc}")
        supervisor_completions = []
    supervisor_by_run = {
        str(row.get("run_id")): row for row in supervisor_completions
    }
    listed_launch_paths: set[Path] = set()
    for raw in attempts_raw:
        if not isinstance(raw, dict):
            continue
        descriptor = raw.get("launch_receipt")
        if isinstance(descriptor, dict) and isinstance(descriptor.get("path"), str):
            listed_launch_paths.add(
                _resolve_artifact(manifest_path, descriptor["path"])
            )
    generated_launch_paths = {
        path.resolve() for path in attempts_root.rglob("launch.json")
    } if attempts_root.is_dir() else set()
    if generated_launch_paths != listed_launch_paths:
        reasons.append("attempt launch receipt set mismatch")
    slot_index = {row["slot_id"]: row for row in slots if isinstance(row.get("slot_id"), str)}
    attempts: list[dict[str, Any]] = []
    grouped: dict[str, list[dict[str, Any]]] = {}
    seen_run_ids: set[str] = set()
    expected_sessions: list[tuple[str, int, str, str, str]] = []
    envelope_starts: list[datetime] = []
    envelope_ends: list[datetime] = []
    snapshot_cache: set[tuple[str, str, str]] = set()
    snapshot_verified_run_ids: set[str] = set()
    for row in attempts_raw:
        if not isinstance(row, dict):
            reasons.append("attempt row is not an object")
            continue
        run_id = row.get("run_id")
        slot_id = row.get("slot_id")
        attempt_number = row.get("attempt")
        if not isinstance(run_id, str) or run_id in seen_run_ids:
            reasons.append("attempt run_id missing/duplicate")
            continue
        seen_run_ids.add(run_id)
        slot = slot_index.get(slot_id)
        if slot is None:
            reasons.append(f"{run_id}: unknown slot_id")
            continue
        if (
            isinstance(attempt_number, bool)
            or not isinstance(attempt_number, int)
            or not 1 <= attempt_number <= 3
        ):
            reasons.append(f"{run_id}: attempt outside 1..3")
            continue
        supervisor_row = supervisor_by_run.get(run_id)
        if (
            isinstance(supervisor_row, Mapping)
            and supervisor_row.get("process_started") is False
        ):
            failure_class = supervisor_row.get("failure_class")
            if (
                row.get("process_started") is not False
                or row.get("not_launched") is not True
                or row.get("failure_class") != failure_class
                or row.get("prelaunch_failure")
                != supervisor_row.get("prelaunch_failure")
                or row.get("pair_invalidation")
                != supervisor_row.get("pair_invalidation")
            ):
                reasons.append(
                    f"{run_id}: manifest/prelaunch completion mismatch"
                )
            failed_attempt = {
                "run_id": run_id,
                "slot_id": slot_id,
                "attempt": attempt_number,
                "benchmark_task_id": slot.get("benchmark_task_id"),
                "stage": slot.get("stage"),
                "requested_model": slot.get("requested_model", MODEL),
                "cache_condition": slot.get("cache_condition"),
                "price_version": slot.get("price_version"),
                "oracle_kind": slot.get("oracle_kind"),
                "legacy_case": slot.get("legacy_case"),
                "case": slot.get("case"),
                "arm": slot.get("arm"),
                "block_id": slot.get("block_id"),
                "block_order": slot.get("block_order"),
                "parent_run_id": row.get("parent_run_id"),
                "input_tokens": supervisor_row.get("input_tokens", 0),
                "cached_input_tokens": supervisor_row.get(
                    "cached_input_tokens", 0
                ),
                "output_tokens": supervisor_row.get("output_tokens", 0),
                "reasoning_output_tokens": supervisor_row.get(
                    "reasoning_output_tokens", 0
                ),
                "cli_reported": supervisor_row.get("cli_reported", 0),
                "model_calls": supervisor_row.get("model_calls", 0),
                "turn_protocol": supervisor_row.get(
                    "turn_protocol", "single-turn-required"
                ),
                "wall_clock_ms": supervisor_row.get("wall_clock_ms", 0),
                "rate_limited": supervisor_row.get("rate_limited", False),
                "retry": attempt_number > 1,
                "compaction_observed": supervisor_row.get(
                    "compaction_observed", False
                ),
                "failure_class": failure_class,
                "failure_classes": list(
                    supervisor_row.get("failure_classes", [])
                ),
                "individual_failure_class": supervisor_row.get(
                    "individual_failure_class"
                ),
                "pair_invalidation": supervisor_row.get("pair_invalidation"),
                "treatment_started": False,
                "prelaunch_failure": supervisor_row.get("prelaunch_failure"),
            }
            attempts.append(failed_attempt)
            grouped.setdefault(str(slot_id), []).append(failed_attempt)
            continue
        try:
            launch_path = _artifact_path(manifest_path, row.get("launch_receipt"), f"{run_id}:launch")
            events_path = _artifact_path(manifest_path, row.get("events"), f"{run_id}:events")
            done_path = _artifact_path(manifest_path, row.get("done"), f"{run_id}:done")
            prompt_path = _artifact_path(manifest_path, row.get("prompt"), f"{run_id}:prompt")
            output_path = _artifact_path(manifest_path, row.get("output"), f"{run_id}:output")
            oracle_path = _artifact_path(
                manifest_path, row.get("snapshot_oracle"), f"{run_id}:snapshot_oracle"
            )
            oracle_after_path = _artifact_path(
                manifest_path,
                row.get("snapshot_after"),
                f"{run_id}:snapshot_after",
            )
            rollout_path = _artifact_path(
                manifest_path, row.get("rollout"), f"{run_id}:rollout",
                root=sessions_root,
            )
            receipt_path = _artifact_path(manifest_path, row.get("receipt"), f"{run_id}:receipt")
            score_path = _artifact_path(manifest_path, row.get("score"), f"{run_id}:score")
            launch = _load_json_object(launch_path)
            oracle = _load_json_object(oracle_path)
            oracle_after = _load_json_object(oracle_after_path)
            snapshot_replay_bindings_passed = True
            for field, expected_value in (
                ("run_id", run_id),
                ("slot_id", slot_id),
                ("attempt", attempt_number),
                ("parent_run_id", row.get("parent_run_id")),
                ("case", slot.get("case")),
                ("arm", slot.get("arm")),
                ("requested_model", slot.get("requested_model", MODEL)),
            ):
                if launch.get(field) != expected_value:
                    reasons.append(f"{run_id}: launch/manifest {field} mismatch")
            if schedule_path.stat().st_mtime_ns > launch_path.stat().st_mtime_ns:
                reasons.append(f"{run_id}: schedule was frozen after launch")
            if launch.get("schedule_sha256") != schedule_sha:
                reasons.append(f"{run_id}: launch/schedule sha mismatch")
            launch_prompt = launch.get("prompt")
            launch_oracle = launch.get("snapshot_oracle")
            if (
                not isinstance(launch_prompt, dict)
                or launch_prompt.get("sha256") != slot.get("prompt_sha256")
            ):
                reasons.append(f"{run_id}: scheduled prompt sha mismatch")
            if (
                not isinstance(launch_oracle, dict)
                or launch_oracle.get("sha256") != slot.get("snapshot_manifest_sha256")
            ):
                reasons.append(f"{run_id}: scheduled snapshot manifest sha mismatch")
                snapshot_replay_bindings_passed = False
            if oracle.get("submodule_manifest_sha256") != slot.get(
                "submodule_manifest_sha256"
            ):
                reasons.append(
                    f"{run_id}: scheduled submodule initialization or "
                    "gitlink state mismatch"
                )
                snapshot_replay_bindings_passed = False
            snapshot_oracle_descriptor = row.get("snapshot_oracle")
            snapshot_identity = (
                oracle_path.resolve().as_posix(),
                str(snapshot_oracle_descriptor["sha256"]),
                str(slot["case"]),
            )
            snapshot_replay_verified = snapshot_identity in snapshot_cache
            if not snapshot_replay_verified:
                replay_oracle = verify_snapshot(
                    Path(oracle["snapshot"]),
                    str(slot["case"]),
                    task_manifest=task_manifest,
                )
                if _canonical_bytes(replay_oracle) != oracle_path.read_bytes():
                    reasons.append(f"{run_id}: snapshot oracle replay mismatch")
                else:
                    snapshot_cache.add(snapshot_identity)
                    snapshot_replay_verified = True
            if (
                oracle_after != oracle
                or oracle_after_path.read_bytes() != oracle_path.read_bytes()
            ):
                reasons.append(f"{run_id}: pre/post snapshot oracle mismatch")
                snapshot_replay_bindings_passed = False
            if snapshot_replay_verified and snapshot_replay_bindings_passed:
                snapshot_verified_run_ids.add(run_id)
            replay_receipt, _ = collect_run(
                run_id=run_id,
                case=str(slot["case"]),
                requested_effort=str(slot["arm"]),
                events=events_path,
                done=done_path,
                output=output_path,
                prompt=prompt_path,
                sessions_root=sessions_root,
                snapshot=Path(oracle["snapshot"]),
                launch_receipt=launch_path,
                expected_requested_model=slot.get("requested_model", MODEL),
                task_manifest=task_manifest,
            )
            if _canonical_bytes(replay_receipt) != receipt_path.read_bytes():
                reasons.append(f"{run_id}: receipt canonical replay mismatch")
            replay_score, _ = score_run(output_path, run_id)
            if _canonical_bytes(replay_score) != score_path.read_bytes():
                reasons.append(f"{run_id}: score canonical replay mismatch")
            if replay_receipt.get("rollout_path") != os.fspath(rollout_path.resolve()):
                reasons.append(f"{run_id}: rollout path mismatch")
            joined = _apply_score_failure(
                {
                    **replay_receipt,
                    "slot_id": slot_id,
                    "attempt": attempt_number,
                    "block_id": slot.get("block_id"),
                    "block_order": slot.get("block_order"),
                    "parent_run_id": row.get("parent_run_id"),
                    "output_sha256": _sha256(output_path.read_bytes()),
                    "r1_candidate": replay_score.get("r1_candidate"),
                    "decision": replay_score.get("decision"),
                },
                replay_score,
            )
            for field in (
                "benchmark_task_id",
                "stage",
                "requested_model",
                "cache_condition",
                "price_version",
                "oracle_kind",
                "legacy_case",
            ):
                scheduled_value = slot.get(
                    field, MODEL if field == "requested_model" else None
                )
                if field in joined and joined.get(field) != scheduled_value:
                    reasons.append(
                        f"{run_id}: attempt {field} does not match scheduled slot"
                    )
                joined[field] = scheduled_value
            joined["case"] = slot.get("case")
            joined["arm"] = slot.get("arm")
            if supervisor_row is None:
                reasons.append(f"{run_id}: supervisor completion row missing")
            else:
                actual_wall = supervisor_row.get("process_wall_ms")
                if (
                    replay_receipt.get("wall_clock_ms") is not None
                    and replay_receipt.get("wall_clock_ms") != actual_wall
                ):
                    reasons.append(f"{run_id}: process wall-clock mismatch")
                joined["wall_clock_ms"] = actual_wall
            attempts.append(joined)
            grouped.setdefault(str(slot_id), []).append(joined)
            if isinstance(replay_receipt.get("session_id"), str):
                expected_sessions.append(
                    (
                        str(replay_receipt["rollout_path"]),
                        int(replay_receipt["rollout_inode"]),
                        str(replay_receipt["thread_id"]),
                        str(replay_receipt["session_id"]),
                        str(replay_receipt["session_timestamp"]),
                    )
                )
            start = _parse_timestamp(launch.get("created_at"))
            done_value = _read_json_value(done_path)
            end = _parse_timestamp(done_value.get("exited_at") if isinstance(done_value, dict) else None)
            if start is not None and end is not None:
                envelope_starts.append(start)
                envelope_ends.append(end)
        except (ValidationError, OSError, KeyError, TypeError, ValueError) as exc:
            reasons.append(f"{run_id}: replay failed: {exc}")
            supervisor_row = supervisor_by_run.get(str(run_id), {})
            failed_attempt = {
                "run_id": run_id,
                "slot_id": slot_id,
                "attempt": attempt_number,
                "benchmark_task_id": slot.get("benchmark_task_id"),
                "stage": slot.get("stage"),
                "requested_model": slot.get("requested_model", MODEL),
                "cache_condition": slot.get("cache_condition"),
                "price_version": slot.get("price_version"),
                "oracle_kind": slot.get("oracle_kind"),
                "legacy_case": slot.get("legacy_case"),
                "case": slot.get("case"),
                "arm": slot.get("arm"),
                "block_id": slot.get("block_id"),
                "block_order": slot.get("block_order"),
                "parent_run_id": row.get("parent_run_id"),
                "input_tokens": None,
                "cached_input_tokens": None,
                "output_tokens": None,
                "reasoning_output_tokens": None,
                "cli_reported": None,
                "model_calls": None,
                "turn_protocol": "single-turn-required",
                "wall_clock_ms": supervisor_row.get("process_wall_ms"),
                "rate_limited": None,
                "retry": attempt_number > 1,
                "compaction_observed": None,
                "failure_class": "technical-invalid",
                "failure_reasons": [f"replay failed: {exc}"],
            }
            attempts.append(failed_attempt)
            grouped.setdefault(str(slot_id), []).append(failed_attempt)
    _apply_pair_invalidations(attempts)
    reasons.extend(_retry_lineage_reasons(grouped))
    if set(grouped) != set(slot_index):
        reasons.append("slot/attempt set mismatch")
    if envelope_starts and envelope_ends:
        actual_sessions = _scan_session_rows(
            sessions_root, min(envelope_starts), max(envelope_ends)
        )
        if sorted(actual_sessions) != sorted(expected_sessions):
            reasons.append("generated session row set mismatch")
    final_attempts = {
        slot_id: sorted(rows, key=lambda item: int(item["attempt"]))[-1]
        for slot_id, rows in grouped.items()
        if rows
    }
    verdicts, adjudication_reasons = _load_adjudication(
        manifest_path,
        manifest,
        slots,
        final_attempts,
        snapshot_verified_run_ids=snapshot_verified_run_ids,
        task_manifest=task_manifest,
    )
    reasons.extend(adjudication_reasons)
    identities: dict[tuple[Any, ...], set[str]] = {}
    for row in attempts:
        launch_descriptor = next(
            (
                raw.get("launch_receipt")
                for raw in attempts_raw
                if isinstance(raw, dict)
                and raw.get("run_id") == row.get("run_id")
            ),
            None,
        )
        if not isinstance(launch_descriptor, dict):
            continue
        launch_path = _artifact_path(
            manifest_path, launch_descriptor, f"{row['run_id']}:launch_identity"
        )
        launch = _load_json_object(launch_path)
        slot = slot_index.get(str(row.get("slot_id")))
        if slot is None:
            continue
        identity_key = tuple(slot.get(field) for field in _AXIS_FIELDS)
        identities.setdefault(identity_key, set()).add(
            str(launch.get("treatment_identity_sha256"))
        )
    for identity_key, values in identities.items():
        if values and len(values) != 1:
            reasons.append(
                "treatment identity concentration is not 1: "
                f"{identity_key}"
            )
    return slots, attempts, verdicts, reasons


def _certification_scope() -> dict[str, Any]:
    return {
        "certification_subject": "material-report",
        "certified_entrypoints": ["verify", "aggregate"],
        "certified_report_fields": ["valid"],
        "uncertified_artifact_universe": (
            "adjudication_intermediate_artifacts"
        ),
        "uncertified_artifact_kinds": [
            "packet",
            "packet_state",
            "verdict_log",
            "verdict_freeze",
            "revealed_map",
        ],
        "material_packet_requirement": (
            "mapped_final_run_snapshot_evidence_replayed"
        ),
        "closed_world": True,
    }


def verify_manifest(
    manifest_path: Path,
    sessions_root: Path | None = None,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[dict[str, Any], int]:
    if sessions_root is None:
        output = {
            "schema_version": SCHEMA_VERSION,
            "task_manifest_sha256": _task_manifest_sha256(task_manifest),
            "valid": False,
            "failure_reasons": ["sessions-root is required"],
            "certification_scope": _certification_scope(),
        }
        return _with_wiring_slice_status(output, task_manifest), RC_AGGREGATE
    try:
        slots, attempts, verdicts, reasons = _replay_manifest(
            manifest_path,
            sessions_root.resolve(),
            task_manifest=task_manifest,
        )
        output = _aggregate_verified(
            manifest_path.resolve(),
            slots,
            attempts,
            verdicts,
            reasons,
            task_manifest=task_manifest,
        )
    except ValidationError as exc:
        output = {
            "schema_version": SCHEMA_VERSION,
            "task_manifest_sha256": _task_manifest_sha256(task_manifest),
            "valid": False,
            "failure_reasons": list(exc.reasons),
        }
    output.setdefault(
        "task_manifest_sha256", _task_manifest_sha256(task_manifest)
    )
    output["certification_scope"] = _certification_scope()
    output = _with_wiring_slice_status(output, task_manifest)
    return output, 0 if output.get("valid") else RC_AGGREGATE


def aggregate_manifest(
    manifest_path: Path,
    *,
    sessions_root: Path | None = None,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> tuple[dict[str, Any], int]:
    return verify_manifest(
        manifest_path,
        sessions_root=sessions_root,
        task_manifest=task_manifest,
    )


def make_packets(
    manifest_path: Path,
    packet_dir: Path,
    custodian_root: Path,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    task_manifest_sha256 = _task_manifest_sha256(task_manifest)
    manifest = _load_json_object(manifest_path)
    _require_task_manifest_sha256(
        manifest,
        task_manifest,
        "packet source manifest",
        rc=RC_AGGREGATE,
    )
    attempts = manifest.get("attempts")
    if not isinstance(attempts, list):
        raise ValidationError("manifest.attempts is not an array", RC_AGGREGATE)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in attempts:
        if isinstance(row, dict) and isinstance(row.get("slot_id"), str):
            grouped.setdefault(row["slot_id"], []).append(row)
    schedule_descriptor = manifest.get("schedule")
    bound_price_version: str | None = None
    if schedule_descriptor is None and not grouped:
        raise ValidationError(
            "packets require at least one logical slot", RC_AGGREGATE
        )
    if schedule_descriptor is not None:
        if isinstance(schedule_descriptor, Mapping) and "slots" in schedule_descriptor:
            schedule = dict(schedule_descriptor)
        else:
            schedule_path, schedule_bytes = _artifact_path_with_bytes(
                manifest_path.resolve(), schedule_descriptor, "schedule"
            )
            schedule = _load_json_object(schedule_path, data=schedule_bytes)
        _require_task_manifest_sha256(
            schedule,
            task_manifest,
            "schedule",
            rc=RC_AGGREGATE,
        )
        schedule = _legacy_schedule_view(schedule)
        schedule_slots, schedule_reasons = _validate_schedule(
            schedule, task_manifest=task_manifest
        )
        if schedule_reasons:
            raise ValidationError(schedule_reasons, RC_AGGREGATE)
        bound_price_version = _validated_slots_price_version(schedule_slots)
        expected_counts = expected_schedule_from_manifest(
            task_manifest,
            schedule,
            expected_price_version=bound_price_version,
        )
        observed_counts: dict[tuple[str, str], int] = {}
        for row in schedule_slots:
            key = (str(row["benchmark_task_id"]), str(row["arm"]))
            observed_counts[key] = observed_counts.get(key, 0) + 1
        if observed_counts != expected_counts:
            raise ValidationError(
                f"packet schedule cardinality mismatch: {observed_counts}",
                RC_AGGREGATE,
            )
        expected_slot_ids = {str(row["slot_id"]) for row in schedule_slots}
        if set(grouped) != expected_slot_ids:
            raise ValidationError(
                "packet/manifest slot set mismatch: "
                f"expected={sorted(expected_slot_ids)} observed={sorted(grouped)}",
                RC_AGGREGATE,
            )
    # Old packet-only fixtures have no schedule descriptor.  Their distinct
    # attempt slot IDs are the only available cardinality authority.
    packet_candidates: list[tuple[str, dict[str, Any], bytes]] = []
    for slot_id, slot_attempts in grouped.items():
        final = max(slot_attempts, key=lambda row: int(row.get("attempt", 0)))
        run_id = final.get("run_id")
        output_path = _artifact_path(
            manifest_path.resolve(), final.get("output"), f"{run_id}:packet-output"
        )
        body = output_path.read_bytes()
        if (
            bound_price_version == FROZEN_PRICE_VERSION
            and FROZEN_PRICE_VERSION.encode("utf-8") in body
        ):
            raise ValidationError(
                "bound price_version literal appears in public packet output",
                RC_AGGREGATE,
            )
        packet_candidates.append((slot_id, final, body))
    if packet_dir.exists():
        raise ValidationError(f"packet directory already exists: {packet_dir}", RC_AGGREGATE)
    packet_dir = packet_dir.resolve()
    custodian_root = custodian_root.resolve()
    if (
        custodian_root == packet_dir
        or packet_dir in custodian_root.parents
        or custodian_root in packet_dir.parents
    ):
        raise ValidationError(
            "mapping custodian root must be outside packet directory",
            RC_AGGREGATE,
        )
    if custodian_root.exists() or custodian_root.is_symlink():
        raise ValidationError(
            f"mapping custodian root must be fresh: {custodian_root}",
            RC_AGGREGATE,
        )
    packet_dir.mkdir(parents=True)
    custodian_root.mkdir(parents=True, mode=0o700)
    custodian_root.chmod(0o700)
    rows: list[dict[str, Any]] = []
    private_rows: list[dict[str, str]] = []
    secrets.SystemRandom().shuffle(packet_candidates)
    for slot_id, final, body in packet_candidates:
        run_id = final.get("run_id")
        packet_id = secrets.token_hex(16)
        filename = f"packet-{packet_id}.md"
        target = packet_dir / filename
        target.write_bytes(body)
        os.utime(target, ns=(PACKET_MTIME_NS, PACKET_MTIME_NS))
        rows.append(
            {
                "packet_id": packet_id,
                "filename": filename,
            }
        )
        private_rows.append(
            {
                "packet_id": packet_id,
                "run_id": str(run_id),
                "slot_id": slot_id,
                "packet_sha256": _sha256(body),
                "score_input_sha256": _sha256(body),
            }
        )
    secrets.SystemRandom().shuffle(rows)
    state = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "mask_strength": "same-owner-advisory",
        "packets": rows,
    }
    state_path = packet_dir / "packet-state.json"
    _write_frozen_json(state_path, state, rc=RC_AGGREGATE)
    os.utime(state_path, ns=(PACKET_MTIME_NS, PACKET_MTIME_NS))
    private_path = custodian_root / f"mapping-{secrets.token_hex(24)}.json"
    _write_frozen_json(
        private_path,
        {
            "schema_version": SCHEMA_VERSION,
            "task_manifest_sha256": task_manifest_sha256,
            "mask_strength": "same-owner-advisory",
            "mapping": private_rows,
        },
        rc=RC_AGGREGATE,
    )
    private_path.chmod(0o600)
    return {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "mask_strength": "same-owner-advisory",
        "packet_state": os.fspath(state_path.resolve()),
        "packet_state_sha256": _sha256(state_path.read_bytes()),
        "custodian_protocol": "fresh-0700-root/opaque-name/freeze-before-discovery",
        "packet_count": len(rows),
    }


def _packet_digests(
    packet_state_path: Path,
    packet_rows: Sequence[Any],
) -> dict[str, str]:
    digests: dict[str, str] = {}
    for row in packet_rows:
        if (
            not isinstance(row, dict)
            or not isinstance(row.get("packet_id"), str)
            or not isinstance(row.get("filename"), str)
            or not re.fullmatch(r"packet-[0-9a-f]{32}\.md", row["filename"])
        ):
            raise ValidationError("packet state row malformed", RC_AGGREGATE)
        packet_id = row["packet_id"]
        if packet_id in digests:
            raise ValidationError("duplicate packet state packet_id", RC_AGGREGATE)
        packet_path = packet_state_path.parent / row["filename"]
        try:
            packet_bytes = packet_path.read_bytes()
        except OSError as exc:
            raise ValidationError(
                f"{packet_id}: packet cannot be read: {exc}", RC_AGGREGATE
            ) from exc
        digests[packet_id] = _sha256(packet_bytes)
    return digests


def _validate_verdict_row(
    row: Mapping[str, Any],
    packet_ids: set[str],
    *,
    require_packet_digest: bool = True,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> None:
    _require_task_manifest_sha256(
        row,
        task_manifest,
        "verdict row",
        rc=RC_AGGREGATE,
    )
    if row.get("packet_id") not in packet_ids:
        raise ValidationError("verdict packet_id is unknown", RC_AGGREGATE)
    if require_packet_digest and (
        not isinstance(row.get("packet_sha256_at_read"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", row["packet_sha256_at_read"])
    ):
        raise ValidationError(
            "verdict read-time packet digest is missing", RC_AGGREGATE
        )
    if not isinstance(row.get("r1_detected"), bool):
        raise ValidationError("verdict r1_detected must be boolean", RC_AGGREGATE)
    if not isinstance(row.get("findings", []), list):
        raise ValidationError("verdict findings must be an array", RC_AGGREGATE)
    known_finding_ids = known_finding_ids_for_manifest(task_manifest)
    for finding in row.get("findings", []):
        if not isinstance(finding, dict) or not isinstance(finding.get("real"), bool):
            raise ValidationError("finding verdict schema mismatch", RC_AGGREGATE)
        if finding.get("severity") not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise ValidationError("finding severity is invalid", RC_AGGREGATE)
        if not isinstance(finding.get("must_fix"), bool):
            raise ValidationError("finding must_fix must be boolean", RC_AGGREGATE)
        equivalent = finding.get("equivalent_to")
        if equivalent is not None and equivalent not in known_finding_ids:
            raise ValidationError("finding equivalent_to is unknown", RC_AGGREGATE)
        if (
            finding["real"]
            and equivalent is None
            and (
                not isinstance(finding.get("root_cause"), str)
                or not finding["root_cause"]
            )
        ):
            raise ValidationError("novel finding root_cause missing", RC_AGGREGATE)


def append_verdicts(
    packet_state_path: Path,
    verdict_log_path: Path,
    reader: str,
    verdict_input_path: Path,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    """Append blind reader verdicts using the manifest-wide finding union.

    The task is intentionally unknown at append time, before mapping reveal.
    """
    state = _load_json_object(packet_state_path)
    task_manifest_sha256 = _require_task_manifest_sha256(
        state,
        task_manifest,
        "packet state",
        rc=RC_AGGREGATE,
    )
    verdicts = _load_json_object(verdict_input_path)
    packet_rows = state.get("packets")
    verdict_rows = verdicts.get("verdicts")
    if not isinstance(packet_rows, list) or not isinstance(verdict_rows, list):
        raise ValidationError("packet/verdict rows missing", RC_AGGREGATE)
    packet_digests = _packet_digests(packet_state_path, packet_rows)
    if reader not in {"parent", "second-reader"}:
        raise ValidationError("verdict reader is invalid", RC_AGGREGATE)
    packet_ids = set(packet_digests)
    existing, issues = _json_lines(verdict_log_path) if verdict_log_path.exists() else ([], [])
    if issues:
        raise ValidationError(issues, RC_AGGREGATE)
    for row in existing:
        _validate_verdict_row(
            row,
            packet_ids,
            task_manifest=task_manifest,
        )
    if any(row.get("reader") == reader for row in existing):
        raise ValidationError("reader verdicts are already appended", RC_AGGREGATE)
    seen: set[str] = set()
    for row in verdict_rows:
        if not isinstance(row, dict) or not isinstance(row.get("packet_id"), str):
            raise ValidationError("verdict row malformed", RC_AGGREGATE)
        packet_id = row["packet_id"]
        if packet_id in seen:
            raise ValidationError("duplicate verdict packet_id", RC_AGGREGATE)
        if packet_id not in packet_ids:
            raise ValidationError("verdict packet_id is unknown", RC_AGGREGATE)
        seen.add(packet_id)
        _validate_verdict_row(
            {
                **row,
                "task_manifest_sha256": task_manifest_sha256,
                "packet_sha256_at_read": packet_digests[packet_id],
            },
            packet_ids,
            task_manifest=task_manifest,
        )
    if seen != packet_ids:
        raise ValidationError("verdict/packet id set mismatch", RC_AGGREGATE)
    for row in verdict_rows:
        packet_id = str(row["packet_id"])
        _append_jsonl(
            verdict_log_path,
            {
                **row,
                "reader": reader,
                "task_manifest_sha256": task_manifest_sha256,
                "packet_sha256_at_read": packet_digests[packet_id],
            },
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "reader": reader,
        "appended": len(verdict_rows),
        "verdict_log_sha256": _sha256(verdict_log_path.read_bytes()),
    }


def freeze_verdicts(
    packet_state_path: Path,
    verdict_log_path: Path,
    output: Path,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    state = _load_json_object(packet_state_path)
    task_manifest_sha256 = _require_task_manifest_sha256(
        state,
        task_manifest,
        "packet state",
        rc=RC_AGGREGATE,
    )
    packet_rows = state.get("packets")
    if not isinstance(packet_rows, list):
        raise ValidationError("packet rows missing", RC_AGGREGATE)
    packet_digests = _packet_digests(packet_state_path, packet_rows)
    packet_ids = set(packet_digests)
    verdict_rows, issues = _json_lines(verdict_log_path)
    if issues:
        raise ValidationError(issues, RC_AGGREGATE)
    seen: set[tuple[str, str]] = set()
    for row in verdict_rows:
        reader = row.get("reader")
        if reader not in {"parent", "second-reader"}:
            raise ValidationError("verdict reader is invalid", RC_AGGREGATE)
        _validate_verdict_row(
            row, packet_ids, task_manifest=task_manifest
        )
        if row.get("packet_sha256_at_read") != packet_digests.get(
            str(row.get("packet_id"))
        ):
            raise ValidationError(
                "verdict read-time packet digest changed before freeze",
                RC_AGGREGATE,
            )
        key = (str(row["packet_id"]), str(reader))
        if key in seen:
            raise ValidationError("duplicate reader/packet verdict", RC_AGGREGATE)
        seen.add(key)
    expected = {
        (str(packet_id), reader)
        for packet_id in packet_ids
        for reader in ("parent", "second-reader")
    }
    if seen != expected:
        raise ValidationError("both reader verdict sets are required", RC_AGGREGATE)
    freeze = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "packet_state_sha256": _sha256(packet_state_path.read_bytes()),
        "verdict_log_sha256": _sha256(verdict_log_path.read_bytes()),
        "packet_sha256_at_freeze": packet_digests,
        "frozen_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    _write_frozen_json(output, freeze, rc=RC_AGGREGATE)
    return freeze


def _custodian_mapping_path(custodian_root: Path) -> Path:
    try:
        metadata = custodian_root.lstat()
    except OSError as exc:
        raise ValidationError(
            f"mapping custodian root is unavailable: {exc}", RC_AGGREGATE
        ) from exc
    if (
        stat.S_ISLNK(metadata.st_mode)
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != 0o700
    ):
        raise ValidationError(
            "mapping custodian root must be a 0700 directory", RC_AGGREGATE
        )
    candidates = [
        path
        for path in custodian_root.iterdir()
        if stat.S_ISREG(path.lstat().st_mode)
        and stat.S_IMODE(path.lstat().st_mode) == 0o600
        and re.fullmatch(r"mapping-[0-9a-f]{48}\.json", path.name)
    ]
    if len(candidates) != 1 or len(list(custodian_root.iterdir())) != 1:
        raise ValidationError(
            "mapping custodian secret closure mismatch", RC_AGGREGATE
        )
    return candidates[0]


def reveal_mapping(
    packet_state_path: Path,
    custodian_root: Path,
    verdict_log_path: Path,
    verdict_freeze_path: Path,
    output: Path,
    *,
    task_manifest: Mapping[str, Any] = TASK_MANIFEST,
) -> dict[str, Any]:
    state = _load_json_object(packet_state_path)
    freeze = _load_json_object(verdict_freeze_path)
    task_manifest_sha256 = _require_task_manifest_sha256(
        state,
        task_manifest,
        "packet state",
        rc=RC_AGGREGATE,
    )
    _require_task_manifest_sha256(
        freeze,
        task_manifest,
        "verdict freeze",
        rc=RC_AGGREGATE,
    )
    if (
        freeze.get("packet_state_sha256") != _sha256(packet_state_path.read_bytes())
        or freeze.get("verdict_log_sha256") != _sha256(verdict_log_path.read_bytes())
    ):
        raise ValidationError("verdicts are not frozen for this packet set", RC_AGGREGATE)
    rows = state.get("packets")
    if not isinstance(rows, list):
        raise ValidationError("packet state rows missing", RC_AGGREGATE)
    packet_digests = _packet_digests(packet_state_path, rows)
    if freeze.get("packet_sha256_at_freeze") != packet_digests:
        raise ValidationError(
            "frozen packet digest does not match revealed packet bytes",
            RC_AGGREGATE,
        )
    if _parse_timestamp(freeze.get("frozen_at")) is None:
        raise ValidationError("verdict freeze timestamp is invalid", RC_AGGREGATE)
    packet_ids = set(packet_digests)
    verdict_rows, verdict_issues = _json_lines(verdict_log_path)
    if verdict_issues:
        raise ValidationError(verdict_issues, RC_AGGREGATE)
    frozen_pairs: set[tuple[str, str]] = set()
    for row in verdict_rows:
        _validate_verdict_row(
            row, packet_ids, task_manifest=task_manifest
        )
        reader = row.get("reader")
        if reader not in {"parent", "second-reader"}:
            raise ValidationError("verdict reader is invalid", RC_AGGREGATE)
        pair = (str(row["packet_id"]), str(reader))
        if pair in frozen_pairs:
            raise ValidationError(
                "duplicate reader/packet verdict", RC_AGGREGATE
            )
        frozen_pairs.add(pair)
    expected_pairs = {
        (str(packet_id), reader)
        for packet_id in packet_ids
        for reader in ("parent", "second-reader")
    }
    if frozen_pairs != expected_pairs:
        raise ValidationError(
            "both frozen reader verdict sets are required", RC_AGGREGATE
        )
    private_path = _custodian_mapping_path(custodian_root.resolve())
    private = _load_json_object(private_path)
    _require_task_manifest_sha256(
        private,
        task_manifest,
        "private packet mapping",
        rc=RC_AGGREGATE,
    )
    private_rows = private.get("mapping")
    if not isinstance(private_rows, list):
        raise ValidationError("private packet mapping missing", RC_AGGREGATE)
    if {
        row.get("packet_id") for row in private_rows if isinstance(row, dict)
    } != packet_ids:
        raise ValidationError("private/public packet set mismatch", RC_AGGREGATE)
    if any(
        not isinstance(row, dict)
        or not isinstance(row.get("run_id"), str)
        or not isinstance(row.get("slot_id"), str)
        or not all(
            isinstance(row.get(field), str)
            and re.fullmatch(r"[0-9a-f]{64}", row[field])
            for field in ("packet_sha256", "score_input_sha256")
        )
        for row in private_rows
    ):
        raise ValidationError("private packet mapping schema mismatch", RC_AGGREGATE)
    private_by_packet = {
        str(row["packet_id"]): row
        for row in private_rows
        if isinstance(row, dict)
    }
    for row in verdict_rows:
        packet_id = str(row["packet_id"])
        read_digest = row.get("packet_sha256_at_read")
        if (
            read_digest != freeze["packet_sha256_at_freeze"].get(packet_id)
            or read_digest != private_by_packet[packet_id].get("packet_sha256")
            or read_digest
            != private_by_packet[packet_id].get("score_input_sha256")
        ):
            raise ValidationError(
                f"{packet_id}: read-time packet digest/output binding mismatch",
                RC_AGGREGATE,
            )
    mapping = {
        "schema_version": SCHEMA_VERSION,
        "task_manifest_sha256": task_manifest_sha256,
        "mask_strength": "same-owner-advisory",
        "verdict_freeze_sha256": _sha256(verdict_freeze_path.read_bytes()),
        "mapping": [
            {
                "packet_id": row["packet_id"],
                "run_id": row["run_id"],
                "packet_sha256": row["packet_sha256"],
                "score_input_sha256": row["score_input_sha256"],
            }
            for row in private_rows
            if isinstance(row, dict)
        ],
    }
    _write_frozen_json(output, mapping, rc=RC_AGGREGATE)
    return mapping


def _sessions_default() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    return (
        Path(codex_home).expanduser() / "sessions"
        if codex_home
        else Path("~/.codex/sessions").expanduser()
    )


def _add_benchmark_task_selector(
    parser: argparse.ArgumentParser,
    *,
    external_aliases: bool = False,
) -> None:
    if external_aliases:
        parser.add_argument("--case")
    else:
        parser.add_argument("--case", choices=("POS", "NEG"))
    parser.add_argument("--benchmark-task-id")


def _add_task_manifest_option(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--task-manifest", type=Path)
    parser.add_argument(
        "--task-manifest-profile",
        choices=(WIRING_SLICE_PROFILE,),
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-snapshot")
    build.add_argument("--repo", type=Path, default=_ROOT)
    build.add_argument("--snapshot", type=Path, required=True)
    build.add_argument("--sessions-root", type=Path, default=_sessions_default())
    _add_benchmark_task_selector(build, external_aliases=True)
    _add_task_manifest_option(build)

    snapshot = sub.add_parser("verify-snapshot")
    snapshot.add_argument("--snapshot", type=Path, required=True)
    _add_benchmark_task_selector(snapshot)

    prompt = sub.add_parser("render-prompt")
    prompt.add_argument("--sessions-root", type=Path, default=_sessions_default())
    _add_benchmark_task_selector(prompt, external_aliases=True)
    prompt.add_argument("--new-root", type=Path, required=True)
    prompt.add_argument("--output", type=Path)
    prompt.add_argument("--snapshot-oracle", type=Path)
    _add_task_manifest_option(prompt)

    stage2_freeze = sub.add_parser("freeze-stage2-plan-replayer")
    stage2_freeze.add_argument("--plan-input", type=Path, required=True)
    stage2_freeze.add_argument(
        "--requested-model", choices=sorted(MODEL_ALLOWLIST), required=True
    )
    stage2_freeze.add_argument(
        "--requested-effort", choices=sorted(_STAGE2_EFFORTS), required=True
    )
    stage2_freeze.add_argument("--fix-pass-limit", type=int, required=True)
    stage2_freeze.add_argument(
        "--acceptance-kind", choices=sorted(_STAGE2_ACCEPTANCE_KINDS), default="unbound"
    )
    stage2_freeze.add_argument("--acceptance-reason")
    stage2_freeze.add_argument("--output", type=Path, required=True)
    stage2_freeze.add_argument("--snapshot", type=Path, required=True)
    stage2_freeze.add_argument("--config-source", type=Path, required=True)
    stage2_freeze.add_argument("--auth-source", type=Path, required=True)
    stage2_freeze.add_argument("--codex-bin", type=Path, required=True)

    collect = sub.add_parser("collect-run")
    collect.add_argument("--run-id", required=True)
    _add_benchmark_task_selector(collect, external_aliases=True)
    collect.add_argument("--requested-effort", choices=("max", "high"), required=True)
    collect.add_argument("--events", type=Path, required=True)
    collect.add_argument("--done", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--prompt", type=Path, required=True)
    collect.add_argument("--sessions-root", type=Path, default=_sessions_default())
    collect.add_argument("--snapshot", type=Path, required=True)
    collect.add_argument("--launch-receipt", type=Path, required=True)
    collect.add_argument(
        "--expected-model", dest="expected_requested_model", default=MODEL
    )
    _add_task_manifest_option(collect)

    supervisor = sub.add_parser("supervise-pair")
    supervisor.add_argument("--schedule", type=Path, required=True)
    supervisor.add_argument("--run-root", type=Path, required=True)
    supervisor.add_argument("--block-id", required=True)
    supervisor.add_argument("--attempt", type=int, required=True)
    supervisor.add_argument("--snapshot", type=Path, required=True)
    supervisor.add_argument("--prompt", type=Path, required=True)
    supervisor.add_argument("--config-source", type=Path, required=True)
    supervisor.add_argument("--auth-source", type=Path, required=True)
    supervisor.add_argument("--codex-bin", type=Path, required=True)
    supervisor.add_argument("--bwrap-bin", type=Path, default=Path("/usr/bin/bwrap"))
    supervisor.add_argument("--dry-run", action="store_true")
    _add_task_manifest_option(supervisor)

    stage2_replay = sub.add_parser("replay-stage2-plan")
    stage2_replay.add_argument("--contract", type=Path, required=True)
    stage2_replay.add_argument("--run-root", type=Path, required=True)
    stage2_replay.add_argument("--result", type=Path, required=True)
    stage2_replay.add_argument("--snapshot", type=Path, required=True)
    stage2_replay.add_argument("--config-source", type=Path)
    stage2_replay.add_argument("--auth-source", type=Path)
    stage2_replay.add_argument("--codex-bin", type=Path)
    stage2_replay.add_argument("--dry-run", action="store_true")
    stage2_replay.add_argument(
        "--wall-clock-timeout-s",
        type=float,
        default=STAGE2_REPLAYER_DEFAULT_WALL_CLOCK_TIMEOUT_S,
    )

    stage5_freeze = sub.add_parser("freeze-stage5-author-replayer")
    stage5_freeze.add_argument("--plan-input", type=Path, required=True)
    stage5_freeze.add_argument("--author-output", type=Path, required=True)
    stage5_freeze.add_argument("--output", type=Path, required=True)
    stage5_freeze.add_argument("--snapshot", type=Path, required=True)
    stage5_freeze.add_argument("--application-root", required=True)
    stage5_freeze.add_argument("--git-bin", type=Path, required=True)
    stage5_freeze.add_argument(
        "--review-model", choices=sorted(MODEL_ALLOWLIST), required=True
    )
    stage5_freeze.add_argument(
        "--review-effort", choices=sorted(_STAGE5_EFFORTS), required=True
    )
    stage5_freeze.add_argument(
        "--fix-model", choices=sorted(MODEL_ALLOWLIST), required=True
    )
    stage5_freeze.add_argument(
        "--fix-effort", choices=sorted(_STAGE5_EFFORTS), required=True
    )
    stage5_freeze.add_argument("--fix-pass-limit", type=int, required=True)

    stage5_validate = sub.add_parser("validate-stage5-author-application")
    stage5_validate.add_argument("--contract", type=Path, required=True)
    stage5_validate.add_argument("--run-root", type=Path, required=True)
    stage5_validate.add_argument("--receipt", type=Path, required=True)

    stage5_receipt = sub.add_parser("validate-stage5-downstream-receipt")
    stage5_receipt.add_argument("--contract", type=Path, required=True)
    stage5_receipt.add_argument("--run-root", type=Path, required=True)
    stage5_receipt.add_argument("--receipt", type=Path, required=True)
    stage5_receipt.add_argument(
        "--expected-role", choices=("review", "fix"), required=True
    )
    stage5_receipt.add_argument("--expected-pass-index", type=int, required=True)
    stage5_receipt.add_argument("--stdin-file", type=Path, required=True)
    stage5_receipt.add_argument("--output-file", type=Path, required=True)
    stage5_receipt.add_argument(
        "--previous-receipt", type=Path, required=True
    )

    score = sub.add_parser("score-run")
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--run-id")

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--manifest", type=Path, required=True)
    aggregate.add_argument("--sessions-root", type=Path, required=True)
    _add_task_manifest_option(aggregate)

    verify = sub.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--sessions-root", type=Path, required=True)
    _add_task_manifest_option(verify)

    packets = sub.add_parser("make-packets")
    packets.add_argument("--manifest", type=Path, required=True)
    packets.add_argument("--packet-dir", type=Path, required=True)
    packets.add_argument("--custodian-root", type=Path, required=True)
    _add_task_manifest_option(packets)

    append = sub.add_parser("append-verdicts")
    append.add_argument("--packet-state", type=Path, required=True)
    append.add_argument("--verdict-log", type=Path, required=True)
    append.add_argument(
        "--reader", choices=("parent", "second-reader"), required=True
    )
    append.add_argument("--input", type=Path, required=True)
    _add_task_manifest_option(append)

    freeze = sub.add_parser("freeze-verdicts")
    freeze.add_argument("--packet-state", type=Path, required=True)
    freeze.add_argument("--verdict-log", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)
    _add_task_manifest_option(freeze)

    reveal = sub.add_parser("reveal-mapping")
    reveal.add_argument("--packet-state", type=Path, required=True)
    reveal.add_argument("--custodian-root", type=Path, required=True)
    reveal.add_argument("--verdict-log", type=Path, required=True)
    reveal.add_argument("--verdict-freeze", type=Path, required=True)
    reveal.add_argument("--output", type=Path, required=True)
    _add_task_manifest_option(reveal)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    task_manifest: Mapping[str, Any] = TASK_MANIFEST
    task_manifest_profile = getattr(args, "task_manifest_profile", None)
    try:
        if (
            task_manifest_profile is not None
            and getattr(args, "task_manifest", None) is None
        ):
            raise ValidationError(
                "task manifest profile requires --task-manifest",
                RC_ROUTING,
            )
        task_manifest = (
            _load_task_manifest(
                args.task_manifest,
                profile=task_manifest_profile,
            )
            if getattr(args, "task_manifest", None) is not None
            else TASK_MANIFEST
        )
        _require_task_manifest_command(
            task_manifest,
            args.command,
            profile=task_manifest_profile,
        )
        benchmark_task_id: str | None = None
        if args.command in {
            "build-snapshot",
            "verify-snapshot",
            "render-prompt",
            "collect-run",
        }:
            benchmark_task_id = resolve_benchmark_task_id(
                args.benchmark_task_id,
                case=args.case,
                manifest=task_manifest,
            )
        if args.command == "build-snapshot":
            result = build_snapshot(
                args.repo,
                args.snapshot,
                args.sessions_root,
                benchmark_task_id,
                task_manifest=task_manifest,
            )
            rc = 0
        elif args.command == "verify-snapshot":
            result = verify_snapshot(
                args.snapshot,
                benchmark_task_id,
            )
            rc = 0
        elif args.command == "render-prompt":
            snapshot_oracle = (
                _load_json_object(args.snapshot_oracle)
                if args.snapshot_oracle is not None
                else None
            )
            data, result = render_prompt(
                args.sessions_root,
                benchmark_task_id,
                args.new_root,
                task_manifest=task_manifest,
                snapshot_oracle=snapshot_oracle,
            )
            if args.output:
                if args.output.exists():
                    raise ValidationError(
                        f"prompt output already exists: {args.output}", RC_SNAPSHOT
                    )
                args.output.write_bytes(data)
                result["output"] = os.fspath(args.output.resolve())
            else:
                result["prompt"] = data.decode("utf-8")
            rc = 0
        elif args.command == "freeze-stage2-plan-replayer":
            result = freeze_stage2_plan_replayer(
                args.plan_input,
                args.output,
                args.requested_model,
                args.requested_effort,
                args.fix_pass_limit,
                snapshot=args.snapshot,
                acceptance_kind=args.acceptance_kind,
                acceptance_reason=args.acceptance_reason,
                config_source=args.config_source,
                auth_source=args.auth_source,
                codex_binary=args.codex_bin,
            )
            rc = 0
        elif args.command == "collect-run":
            result, rc = collect_run(
                run_id=args.run_id,
                case=benchmark_task_id,
                requested_effort=args.requested_effort,
                events=args.events,
                done=args.done,
                output=args.output,
                prompt=args.prompt,
                sessions_root=args.sessions_root,
                snapshot=args.snapshot,
                launch_receipt=args.launch_receipt,
                expected_requested_model=args.expected_requested_model,
                task_manifest=task_manifest,
            )
        elif args.command == "supervise-pair":
            result = supervise_pair(
                schedule_path=args.schedule,
                run_root=args.run_root,
                block_id=args.block_id,
                attempt=args.attempt,
                snapshot=args.snapshot,
                prompt=args.prompt,
                config_source=args.config_source,
                auth_source=args.auth_source,
                codex_binary=args.codex_bin,
                bwrap_binary=args.bwrap_bin,
                dry_run=args.dry_run,
                task_manifest=task_manifest,
            )
            rc = 0
        elif args.command == "replay-stage2-plan":
            result, rc = replay_stage2_plan(
                contract_path=args.contract,
                run_root=args.run_root,
                result_path=args.result,
                snapshot=args.snapshot,
                config_source=args.config_source,
                auth_source=args.auth_source,
                codex_binary=args.codex_bin,
                dry_run=args.dry_run,
                wall_clock_timeout_s=args.wall_clock_timeout_s,
            )
        elif args.command == "freeze-stage5-author-replayer":
            result = freeze_stage5_author_replayer(
                args.plan_input,
                args.author_output,
                args.output,
                snapshot=args.snapshot,
                application_root=args.application_root,
                git_binary=args.git_bin,
                review_model=args.review_model,
                review_effort=args.review_effort,
                fix_model=args.fix_model,
                fix_effort=args.fix_effort,
                fix_pass_limit=args.fix_pass_limit,
            )
            rc = 0
        elif args.command == "validate-stage5-author-application":
            result = validate_stage5_author_application(
                contract_path=args.contract,
                run_root=args.run_root,
                receipt_path=args.receipt,
            )
            rc = 0
        elif args.command == "validate-stage5-downstream-receipt":
            result = validate_stage5_downstream_receipt(
                contract_path=args.contract,
                run_root=args.run_root,
                receipt_path=args.receipt,
                expected_role=args.expected_role,
                expected_pass_index=args.expected_pass_index,
                stdin_path=args.stdin_file,
                output_path=args.output_file,
                previous_receipt_path=args.previous_receipt,
            )
            rc = 0
        elif args.command == "score-run":
            result, rc = score_run(args.output, args.run_id)
        elif args.command == "aggregate":
            result, rc = aggregate_manifest(
                args.manifest,
                sessions_root=args.sessions_root,
                task_manifest=task_manifest,
            )
        elif args.command == "verify":
            result, rc = verify_manifest(
                args.manifest,
                sessions_root=args.sessions_root,
                task_manifest=task_manifest,
            )
        elif args.command == "make-packets":
            result = make_packets(
                args.manifest,
                args.packet_dir,
                args.custodian_root,
                task_manifest=task_manifest,
            )
            rc = 0
        elif args.command == "append-verdicts":
            result = append_verdicts(
                args.packet_state,
                args.verdict_log,
                args.reader,
                args.input,
                task_manifest=task_manifest,
            )
            rc = 0
        elif args.command == "freeze-verdicts":
            result = freeze_verdicts(
                args.packet_state,
                args.verdict_log,
                args.output,
                task_manifest=task_manifest,
            )
            rc = 0
        elif args.command == "reveal-mapping":
            result = reveal_mapping(
                args.packet_state,
                args.custodian_root,
                args.verdict_log,
                args.verdict_freeze,
                args.output,
                task_manifest=task_manifest,
            )
            rc = 0
        else:
            raise AssertionError(args.command)
    except ValidationError as exc:
        stage5_command = args.command in {
            "freeze-stage5-author-replayer",
            "validate-stage5-author-application",
            "validate-stage5-downstream-receipt",
        }
        result = {
            "schema_version": (
                STAGE5_AUTHOR_REPLAYER_SCHEMA_VERSION
                if stage5_command
                else STAGE2_REPLAYER_SCHEMA_VERSION
                if args.command
                in {"freeze-stage2-plan-replayer", "replay-stage2-plan"}
                else SCHEMA_VERSION
            ),
            "valid": False,
            "failure_reasons": list(exc.reasons),
        }
        if stage5_command:
            result.update(
                {
                    "task_acceptance_status": "unbound",
                    "fix_gate_eligible": False,
                    "routing_evidence_eligible": False,
                }
            )
        rc = exc.rc
    result = _with_wiring_slice_status(
        result,
        task_manifest,
        profile=task_manifest_profile,
    )
    sys.stdout.buffer.write(_canonical_bytes(result))
    return rc


if __name__ == "__main__":
    sys.exit(main())
