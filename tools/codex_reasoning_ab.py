#!/usr/bin/env python3
"""T-181 の凍結 benchmark と Codex run を read-only に検査・集計する。

このツールは reasoning の既定値を変更しない。機械層が返す R-1 は候補だけであり、
primary endpoint は arm 情報を隠した親の意味裁定である。
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import importlib.util
import json
import os
import re
import secrets
import shutil
import stat
import subprocess
import sys
import time
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


SCHEMA_VERSION = 2
BASE_COMMIT = "8c8dc5e0a337677e213b4ebabbeff5ea188111ae"
INTEGRATED_COMMIT = "9b26b3bd3acc10df95ef6ef6684a91d2ff3fa2ec"
ARTIFACT_COMMIT = "08a7e5f2fc08d57309a86ef70d00e9b050ebec9c"
BRANCH = "codex/dev-wave-t153e-t15423"
MODEL = "gpt-5.6-sol"
OLD_ROOT = (
    "/home/SFC/tanab/github/izanagi/.codex/worktrees/"
    "dev-wave-t153e-t15423"
)
ARTIFACT_DIR = "output/insights/2026-07-29_t153e-t15423-review-verbatim"

SESSION_IDS = {
    "POS": "019faca2-6e1f-7601-bfc7-be27edcfb4ba",
    "NEG": "019facbe-9584-7642-aa30-37f1c77e6c5f",
    "fix2": "019facb2-7ddb-7102-814d-eeddcb1102ed",
    "author": "019fac6b-4f74-7a03-aa4d-8a9de22b352c",
    "fix1": "019fac91-8cde-7f73-bce1-77a9d63b4269",
}
ROLLOUT_SHA256 = {
    "POS": "9b90d51079e6a2be4603b366d77283950fff79535f59dbb8b4f4eecb1374032b",
    "NEG": "40a14e9089c2a9931b661023d104dcde2d965452e7c5ce3c630dbd2662ff4012",
    "fix2": "b07581b4f0e6ef9935549e9b9783a8ebb6877d87a10265ac7916a7d4a89c880a",
    "author": "e1ffc1e5b5e6d354701798d41a97a5e6da622423214531f356db3f1bb3ce6cbe",
    "fix1": "f210f2e135f6cfdb2e6c2a40e81b784a2a8f4ac51135c353cf859365e17fb475",
}
PROMPT_SOURCE = {
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
CASE_ARTIFACTS = {
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
CASE_HASHES = {
    "POS": {
        **TRACKED_HASHES,
        "tools/check_ai_provenance.py": "bc3f5f95f5c9c3f44955bbd1b2e3affbbafb6e62fda8e836173e1b9d5998c3af",
        "orchestrator/tests/test_check_ai_provenance.py": "ed3f93d196e7c43c8ba61c83f91f065d3fc829f0d12bdc4d9ead31b2ec3d57ed",
        **{
            f"{ARTIFACT_DIR}/{name}": ARTIFACT_HASHES[name]
            for name in CASE_ARTIFACTS["POS"]
        },
    },
    "NEG": {
        **TRACKED_HASHES,
        "tools/check_ai_provenance.py": "0bc510b4e239394524aad209bd1c01ec4ff3d3d34938dec432c211bf8964970f",
        "orchestrator/tests/test_check_ai_provenance.py": "c4f5f04b8a06c03f4c7e85900e54a2c34a9ea65873e37a340f81b926df098e74",
        **{
            f"{ARTIFACT_DIR}/{name}": ARTIFACT_HASHES[name]
            for name in CASE_ARTIFACTS["NEG"]
        },
    },
}
CASE_NUMSTAT = {
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
EXPECTED_SCHEDULE = {
    ("POS", "max"): 3,
    ("POS", "high"): 3,
    ("NEG", "max"): 2,
    ("NEG", "high"): 2,
}
KNOWN_FINDINGS = {
    "A-1", "A-2", "A-3", "A-4",
    "B-1", "B-2", "B-3", "B-4", "B-5", "B-6", "R-1",
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
) -> Path:
    eligible = (
        pinned_label is not None
        and SESSION_IDS.get(pinned_label) == target_session_id
        and pinned_label in ROLLOUT_SHA256
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
                _verify_rollout_sha(resolved, pinned_label)
            except Exception:
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


def _verify_rollout_sha(path: Path, label: str) -> None:
    expected = ROLLOUT_SHA256[label]
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
) -> dict[str, bytes]:
    paths = {
        label: _find_rollout(
            sessions_root,
            SESSION_IDS[label],
            pinned_label=label,
        )
        for label in ("author", "fix1", "fix2")
    }
    if verify_source_sha:
        for label, path in paths.items():
            _verify_rollout_sha(path, label)
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


def _snapshot_spec(case: str) -> dict[str, Any]:
    return {
        "case": case,
        "head": BASE_COMMIT,
        "branch": BRANCH,
        "tracked_paths": list(TRACKED_PATHS),
        "hashes": CASE_HASHES[case],
        "numstat": [list(row) for row in CASE_NUMSTAT[case]],
        "untracked": [
            f"{ARTIFACT_DIR}/{name}" for name in CASE_ARTIFACTS[case]
        ],
        "modes": {path: stat.S_IFREG | 0o644 for path in CASE_HASHES[case]},
        "forbidden": (
            [f"{ARTIFACT_DIR}/focus1.md", f"{ARTIFACT_DIR}/focus2.md"]
            if case == "POS"
            else [f"{ARTIFACT_DIR}/focus2.md"]
        ),
    }


def _init_submodules_from_local_source(source: Path, snapshot: Path) -> None:
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
            )
            if state == "initialized":
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
    raw = _git(repo, "rev-parse", "--absolute-git-dir").decode().strip()
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

    modules_root = (_git_dir(repository) / "modules").resolve()
    admin_dir = (modules_root / name).resolve()
    if admin_dir != modules_root and modules_root not in admin_dir.parents:
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
        probe = _run(
            ("git", "rev-parse", "--show-toplevel"),
            cwd=candidate_path,
            check=False,
        )
        if (
            probe.returncode == 0
            and Path(probe.stdout.decode().strip()).resolve() == candidate
        ):
            head = _git(candidate_path, "rev-parse", "HEAD").decode().strip()
            if head != gitlink_commit:
                raise ValidationError(
                    f"initialized submodule HEAD/gitlink mismatch: "
                    f"{candidate.relative_to(snapshot).as_posix()}: "
                    f"{head} != {gitlink_commit}",
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


def _submodule_inventory(snapshot: Path) -> tuple[list[Path], list[dict[str, str]]]:
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
    repositories, _ = _submodule_inventory(snapshot)
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


def _metadata_manifest(root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
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

    The walk is not atomic if the filesystem changes while it is in progress,
    matching the existing ``Path.rglob`` behavior.  Parent resolution remains
    per path, so its call order and exception surface are unchanged; only the
    pure root-``.git`` containment decision is memoized for resolved parents.
    """
    found: set[str] = set()
    root_git = (snapshot / ".git").resolve()
    parent_is_root_git: dict[Path, bool] = {}
    for path in snapshot.rglob("*"):
        resolved_parent = path.parent.resolve()
        is_root_git = parent_is_root_git.get(resolved_parent)
        if is_root_git is None:
            is_root_git = (
                resolved_parent == root_git or root_git in resolved_parent.parents
            )
            parent_is_root_git[resolved_parent] = is_root_git
        if is_root_git:
            continue
        metadata = path.lstat()
        if not stat.S_ISDIR(metadata.st_mode):
            found.add(path.relative_to(snapshot).as_posix())
    return found


def _index_stage_entries(repository: Path) -> list[tuple[str, str, str, str]]:
    entries: list[tuple[str, str, str, str]] = []
    raw = _git(repository, "ls-files", "--stage", "-z")
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


def _expected_filesystem_files(snapshot: Path, untracked: Iterable[str]) -> set[str]:
    snapshot = snapshot.resolve()
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


def _one_git_closure_reasons(
    snapshot: Path,
    repository: Path,
    expected_refs: list[str],
) -> tuple[list[str], dict[str, Any]]:
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
        if path.is_dir():
            if any(path.rglob("*")):
                reasons.append(f"{label}: {closure_label} closure is not empty")
        elif path.exists() and path.stat().st_size:
            reasons.append(f"{label}: {closure_label} closure is not empty")
    pseudo_refs = sorted(
        path.name
        for path in git_dir.iterdir()
        if path.is_file()
        and (
            path.name.endswith("_HEAD")
            or path.name in {"MERGE_HEAD", "BISECT_HEAD", "REVERT_HEAD", "CHERRY_PICK_HEAD"}
        )
    )
    if pseudo_refs:
        reasons.append(f"{label}: pseudo refs are present: {pseudo_refs}")
    metadata = _metadata_manifest(git_dir)
    commit_graph_reasons, commit_graph = _commit_graph_manifest(
        repository, label, metadata
    )
    reasons.extend(commit_graph_reasons)
    fsck = _run(
        ("git", "fsck", "--unreachable", "--no-reflogs"),
        cwd=repository,
        check=False,
    )
    reasons.extend(_git_fsck_reasons(label, fsck))
    return reasons, {
        "repository": label,
        "git_dir": git_dir.relative_to(snapshot).as_posix()
        if snapshot == git_dir or snapshot in git_dir.parents
        else os.fspath(git_dir),
        "head": _git(repository, "rev-parse", "HEAD").decode().strip(),
        "refs": refs,
        "commit_graph": commit_graph,
        "metadata": metadata,
    }


def _git_closure_reasons(
    snapshot: Path, untracked: Iterable[str]
) -> tuple[list[str], list[dict[str, Any]], list[dict[str, str]]]:
    initialized, submodules = _submodule_inventory(snapshot)
    reasons, root_manifest = _one_git_closure_reasons(
        snapshot, snapshot, [f"refs/heads/{BRANCH}"]
    )
    manifests = [root_manifest]
    for repository in initialized:
        nested_reasons, nested_manifest = _one_git_closure_reasons(
            snapshot, repository, []
        )
        reasons.extend(nested_reasons)
        manifests.append(nested_manifest)
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
    actual_files = _filesystem_file_set(snapshot)
    expected_files = _expected_filesystem_files(snapshot, untracked)
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


def _prepare_snapshot_case(
    repo: Path, sessions_root: Path, case: str
) -> dict[str, bytes]:
    if case not in CASE_HASHES:
        raise ValidationError(f"unknown case: {case}", RC_SNAPSHOT)
    return (
        derive_independent_golden(repo, sessions_root)
        if case == "POS"
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
) -> dict[str, Any]:
    if case == "POS":
        for path, data in golden.items():
            target = snapshot / path
            target.write_bytes(data)
            target.chmod(0o644)
    for name in CASE_ARTIFACTS[case]:
        relative = f"{ARTIFACT_DIR}/{name}"
        target = snapshot / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_git(repo, "show", f"{ARTIFACT_COMMIT}:{relative}"))
        target.chmod(0o644)
    return verify_snapshot(snapshot, case)


def _derive_snapshot_from_base(
    repo: Path,
    base: Path,
    snapshot: Path,
    sessions_root: Path,
    case: str,
    *,
    prepared_golden: Mapping[str, bytes] | None = None,
    prepared_destination: tuple[Path, Path] | None = None,
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
    if case not in CASE_HASHES:
        raise ValidationError(f"unknown case: {case}", RC_SNAPSHOT)
    golden = (
        _prepare_snapshot_case(repo, sessions_root, case)
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
    return _finish_snapshot_case(repo, snapshot, case, golden)


def build_snapshot(
    repo: Path,
    snapshot: Path,
    sessions_root: Path,
    case: str,
) -> dict[str, Any]:
    repo, snapshot = _resolve_snapshot_destination(repo, snapshot)
    golden = _prepare_snapshot_case(repo, sessions_root, case)
    _build_snapshot_base(repo, snapshot)
    return _finish_snapshot_case(repo, snapshot, case, golden)


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
) -> dict[str, Any]:
    snapshot = snapshot.resolve()
    expected = dict(spec or _snapshot_spec(case))
    reasons: list[str] = []
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
            snapshot, expected["untracked"]
        )
        reasons.extend(closure_reasons)
    else:
        _, submodule_manifest = _submodule_inventory(snapshot)
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
        "filesystem_files": sorted(_filesystem_file_set(snapshot)),
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
) -> tuple[bytes, dict[str, Any]]:
    if case not in ("POS", "NEG"):
        raise ValidationError(f"unknown case: {case}", RC_SNAPSHOT)
    rollout = _find_rollout(
        sessions_root,
        SESSION_IDS[case],
        pinned_label=case,
    )
    if verify_source:
        _verify_rollout_sha(rollout, case)
    message = extract_user_message(rollout)
    source = message.encode("utf-8")
    pin = PROMPT_SOURCE[case]
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
        f"{ARTIFACT_DIR}/{name}" for name in CASE_ARTIFACTS[case]
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
        "case": case,
        "source_session_id": SESSION_IDS[case],
        "source_rollout_sha256": _sha256(rollout.read_bytes()),
        "source_prompt_sha256": _sha256(source),
        "rendered_prompt_sha256": _sha256(data),
        "replacement_count": count,
        "new_root": new,
        "absolute_paths": sorted(rooted_paths),
        "untracked_paths": sorted(requested_untracked),
    }
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


def _normalized_exec_argv(argv: Sequence[str], effort: str) -> list[str]:
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
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o600)
    try:
        os.write(descriptor, _canonical_bytes(dict(value)))
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


def _copy_identity_file(source: Path, target: Path, label: str) -> str:
    source = source.resolve(strict=True)
    metadata = source.lstat()
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ValidationError(f"{label} source is not a regular file", RC_RECEIPT)
    shutil.copyfile(source, target)
    target.chmod(0o600)
    source_sha = _sha256(source.read_bytes())
    if _sha256(target.read_bytes()) != source_sha:
        raise ValidationError(f"{label} copy sha mismatch", RC_RECEIPT)
    return source_sha


def _codex_exec_argv(
    codex_binary: Path,
    arm: str,
    snapshot: Path,
    output: Path,
) -> list[str]:
    return [
        os.fspath(codex_binary),
        "exec",
        "-m",
        MODEL,
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
) -> dict[str, Any]:
    slot_id = str(slot["slot_id"])
    case = str(slot["case"])
    arm = str(slot["arm"])
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
    oracle_before = verify_snapshot(snapshot, case)
    oracle_before_path = attempt_dir / "snapshot-before.json"
    _write_frozen_json(oracle_before_path, oracle_before)

    actual_cli = codex_binary.resolve(strict=True)
    actual_bwrap = bwrap_binary.resolve(strict=True)
    version_probe = _run((os.fspath(actual_cli), "--version"), cwd=attempt_dir)
    cli_version = version_probe.stdout.decode("utf-8", "replace").strip()
    if not cli_version:
        raise ValidationError("CLI version output is empty", RC_ROUTING)
    bwrap_version_probe = _run(
        (os.fspath(actual_bwrap), "--version"), cwd=attempt_dir
    )
    bwrap_version = bwrap_version_probe.stdout.decode(
        "utf-8", "replace"
    ).strip()
    if not bwrap_version:
        raise ValidationError("bwrap version output is empty", RC_ROUTING)
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
    codex_argv = _codex_exec_argv(actual_cli, arm, snapshot, output)
    normalized_argv = _normalized_exec_argv(codex_argv, arm)
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
            "run_id": run_id,
            "slot_id": slot_id,
            "attempt": attempt,
            "parent_run_id": parent_run_id,
            "case": case,
            "arm": arm,
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
        oracle_after = verify_snapshot(snapshot, case)
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
        if frozen_schedule.read_bytes() != source_schedule_bytes:
            raise ValidationError("run-root schedule bytes changed", RC_ROUTING)
    else:
        frozen_schedule.write_bytes(source_schedule_bytes)
    schedule_sha = _sha256(frozen_schedule.read_bytes())
    schedule = _load_json_object(frozen_schedule)
    slots, schedule_reasons = _validate_schedule(schedule)
    if schedule_reasons:
        raise ValidationError(schedule_reasons, RC_ROUTING)
    block_slots = [row for row in slots if row.get("block_id") == block_id]
    if len(block_slots) != 2:
        raise ValidationError("supervisor block must contain two slots", RC_ROUTING)
    block_slots.sort(key=lambda row: int(row["block_order"]))
    if len({row["case"] for row in block_slots}) != 1:
        raise ValidationError("supervisor block case mismatch", RC_ROUTING)
    oracle_probe = verify_snapshot(snapshot, str(block_slots[0]["case"]))
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
    launch_path: Path, launch: Mapping[str, Any], arm: str
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
            launch.get("argv", []), arm
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
    expected_model: str = MODEL,
) -> tuple[dict[str, Any], int]:
    reasons: list[str] = []
    launch = _load_json_object(launch_receipt)
    for field, expected_value in (
        ("run_id", run_id),
        ("case", case),
        ("arm", requested_effort),
    ):
        if launch.get(field) != expected_value:
            reasons.append(f"launch receipt {field} mismatch")
    reasons.extend(_verify_launch_receipt(launch_receipt, launch, requested_effort))
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
        if contexts and contexts[0].get("model") != expected_model:
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


def _load_json_object(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_bytes())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValidationError(f"cannot read JSON object {path}: {exc}", RC_AGGREGATE) from exc
    if not isinstance(value, dict):
        raise ValidationError(f"JSON artifact is not an object: {path}", RC_AGGREGATE)
    return value


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


def _validate_schedule(schedule: Mapping[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    reasons: list[str] = []
    slots = schedule.get("slots")
    if not isinstance(slots, list):
        return [], ["schedule.slots is not an array"]
    counts: dict[tuple[str, str], int] = {}
    seen: set[str] = set()
    blocks: dict[str, list[dict[str, Any]]] = {}
    for index, row in enumerate(slots):
        if not isinstance(row, dict) or not isinstance(row.get("slot_id"), str):
            reasons.append("schedule slot row malformed")
            continue
        slot_id = row["slot_id"]
        try:
            _assert_arm_neutral_paths(
                [slot_id, str(row.get("block_id", ""))]
            )
        except ValidationError as exc:
            reasons.extend(exc.reasons)
        if slot_id in seen:
            reasons.append(f"duplicate slot_id: {slot_id}")
        seen.add(slot_id)
        key = (row.get("case"), row.get("arm"))
        counts[key] = counts.get(key, 0) + 1
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
        if row.get("block_order") not in {1, 2}:
            reasons.append(f"{slot_id}: block_order must be 1 or 2")
    if len(slots) != 10 or counts != EXPECTED_SCHEDULE:
        reasons.append(f"logical slot cardinality mismatch: {counts}")
    for block_id, rows in blocks.items():
        if (
            len(rows) != 2
            or {row.get("arm") for row in rows} != {"max", "high"}
            or len({row.get("case") for row in rows}) != 1
            or [row.get("block_order") for row in rows] != [1, 2]
            or rows[1]["_index"] != rows[0]["_index"] + 1
        ):
            reasons.append(f"sequential crossover block mismatch: {block_id}")
    scheduled_cases = {
        row.get("case") for row in slots if isinstance(row, dict)
    }
    if scheduled_cases <= {"POS", "NEG"}:
        for case in ("POS", "NEG"):
            case_rows = [
                row
                for row in slots
                if isinstance(row, dict) and row.get("case") == case
            ]
            for field in ("prompt_sha256", "snapshot_manifest_sha256"):
                if len({row.get(field) for row in case_rows}) != 1:
                    reasons.append(f"{case}: {field} concentration is not 1")
        submodule_states = {
            row.get("submodule_manifest_sha256")
            for row in slots
            if isinstance(row, dict)
        }
        if len(submodule_states) != 1:
            reasons.append(
                "POS/NEG submodule initialization and gitlink state mismatch"
            )
    return [row for row in slots if isinstance(row, dict)], reasons


def _load_adjudication(
    manifest_path: Path,
    manifest: Mapping[str, Any],
    slots: Sequence[Mapping[str, Any]],
    final_attempts: Mapping[str, Mapping[str, Any]],
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
            _validate_verdict_row(row, set(packets))
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
    for packet_id, mapping_row in mapping.items():
        run_id = mapping_row.get("run_id")
        packet = packets.get(packet_id, {})
        reader_rows = verdict_by_packet.get(packet_id, {})
        parent_verdict = reader_rows.get("parent", {})
        second_verdict = reader_rows.get("second-reader", {})
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
        slot = slot_by_run.get(run_id)
        attempt = next(
            (value for value in final_attempts.values() if value.get("run_id") == run_id),
            None,
        )
        if slot is None or attempt is None:
            reasons.append(f"{packet_id}: run_id join failed")
            continue
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


def _aggregate_token_usage_observations(
    attempts: Sequence[Mapping[str, Any]], reasons: list[str]
) -> dict[str, Any]:
    by_arm_case = {
        arm: {case: 0 for case in ("POS", "NEG")}
        for arm in ("max", "high")
    }
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
        arm = attempt.get("arm")
        case = attempt.get("case")
        if arm not in by_arm_case or case not in by_arm_case[str(arm)]:
            reasons.append(
                f"{run_id}: {ZERO_COMPONENT_TOTAL_ONLY} arm/case missing"
            )
            continue
        by_arm_case[str(arm)][str(case)] += count
        total_count += count
    return {
        ZERO_COMPONENT_TOTAL_ONLY: {
            "total_count": total_count,
            "by_arm_case": by_arm_case,
        }
    }


def _aggregate_verified(
    manifest_path: Path,
    slots: Sequence[Mapping[str, Any]],
    attempts: Sequence[Mapping[str, Any]],
    verdicts: Mapping[str, Mapping[str, Any]],
    reasons: list[str],
) -> dict[str, Any]:
    grouped: dict[str, list[Mapping[str, Any]]] = {
        str(slot["slot_id"]): [] for slot in slots
    }
    for attempt in attempts:
        grouped.setdefault(str(attempt.get("slot_id")), []).append(attempt)
    token_usage_observations = _aggregate_token_usage_observations(
        attempts, reasons
    )
    final_attempts = {
        slot_id: sorted(rows, key=lambda row: int(row["attempt"]))[-1]
        for slot_id, rows in grouped.items()
        if rows
    }
    experiment_complete = (
        not reasons
        and len(final_attempts) == 10
        and all(
            row.get("failure_class")
            not in {"technical-invalid", "pair-invalidated"}
            for row in final_attempts.values()
        )
    )
    primary: dict[str, dict[str, int]] = {}
    for arm in ("max", "high"):
        arm_slots = [
            slot for slot in slots if slot.get("case") == "POS" and slot.get("arm") == arm
        ]
        primary[arm] = {
            "k": sum(
                bool(verdicts.get(str(slot["slot_id"]), {}).get("r1_detected"))
                and final_attempts.get(str(slot["slot_id"]), {}).get("failure_class") is None
                for slot in arm_slots
            ),
            "n": len(arm_slots),
        }
    false_findings: dict[str, int] = {"max": 0, "high": 0}
    novel_by_root: dict[str, dict[str, Any]] = {}
    for slot in slots:
        slot_id = str(slot["slot_id"])
        verdict = verdicts.get(slot_id, {})
        for finding in verdict.get("findings", []) if isinstance(verdict.get("findings"), list) else []:
            if not isinstance(finding, dict) or finding.get("real") is not True:
                continue
            equivalent = finding.get("equivalent_to")
            if equivalent is not None and equivalent not in KNOWN_FINDINGS:
                reasons.append(f"{slot_id}: unknown equivalent finding id")
            if (
                slot.get("case") == "NEG"
                and finding.get("severity") in {"CRITICAL", "HIGH"}
                and finding.get("must_fix") is True
            ):
                false_findings[str(slot.get("arm"))] += 1
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
    if reasons:
        experiment_complete = False
    if experiment_complete:
        max_k, high_k = primary["max"]["k"], primary["high"]["k"]
        if max_k == high_k == 3:
            quality = "この6 runでは劣化を観測しなかった"
            pos_eligibility = {"max": True, "high": True}
        elif max_k == 3 and high_k <= 2:
            quality = "highはzero-miss安全条件を満たさない"
            pos_eligibility = {"max": True, "high": False}
        elif max_k <= 2 and high_k == 3:
            quality = "benchmarkまたはmax基準が不安定"
            pos_eligibility = {"max": False, "high": False}
        else:
            quality = "品質判断不能"
            pos_eligibility = {"max": False, "high": False}
        excluded_arms = sorted(
            arm for arm, count in false_findings.items() if count > 0
        )
        decision = {
            "row": (
                "NEG_ADJUDICATED_FALSE_FINDING"
                if excluded_arms
                else "POS_PRIMARY"
            ),
            "reason": (
                f"label-masked R-1 judgment max={max_k}/3 high={high_k}/3; "
                f"NEG real false finding occurrence={false_findings}"
            ),
            "quality_decision": quality,
            "pos_adoption_eligibility": pos_eligibility,
            "neg_excluded_arms": excluded_arms,
            "adoption_eligibility": {
                arm: pos_eligibility[arm] and arm not in excluded_arms
                for arm in ("max", "high")
            },
        }
    reliability = {
        arm: sum(
            attempt.get("failure_class") == "post-treatment"
            or attempt.get("individual_failure_class") == "post-treatment"
            for attempt in attempts
            if attempt.get("arm") == arm
        )
        for arm in ("max", "high")
    }
    resources = [
        {
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
        for attempt in attempts
    ]
    if not experiment_complete:
        primary_output = None
        findings_output = None
        reliability_output = None
        escalation_output = None
        decision_output = None
        agreement_output = None
    else:
        primary_output = primary
        findings_output = sorted(
            novel_by_root.values(), key=lambda row: row["root_cause"]
        )
        reliability_output = reliability
        escalation_output = reliability["high"] > 0
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
    return {
        "schema_version": SCHEMA_VERSION,
        "manifest_sha256": _sha256(manifest_path.read_bytes()),
        "valid": not reasons,
        "failure_reasons": sorted(set(reasons)),
        "experiment_complete": experiment_complete,
        "primary_judgment_ledger": primary_output,
        "new_finding_ledger": findings_output,
        "resource_ledger": resources,
        "token_usage_observations": token_usage_observations,
        "turn_accounting": {
            "protocol": "single-turn-required",
            "comparative_metric": "model_calls",
            "logical_turns_reported": False,
        },
        "post_treatment_reliability": reliability_output,
        "online_max_escalation_candidate": escalation_output,
        "reader_agreement": agreement_output,
        "decision": decision_output,
    }


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
    manifest_path: Path, sessions_root: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, dict[str, Any]], list[str]]:
    manifest_path = manifest_path.resolve()
    manifest = _load_json_object(manifest_path)
    reasons: list[str] = []
    schedule_path = _artifact_path(manifest_path, manifest.get("schedule"), "schedule")
    schedule = _load_json_object(schedule_path)
    slots, schedule_reasons = _validate_schedule(schedule)
    reasons.extend(schedule_reasons)
    schedule_sha = _sha256(schedule_path.read_bytes())
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
    snapshot_cache: set[str] = set()
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
            for field, expected_value in (
                ("run_id", run_id),
                ("slot_id", slot_id),
                ("attempt", attempt_number),
                ("parent_run_id", row.get("parent_run_id")),
                ("case", slot.get("case")),
                ("arm", slot.get("arm")),
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
            if oracle.get("submodule_manifest_sha256") != slot.get(
                "submodule_manifest_sha256"
            ):
                reasons.append(
                    f"{run_id}: scheduled submodule initialization or "
                    "gitlink state mismatch"
                )
            if oracle_path.as_posix() not in snapshot_cache:
                replay_oracle = verify_snapshot(Path(oracle["snapshot"]), str(slot["case"]))
                if _canonical_bytes(replay_oracle) != oracle_path.read_bytes():
                    reasons.append(f"{run_id}: snapshot oracle replay mismatch")
                if oracle_after != oracle or oracle_after_path.read_bytes() != oracle_path.read_bytes():
                    reasons.append(f"{run_id}: pre/post snapshot oracle mismatch")
                snapshot_cache.add(oracle_path.as_posix())
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
        manifest_path, manifest, slots, final_attempts
    )
    reasons.extend(adjudication_reasons)
    identities: dict[str, set[str]] = {"POS": set(), "NEG": set()}
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
        identities[str(row["case"])].add(str(launch.get("treatment_identity_sha256")))
    for case, values in identities.items():
        if values and len(values) != 1:
            reasons.append(f"{case}: treatment identity concentration is not 1")
    return slots, attempts, verdicts, reasons


def verify_manifest(
    manifest_path: Path, sessions_root: Path | None = None
) -> tuple[dict[str, Any], int]:
    if sessions_root is None:
        return {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "failure_reasons": ["sessions-root is required"],
        }, RC_AGGREGATE
    try:
        slots, attempts, verdicts, reasons = _replay_manifest(
            manifest_path, sessions_root.resolve()
        )
        output = _aggregate_verified(
            manifest_path.resolve(), slots, attempts, verdicts, reasons
        )
    except ValidationError as exc:
        output = {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "failure_reasons": list(exc.reasons),
        }
    return output, 0 if output.get("valid") else RC_AGGREGATE


def aggregate_manifest(
    manifest_path: Path, *, sessions_root: Path | None = None
) -> tuple[dict[str, Any], int]:
    return verify_manifest(manifest_path, sessions_root=sessions_root)


def make_packets(
    manifest_path: Path, packet_dir: Path, custodian_root: Path
) -> dict[str, Any]:
    manifest = _load_json_object(manifest_path)
    attempts = manifest.get("attempts")
    if not isinstance(attempts, list):
        raise ValidationError("manifest.attempts is not an array", RC_AGGREGATE)
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in attempts:
        if isinstance(row, dict) and isinstance(row.get("slot_id"), str):
            grouped.setdefault(row["slot_id"], []).append(row)
    if len(grouped) != 10:
        raise ValidationError("packets require exactly 10 logical slots", RC_AGGREGATE)
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
    candidates = list(grouped.items())
    secrets.SystemRandom().shuffle(candidates)
    for slot_id, slot_attempts in candidates:
        final = max(slot_attempts, key=lambda row: int(row.get("attempt", 0)))
        run_id = final.get("run_id")
        output_path = _artifact_path(
            manifest_path.resolve(), final.get("output"), f"{run_id}:packet-output"
        )
        packet_id = secrets.token_hex(16)
        filename = f"packet-{packet_id}.md"
        target = packet_dir / filename
        body = output_path.read_bytes()
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
            "mask_strength": "same-owner-advisory",
            "mapping": private_rows,
        },
        rc=RC_AGGREGATE,
    )
    private_path.chmod(0o600)
    return {
        "schema_version": SCHEMA_VERSION,
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
) -> None:
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
    for finding in row.get("findings", []):
        if not isinstance(finding, dict) or not isinstance(finding.get("real"), bool):
            raise ValidationError("finding verdict schema mismatch", RC_AGGREGATE)
        if finding.get("severity") not in {"CRITICAL", "HIGH", "MEDIUM", "LOW"}:
            raise ValidationError("finding severity is invalid", RC_AGGREGATE)
        if not isinstance(finding.get("must_fix"), bool):
            raise ValidationError("finding must_fix must be boolean", RC_AGGREGATE)
        equivalent = finding.get("equivalent_to")
        if equivalent is not None and equivalent not in KNOWN_FINDINGS:
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
) -> dict[str, Any]:
    state = _load_json_object(packet_state_path)
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
                "packet_sha256_at_read": packet_digests[packet_id],
            },
            packet_ids,
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
                "packet_sha256_at_read": packet_digests[packet_id],
            },
        )
    return {
        "schema_version": SCHEMA_VERSION,
        "reader": reader,
        "appended": len(verdict_rows),
        "verdict_log_sha256": _sha256(verdict_log_path.read_bytes()),
    }


def freeze_verdicts(
    packet_state_path: Path, verdict_log_path: Path, output: Path
) -> dict[str, Any]:
    state = _load_json_object(packet_state_path)
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
        _validate_verdict_row(row, packet_ids)
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
) -> dict[str, Any]:
    state = _load_json_object(packet_state_path)
    freeze = _load_json_object(verdict_freeze_path)
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
        _validate_verdict_row(row, packet_ids)
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


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-snapshot")
    build.add_argument("--repo", type=Path, default=_ROOT)
    build.add_argument("--snapshot", type=Path, required=True)
    build.add_argument("--sessions-root", type=Path, default=_sessions_default())
    build.add_argument("--case", choices=("POS", "NEG"), required=True)

    snapshot = sub.add_parser("verify-snapshot")
    snapshot.add_argument("--snapshot", type=Path, required=True)
    snapshot.add_argument("--case", choices=("POS", "NEG"), required=True)

    prompt = sub.add_parser("render-prompt")
    prompt.add_argument("--sessions-root", type=Path, default=_sessions_default())
    prompt.add_argument("--case", choices=("POS", "NEG"), required=True)
    prompt.add_argument("--new-root", type=Path, required=True)
    prompt.add_argument("--output", type=Path)

    collect = sub.add_parser("collect-run")
    collect.add_argument("--run-id", required=True)
    collect.add_argument("--case", choices=("POS", "NEG"), required=True)
    collect.add_argument("--requested-effort", choices=("max", "high"), required=True)
    collect.add_argument("--events", type=Path, required=True)
    collect.add_argument("--done", type=Path, required=True)
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--prompt", type=Path, required=True)
    collect.add_argument("--sessions-root", type=Path, default=_sessions_default())
    collect.add_argument("--snapshot", type=Path, required=True)
    collect.add_argument("--launch-receipt", type=Path, required=True)
    collect.add_argument("--expected-model", default=MODEL)

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

    score = sub.add_parser("score-run")
    score.add_argument("--output", type=Path, required=True)
    score.add_argument("--run-id")

    aggregate = sub.add_parser("aggregate")
    aggregate.add_argument("--manifest", type=Path, required=True)
    aggregate.add_argument("--sessions-root", type=Path, required=True)

    verify = sub.add_parser("verify")
    verify.add_argument("--manifest", type=Path, required=True)
    verify.add_argument("--sessions-root", type=Path, required=True)

    packets = sub.add_parser("make-packets")
    packets.add_argument("--manifest", type=Path, required=True)
    packets.add_argument("--packet-dir", type=Path, required=True)
    packets.add_argument("--custodian-root", type=Path, required=True)

    append = sub.add_parser("append-verdicts")
    append.add_argument("--packet-state", type=Path, required=True)
    append.add_argument("--verdict-log", type=Path, required=True)
    append.add_argument(
        "--reader", choices=("parent", "second-reader"), required=True
    )
    append.add_argument("--input", type=Path, required=True)

    freeze = sub.add_parser("freeze-verdicts")
    freeze.add_argument("--packet-state", type=Path, required=True)
    freeze.add_argument("--verdict-log", type=Path, required=True)
    freeze.add_argument("--output", type=Path, required=True)

    reveal = sub.add_parser("reveal-mapping")
    reveal.add_argument("--packet-state", type=Path, required=True)
    reveal.add_argument("--custodian-root", type=Path, required=True)
    reveal.add_argument("--verdict-log", type=Path, required=True)
    reveal.add_argument("--verdict-freeze", type=Path, required=True)
    reveal.add_argument("--output", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.command == "build-snapshot":
            result = build_snapshot(
                args.repo, args.snapshot, args.sessions_root, args.case
            )
            rc = 0
        elif args.command == "verify-snapshot":
            result = verify_snapshot(args.snapshot, args.case)
            rc = 0
        elif args.command == "render-prompt":
            data, result = render_prompt(
                args.sessions_root, args.case, args.new_root
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
        elif args.command == "collect-run":
            result, rc = collect_run(
                run_id=args.run_id,
                case=args.case,
                requested_effort=args.requested_effort,
                events=args.events,
                done=args.done,
                output=args.output,
                prompt=args.prompt,
                sessions_root=args.sessions_root,
                snapshot=args.snapshot,
                launch_receipt=args.launch_receipt,
                expected_model=args.expected_model,
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
            )
            rc = 0
        elif args.command == "score-run":
            result, rc = score_run(args.output, args.run_id)
        elif args.command == "aggregate":
            result, rc = aggregate_manifest(
                args.manifest, sessions_root=args.sessions_root
            )
        elif args.command == "verify":
            result, rc = verify_manifest(
                args.manifest, sessions_root=args.sessions_root
            )
        elif args.command == "make-packets":
            result = make_packets(
                args.manifest, args.packet_dir, args.custodian_root
            )
            rc = 0
        elif args.command == "append-verdicts":
            result = append_verdicts(
                args.packet_state,
                args.verdict_log,
                args.reader,
                args.input,
            )
            rc = 0
        elif args.command == "freeze-verdicts":
            result = freeze_verdicts(
                args.packet_state, args.verdict_log, args.output
            )
            rc = 0
        elif args.command == "reveal-mapping":
            result = reveal_mapping(
                args.packet_state,
                args.custodian_root,
                args.verdict_log,
                args.verdict_freeze,
                args.output,
            )
            rc = 0
        else:
            raise AssertionError(args.command)
    except ValidationError as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "valid": False,
            "failure_reasons": list(exc.reasons),
        }
        rc = exc.rc
    sys.stdout.buffer.write(_canonical_bytes(result))
    return rc


if __name__ == "__main__":
    sys.exit(main())
