import json
import os
import re
import shlex
import subprocess
import sys
from pathlib import Path

import pytest

from orchestrator.campaign import p3_s4_loop
from orchestrator.campaign import site_policy


REPO = Path(__file__).resolve().parents[2]
JOB = REPO / "tools/pegasus/p3_s4_loop_pegasus.sh"
REGISTRY = REPO / "tools/pegasus/admission_registry.json"
README = REPO / "tools/pegasus/README.md"

SUPERPROJECT_STATUS_GATE = (
    "if ! superproject_status=$(git status --porcelain --untracked-files=no \\\n"
    "  --ignore-submodules=all); then\n"
    '  refuse "cannot inspect superproject tracked status"\n'
    "fi\n"
    '[[ -z "$superproject_status" ]] || \\\n'
    '  refuse "superproject tracked worktree is not clean"'
)
CCBENCH_STATUS_GATE = (
    'if ! ccbench_status=$(git -C "$ccbench_dir" status --porcelain \\\n'
    "  --untracked-files=no); then\n"
    '  refuse "cannot inspect CCBench tracked status"\n'
    "fi\n"
    '[[ -z "$ccbench_status" ]] || refuse "CCBench source tree is not clean"'
)
THIRDPARTY_STATUS_GATE = (
    'if ! source_status=$(git -C "$source" status --porcelain \\\n'
    "    --untracked-files=no); then\n"
    '    refuse "cannot inspect third-party source tracked status: $source_name"\n'
    "  fi\n"
    '  [[ -z "$source_status" ]] || \\\n'
    '    refuse "third-party source tree is not clean: $source_name"'
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


def _shell_executable_surface(source: str) -> str:
    body = _shell_body_without_heredocs(source)
    return "".join(
        line for line in body.splitlines(keepends=True)
        if re.match(r"^\s*#", line) is None
    )


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


def _assert_static_job_contract(source: str) -> None:
    required = {
        "pbs-account": "#PBS -A SFC",
        "pbs-queue": "#PBS -q gen_S",
        "pbs-node-count": "#PBS -b 1",
        "pbs-walltime": "#PBS -l elapstim_req=03:00:00",
        "pbs-name": "#PBS -N izs4loop",
        "job-body-comment": (
            "# 親が直接投入する compute-only job body であり、投入器ではない。"
        ),
        "strict-shell": "set -Eeuo pipefail",
        "private-umask": "umask 077",
        "refusal-rc": 'echo "p3 S4 loop job refused: $1" >&2\n  exit 2',
        "required-pbs": "PBS_JOBID PBS_NODEFILE PBS_O_WORKDIR",
        "required-repo": "IZANAGI_S4_REPO_ROOT IZANAGI_S4_EXPECTED_HEAD",
        "required-evidence": (
            "IZANAGI_S4_EVIDENCE_ROOT IZANAGI_S4_THIRDPARTY_SOURCE_ROOT"
        ),
        "host-probe": "host=$(hostname 2>/dev/null || true)",
        "compute-refusal": 'refuse "P3 S4 loop job body is compute-only"',
        "base-build-env-sanitize": (
            "unset CC CXX CPP CFLAGS CXXFLAGS CPPFLAGS LDFLAGS"
        ),
        "library-env-sanitize": (
            "unset LD_PRELOAD LD_LIBRARY_PATH CPATH CPLUS_INCLUDE_PATH LIBRARY_PATH"
        ),
        "config-site-sanitize": "GCC_EXEC_PREFIX CONFIG_SITE",
        "cmake-toolchain-sanitize": (
            "unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE"
        ),
        "cmake-generator-sanitize": (
            "unset CMAKE_GENERATOR CMAKE_GENERATOR_INSTANCE CMAKE_GENERATOR_PLATFORM"
        ),
        "cmake-include-sanitize": (
            "CMAKE_PROJECT_TOP_LEVEL_INCLUDES CMAKE_C_COMPILER_LAUNCHER"
        ),
        "python-env-sanitize": (
            "CMAKE_CXX_COMPILER_LAUNCHER PYTHONPATH PYTHONHOME PYTHONSTARTUP MAKEFLAGS"
        ),
        "official-root-sanitize": "unset IZANAGI_OFFICIAL_OUTPUT_ROOT",
        "exploration-root-sanitize": "IZANAGI_EXPLORATION_OUTPUT_ROOT",
        "binary-policy-sanitize": "unset IZANAGI_B10_BINARY_PATH_POLICY",
        "dynamic-env-sanitize": "GIT_*|CCACHE_*|SCCACHE_*|DISTCC_*|ICECC_*",
        "bootstrap-path": (
            'export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"'
        ),
        "git-optional-locks": "export GIT_OPTIONAL_LOCKS=0",
        "http-proxy": 'export http_proxy="http://10.120.96.1:8080"',
        "https-proxy": 'export https_proxy="http://10.120.96.1:8080"',
        "no-user-site": "export PYTHONNOUSERSITE=1",
        "no-bytecode": "export PYTHONDONTWRITEBYTECODE=1",
        "canonical-repo": 'repo=$(cd -- "$IZANAGI_S4_REPO_ROOT" && pwd -P)',
        "worktree-container": '*"/.claude/worktrees/"*|*"/.codex/worktrees/"*',
        "git-common-root": (
            'git -C "$repo" rev-parse --path-format=absolute --git-common-dir'
        ),
        "evidence-outside-repo": (
            'if [[ "$evidence_root" == "$repo" '
            '|| "$evidence_root" == "$repo/"* \\\n'
            '   || "$evidence_root" == "$git_common_repo" \\\n'
            '   || "$evidence_root" == "$git_common_repo/"* ]]; then'
        ),
        "result-create-only": 'if ! ln "$tmp" "$result"; then',
        "result-schema": "p3-s4-loop-compute-result/v1",
        "result-fields": (
            '\"driver_rc\":%s,\"pbs_jobid\":\"%s\",'
            '\"python_realpath\":\"%s\",\"python_sha256\":\"%s\"'
        ),
        "exit-trap": "trap finish EXIT",
        "python-candidates": (
            "for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do"
        ),
        "python-exact-version": "sys.version_info[:2] == (3, 10)",
        "python-driver-import": "import orchestrator.campaign.p3_s4_loop",
        "python-realpath": "print(os.path.realpath(sys.executable))",
        "python-sha256": 'python_sha256=$(sha256sum -- "$PY")',
        "scratch-path": 'scratch=$scratch_base/${pbs_jobid_path_component}',
        "shim-runtime-closure": (
            '${#shim_entries[@]} -ne 1 || "${shim_entries[0]##*/}" != python3'
        ),
        "expected-head": '"$observed_head" != "$IZANAGI_S4_EXPECTED_HEAD"',
        "clean-tree": SUPERPROJECT_STATUS_GATE,
        "campaign-pin-import": (
            "'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)'"
        ),
        "campaign-pin-resolver": (
            'git -C "$ccbench_dir" rev-parse --verify "${campaign_pin}^{commit}"'
        ),
        "campaign-pin-exact": (
            '"$ccbench_full_head" != "$resolved_campaign_pin"'
        ),
        "campaign-pin-prefix": '"$ccbench_full_head" != "$campaign_pin"*',
        "ccbench-clean": CCBENCH_STATUS_GATE,
        "qstat-jobid": 'qstat_jobid=${PBS_JOBID#0:}',
        "scheduler-observation": 'qstat -f "$qstat_jobid"',
        "reservation-job-id": 'export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"',
        "reservation-requested": (
            'export IZANAGI_RESERVATION_REQUESTED_S="$requested_s"'
        ),
        "reservation-started": (
            'export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH='
            '"$scheduler_started_epoch"'
        ),
        "reservation": (
            'export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"'
        ),
        "reservation-host": 'export IZANAGI_RESERVATION_HOST="$host"',
        "reservation-boot": 'export IZANAGI_RESERVATION_BOOT_ID="$boot_id"',
        "reservation-script-hash": (
            'export IZANAGI_RESERVATION_SCRIPT_SHA256="$script_sha256"'
        ),
        "reservation-nonce": 'export IZANAGI_RESERVATION_NONCE="$PBS_JOBID"',
        "reservation-script": (
            "job_body=$repo/tools/pegasus/p3_s4_loop_pegasus.sh"
        ),
        "reservation-schema": "p3-s4-loop-reservation-result/v1",
        "reservation-create-only": 'with open(destination, "x", encoding="utf-8")',
        "claim-root": 'mkdir -p -m 0700 -- "$claim_root"',
        "source-head": "git -C \"$source\" rev-parse --verify 'HEAD^{commit}'",
        "source-clean": THIRDPARTY_STATUS_GATE,
        "prebuild-scratch-copy": 'cp -a "$source"/. "$destination"/',
        "prebuild-copy-destination": (
            "destination=$prebuild_source_root/${source_name}-src"
        ),
        "prebuild-base-equality": (
            "fetchcontent_base_dir=$prebuild_source_root"
        ),
        "prebuild-masstree-copy-root": (
            "masstree_source_dir=$prebuild_source_root/masstree-src"
        ),
        "prebuild-mimalloc-copy-root": (
            "mimalloc_source_dir=$prebuild_source_root/mimalloc-src"
        ),
        "prebuild-googletest-copy-root": (
            "googletest_source_dir=$prebuild_source_root/googletest-src"
        ),
        "prebuild-fresh-config": (
            '[[ -e "$masstree_source_dir/config.h" '
            '|| -L "$masstree_source_dir/config.h" ]]'
        ),
        "prebuild-toolchain": (
            "expected_toolchain_manifest = buildcache.observed_toolchain_manifest("
        ),
        "prebuild-call": "prepared = buildcache.prepare_masstree_fetchcontent(",
        "prebuild-ccbench": "ccbench_dir=ccbench_dir,",
        "prebuild-base": "fetchcontent_base_dir=fetchcontent_base_dir,",
        "prebuild-timeouts": "configure_timeout_s=900,\n    target_timeout_s=900,",
        "prebuild-masstree": "masstree_source_dir=masstree_source_dir,",
        "prebuild-mimalloc": "mimalloc_source_dir=mimalloc_source_dir,",
        "prebuild-googletest": "googletest_source_dir=googletest_source_dir,",
        "receipt-schema": "p3-s4-loop-masstree-prebuild/v1",
        "receipt-source-root": '\"source_root\": os.path.realpath(source_root)',
        "receipt-masstree-head": '\"head_commit\": masstree_head',
        "receipt-mimalloc-head": '\"head_commit\": mimalloc_head',
        "receipt-googletest-head": '\"head_commit\": googletest_head',
        "receipt-config-hash": '\"config_h_sha256\": config_h_sha256',
        "receipt-config-regular": (
            "not os.path.isfile(config_h_candidate) or "
            "os.path.islink(config_h_candidate)"
        ),
        "receipt-config-canonical": (
            "config_h_path = os.path.realpath(config_h_candidate)"
        ),
        "receipt-configure": '\"configure_argv\": list(prepared.configure_argv)',
        "receipt-build": '\"build_argv\": list(prepared.build_argv)',
        "receipt-toolchain": '\"toolchain_manifest\": expected_toolchain_manifest',
        "receipt-pbs": '\"pbs_jobid\": pbs_jobid',
        "receipt-create-only": 'with open(receipt_path, "x", encoding="utf-8")',
        "driver": '"$PY" -B -m orchestrator.campaign.p3_s4_loop',
        "build-authority": "--allow-coder-derived-build",
        "isolation": "--isolate-worktree",
        "proposal": (
            '--fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"'
        ),
        "fixture": (
            '--fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
            '    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"'
        ),
    }
    missing = [label for label, fragment in required.items() if fragment not in source]
    if missing:
        raise AssertionError("job contract missing: " + ",".join(missing))
    canonical_dump = (
        'json.dump(record, stream, ensure_ascii=True, sort_keys=True, '
        'separators=(",", ":"))'
    )
    if source.count(canonical_dump) != 2:
        raise AssertionError("job contract missing: canonical-json-receipts")
    if source.count("os.fsync(stream.fileno())") != 2:
        raise AssertionError("job contract missing: fsync-receipts")

    _assert_forbidden_job_constructs(source)


def _assert_forbidden_job_constructs(source: str) -> None:
    body = _shell_body_without_heredocs(source)
    if "--no-build" in body:
        raise AssertionError("forbidden-no-build")
    forbidden_assignment = re.search(
        r"(?m)^\s*(?:export\s+)?(?:CMAKE_PREFIX_PATH|CMAKE_PROJECT_INCLUDE"
        r"(?:_BEFORE)?|CMAKE_PROJECT_TOP_LEVEL_INCLUDES|"
        r"CMAKE_(?:C|CXX)_COMPILER_LAUNCHER)=",
        body,
    )
    if forbidden_assignment is not None:
        raise AssertionError("forbidden-cmake-environment-injection")
    forbidden_shim = re.search(
        r'\$(?:\{)?shim_dir(?:\})?/(?:cmake|c\+\+|gcc|cc|g\+\+|make|git|nm)(?:["\s]|$)',
        body,
    )
    if forbidden_shim is not None:
        raise AssertionError("forbidden-shim-entry")


def test_job_body_static_contract() -> None:
    _assert_static_job_contract(JOB.read_text(encoding="utf-8"))


def _assert_static_job_stage_order(source: str) -> None:
    surface = _shell_executable_surface(source)
    markers = (
        "required_env=(",
        "host=$(hostname",
        "unset CC CXX",
        'export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"',
        'repo=$(cd -- "$IZANAGI_S4_REPO_ROOT"',
        "trap finish EXIT",
        "resolve_python() {",
        "\nresolve_python\n",
        'shim_dir=$scratch/python-shim',
        "observed_head=$(git rev-parse HEAD)",
        "\ncampaign_pin=$(\n",
        "qstat_jobid=",
        'claim_root="$repo/output/env/',
        "prebuild_source_root=",
        '"$PY" - "$prebuild_receipt"',
        'sync "$prebuild_receipt"',
        'if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]',
    )
    counts = {marker: surface.count(marker) for marker in markers}
    assert all(count == 1 for count in counts.values()), counts
    positions = [surface.index(marker) for marker in markers]
    assert positions == sorted(positions), list(zip(markers, positions))


def test_static_contract_orders_all_job_stages() -> None:
    _assert_static_job_stage_order(JOB.read_text(encoding="utf-8"))


def test_dead_comment_cannot_mask_a_late_exit_trap() -> None:
    source = JOB.read_text(encoding="utf-8")
    mutant = source.replace("trap finish EXIT", "# trap finish EXIT", 1)
    mutant = mutant.replace(
        "\nresolve_python\n",
        "\nresolve_python\ntrap finish EXIT\n",
        1,
    )
    with pytest.raises(AssertionError):
        _assert_static_job_stage_order(mutant)


def test_gate_refusals_share_the_fixed_rc2_boundary() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert 'echo "p3 S4 loop job refused: $1" >&2\n  exit 2' in source
    for message in (
        "missing required environment: $name",
        "P3 S4 loop job body is compute-only",
        "repository root must not be inside an AI worktree container",
        "evidence root resolves inside a repository",
        "compute result already exists",
        "Python 3.10 capable of importing the P3 S4 loop is required",
        "Python shim directory must contain only python3",
        "expected HEAD mismatch",
        "superproject tracked worktree is not clean",
        "CCBench P3 S4 campaign pin mismatch",
        "scheduler reservation observation is incomplete",
        "campaign claim root provisioning failed",
        "scratch masstree source is not fresh",
        "masstree prebuild receipt is not fresh",
    ):
        assert f'refuse "{message}"' in source


@pytest.mark.parametrize(
    "label,fragment,replacement",
    (
        (
            "expected-head",
            '"$observed_head" != "$IZANAGI_S4_EXPECTED_HEAD"',
            '"$observed_head" != ""',
        ),
        (
            "clean-tree",
            SUPERPROJECT_STATUS_GATE,
            "true # superproject status gate removed",
        ),
        (
            "campaign-pin-import",
            "'from orchestrator.campaign.p3_s4_loop import PIN; print(PIN)'",
            "'from orchestrator.campaign.pin import CURRENT_PIN; print(CURRENT_PIN)'",
        ),
        (
            "evidence-outside-repo",
            'if [[ "$evidence_root" == "$repo" '
            '|| "$evidence_root" == "$repo/"* \\\n'
            '   || "$evidence_root" == "$git_common_repo" \\\n'
            '   || "$evidence_root" == "$git_common_repo/"* ]]; then',
            'if [[ "$evidence_root" == "/impossible" ]]; then',
        ),
        (
            "prebuild-scratch-copy",
            'cp -a "$source"/. "$destination"/',
            'source=$destination',
        ),
        pytest.param(
            "prebuild-copy-destination",
            "destination=$prebuild_source_root/${source_name}-src",
            "destination=$prebuild_source_root/$source_name",
            id="prebuild-copy-destination",
        ),
        pytest.param(
            "prebuild-base-equality",
            "fetchcontent_base_dir=$prebuild_source_root",
            "fetchcontent_base_dir=$scratch/fetchcontent-base",
            id="prebuild-base-equality",
        ),
        pytest.param(
            "proposal",
            '--fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
            '--run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
            id="proposal",
        ),
        pytest.param(
            "fixture",
            '--fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
            '    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"',
            '--value "${IZANAGI_S4_FIXTURE_VALUE:-20}"',
            id="fixture",
        ),
        (
            "receipt-create-only",
            'with open(receipt_path, "x", encoding="utf-8")',
            'with open(receipt_path, "w", encoding="utf-8")',
        ),
        (
            "reservation",
            'export IZANAGI_RESERVATION_DEADLINE_EPOCH="$deadline_epoch"',
            'true # deadline export removed',
        ),
        (
            "claim-root",
            'mkdir -p -m 0700 -- "$claim_root"',
            'true # claim root provisioning removed',
        ),
        (
            "qstat-jobid",
            'qstat_jobid=${PBS_JOBID#0:}',
            "qstat_jobid=$PBS_JOBID",
        ),
    ),
)
def test_registered_fragment_mutants_have_one_static_failure(
    label: str, fragment: str, replacement: str
) -> None:
    source = JOB.read_text(encoding="utf-8")
    assert source.count(fragment) == 1
    mutant = source.replace(fragment, replacement, 1)
    with pytest.raises(AssertionError) as error:
        _assert_static_job_contract(mutant)
    assert str(error.value) == f"job contract missing: {label}"


@pytest.mark.parametrize("tool", ("cmake", "c++", "gcc", "cc", "g++", "make", "git", "nm"))
def test_forbidden_build_tool_shim_mutants_are_rejected(tool: str) -> None:
    source = JOB.read_text(encoding="utf-8")
    anchor = 'mkdir -m 0700 -- "$shim_dir"'
    mutant = source.replace(
        anchor,
        anchor + f'\nln -s -- /usr/bin/{tool} "$shim_dir/{tool}"',
        1,
    )
    with pytest.raises(AssertionError, match="^forbidden-shim-entry$"):
        _assert_static_job_contract(mutant)


def test_no_build_mutant_has_one_negative_failure() -> None:
    source = JOB.read_text(encoding="utf-8")
    mutant = source.replace("--allow-coder-derived-build", "--no-build")
    with pytest.raises(AssertionError) as error:
        _assert_static_job_contract(mutant)
    assert str(error.value) == "job contract missing: build-authority"

    injected = source.replace(
        '--isolate-worktree \\\n',
        '--isolate-worktree \\\n    --no-build \\\n',
        1,
    )
    with pytest.raises(AssertionError) as error:
        _assert_forbidden_job_constructs(injected)
    assert str(error.value) == "forbidden-no-build"


@pytest.mark.parametrize(
    "assignment",
    (
        'CMAKE_PREFIX_PATH=/tmp/deps',
        'CMAKE_PROJECT_INCLUDE=/tmp/inject.cmake',
        'CMAKE_PROJECT_INCLUDE_BEFORE=/tmp/inject.cmake',
        'CMAKE_PROJECT_TOP_LEVEL_INCLUDES=/tmp/inject.cmake',
        'CMAKE_C_COMPILER_LAUNCHER=/tmp/launcher',
        'CMAKE_CXX_COMPILER_LAUNCHER=/tmp/launcher',
    ),
)
def test_forbidden_cmake_environment_mutants_are_rejected(assignment: str) -> None:
    source = JOB.read_text(encoding="utf-8") + "\n" + assignment + "\n"
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_static_job_contract(source)


def test_job_body_has_no_submitter_invocation() -> None:
    assert _shell_submitter_violations(JOB.read_text(encoding="utf-8")) == []


def test_submitter_guard_accepts_qstat_and_comment_mentions() -> None:
    source = """#!/bin/bash
# qsub is named only in this comment.
qstat -f "$PBS_JOBID"
"""
    assert _shell_submitter_violations(source) == []


@pytest.mark.parametrize(
    "source,expected",
    (
        ("qsub job.sh\n", "qsub-invocation:qsub"),
        ("command qsub job.sh\n", "qsub-invocation:qsub"),
        ("/usr/bin/qsub job.sh\n", "qsub-invocation:/usr/bin/qsub"),
        ("QSUB=/usr/bin/qsub\n$QSUB job.sh\n", "qsub-indirect:$QSUB"),
    ),
)
def test_submitter_guard_detects_four_invocation_forms(
    source: str, expected: str
) -> None:
    assert _shell_submitter_violations(source) == [expected]


def _resolver_and_shim_snippet(source: str) -> str:
    start = source.index("resolve_python() {")
    final_path = 'export PATH="$SANITIZED_PATH"'
    end = source.index(final_path, start) + len(final_path)
    snippet = source[start:end]
    closure_start = snippet.index("shopt -s nullglob dotglob")
    path_start = snippet.index('SANITIZED_PATH="$shim_dir:/usr/bin:/bin"')
    return snippet[:closure_start] + snippet[path_start:]


def _write_executable(path: Path, source: str) -> None:
    path.write_text(source, encoding="utf-8")
    path.chmod(0o755)


def test_interpreter_resolver_hides_an_old_bare_python3(tmp_path: Path) -> None:
    old_bin = tmp_path / "old-bin"
    good_bin = tmp_path / "good-bin"
    old_bin.mkdir()
    good_bin.mkdir()
    old_marker = tmp_path / "old-python3-called"
    _write_executable(
        old_bin / "python3",
        "#!/bin/bash\n"
        f"touch {shlex.quote(str(old_marker))}\n"
        "echo OLD-PYTHON3 >&2\n"
        "exit 1\n",
    )
    (good_bin / "python3.10").symlink_to(Path(sys.executable))

    source = JOB.read_text(encoding="utf-8")
    snippet = _resolver_and_shim_snippet(source).replace(
        "for candidate in python3.10 /usr/bin/python3.10 /bin/python3.10; do",
        "for candidate in python3.10; do",
        1,
    ).replace(
        "scratch_base=/scr/$USER/p3-s4-loop-pegasus",
        f"scratch_base={shlex.quote(str(tmp_path / 'scratch-base'))}",
        1,
    ).replace(
        'SANITIZED_PATH="$shim_dir:/usr/bin:/bin"',
        f'SANITIZED_PATH="$shim_dir:{old_bin}:{good_bin}:/usr/bin:/bin"',
        1,
    )
    bootstrap = (
        f"export PATH={shlex.quote(str(old_bin) + os.pathsep + str(good_bin) + os.pathsep + '/usr/bin:/bin')}\n"
    )
    script = (
        "set -Eeuo pipefail\n"
        "refuse() { echo \"$1\" >&2; exit 2; }\n"
        f"repo={shlex.quote(str(REPO))}\n"
        "pbs_jobid_path_component=resolver-harness\n"
        + bootstrap
        + snippet
        + "\nprintf '%s\\n' \"$PY\"\n"
        + "command -v python3\n"
        + "python3 -c 'import sys; print(sys.executable)'\n"
    )
    completed = subprocess.run(
        ["bash", "-c", script], cwd=REPO,
        env=dict(os.environ), capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    selected_line, shim_line, executable_line = completed.stdout.splitlines()
    assert Path(selected_line).samefile(sys.executable)
    assert Path(shim_line).name == "python3"
    assert Path(shim_line).samefile(selected_line)
    assert Path(executable_line).samefile(selected_line)
    assert "OLD-PYTHON3" not in completed.stderr
    assert not old_marker.exists()

    bare_path_snippet = re.sub(
        r'(?m)^SANITIZED_PATH=.*$',
        'SANITIZED_PATH="$PATH"',
        snippet,
        count=1,
    )
    assert bare_path_snippet != snippet
    bare_path_script = (
        "set -Eeuo pipefail\n"
        "refuse() { echo \"$1\" >&2; exit 2; }\n"
        f"repo={shlex.quote(str(REPO))}\n"
        "pbs_jobid_path_component=bare-python3-mutant\n"
        + bootstrap
        + bare_path_snippet
        + "\ncommand -v python3\n"
        + "python3 -c 'raise SystemExit(0)'\n"
    )
    bare_path = subprocess.run(
        ["bash", "-c", bare_path_script], cwd=REPO,
        env=dict(os.environ), capture_output=True, text=True, check=False,
    )
    assert bare_path.returncode == 1
    assert bare_path.stdout.splitlines()[-1] == str(old_bin / "python3")
    assert bare_path.stderr == "OLD-PYTHON3\n"
    assert old_marker.is_file()


def test_pbs_jobid_path_sanitization_is_load_bearing() -> None:
    source = JOB.read_text(encoding="utf-8")
    fragment = 'pbs_jobid_path_component=${PBS_JOBID//:/_}'
    assert source.count(fragment) == 1
    assert 'scratch=$scratch_base/${PBS_JOBID}' not in source
    mutant = source.replace(fragment, 'pbs_jobid_path_component=$PBS_JOBID', 1)
    assert fragment not in mutant
    production_lines = [
        line.strip()
        for line in _shell_executable_surface(source).splitlines()
        if line.lstrip().startswith("pbs_jobid_path_component=")
    ]
    mutant_lines = [
        line.strip()
        for line in _shell_executable_surface(mutant).splitlines()
        if line.lstrip().startswith("pbs_jobid_path_component=")
    ]
    assert len(production_lines) == len(mutant_lines) == 1
    outputs = []
    for assignment in (production_lines[0], mutant_lines[0]):
        completed = subprocess.run(
            ["bash", "-c", (
                'PBS_JOBID="0:945411.nqsv"; '
                f"{assignment}; "
                'printf "%s\\n" "$pbs_jobid_path_component"'
            )],
            capture_output=True, text=True, check=True,
        )
        outputs.append(completed.stdout)
    assert outputs == ["0_945411.nqsv\n", "0:945411.nqsv\n"]


def test_login_host_refuses_before_sanitize_or_sentinels(tmp_path: Path) -> None:
    binary_dir = tmp_path / "bin"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    binary_dir.mkdir()
    evidence_root.mkdir()
    thirdparty_root.mkdir()
    hostname_marker = tmp_path / "hostname-called"
    _write_executable(
        binary_dir / "hostname",
        "#!/bin/bash\n"
        f"touch {shlex.quote(str(hostname_marker))}\n"
        "printf '%s\\n' pegasus01\n",
    )
    sentinel_markers = []
    for name in ("git", "cmake", "python3.10", "qstat"):
        marker = tmp_path / f"{name}-called"
        sentinel_markers.append(marker)
        _write_executable(
            binary_dir / name,
            "#!/bin/bash\n"
            f"touch {shlex.quote(str(marker))}\n"
            "exit 99\n",
        )
    fake_user = f"p3-s4-contract-{os.getpid()}-{tmp_path.name}"
    environment = dict(os.environ)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "USER": fake_user,
        "PBS_JOBID": "0:945411.nqsv",
        "PBS_NODEFILE": str(tmp_path / "nodefile"),
        "PBS_O_WORKDIR": str(REPO),
        "IZANAGI_S4_REPO_ROOT": str(REPO),
        "IZANAGI_S4_EXPECTED_HEAD": "1" * 40,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence_root),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty_root),
    })
    completed = subprocess.run(
        [str(JOB)], cwd=REPO, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert "P3 S4 loop job body is compute-only" in completed.stderr
    assert hostname_marker.is_file()
    assert not any(marker.exists() for marker in sentinel_markers)
    assert not (evidence_root / "compute-result.json").exists()
    assert not (evidence_root / "reservation.json").exists()
    assert not (evidence_root / "masstree-prebuild-receipt.json").exists()
    assert not (Path("/scr") / fake_user / "p3-s4-loop-pegasus").exists()


def test_superproject_status_failure_is_fail_closed(tmp_path: Path) -> None:
    binary_dir = tmp_path / "bin"
    git_stub_dir = tmp_path / "git-bin"
    repo_root = tmp_path / "repo"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    for path in (
        binary_dir, git_stub_dir, repo_root, evidence_root, thirdparty_root
    ):
        path.mkdir()
    (repo_root / "orchestrator").symlink_to(
        REPO / "orchestrator", target_is_directory=True
    )

    hostname_marker = tmp_path / "hostname-called"
    _write_executable(
        binary_dir / "hostname",
        "#!/bin/bash\n"
        f"touch {shlex.quote(str(hostname_marker))}\n"
        "printf '%s\\n' bnode001\n",
    )
    sentinel_markers = []
    for name in ("qstat", "cmake", "python3.10"):
        marker = tmp_path / f"{name}-called"
        sentinel_markers.append(marker)
        _write_executable(
            binary_dir / name,
            "#!/bin/bash\n"
            f"touch {shlex.quote(str(marker))}\n"
            "exit 99\n",
        )

    expected_head = "a" * 40
    git_common_dir = repo_root / ".git"
    git_status_marker = tmp_path / "git-status-called"
    unexpected_git_marker = tmp_path / "unexpected-git-called"
    _write_executable(
        git_stub_dir / "git",
        "#!/bin/bash\n"
        "case \"$*\" in\n"
        "  *\"rev-parse --path-format=absolute --git-common-dir\"*)\n"
        f"    printf '%s\\n' {shlex.quote(str(git_common_dir))}; exit 0 ;;\n"
        "  *\"rev-parse HEAD\"*)\n"
        f"    printf '%s\\n' {expected_head}; exit 0 ;;\n"
        "  *\"status --porcelain --untracked-files=no --ignore-submodules=all\"*)\n"
        f"    touch {shlex.quote(str(git_status_marker))}; exit 1 ;;\n"
        "  *)\n"
        f"    touch {shlex.quote(str(unexpected_git_marker))}; exit 99 ;;\n"
        "esac\n",
    )

    source = JOB.read_text(encoding="utf-8")
    bootstrap_anchor = (
        'export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"'
    )
    final_path_anchor = 'SANITIZED_PATH="$shim_dir:/usr/bin:/bin"'
    scratch_anchor = "scratch_base=/scr/$USER/p3-s4-loop-pegasus"
    assert source.count(bootstrap_anchor) == 1
    assert source.count(final_path_anchor) == 1
    assert source.count(scratch_anchor) == 1
    fixture_job = tmp_path / JOB.name
    _write_executable(
        fixture_job,
        source.replace(
            bootstrap_anchor,
            "export PATH=" + shlex.quote(
                str(git_stub_dir)
                + ":/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"
            ),
            1,
        ).replace(
            final_path_anchor,
            'SANITIZED_PATH="$shim_dir:' + str(git_stub_dir) + ':/usr/bin:/bin"',
            1,
        ).replace(
            scratch_anchor,
            f"scratch_base={shlex.quote(str(tmp_path / 'scratch-base'))}",
            1,
        ),
    )
    fake_user = f"p3-s4-status-contract-{os.getpid()}-{tmp_path.name}"
    environment = dict(os.environ)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "USER": fake_user,
        "PBS_JOBID": "0:945411.nqsv",
        "PBS_NODEFILE": str(tmp_path / "nodefile"),
        "PBS_O_WORKDIR": str(repo_root),
        "IZANAGI_S4_REPO_ROOT": str(repo_root),
        "IZANAGI_S4_EXPECTED_HEAD": expected_head,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence_root),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty_root),
    })
    completed = subprocess.run(
        [str(fixture_job)], cwd=REPO, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert "cannot inspect superproject tracked status" in completed.stderr
    assert hostname_marker.is_file()
    assert git_status_marker.is_file()
    assert not unexpected_git_marker.exists()
    assert not any(marker.exists() for marker in sentinel_markers)


def test_worktree_container_refuses_before_sentinels_or_artifacts(
    tmp_path: Path,
) -> None:
    binary_dir = tmp_path / "bin"
    repo_root = tmp_path / ".claude/worktrees/probe"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    binary_dir.mkdir()
    repo_root.mkdir(parents=True)
    evidence_root.mkdir()
    thirdparty_root.mkdir()

    hostname_marker = tmp_path / "hostname-called"
    _write_executable(
        binary_dir / "hostname",
        "#!/bin/bash\n"
        f"touch {shlex.quote(str(hostname_marker))}\n"
        "printf '%s\\n' bnode001\n",
    )
    sentinel_markers = []
    for name in ("git", "cmake", "python3.10", "qstat"):
        marker = tmp_path / f"{name}-called"
        sentinel_markers.append(marker)
        _write_executable(
            binary_dir / name,
            "#!/bin/bash\n"
            f"touch {shlex.quote(str(marker))}\n"
            "exit 99\n",
        )

    fake_user = f"p3-s4-worktree-contract-{os.getpid()}-{tmp_path.name}"
    environment = dict(os.environ)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "USER": fake_user,
        "PBS_JOBID": "0:945411.nqsv",
        "PBS_NODEFILE": str(tmp_path / "nodefile"),
        "PBS_O_WORKDIR": str(repo_root),
        "IZANAGI_S4_REPO_ROOT": str(repo_root),
        "IZANAGI_S4_EXPECTED_HEAD": "1" * 40,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence_root),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty_root),
    })
    completed = subprocess.run(
        [str(JOB)], cwd=REPO, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 2
    assert (
        "repository root must not be inside an AI worktree container"
        in completed.stderr
    )
    assert hostname_marker.is_file()
    assert not any(marker.exists() for marker in sentinel_markers)
    assert not (evidence_root / "compute-result.json").exists()
    assert not (evidence_root / "reservation.json").exists()
    assert not (evidence_root / "masstree-prebuild-receipt.json").exists()
    assert not (Path("/scr") / fake_user / "p3-s4-loop-pegasus").exists()


def test_claim_root_uses_the_campaign_pegasus_env_tag() -> None:
    env_tag = p3_s4_loop._SITE_ENV_TAGS[site_policy.PEGASUS_COMPUTE]
    source = JOB.read_text(encoding="utf-8")
    assert f'claim_root="$repo/output/env/{env_tag}/claims"' in source


def test_job_body_is_registered_only_as_dispatch_required() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))["entries"]
    assert registry["tools/pegasus/p3_s4_loop_pegasus.sh"] == {
        "class": "dispatch-required",
        "reason": "PBS P3 stage 4 loop build, verification, and benchmark job body",
        "primary_gate": "PBS allocation and job-body site preflight",
        "evidence": "static job-body classification",
    }


def test_readme_tagged_qsub_fence_routes_both_streams_to_evidence() -> None:
    source = README.read_text(encoding="utf-8")
    blocks = [
        block for block in re.findall(r"```bash\n(.*?)```", source, re.DOTALL)
        if "tools/pegasus/p3_s4_loop_pegasus.sh" in block
    ]
    assert len(blocks) == 1
    block = blocks[0]
    assert block.splitlines()[0] == "# admission-site: qsub-job-body"
    command_lines = [
        line for line in block.splitlines()
        if "qsub " in line and "tools/pegasus/p3_s4_loop_pegasus.sh" in line
    ]
    assert len(command_lines) == 1
    command = command_lines[0]
    assert '-o "$EVIDENCE_ROOT/$ATTEMPT/job.stdout"' in command
    assert '-e "$EVIDENCE_ROOT/$ATTEMPT/job.stderr"' in command


def test_job_body_mode_is_executable() -> None:
    assert os.stat(JOB).st_mode & 0o111


def test_job_body_has_valid_stdin_shell_syntax() -> None:
    source = _shell_body_without_heredocs(JOB.read_text(encoding="utf-8"))
    completed = subprocess.run(
        ["bash", "-n"], input=source, text=True,
        capture_output=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
