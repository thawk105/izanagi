#!/usr/bin/env python3
"""凍結した T-471 の 5 arm だけを計算ノードで測る使い捨て driver。"""

from __future__ import annotations

import datetime as dt
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
from pathlib import Path, PurePosixPath
from types import ModuleType
from typing import Any
SCHEMA = "izanagi-t471-restore-observed/v1"
TRIALS_PER_ARM = 100
ARM_ORDER = ("A-e0", "A-e143-fresh", "A-e143-aged", "A-b240-n1", "A-p2-synth")
ARM_LAYOUTS = {
    "A-e0": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [0], "cache_temperature_label": "absent", "synthetic": False},
    "A-e143-fresh": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [143], "cache_temperature_label": "fresh-hot", "synthetic": False},
    "A-e143-aged": {"case": "C2", "n": 2, "P": 1, "E_by_parent": [143], "cache_temperature_label": "aged-from-attempt-start", "synthetic": False},
    "A-b240-n1": {"case": "C1", "n": 1, "P": 1, "E_by_parent": [143], "cache_temperature_label": "fresh-hot", "synthetic": False},
    "A-p2-synth": {"case": "C2", "n": 2, "P": 2, "E_by_parent": [143, 97], "cache_temperature_label": "fresh-hot", "synthetic": True},
}
CASES = {
    "C2": ("output/insights/2026-08-04_t244-p5-injection-gate/mutation-spec-v2.json", "MX4-MX6-both-layers", ("orchestrator/campaign/autonomous_trial_completeness.py", "orchestrator/campaign/claude_projected_provider.py")),
    "C1": ("output/insights/2026-08-04_t399-t400-signal-mitigation/mutation-spec.json", "G1", ("output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py",)),
}
class MeasurementError(RuntimeError): pass
def _utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()

def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()
def _run(argv: list[str]) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)


def _value(argv: list[str], label: str) -> str:
    result = _run(argv)
    value = result.stdout.decode(errors="replace").strip()
    if result.returncode or not value:
        raise MeasurementError(f"{label} unavailable: rc={result.returncode}")
    return value
def _regular(repo: Path, rel: str) -> Path:
    pure = PurePosixPath(rel)
    if pure.is_absolute() or pure.as_posix() != rel or any(x in {"", ".", ".."} for x in pure.parts):
        raise MeasurementError(f"unsafe path: {rel!r}")
    path = repo / rel
    cursor = path
    while cursor != repo:
        if cursor.is_symlink():
            raise MeasurementError(f"symlink rejected: {rel}")
        cursor = cursor.parent
    if not path.is_file():
        raise MeasurementError(f"not a regular file: {rel}")
    return path.resolve(strict=True)
def _reject_symlink_chain(path: Path) -> None:
    while path != path.parent:
        if path.is_symlink():
            raise MeasurementError(f"symlink path rejected: {path}")
        path = path.parent
def _head_bytes(repo: Path, rel: str) -> tuple[Path, bytes]:
    path = _regular(repo, rel)
    result = _run(["git", "-C", str(repo), "show", f"HEAD:{rel}"])
    if result.returncode or path.read_bytes() != result.stdout:
        raise MeasurementError(f"working bytes differ from HEAD: {rel}")
    return path, result.stdout
def _load_source(path: Path, raw: bytes, name: str) -> ModuleType:
    module = ModuleType(name)
    module.__file__ = str(path)
    sys.modules[name] = module
    exec(compile(raw, str(path), "exec"), module.__dict__)
    return module
def _case(repo: Path, case_id: str) -> dict[str, Any]:
    spec_rel, mutation_id, target_rels = CASES[case_id]
    spec_path, spec_raw = _head_bytes(repo, spec_rel)
    document = json.loads(spec_raw)
    matches = [m for m in document.get("mutations", []) if m.get("id") == mutation_id]
    if len(matches) != 1:
        raise MeasurementError(f"literal mutation is not unique: {case_id}")
    originals: dict[str, str] = {}
    for rel in target_rels:
        _, raw = _head_bytes(repo, rel)
        originals[rel] = raw.decode("utf-8")
    mutated = dict(originals)
    for replacement in matches[0].get("replacements", []):
        rel, old, new = replacement.get("file"), replacement.get("old"), replacement.get("new")
        if rel not in mutated or not isinstance(old, str) or not isinstance(new, str) or mutated[rel].count(old) != 1:
            raise MeasurementError(f"literal replacement is inapplicable: {case_id}")
        mutated[rel] = mutated[rel].replace(old, new, 1)
    if set(mutated) != set(target_rels) or any(mutated[x] == originals[x] for x in target_rels):
        raise MeasurementError(f"literal case did not mutate every target: {case_id}")
    return {"id": case_id, "spec_path": str(spec_path), "spec_sha256": _sha(spec_raw), "mutation_id": mutation_id, "target_rels": target_rels, "target_head_sha256": {rel: _sha(text.encode()) for rel, text in originals.items()}, "originals": originals, "mutated": mutated}
def _profile(case: dict[str, Any], arm: str) -> dict[str, Any]:
    layout = ARM_LAYOUTS[arm]
    originals, mutated = case["originals"], case["mutated"]
    return {"n": layout["n"], "B_original_total": sum(len(x.encode()) for x in originals.values()), "B_mutated_total": sum(len(x.encode()) for x in mutated.values()), "target_existence_states": ["regular-file"] * layout["n"], "P": layout["P"], "E_by_parent": list(layout["E_by_parent"]), "E_total": sum(layout["E_by_parent"]), "cache_temperature_label": layout["cache_temperature_label"]}
def _prepare(scratch: Path, arm: str, index: int, case: dict[str, Any], phase: str, replica: bool = False) -> dict[str, Any]:
    root = scratch / (f"layout-{arm}" if replica else f"{index:03d}-{arm}")
    root.mkdir(mode=0o700)
    parents = [root / f"parent-{i}" for i in range(ARM_LAYOUTS[arm]["P"])]
    for parent in parents:
        parent.mkdir(mode=0o700)
    rels, originals = [], {}
    for number, source_rel in enumerate(case["target_rels"]):
        parent = 0 if len(parents) == 1 else number
        rel = f"parent-{parent}/target-{number}.py"
        (root / rel).write_text(case["mutated"][source_rel], encoding="utf-8")
        rels.append(rel)
        originals[rel] = case["originals"][source_rel]
    for parent, count in zip(parents, ARM_LAYOUTS[arm]["E_by_parent"], strict=True):
        if count:
            cache = parent / "__pycache__"
            cache.mkdir(mode=0o700)
            for number in range(count):
                (cache / f"entry-{number:03d}.pyc").write_bytes(b"t471")
    stamp = _utc()
    return {"root": root, "parents": parents, "rels": tuple(rels), "originals": originals, "entries": tuple(ARM_LAYOUTS[arm]["E_by_parent"]), "created_phase": phase, "cache_created_at_utc": stamp, "last_intentional_cache_access_at_utc": stamp}


def _observed(prepared: dict[str, Any], case: dict[str, Any]) -> dict[str, Any]:
    phase = prepared["created_phase"]
    temperature = "aged-from-attempt-start" if phase == "attempt-start" else ("absent" if sum(prepared["entries"]) == 0 else "fresh-hot")
    return {"n": len(prepared["rels"]), "B_original_total": sum(len(x.encode()) for x in prepared["originals"].values()), "B_mutated_total": sum(len(x.encode()) for x in case["mutated"].values()), "target_existence_states": ["regular-file" if (prepared["root"] / rel).is_file() and not (prepared["root"] / rel).is_symlink() else "other" for rel in prepared["rels"]], "P": len(prepared["parents"]), "E_by_parent": list(prepared["entries"]), "E_total": sum(prepared["entries"]), "cache_temperature_label": temperature}


def _lfs(path: Path) -> dict[str, Any]:
    result = _run(["lfs", "getstripe", str(path)])
    return {"path": str(path), "available": result.returncode == 0 and bool(result.stdout.strip()), "returncode": result.returncode, "stdout": result.stdout.decode(errors="replace"), "stderr": result.stderr.decode(errors="replace")}


def _layout(prepared: dict[str, Any]) -> dict[str, Any]:
    return {"root": _lfs(prepared["root"]), "targets": [_lfs(prepared["root"] / rel) for rel in prepared["rels"]], "parents": [{"entry_count": sum(1 for _ in parent.iterdir()), "lfs_getstripe": _lfs(parent)} for parent in prepared["parents"]]}


def _measure_restore_call(harness: ModuleType, prepared: dict[str, Any]) -> tuple[int | None, int | None, BaseException | None]:
    started = time.perf_counter_ns()
    try:
        harness._restore_targets(prepared["root"], prepared["originals"])
    except BaseException as exc:
        return None, time.perf_counter_ns() - started, exc
    return time.perf_counter_ns() - started, None, None


def _trial(sequence: int, arm: str, index: int, prepared: dict[str, Any] | tuple[Exception, int] | None, scratch: Path, case: dict[str, Any], harness: ModuleType, analysis: ModuleType) -> dict[str, Any]:
    trial_started = time.perf_counter_ns()
    record = {"sequence": sequence, "arm": arm, "arm_trial_index": index, "success": False, "restore_call_count": 0, "elapsed_ns": None, "elapsed_until_error_ns": None, "exception_type": None, "exception_message": None, "precheck": None, "postcheck": None}
    if isinstance(prepared, tuple):
        exc, record["elapsed_until_error_ns"] = prepared
        record["exception_type"], record["exception_message"] = type(exc).__name__, str(exc)
        return record
    try:
        if prepared is None:
            prepared = _prepare(scratch, arm, index, case, "trial-start")
        record.update({"cache_created_at_utc": prepared["cache_created_at_utc"], "last_intentional_cache_access_at_utc": prepared["last_intentional_cache_access_at_utc"]})
        observed = _observed(prepared, case)
        check = analysis.validate_arm_profile(_profile(case, arm), observed)
        expected = {_rel: _sha(case["mutated"][src].encode()) for _rel, src in zip(prepared["rels"], case["target_rels"], strict=True)}
        actual = {rel: _sha((prepared["root"] / rel).read_bytes()) for rel in prepared["rels"]}
        if check["valid"] is not True or actual != expected:
            raise MeasurementError(f"precheck failed: {check['reasons']}")
        record["precheck"] = {"observed_profile": observed, "target_hashes": actual}
        record["restore_call_count"] = 1
        elapsed, error_elapsed, error = _measure_restore_call(harness, prepared)
        record["elapsed_ns"], record["elapsed_until_error_ns"] = elapsed, error_elapsed
        if error is not None:
            raise error
        restored = {rel: _sha((prepared["root"] / rel).read_bytes()) for rel in prepared["rels"]}
        expected = {rel: _sha(text.encode()) for rel, text in prepared["originals"].items()}
        if restored != expected or any((parent / "__pycache__").exists() for parent in prepared["parents"]):
            raise MeasurementError("postcheck failed")
        record["postcheck"] = {"target_hashes": restored, "cache_absent_by_parent": [True] * len(prepared["parents"])}
        record["success"] = True
    except BaseException as exc:
        record["elapsed_until_error_ns"] = time.perf_counter_ns() - trial_started
        record["exception_type"], record["exception_message"] = type(exc).__name__, str(exc)
    if isinstance(prepared, dict):
        try:
            shutil.rmtree(prepared["root"])
        except BaseException as exc:
            record["success"] = False
            record["elapsed_until_error_ns"] = time.perf_counter_ns() - trial_started
            record["exception_type"], record["exception_message"] = type(exc).__name__, f"scratch cleanup failed: {exc}"
    return record


def _environment(repo: Path, scratch: Path, started: str) -> dict[str, Any]:
    host, job = socket.gethostname().split(".", 1)[0], os.environ.get("PBS_JOBID")
    if re.fullmatch(r"bnode[0-9]+", host) is None or not job:
        raise MeasurementError("compute hostname/PBS_JOBID missing")
    fs_type = _value(["stat", "-f", "-c", "%T", str(scratch)], "filesystem type")
    if fs_type.lower() != "lustre":
        raise MeasurementError("scratch is not Lustre")
    clock = time.get_clock_info("perf_counter")
    return {"hostname": host, "PBS_JOBID": job, "filesystem": {"type": fs_type, "mount_source": _value(["findmnt", "-n", "-o", "SOURCE", "-T", str(scratch)], "mount source")}, "kernel": platform.release(), "python_version": sys.version, "repo_commit": _value(["git", "-C", str(repo), "rev-parse", "HEAD"], "repo commit"), "perf_counter": {"implementation": clock.implementation, "monotonic": clock.monotonic, "adjustable": clock.adjustable, "resolution": clock.resolution}, "started_at_utc": started}


def _layout_complete(layout: dict[str, Any]) -> bool:
    pending = [layout]
    found = 0
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            if "available" in value:
                found += 1
                if value.get("available") is not True or not str(value.get("stdout", "")).strip():
                    return False
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
    return found > 0


def _attempt(repo: Path, scratch: Path, evidence: dict[str, Any]) -> None:
    harness_path, harness_raw = _head_bytes(repo, "tools/mutation_harness.py")
    harness_hash = _sha(harness_raw)
    harness = _load_source(harness_path, harness_raw, "t471_real_mutation_harness")
    analysis_path = Path(__file__).with_name("restore_bound_analysis.py")
    analysis = _load_source(analysis_path, analysis_path.read_bytes(), "t471_restore_analysis")
    cases = {case_id: _case(repo, case_id) for case_id in CASES}
    aged: list[dict[str, Any] | tuple[Exception, int]] = []
    for index in range(TRIALS_PER_ARM):
        setup_started = time.perf_counter_ns()
        try:
            aged.append(_prepare(scratch, "A-e143-aged", index, cases["C2"], "attempt-start"))
        except Exception as exc:
            aged.append((exc, time.perf_counter_ns() - setup_started))
    evidence["identity"] = {"harness_path": str(harness_path), "harness_sha256_before": harness_hash}
    evidence["spec_manifest"] = [{"path": case["spec_path"], "sha256": case["spec_sha256"]} for case in cases.values()]
    evidence["measurement_cases"] = [{key: value for key, value in case.items() if key not in {"originals", "mutated"}} for case in cases.values()]
    profiles = {arm: {"trials_required": TRIALS_PER_ARM, "synthetic_profile": ARM_LAYOUTS[arm]["synthetic"], **_profile(cases[ARM_LAYOUTS[arm]["case"]], arm)} for arm in ARM_ORDER}
    evidence["arm_profiles"] = profiles
    evidence["environment"] = _environment(repo, scratch, evidence["started_at_utc"])
    for arm in ARM_ORDER:
        replica = _prepare(scratch, arm, 0, cases[ARM_LAYOUTS[arm]["case"]], "layout-replica", True)
        evidence["layout"]["replica_by_arm"][arm] = _layout(replica)
        shutil.rmtree(replica["root"])
    evidence["layout"]["scratch_root"] = _lfs(scratch)
    evidence["layout"]["real_targets"] = [{"relative_path": rel, "parent_directory_entry_count": sum(1 for _ in _regular(repo, rel).parent.iterdir()), "lfs_getstripe": _lfs(_regular(repo, rel))} for case in cases.values() for rel in case["target_rels"]]
    for index in range(TRIALS_PER_ARM):
        for arm in ARM_ORDER:
            case = cases[ARM_LAYOUTS[arm]["case"]]
            prepared = aged[index] if arm == "A-e143-aged" else None
            evidence["trials"].append(_trial(len(evidence["trials"]), arm, index, prepared, scratch, case, harness, analysis))
    reasons = list(analysis.attempt_validity(evidence["trials"])["reasons"])
    if len(evidence["trials"]) != len(ARM_ORDER) * TRIALS_PER_ARM:
        reasons.append("trial count mismatch")
    if any(sum(t["arm"] == arm for t in evidence["trials"]) != TRIALS_PER_ARM for arm in ARM_ORDER):
        reasons.append("per-arm trial count mismatch")
    if not _layout_complete(evidence["layout"]):
        reasons.append("required lfs layout tag missing")
    _, harness_after = _head_bytes(repo, "tools/mutation_harness.py")
    evidence["identity"]["harness_sha256_after"] = _sha(harness_after)
    if _sha(harness_after) != harness_hash:
        reasons.append("harness changed during attempt")
    evidence["validity"] = {"valid": not reasons, "reasons": reasons}
    if not reasons:
        evidence["R_restore_observed_by_arm"] = {arm: {f"R_restore_observed_{key}": value for key, value in analysis.summarize_elapsed_ns([t["elapsed_ns"] for t in evidence["trials"] if t["arm"] == arm]).items()} for arm in ARM_ORDER}


def main() -> int:
    started = _utc()
    evidence: dict[str, Any] = {"schema": SCHEMA, "validity": {"valid": False, "reasons": []}, "environment": {}, "identity": {}, "spec_manifest": [], "measurement_cases": [], "arm_profiles": {}, "layout": {"replica_by_arm": {}}, "trials": [], "R_restore_observed_by_arm": None, "started_at_utc": started, "ended_at_utc": None}
    output = Path(os.environ["T471_EVIDENCE_JSON"])
    try:
        repo_raw, scratch_raw = Path(os.environ["T471_REPO_ROOT"]), Path(os.environ["T471_SCRATCH_ROOT"])
        _reject_symlink_chain(repo_raw)
        _reject_symlink_chain(scratch_raw)
        repo, scratch = repo_raw.resolve(strict=True), scratch_raw.resolve(strict=True)
        if not repo.is_dir() or not scratch.is_dir() or any(scratch.iterdir()):
            raise MeasurementError("repo/scratch contract failed")
        _attempt(repo, scratch, evidence)
    except BaseException as exc:
        evidence["validity"] = {"valid": False, "reasons": [*evidence["validity"].get("reasons", []), f"fatal {type(exc).__name__}: {exc}"]}
        evidence["R_restore_observed_by_arm"] = None
    evidence["ended_at_utc"] = _utc()
    if evidence["environment"]:
        evidence["environment"]["ended_at_utc"] = evidence["ended_at_utc"]
    if output.exists() or output.is_symlink():
        print("evidence path already exists", file=sys.stderr)
        return 2
    output.write_text(json.dumps(evidence, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if evidence["validity"]["valid"] is True else 2


if __name__ == "__main__":
    raise SystemExit(main())
