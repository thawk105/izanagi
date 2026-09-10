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
K2_ENV_NAMES = (
    "k2_env_names=(\n"
    "  IZANAGI_S4_KNOWLEDGE_MANIFEST\n"
    "  IZANAGI_S4_CODER_ROLE\n"
    "  IZANAGI_S4_KNOWLEDGE_CLASSIFICATION\n"
    "  IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM\n"
    ")"
)
K2_REQUIRED_ENV_NAMES = (
    "k2_required_env_names=(\n"
    "  IZANAGI_S4_KNOWLEDGE_MANIFEST\n"
    "  IZANAGI_S4_CODER_ROLE\n"
    ")"
)
K2_REQUIRED_ARGV = (
    "k2_argv=(\n"
    '    --knowledge-manifest "$IZANAGI_S4_KNOWLEDGE_MANIFEST"\n'
    '    --coder-role "$IZANAGI_S4_CODER_ROLE"\n'
    "  )"
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
        if re.match(r"^\s*#", line) is not None:
            output.append(line)
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
        "k2-environment-names": K2_ENV_NAMES,
        "k2-required-environment-names": K2_REQUIRED_ENV_NAMES,
        "k2-request-set-detection": (
            'for name in "${k2_env_names[@]}"; do\n'
            "  if [[ -v $name ]]; then\n"
            "    k2_requested=true\n"
            "    break\n"
            "  fi\n"
            "done"
        ),
        "k2-required-nonempty": (
            'for name in "${k2_required_env_names[@]}"; do\n'
            '    [[ -n "${!name:-}" ]] || '
            'refuse "missing K2 environment: $name"\n'
            "  done"
        ),
        "k2-required-argv": K2_REQUIRED_ARGV,
        "k2-optional-classification": (
            "if [[ -v IZANAGI_S4_KNOWLEDGE_CLASSIFICATION ]]; then\n"
            '    [[ -n "$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION" ]] \\\n'
            '      || refuse "empty K2 environment: '
            'IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"\n'
            "    k2_argv+=(\n"
            '      --knowledge-classification '
            '"$IZANAGI_S4_KNOWLEDGE_CLASSIFICATION"\n'
            "    )\n"
            "  fi"
        ),
        "k2-optional-de-novo": (
            "if [[ -v IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM ]]; then\n"
            '    [[ -n "$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM" ]] \\\n'
            '      || refuse "empty K2 environment: '
            'IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM"\n'
            "    k2_argv+=(\n"
            '      --knowledge-de-novo-claim '
            '"$IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM"\n'
            "    )\n"
            "  fi"
        ),
        "k2-proposal-required": (
            '[[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \\\n'
            '    || refuse "K2 environment requires '
            'IZANAGI_S4_PROPOSAL_PATH"'
        ),
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
        "scratch-tmpdir": "export TMPDIR=$scratch",
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
        "dependency-policy-path": "POLICY=$repo/tools/pegasus/policy.json",
        "dependency-policy-fields": (
            '"gflags_source_path",\n'
            '    "gflags_expected_head",\n'
            '    "glog_source_path",\n'
            '    "glog_expected_head",'
        ),
        "dependency-compilers": (
            "CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v g++)"
        ),
        "gflags-head-exact": (
            '"$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD"'
        ),
        "gflags-dirty-all": (
            'GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status '
            "--porcelain --untracked-files=all)"
        ),
        "gflags-install-root": 'GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"',
        "gflags-configure-root": (
            'gflags_configure_argv=(cmake -S "$GFLAGS_SOURCE_PATH" '
            '-B "$GFLAGS_BUILD_DIR"'
        ),
        "gflags-configure-definitions": (
            "-DCMAKE_POSITION_INDEPENDENT_CODE=ON "
            "-DREGISTER_INSTALL_PREFIX=OFF"
        ),
        "gflags-build-argv": (
            'gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)'
        ),
        "gflags-install-timeout": 'timeout 60 "${gflags_install_argv[@]}"',
        "glog-head-exact": '"$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD"',
        "glog-dirty-all": (
            'GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status '
            "--porcelain --untracked-files=all)"
        ),
        "glog-install-root": 'GLOG_INSTALL_DIR="$TMPDIR/glog-install"',
        "glog-configure-definitions": (
            '-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"'
        ),
        "glog-build-argv": (
            'glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)'
        ),
        "glog-install-timeout": 'timeout 120 "${glog_install_argv[@]}"',
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
        "prebuild-dependency-prefix": 'dependency_prefix=";".join(',
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
            '    "${k2_argv[@]}" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"'
        ),
        "fixture": (
            '--fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
            '    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"'
        ),
    }
    uncommented_source = "".join(
        line for line in source.splitlines(keepends=True)
        if re.match(r"^\s*#(?!PBS(?:\s|$))", line) is None
    )
    missing = [
        label for label, fragment in required.items()
        if fragment not in source
        or (label != "job-body-comment" and fragment not in uncommented_source)
    ]
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
    body = _shell_executable_surface(source)
    if "--no-build" in body:
        raise AssertionError("forbidden-no-build")

    allowed = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    sanitize = "unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE"
    allowed_prefix_lines = [
        sanitize,
        '-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"',
        allowed,
    ]
    prefix_lines = [
        line.strip() for line in body.splitlines()
        if "CMAKE_PREFIX_PATH" in line
    ]
    if prefix_lines != allowed_prefix_lines:
        raise AssertionError("forbidden-cmake-environment-injection")

    prefix_assignments = [
        line for line in body.splitlines()
        if re.search(r"(?<![-A-Za-z0-9_])CMAKE_PREFIX_PATH(?:\+)?=", line)
    ]
    if prefix_assignments != [allowed]:
        raise AssertionError("forbidden-cmake-environment-injection")

    prefix_unsets = [
        line.strip() for line in body.splitlines()
        if re.search(r"\bunset\b.*\bCMAKE_PREFIX_PATH\b", line)
    ]
    if prefix_unsets != [sanitize]:
        raise AssertionError("forbidden-cmake-environment-injection")

    singleton_order = (
        'timeout 60 "${gflags_install_argv[@]}"',
        'timeout 120 "${glog_install_argv[@]}"',
        allowed,
        '"$PY" - "$prebuild_receipt"',
    )
    if any(body.count(marker) != 1 for marker in singleton_order):
        raise AssertionError("forbidden-cmake-environment-injection")
    positions = [body.index(marker) for marker in singleton_order]
    if positions != sorted(positions) or body.index(sanitize) >= body.index(allowed):
        raise AssertionError("forbidden-cmake-environment-injection")

    driver = '"$PY" -B -m orchestrator.campaign.p3_s4_loop'
    driver_positions = [match.start() for match in re.finditer(re.escape(driver), body)]
    prebuild_position = body.index('"$PY" - "$prebuild_receipt"')
    if len(driver_positions) != 2 or any(
        position <= body.index(allowed) or position <= prebuild_position
        for position in driver_positions
    ):
        raise AssertionError("forbidden-cmake-environment-injection")

    forbidden_assignment = re.search(
        r"(?m)^\s*(?:export\s+)?(?:CMAKE_PROJECT_INCLUDE"
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
        "k2_env_names=(",
        'repo=$(cd -- "$IZANAGI_S4_REPO_ROOT"',
        "trap finish EXIT",
        "resolve_python() {",
        "\nresolve_python\n",
        "export TMPDIR=$scratch",
        'shim_dir=$scratch/python-shim',
        'export PATH="$SANITIZED_PATH"',
        "observed_head=$(git rev-parse HEAD)",
        "\ncampaign_pin=$(\n",
        "qstat_jobid=",
        'claim_root="$repo/output/env/',
        "POLICY=$repo/tools/pegasus/policy.json",
        'GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)',
        'timeout 60 "${gflags_install_argv[@]}"',
        'GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)',
        'timeout 120 "${glog_install_argv[@]}"',
        'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"',
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
        "policy file missing, not regular, or a symlink",
        "policy yielded an unexpected field count",
        "gflags source path missing",
        "gflags source HEAD mismatch",
        "gflags working tree is dirty",
        "glog source path missing",
        "glog source HEAD mismatch",
        "glog working tree is dirty",
        "scratch masstree source is not fresh",
        "masstree prebuild receipt is not fresh",
        "missing K2 environment: $name",
        "empty K2 environment: IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "empty K2 environment: IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
        "K2 environment requires IZANAGI_S4_PROPOSAL_PATH",
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
            '    "${k2_argv[@]}" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
            '--run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
            id="proposal",
        ),
        pytest.param(
            "k2-request-set-detection",
            "  if [[ -v $name ]]; then\n"
            "    k2_requested=true\n"
            "    break\n"
            "  fi",
            '  if [[ -n "${!name:-}" ]]; then\n'
            "    k2_requested=true\n"
            "    break\n"
            "  fi",
            id="k2-request-set-detection",
        ),
        pytest.param(
            "k2-proposal-required",
            '[[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \\\n'
            '    || refuse "K2 environment requires '
            'IZANAGI_S4_PROPOSAL_PATH"',
            "true # K2 proposal requirement removed",
            id="k2-proposal-required",
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
        pytest.param(
            "dependency-policy-path",
            "POLICY=$repo/tools/pegasus/policy.json",
            "POLICY=/tmp/policy.json",
            id="dependency-policy-path",
        ),
        pytest.param(
            "dependency-policy-fields",
            '"gflags_source_path",\n'
            '    "gflags_expected_head",\n'
            '    "glog_source_path",\n'
            '    "glog_expected_head",',
            '"gflags_source_path",\n'
            '    "gflags_expected_head",\n'
            '    "glog_source_path",\n'
            '    "glog_head",',
            id="dependency-policy-fields",
        ),
        pytest.param(
            "dependency-compilers",
            "CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v g++)",
            "CC_PATH=$(command -v gcc)\nCXX_PATH=$(command -v gcc)",
            id="dependency-compilers",
        ),
        pytest.param(
            "gflags-head-exact",
            '"$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD"',
            '"$GFLAGS_SOURCE_HEAD" != ""',
            id="gflags-head-exact",
        ),
        pytest.param(
            "gflags-dirty-all",
            'GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status '
            "--porcelain --untracked-files=all)",
            'GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status '
            "--porcelain --untracked-files=no)",
            id="gflags-dirty-all",
        ),
        pytest.param(
            "gflags-install-root",
            'GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"',
            'GFLAGS_INSTALL_DIR="/tmp/gflags-install"',
            id="gflags-install-root",
        ),
        pytest.param(
            "gflags-build-argv",
            'gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)',
            'gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 47)',
            id="gflags-build-argv",
        ),
        pytest.param(
            "glog-install-root",
            'GLOG_INSTALL_DIR="$TMPDIR/glog-install"',
            'GLOG_INSTALL_DIR="/tmp/glog-install"',
            id="glog-install-root",
        ),
        pytest.param(
            "glog-configure-definitions",
            '-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"',
            '-DWITH_UNWIND=ON "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"',
            id="glog-configure-definitions",
        ),
        pytest.param(
            "glog-install-timeout",
            'timeout 120 "${glog_install_argv[@]}"',
            'timeout 60 "${glog_install_argv[@]}"',
            id="glog-install-timeout",
        ),
        pytest.param(
            "prebuild-dependency-prefix",
            'dependency_prefix=";".join('
            "[gflags_install_dir, glog_install_dir]),",
            "# dependency prefix dropped",
            id="prebuild-dependency-prefix",
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
        pytest.param(
            'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR"',
            id="partial-prefix",
        ),
        pytest.param(
            'export CMAKE_PREFIX_PATH="$OTHER_GFLAGS:$OTHER_GLOG"',
            id="different-prefix-variables",
        ),
        pytest.param(
            'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"',
            id="second-exact-prefix",
        ),
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


def test_dependency_prefix_before_install_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    exact = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    anchor = 'timeout 120 "${glog_install_argv[@]}"'
    mutant = source.replace(exact + "\n", "", 1).replace(
        anchor, exact + "\n" + anchor, 1
    )
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_dependency_prefix_unset_after_export_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    exact = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    mutant = source.replace(exact, exact + "\nunset CMAKE_PREFIX_PATH", 1)
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_dependency_prefix_export_attribute_removal_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    exact = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    mutant = source.replace(exact, exact + "\nexport -n CMAKE_PREFIX_PATH", 1)
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_driver_dependency_prefix_removal_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    driver = '"$PY" -B -m orchestrator.campaign.p3_s4_loop'
    mutant = source.replace(
        driver,
        'env -u CMAKE_PREFIX_PATH ' + driver,
        1,
    )
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_comment_heredoc_cannot_mask_dependency_prefix_unset() -> None:
    source = JOB.read_text(encoding="utf-8")
    exact = 'export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"'
    mutant = source.replace(
        exact,
        exact + "\n# <<true\nunset CMAKE_PREFIX_PATH\ntrue",
        1,
    )
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_fixture_driver_before_prebuild_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    fixture_driver = (
        '  "$PY" -B -m orchestrator.campaign.p3_s4_loop \\\n'
        "    --allow-coder-derived-build \\\n"
        "    --isolate-worktree \\\n"
        '    --fetchcontent-prebuild-receipt "$prebuild_receipt" \\\n'
        '    --value "${IZANAGI_S4_FIXTURE_VALUE:-20}"'
    )
    prebuild = '"$PY" - "$prebuild_receipt"'
    assert source.count(fixture_driver) == 1
    assert source.count(prebuild) == 1
    mutant = source.replace(fixture_driver, "  true", 1).replace(
        prebuild,
        fixture_driver + "\n\n" + prebuild,
        1,
    )
    with pytest.raises(
        AssertionError, match="^forbidden-cmake-environment-injection$"
    ):
        _assert_forbidden_job_constructs(mutant)


def test_commented_dependency_policy_field_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    fragment = '    "gflags_source_path",'
    assert source.count(fragment) == 1
    mutant = source.replace(fragment, '    # "gflags_source_path",', 1)
    with pytest.raises(
        AssertionError, match="^job contract missing: dependency-policy-fields$"
    ):
        _assert_static_job_contract(mutant)


def test_commented_prebuild_dependency_prefix_is_rejected() -> None:
    source = JOB.read_text(encoding="utf-8")
    fragment = (
        '    dependency_prefix=";".join('
        "[gflags_install_dir, glog_install_dir]),"
    )
    assert source.count(fragment) == 1
    mutant = source.replace(fragment, "    # " + fragment.lstrip(), 1)
    with pytest.raises(
        AssertionError, match="^job contract missing: prebuild-dependency-prefix$"
    ):
        _assert_static_job_contract(mutant)


def test_exact_dependency_prefix_export_is_accepted() -> None:
    _assert_forbidden_job_constructs(JOB.read_text(encoding="utf-8"))


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


def _k2_preflight_environment(
    tmp_path: Path,
) -> tuple[dict[str, str], Path, Path, tuple[Path, ...]]:
    binary_dir = tmp_path / "bin"
    repo_root = tmp_path / "repo"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    binary_dir.mkdir()
    repo_root.mkdir()
    evidence_root.mkdir()
    thirdparty_root.mkdir()
    _write_executable(
        binary_dir / "hostname",
        "#!/bin/bash\nprintf '%s\\n' bnode001\n",
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

    source = JOB.read_text(encoding="utf-8")
    bootstrap_anchor = (
        'export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"'
    )
    assert source.count(bootstrap_anchor) == 1
    fixture_job = tmp_path / JOB.name
    _write_executable(
        fixture_job,
        source.replace(
            bootstrap_anchor,
            f'export PATH="{binary_dir}:/usr/bin:/bin:'
            '/opt/nec/nqsv/bin:/system/tool/bin"',
            1,
        ),
    )
    environment = dict(os.environ)
    for name in (
        "IZANAGI_S4_KNOWLEDGE_MANIFEST",
        "IZANAGI_S4_CODER_ROLE",
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
        "IZANAGI_S4_PROPOSAL_PATH",
    ):
        environment.pop(name, None)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "USER": f"p3-s4-k2-preflight-{os.getpid()}-{tmp_path.name}",
        "PBS_JOBID": "0:945411.nqsv",
        "PBS_NODEFILE": str(tmp_path / "nodefile"),
        "PBS_O_WORKDIR": str(repo_root),
        "IZANAGI_S4_REPO_ROOT": str(repo_root),
        "IZANAGI_S4_EXPECTED_HEAD": "1" * 40,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence_root),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty_root),
    })
    return environment, evidence_root, fixture_job, tuple(sentinel_markers)


def _run_actual_job_to_k2_preflight(
    tmp_path: Path,
    k2_environment: dict[str, str],
) -> tuple[subprocess.CompletedProcess[str], Path, tuple[Path, ...]]:
    environment, evidence_root, fixture_job, sentinel_markers = (
        _k2_preflight_environment(tmp_path)
    )
    environment.update(k2_environment)
    completed = subprocess.run(
        [str(fixture_job)], cwd=environment["IZANAGI_S4_REPO_ROOT"],
        env=environment,
        capture_output=True, text=True, check=False,
    )
    return completed, evidence_root, sentinel_markers


def test_set_empty_manifest_alone_is_refused_by_actual_job_body(
    tmp_path: Path,
) -> None:
    completed, evidence_root, sentinel_markers = _run_actual_job_to_k2_preflight(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "",
            "IZANAGI_S4_PROPOSAL_PATH": "/absolute/proposal.json",
        },
    )
    assert not any(marker.exists() for marker in sentinel_markers)
    assert completed.returncode == 2
    assert completed.stderr == (
        "p3 S4 loop job refused: missing K2 environment: "
        "IZANAGI_S4_KNOWLEDGE_MANIFEST\n"
    )
    assert not (evidence_root / "compute-result.json").exists()


def test_complete_k2_pair_without_proposal_is_refused_by_actual_job_body(
    tmp_path: Path,
) -> None:
    completed, evidence_root, sentinel_markers = _run_actual_job_to_k2_preflight(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
        },
    )
    assert not any(marker.exists() for marker in sentinel_markers)
    assert completed.returncode == 2
    assert completed.stderr == (
        "p3 S4 loop job refused: K2 environment requires "
        "IZANAGI_S4_PROPOSAL_PATH\n"
    )
    assert not (evidence_root / "compute-result.json").exists()


@pytest.mark.parametrize(
    "name",
    (
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
    ),
)
def test_set_empty_optional_k2_declaration_is_refused_by_actual_job_body(
    tmp_path: Path,
    name: str,
) -> None:
    completed, evidence_root, sentinel_markers = _run_actual_job_to_k2_preflight(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_PROPOSAL_PATH": "/absolute/proposal.json",
            name: "",
        },
    )
    assert not any(marker.exists() for marker in sentinel_markers)
    assert completed.returncode == 2
    assert completed.stderr == f"p3 S4 loop job refused: empty K2 environment: {name}\n"
    assert not (evidence_root / "compute-result.json").exists()


def _run_actual_job_body_through_driver(
    tmp_path: Path,
    k2_environment: dict[str, str],
) -> list[str]:
    binary_dir = tmp_path / "bin"
    repo_root = tmp_path / "repo"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    gflags_source = tmp_path / "gflags-source"
    glog_source = tmp_path / "glog-source"
    driver_argv = tmp_path / "driver-argv.json"
    for path in (
        binary_dir,
        repo_root / "external/ccbench",
        repo_root / "tools/pegasus",
        evidence_root,
        thirdparty_root / "masstree",
        thirdparty_root / "mimalloc",
        thirdparty_root / "googletest",
        gflags_source,
        glog_source,
    ):
        path.mkdir(parents=True, exist_ok=True)

    expected_head = "e" * 40
    gflags_head = "b" * 40
    glog_head = "c" * 40
    ccbench_head = "511c9538e4e8efa54b45cda62e72389ed3b706ec"
    (repo_root / "tools/pegasus/policy.json").write_text("{}\n", encoding="utf-8")

    _write_executable(
        binary_dir / "hostname",
        "#!/bin/bash\nprintf '%s\\n' bnode001\n",
    )
    _write_executable(binary_dir / "timeout", "#!/bin/bash\nexit 0\n")
    _write_executable(binary_dir / "gcc", "#!/bin/bash\nexit 0\n")
    _write_executable(binary_dir / "g++", "#!/bin/bash\nexit 0\n")
    _write_executable(
        binary_dir / "qstat",
        "#!/bin/bash\nprintf '%s\\n' 'stub scheduler observation'\n",
    )
    _write_executable(
        binary_dir / "git",
        "#!/usr/bin/python3\n"
        "import sys\n"
        "args = sys.argv[1:]\n"
        "joined = ' '.join(args)\n"
        "if '--git-common-dir' in args:\n"
        f"    print({str(repo_root / '.git')!r})\n"
        "elif 'status' in args:\n"
        "    pass\n"
        "elif 'rev-parse' in args:\n"
        "    if 'gflags-source' in joined:\n"
        f"        print({gflags_head!r})\n"
        "    elif 'glog-source' in joined:\n"
        f"        print({glog_head!r})\n"
        "    elif 'external/ccbench' in joined:\n"
        f"        print({ccbench_head!r})\n"
        "    elif 'thirdparty' in joined:\n"
        "        print('a' * 40)\n"
        "    else:\n"
        f"        print({expected_head!r})\n"
        "else:\n"
        "    raise SystemExit(99)\n",
    )
    _write_executable(
        binary_dir / "python3.10",
        "#!/usr/bin/python3\n"
        "import json\n"
        "import os\n"
        "import sys\n"
        "from pathlib import Path\n"
        "args = sys.argv[1:]\n"
        "if '-m' in args:\n"
        "    Path(os.environ['IZANAGI_TEST_DRIVER_ARGV']).write_text(\n"
        "        json.dumps(args), encoding='utf-8')\n"
        "elif '-c' in args:\n"
        "    code = args[-1]\n"
        "    if 'print(os.path.realpath(sys.executable))' in code:\n"
        "        print(Path(__file__).resolve())\n"
        "    elif 'from orchestrator.campaign.p3_s4_loop import PIN' in code:\n"
        "        print('511c9538e4e8efa54b45cda62e72389ed3b706ec')\n"
        "elif args[:3] == ['-I', '-B', '-']:\n"
        "    print(os.environ['IZANAGI_TEST_GFLAGS_SOURCE'])\n"
        "    print(os.environ['IZANAGI_TEST_GFLAGS_HEAD'])\n"
        "    print(os.environ['IZANAGI_TEST_GLOG_SOURCE'])\n"
        "    print(os.environ['IZANAGI_TEST_GLOG_HEAD'])\n"
        "elif args and args[0] == '-' and len(args) == 2:\n"
        "    print('1000')\n"
        "    print('10800')\n"
        "elif args and args[0] == '-' and len(args) == 4:\n"
        "    Path(args[1]).write_text('{}\\n', encoding='utf-8')\n"
        "elif args and args[0] == '-' and len(args) > 4:\n"
        "    Path(args[5], 'config.h').write_text('stub\\n', encoding='utf-8')\n"
        "    Path(args[1]).write_text('{}\\n', encoding='utf-8')\n"
        "else:\n"
        "    raise SystemExit(99)\n",
    )

    source = JOB.read_text(encoding="utf-8")
    bootstrap_anchor = 'export PATH="/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"'
    final_path_anchor = 'SANITIZED_PATH="$shim_dir:/usr/bin:/bin"'
    scratch_anchor = "scratch_base=/scr/$USER/p3-s4-loop-pegasus"
    assert source.count(bootstrap_anchor) == 1
    assert source.count(final_path_anchor) == 1
    assert source.count(scratch_anchor) == 1
    job = repo_root / "tools/pegasus/p3_s4_loop_pegasus.sh"
    _write_executable(
        job,
        source.replace(
            bootstrap_anchor,
            f'export PATH="{binary_dir}:/usr/bin:/bin:/opt/nec/nqsv/bin:/system/tool/bin"',
            1,
        ).replace(
            final_path_anchor,
            f'SANITIZED_PATH="$shim_dir:{binary_dir}:/usr/bin:/bin"',
            1,
        ).replace(
            scratch_anchor,
            f"scratch_base={shlex.quote(str(tmp_path / 'scratch-base'))}",
            1,
        ),
    )

    environment = dict(os.environ)
    for name in (
        "IZANAGI_S4_KNOWLEDGE_MANIFEST",
        "IZANAGI_S4_CODER_ROLE",
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
        "IZANAGI_S4_PROPOSAL_PATH",
    ):
        environment.pop(name, None)
    environment.update({
        "PATH": str(binary_dir) + os.pathsep + environment["PATH"],
        "USER": f"p3-s4-k2-contract-{os.getpid()}-{tmp_path.name}",
        "PBS_JOBID": "0:945411.nqsv",
        "PBS_NODEFILE": str(tmp_path / "nodefile"),
        "PBS_O_WORKDIR": str(repo_root),
        "IZANAGI_S4_REPO_ROOT": str(repo_root),
        "IZANAGI_S4_EXPECTED_HEAD": expected_head,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence_root),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty_root),
        "IZANAGI_TEST_DRIVER_ARGV": str(driver_argv),
        "IZANAGI_TEST_GFLAGS_SOURCE": str(gflags_source),
        "IZANAGI_TEST_GFLAGS_HEAD": gflags_head,
        "IZANAGI_TEST_GLOG_SOURCE": str(glog_source),
        "IZANAGI_TEST_GLOG_HEAD": glog_head,
        **k2_environment,
    })
    completed = subprocess.run(
        [str(job)], cwd=repo_root, env=environment,
        capture_output=True, text=True, check=False,
    )
    assert completed.returncode == 0, completed.stderr
    assert (evidence_root / "compute-result.json").is_file()
    return json.loads(driver_argv.read_text(encoding="utf-8"))


def test_complete_k2_environment_reaches_actual_job_driver_argv(
    tmp_path: Path,
) -> None:
    knowledge_manifest = "/absolute/knowledge manifest.json"
    proposal = "/absolute/proposal.json"
    argv = _run_actual_job_body_through_driver(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": knowledge_manifest,
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "reproduction_or_selection",
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false",
            "IZANAGI_S4_PROPOSAL_PATH": proposal,
        },
    )
    assert argv == [
        "-B", "-m", "orchestrator.campaign.p3_s4_loop",
        "--allow-coder-derived-build",
        "--isolate-worktree",
        "--fetchcontent-prebuild-receipt",
        str(tmp_path / "evidence/masstree-prebuild-receipt.json"),
        "--knowledge-manifest", knowledge_manifest,
        "--coder-role", "coder-v4-autonomous-k2",
        "--knowledge-classification", "reproduction_or_selection",
        "--knowledge-de-novo-claim", "false",
        "--run-iteration", proposal,
    ]


def test_omitted_optional_k2_declarations_add_no_driver_argv(
    tmp_path: Path,
) -> None:
    argv = _run_actual_job_body_through_driver(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_PROPOSAL_PATH": "/absolute/proposal.json",
        },
    )
    assert "--knowledge-manifest" in argv
    assert "--coder-role" in argv
    assert "--knowledge-classification" not in argv
    assert "--knowledge-de-novo-claim" not in argv


def test_k2_argv_expansion_is_proposal_only() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert source.count('    "${k2_argv[@]}" \\\n') == 1
    proposal_start = source.index(
        'if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]'
    )
    fixture_start = source.index("\nelse\n", proposal_start)
    assert '"${k2_argv[@]}"' in source[proposal_start:fixture_start]
    assert '"${k2_argv[@]}"' not in source[fixture_start:]


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
    for name in (
        "IZANAGI_S4_PROPOSAL_PATH",
        "IZANAGI_S4_KNOWLEDGE_MANIFEST",
        "IZANAGI_S4_CODER_ROLE",
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
    ):
        assert command.count(f"{name}=") == 1


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
