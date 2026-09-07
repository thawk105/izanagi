import json
import re
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PEGASUS = REPO / "tools/pegasus"
SUBMITTER = PEGASUS / "submit_t1998_balanced_stock_inline.sh"
JOB = PEGASUS / "a5_second_boot_backoff_sweep.sh"
REGISTRY = PEGASUS / "admission_registry.json"


def _normalized(source: str) -> str:
    source = re.sub(r"\\\n\s*", " ", source)
    return re.sub(r"[ \t]+", " ", source)


def test_submitter_launches_exactly_one_balanced_workload():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    normalized = _normalized(submitter)
    assert re.findall(r"(?m)^WORKLOAD=([^\s#]+)$", submitter) == ["balanced"]
    assert "WORKLOADS=" not in submitter
    assert "for workload" not in submitter
    assert normalized.count("job_id=$(qsub ") == 1
    assert 'A5_WORKLOAD=$WORKLOAD' in submitter
    assert '"workloads": [workload]' in submitter


def test_submitter_reuses_the_existing_a5_job_body_and_adds_no_job_body():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    assert 'JOB_SCRIPT="$SCRIPT_DIR/a5_second_boot_backoff_sweep.sh"' in submitter
    assert 'JOB_SCRIPT_PATH="tools/pegasus/a5_second_boot_backoff_sweep.sh"' in submitter
    assert JOB.is_file()
    assert "#PBS" not in submitter
    t1998_job_bodies = []
    for path in PEGASUS.glob("*t1998*"):
        if path.is_file() and "#PBS" in path.read_text(encoding="utf-8"):
            t1998_job_bodies.append(path.name)
    assert t1998_job_bodies == []


def test_qsub_passes_all_five_a5_job_body_bindings():
    normalized = _normalized(SUBMITTER.read_text(encoding="utf-8"))
    binding = (
        '-v "A5_WORKLOAD=$WORKLOAD,A5_OUTPUT_ROOT=$root,'
        'A5_SUBMISSION_NONCE=$SUBMISSION_NONCE,'
        'A5_EXPECTED_HEAD=$EXPECTED_HEAD,'
        'JOB_SCRIPT_SHA256=$JOB_SCRIPT_SHA256"'
    )
    assert normalized.count(binding) == 1
    assert '-o "$stdout" -e "$stderr" "$JOB_SCRIPT"' in normalized
    assert normalized.index('cd -- "$REPO_ROOT"') < normalized.index("job_id=$(qsub")


def test_output_parent_is_existing_absolute_and_outside_every_repo_ancestor():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    for fragment in (
        '"$OUTPUT_PARENT" == /*',
        '-d "$OUTPUT_PARENT"',
        '! -L "$OUTPUT_PARENT"',
        'target == repo or repo in target.parents or target in repo.parents',
        'any((parent / ".git").exists() for parent in (target, *target.parents))',
    ):
        assert fragment in submitter


def test_preflight_and_atomic_receipt_match_the_a5_submission_strength():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    normalized = _normalized(submitter)
    for command in (
        "git", "qstat", "qsub", "pegasusinfo", "check_quota", "sha256sum",
        "python3.10",
    ):
        assert command in re.search(
            r"for command_name in (?P<commands>.*?); do", submitter
        ).group("commands").split()
    for fragment in (
        "python3.10 -I -B -c",
        "check_quota >/dev/null",
        "QUEUE_STATE=$(qstat -Q)",
        '"gen_S" in text',
        're.search(r"(?i)\\b(ENA|ENABLE(?:D)?)\\b", text)',
        're.search(r"(?i)\\b(ACT|ACTIVE)\\b", text)',
        "PEGASUS_INFO=$(pegasusinfo)",
        '[[ ! -e "$root" && ! -e "$stdout" && ! -e "$stderr" ]]',
        "os.O_WRONLY | os.O_CREAT | os.O_EXCL",
        "os.O_WRONLY | os.O_APPEND",
        'getattr(os, "O_NOFOLLOW", 0)',
        "stat.S_ISREG(info.st_mode)",
        "info.st_nlink != 1",
        "os.fsync(fd)",
        "os.fsync(parent_fd)",
    ):
        assert fragment in submitter
    assert normalized.index("check_quota >/dev/null") < normalized.index("job_id=$(qsub")
    assert 'GROUP_ID="t1998-balanced-stock-inline-' in submitter
    assert '"submitter_path": submitter_path' in submitter
    assert '"submitter_sha256": submitter_hash' in submitter
    assert '"job_script_sha256": job_script_hash' in submitter
    assert '"repository_commit": expected_head' in submitter


def test_submitter_is_registered_as_local_ok():
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/submit_t1998_balanced_stock_inline.sh"] == {
        "class": "local-ok",
        "reason": "login-side PBS T-1998 balanced-only submitter",
        "primary_gate": "qsub submission; compute work stays in existing A-5 job body",
        "evidence": "static login-side submitter classification",
    }


def _run() -> int:
    tests = [
        value for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
            passed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
