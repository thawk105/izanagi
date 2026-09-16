#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pegasus 計算ノード上で committed perf candidates を実コード測定する。"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import platform
import re
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence


SCHEMA_VERSION = "t293-perf-site-probe/v1"
OK_SEMANTICS = (
    "ok は期待 HEAD・policy・probe・PBS・submission の binding が一致し、"
    "必須 field が完備し、全測定層を試行して完了でき、正の control が解決し"
    "負の control が未解決だったことを表す。候補未解決や smoke 不合格は"
    "正当な否定結果であり、それ自体では ok を false にしない。"
)
CONTROL_CANDIDATES = ["/nonexistent/izanagi-t293-control/perf"]
CONTROL_NOTE = (
    "同じ計算ノードの同じ run で、実在する sys.executable を解決し、起動時に"
    "不存在を確認した候補を解決しない二側 control により resolver の感度を確認する。"
)
PER_CANDIDATE_LIMITATION = (
    "模擬測定は production が行う canonical path の SHA-256 と inode/size/mtime の"
    "安定性検査を再現しない。"
)
TOOL_CANDIDATES = {
    "python": ["python3", "python3.10", "python3.11"],
    "cc": ["gcc-13"],
    "cxx": ["g++-13"],
    "cmake": ["cmake"],
}
MEASUREMENT_LAYERS = (
    "environment_observation",
    "policy_candidates",
    "real_executable_resolution",
    "individual_executable_resolutions",
    "real_prepare_toolchain",
    "simulated_smoke",
    "control_resolution",
)
REQUIRED_FIELDS = (
    "schema_version",
    "ok",
    "ok_semantics",
    "site.hostname",
    "site.uname_release",
    "site.PBS_JOBID",
    "site.observed_epoch",
    "site.cwd",
    "sample_scope",
    "control_note",
    "control_sensitivity",
    "required_fields",
    "required_fields_complete",
    "positive_control_preflight.path",
    "positive_control_preflight.exists",
    "positive_control_preflight.is_file",
    "positive_control_preflight.is_symlink",
    "positive_control_preflight.executable",
    "positive_control_preflight.is_absolute",
    "negative_control_preflight.path",
    "negative_control_preflight.exists",
    "binding.attempted",
    "binding.matched",
    "binding.expected_head",
    "binding.head",
    "binding.expected_policy_sha256",
    "binding.policy_sha256",
    "binding.expected_probe_sha256",
    "binding.probe_sha256",
    "binding.expected_pbs_sha256",
    "binding.pbs_sha256",
    "binding.expected_submission_sha256",
    "binding.submission_sha256",
    "policy_file.path",
    "policy_file.sha256",
    "measurement_layers.environment_observation.attempted",
    "measurement_layers.policy_candidates.attempted",
    "measurement_layers.real_executable_resolution.attempted",
    "measurement_layers.individual_executable_resolutions.attempted",
    "measurement_layers.real_prepare_toolchain.attempted",
    "measurement_layers.simulated_smoke.attempted",
    "measurement_layers.control_resolution.attempted",
    "environment_observation.attempted",
    "policy_candidates",
    "real_executable_resolution.attempted",
    "real_executable_resolution.resolved",
    "individual_executable_resolutions.attempted",
    "individual_executable_resolutions.results",
    "real_prepare_toolchain.attempted",
    "real_prepare_toolchain.ok",
    "real_prepare_toolchain.failure_stage",
    "simulated_smoke.attempted",
    "positive_control_resolution.attempted",
    "positive_control_resolution.resolved",
    "control_resolution.attempted",
    "control_resolution.resolved",
    "consistency.inconsistent",
    "consistency.reasons",
    "measurement_errors",
)
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_HEAD_RE = re.compile(r"^[0-9a-fA-F]{40}$")


def _error(exc: BaseException) -> dict[str, str]:
    return {"type": type(exc).__name__, "message": str(exc)}


def _path_record(path: Path) -> dict[str, Any]:
    return {
        "path": str(path),
        "exists": path.exists(),
        "is_file": path.is_file(),
        "is_symlink": path.is_symlink(),
        "executable": os.access(path, os.X_OK),
    }


def _linux_tools_inventory() -> list[dict[str, Any]]:
    paths: set[str] = set()
    for pattern in (
        "/usr/lib/linux-tools/*/perf",
        "/usr/lib/linux-tools-*/perf",
    ):
        paths.update(glob.glob(pattern))
    return [_path_record(Path(path)) for path in sorted(paths)]


def _parse_policy(policy_bytes: bytes) -> Mapping[str, Any]:
    policy = json.loads(policy_bytes.decode("utf-8"))
    if not isinstance(policy, Mapping):
        raise TypeError("policy root must be a JSON object")
    candidates = policy.get("perf_candidates")
    if not isinstance(candidates, list) or not all(
        isinstance(candidate, str) for candidate in candidates
    ):
        raise TypeError("policy perf_candidates must be a list of strings")
    return policy


def _load_submission(repo_root: Path) -> Any:
    # tools/pegasus/run_probe.py と同じく repo 内 orchestrator を import root にする。
    orchestrator = repo_root / "orchestrator"
    if str(orchestrator) not in sys.path:
        sys.path.insert(0, str(orchestrator))
    from qualification import submission

    return submission


def _read_perf_event_paranoid() -> dict[str, Any]:
    path = Path("/proc/sys/kernel/perf_event_paranoid")
    try:
        return {"path": str(path), "value": path.read_text(encoding="utf-8").strip()}
    except Exception as exc:
        return {"path": str(path), "error": _error(exc)}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def _git_head(repo_root: Path) -> str:
    completed = subprocess.run(
        ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        timeout=10,
    )
    head = completed.stdout.strip()
    if not _HEAD_RE.fullmatch(head):
        raise ValueError(f"git HEAD is not a 40-hex object name: {head!r}")
    return head.lower()


def _binding(
    repo_root: Path,
    expect_policy_sha256: str,
    expect_head: str,
    expect_probe_sha256: str,
    expect_pbs_sha256: str,
    expect_submission_sha256: str,
) -> tuple[dict[str, Any], bytes]:
    policy_path = repo_root / "tools/pegasus/policy.json"
    probe_path = Path(__file__).resolve(strict=True)
    pbs_path = repo_root / "tools/pegasus/probes/t293_perf_site_probe.pbs"
    submission_path = repo_root / "orchestrator/qualification/submission.py"
    policy_bytes = policy_path.read_bytes()
    policy_sha256 = hashlib.sha256(policy_bytes).hexdigest()
    probe_sha256 = _sha256(probe_path)
    pbs_sha256 = _sha256(pbs_path)
    submission_sha256 = _sha256(submission_path)
    head = _git_head(repo_root)
    record = {
        "attempted": True,
        "matched": (
            policy_sha256 == expect_policy_sha256.lower()
            and head == expect_head.lower()
            and probe_sha256 == expect_probe_sha256.lower()
            and pbs_sha256 == expect_pbs_sha256.lower()
            and submission_sha256 == expect_submission_sha256.lower()
        ),
        "expected_head": expect_head.lower(),
        "head": head,
        "expected_policy_sha256": expect_policy_sha256.lower(),
        "policy_sha256": policy_sha256,
        "expected_probe_sha256": expect_probe_sha256.lower(),
        "probe_sha256": probe_sha256,
        "expected_pbs_sha256": expect_pbs_sha256.lower(),
        "pbs_sha256": pbs_sha256,
        "expected_submission_sha256": expect_submission_sha256.lower(),
        "submission_sha256": submission_sha256,
    }
    return record, policy_bytes


def _sample_scope(hostname: str, observed_epoch: int, policy_sha256: str) -> str:
    return (
        f"この結果は hostname={hostname} + observed_epoch={observed_epoch} + "
        f"policy sha256={policy_sha256} の1標本であり、gen_S の全 bnode や将来の "
        "allocation へ一般化しない。"
    )


def _base_payload() -> dict[str, Any]:
    hostname = socket.gethostname()
    observed_epoch = int(time.time())
    positive_control_path = Path(sys.executable)
    negative_control_path = Path(CONTROL_CANDIDATES[0])
    return {
        "schema_version": SCHEMA_VERSION,
        "ok": False,
        "ok_semantics": OK_SEMANTICS,
        "site": {
            "hostname": hostname,
            "uname_release": platform.uname().release,
            "PBS_JOBID": os.environ.get("PBS_JOBID"),
            "observed_epoch": observed_epoch,
            "cwd": os.getcwd(),
        },
        "sample_scope": _sample_scope(hostname, observed_epoch, "未取得"),
        "control_note": CONTROL_NOTE,
        "control_sensitivity": "not-established",
        "required_fields": list(REQUIRED_FIELDS),
        "required_fields_complete": False,
        "positive_control_preflight": {
            **_path_record(positive_control_path),
            "is_absolute": positive_control_path.is_absolute(),
        },
        "negative_control_preflight": _path_record(negative_control_path),
        "measurement_layers": {
            name: {"attempted": False} for name in MEASUREMENT_LAYERS
        },
        "binding": {
            "attempted": False,
            "matched": False,
            "expected_head": None,
            "head": None,
            "expected_policy_sha256": None,
            "policy_sha256": None,
            "expected_probe_sha256": None,
            "probe_sha256": None,
            "expected_pbs_sha256": None,
            "pbs_sha256": None,
            "expected_submission_sha256": None,
            "submission_sha256": None,
        },
        "policy_file": {"path": None, "sha256": None},
        "environment_observation": {"attempted": False},
        "policy_candidates": [],
        "real_executable_resolution": {
            "attempted": False,
            "resolved": False,
        },
        "individual_executable_resolutions": {
            "attempted": False,
            "results": {},
        },
        "real_prepare_toolchain": {
            "attempted": False,
            "ok": False,
            "failure_stage": None,
        },
        "simulated_smoke": {"attempted": False},
        "positive_control_resolution": {
            "attempted": False,
            "resolved": False,
        },
        "control_resolution": {"attempted": False, "resolved": False},
        "consistency": {"inconsistent": False, "reasons": []},
        "measurement_errors": [],
    }


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _run_record(argv: Sequence[str], *, timeout: int = 10) -> dict[str, Any]:
    record: dict[str, Any] = {
        "attempted": True,
        "executed": True,
        "argv": list(argv),
        "rc": None,
        "stdout": "",
        "stderr": "",
    }
    try:
        completed = subprocess.run(
            list(argv),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        record.update(
            {
                "rc": completed.returncode,
                "stdout": completed.stdout,
                "stderr": completed.stderr,
            }
        )
    except subprocess.TimeoutExpired as exc:
        record.update(
            {
                "timed_out": True,
                "stdout": _text(exc.stdout),
                "stderr": _text(exc.stderr),
                "error": _error(exc),
            }
        )
    except OSError as exc:
        # 起動不能は候補の正当な否定結果であり、probe 自体の内部故障ではない。
        record["error"] = _error(exc)
    return record


def _version_accepted(record: Mapping[str, Any]) -> bool:
    output = record.get("stdout") or record.get("stderr") or ""
    lines = str(output).splitlines()
    return record.get("rc") == 0 and bool(lines and lines[0])


def _smoke_accepted(record: Mapping[str, Any]) -> bool:
    text = f"{record.get('stdout', '')}\n{record.get('stderr', '')}".lower()
    return (
        record.get("rc") == 0
        and "<not supported>" not in text
        and "<not counted>" not in text
    )


def _measure_candidate(candidate: str) -> dict[str, Any]:
    path = Path(candidate)
    record = {
        "attempted": True,
        **_path_record(path),
        "note": "simulated: argv replicated from prepare_toolchain",
        "limitation": PER_CANDIDATE_LIMITATION,
    }
    if not record["executable"]:
        record.update(
            {
                "version": {
                    "attempted": True,
                    "executed": False,
                    "skipped": True,
                    "reason": "candidate is not executable",
                },
                "smoke": {
                    "attempted": True,
                    "executed": False,
                    "skipped": True,
                    "reason": "candidate is not executable",
                    "note": "simulated: argv replicated from prepare_toolchain",
                },
                "functional": False,
            }
        )
        return record

    version = _run_record([candidate, "--version"], timeout=20)
    smoke = _run_record(
        [
            candidate,
            "stat",
            "-x,",
            "-e",
            "LLC-load-misses,LLC-loads,instructions,cycles",
            "--",
            "true",
        ]
    )
    smoke["note"] = "simulated: argv replicated from prepare_toolchain"
    record.update(
        {
            "version": version,
            "smoke": smoke,
            "functional": (
                bool(record["exists"])
                and bool(record["is_file"])
                and not bool(record["is_symlink"])
                and _version_accepted(version)
                and _smoke_accepted(smoke)
            ),
        }
    )
    return record


def _real_resolution(
    submission: Any,
    name: str,
    candidates: Sequence[str],
    *,
    note: Optional[str] = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "attempted": True,
        "name": name,
        "candidates": list(candidates),
    }
    if note is not None:
        record["note"] = note
    try:
        result = submission._executable(name, candidates)
        record.update({"resolved": True, **result})
    except submission.SubmissionPreparationError as exc:
        # 候補未解決や version 失敗は production resolver の正当な否定結果。
        record.update({"resolved": False, "error": _error(exc)})
    except Exception as exc:
        record.update(
            {
                "attempted": False,
                "resolved": False,
                "error": _error(exc),
            }
        )
    return record


def _prepare_failure_stage(resolver_results: Mapping[str, Mapping[str, Any]]) -> str:
    for name in ("python", "cc", "cxx", "cmake", "perf"):
        if not resolver_results[name].get("resolved", False):
            return name
    return "dependencies-or-smoke"


def _resolved_candidate_record(
    candidate_records: Sequence[Mapping[str, Any]], resolved_path: str
) -> Optional[Mapping[str, Any]]:
    selected = Path(resolved_path)
    for record in candidate_records:
        candidate = record.get("path")
        if not isinstance(candidate, str):
            continue
        try:
            if Path(candidate).resolve(strict=True) == selected:
                return record
        except (OSError, RuntimeError):
            continue
    return None


def _consistency_record(
    candidate_records: Sequence[Mapping[str, Any]],
    real_perf: Mapping[str, Any],
    prepare: Mapping[str, Any],
) -> dict[str, Any]:
    reasons: list[str] = []
    functional = [
        str(record.get("path"))
        for record in candidate_records
        if record.get("functional") is True
    ]
    selected_record: Optional[Mapping[str, Any]] = None
    if real_perf.get("attempted") and real_perf.get("resolved"):
        selected_record = _resolved_candidate_record(
            candidate_records, str(real_perf["path"])
        )
        if selected_record is None:
            reasons.append(
                "real_executable_resolution の解決先に対応する per-candidate record がない"
            )
        elif selected_record.get("functional") is not True:
            reasons.append(
                "real_executable_resolution は解決したが対応候補の functional が false"
            )
    elif real_perf.get("attempted") and functional:
        reasons.append(
            "functional な候補があるが real_executable_resolution は未解決"
        )

    if prepare.get("attempted") and prepare.get("ok"):
        if selected_record is None or selected_record.get("functional") is not True:
            reasons.append(
                "real_prepare_toolchain は成功したが対応する functional な候補がない"
            )
    elif (
        prepare.get("attempted")
        and prepare.get("failure_stage") == "perf"
        and functional
    ):
        reasons.append(
            "functional な候補があるが real_prepare_toolchain は perf 解決段で失敗"
        )

    return {
        "inconsistent": bool(reasons),
        "reasons": reasons,
        "functional_candidates": functional,
        "real_resolution_resolved": real_perf.get("resolved"),
        "real_prepare_ok": prepare.get("ok"),
        "real_prepare_failure_stage": prepare.get("failure_stage"),
    }


def _mark_unattempted(payload: dict[str, Any], reason: str) -> None:
    payload.update(
        {
            "environment_observation": {"attempted": False, "reason": reason},
            "policy_candidates": [],
            "real_executable_resolution": {
                "attempted": False,
                "resolved": False,
                "reason": reason,
            },
            "individual_executable_resolutions": {
                "attempted": False,
                "results": {},
                "reason": reason,
            },
            "real_prepare_toolchain": {
                "attempted": False,
                "ok": False,
                "failure_stage": None,
                "reason": reason,
            },
            "simulated_smoke": {"attempted": False, "reason": reason},
            "positive_control_resolution": {
                "attempted": False,
                "resolved": False,
                "reason": reason,
            },
            "control_resolution": {
                "attempted": False,
                "resolved": False,
                "reason": reason,
            },
        }
    )


def probe(
    repo_root: Path,
    expect_policy_sha256: str,
    expect_head: str,
    expect_probe_sha256: str,
    expect_pbs_sha256: str,
    expect_submission_sha256: str,
) -> tuple[int, dict[str, Any]]:
    """全測定を実行し、process rc と JSON 化可能な結果を返す。"""
    payload = _base_payload()
    try:
        binding, policy_bytes = _binding(
            repo_root,
            expect_policy_sha256,
            expect_head,
            expect_probe_sha256,
            expect_pbs_sha256,
            expect_submission_sha256,
        )
        payload["binding"] = binding
        payload["policy_file"] = {
            "path": str(repo_root / "tools/pegasus/policy.json"),
            "sha256": binding["policy_sha256"],
        }
        payload["sample_scope"] = _sample_scope(
            payload["site"]["hostname"],
            payload["site"]["observed_epoch"],
            binding["policy_sha256"],
        )
    except Exception as exc:
        payload["binding"].update(
            {"attempted": False, "matched": False, "error": _error(exc)}
        )
        _mark_unattempted(payload, "binding could not be completed")
        payload["error"] = {"stage": "binding", **_error(exc)}
        return 2, payload

    if not binding["matched"]:
        _mark_unattempted(payload, "expected binding value mismatch")
        payload["error"] = {
            "stage": "binding",
            "type": "BindingMismatch",
            "message": (
                "expected HEAD, policy, probe, PBS, or submission sha256 mismatch"
            ),
        }
        return 2, payload

    if payload["negative_control_preflight"]["exists"]:
        reason = "negative control candidate existed at probe startup"
        _mark_unattempted(payload, reason)
        payload["measurement_errors"] = [
            {
                "stage": "control_preflight",
                "type": "UnexpectedControlPathExistence",
                "message": reason,
            }
        ]
        payload["error"] = payload["measurement_errors"][0]
        return 3, payload

    try:
        policy = _parse_policy(policy_bytes)
    except Exception as exc:
        _mark_unattempted(payload, "bound policy could not be parsed")
        payload["error"] = {"stage": "policy", **_error(exc)}
        return 2, payload

    measurement_errors: list[dict[str, Any]] = []

    try:
        environment = {
            "attempted": True,
            "linux_tools_inventory": _linux_tools_inventory(),
            "toolchain_which": {
                name: shutil.which(name)
                for name in ("python3", "gcc-13", "g++-13", "cmake")
            },
            "perf_event_paranoid": _read_perf_event_paranoid(),
        }
        payload["environment_observation"] = environment
        payload["linux_tools_inventory"] = environment["linux_tools_inventory"]
        payload["toolchain_which"] = environment["toolchain_which"]
        payload["perf_event_paranoid"] = environment["perf_event_paranoid"]
        payload["measurement_layers"]["environment_observation"]["attempted"] = True
    except Exception as exc:
        payload["environment_observation"] = {
            "attempted": False,
            "error": _error(exc),
        }
        measurement_errors.append(
            {"stage": "environment_observation", **_error(exc)}
        )

    candidate_records: list[dict[str, Any]] = []
    candidates_attempted = True
    for candidate in policy["perf_candidates"]:
        try:
            candidate_records.append(_measure_candidate(candidate))
        except Exception as exc:
            candidates_attempted = False
            candidate_records.append(
                {
                    "attempted": False,
                    "path": candidate,
                    "functional": False,
                    "limitation": PER_CANDIDATE_LIMITATION,
                    "error": _error(exc),
                }
            )
            measurement_errors.append(
                {"stage": "policy_candidates", "candidate": candidate, **_error(exc)}
            )
    payload["policy_candidates"] = candidate_records
    payload["measurement_layers"]["policy_candidates"][
        "attempted"
    ] = candidates_attempted

    try:
        submission = _load_submission(repo_root)
    except Exception as exc:
        import_error = _error(exc)
        reason = "qualification.submission could not be imported"
        payload["real_executable_resolution"] = {
            "attempted": False,
            "resolved": False,
            "reason": reason,
            "error": import_error,
        }
        payload["individual_executable_resolutions"] = {
            "attempted": False,
            "results": {},
            "reason": reason,
            "error": import_error,
        }
        payload["real_prepare_toolchain"] = {
            "attempted": False,
            "ok": False,
            "failure_stage": None,
            "reason": reason,
            "error": import_error,
        }
        payload["simulated_smoke"] = {
            "attempted": False,
            "reason": reason,
        }
        payload["positive_control_resolution"] = {
            "attempted": False,
            "resolved": False,
            "reason": reason,
            "error": import_error,
        }
        payload["control_resolution"] = {
            "attempted": False,
            "resolved": False,
            "reason": reason,
            "error": import_error,
        }
        measurement_errors.append({"stage": "submission_import", **import_error})
        payload["measurement_errors"] = measurement_errors
        return 3, payload

    real_perf = _real_resolution(
        submission, "perf", policy["perf_candidates"]
    )
    payload["real_executable_resolution"] = real_perf
    payload["measurement_layers"]["real_executable_resolution"][
        "attempted"
    ] = real_perf["attempted"]
    if not real_perf["attempted"]:
        measurement_errors.append(
            {"stage": "real_executable_resolution", **real_perf["error"]}
        )

    resolver_results: dict[str, Any] = {}
    for name, candidates in {
        **TOOL_CANDIDATES,
        "perf": list(policy["perf_candidates"]),
    }.items():
        note = (
            "simulated: candidates replicated from prepare_toolchain"
            if name != "perf"
            else None
        )
        result = _real_resolution(
            submission, name, candidates, note=note
        )
        resolver_results[name] = result
        if not result["attempted"]:
            measurement_errors.append(
                {
                    "stage": "individual_executable_resolutions",
                    "name": name,
                    **result["error"],
                }
            )
    individual_attempted = all(
        result["attempted"] for result in resolver_results.values()
    )
    payload["individual_executable_resolutions"] = {
        "attempted": individual_attempted,
        "results": resolver_results,
    }
    payload["measurement_layers"]["individual_executable_resolutions"][
        "attempted"
    ] = individual_attempted

    try:
        toolchain = submission.prepare_toolchain(policy, repo_root=repo_root)
        prepare = {"attempted": True, "ok": True, "result": toolchain}
    except submission.SubmissionPreparationError as exc:
        prepare = {"attempted": True, "ok": False, "error": _error(exc)}
    except Exception as exc:
        prepare = {"attempted": False, "ok": False, "error": _error(exc)}
        measurement_errors.append({"stage": "real_prepare_toolchain", **_error(exc)})
    prepare["failure_stage"] = _prepare_failure_stage(resolver_results)
    payload["real_prepare_toolchain"] = prepare
    payload["measurement_layers"]["real_prepare_toolchain"][
        "attempted"
    ] = prepare["attempted"]

    if not real_perf["attempted"]:
        simulated_smoke = {
            "attempted": False,
            "reason": "real executable resolution did not complete",
        }
    elif not real_perf["resolved"]:
        simulated_smoke = {
            "attempted": True,
            "executed": False,
            "skipped": True,
            "reason": "real executable resolution did not resolve perf",
            "note": "simulated: argv replicated from prepare_toolchain",
        }
    else:
        perf = real_perf["path"]
        simulated_smoke = _run_record(
            [
                perf,
                "stat",
                "-x,",
                "-e",
                "LLC-load-misses,LLC-loads,instructions,cycles",
                "--",
                "true",
            ]
        )
        simulated_smoke["note"] = (
            "simulated: argv replicated from prepare_toolchain"
        )
        simulated_smoke["functional"] = _smoke_accepted(simulated_smoke)
    payload["simulated_smoke"] = simulated_smoke
    payload["measurement_layers"]["simulated_smoke"][
        "attempted"
    ] = simulated_smoke["attempted"]

    payload["consistency"] = _consistency_record(
        candidate_records, real_perf, prepare
    )

    positive_control = _real_resolution(
        submission,
        "python",
        [str(Path(sys.executable).resolve())],
        note="symlink を解決した実体 path を使う。_executable は symlink 候補を拒否するため。",
    )
    negative_control = _real_resolution(submission, "perf", CONTROL_CANDIDATES)
    payload["positive_control_resolution"] = positive_control
    payload["control_resolution"] = negative_control
    payload["measurement_layers"]["control_resolution"][
        "attempted"
    ] = positive_control["attempted"] and negative_control["attempted"]
    positive_preflight = payload["positive_control_preflight"]
    positive_preflight_ok = (
        positive_preflight["is_absolute"]
        and positive_preflight["is_file"]
        and not positive_preflight["is_symlink"]
        and positive_preflight["executable"]
    )
    if not positive_preflight_ok:
        measurement_errors.append(
            {
                "stage": "positive_control_preflight",
                "type": "InvalidPositiveControlCandidate",
                "message": (
                    "sys.executable is not an absolute regular executable file"
                ),
            }
        )
    if not positive_control["attempted"]:
        measurement_errors.append(
            {"stage": "positive_control_resolution", **positive_control["error"]}
        )
    elif not positive_control["resolved"]:
        measurement_errors.append(
            {
                "stage": "positive_control_resolution",
                "type": "PositiveControlNotResolved",
                "message": "existing positive control candidate was not resolved",
            }
        )
    if not negative_control["attempted"]:
        measurement_errors.append(
            {"stage": "control_resolution", **negative_control["error"]}
        )
    elif negative_control["resolved"]:
        measurement_errors.append(
            {
                "stage": "control_resolution",
                "type": "UnexpectedControlResolution",
                "message": "nonexistent negative control candidate unexpectedly resolved",
            }
        )

    controls_ok = (
        positive_preflight_ok
        and not payload["negative_control_preflight"]["exists"]
        and positive_control["attempted"]
        and positive_control["resolved"]
        and negative_control["attempted"]
        and not negative_control["resolved"]
    )
    if controls_ok:
        payload["control_sensitivity"] = "two-sided-ok"

    all_attempted = all(
        layer["attempted"] for layer in payload["measurement_layers"].values()
    )
    payload["measurement_errors"] = measurement_errors
    payload["ok"] = all_attempted and controls_ok
    return (0 if payload["ok"] else 3), payload


def _encode(payload: Mapping[str, Any]) -> str:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    ) + "\n"


def _missing_required_fields(payload: Mapping[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_FIELDS:
        current: Any = payload
        for component in field.split("."):
            if not isinstance(current, Mapping) or component not in current:
                missing.append(field)
                break
            current = current[component]
    return missing


def _write_create_only(path: Path, payload: Mapping[str, Any]) -> None:
    with path.open("x", encoding="utf-8") as handle:
        handle.write(_encode(payload))


def run(
    repo_root: Path,
    output: Path,
    expect_policy_sha256: str,
    expect_head: str,
    expect_probe_sha256: str,
    expect_pbs_sha256: str,
    expect_submission_sha256: str,
) -> tuple[int, dict[str, Any]]:
    try:
        rc, payload = probe(
            repo_root,
            expect_policy_sha256,
            expect_head,
            expect_probe_sha256,
            expect_pbs_sha256,
            expect_submission_sha256,
        )
    except Exception as exc:
        rc = 3
        payload = _base_payload()
        _mark_unattempted(payload, "unexpected measurement failure")
        payload["error"] = {"stage": "measurement", **_error(exc)}

    missing_fields = _missing_required_fields(payload)
    payload["required_fields_complete"] = not missing_fields
    if missing_fields:
        payload["ok"] = False
        payload["error"] = {
            "stage": "schema",
            "type": "MissingRequiredFields",
            "message": "required fields are missing: " + ", ".join(missing_fields),
            "missing_fields": missing_fields,
        }
        rc = 3

    try:
        _write_create_only(output, payload)
    except Exception as exc:
        payload["ok"] = False
        payload["error"] = {"stage": "output", **_error(exc)}
        rc = 4
    return rc, payload


def _expected_sha256(value: str) -> str:
    if not _SHA256_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("must be exactly 64 hexadecimal characters")
    return value.lower()


def _expected_head(value: str) -> str:
    if not _HEAD_RE.fullmatch(value):
        raise argparse.ArgumentTypeError("must be exactly 40 hexadecimal characters")
    return value.lower()


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--expect-policy-sha256", required=True, type=_expected_sha256
    )
    parser.add_argument("--expect-head", required=True, type=_expected_head)
    parser.add_argument(
        "--expect-probe-sha256", required=True, type=_expected_sha256
    )
    parser.add_argument(
        "--expect-pbs-sha256", required=True, type=_expected_sha256
    )
    parser.add_argument(
        "--expect-submission-sha256", required=True, type=_expected_sha256
    )
    args = parser.parse_args(argv)
    rc, payload = run(
        args.repo_root,
        args.output,
        args.expect_policy_sha256,
        args.expect_head,
        args.expect_probe_sha256,
        args.expect_pbs_sha256,
        args.expect_submission_sha256,
    )
    sys.stdout.write(_encode(payload))
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
