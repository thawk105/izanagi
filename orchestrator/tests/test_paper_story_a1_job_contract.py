from __future__ import annotations

import ast
import hashlib
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign import ident, site_policy
from orchestrator.campaign import paper_story_a1_paired as paired
from orchestrator.campaign.build_admission import GeneratorId, build_run_context


REPO_ROOT = Path(__file__).resolve().parents[2]
JOB = REPO_ROOT / "tools/pegasus/paper_story_a1_paired.sh"
REGISTRY = REPO_ROOT / "tools/pegasus/admission_registry.json"


def _gate_args(tmp_path: Path) -> dict:
    repo = tmp_path / "repo"
    repo.mkdir(parents=True)
    attempt = tmp_path / "attempt"
    return {
        "repo_root": repo,
        "expected_head": "a" * 40,
        "output_root": attempt / "raw" / "campaign-output",
        "cache_root": attempt / "cache",
        "result_root": attempt / "raw" / "results",
        "pbs_jobid": "12345.nqsv",
        "site": site_policy.PEGASUS_COMPUTE,
        "observed_head": "a" * 40,
        "porcelain": "",
        "attempt_root": attempt,
    }


def test_clean_h0_compute_fresh_roots_positive_contract(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    roots = paired.validate_measure_environment(**args)
    assert roots == {
        "output_root": os.fspath((tmp_path / "attempt/raw/campaign-output").resolve()),
        "cache_root": os.fspath((tmp_path / "attempt/cache").resolve()),
        "result_root": os.fspath((tmp_path / "attempt/raw/results").resolve()),
    }
    assert not any(Path(path).exists() for path in roots.values())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("site", site_policy.PEGASUS_LOGIN, "Pegasus compute"),
        ("site", site_policy.PEGASUS_SUSPECT, "Pegasus compute"),
        ("observed_head", "b" * 40, "HEAD differs"),
        ("porcelain", " M tracked.py", "dirty"),
        ("pbs_jobid", "bad job id", "PBS_JOBID"),
    ],
    ids=["M12-login", "M12-suspect", "M12-head-mismatch", "M12-dirty", "bad-pbs"],
)
def test_measure_environment_rejects_site_head_dirty_and_pbs(
    tmp_path: Path, field: str, value: str, message: str
) -> None:
    args = _gate_args(tmp_path)
    args[field] = value
    with pytest.raises(paired.PaperStoryError, match=message):
        paired.validate_measure_environment(**args)


@pytest.mark.parametrize("root_name", ["output_root", "cache_root", "result_root"])
def test_measure_environment_rejects_every_existing_root(
    tmp_path: Path, root_name: str
) -> None:
    args = _gate_args(tmp_path)
    Path(args[root_name]).mkdir(parents=True)
    with pytest.raises(paired.PaperStoryError, match="must not already exist"):
        paired.validate_measure_environment(**args)


def test_measure_environment_rejects_repo_internal_or_aliased_roots(tmp_path: Path) -> None:
    args = _gate_args(tmp_path)
    args["output_root"] = args["repo_root"] / "raw"
    with pytest.raises(paired.PaperStoryError, match="outside the repository"):
        paired.validate_measure_environment(**args)

    args = _gate_args(tmp_path / "nested")
    args["cache_root"] = args["output_root"] / "cache"
    with pytest.raises(paired.PaperStoryError, match="overlap"):
        paired.validate_measure_environment(**args)

    args = _gate_args(tmp_path / "second")
    args["cache_root"] = args["output_root"]
    with pytest.raises(paired.PaperStoryError, match="distinct"):
        paired.validate_measure_environment(**args)


def _policy_for_base(base: Path) -> dict:
    policy = json.loads(json.dumps(paired.load_policy()[0]))
    policy["execution"]["durable_measurement_base"] = os.fspath(base)
    return policy


def _acquisition(attempt_root: Path, repo_root: Path) -> dict:
    job = repo_root / paired.JOB_RELATIVE_PATH
    if not job.exists():
        job.parent.mkdir(parents=True, exist_ok=True)
        job.write_text("# receipt job fixture\n", encoding="utf-8")
    argv, options = paired._canonical_qsub_contract(
        repo_root=repo_root.resolve(),
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        attempt=attempt_root,
    )
    qsub_stdout = "12345.nqsv\n"
    qsub_stderr = ""
    evidence = paired._attempt_evidence_paths(attempt_root)
    return {
        "schema_version": paired.SUBMISSION_SCHEMA,
        "route": "direct-qsub",
        "study_id": paired.STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": os.fspath(attempt_root),
        "request_id": "12345.nqsv",
        "submission_receipt_path": evidence["submission_receipt"],
        "completion_receipt_path": evidence["completion_receipt"],
        "qsub_argv": argv,
        "qsub_options": options,
        "submit_observation": {
            "submit_host": "pegasus01",
            "qsub_stdout": qsub_stdout,
            "qsub_stdout_sha256": hashlib.sha256(qsub_stdout.encode()).hexdigest(),
            "qsub_stderr": qsub_stderr,
            "qsub_stderr_sha256": hashlib.sha256(qsub_stderr.encode()).hexdigest(),
            "qstat_visibility": {
                "request_id": "12345.nqsv",
                "visible": True,
                "state": "Q",
                "observed_epoch": 1,
            },
        },
    }


def _pbs_observation(
    attempt_root: Path,
    repo_root: Path,
    *,
    host: str = "pegasus01",
) -> dict[str, str]:
    evidence = paired._attempt_evidence_paths(attempt_root)
    return {
        "pbs_jobid": "12345.nqsv",
        "pbs_o_host": host,
        "pbs_o_workdir": os.fspath(repo_root.resolve()),
        "pbs_o_queue": "gen_S",
        "stdout_path": evidence["stdout_path"],
        "stderr_path": evidence["stderr_path"],
    }


def test_acquisition_receipt_binds_request_and_fixed_topology(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "trusted-attempt"
    attempt.mkdir()
    policy = _policy_for_base(base)
    roots = paired.validate_acquisition_receipt(
        _acquisition(attempt, repo),
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=policy,
    )
    assert roots["raw_root"] == os.fspath(attempt / "raw")
    assert roots["cache_root"] == os.fspath(attempt / "cache")
    assert Path(roots["raw_root"]).parent == Path(roots["cache_root"]).parent

    with pytest.raises(paired.PaperStoryError, match="request ID"):
        paired.validate_acquisition_receipt(
            _acquisition(attempt, repo),
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="99999.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=policy,
        )


@pytest.mark.parametrize(
    "field",
    [
        "pbs_jobid",
        "pbs_o_host",
        "pbs_o_workdir",
        "pbs_o_queue",
        "stdout_path",
        "stderr_path",
    ],
)
def test_pbs_environment_cross_bind_rejects_each_mismatch_M19(
    tmp_path: Path, field: str
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo)
    observation = _pbs_observation(attempt, repo)
    observation[field] += "-wrong"
    with pytest.raises(
        paired.PaperStoryError,
        match="PBS environment observation does not cross-bind receipt",
    ):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=observation,
            policy=_policy_for_base(base),
        )


def test_attempt_root_inode_revalidation_rejects_replacement_M20(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    trusted = paired.validate_acquisition_receipt(
        _acquisition(attempt, repo),
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=_policy_for_base(base),
    )
    paired._revalidate_attempt_root(trusted)
    attempt.rename(base / "original-attempt")
    attempt.mkdir()
    with pytest.raises(paired.PaperStoryError, match="inode binding differs"):
        paired._revalidate_attempt_root(trusted)


def test_materializer_keeps_attempt_inode_revalidation_call_M20() -> None:
    source = (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    materializer = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "run_materialize"
    )
    calls = {
        node.func.id
        for node in ast.walk(materializer)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "_revalidate_attempt_root" in calls


def test_submission_receipt_rejects_handmade_six_field_json(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    complete = _acquisition(attempt, repo)
    handmade = {
        key: complete[key]
        for key in (
            "schema_version", "route", "study_id", "source_commit",
            "attempt_root", "request_id",
        )
    }
    with pytest.raises(paired.PaperStoryError, match="submission receipt shape"):
        paired.validate_acquisition_receipt(
            handmade,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_submission_receipt_rejects_noncanonical_qsub_argv_M15(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    receipt = _acquisition(attempt, repo)
    receipt["qsub_argv"][-1] = os.fspath(repo / "wrong-job.sh")
    with pytest.raises(paired.PaperStoryError, match="canonical qsub argv"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(attempt, repo),
            policy=_policy_for_base(base),
        )


def test_acquisition_receipt_requires_direct_durable_child_M16(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    policy = _policy_for_base(base)
    for attempt in (base, tmp_path / "outside", base / "parent" / "grandchild"):
        receipt = _acquisition(attempt, repo)
        with pytest.raises(paired.PaperStoryError, match="direct durable-base child"):
            paired.validate_acquisition_receipt(
                receipt,
                repo_root=repo,
                study_id=paired.STUDY_ID,
                source_commit="a" * 40,
                request_id="12345.nqsv",
                pbs_observation=_pbs_observation(attempt, repo),
                policy=policy,
            )

    target = tmp_path / "symlink-target"
    target.mkdir()
    alias = base / "alias"
    alias.symlink_to(target, target_is_directory=True)
    receipt = _acquisition(alias, repo)
    with pytest.raises(paired.PaperStoryError, match="canonical absolute"):
        paired.validate_acquisition_receipt(
            receipt,
            repo_root=repo,
            study_id=paired.STUDY_ID,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            pbs_observation=_pbs_observation(alias, repo),
            policy=policy,
        )


def test_scheduler_completion_receipt_cross_binds_terminal_and_logs(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    attempt = base / "attempt"
    attempt.mkdir()
    submission = _acquisition(attempt, repo)
    trusted = paired.validate_acquisition_receipt(
        submission,
        repo_root=repo,
        study_id=paired.STUDY_ID,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        pbs_observation=_pbs_observation(attempt, repo),
        policy=_policy_for_base(base),
    )
    submission_raw = (json.dumps(submission, sort_keys=True) + "\n").encode()
    Path(trusted["submission_receipt"]).write_bytes(submission_raw)
    Path(trusted["stdout_path"]).write_bytes(b"job stdout\n")
    Path(trusted["stderr_path"]).write_bytes(b"")
    terminal_path = Path(trusted["raw_root"]) / "job-terminal.json"
    terminal_path.parent.mkdir(parents=True)
    terminal_path.write_bytes(b"terminal\n")
    qstat_stdout = "Job Id: 12345.nqsv\n    job_state = F\n"

    def binding(path: str | Path) -> dict:
        candidate = Path(path)
        return {
            "path": os.fspath(candidate),
            "sha256": hashlib.sha256(candidate.read_bytes()).hexdigest(),
        }

    completion = {
        "schema_version": paired.COMPLETION_SCHEMA,
        "study_id": paired.STUDY_ID,
        "source_commit": "a" * 40,
        "attempt_root": trusted["attempt_root"],
        "request_id": "12345.nqsv",
        "submission_receipt": binding(trusted["submission_receipt"]),
        "scheduler_terminal": {
            "qstat_visible": True,
            "state": "F",
            "exit_status": 0,
            "observed_epoch": 2,
            "qstat_stdout": qstat_stdout,
            "qstat_stdout_sha256": hashlib.sha256(qstat_stdout.encode()).hexdigest(),
        },
        "stdout": binding(trusted["stdout_path"]),
        "stderr": binding(trusted["stderr_path"]),
        "job_terminal": binding(terminal_path),
    }
    assert paired.validate_completion_receipt(
        completion,
        trusted_roots=trusted,
        source_commit="a" * 40,
        request_id="12345.nqsv",
        submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
        job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
    ) == completion

    incomplete = json.loads(json.dumps(completion))
    incomplete["stdout"].pop("sha256")
    with pytest.raises(paired.PaperStoryError, match="stdout binding"):
        paired.validate_completion_receipt(
            incomplete,
            trusted_roots=trusted,
            source_commit="a" * 40,
            request_id="12345.nqsv",
            submission_receipt_sha256=hashlib.sha256(submission_raw).hexdigest(),
            job_terminal_sha256=hashlib.sha256(terminal_path.read_bytes()).hexdigest(),
        )

def _shell_body_without_heredocs(source: str) -> str:
    output = []
    delimiter = None
    opener = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\1")
    for line in source.splitlines(keepends=True):
        if delimiter is not None:
            if line.strip() == delimiter:
                delimiter = None
            continue
        match = opener.search(line)
        if match is None:
            output.append(line)
            continue
        delimiter = match.group(2)
        output.append(line[:match.start()] + "<<< ''" + line[match.end():])
    if delimiter is not None:
        raise AssertionError("unterminated shell heredoc")
    return "".join(output)


def _shell_submitter_violations(source: str) -> list[str]:
    body = _shell_body_without_heredocs(source)
    syntax = subprocess.run(
        ["bash", "-n"], input=body, text=True, capture_output=True, check=False
    )
    if syntax.returncode != 0:
        raise AssertionError(f"heredoc-free shell syntax is invalid: {syntax.stderr}")
    violations = []
    declaration = re.compile(
        r"(?m)(?:^|[;{}&|])\s*(?:function\s+)?"
        r"(submit[A-Za-z0-9_]*)\s*(?:\(\s*\))?\s*\{"
    )
    violations.extend(
        f"submitter-function:{match.group(1)}" for match in declaration.finditer(body)
    )

    lexer = shlex.shlex(body, posix=True, punctuation_chars=";&|(){}\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = "#"
    command_position = True
    wrapper = False
    indirect_qsub = set()
    separators = {";", ";;", "&", "&&", "|", "||", "(", ")", "{", "}", "\n"}
    reserved = {"if", "then", "elif", "else", "while", "until", "do"}
    for token in lexer:
        if token in separators or set(token) <= set(";&|(){}\n"):
            command_position = True
            wrapper = False
            continue
        if not command_position:
            continue
        assignment = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=(.*)", token)
        if assignment is not None:
            name, value = assignment.groups()
            if Path(value).name == "qsub" or "QSUB" in name.upper():
                indirect_qsub.add(name)
            continue
        if token in reserved or token == "!":
            continue
        if token in {"command", "exec", "builtin"}:
            wrapper = True
            continue
        if wrapper and token == "--":
            continue
        variable = re.fullmatch(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?", token)
        if Path(token).name == "qsub":
            violations.append(f"qsub-invocation:{token}")
        elif variable is not None and (
            variable.group(1) in indirect_qsub
            or "QSUB" in variable.group(1).upper()
        ):
            violations.append(f"qsub-indirect:{token}")
        command_position = False
        wrapper = False
    return violations


@pytest.mark.parametrize(
    "source",
    [
        "submit_job() { qsub job.sh; }\n",
        "function submit_job { :; }\n",
        "command qsub job.sh\n",
        "/usr/bin/qsub job.sh\n",
        "QSUB=/usr/bin/qsub\n$QSUB job.sh\n",
    ],
)
def test_submitter_guard_detects_bash_syntax_variants(source: str) -> None:
    assert _shell_submitter_violations(source)


def test_submitter_guard_ignores_python_heredoc_receipt_keys() -> None:
    source = """#!/bin/bash
python3 - <<'PY'
document = {"submit_observation": {"submit_host": "pegasus01"}}
PY
"""
    assert _shell_submitter_violations(source) == []


def test_job_body_contains_all_m12_gates_and_no_submitter() -> None:
    source = JOB.read_text(encoding="utf-8")
    required = (
        '[[ -n "${PBS_JOBID:-}" ]]',
        '[[ -n "${PBS_O_HOST:-}" ]]',
        '[[ -n "${PBS_O_WORKDIR:-}" ]]',
        '[[ -n "${PBS_O_QUEUE:-}" ]]',
        '[[ -n "${IZANAGI_A1_ACQUISITION_RECEIPT:-}" ]]',
        '[[ -n "${IZANAGI_A1_COMPLETION_RECEIPT:-}" ]]',
        '[[ "$CURRENT_HEAD" == "$IZANAGI_EXPECTED_HEAD" ]]',
        "status --porcelain --untracked-files=all",
        "site_policy.PEGASUS_COMPUTE",
        "for ((WAITED=0; WAITED<60; WAITED++))",
        'mkdir -- "$ATTEMPT_ROOT"',
        'mkdir -- "$RAW_ROOT"',
        '--study-id "$EXPECTED_STUDY_ID"',
        '--expected-head "$IZANAGI_EXPECTED_HEAD"',
        '--acquisition-receipt "$IZANAGI_A1_ACQUISITION_RECEIPT"',
        '--acquisition-receipt-sha256 "$ACQUISITION_SHA"',
        '--output-root "$OUTPUT_ROOT"',
        '--cache-root "$CACHE_ROOT"',
        '--result-root "$RESULT_ROOT"',
        'export IZANAGI_EXPLORATION_OUTPUT_ROOT="$OUTPUT_ROOT"',
        "os.O_EXCL",
        'observation["submit_host"] != pbs_o_host',
        'pbs_stdout_path != options["o"]',
        '"pbs_observation": {',
        '"attempt_identity": {',
    )
    for marker in required:
        assert source.count(marker) == 1, marker
    assert _shell_submitter_violations(source) == []
    assert "dispatch_compute.py" not in source


def _shell_fixture(tmp_path: Path, *, dirty: bool = False, mode: str = "ok"):
    repo = tmp_path / "repo"
    driver = repo / paired.DRIVER_RELATIVE_PATH
    driver.parent.mkdir(parents=True)
    driver.write_text("# driver stub target\n", encoding="utf-8")
    base = (tmp_path / "measurement").resolve()
    base.mkdir()
    policy_path = repo / paired.POLICY_RELATIVE_PATH
    policy_path.parent.mkdir(parents=True, exist_ok=True)
    policy_path.write_text(
        json.dumps(_policy_for_base(base), sort_keys=True) + "\n",
        encoding="utf-8",
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    head = "a" * 40
    git_stub = bin_dir / "git"
    git_stub.write_text(
        "#!/bin/bash\n"
        "if [[ \"$*\" == *\"rev-parse HEAD\"* ]]; then echo \"$FAKE_HEAD\"; exit 0; fi\n"
        "if [[ \"$*\" == *\"status --porcelain\"* ]]; then "
        "[[ \"${FAKE_DIRTY:-0}\" == 1 ]] && echo ' M tracked.py'; exit 0; fi\n"
        "echo \"${FAKE_BLOB:-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb}\"\n",
        encoding="utf-8",
    )
    git_stub.chmod(0o755)
    python_stub_source = (
        "#!/bin/bash\n"
        "printf '%s\\n' \"$*\" >> \"$STUB_LOG\"\n"
        "if [[ \"$1\" == '-c' ]]; then exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == *.submission.json ]]; then "
        "exec /usr/bin/python3 \"$@\"; fi\n"
        "if [[ \"$1\" == '-' && \"$2\" == *job-terminal.json ]]; then\n"
        "  [[ \"$STUB_MODE\" == writer-fail ]] && exit 9\n"
        "  : > \"$2\"; exit 0\n"
        "fi\n"
        "if [[ \"$1\" == '-' ]]; then exit 0; fi\n"
        "if [[ \"$1\" == *.py ]]; then\n"
        "  if [[ \"$STUB_MODE\" == existing-terminal ]]; then "
        ": > \"$IZANAGI_A1_ATTEMPT_ROOT/raw/job-terminal.json\"; fi\n"
        "  exit 0\n"
        "fi\n"
        "exit 8\n"
    )
    for name in ("python3.10", "python3.11", "python3.12", "python3"):
        stub = bin_dir / name
        stub.write_text(python_stub_source, encoding="utf-8")
        stub.chmod(0o755)
    attempt = base / "attempt"
    acquisition = Path(paired._attempt_evidence_paths(attempt)["submission_receipt"])
    acquisition.write_text(
        json.dumps(_acquisition(attempt, repo), sort_keys=True) + "\n", encoding="utf-8"
    )
    completion = Path(paired._attempt_evidence_paths(attempt)["completion_receipt"])
    log = tmp_path / "stub.log"
    environment = {
        **os.environ,
        "PATH": f"{bin_dir}:/usr/bin:/bin",
        "PBS_JOBID": "12345.nqsv",
        "PBS_O_HOST": "pegasus01",
        "PBS_O_WORKDIR": os.fspath(repo),
        "PBS_O_QUEUE": "gen_S",
        "IZANAGI_A1_STUDY_ID": paired.STUDY_ID,
        "IZANAGI_EXPECTED_HEAD": head,
        "IZANAGI_A1_ATTEMPT_ROOT": os.fspath(attempt),
        "IZANAGI_A1_ACQUISITION_RECEIPT": os.fspath(acquisition),
        "IZANAGI_A1_COMPLETION_RECEIPT": os.fspath(completion),
        "FAKE_HEAD": head,
        "FAKE_DIRTY": "1" if dirty else "0",
        "STUB_LOG": os.fspath(log),
        "STUB_MODE": mode,
    }
    return environment, attempt, log


def _run_shell_job(
    environment: dict[str, str],
    *,
    stdout_path: Path | None = None,
    stderr_path: Path | None = None,
):
    attempt = Path(environment["IZANAGI_A1_ATTEMPT_ROOT"])
    evidence = paired._attempt_evidence_paths(attempt)
    stdout_path = stdout_path or Path(evidence["stdout_path"])
    stderr_path = stderr_path or Path(evidence["stderr_path"])
    with stdout_path.open("w", encoding="utf-8") as stdout_stream, stderr_path.open(
        "w", encoding="utf-8"
    ) as stderr_stream:
        completed = subprocess.run(
            [os.fspath(JOB)],
            env=environment,
            text=True,
            stdout=stdout_stream,
            stderr=stderr_stream,
            check=False,
        )
    return completed, stderr_path.read_text(encoding="utf-8")


@pytest.mark.parametrize(
    "field",
    ["pbs_o_host", "pbs_o_workdir", "pbs_o_queue", "stdout_path", "stderr_path"],
)
def test_production_job_rejects_pbs_environment_cross_bind_M19(
    tmp_path: Path, field: str
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    run_options = {}
    if field == "pbs_o_host":
        environment["PBS_O_HOST"] = "other-submit-host"
    elif field == "pbs_o_workdir":
        alias = tmp_path / "repo-alias"
        alias.symlink_to(environment["PBS_O_WORKDIR"], target_is_directory=True)
        environment["PBS_O_WORKDIR"] = os.fspath(alias)
    elif field == "pbs_o_queue":
        environment["PBS_O_QUEUE"] = "other_queue"
    elif field == "stdout_path":
        run_options["stdout_path"] = tmp_path / "wrong.stdout"
    else:
        run_options["stderr_path"] = tmp_path / "wrong.stderr"
    completed, stderr = _run_shell_job(environment, **run_options)
    assert completed.returncode == 2
    assert "acquisition receipt validation failed" in stderr
    assert not attempt.exists()


def test_production_job_subprocess_rejects_dirty_before_creating_roots(
    tmp_path: Path,
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path, dirty=True)
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "working tree is dirty" in stderr
    assert not attempt.exists()


def test_production_job_rejects_noncanonical_qsub_argv_M15(
    tmp_path: Path,
) -> None:
    environment, attempt, _ = _shell_fixture(tmp_path)
    receipt_path = Path(environment["IZANAGI_A1_ACQUISITION_RECEIPT"])
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["qsub_argv"][-1] = os.fspath(tmp_path / "wrong-job.sh")
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 2
    assert "acquisition receipt validation failed" in stderr
    assert not attempt.exists()


def test_production_job_narrow_stub_reaches_site_and_driver(tmp_path: Path) -> None:
    environment, attempt, log = _shell_fixture(tmp_path)
    completed, stderr = _run_shell_job(environment)
    assert completed.returncode == 0, stderr
    assert (attempt / "raw/tmp").is_dir()
    assert paired.DRIVER_RELATIVE_PATH in log.read_text(encoding="utf-8")


@pytest.mark.parametrize("mode", ["writer-fail", "existing-terminal"])
def test_production_job_terminal_writer_failures_are_nonzero(
    tmp_path: Path, mode: str
) -> None:
    environment, _, _ = _shell_fixture(tmp_path, mode=mode)
    completed, _ = _run_shell_job(environment)
    assert completed.returncode == 70


def test_job_body_is_executable_and_registry_is_exact_dispatch_required() -> None:
    assert JOB.stat().st_mode & 0o111
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/paper_story_a1_paired.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS paper-story A-1 paired measurement job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }


def test_driver_reuses_run_campaign_without_direct_evaluate_call() -> None:
    source = (REPO_ROOT / paired.DRIVER_RELATIVE_PATH).read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        for alias in node.names
    }
    called = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert "run_campaign" in imported
    assert "run_campaign" in called
    assert "evaluate" not in imported
    assert "evaluate" not in called


def test_exact_two_arm_three_workload_campaign_ids_are_distinct_and_bound() -> None:
    policy = paired.load_policy()[0]
    context = build_run_context(generator_id=GeneratorId.BACKOFF_SWEEP)
    ids = [
        str(ident.campaign_id(ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )))
        for workload in paired.WORKLOAD_ORDER
    ]
    assert len(set(ids)) == 3
    assert len(paired.genomes(policy)) == 2
    for workload in paired.WORKLOAD_ORDER:
        cfg = ident.bind_admission_policy(
            paired.campaign_config(policy, workload), context.policy
        )
        assert cfg.search_config["study_id"] == paired.STUDY_ID
        assert cfg.search_config["arm_order"] == ["adaptive", "static10"]
        assert cfg.search_config["scale"] == {
            "records": 1_000_000,
            "threads": 48,
            "ycsb_zipf_skew": "0.9",
            "ycsb_rmw": "0",
            "ycsb_max_ope": "10",
            "extime_s": 3,
            "reps": 5,
            "expected_verify_configs": ["legacy"],
        }
        assert cfg.search_config["build_admission"] == json.loads(
            context.policy._preimage_json
        )
