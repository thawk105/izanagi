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


STOCK_PINS = {
    "stock-default-off": '${IZANAGI_S4_STOCK_CONTROL-0}',
    "stock-mode": 'pair_argv=(--stock-control)',
    "pair-argv": '"${pair_argv[@]}"',
    "fixture-pair-refusal": 'refuse "IZANAGI_S4_STOCK_CONTROL=1 requires IZANAGI_S4_PROPOSAL_PATH"',
    "proposal-status-capture": (
        '--run-iteration "$IZANAGI_S4_PROPOSAL_PATH" || candidate_rc=$?'
    ),
    "fixture-status-capture": (
        '--value "${IZANAGI_S4_FIXTURE_VALUE:-20}" || candidate_rc=$?'
    ),
    "driver-status": 'exit "$candidate_rc"',
}

B5_PINS = {
    "b5-mode-set": 'if [[ -v IZANAGI_S4_B5_MODE ]]; then',
    "b5-mode-values": '*) refuse "IZANAGI_S4_B5_MODE must be series or block-stock" ;;',
    "b5-required": '[[ -n "${!name:-}" ]] || refuse "missing B-5 environment: $name"',
    "b5-arm": 'series:llm|series:random|series:sweep-matched|block-stock:stock) ;;',
    "b5-workload": 'write-heavy|balanced|read-heavy) ;;',
    "b5-series": '[[ "$IZANAGI_S4_B5_SERIES" =~ ^([1-9]|1[0-2])$ ]]',
    "b5-block": '[[ "$IZANAGI_S4_B5_BLOCK" =~ ^[1-3]$ ]]',
    "b5-ledger-absolute": '[[ "$IZANAGI_S4_B5_LEDGER_ROOT" == /* ]]',
    "b5-exclusive": 'refuse "B-5 mode excludes proposal, fixture, and stock-control"',
    "b5-partial": '[[ ! -v $name ]] || refuse "B-5 environment requires IZANAGI_S4_B5_MODE"',
    "b5-llm-k2": '[[ -n "${!name:-}" ]] || refuse "B-5 llm requires K2 environment: $name"',
    "b5-non-llm-k2": 'refuse "B-5 non-llm arm excludes K2 environment"',
    "b5-ledger-outside": 'refuse "B-5 ledger root resolves inside a repository"',
    "b5-command": 'b5_argv=("run-$b5_mode")',
    "b5-series-argv": 'b5_argv+=(--arm "$IZANAGI_S4_B5_ARM" --series "$IZANAGI_S4_B5_SERIES")',
    "b5-common-argv": (
        'b5_argv+=(--workload "$IZANAGI_S4_B5_WORKLOAD" --block "$IZANAGI_S4_B5_BLOCK"\n'
        '    --ledger-root "$b5_ledger_root" --fetchcontent-prebuild-receipt "$prebuild_receipt")'
    ),
    "b5-driver": '"$PY" -B -m orchestrator.campaign.b5_generator_contrast "${b5_argv[@]}"',
    "b5-status": '|| b5_rc=$?',
    "b5-exit": 'exit "$b5_rc"',
}


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
            '[[ ( "$b5_mode" == series && "${IZANAGI_S4_B5_ARM-}" == llm ) \\\n'
            '     || -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \\\n'
            '    || refuse "K2 environment requires '
            'IZANAGI_S4_PROPOSAL_PATH"'
        ),
        "canonical-repo": 'repo=$(cd -- "$IZANAGI_S4_REPO_ROOT" && pwd -P)',
        "canonical-evidence-export": 'export IZANAGI_S4_EVIDENCE_ROOT="$evidence_root"',
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
        "dependency-hydrated-sources": (
            'THIRDPARTY_SOURCE_ROOT="$IZANAGI_S4_THIRDPARTY_SOURCE_ROOT"\n'
            'GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"\n'
            'GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"'
        ),
        "dependency-policy-fields": (
            '"gflags_expected_head",\n'
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
        # Each branch owns its receipt; argv expansions have separate pins,
        # and the status-capture pins own --run-iteration / --value and status.
        "proposal": '--fetchcontent-prebuild-receipt "$prebuild_receipt"',
        "fixture": '--fetchcontent-prebuild-receipt "$prebuild_receipt"',
    }
    required.update(STOCK_PINS)
    required.update(B5_PINS)
    uncommented_source = "".join(
        line for line in source.splitlines(keepends=True)
        if re.match(r"^\s*#(?!PBS(?:\s|$))", line) is None
    )
    def pin_surface(label: str, text: str) -> str:
        if label in ("proposal", "fixture"):
            # The other branch's identical receipt must not hide its removal.
            # Keep receipt pins independent of argv and status-capture pins.
            branches = text.partition(
                'if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]; then\n'
            )[2].partition("\nelse\n")
            return (branches[0] if label == "proposal"
                    else branches[2].partition("\nfi\n")[0])
        return text

    missing = [
        label for label, fragment in required.items()
        if fragment not in pin_surface(label, source)
        or (label != "job-body-comment"
            and fragment not in pin_surface(label, uncommented_source))
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
    driver_positions = [match.start() for match in re.finditer(
        re.escape(driver) + r"(?=\s)", body)]
    prebuild_position = body.index('"$PY" - "$prebuild_receipt"')
    if len(driver_positions) != 2 or any(
        position <= body.index(allowed) or position <= prebuild_position
        for position in driver_positions
    ):
        raise AssertionError("forbidden-cmake-environment-injection")

    b5_driver = '"$PY" -B -m orchestrator.campaign.b5_generator_contrast'
    if body.count(b5_driver) != 1 or not (
        prebuild_position < body.index(b5_driver) < min(driver_positions)
    ):
        raise AssertionError("b5-driver-count-or-order")

    policy_driver = '"$PY" -B -m orchestrator.campaign.p3_s4_loop_policy'
    policy_positions = [match.start() for match in re.finditer(
        re.escape(policy_driver) + r"(?=\s)", body)]
    if len(policy_positions) != 1 or policy_positions[0] <= prebuild_position:
        raise AssertionError("policy-driver-count-or-order")

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
        'b5_mode=${IZANAGI_S4_B5_MODE-}',
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
        'b5_argv=("run-$b5_mode")',
        '"$PY" -B -m orchestrator.campaign.b5_generator_contrast',
        'if [[ -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]]',
        '"${k2_argv[@]}" "${pair_argv[@]}"',
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
            '    "${k2_argv[@]}" "${pair_argv[@]}" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
            '    "${k2_argv[@]}" "${pair_argv[@]}" \\\n'
            '    --run-iteration "$IZANAGI_S4_PROPOSAL_PATH"',
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
            '[[ ( "$b5_mode" == series && "${IZANAGI_S4_B5_ARM-}" == llm ) \\\n'
            '     || -n "${IZANAGI_S4_PROPOSAL_PATH:-}" ]] \\\n'
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
            '"gflags_expected_head",\n'
            '    "glog_expected_head",',
            '"gflags_expected_head",\n'
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
    fragment = '    "gflags_expected_head",'
    assert source.count(fragment) == 1
    mutant = source.replace(fragment, '    # "gflags_expected_head",', 1)
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
    for name in list(environment):
        if name.startswith(("IZANAGI_S4_B5_", "IZANAGI_S4_T2849_", "IZANAGI_S4_POLICY_")) or name == "IZANAGI_S4_FIXTURE_VALUE":
            environment.pop(name)
    for name in (
        "IZANAGI_S4_KNOWLEDGE_MANIFEST",
        "IZANAGI_S4_CODER_ROLE",
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
        "IZANAGI_S4_PROPOSAL_PATH",
        "IZANAGI_S4_STOCK_CONTROL",
        "IZANAGI_TRACE_ARCHIVE_ROOT",
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
    *,
    relative_evidence: bool = False,
    driver_rcs: tuple[int, int] = (0, 0),
    source_override: str | None = None,
    ccbench_head: str | None = None,
    expect_driver: bool = True,
    git_common_repo: Path | None = None,
    expected_stderr: str | None = None,
) -> tuple[list[list[str]], int, dict]:
    # Scheduler/build/driver work is simulated; shell path conversion and the
    # Python driver's environment/path observation and file write are real.
    binary_dir = tmp_path / "bin"
    repo_root = tmp_path / "repo"
    evidence_root = tmp_path / "evidence"
    thirdparty_root = tmp_path / "thirdparty"
    gflags_source = thirdparty_root / "gflags"
    glog_source = thirdparty_root / "glog"
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
    if ccbench_head is None:
        ccbench_head = ("68106660686232781bca3be792a750d3e19d7a8a"
                        if k2_environment.get("IZANAGI_S4_POLICY_MODE")
                        else "68106660686232781bca3be792a750d3e19d7a8a"
                        if k2_environment.get("IZANAGI_S4_T2849_MODE")
                        and k2_environment.get("IZANAGI_S4_T2849_PROTOCOL") == "mocc"
                        else "511c9538e4e8efa54b45cda62e72389ed3b706ec")
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
        f"    print({str((git_common_repo or repo_root) / '.git')!r})\n"
        "elif 'status' in args:\n"
        "    pass\n"
        "elif 'rev-parse' in args:\n"
        f"    if args[:2] == ['-C', {str(gflags_source)!r}]:\n"
        f"        print({gflags_head!r})\n"
        f"    elif args[:2] == ['-C', {str(glog_source)!r}]:\n"
        f"        print({glog_head!r})\n"
        "    elif 'external/ccbench' in joined:\n"
        "        if any('511c9538e4e8efa54b45cda62e72389ed3b706ec' in a for a in args):\n"
        "            print('511c9538e4e8efa54b45cda62e72389ed3b706ec')\n"
        "        elif any('6810666' in a for a in args):\n"
        "            print('68106660686232781bca3be792a750d3e19d7a8a')\n"
        "        else:\n"
        f"            print({ccbench_head!r})\n"
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
        "    with Path(os.environ['IZANAGI_TEST_DRIVER_ARGV']).open('a') as stream:\n"
        "        stream.write(json.dumps(args) + '\\n')\n"
        "    with Path(os.environ['IZANAGI_TEST_DRIVER_ENV']).open('a') as stream:\n"
        "        stream.write(json.dumps({\n"
        "            'TMPDIR': os.environ.get('TMPDIR'),\n"
        "            'IZANAGI_BENCH_LOCK': os.environ.get('IZANAGI_BENCH_LOCK'),\n"
        "        }) + '\\n')\n"
        "    if args[args.index('-m') + 1] == 'orchestrator.campaign.p3_s4_loop_policy':\n"
        "        with Path(os.environ['IZANAGI_TEST_POLICY_ARCHIVE']).open('a') as stream:\n"
        "            stream.write(json.dumps(os.environ.get('IZANAGI_TRACE_ARCHIVE_ROOT')) + '\\n')\n"
        "    root = os.environ['IZANAGI_S4_EVIDENCE_ROOT']\n"
        "    Path(root, 'driver-evidence.json').write_text(\n"
        "        json.dumps({'root': root, 'cwd': str(Path.cwd()),\n"
        "                    'resolved_root': str(Path(root).resolve())}),\n"
        "        encoding='utf-8')\n"
        "    rcs = json.loads(os.environ['IZANAGI_TEST_DRIVER_RCS'])\n"
        "    raise SystemExit(rcs[0])\n"
        "elif '-c' in args:\n"
        "    code = args[-1]\n"
        "    if 'print(os.path.realpath(sys.executable))' in code:\n"
        "        print(Path(__file__).resolve())\n"
        "    elif 'campaign_pin_for_protocol' in code:\n"
        "        print('68106660686232781bca3be792a750d3e19d7a8a')\n"
        "    elif 'from orchestrator.campaign.p3_s4_loop import PIN' in code:\n"
        "        print('511c9538e4e8efa54b45cda62e72389ed3b706ec')\n"
        "    elif 'from orchestrator.campaign.axis_silo_function_policy import PIN' in code:\n"
        "        print('6810666')\n"
        "elif args[:3] == ['-I', '-B', '-']:\n"
        "    print(os.environ['IZANAGI_TEST_GFLAGS_HEAD'])\n"
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

    source = JOB.read_text(encoding="utf-8") if source_override is None else source_override
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
    for name in list(environment):
        if name.startswith(("IZANAGI_S4_B5_", "IZANAGI_S4_T2849_", "IZANAGI_S4_POLICY_")) or name == "IZANAGI_S4_FIXTURE_VALUE":
            environment.pop(name)
    for name in (
        "IZANAGI_S4_KNOWLEDGE_MANIFEST",
        "IZANAGI_S4_CODER_ROLE",
        "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION",
        "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM",
        "IZANAGI_S4_PROPOSAL_PATH",
        "IZANAGI_S4_STOCK_CONTROL",
        "IZANAGI_TRACE_ARCHIVE_ROOT",
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
        "IZANAGI_TEST_DRIVER_ENV": str(tmp_path / "driver-env.jsonl"),
        "IZANAGI_TEST_POLICY_ARCHIVE": str(tmp_path / "policy-archive.jsonl"),
        "IZANAGI_TEST_DRIVER_RCS": json.dumps(driver_rcs),
        "IZANAGI_TEST_GFLAGS_HEAD": gflags_head,
        "IZANAGI_TEST_GLOG_HEAD": glog_head,
        **k2_environment,
    })
    environment.pop("IZANAGI_BENCH_LOCK", None)
    input_root = "./evidence" if relative_evidence else str(evidence_root)
    environment["IZANAGI_S4_EVIDENCE_ROOT"] = input_root
    expected_root = (tmp_path / input_root).resolve()
    completed = subprocess.run(
        [str(job)], cwd=tmp_path, env=environment,
        capture_output=True, text=True, check=False,
    )
    result_path = evidence_root / "compute-result.json"
    if expected_stderr is None:
        assert result_path.is_file()
    else:
        assert completed.stderr == expected_stderr
        assert not result_path.exists()
    if expect_driver:
        assert json.loads((expected_root / "driver-evidence.json").read_text(
            encoding="utf-8",
        )) == {
            "root": str(expected_root),
            "cwd": str(repo_root.resolve()),
            "resolved_root": str(expected_root),
        }
    else:
        assert not (expected_root / "driver-evidence.json").exists()
    return (
        [json.loads(line) for line in driver_argv.read_text(encoding="utf-8").splitlines()]
        if driver_argv.exists() else [],
        completed.returncode,
        json.loads(result_path.read_text()) if expected_stderr is None else {},
    )


def _read_driver_environment(tmp_path: Path) -> list[dict[str, str | None]]:
    return [
        json.loads(line)
        for line in (tmp_path / "driver-env.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def _read_policy_archive(tmp_path: Path) -> list[str | None]:
    return [
        json.loads(line)
        for line in (tmp_path / "policy-archive.jsonl").read_text(encoding="utf-8").splitlines()
    ]


@pytest.mark.parametrize("mode,action", [
    ("stock", ["--stock-baseline"]),
    ("pair", ["--allow-coder-derived-build", "--run-iteration",
              "/absolute/policy proposal.json", "--stock-control"]),
    ("replay", ["--allow-coder-derived-build", "--replay-proposal",
                "/absolute/policy proposal.json"]),
    ("contrast", ["--allow-coder-derived-build", "--contrast-run-unit",
                  "/absolute/unit.json"]),
])
def test_policy_actual_job_argv_archive_and_lock(tmp_path, mode, action):
    archive = tmp_path / "archive"
    env = {
        "IZANAGI_S4_POLICY_MODE": mode,
        "IZANAGI_S4_POLICY_FORM": "cpp",
        "IZANAGI_TRACE_ARCHIVE_ROOT": str(archive),
    }
    if mode != "stock":
        if mode == "contrast":
            env["IZANAGI_S4_POLICY_UNIT_PATH"] = "/absolute/unit.json"
        else:
            env["IZANAGI_S4_POLICY_PROPOSAL_PATH"] = "/absolute/policy proposal.json"
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    receipt = str(tmp_path / "evidence/masstree-prebuild-receipt.json")
    assert history == [[
        "-B", "-m", "orchestrator.campaign.p3_s4_loop_policy",
        "--form", "cpp", "--campaign-env", "pegasus",
        "--fetchcontent-prebuild-receipt", receipt, *action,
    ]]
    assert Path(receipt).is_file()
    assert rc == result["driver_rc"] == 0
    assert _read_driver_environment(tmp_path) == [{
        "TMPDIR": str(tmp_path / "scratch-base/0_945411.nqsv"),
        "IZANAGI_BENCH_LOCK": str(tmp_path / "scratch-base/0_945411.nqsv/bench.lock"),
    }]
    assert _read_policy_archive(tmp_path) == [str(archive)]


@pytest.mark.parametrize('extra', [{},
    {'IZANAGI_S4_POLICY_UNIT_PATH': 'relative/unit.json'},
    {'IZANAGI_S4_POLICY_UNIT_PATH': '/absolute/unit.json',
     'IZANAGI_S4_POLICY_PROPOSAL_PATH': '/absolute/proposal.json'}])
def test_policy_contrast_requires_exclusive_absolute_unit(tmp_path, extra):
    env = {'IZANAGI_S4_POLICY_MODE': 'contrast',
           'IZANAGI_S4_POLICY_FORM': 'ir', **extra}
    reason = ('S4 policy contrast excludes proposal path'
              if 'IZANAGI_S4_POLICY_PROPOSAL_PATH' in extra
              else 'S4 policy contrast requires absolute unit path')
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, env, expected_stderr=f'p3 S4 loop job refused: {reason}\n',
        expect_driver=False)
    assert rc == 2
    assert not history


def test_policy_actual_job_uses_policy_pin(tmp_path):
    env = {
        "IZANAGI_S4_POLICY_MODE": "stock",
        "IZANAGI_S4_POLICY_FORM": "ir",
        "IZANAGI_TRACE_ARCHIVE_ROOT": str(tmp_path / "archive"),
    }
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    assert len(history) == 1 and rc == result["driver_rc"] == 0


@pytest.mark.parametrize("archive", [None, "relative/archive", "repo/archive", "repo/../repo/archive"])
def test_policy_archive_root_is_required_outside_repository(tmp_path, archive):
    env = {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "cpp"}
    if archive is not None:
        env["IZANAGI_TRACE_ARCHIVE_ROOT"] = (
            str(tmp_path / archive) if archive.startswith("repo/") else archive)
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, env, expect_driver=False,
        expected_stderr=(
            "p3 S4 loop job refused: S4 policy trace archive root must be absolute\n"
            if archive is None or not archive.startswith("repo/") else
            "p3 S4 loop job refused: S4 policy trace archive root resolves inside a repository\n"
        ),
    )
    assert history == [] and rc == 2 and result == {}


def test_policy_archive_root_excludes_git_common_repository(tmp_path):
    common_repo = tmp_path / "shared-repository"
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path,
        {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "cpp",
         "IZANAGI_TRACE_ARCHIVE_ROOT": str(common_repo / "archive")},
        git_common_repo=common_repo, expect_driver=False,
        expected_stderr="p3 S4 loop job refused: S4 policy trace archive root resolves inside a repository\n",
    )
    assert history == [] and rc == 2 and result == {}


@pytest.mark.parametrize("extra", [
    {"IZANAGI_S4_T2849_MODE": "series", "IZANAGI_S4_T2849_COHORT": "x",
     "IZANAGI_S4_T2849_COHORT_ROOT": "/tmp/cohort", "IZANAGI_S4_T2849_WORKLOAD": "write-heavy",
     "IZANAGI_S4_T2849_BLOCK": "1", "IZANAGI_S4_T2849_N_EVAL": "1",
     "IZANAGI_S4_T2849_ARM": "x", "IZANAGI_S4_T2849_SERIES": "1",
     "IZANAGI_S4_T2849_A_LIMIT": "1", "IZANAGI_S4_T2849_B_LIMIT": "1"},
    {"IZANAGI_S4_B5_MODE": "block-stock", "IZANAGI_S4_B5_ARM": "stock",
     "IZANAGI_S4_B5_WORKLOAD": "write-heavy", "IZANAGI_S4_B5_SERIES": "1",
     "IZANAGI_S4_B5_BLOCK": "1", "IZANAGI_S4_B5_LEDGER_ROOT": "/tmp/ledger"},
    {"IZANAGI_S4_KNOWLEDGE_MANIFEST": "/tmp/manifest",
     "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
     "IZANAGI_S4_PROPOSAL_PATH": "/tmp/old-proposal"},
    {"IZANAGI_S4_PROPOSAL_PATH": "/tmp/old-proposal"},
    {"IZANAGI_S4_FIXTURE_VALUE": "20"},
    {"IZANAGI_S4_STOCK_CONTROL": "0"},
])
def test_policy_excludes_existing_mode_environment_before_repository(tmp_path, extra):
    env = {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "cpp", **extra}
    completed, evidence, sentinels = _run_actual_job_to_k2_preflight(tmp_path, env)
    assert completed.returncode == 2
    assert not any(path.exists() for path in sentinels)
    assert not (evidence / "compute-result.json").exists()


@pytest.mark.parametrize("env", [
    {"IZANAGI_S4_POLICY_FORM": "cpp"},
    {"IZANAGI_S4_POLICY_PROPOSAL_PATH": "/tmp/proposal"},
    {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "cpp",
     "IZANAGI_S4_POLICY_PROPOSAL_PATH": ""},
    {"IZANAGI_S4_POLICY_MODE": "pair", "IZANAGI_S4_POLICY_FORM": "cpp"},
    {"IZANAGI_S4_POLICY_MODE": "replay", "IZANAGI_S4_POLICY_FORM": "ir",
     "IZANAGI_S4_POLICY_PROPOSAL_PATH": ""},
    {"IZANAGI_S4_POLICY_MODE": "invalid", "IZANAGI_S4_POLICY_FORM": "cpp"},
    {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "invalid"},
])
def test_policy_mode_and_proposal_shape_refused_before_repository(tmp_path, env):
    completed, evidence, sentinels = _run_actual_job_to_k2_preflight(tmp_path, env)
    assert completed.returncode == 2
    assert not any(path.exists() for path in sentinels)
    assert not (evidence / "compute-result.json").exists()


@pytest.mark.parametrize("driver_rc", [0, 7])
def test_policy_driver_status_is_job_status(tmp_path, driver_rc):
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path,
        {"IZANAGI_S4_POLICY_MODE": "stock", "IZANAGI_S4_POLICY_FORM": "cpp",
         "IZANAGI_TRACE_ARCHIVE_ROOT": str(tmp_path / "archive")},
        driver_rcs=(driver_rc, 99),
    )
    assert len(history) == 1 and rc == result["driver_rc"] == driver_rc


@pytest.mark.parametrize("relative_evidence", [True, False], ids=["relative", "absolute"])
def test_evidence_root_reaches_actual_job_driver_as_canonical_path(
    tmp_path: Path, relative_evidence: bool,
) -> None:
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, {}, relative_evidence=relative_evidence,
    )
    assert rc == result["driver_rc"] == 0
    assert len(history) == 1


def test_complete_k2_environment_reaches_actual_job_driver_argv(
    tmp_path: Path,
) -> None:
    knowledge_manifest = "/absolute/knowledge manifest.json"
    proposal = "/absolute/proposal.json"
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": knowledge_manifest,
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "reproduction_or_selection",
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false",
            "IZANAGI_S4_PROPOSAL_PATH": proposal,
        },
    )
    assert rc == result["driver_rc"] == 0
    assert len(history) == 1
    argv = history[0]
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
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path,
        {
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_PROPOSAL_PATH": "/absolute/proposal.json",
        },
    )
    assert rc == result["driver_rc"] == 0
    assert len(history) == 1
    argv = history[0]
    assert "--knowledge-manifest" in argv
    assert "--coder-role" in argv
    assert "--knowledge-classification" not in argv
    assert "--knowledge-de-novo-claim" not in argv


def test_k2_argv_expansion_is_proposal_only() -> None:
    source = JOB.read_text(encoding="utf-8")
    assert source.count('"${k2_argv[@]}"') == 1
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



@pytest.mark.parametrize(
    "label,fragment", tuple(STOCK_PINS.items()),
)
def test_stock_fragment_mutants_have_one_static_failure(label, fragment):
    source = JOB.read_text()
    assert source.count(fragment) == 1
    with pytest.raises(AssertionError) as error:
        _assert_static_job_contract(source.replace(fragment, "true", 1))
    assert str(error.value) == f"job contract missing: {label}"


def _pair_environment(mode):
    if mode == "fixture":
        return {}
    env = {"IZANAGI_S4_PROPOSAL_PATH": "/absolute/proposal.json"}
    if mode == "k2":
        env.update({
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge manifest.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "reproduction_or_selection",
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false",
        })
    return env


@pytest.mark.parametrize("mode", ["fixture", "proposal", "k2"])
@pytest.mark.parametrize("stock", [None, "0"])
def test_default_job_invokes_driver_once(tmp_path, mode, stock):
    env = _pair_environment(mode)
    if stock is not None:
        env["IZANAGI_S4_STOCK_CONTROL"] = stock
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    expected = ["-B", "-m", "orchestrator.campaign.p3_s4_loop",
                "--allow-coder-derived-build", "--isolate-worktree",
                "--fetchcontent-prebuild-receipt",
                str(tmp_path / "evidence/masstree-prebuild-receipt.json")]
    if mode == "k2":
        expected += ["--knowledge-manifest", "/absolute/knowledge manifest.json",
                     "--coder-role", "coder-v4-autonomous-k2",
                     "--knowledge-classification", "reproduction_or_selection",
                     "--knowledge-de-novo-claim", "false"]
    expected += (["--value", "20"] if mode == "fixture" else
                 ["--run-iteration", "/absolute/proposal.json"])
    assert history == [expected]
    assert rc == result["driver_rc"] == 0
    assert [record["IZANAGI_BENCH_LOCK"] for record in _read_driver_environment(tmp_path)] == [None]


@pytest.mark.parametrize("mode", ["proposal", "k2"])
def test_pair_job_invokes_one_driver_with_both_modes(tmp_path, mode):
    env = {**_pair_environment(mode), "IZANAGI_S4_STOCK_CONTROL": "1"}
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    assert len(history) == 1
    expected = ["-B", "-m", "orchestrator.campaign.p3_s4_loop",
                "--allow-coder-derived-build", "--isolate-worktree", "--fetchcontent-prebuild-receipt",
                str(tmp_path / "evidence/masstree-prebuild-receipt.json")]
    if mode == "k2":
        expected += ["--knowledge-manifest", "/absolute/knowledge manifest.json",
                     "--coder-role", "coder-v4-autonomous-k2",
                     "--knowledge-classification", "reproduction_or_selection",
                     "--knowledge-de-novo-claim", "false"]
    assert history == [expected + ["--stock-control", "--run-iteration", "/absolute/proposal.json"]]
    assert rc == result["driver_rc"] == 0
    assert [record["IZANAGI_BENCH_LOCK"] for record in _read_driver_environment(tmp_path)] == [None]


@pytest.mark.parametrize("mode", ["proposal", "k2"])
@pytest.mark.parametrize("expected", [0, 7, 9])
def test_pair_job_propagates_driver_status(tmp_path, mode, expected):
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, {**_pair_environment(mode), "IZANAGI_S4_STOCK_CONTROL": "1"},
        driver_rcs=(expected, 99),
    )
    assert len(history) == 1 and "--stock-control" in history[0]
    assert rc == result["driver_rc"] == expected


def test_fixture_pair_refuses_before_prebuild_and_trap(tmp_path):
    completed, evidence, sentinels = _run_actual_job_to_k2_preflight(
        tmp_path, {"IZANAGI_S4_STOCK_CONTROL": "1", "IZANAGI_S4_FIXTURE_VALUE": "20"})
    assert completed.returncode == 2
    assert "IZANAGI_S4_STOCK_CONTROL=1 requires IZANAGI_S4_PROPOSAL_PATH" in completed.stderr
    assert not any(path.exists() for path in sentinels)
    assert not (evidence / "compute-result.json").exists()


def test_pair_job_has_no_shell_stock_aggregation():
    source = _shell_body_without_heredocs(JOB.read_text())
    assert "stock_rc" not in source
    assert "stock_identity_argv" not in source
    assert "p3 S4 pair:" not in source


@pytest.mark.parametrize("value", ["", "2", "true"])
def test_invalid_stock_environment_refuses_before_prebuild(tmp_path, value):
    completed, evidence, sentinels = _run_actual_job_to_k2_preflight(
        tmp_path, {"IZANAGI_S4_STOCK_CONTROL": value})
    assert completed.returncode == 2
    assert "IZANAGI_S4_STOCK_CONTROL must be 0 or 1" in completed.stderr
    assert not any(path.exists() for path in sentinels)
    assert not (evidence / "compute-result.json").exists()


@pytest.mark.parametrize("label,fragment", tuple(B5_PINS.items()))
def test_b5_fragment_mutants_have_one_static_failure(label, fragment):
    source = JOB.read_text()
    assert source.count(fragment) == 1
    with pytest.raises(AssertionError) as error:
        _assert_static_job_contract(source.replace(fragment, "true", 1))
    assert str(error.value) == f"job contract missing: {label}"


def test_b5_v2_step_surface_is_separate_from_v1_modes():
    body = JOB.read_text()
    assert 'series-step:llm|series-step:random|series-step:sweep-matched) ;;' in body
    assert '[[ "${IZANAGI_S4_B5_PURPOSE-}" == registered-v2 ]]' in body
    assert 'stock-evaluation-1|evaluation-([2-9]|10)|score' in body
    assert 'b5_argv+=(--step "$IZANAGI_S4_B5_STEP")' in body
    assert 'b5_argv+=(--purpose "$IZANAGI_S4_B5_PURPOSE")' in body


def _b5_environment(tmp_path, arm="random"):
    env = {
        "IZANAGI_S4_B5_MODE": "block-stock" if arm == "stock" else "series",
        "IZANAGI_S4_B5_ARM": arm,
        "IZANAGI_S4_B5_WORKLOAD": "write-heavy",
        "IZANAGI_S4_B5_SERIES": "1",
        "IZANAGI_S4_B5_BLOCK": "1",
        "IZANAGI_S4_B5_LEDGER_ROOT": str(tmp_path / "ledger"),
    }
    if arm == "llm":
        env.update({
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": "/absolute/knowledge.json",
            "IZANAGI_S4_CODER_ROLE": "coder-v4-autonomous-k2",
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": "known_result_conditioned_derivative",
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": "false",
        })
    return env


def _assert_b5_driver_history(history, tmp_path, arm):
    # M13: cardinality is observed at the real shell -> driver boundary.
    assert len(history) == 1
    expected = ["-B", "-m", "orchestrator.campaign.b5_generator_contrast",
                "run-block-stock" if arm == "stock" else "run-series"]
    if arm != "stock":
        expected += ["--arm", arm, "--series", "1"]
    expected += ["--workload", "write-heavy", "--block", "1",
                 "--ledger-root", str(tmp_path / "ledger"),
                 "--fetchcontent-prebuild-receipt",
                 str(tmp_path / "evidence/masstree-prebuild-receipt.json")]
    if arm == "llm":
        expected += ["--knowledge-manifest", "/absolute/knowledge.json",
                     "--knowledge-classification", "known_result_conditioned_derivative",
                     "--knowledge-de-novo-claim", "false"]
    assert history == [expected]

    # Independent of observed values: harness scratch base and PBS_JOBID,
    # with ':' replaced by '_' as specified by the job's path rule.
    expected_tmpdir = tmp_path / "scratch-base" / "0:945411.nqsv".replace(":", "_")
    assert _read_driver_environment(tmp_path) == [{
        "TMPDIR": str(expected_tmpdir),
        "IZANAGI_BENCH_LOCK": str(expected_tmpdir / "bench.lock"),
    }]


@pytest.mark.parametrize("arm", ["random", "sweep-matched", "llm", "stock"])
@pytest.mark.parametrize("driver_rc", [0, 7])
def test_b5_actual_shell_one_driver_and_trap_rc(tmp_path, arm, driver_rc):
    history, rc, result = _run_actual_job_body_through_driver(
        tmp_path, _b5_environment(tmp_path, arm), driver_rcs=(driver_rc, 99))
    _assert_b5_driver_history(history, tmp_path, arm)
    assert rc == result["driver_rc"] == driver_rc
    assert result["schema_version"] == "p3-s4-loop-compute-result/v1"


def test_b5_fallthrough_mutant_is_killed_by_shell_call_count(tmp_path):
    source = JOB.read_text()
    assert source.count('exit "$b5_rc"') == 1
    history, _, _ = _run_actual_job_body_through_driver(
        tmp_path, _b5_environment(tmp_path),
        source_override=source.replace('exit "$b5_rc"', "true", 1))
    assert len(history) == 2  # mutation reaches the fixture driver
    with pytest.raises(AssertionError):
        _assert_b5_driver_history(history, tmp_path, "random")


@pytest.mark.parametrize("arm,key,value,reason", [
    ("random", "MODE", "", "IZANAGI_S4_B5_MODE must be"),
    ("random", "MODE", "invalid", "IZANAGI_S4_B5_MODE must be"),
    ("random", "ARM", "", "missing B-5 environment"),
    ("random", "ARM", "stock", "invalid B-5 arm"),
    ("stock", "ARM", "llm", "invalid B-5 arm"),
    ("random", "WORKLOAD", "", "missing B-5 environment"),
    ("random", "WORKLOAD", "unknown", "invalid B-5 workload"),
    ("random", "SERIES", "", "missing B-5 environment"),
    ("random", "SERIES", "01", "invalid B-5 series"),
    ("random", "SERIES", "0", "invalid B-5 series"),
    ("random", "SERIES", "13", "invalid B-5 series"),
    ("random", "BLOCK", "", "missing B-5 environment"),
    ("random", "BLOCK", "01", "invalid B-5 block"),
    ("random", "BLOCK", "4", "invalid B-5 block"),
    ("random", "LEDGER_ROOT", "", "missing B-5 environment"),
    ("random", "LEDGER_ROOT", "relative", "ledger root must be absolute"),
])
def test_b5_invalid_env_precedes_repository_resolution(tmp_path, arm, key, value, reason):
    env = _b5_environment(tmp_path, arm)
    env["IZANAGI_S4_B5_" + key] = value
    _assert_b5_preflight_refusal(tmp_path, env, reason)


def _assert_b5_preflight_refusal(tmp_path, env, reason):
    # Nonexistent repo distinguishes early env rejection from a path gate rc=2.
    env["IZANAGI_S4_REPO_ROOT"] = str(tmp_path / "missing-repository")
    environment, evidence, job, sentinels = _k2_preflight_environment(tmp_path)
    environment.update(env)
    completed = subprocess.run(["bash", str(job)], cwd=tmp_path, env=environment,
                               capture_output=True, text=True, check=False)
    assert completed.returncode == 2
    assert reason in completed.stderr
    assert "repository root is unavailable" not in completed.stderr
    assert not any(path.exists() for path in sentinels)
    assert not (evidence / "compute-result.json").exists()


@pytest.mark.parametrize("key", ["MODE", "ARM", "WORKLOAD", "SERIES", "BLOCK", "LEDGER_ROOT"])
def test_b5_partial_environment_refused_before_paths(tmp_path, key):
    env = _b5_environment(tmp_path)
    del env["IZANAGI_S4_B5_" + key]
    reason = "requires IZANAGI_S4_B5_MODE" if key == "MODE" else "missing B-5 environment"
    _assert_b5_preflight_refusal(tmp_path, env, reason)


@pytest.mark.parametrize("key,value", [
    ("PROPOSAL_PATH", "/absolute/proposal.json"), ("PROPOSAL_PATH", ""),
    ("FIXTURE_VALUE", "20"), ("FIXTURE_VALUE", ""), ("STOCK_CONTROL", "1"),
])
def test_b5_legacy_modes_are_exclusive_before_paths(tmp_path, key, value):
    env = _b5_environment(tmp_path)
    env["IZANAGI_S4_" + key] = value
    _assert_b5_preflight_refusal(tmp_path, env, "B-5 mode excludes")


@pytest.mark.parametrize("key", ["KNOWLEDGE_MANIFEST", "CODER_ROLE",
                                "KNOWLEDGE_CLASSIFICATION", "KNOWLEDGE_DE_NOVO_CLAIM"])
@pytest.mark.parametrize("value", [None, ""])
def test_b5_llm_requires_all_k2_before_paths(tmp_path, key, value):
    env = _b5_environment(tmp_path, "llm")
    if value is None:
        del env["IZANAGI_S4_" + key]
    else:
        env["IZANAGI_S4_" + key] = value
    _assert_b5_preflight_refusal(tmp_path, env, "B-5 llm requires K2 environment")


@pytest.mark.parametrize("arm", ["random", "sweep-matched", "stock"])
@pytest.mark.parametrize("value", ["", "/absolute/knowledge.json"])
def test_b5_non_llm_excludes_k2_before_paths(tmp_path, arm, value):
    env = _b5_environment(tmp_path, arm)
    env["IZANAGI_S4_KNOWLEDGE_MANIFEST"] = value
    _assert_b5_preflight_refusal(tmp_path, env, "B-5 non-llm arm excludes K2")


def test_b5_set_empty_mode_alone_is_refused_before_paths(tmp_path):
    _assert_b5_preflight_refusal(tmp_path, {"IZANAGI_S4_B5_MODE": ""},
                               "IZANAGI_S4_B5_MODE must be")


def test_b5_empty_mode_mutant_is_killed_by_early_rc2(tmp_path, monkeypatch):
    source = JOB.read_text()
    fragment = 'if [[ -v IZANAGI_S4_B5_MODE ]]; then'
    assert source.count(fragment) == 1
    job = tmp_path / JOB.name
    job.write_text(source.replace(fragment, 'if [[ -n "$b5_mode" ]]; then', 1))
    monkeypatch.setitem(globals(), "JOB", job)
    case = tmp_path / "case"
    case.mkdir()
    # M14 escapes the env gate. The independent test rejects the later path rc=2.
    with pytest.raises(AssertionError):
        test_b5_set_empty_mode_alone_is_refused_before_paths(case)


@pytest.mark.parametrize("stock", [None, "0"])
def test_b5_stock_off_preserves_single_b5_call(tmp_path, stock):
    env = _b5_environment(tmp_path)
    if stock is not None:
        env["IZANAGI_S4_STOCK_CONTROL"] = stock
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    _assert_b5_driver_history(history, tmp_path, "random")
    assert rc == result["driver_rc"] == 0


def test_b5_duplicate_driver_and_late_branch_are_rejected():
    source = JOB.read_text()
    driver = '"$PY" -B -m orchestrator.campaign.b5_generator_contrast'
    with pytest.raises(AssertionError, match="b5-driver-count-or-order"):
        _assert_forbidden_job_constructs(source + "\n" + driver)
    start = source.index('if [[ -n "$b5_mode" ]]; then\n  b5_argv=')
    end = source.index('candidate_rc=0', start)
    block = source[start:end]
    mutant = source[:start] + source[end:] + block
    with pytest.raises(AssertionError):
        _assert_static_job_stage_order(mutant)


@pytest.mark.parametrize("location", ["repo", "common", "symlink"])
def test_b5_ledger_inside_repository_refused_before_trap(tmp_path, location):
    environment, evidence, job, _ = _k2_preflight_environment(tmp_path)
    repo = tmp_path / "repo"
    common = tmp_path / "common"
    common.mkdir()
    alias = tmp_path / "alias"
    alias.symlink_to(repo, target_is_directory=True)
    ledger = {"repo": repo, "common": common, "symlink": alias}[location] / "ledger"
    _write_executable(tmp_path / "bin/git",
                      "#!/bin/bash\nprintf '%s\\n' " + shlex.quote(str(common / ".git")) + "\n")
    environment.update(_b5_environment(tmp_path))
    environment["IZANAGI_S4_B5_LEDGER_ROOT"] = str(ledger)
    result = subprocess.run(["bash", str(job)], cwd=tmp_path, env=environment,
                            capture_output=True, text=True)
    assert result.returncode == 2
    assert "B-5 ledger root resolves inside a repository" in result.stderr
    assert not (evidence / "compute-result.json").exists()


@pytest.mark.parametrize("purpose", ["", "unknown", "Registered"])
def test_b5_purpose_invalid_before_prebuild(tmp_path, purpose):
    env = _b5_environment(tmp_path)
    env["IZANAGI_S4_B5_PURPOSE"] = purpose
    _assert_b5_preflight_refusal(tmp_path, env,
                               "IZANAGI_S4_B5_PURPOSE must be pilot or registered")


@pytest.mark.parametrize("purpose", ["", "pilot", "registered"])
def test_b5_purpose_alone_requires_mode(tmp_path, purpose):
    _assert_b5_preflight_refusal(tmp_path, {"IZANAGI_S4_B5_PURPOSE": purpose},
                               "B-5 environment requires IZANAGI_S4_B5_MODE")


@pytest.mark.parametrize("arm", ["random", "sweep-matched", "llm", "stock"])
@pytest.mark.parametrize("driver_rc", [0, 7])
def test_b5_registered_purpose_reaches_driver(tmp_path, arm, driver_rc):
    env = {**_b5_environment(tmp_path, arm), "IZANAGI_S4_B5_PURPOSE": "registered"}
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env, driver_rcs=(driver_rc, 99))
    assert len(history) == 1
    assert history[0][-2:] == ["--purpose", "registered"]
    # Exact old argv and lock contract, followed only by the registered suffix.
    _assert_b5_driver_history([history[0][:-2]], tmp_path, arm)
    assert rc == result["driver_rc"] == driver_rc


@pytest.mark.parametrize("arm", ["random", "sweep-matched", "llm", "stock"])
def test_b5_explicit_pilot_preserves_driver_argv(tmp_path, arm):
    env = {**_b5_environment(tmp_path, arm), "IZANAGI_S4_B5_PURPOSE": "pilot"}
    history, rc, result = _run_actual_job_body_through_driver(tmp_path, env)
    _assert_b5_driver_history(history, tmp_path, arm)
    assert rc == result["driver_rc"] == 0


def _run() -> int:
    """Keep this test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
