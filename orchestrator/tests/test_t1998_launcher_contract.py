import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


REPO = Path(__file__).resolve().parents[2]
PEGASUS = REPO / "tools/pegasus"
SUBMITTER = PEGASUS / "submit_t1998_balanced_stock_inline.sh"
JOB = PEGASUS / "a5_second_boot_backoff_sweep.sh"
REGISTRY = PEGASUS / "admission_registry.json"


def _normalized(source: str) -> str:
    source = re.sub(r"\\\n\s*", " ", source)
    return re.sub(r"[ \t]+", " ", source)


def _python_heredoc_after(source: str, marker: str) -> str:
    marker_offset = source.index(marker)
    match = re.search(
        r"<<'PY'\n(?P<body>.*?)\nPY(?:\n|$)",
        source[marker_offset:],
        flags=re.DOTALL,
    )
    if match is None:
        raise AssertionError(f"missing Python heredoc after {marker!r}")
    return match.group("body")


def _run_python_heredoc(
    program: str, *args: Path | str,
) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-I", "-B", "-", *(str(arg) for arg in args)],
        input=program,
        text=True,
        capture_output=True,
        check=False,
    )


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
    """The executed path-relationship layer alone rejects in-repo output parents."""
    submitter = SUBMITTER.read_text(encoding="utf-8")
    for fragment in (
        '"$OUTPUT_PARENT" == /*',
        '-d "$OUTPUT_PARENT"',
        '! -L "$OUTPUT_PARENT"',
        'target == repo or repo in target.parents or target in repo.parents',
        'any((parent / ".git").exists() for parent in (target, *target.parents))',
    ):
        assert fragment in submitter

    program = _python_heredoc_after(submitter, '"$REPO_ROOT" "$OUTPUT_PARENT"')
    repo = Path("/usr")
    inside = repo / "bin"
    outside = Path("/etc")
    assert not any(
        (parent / ".git").exists() for parent in (inside, *inside.parents)
    )
    assert not any(
        (parent / ".git").exists() for parent in (outside, *outside.parents)
    )
    rejected_inside = _run_python_heredoc(program, repo, inside)
    accepted_outside = _run_python_heredoc(program, repo, outside)

    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_path = Path(raw_tmp)
        repository_ancestor = tmp_path / "other-repo"
        ancestor_output = repository_ancestor / "output"
        ancestor_output.mkdir(parents=True)
        (repository_ancestor / ".git").mkdir()
        rejected_ancestor = _run_python_heredoc(program, repo, ancestor_output)

    assert rejected_inside.returncode != 0
    assert "output parent must be outside the repository" in rejected_inside.stderr
    assert accepted_outside.returncode == 0, accepted_outside.stderr
    assert rejected_ancestor.returncode != 0
    assert "output parent has a repository ancestor" in rejected_ancestor.stderr


def test_preflight_and_atomic_receipt_match_the_a5_submission_strength():
    """The executed receipt-file layer alone rejects a multiply linked receipt."""
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

    program = _python_heredoc_after(submitter, "append_submission_event() {")
    with tempfile.TemporaryDirectory() as raw_tmp:
        tmp_path = Path(raw_tmp)
        regular_receipt = tmp_path / "regular.jsonl"
        linked_source = tmp_path / "linked-source.jsonl"
        linked_receipt = tmp_path / "linked-receipt.jsonl"
        regular_receipt.write_text("{}\n", encoding="utf-8")
        linked_source.write_text("{}\n", encoding="utf-8")
        linked_receipt.hardlink_to(linked_source)
        event_args = (
            "submitted", "balanced", "fixture.1",
            tmp_path / "root", tmp_path / "stdout", tmp_path / "stderr",
        )

        accepted_regular = _run_python_heredoc(
            program, regular_receipt, *event_args,
        )
        rejected_link = _run_python_heredoc(
            program, linked_receipt, *event_args,
        )

    assert accepted_regular.returncode == 0, accepted_regular.stderr
    assert rejected_link.returncode != 0
    assert "submission receipt is not a unique regular file" in rejected_link.stderr


def test_all_submit_receipt_events_pin_the_t1998_schema():
    submitter = SUBMITTER.read_text(encoding="utf-8")
    schema_field = (
        '"schema_version": "t1998-balanced-stock-inline-submit-event/v1"'
    )

    assert submitter.count(schema_field) == 3


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
