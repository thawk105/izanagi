#!/usr/bin/env python3
"""T-247 reservation-envelope mutation harness.

The harness intentionally mutates tracked files in place.  It is therefore
single-run only, fixed to the integration commit, and restores every target by
comparing its text with the source captured before injection.
"""
from __future__ import annotations

import argparse
import datetime as dt
import difflib
import fcntl
import hashlib
import json
import os
import re
import signal
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


HARNESS_DIR = Path(__file__).resolve().parent
REPO = HARNESS_DIR.parent
TARGET_COMMIT = "4573ca813b690a93395f955a0f4efb06b98a634b"
DEFAULT_LEDGER = HARNESS_DIR / "ledger.jsonl"
DEFAULT_TIMEOUT_S = 600.0
ANSI_RE = re.compile(r"\x1b(?:\[[0-?]*[ -/]*[@-~]|\][^\x07]*(?:\x07|\x1b\\))")
FAILED_RE = re.compile(r"^FAILED (?P<node>.+?)(?: - .*)?$")
DISPATCH_CHILD_STDOUT_BEGIN_RE = re.compile(
    r"^\[Pegasus dispatch\] request \S+ child stdout begin$"
)
DISPATCH_CHILD_STDOUT_END_RE = re.compile(
    r"^\[Pegasus dispatch\] request \S+ child stdout end$"
)
PYTEST_SUMMARY_COUNT_RE = re.compile(
    r"\b(?P<count>\d+)\s+"
    r"(?P<label>failed|passed|errors?|skipped|xfailed|xpassed|deselected|warnings?|reruns?)\b"
)

SUBMIT = "tools/pegasus/submit_t126_qualification.sh"
JOB = "tools/pegasus/t126_qualification.sh"
CONTRACT = "orchestrator/qualification/contract.py"
TOOLS_TEST = "orchestrator/tests/test_t126_pegasus_tools.py"
CONTRACT_TEST = "orchestrator/tests/test_t126_qualification_contract.py"


class HarnessAbort(RuntimeError):
    """A fail-closed harness error."""


@dataclass(frozen=True)
class Replacement:
    old: str
    new: str
    label: str


@dataclass(frozen=True)
class MutationSpec:
    mutation_id: str
    target_file: str
    replacements: tuple[Replacement, ...]
    pytest_target: str
    k_expr: str
    expected_kill_nodes: tuple[str, ...]
    semantic_basis: str
    timeout_is_semantic_evidence: bool = False


def replacement(old: str, new: str, label: str) -> Replacement:
    return Replacement(old=old, new=new, label=label)


SUBMIT_TYPE_LOOP = (
    'for key in keys[1:]:\n'
    '    if type(p[key]) is not int:\n'
    '        raise SystemExit("T-126 reservation policy type mismatch")\n'
)
JOB_MAPPING = (
    '[[ "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 \\\n'
    '  && "$PROLOGUE_CAP_S" == 900 ]] || exit 2\n'
)
SUBMIT_MAPPING = (
    '[[ "$PROJECT" == SFC && "$QUEUE" == gen_S && "$NODES" == 1 \\\n'
    '  && "$WALLTIME" == 10:00:00 && "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 ]] || exit 2\n'
)


def _node(path: str, test: str, parameter: str | None = None) -> str:
    suffix = f"[{parameter}]" if parameter is not None else ""
    return f"{path}::{test}{suffix}"


def _single_node_spec(
    mutation_id: str,
    target_file: str,
    replacements: Sequence[Replacement],
    test_file: str,
    test_name: str,
    semantic_basis: str,
    *,
    parameter: str | None = None,
    timeout_is_semantic_evidence: bool = False,
) -> MutationSpec:
    expected = _node(test_file, test_name, parameter)
    return MutationSpec(
        mutation_id=mutation_id,
        target_file=target_file,
        replacements=tuple(replacements),
        pytest_target=expected,
        k_expr=test_name,
        expected_kill_nodes=(expected,),
        semantic_basis=semantic_basis,
        timeout_is_semantic_evidence=timeout_is_semantic_evidence,
    )


def _submit_cap_line(key: str, value: int) -> str:
    return f'        or p["t126_qualification_{key}"] != {value}\n'


def _submit_type_replacement(key: str) -> Replacement:
    new = (
        'for key in (candidate for candidate in keys[1:] '\
        f'if candidate != "t126_qualification_{key}"):\n'
        '    if type(p[key]) is not int:\n'
        '        raise SystemExit("T-126 reservation policy type mismatch")\n'
    )
    return replacement(SUBMIT_TYPE_LOOP, new, f"strict-int scan excludes {key}")


def _job_expected_line(key: str, value: str) -> str:
    return f'    "t126_qualification_{key}":{value},\n'


def _job_numeric_line(key: str) -> str:
    return f'    "t126_qualification_{key}",\n'


def build_specs() -> tuple[MutationSpec, ...]:
    specs: list[MutationSpec] = []
    submit_caps = {
        "prologue_cap_s": 900,
        "attestation_cap_s": 600,
        "finalize_reserve_s": 600,
    }
    submit_test = "test_submit_rejects_compensating_cap_drift_before_scheduler_calls"
    for mutation_id, keys, parameter in (
        ("M-S1", ("prologue_cap_s", "attestation_cap_s"), "1500-0-600"),
        ("M-S2", ("prologue_cap_s", "finalize_reserve_s"), "1500-600-0"),
        ("M-S3", ("attestation_cap_s", "finalize_reserve_s"), "900-1200-0"),
        (
            "M-S4",
            ("prologue_cap_s", "attestation_cap_s", "finalize_reserve_s"),
            "1500-0-600",
        ),
    ):
        specs.append(_single_node_spec(
            mutation_id,
            SUBMIT,
            [replacement(
                _submit_cap_line(key, submit_caps[key]), "", f"delete {key} value comparison",
            ) for key in keys],
            TOOLS_TEST,
            submit_test,
            "compensating integer vector reaches the scheduler only after the registered cap comparisons are deleted",
            parameter=parameter,
        ))

    submit_reader_open = (
        'if ! RESERVATION_OUTPUT=$(python3 -I -B - "$RESERVATION_POLICY" <<\'PY\'\n'
    )
    submit_reader_close = (
        'PY\n'
        '); then\n'
        '  exit 2\n'
        'fi\n'
        'readarray -t RESERVATION_VALUES <<<"$RESERVATION_OUTPUT"\n'
        'unset RESERVATION_OUTPUT\n'
    )
    specs.append(_single_node_spec(
        "M-S5",
        SUBMIT,
        (
            replacement(
                submit_reader_open,
                'readarray -t RESERVATION_VALUES < <(python3 -I -B - "$RESERVATION_POLICY" <<\'PY\'\n',
                "restore process substitution",
            ),
            replacement(submit_reader_close, "PY\n)\n", "remove explicit producer status check"),
        ),
        TOOLS_TEST,
        "test_submit_reservation_reader_rejects_python_failure_after_complete_output",
        "a complete-output producer returning rc=73 is ignored and scheduler reachability changes",
        timeout_is_semantic_evidence=True,
    ))

    submit_wall_old = (
        'if (p["t126_qualification_walltime"] != "10:00:00"\n'
        '        or p["t126_qualification_member_cap_s"] != 900\n'
    )
    submit_wall_new = 'if (p["t126_qualification_member_cap_s"] != 900\n'
    specs.append(_single_node_spec(
        "U-S-WALL-NUL",
        SUBMIT,
        (replacement(submit_wall_old, submit_wall_new, "delete Python walltime value comparison"),),
        TOOLS_TEST,
        "test_submit_rejects_nul_in_walltime_before_scheduler_calls",
        "the NUL-bearing walltime reaches the scheduler when the Python value comparison is absent",
    ))

    submit_type_cases = (
        ("MEMBER", "member_cap_s", "member-cap"),
        ("GAP", "round_gap_s", "round-gap"),
        ("PROLOGUE", "prologue_cap_s", "prologue-cap"),
        ("ATTESTATION", "attestation_cap_s", "attestation-cap"),
        ("FINALIZE", "finalize_reserve_s", "finalize-reserve"),
    )
    for short, key, parameter in submit_type_cases:
        specs.append(_single_node_spec(
            f"U-S-TYPE-{short}",
            SUBMIT,
            (_submit_type_replacement(key),),
            TOOLS_TEST,
            "test_submit_rejects_each_single_layer_equal_float_type_drift",
            f"equal-float {key} reaches the scheduler after its sole strict-int scan is removed",
            parameter=parameter,
        ))

    submit_mapping_replacements = {
        "walltime_s": SUBMIT_MAPPING.replace(' && "$WALLTIME_S" == 36000', ""),
        "wmax_s": SUBMIT_MAPPING.replace(' && "$WMAX_S" == 29100', ""),
    }
    for short, key, parameter in (
        ("WALLTIME_S", "walltime_s", "walltime-s"),
        ("WMAX", "wmax_s", "wmax"),
    ):
        specs.append(_single_node_spec(
            f"U-S-TYPE-{short}",
            SUBMIT,
            (
                _submit_type_replacement(key),
                replacement(
                    SUBMIT_MAPPING,
                    submit_mapping_replacements[key],
                    f"delete Bash mapping guard for {key}",
                ),
            ),
            TOOLS_TEST,
            "test_submit_rejects_each_mapping_masked_equal_float_type_drift",
            f"equal-float {key} reaches the scheduler only after Python type and Bash mapping guards are both removed",
            parameter=parameter,
        ))

    job_value_test = "test_job_reservation_policy_accepts_exact_point_and_rejects_each_frozen_value"
    job_value_cases = (
        ("M-J1", "walltime", '"10:00:00"', "walltime"),
        ("M-J2", "member_cap_s", "900", "member-cap"),
        ("M-J3", "round_gap_s", "1800", "round-gap"),
        ("M-J4", "attestation_cap_s", "600", "attestation-cap"),
        ("M-J5", "finalize_reserve_s", "600", "finalize-reserve"),
    )
    for mutation_id, key, value, parameter in job_value_cases:
        specs.append(_single_node_spec(
            mutation_id,
            JOB,
            (replacement(
                _job_expected_line(key, value), "", f"delete expected comparison for {key}",
            ),),
            TOOLS_TEST,
            job_value_test,
            f"single drift of {key} reaches the downstream dependency marker",
            parameter=parameter,
        ))

    job_mapping_replacements = {
        "walltime_s": (
            '[[ "$WMAX_S" == 29100 \\\n'
            '  && "$PROLOGUE_CAP_S" == 900 ]] || exit 2\n'
        ),
        "wmax_s": (
            '[[ "$WALLTIME_S" == 36000 \\\n'
            '  && "$PROLOGUE_CAP_S" == 900 ]] || exit 2\n'
        ),
        "prologue_cap_s": (
            '[[ "$WALLTIME_S" == 36000 && "$WMAX_S" == 29100 ]] || exit 2\n'
        ),
    }
    for mutation_id, key, value, parameter in (
        ("M-J6", "walltime_s", "36000", "walltime-s"),
        ("M-J7", "wmax_s", "29100", "wmax"),
        ("M-J8", "prologue_cap_s", "900", "prologue-cap"),
    ):
        specs.append(_single_node_spec(
            mutation_id,
            JOB,
            (
                replacement(
                    _job_expected_line(key, value), "", f"delete expected comparison for {key}",
                ),
                replacement(
                    JOB_MAPPING,
                    job_mapping_replacements[key],
                    f"delete Bash mapping guard for {key}",
                ),
            ),
            TOOLS_TEST,
            job_value_test,
            f"single drift of {key} reaches the downstream marker only after both value and mapping guards are removed",
            parameter=parameter,
        ))

    job_assignment = (
        'WALLTIME_S=${RESERVATION_VALUES[0]}\n'
        'WMAX_S=${RESERVATION_VALUES[1]}\n'
        'PROLOGUE_CAP_S=${RESERVATION_VALUES[2]}\n'
    )
    job_assignment_swapped = (
        'WALLTIME_S=${RESERVATION_VALUES[1]}\n'
        'WMAX_S=${RESERVATION_VALUES[0]}\n'
        'PROLOGUE_CAP_S=${RESERVATION_VALUES[2]}\n'
    )
    specs.append(_single_node_spec(
        "M-J9",
        JOB,
        (replacement(job_assignment, job_assignment_swapped, "swap reservation array indexes 0 and 1"),),
        TOOLS_TEST,
        job_value_test,
        "canonical policy is rejected by the Bash mapping assertion after the array index swap",
        parameter="canonical",
    ))

    job_reader_open = (
        'if ! RESERVATION_OUTPUT=$("$PY" -I -S -B - "$RESERVATION_POLICY" <<\'PY\'\n'
    )
    job_reader_close = (
        'PY\n'
        '); then\n'
        '  exit 2\n'
        'fi\n'
        'readarray -t RESERVATION_VALUES <<<"$RESERVATION_OUTPUT"\n'
        'unset RESERVATION_OUTPUT\n'
    )
    specs.append(_single_node_spec(
        "M-J10",
        JOB,
        (
            replacement(
                job_reader_open,
                'readarray -t RESERVATION_VALUES < <("$PY" -I -S -B - "$RESERVATION_POLICY" <<\'PY\'\n',
                "restore process substitution",
            ),
            replacement(job_reader_close, "PY\n)\n", "remove explicit producer status check"),
        ),
        TOOLS_TEST,
        "test_job_reservation_reader_rejects_python_failure_after_complete_output",
        "a complete three-line producer returning rc=73 is ignored and the downstream dependency marker is reached",
        timeout_is_semantic_evidence=True,
    ))

    for short, key, parameter in (
        ("MEMBER", "member_cap_s", "member-cap"),
        ("GAP", "round_gap_s", "round-gap"),
        ("ATTESTATION", "attestation_cap_s", "attestation-cap"),
        ("FINALIZE", "finalize_reserve_s", "finalize-reserve"),
    ):
        specs.append(_single_node_spec(
            f"U-J-TYPE-{short}",
            JOB,
            (replacement(
                _job_numeric_line(key), "", f"strict-int scan excludes {key}",
            ),),
            TOOLS_TEST,
            "test_job_rejects_each_single_layer_equal_float_type_drift",
            f"equal-float {key} reaches the downstream marker after its sole strict-int scan is removed",
            parameter=parameter,
        ))

    for short, key, parameter in (
        ("WALLTIME_S", "walltime_s", "walltime-s"),
        ("WMAX", "wmax_s", "wmax"),
        ("PROLOGUE", "prologue_cap_s", "prologue-cap"),
    ):
        specs.append(_single_node_spec(
            f"U-J-TYPE-{short}",
            JOB,
            (
                replacement(
                    _job_numeric_line(key), "", f"strict-int scan excludes {key}",
                ),
                replacement(
                    JOB_MAPPING,
                    job_mapping_replacements[key],
                    f"delete Bash mapping guard for {key}",
                ),
            ),
            TOOLS_TEST,
            "test_job_rejects_each_mapping_masked_equal_float_type_drift",
            f"equal-float {key} reaches the downstream marker only after Python type and Bash mapping guards are both removed",
            parameter=parameter,
        ))

    contract_test = "test_protocol_rejects_each_compensating_timing_cap_drift"
    contract_values = {
        "prologue_cap_s": 900,
        "attestation_cap_s": 600,
        "finalize_reserve_s": 600,
    }
    for mutation_id, keys, parameter in (
        ("M-C1", ("attestation_cap_s", "finalize_reserve_s"), "900-1199-1"),
        ("M-C2", ("prologue_cap_s", "attestation_cap_s"), "1499-1-600"),
        ("M-C3", ("prologue_cap_s", "finalize_reserve_s"), "1499-600-1"),
        (
            "M-C4",
            ("prologue_cap_s", "attestation_cap_s", "finalize_reserve_s"),
            "900-1199-1",
        ),
    ):
        specs.append(_single_node_spec(
            mutation_id,
            CONTRACT,
            tuple(replacement(
                f'            or timing["{key}"] != {contract_values[key]}\n',
                "",
                f"delete {key} value comparison",
            ) for key in keys),
            CONTRACT_TEST,
            contract_test,
            "the positive compensating timing vector is accepted only after the registered comparisons are deleted",
            parameter=parameter,
        ))

    specs.append(_single_node_spec(
        "U-FIXTURE-COPYMODE",
        TOOLS_TEST,
        (replacement(
            "                shutil.copymode(source, path)\n",
            "                pass  # U-FIXTURE-COPYMODE\n",
            "make copymode a no-op",
        ),),
        TOOLS_TEST,
        job_value_test,
        "the generated job source loses executable mode and the fixture's destination-mode assertion fails",
        parameter="canonical",
    ))

    return tuple(specs)


SPECS = build_specs()


def normalize_node(value: str) -> str:
    value = ANSI_RE.sub("", value).strip()
    if value.startswith("FAILED "):
        value = value[len("FAILED "):]
    if " - " in value:
        value = value.split(" - ", 1)[0]
    value = value.replace("\\", "/")
    repo_prefix = REPO.as_posix().rstrip("/") + "/"
    if value.startswith(repo_prefix):
        value = value[len(repo_prefix):]
    while value.startswith("./"):
        value = value[2:]
    return value.strip()


def _validate_specs() -> None:
    if len(SPECS) != 35:
        raise HarnessAbort(f"mutation spec count is {len(SPECS)}, expected 35")
    ids = [spec.mutation_id for spec in SPECS]
    if len(ids) != len(set(ids)):
        raise HarnessAbort("mutation IDs are not unique")
    for spec in SPECS:
        path = REPO / spec.target_file
        if not path.is_file():
            raise HarnessAbort(f"target file is missing: {spec.target_file}")
        if not spec.replacements:
            raise HarnessAbort(f"no replacements registered: {spec.mutation_id}")
        expected = tuple(normalize_node(node) for node in spec.expected_kill_nodes)
        if not expected or any(not node for node in expected):
            raise HarnessAbort(f"expected kill node is empty: {spec.mutation_id}")


def _git(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", *args], cwd=REPO, text=True, capture_output=True, timeout=30,
    )


def _assert_target_commit() -> None:
    result = _git("rev-parse", "HEAD")
    if result.returncode != 0:
        raise HarnessAbort(f"cannot resolve HEAD: {result.stderr.strip()}")
    if result.stdout.strip() != TARGET_COMMIT:
        raise HarnessAbort(
            f"HEAD is {result.stdout.strip()}, expected integration commit {TARGET_COMMIT}"
        )


def _assert_clean_except_harness() -> None:
    result = _git("status", "--porcelain=v1", "--untracked-files=all")
    if result.returncode != 0:
        raise HarnessAbort(f"cannot inspect worktree: {result.stderr.strip()}")
    unexpected: list[str] = []
    for line in result.stdout.splitlines():
        path_field = line[3:]
        if " -> " in path_field:
            path_field = path_field.split(" -> ", 1)[1]
        if path_field == ".mutation-harness-t247" or path_field.startswith(
            ".mutation-harness-t247/"
        ):
            continue
        unexpected.append(line)
    if unexpected:
        raise HarnessAbort(
            "worktree is not clean outside the harness directory:\n" + "\n".join(unexpected)
        )


def _acquire_lock() -> object:
    lock_path = HARNESS_DIR / "harness.lock"
    handle = lock_path.open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise HarnessAbort(f"another T-247 mutation harness holds {lock_path}") from exc
    handle.seek(0)
    handle.truncate()
    handle.write(f"pid={os.getpid()}\n")
    handle.flush()
    os.fsync(handle.fileno())
    return handle


def _apply_replacements(spec: MutationSpec, original: str) -> tuple[str, str]:
    current = original
    for index, item in enumerate(spec.replacements, 1):
        count = current.count(item.old)
        if count != 1:
            raise HarnessAbort(
                f"{spec.mutation_id} replacement {index} ({item.label}) matched {count} locations; expected exactly 1"
            )
        current = current.replace(item.old, item.new, 1)
        if current == original and index == len(spec.replacements):
            raise HarnessAbort(f"{spec.mutation_id} produced no content change")
    diff = "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        current.splitlines(keepends=True),
        fromfile=f"a/{spec.target_file}",
        tofile=f"b/{spec.target_file} ({spec.mutation_id})",
    ))
    if not diff:
        raise HarnessAbort(f"{spec.mutation_id} has no injected diff")
    return current, diff


def _restore(path: Path, original: str) -> None:
    path.write_text(original, encoding="utf-8")
    restored = path.read_text(encoding="utf-8")
    if restored != original:
        raise HarnessAbort(f"restoration content mismatch: {path.relative_to(REPO)}")


def _terminate_after_timeout(process: subprocess.Popen[str], grace_s: float = 30.0) -> str:
    process.terminate()
    try:
        output, _ = process.communicate(timeout=grace_s)
        return output
    except subprocess.TimeoutExpired:
        process.kill()
        output, _ = process.communicate()
        return output


def _run_pytest(
    spec: MutationSpec,
    timeout_s: float,
) -> tuple[int | None, bool, str, float]:
    command = [
        sys.executable,
        "tools/run_tests.py",
        spec.pytest_target,
        "-k",
        spec.k_expr,
        "-rf",
        "--color=no",
        "-n",
        "1",
    ]
    started = time.monotonic()
    process = subprocess.Popen(
        command,
        cwd=REPO,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        start_new_session=False,
    )
    try:
        output, _ = process.communicate(timeout=timeout_s)
        return process.returncode, False, output, time.monotonic() - started
    except subprocess.TimeoutExpired as exc:
        partial = exc.output or ""
        if isinstance(partial, bytes):
            partial = partial.decode("utf-8", "replace")
        tail = _terminate_after_timeout(process)
        if tail.startswith(partial):
            output = tail
        else:
            output = partial + tail
        return None, True, output, time.monotonic() - started
    except BaseException:
        # A parent-side signal must not leave run_tests.py (or its queued PBS
        # request) alive while the source restoration below proceeds.
        _terminate_after_timeout(process)
        raise


def _pytest_output_lines(output: str) -> tuple[list[str], dict[str, object]]:
    source_lines = output.splitlines()
    child_lines: list[str] = []
    inside_child_stdout = False
    child_stdout_regions = 0
    completed_regions = 0
    saw_begin = False
    saw_end = False
    for line in source_lines:
        boundary_line = ANSI_RE.sub("", line)
        if DISPATCH_CHILD_STDOUT_BEGIN_RE.fullmatch(boundary_line):
            saw_begin = True
            inside_child_stdout = True
            child_stdout_regions += 1
            continue
        if DISPATCH_CHILD_STDOUT_END_RE.fullmatch(boundary_line):
            saw_end = True
            if inside_child_stdout:
                completed_regions += 1
                inside_child_stdout = False
            continue
        if inside_child_stdout:
            child_lines.append(line)

    selected_lines = child_lines if saw_begin else source_lines
    clean_lines = [
        ANSI_RE.sub("", line[2:] if line.startswith("| ") else line)
        for line in selected_lines
    ]
    metadata: dict[str, object] = {
        "mode": "dispatch_child_stdout" if saw_begin else "direct",
        "child_stdout_regions": child_stdout_regions,
        "child_stdout_completed_regions": completed_regions,
        "child_stdout_boundaries_complete": bool(
            not saw_begin or (saw_end and completed_regions == child_stdout_regions)
        ),
    }
    return clean_lines, metadata


def _failed_nodes(clean_lines: Sequence[str]) -> tuple[list[str], list[str]]:
    raw: list[str] = []
    for line in clean_lines:
        match = FAILED_RE.fullmatch(line)
        if match:
            raw.append(match.group("node").strip())
    normalized: list[str] = []
    for node in raw:
        value = normalize_node(node)
        if value and value not in normalized:
            normalized.append(value)
    return raw, normalized


def _pytest_summaries(
    clean_lines: Sequence[str],
) -> tuple[list[dict[str, object]], dict[str, int]]:
    records: list[dict[str, object]] = []
    totals: dict[str, int] = {}
    canonical_labels = {
        "error": "errors",
        "warning": "warnings",
        "rerun": "reruns",
    }
    for line in clean_lines:
        stripped = line.strip()
        if not stripped.startswith("="):
            continue
        counts: dict[str, int] = {}
        for match in PYTEST_SUMMARY_COUNT_RE.finditer(stripped):
            label = canonical_labels.get(match.group("label"), match.group("label"))
            counts[label] = counts.get(label, 0) + int(match.group("count"))
        if not counts:
            continue
        records.append({"line": stripped, "counts": counts})
        for label, count in counts.items():
            totals[label] = totals.get(label, 0) + count
    return records, totals


def _parse_health(
    returncode: int | None,
    observed_nodes: Sequence[str],
    summary_failed_count: int | None,
) -> tuple[bool | None, list[str]]:
    failed_count_matches_summary = (
        len(observed_nodes) == summary_failed_count
        if summary_failed_count is not None
        else None
    )
    reasons: list[str] = []
    if returncode is not None and returncode != 0 and not observed_nodes:
        reasons.append("nonzero returncode but no FAILED test nodes parsed")
    if failed_count_matches_summary is False:
        reasons.append(
            f"pytest summary reports {summary_failed_count} failed but "
            f"{len(observed_nodes)} unique FAILED test nodes were parsed"
        )
    return failed_count_matches_summary, reasons


def _append_ledger(path: Path, record: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def run_mutation(
    spec: MutationSpec,
    *,
    ledger: Path,
    timeout_s: float,
    run_id: str,
) -> dict[str, object]:
    path = REPO / spec.target_file
    original = path.read_text(encoding="utf-8")
    mutated, injected_diff = _apply_replacements(spec, original)
    expected = [normalize_node(node) for node in spec.expected_kill_nodes]
    started_at = _utc_now()
    result: dict[str, object] | None = None
    restored = False
    try:
        if path.read_text(encoding="utf-8") != original:
            raise HarnessAbort(f"source drift before injection: {spec.target_file}")
        path.write_text(mutated, encoding="utf-8")
        if path.read_text(encoding="utf-8") != mutated:
            raise HarnessAbort(f"injected content mismatch: {spec.target_file}")
        rc, timed_out, output, duration_s = _run_pytest(spec, timeout_s)
        clean_lines, pytest_output = _pytest_output_lines(output)
        full_clean_output = ANSI_RE.sub("", output)
        raw_nodes, observed = _failed_nodes(clean_lines)
        summary_records, summary_counts = _pytest_summaries(clean_lines)
        summary_failed_count = (
            summary_counts.get("failed", 0) if summary_records else None
        )
        failed_count_matches_summary, parse_failure_reasons = _parse_health(
            rc, observed, summary_failed_count,
        )
        parse_failure = bool(parse_failure_reasons)
        matches = sorted(set(expected) & set(observed))
        compute_running = bool(re.search(
            r"\[Pegasus dispatch\] request \S+ の状態: RUN", full_clean_output,
        ))
        timeout_evidence = bool(
            timed_out and compute_running and spec.timeout_is_semantic_evidence
        )
        semantic_kill = not parse_failure and (bool(matches) or timeout_evidence)
        diagnostic_only = bool(
            not parse_failure
            and not semantic_kill
            and rc not in (None, 0, 5, 16)
            and observed
        )
        if parse_failure:
            outcome = "PARSE_FAILURE"
        elif semantic_kill:
            outcome = "KILLED"
        elif diagnostic_only:
            outcome = "DIAGNOSTIC_ONLY"
        elif timed_out:
            outcome = "TIMEOUT_INCONCLUSIVE"
        elif rc == 0:
            outcome = "SURVIVED"
        elif rc in (5, 16) or not observed:
            outcome = "INFRA_OR_HARNESS_ERROR"
        else:
            outcome = "UNEXPECTED_FAILURE"
        log_path = ledger.parent / "logs" / f"{run_id}-{spec.mutation_id}.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(output, encoding="utf-8")
        result = {
            "schema_version": "t247-mutation-ledger/v1",
            "run_id": run_id,
            "mutation_id": spec.mutation_id,
            "target_commit": TARGET_COMMIT,
            "target_file": spec.target_file,
            "started_at": started_at,
            "finished_at": _utc_now(),
            "duration_s": round(duration_s, 3),
            "pytest_target": spec.pytest_target,
            "pytest_k": spec.k_expr,
            "pytest_args": [spec.pytest_target, "-k", spec.k_expr, "-rf", "--color=no", "-n", "1"],
            "timeout_s": timeout_s,
            "timed_out": timed_out,
            "compute_running_before_timeout": compute_running,
            "fail_open_timeout_evidence": timeout_evidence,
            "returncode": rc,
            "pytest_output": pytest_output,
            "failed_nodes_raw": raw_nodes,
            "failed_nodes": observed,
            "failed_node_count": len(observed),
            "pytest_summary_records": summary_records,
            "pytest_summary_counts": summary_counts,
            "pytest_summary_failed_count": summary_failed_count,
            "failed_node_count_matches_summary": failed_count_matches_summary,
            "parse_failure": parse_failure,
            "parse_failure_reasons": parse_failure_reasons,
            "expected_kill_nodes": expected,
            "matched_kill_nodes": matches,
            "semantic_basis": spec.semantic_basis,
            "semantic_kill": semantic_kill,
            "diagnostic_only": diagnostic_only,
            "outcome": outcome,
            "injection_sha256": hashlib.sha256(mutated.encode("utf-8")).hexdigest(),
            "injected_diff": injected_diff,
            "log_path": str(log_path),
        }
    finally:
        _restore(path, original)
        restored = path.read_text(encoding="utf-8") == original
        if not restored:
            raise HarnessAbort(f"restoration verification failed: {spec.target_file}")
    if result is None:
        raise HarnessAbort(f"mutation produced no result: {spec.mutation_id}")
    result["restored"] = restored
    result["restore_content_equal"] = restored
    _append_ledger(ledger, result)
    return result


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--all", action="store_true", help="run all 35 mutations")
    selection.add_argument(
        "--mutant", action="append", default=[], metavar="ID",
        help="run one mutation; repeat for at most the desired trial subset",
    )
    parser.add_argument(
        "--ledger", type=Path, default=DEFAULT_LEDGER,
        help=f"JSONL ledger path (default: {DEFAULT_LEDGER})",
    )
    parser.add_argument(
        "--timeout", type=float, default=DEFAULT_TIMEOUT_S,
        help=f"per-dispatch timeout in seconds (default: {DEFAULT_TIMEOUT_S:g})",
    )
    parser.add_argument("--list", action="store_true", help="list specs without mutation")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    _validate_specs()
    if args.list:
        for spec in SPECS:
            print(json.dumps({
                "mutation_id": spec.mutation_id,
                "target_file": spec.target_file,
                "pytest_target": spec.pytest_target,
                "pytest_k": spec.k_expr,
                "expected_kill_nodes": [normalize_node(node) for node in spec.expected_kill_nodes],
            }, ensure_ascii=False, sort_keys=True))
        return 0
    if args.timeout <= 0:
        raise HarnessAbort("--timeout must be positive")
    if not args.all and not args.mutant:
        raise HarnessAbort("select --all or at least one --mutant ID")
    by_id = {spec.mutation_id: spec for spec in SPECS}
    unknown = [mutation_id for mutation_id in args.mutant if mutation_id not in by_id]
    if unknown:
        raise HarnessAbort("unknown mutation IDs: " + ", ".join(unknown))
    selected = list(SPECS) if args.all else [by_id[item] for item in args.mutant]
    if len({spec.mutation_id for spec in selected}) != len(selected):
        raise HarnessAbort("duplicate --mutant ID")

    lock = _acquire_lock()
    original_handlers: dict[int, object] = {}

    def abort_on_signal(signum: int, _frame: object) -> None:
        raise KeyboardInterrupt(f"signal {signum}")

    try:
        for signum in (signal.SIGINT, signal.SIGTERM):
            original_handlers[signum] = signal.signal(signum, abort_on_signal)
        _assert_target_commit()
        _assert_clean_except_harness()
        run_id = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
        killed = 0
        for index, spec in enumerate(selected, 1):
            _assert_target_commit()
            _assert_clean_except_harness()
            print(f"[{index}/{len(selected)}] {spec.mutation_id}: dispatch", flush=True)
            result = run_mutation(
                spec,
                ledger=args.ledger.resolve(),
                timeout_s=args.timeout,
                run_id=run_id,
            )
            killed += int(bool(result["semantic_kill"]))
            print(
                f"[{index}/{len(selected)}] {spec.mutation_id}: {result['outcome']} "
                f"nodes={result['failed_nodes']} "
                f"summary_failed={result['pytest_summary_failed_count']} "
                f"restored={result['restore_content_equal']}"
                + (
                    f" parse_failure={result['parse_failure_reasons']}"
                    if result["parse_failure"]
                    else ""
                ),
                flush=True,
            )
        print(
            f"run_id={run_id} semantic_kill={killed}/{len(selected)} ledger={args.ledger.resolve()}",
            flush=True,
        )
        return 0 if killed == len(selected) else 1
    finally:
        for signum, handler in original_handlers.items():
            signal.signal(signum, handler)
        fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
        lock.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except HarnessAbort as exc:
        print(f"ABORT: {exc}", file=sys.stderr)
        raise SystemExit(2)
