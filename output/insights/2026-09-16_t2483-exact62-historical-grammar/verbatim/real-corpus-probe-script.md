# 逐語 — 実 corpus 検証 script (Codex role=author が作成、親が repo 外で実行)

実行形 (`.py`) は repo へ入れない。以下は実行した bytes の逐語である。

```python
#!/usr/bin/env python3
"""Read-only corpus probe. Run outside the repository with --repo-root.

Only the optional, exclusively created JSON report is writable. C is a
measurement, not an acceptance requirement. No layer3_report claim is made.
"""
import argparse
import contextlib
import hashlib
import importlib
import json
import os
from pathlib import Path
import sys


DEFAULTS = {
    "rr5": "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-1af9fc2b",
    "rr50": "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2364-20260907b/jobs/rr50/campaigns/paper-story-a2-rr50-paper-story-a2-certification-rr50-5efd479e",
    "rr95": "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b/jobs/rr95/campaigns/paper-story-a2-rr95-paper-story-a6-certification-rr95-1e7d99f2",
    "exact24": "/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260827/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-df07b695",
}
ARTIFACTS = ("campaign.lock", "runs/wal.jsonl")


def exception_record(exc):
    """Include every explicit cause; cycles are identified without truncation."""
    chain, seen = [], {}
    while exc is not None:
        if id(exc) in seen:
            return {"chain": chain, "cause_cycle_to": seen[id(exc)]}
        seen[id(exc)] = len(chain)
        try:
            message = str(exc)
        except BaseException:
            message = "<exception __str__ failed>"
        chain.append({"type": type(exc).__name__,
                      "module": type(exc).__module__, "message": message})
        exc = exc.__cause__
    return {"chain": chain, "cause_cycle_to": None}


def attempt(operation):
    try:
        # Imported APIs must not contaminate the single stdout JSON document.
        with contextlib.redirect_stdout(sys.stderr):
            value = operation()
        return {"status": "ok", **value}
    except BaseException as exc:
        return {"status": "error", "passed": False,
                "exception": exception_record(exc)}


class Parser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def parse_args():
    parser = Parser(description=__doc__, add_help=False, allow_abbrev=False)
    parser.add_argument("--repo-root", required=True)
    parser.add_argument("--out", help="New JSON file only; must not already exist")
    for name, default in DEFAULTS.items():
        parser.add_argument("--" + name, default=default)
    return parser.parse_args()


def sha256_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"sha256": digest.hexdigest()}


def hashes(root):
    return {name: attempt(lambda name=name: sha256_file(root / name))
            for name in ARTIFACTS}


def decode_probe(root, codec, count):
    decoded = codec.decode_historical_campaign_lock_bytes(
        (root / "campaign.lock").read_bytes())
    paths = decoded.authority.recorded_contract_loader_relative_paths
    expected = (codec.T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS
                if count == 62 else codec.PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS)
    matches = paths == expected
    return {"decode_succeeded": True, "return_type": type(decoded).__name__,
            "expected_grammar": "exact-" + str(count),
            "recorded_contract_loader_relative_paths": list(paths),
            "path_count": len(paths), "matches_expected_tuple": matches,
            "passed": matches and type(paths) is tuple and len(paths) == count}


def epoch_probe(root, admission, count):
    value = admission.require_campaign_verifier_epoch(
        root, purpose=admission.CampaignReadPurpose.HISTORICAL_RAW)
    prefix = "T733_EXACT62" if count == 62 else "PRE_T733"
    scope_matches = (
        value.identity_scope == getattr(admission, prefix + "_CAMPAIGN_VERIFIER_EPOCH_SCOPE")
        and value.excluded_scope == getattr(
            admission, prefix + "_CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE"))
    required = (type(value) is admission.HistoricalCampaignVerifierEpoch
                and value.state == "E1")
    return {"return_type": type(value).__name__, "state": value.state,
            "campaign_verifier_epoch": value.campaign_verifier_epoch,
            "identity_scope": value.identity_scope,
            "excluded_scope": value.excluded_scope,
            "current_verifier_conformance": getattr(value, "current_verifier_conformance", None),
            "scope_matches_expected": scope_matches, "passed": required}


def admission_probe(root, admission):
    value = admission.require_admitted_campaign(
        root, purpose=admission.CampaignReadPurpose.HISTORICAL_RAW)
    return {"call_succeeded": True, "return_type": type(value).__name__,
            "read_purpose": value.read_purpose.value,
            "passed": (type(value) is admission.HistoricalCampaignView
                       and value.read_purpose is admission.CampaignReadPurpose.HISTORICAL_RAW)}


def certified_probe(root, admission):
    # Only exceptions from the actual gate count as observed rejection.
    purpose = admission.CampaignReadPurpose.CERTIFIED_ACCEPTANCE
    gate = admission.require_campaign_verifier_epoch
    try:
        value = gate(root, purpose=purpose)
    except BaseException as exc:
        expected_rejection = isinstance(exc, admission.ArtifactAdmissionError)
        return {"rejected": True, "unexpected_success": False,
                "expected_rejection_type": expected_rejection,
                "passed": expected_rejection, "exception": exception_record(exc)}
    return {"rejected": False, "unexpected_success": True, "passed": False,
            "return_type": type(value).__name__,
            "campaign_verifier_epoch": getattr(value, "campaign_verifier_epoch", None)}


def compare_hashes(before, after):
    matches = {}
    for name in ARTIFACTS:
        old, new = before[name], after[name]
        matches[name] = (old["sha256"] == new["sha256"]
                         if old["status"] == new["status"] == "ok" else None)
    return {"matches": matches, "passed": all(v is True for v in matches.values())}


def run_probe(args, report):
    repo = Path(args.repo_root).resolve(strict=True)
    if not repo.is_dir():
        raise ValueError("--repo-root must be a directory")
    report["repo_root"] = str(repo)
    sys.path.insert(0, str(repo))
    sys.dont_write_bytecode = True
    modules = {}

    def load(name):
        module = importlib.import_module("orchestrator.campaign." + name)
        module_path = Path(module.__file__).resolve()
        if not module_path.is_relative_to(repo):
            raise ValueError("module was imported outside --repo-root: " + str(module_path))
        modules[name] = module
        return {"module_file": str(module_path)}

    for name in ("campaign_lock", "artifact_admission"):
        report["imports"][name] = attempt(lambda name=name: load(name))

    def invoke(name, operation):
        if name not in modules:
            return {"status": "blocked", "passed": False,
                    "reason": "module import failed", "import_key": name}
        return attempt(lambda: operation(modules[name]))

    subjects = []
    for name in DEFAULTS:
        root = Path(getattr(args, name)).absolute()
        row = {"subject": name, "campaign_dir": str(root),
               "expected_path_count": 24 if name == "exact24" else 62}
        subjects.append((root, row))
        if name == "exact24":
            report["negative_control"] = row
        else:
            report["campaigns"].append(row)

    try:
        for root, row in subjects:
            row["hashes_before"] = hashes(root)
        for root, row in subjects:
            count = row["expected_path_count"]
            row["A_decode"] = invoke("campaign_lock", lambda m: decode_probe(root, m, count))
            row["B_epoch"] = invoke("artifact_admission", lambda m: epoch_probe(root, m, count))
            if count == 62:
                row["C_admission"] = invoke("artifact_admission", lambda m: admission_probe(root, m))
        for root, row in subjects:
            if row["expected_path_count"] == 62:
                row["certified_rejection"] = invoke(
                    "artifact_admission", lambda m: certified_probe(root, m))
    finally:
        for root, row in subjects:
            row["hashes_after"] = hashes(root)
            row["bytes_unchanged"] = compare_hashes(
                row.get("hashes_before", {n: {"status": "missing"} for n in ARTIFACTS}),
                row["hashes_after"])
    report["completed"] = True
    report["required_checks_passed"] = all(
        row.get(key, {}).get("passed") is True
        for _, row in subjects
        for key in (("A_decode", "B_epoch", "bytes_unchanged", "certified_rejection")
                    if row["expected_path_count"] == 62
                    else ("A_decode", "B_epoch", "bytes_unchanged")))


def json_text(report):
    return json.dumps(report, ensure_ascii=True, indent=2, allow_nan=False) + "\n"


def write_report(path, args, report):
    """Exclusive output creation: never overwrite any existing inode or artifact."""
    target = Path(path).resolve()
    roots = [Path(value).resolve() for value in DEFAULTS.values()]
    roots.extend(Path(getattr(args, name)).resolve() for name in DEFAULTS)
    if (target.name in {"campaign.lock", "wal.jsonl"}
            or any(target == root or target.is_relative_to(root) for root in roots)):
        raise ValueError("--out must be outside all campaign directories and not an artifact name")
    # This is the sole write destination, reserved exclusively for a NEW report.
    # O_EXCL also rejects symlinks/hardlinks to existing lock or WAL files.
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        report["output"] = {"status": "ok", "path": str(target)}
        data = memoryview(json_text(report).encode("utf-8"))
        while data:
            written = os.write(fd, data)
            if written <= 0:
                raise OSError("JSON report write made no progress")
            data = data[written:]
    finally:
        os.close(fd)


def main():
    report = {"schema_version": "t2483-real-corpus-probe/v1", "repo_root": None,
              "imports": {}, "campaigns": [], "negative_control": None,
              "completed": False, "required_checks_passed": False,
              "errors": [], "output": {"status": "not_requested"}}
    args = None
    try:
        args = parse_args()
        with contextlib.redirect_stdout(sys.stderr):
            run_probe(args, report)
    except BaseException as exc:
        report["errors"].append(exception_record(exc))
    if args is not None and args.out:
        try:
            write_report(args.out, args, report)
        except BaseException as exc:
            report["output"] = {"status": "error", "path": args.out,
                                "exception": exception_record(exc)}
    try:
        sys.stdout.write(json_text(report))
        sys.stdout.flush()
    except BaseException as exc:
        # A closed stdout cannot carry JSON; still avoid a nonzero shutdown.
        try:
            sys.stderr.write(json_text({"stdout_error": exception_record(exc),
                                       "report": report}))
        except BaseException:
            pass
        sys.stdout = None
    return 0


if __name__ == "__main__":
    sys.exit(main())
```
