#!/bin/bash
#PBS -A SFC
#PBS -q gen_S
#PBS -l elapstim_req=01:00:00
#PBS -b 1
#
# Bounded execution reservation (seconds): gflags (60*3=180) + glog
# (120*3=360) + third-party hydrate (timeout 20) + CMake configure/build
# (180+600=780) + workload (120+kill-after 30=150) + finalize reserve (300)
# = 1790, leaving 1810 seconds of margin within the 3600-second PBS request.
# Compute-side Mocc trace pilot.  The workload tuple is parent-selected pilot
# data and is not a reproduction of historical T-816 measurements.
set -Eeuo pipefail
umask 077

if [[ -z "${PBS_JOBID:-}" || -z "${PBS_O_WORKDIR:-}" ]]; then
  echo "PBS_JOBID/PBS_O_WORKDIR is required" >&2
  exit 2
fi
if [[ ! "$PBS_JOBID" =~ ^([0-9]+:)?[A-Za-z0-9._-]+$ ]]; then
  echo "unsafe PBS_JOBID" >&2
  exit 2
fi
if [[ -z "${IZANAGI_SUBMISSION_NONCE:-}" ||
      ! "$IZANAGI_SUBMISSION_NONCE" =~ ^[A-Za-z0-9_-]+([.][A-Za-z0-9_-]+)*$ ]]; then
  echo "IZANAGI_SUBMISSION_NONCE is missing or unsafe" >&2
  exit 2
fi
if [[ ! "${IZANAGI_MOCC_TRACE_MODE:-}" =~ ^[01]$ ]]; then
  echo "IZANAGI_MOCC_TRACE_MODE must be 0 or 1" >&2
  exit 2
fi
if [[ ! "${IZANAGI_MOCC_POLICY_RAW_SHA256:-}" =~ ^[0-9a-f]{64}$ ]]; then
  echo "IZANAGI_MOCC_POLICY_RAW_SHA256 must be 64 lowercase hex" >&2
  exit 2
fi
if [[ ! "${IZANAGI_MOCC_G2_DISCRIMINATOR:-0}" =~ ^[01]$ ]]; then
  echo "IZANAGI_MOCC_G2_DISCRIMINATOR must be 0 or 1" >&2
  exit 2
fi
T1943_G2=${IZANAGI_MOCC_G2_DISCRIMINATOR:-0}
if [[ "$T1943_G2" -eq 1 && "$IZANAGI_MOCC_TRACE_MODE" -ne 1 ]]; then
  echo "T-1943 discriminator mode requires TRACE mode 1" >&2
  exit 2
fi

export TMPDIR="/scr/${PBS_JOBID//:/_}"
if ! mkdir "$TMPDIR"; then
  echo "TMPDIR already exists or cannot be created (create-only): $TMPDIR" >&2
  exit 2
fi

REPO_ROOT=$(cd "$PBS_O_WORKDIR" && pwd -P)
TOOLS="$REPO_ROOT/tools/pegasus"
POLICY="$TOOLS/mocc_trace_v1_policy.json"
ATTEMPTS_ROOT=${IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT:-"$REPO_ROOT/output/env/pegasus/mocc-trace/attempts"}
JOB_STAGING_ROOT="$REPO_ROOT/output/env/pegasus/mocc-trace/job-staging"
case "$ATTEMPTS_ROOT" in
  *:*|*,*|*$'\n'*)
    echo "unsafe Mocc trace attempts root" >&2
    exit 2
    ;;
esac
mkdir -p "$ATTEMPTS_ROOT" "$JOB_STAGING_ROOT"
if [[ -L "$ATTEMPTS_ROOT" || ! -d "$ATTEMPTS_ROOT" ]]; then
  echo "Mocc trace attempts root is not a real directory" >&2
  exit 2
fi
ATTEMPTS_ROOT=$(cd "$ATTEMPTS_ROOT" && pwd -P)
case "$ATTEMPTS_ROOT" in
  *:*|*,*|*$'\n'*)
    echo "unsafe normalized Mocc trace attempts root" >&2
    exit 2
    ;;
esac
ATTEMPT_DIR="$JOB_STAGING_ROOT/$PBS_JOBID"
if ! mkdir "$ATTEMPT_DIR"; then
  echo "attempt already exists (create-only): $ATTEMPT_DIR" >&2
  exit 2
fi

failure_written=0
CCBENCH_BASE=""
BUILD_SOURCE=""
ATTEMPT_RECEIPT=""
CURRENT_COMMIT=""
CURRENT_SCRIPT_SHA=""
BINARY=""
BINARY_SHA=""
BUILD_DIR=""
TRACE_DIR=""
RUN_STDOUT=""
RUN_STDERR=""
RUN_ARGV_JSON=""
COMMIT_COUNT=""
RUN_ELAPSED_NS=""
CHECKER_RC="not-run"
CHECKER_PY=""
CHECKER_TOOL_PATH=""
CHECKER_TOOL_SHA=""
VERIFIER_PY=""
VERIFIER_TOOL_PATH=""
VERIFIER_TOOL_SHA=""
DISCRIMINATOR_TOOL_PATH=""
DISCRIMINATOR_TOOL_SHA=""
CHECKER_REPORT_SHA=""
VERIFIER_RC="not-run"
DISCRIMINATOR_RC="not-run"
DISCRIMINATOR_RESULT="not-run"
TRACE_MANIFEST_SHA=""
WITNESS_DIR=""
WITNESS_MANIFEST_SHA=""
DISCRIMINATOR_RESULT_SHA=""
TRACE0_WATERMARK_ABSENCE_SHA=""
SUBMIT_RECEIPT_SHA=""
POLICY_RAW_SHA256=""
RUN_RC="not-run"
JUDGMENT_PRE_CAPTURE=""
JUDGMENT_PRE_SHA=""
JUDGMENT_POST_CAPTURE=""
JUDGMENT_POST_SHA=""
TRACE_MODE=$IZANAGI_MOCC_TRACE_MODE

write_failure() {
  local rc=$1
  local stage=$2
  local message=$3
  if [[ "$failure_written" -eq 0 ]]; then
    failure_written=1
    python3 - "$ATTEMPT_DIR/failure.json" "$PBS_JOBID" "$rc" "$stage" "$message" <<'PY' || true
import json
import sys
import time

path, job_id, rc, stage, message = sys.argv[1:]
payload = {
    "schema_version": "mocc-trace-pilot-failure/v1",
    "pbs_jobid": job_id,
    "rc": int(rc),
    "stage": stage,
    "message": message,
    "recorded_epoch": int(time.time()),
}
try:
    with open(path, "x", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
        handle.write("\n")
except FileExistsError:
    pass
PY
  fi
}

on_err() {
  local rc=$?
  local line=${BASH_LINENO[0]:-unknown}
  trap - ERR
  write_failure "$rc" "shell" "command failed at line $line"
  exit "$rc"
}
trap on_err ERR

on_signal() {
  local signal=$1
  trap - ERR INT TERM HUP
  write_failure 128 "signal" "received $signal"
  exit 128
}
trap 'on_signal INT' INT
trap 'on_signal TERM' TERM
trap 'on_signal HUP' HUP

write_artifact_classification_manifest() {
  python3 - "$ATTEMPT_DIR/artifact-classification-manifest.json" \
    "$TRACE_MODE" "$T1943_G2" <<'PY_ARTIFACT_MANIFEST'
import json
import sys

output, trace_mode, t1943_g2 = sys.argv[1:]
trace_mode_i = int(trace_mode)
t1943_g2_i = int(t1943_g2)
if trace_mode_i not in {0, 1}:
    raise SystemExit("trace mode must be zero or one")
if t1943_g2_i not in {0, 1} or (t1943_g2_i and trace_mode_i != 1):
    raise SystemExit("T-1943 discriminator mode differs")

classifications = (
    "correctness_evidence",
    "performance_evidence",
    "operational_diagnostic",
)
artifacts = []


def add(scope, path_pattern, classification, reason, modes=(0, 1)):
    if trace_mode_i not in modes:
        return
    if classification not in classifications:
        raise ValueError("artifact classification is outside the closed enum")
    if not reason or "\n" in reason or "\r" in reason:
        raise ValueError("artifact reason must be one nonempty line")
    artifacts.append(
        {
            "scope": scope,
            "path_pattern": path_pattern,
            "classification": classification,
            "trace1_performance_use_forbidden": trace_mode_i == 1,
            "reason": reason,
        }
    )


for path_pattern in (
    "artifact-classification-manifest.json",
    "failure.json",
    "worktree-cleanup.stdout",
    "worktree-cleanup.stderr",
    "qstat-f.stdout",
    "qstat-f.stderr",
    "qstat-f.rc",
    "hostname.stdout",
    "hostname-f.stdout",
    "allocation-unavailable.json",
    "reservation.json",
    "window-remaining-*.stdout",
    "topology.json",
    "cpu-model.stdout",
    "module-list.stdout",
    "module-list.stderr",
    "module-list.rc",
    "compiler-gcc.path",
    "compiler-gxx.path",
    "cmake.path",
    "compiler-gcc.version",
    "compiler-gxx.version",
    "cmake.version",
    "gflags-source-head.stdout",
    "gflags-source-status.stdout",
    "gflags-configure.argv.json",
    "gflags-configure.stdout",
    "gflags-configure.stderr",
    "gflags-build.stdout",
    "gflags-build.stderr",
    "gflags-install.stdout",
    "gflags-install.stderr",
    "glog-source-head.stdout",
    "glog-source-status.stdout",
    "glog-configure.argv.json",
    "glog-configure.stdout",
    "glog-configure.stderr",
    "glog-build.stdout",
    "glog-build.stderr",
    "glog-install.stdout",
    "glog-install.stderr",
    "third-party-hydrate.json",
    "third-party-hydrate.stderr",
    "third-party-source-root.stdout",
    "submodule-head.stdout",
    "submodule-status.stdout",
    "worktree-add.stdout",
    "worktree-add.stderr",
    "configure-trace*.argv.json",
    "configure-trace*.stdout",
    "configure-trace*.stderr",
    "build-trace*.stdout",
    "build-trace*.stderr",
    "compiler-used.version",
    "run/workload.stderr",
    "run/workload.rc",
    "qstat-final.stdout",
    "qstat-final.stderr",
    "qstat-final.rc",
    "qstat-accounting.stdout",
    "qstat-accounting.stderr",
    "qstat-accounting.rc",
    "worktree-remove.stdout",
    "worktree-remove.stderr",
):
    add(
        "attempt_dir",
        path_pattern,
        "operational_diagnostic",
        "Records execution, environment, build, scheduler, or failure diagnostics.",
    )

for path_pattern, reason in (
    (
        "submit-receipt.json",
        "Binds the job to the submitted request and frozen source inputs.",
    ),
    (
        "judgment-source-pre.json",
        "Records the source identity and clean state before judgment.",
    ),
    (
        "judgment-source-post.json",
        "Records the source identity and clean state after judgment.",
    ),
    (
        "binary-trace*.sha256",
        "Binds the executed workload binary bytes.",
    ),
    (
        "binary-trace*.path",
        "Records the executed workload binary path.",
    ),
    (
        "run/workload.argv.json",
        "Records the exact workload configuration and arguments.",
    ),
    (
        "mocc-trace-pilot-receipt.sha256",
        "Binds the pilot receipt bytes by digest.",
    ),
    (
        "job-result.json",
        "Binds the completed job result to the pilot receipt.",
    ),
):
    add("attempt_dir", path_pattern, "correctness_evidence", reason)

for path_pattern, reason in (
    (
        "run/workload.stdout",
        "CCBench stdout contains the commit-count witness and may expose other performance values.",
    ),
    (
        "run/workload.elapsed_ns",
        "Elapsed time combines with a commit count to derive throughput.",
    ),
    (
        "commit-count.json",
        "The commit-count witness combines with elapsed time to derive throughput.",
    ),
):
    add("attempt_dir", path_pattern, "performance_evidence", reason)

if trace_mode_i == 0:
    add(
        "attempt_dir",
        "mocc-trace-pilot-receipt.json",
        "performance_evidence",
        "The TRACE=0 receipt records completed transactions and elapsed time.",
    )
else:
    add(
        "attempt_dir",
        "mocc-trace-pilot-receipt.json",
        "correctness_evidence",
        "The TRACE=1 receipt binds correctness artifacts while other listed files still permit performance derivation.",
    )

for path_pattern, classification, reason in (
    (
        "trace0-preprocess-identity.json",
        "correctness_evidence",
        "Certifies the D297 TRACE=0 preprocess identity gate, which is only one necessary condition for complete trace removal from the measurement build and does not prove that removal.",
    ),
    (
        "trace0-preprocess-identity.stderr",
        "operational_diagnostic",
        "Records diagnostics from the TRACE=0 preprocess identity gate.",
    ),
    (
        "trace0-preprocess-identity.rc",
        "operational_diagnostic",
        "Records the TRACE=0 preprocess identity gate return code.",
    ),
    (
        "trace0-execution.json",
        "correctness_evidence",
        "Records fail-closed skipping when the TRACE=0 identity gate rejects.",
    ),
    (
        "throughput.json",
        "performance_evidence",
        "Records TRACE=0 throughput and latency derived from count and elapsed time.",
    ),
):
    add("attempt_dir", path_pattern, classification, reason, modes=(0,))

for path_pattern, classification, reason in (
    (
        "run/trace/trace_*.log",
        "correctness_evidence",
        "Trace records support verification and may expose timing or transaction-count information.",
    ),
    (
        "trace-manifest.json",
        "correctness_evidence",
        "Binds trace file names, sizes, and digests for verification.",
    ),
    (
        "verifier.json",
        "correctness_evidence",
        "The verifier verdict includes stats.txns, which exposes a transaction count.",
    ),
    (
        "verifier.stderr",
        "operational_diagnostic",
        "Records verifier diagnostics.",
    ),
    (
        "verifier.rc",
        "operational_diagnostic",
        "Records the verifier return code.",
    ),
):
    add("attempt_dir", path_pattern, classification, reason, modes=(1,))

if t1943_g2_i:
    for path_pattern, classification, reason in (
        (
            "instr-patch.sha256",
            "correctness_evidence",
            "Binds the instrumentation patch bytes before application.",
        ),
        (
            "instr-patch.numstat",
            "correctness_evidence",
            "Records the checked instrumentation patch touch set.",
        ),
        (
            "instr-patch-source.sha256",
            "correctness_evidence",
            "Binds the patched transaction source bytes.",
        ),
        (
            "instr-patch-apply.stdout",
            "operational_diagnostic",
            "Records patch check/apply stdout, normally empty.",
        ),
        (
            "instr-patch-apply.stderr",
            "operational_diagnostic",
            "Records patch numstat/check/apply stderr, normally empty.",
        ),
        (
            "discriminator.stderr",
            "operational_diagnostic",
            "Records payload discriminator diagnostics.",
        ),
        (
            "discriminator.rc",
            "operational_diagnostic",
            "Records the payload discriminator return code.",
        ),
        (
            "trace0-preprocess-identity.json",
            "correctness_evidence",
            "Certifies the D297 TRACE=0 preprocess identity gate, which is only one necessary condition for complete trace removal from the measurement build and does not prove that removal.",
        ),
        (
            "trace0-preprocess-identity.stderr",
            "operational_diagnostic",
            "Records diagnostics from the TRACE=0 preprocess identity gate.",
        ),
        (
            "trace0-preprocess-identity.rc",
            "operational_diagnostic",
            "Records the TRACE=0 preprocess identity gate return code.",
        ),
        (
            "trace0-execution.json",
            "correctness_evidence",
            "Records fail-closed skipping when the TRACE=0 identity gate rejects.",
        ),
        (
            "throughput.json",
            "performance_evidence",
            "Records TRACE=0 throughput and latency derived from count and elapsed time.",
        ),
        (
            "run/witness",
            "correctness_evidence",
            "Separates payload-lineage evidence from the standard trace directory.",
        ),
        (
            "run/witness/witness_*.log",
            "correctness_evidence",
            "Payload lineage is isolated from standard verifier trace files.",
        ),
        (
            "witness-manifest.json",
            "correctness_evidence",
            "Binds payload witness file names, sizes, and digests.",
        ),
        (
            "trace0-watermark-absence.json",
            "correctness_evidence",
            "Certifies T-1943 marker and symbol absence in the TRACE=0 binary.",
        ),
        (
            "discriminator.json",
            "correctness_evidence",
            "Records the bounded payload-lineage discriminator conclusion.",
        ),
    ):
        add("attempt_dir", path_pattern, classification, reason, modes=(1,))

for path_pattern, reason in (
    (
        "pbs-job.stdout",
        "PBS captures the job's unredirected standard output.",
    ),
    (
        "pbs-job.stderr",
        "PBS captures the job's unredirected standard error.",
    ),
):
    add("submission_dir", path_pattern, "operational_diagnostic", reason)

artifacts.sort(key=lambda item: (item["scope"], item["path_pattern"]))
identities = [(item["scope"], item["path_pattern"]) for item in artifacts]
if len(identities) != len(set(identities)):
    raise ValueError("artifact path patterns must be unique within each scope")

payload = {
    "schema_version": "mocc-trace-artifact-classification-manifest/v1",
    "trace_mode": trace_mode_i,
    "classification_enum": list(classifications),
    "performance_use_policy": (
        "TRACE=1 files must not be used as performance evidence even when "
        "performance values remain derivable from their contents or combinations."
    ),
    "artifacts": artifacts,
}
with open(output, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY_ARTIFACT_MANIFEST
}

validate_artifact_classification_manifest() {
  python3 - "$ATTEMPT_DIR/artifact-classification-manifest.json" \
    "$ATTEMPT_DIR" "$TRACE_MODE" "$T1943_G2" <<'PY_VALIDATE_ARTIFACT_MANIFEST'
import fnmatch
import json
import os
import pathlib
import sys

manifest_path, attempt_dir, trace_mode, t1943_g2 = sys.argv[1:]
with open(manifest_path, encoding="utf-8") as handle:
    manifest = json.load(handle)

classifications = {
    "correctness_evidence",
    "performance_evidence",
    "operational_diagnostic",
}
if manifest.get("schema_version") != (
    "mocc-trace-artifact-classification-manifest/v1"
):
    raise ValueError("artifact classification manifest schema differs")
if manifest.get("trace_mode") != int(trace_mode):
    raise ValueError("artifact classification manifest trace mode differs")
if set(manifest.get("classification_enum", ())) != classifications:
    raise ValueError("artifact classification enum differs")
entries = manifest.get("artifacts")
if not isinstance(entries, list) or not entries:
    raise ValueError("artifact classification entries are absent")

entry_keys = {
    "scope",
    "path_pattern",
    "classification",
    "trace1_performance_use_forbidden",
    "reason",
}
identities = []
for entry in entries:
    if not isinstance(entry, dict) or set(entry) != entry_keys:
        raise ValueError("artifact classification entry shape differs")
    if entry["scope"] not in {"attempt_dir", "submission_dir"}:
        raise ValueError("artifact classification scope differs")
    if (
        not isinstance(entry["path_pattern"], str)
        or not entry["path_pattern"]
        or os.path.isabs(entry["path_pattern"])
        or ".." in pathlib.PurePosixPath(entry["path_pattern"]).parts
    ):
        raise ValueError("artifact path pattern is unsafe")
    if entry["classification"] not in classifications:
        raise ValueError("artifact classification is outside the closed enum")
    forbidden = entry["trace1_performance_use_forbidden"]
    if type(forbidden) is not bool:
        raise ValueError("TRACE=1 performance-use flag is not boolean")
    if int(trace_mode) == 1 and forbidden is not True:
        raise ValueError("TRACE=1 artifact performance use is not forbidden")
    if int(trace_mode) == 0 and forbidden is not False:
        raise ValueError("TRACE=0 artifact is over-restricted")
    reason = entry["reason"]
    if not isinstance(reason, str) or not reason or "\n" in reason or "\r" in reason:
        raise ValueError("artifact reason must be one nonempty line")
    identities.append((entry["scope"], entry["path_pattern"]))
if len(identities) != len(set(identities)):
    raise ValueError("artifact path patterns are duplicated")

serialized_text = json.dumps(manifest, ensure_ascii=False).casefold()
for prohibited_claim in (
    "not derivable",
    "cannot derive",
    "impossible to derive",
    "non-derivable",
):
    if prohibited_claim in serialized_text:
        raise ValueError("manifest overstates performance redaction")

attempt_entries = [entry for entry in entries if entry["scope"] == "attempt_dir"]
unclassified = []
root = pathlib.Path(attempt_dir)
for path in root.rglob("*"):
    if path.is_symlink():
        raise ValueError(f"artifact is a symlink: {path.relative_to(root)}")
    if not path.is_file():
        continue
    relative = path.relative_to(root).as_posix()
    matches = [
        entry
        for entry in attempt_entries
        if fnmatch.fnmatchcase(relative, entry["path_pattern"])
    ]
    if len(matches) != 1:
        unclassified.append(relative)
if unclassified:
    raise ValueError(
        "unclassified or ambiguously classified artifacts: " + repr(unclassified)
    )
if int(t1943_g2):
    witness_root = root / "run/witness"
    try:
        witness_info = os.lstat(witness_root)
    except OSError as exc:
        raise ValueError("T-1943 witness root is unavailable") from exc
    if not witness_root.is_dir() or witness_root.is_symlink():
        raise ValueError("T-1943 witness root is not a real directory")
    if not __import__("stat").S_ISDIR(witness_info.st_mode):
        raise ValueError("T-1943 witness root is not a directory")
    witness_root_entries = [
        entry
        for entry in attempt_entries
        if entry["path_pattern"] == "run/witness"
    ]
    if len(witness_root_entries) != 1:
        raise ValueError("T-1943 witness root classification differs")
elif any(
    entry["path_pattern"].startswith("run/witness")
    or entry["path_pattern"].startswith("discriminator")
    or entry["path_pattern"] in {
        "instr-patch.sha256",
        "instr-patch.numstat",
        "instr-patch-source.sha256",
        "instr-patch-apply.stdout",
        "instr-patch-apply.stderr",
        "witness-manifest.json",
        "trace0-watermark-absence.json",
    }
    for entry in attempt_entries
):
    raise ValueError("T-1943 artifact classification leaked into general mode")
PY_VALIDATE_ARTIFACT_MANIFEST
}

write_artifact_classification_manifest

capture_judgment_source_state() {
  local phase=$1
  local output=$2
  python3 - "$REPO_ROOT" "$output" "$phase" <<'PY'
import base64
import hashlib
import json
import re
import subprocess
import sys

repo_root, output, phase = sys.argv[1:]
if phase not in {"pre_judgment", "post_judgment"}:
    raise SystemExit("unsupported judgment source capture phase")


def run_git(arguments):
    try:
        return subprocess.run(
            ["git", "-C", repo_root, *arguments],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return subprocess.CompletedProcess(arguments, 127, stdout=b"", stderr=b"")


head_result = run_git(["rev-parse", "HEAD"])
status_result = run_git(
    [
        "status",
        "--porcelain=v1",
        "-z",
        "--untracked-files=all",
        "--",
        ".",
        ":(exclude)output",
    ]
)
try:
    head = head_result.stdout.decode("ascii").strip()
except UnicodeDecodeError:
    head = ""
head_valid = bool(re.fullmatch(r"[0-9a-f]{40}", head))
capture_ok = (
    head_result.returncode == 0
    and status_result.returncode == 0
    and head_valid
)
clean = capture_ok and status_result.stdout == b""
payload = {
    "schema_version": "mocc-trace-judgment-source-capture/v1",
    "capture_phase": phase,
    "capture_ok": capture_ok,
    "head": head if head_valid else None,
    "clean": clean,
    "pathspec": [".", ":(exclude)output"],
    "status_format": "git status --porcelain=v1 -z --untracked-files=all",
    "status_bytes_base64": base64.b64encode(status_result.stdout).decode("ascii"),
    "command_rc": {
        "head": head_result.returncode,
        "status": status_result.returncode,
    },
}
capture_bytes = (
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
with open(output, "xb") as handle:
    handle.write(capture_bytes)
print("1" if capture_ok else "0")
print(head if head_valid else "-")
print("1" if clean else "0")
print(hashlib.sha256(capture_bytes).hexdigest())
PY
}

initialize_judgment_source_state() {
  local capture_output
  local -a capture_values=()
  JUDGMENT_PRE_CAPTURE="$ATTEMPT_DIR/judgment-source-pre.json"
  if ! capture_output=$(capture_judgment_source_state \
    pre_judgment "$JUDGMENT_PRE_CAPTURE"); then
    write_failure 2 source_identity "pre_judgment source capture failed"
    return 2
  fi
  mapfile -t capture_values <<<"$capture_output"
  if [[ ${#capture_values[@]} -ne 4 ]]; then
    write_failure 2 source_identity "pre_judgment source capture failed"
    return 2
  fi
  if [[ "${capture_values[0]}" != 1 ||
        ! "${capture_values[3]}" =~ ^[0-9a-f]{64}$ ]]; then
    write_failure 2 source_identity "pre_judgment source capture failed"
    return 2
  fi
  CURRENT_COMMIT=${capture_values[1]}
  JUDGMENT_PRE_SHA=${capture_values[3]}
  if [[ "${capture_values[2]}" != 1 ]]; then
    write_failure 2 source_identity "working tree was dirty at pre_judgment"
    return 2
  fi
  return 0
}

verify_post_judgment_source_state() {
  local capture_output
  local -a capture_values=()
  JUDGMENT_POST_CAPTURE="$ATTEMPT_DIR/judgment-source-post.json"
  if ! capture_output=$(capture_judgment_source_state \
    post_judgment "$JUDGMENT_POST_CAPTURE"); then
    write_failure 2 post_judgment_source \
      "post_judgment source capture failed"
    return 2
  fi
  mapfile -t capture_values <<<"$capture_output"
  if [[ ${#capture_values[@]} -ne 4 ]]; then
    write_failure 2 post_judgment_source \
      "post_judgment source capture failed"
    return 2
  fi
  if [[ "${capture_values[0]}" != 1 ||
        ! "${capture_values[3]}" =~ ^[0-9a-f]{64}$ ]]; then
    write_failure 2 post_judgment_source \
      "post_judgment source capture failed"
    return 2
  fi
  JUDGMENT_POST_SHA=${capture_values[3]}
  if [[ "${capture_values[1]}" != "$CURRENT_COMMIT" ]]; then
    write_failure 2 post_judgment_source \
      "outer source HEAD changed between pre_judgment and post_judgment"
    return 2
  fi
  if [[ "${capture_values[2]}" != 1 ]]; then
    write_failure 2 post_judgment_source \
      "working tree was dirty at post_judgment"
    return 2
  fi
  return 0
}

cleanup_worktree() {
  local original_rc=$?
  trap - EXIT
  if [[ -n "$CCBENCH_BASE" && -n "$BUILD_SOURCE" ]]; then
    git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
      >>"$ATTEMPT_DIR/worktree-cleanup.stdout" \
      2>>"$ATTEMPT_DIR/worktree-cleanup.stderr" || true
  fi
  exit "$original_rc"
}
trap cleanup_worktree EXIT

# BEGIN T2195 POLICY PARSE
if [[ ! -f "$POLICY" || -L "$POLICY" ]]; then
  write_failure 2 policy "Mocc trace policy is missing or is a symlink"
  exit 2
fi

readarray -t policy_values < <(python3 - "$POLICY" <<'PY'
import hashlib
import json
import os
import stat
import sys


def reject_duplicate_keys(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key: {key}")
        document[key] = value
    return document


def _reject_non_finite(value):
    raise ValueError(f"non-finite JSON constant: {value}")


policy_fd = os.open(
    sys.argv[1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
)
try:
    policy_info = os.fstat(policy_fd)
    if not stat.S_ISREG(policy_info.st_mode):
        raise SystemExit("Mocc trace policy is not a regular file")
    with os.fdopen(policy_fd, "rb") as handle:
        policy_fd = -1
        policy_bytes = handle.read()
finally:
    if policy_fd >= 0:
        os.close(policy_fd)
policy = json.loads(
    policy_bytes.decode("utf-8"),
    object_pairs_hook=reject_duplicate_keys,
    parse_constant=_reject_non_finite,
)
trace = policy["mocc_trace"]
workload = trace["workload"]
expected_compilers = policy["expected_compiler_version_body_sha256"]
if type(expected_compilers) is not dict or set(expected_compilers) != {"gcc", "g++"}:
    raise SystemExit("expected compiler mapping keys differ")
for role, digest in expected_compilers.items():
    if type(digest) is not str or len(digest) != 64 or any(
        char not in "0123456789abcdef" for char in digest
    ):
        raise SystemExit(f"expected compiler digest is invalid: {role}")
if set(workload) != {
    "records", "threads", "zipf_skew", "ycsb_rratio", "ycsb_rmw",
    "ycsb_max_ope", "extime_s"
}:
    raise SystemExit("mocc_trace.workload keys differ")
if trace["cmake_target"] != "ycsb_mocc.exe":
    raise SystemExit("mocc_trace cmake target differs")
for key, expected in (
    ("trace1_defines", {"CCBENCH_TRACE": "1"}),
    ("trace0_defines", {"CCBENCH_TRACE": "0"}),
):
    if trace[key] != expected:
        raise SystemExit(f"{key} differs")
for key in ("base_oid", "new_oid"):
    value = trace[key]
    if type(value) is not str or len(value) != 40 or any(
        char not in "0123456789abcdef" for char in value
    ):
        raise SystemExit(f"{key} is not a full lowercase OID")
print(policy["project"])
print(policy["queue"])
print(policy["nodes"])
print(policy["pilot_walltime_s"])
print(policy["finalize_reserve_s"])
print(policy["expected_cpu_model"])
print(policy["expected_physical_cores"])
print(policy["gflags_expected_head"])
print(policy["glog_expected_head"])
print(policy["third_party_cache_env"])
print(json.dumps(expected_compilers, sort_keys=True, separators=(",", ":")))
print(trace["base_oid"])
print(trace["new_oid"])
print(trace["cmake_target"])
print(json.dumps(workload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
print(hashlib.sha256(policy_bytes).hexdigest())
PY
)
if [[ ${#policy_values[@]} -ne 16 ]]; then
  write_failure 2 policy "Mocc trace policy parse failed"
  exit 2
fi
PROJECT=${policy_values[0]}
QUEUE=${policy_values[1]}
NODES=${policy_values[2]}
REQUESTED_S=${policy_values[3]}
FINALIZE_RESERVE_S=${policy_values[4]}
EXPECTED_CPU=${policy_values[5]}
EXPECTED_CORES=${policy_values[6]}
GFLAGS_EXPECTED_HEAD=${policy_values[7]}
GLOG_EXPECTED_HEAD=${policy_values[8]}
THIRD_PARTY_CACHE_ENV=${policy_values[9]}
EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON=${policy_values[10]}
BASE_OID=${policy_values[11]}
NEW_OID=${policy_values[12]}
CMAKE_TARGET=${policy_values[13]}
WORKLOAD_JSON=${policy_values[14]}
POLICY_PARSE_RAW_SHA256=${policy_values[15]}
# END T2195 POLICY PARSE
if [[ "$T1943_G2" -eq 1 ]]; then
  python3 - "$WORKLOAD_JSON" <<'PY_T1943_WORKLOAD'
import json
import sys

expected = {
    "extime_s": 3,
    "records": 10000,
    "threads": 48,
    "ycsb_max_ope": 10,
    "ycsb_rmw": 0,
    "ycsb_rratio": 50,
    "zipf_skew": 0.9,
}
actual = json.loads(sys.argv[1])
if (
    not isinstance(actual, dict)
    or set(actual) != set(expected)
    or any(type(actual[key]) is not type(value) or actual[key] != value
           for key, value in expected.items())
):
    raise SystemExit("T-1943 workload tuple differs")
PY_T1943_WORKLOAD
fi

# BEGIN T2195 SUBMIT RECEIPT PIN
SUBMISSION_DIR="$ATTEMPTS_ROOT/submissions/$IZANAGI_SUBMISSION_NONCE"
SUBMIT_SOURCE="$SUBMISSION_DIR/submit-receipt.json"
ATTEMPT_RECEIPT="$ATTEMPT_DIR/submit-receipt.json"
for _ in $(seq 1 60); do
  submit_pin_rc=0
  set +e
  SUBMIT_RECEIPT_SHA=$(python3 - "$SUBMIT_SOURCE" "$ATTEMPT_RECEIPT" <<'PY_SUBMIT_PIN'
import hashlib
import os
import stat
import sys

source, target = sys.argv[1:]
try:
    source_fd = os.open(source, os.O_RDONLY | os.O_NOFOLLOW)
except FileNotFoundError:
    raise SystemExit(75)
except OSError as exc:
    raise SystemExit(f"submit receipt cannot be opened without following: {exc}")
try:
    source_info = os.fstat(source_fd)
    if not stat.S_ISREG(source_info.st_mode):
        raise SystemExit("submit receipt is not a regular file")
    with os.fdopen(source_fd, "rb") as handle:
        source_fd = -1
        receipt_bytes = handle.read()
finally:
    if source_fd >= 0:
        os.close(source_fd)
pinned_sha = hashlib.sha256(receipt_bytes).hexdigest()
target_fd = os.open(
    target,
    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
    0o600,
)
with os.fdopen(target_fd, "wb") as handle:
    handle.write(receipt_bytes)
    handle.flush()
    os.fsync(handle.fileno())
print(pinned_sha)
PY_SUBMIT_PIN
  )
  submit_pin_rc=$?
  set -e
  if [[ "$submit_pin_rc" -eq 0 ]]; then
    break
  fi
  if [[ "$submit_pin_rc" -ne 75 ]]; then
    write_failure 2 submit_binding "submit receipt failed no-follow regular-file pin"
    exit 2
  fi
  sleep 1
done
if [[ ! "$SUBMIT_RECEIPT_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  write_failure 2 submit_binding "submit receipt did not appear within 60 seconds"
  exit 2
fi
# END T2195 SUBMIT RECEIPT PIN

if ! initialize_judgment_source_state; then
  exit 2
fi
if [[ ! "$CURRENT_COMMIT" =~ ^[0-9a-f]{40}$ ]]; then
  write_failure 2 source_identity "outer source commit is not a full OID"
  exit 2
fi
CURRENT_SCRIPT_SHA=$(sha256sum "$TOOLS/mocc_trace_pilot.sh" | awk '{print $1}')
python3 - "$ATTEMPT_RECEIPT" "$CURRENT_COMMIT" "$CURRENT_SCRIPT_SHA" "$PBS_JOBID" \
  "$PROJECT" "$QUEUE" "$NODES" "$REQUESTED_S" "$BASE_OID" "$NEW_OID" \
  "$TRACE_MODE" "$WORKLOAD_JSON" "$ATTEMPTS_ROOT" "$SUBMISSION_DIR" \
  "$T1943_G2" "$SUBMIT_RECEIPT_SHA" <<'PY'
import hashlib
import json
import os
import stat
import sys

(
    path, commit, script_sha, job_id, project, queue, nodes, requested_s,
    base_oid, new_oid, trace_mode, workload_json, attempts_root, submission_dir,
    t1943_g2, pinned_sha,
) = sys.argv[1:]
receipt_fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
try:
    receipt_info = os.fstat(receipt_fd)
    if not stat.S_ISREG(receipt_info.st_mode):
        raise SystemExit("pinned submit receipt is not a regular file")
    with os.fdopen(receipt_fd, "rb") as handle:
        receipt_fd = -1
        receipt_bytes = handle.read()
finally:
    if receipt_fd >= 0:
        os.close(receipt_fd)
if hashlib.sha256(receipt_bytes).hexdigest() != pinned_sha:
    raise SystemExit("pinned submit receipt digest differs")
receipt = json.loads(receipt_bytes.decode("utf-8"))
qsub = receipt["qsub"]
mocc = receipt["mocc_trace"]

def normalized(value):
    value = str(value)
    return value[2:] if value.startswith("0:") else value

checks = {
    "schema": receipt.get("schema_version") == "pegasus-submit-receipt/v2",
    "dry_run": receipt.get("dry_run") is False,
    "source_commit": receipt.get("source_commit") == commit,
    "job_script_sha256": receipt.get("job_script_sha256") == script_sha,
    "request_id": normalized(qsub.get("request_id")) == normalized(job_id),
    "project": qsub.get("project") == project,
    "queue": qsub.get("queue") == queue,
    "nodes": qsub.get("nodes") == int(nodes),
    "walltime": qsub.get("elapstim_req_s") == int(requested_s),
    "base_oid": mocc.get("base_oid") == base_oid,
    "new_oid": mocc.get("new_oid") == new_oid,
    "trace_mode": mocc.get("trace_mode") == int(trace_mode),
    "workload": mocc.get("workload") == json.loads(workload_json),
    "t1943_g2_discriminator": (
        mocc.get("t1943_g2_discriminator") is True
        if int(t1943_g2)
        else "t1943_g2_discriminator" not in mocc
    ),
}


def option_value(argv, option):
    if not isinstance(argv, list) or argv.count(option) != 1:
        return None
    index = argv.index(option)
    if index + 1 >= len(argv) or not isinstance(argv[index + 1], str):
        return None
    return argv[index + 1]


argv = qsub.get("argv")
export_spec = option_value(argv, "-v")
checks.update(
    {
        "attempts_root_export": (
            isinstance(export_spec, str)
            and f"IZANAGI_MOCC_TRACE_ATTEMPTS_ROOT={attempts_root}"
            in export_spec.split(",")
        ),
        "t1943_export": (
            isinstance(export_spec, str)
            and (
                "IZANAGI_MOCC_G2_DISCRIMINATOR=1" in export_spec.split(",")
                if int(t1943_g2)
                else not any(
                    item.startswith("IZANAGI_MOCC_G2_DISCRIMINATOR=")
                    for item in export_spec.split(",")
                )
            )
        ),
        "pbs_stdout": option_value(argv, "-o")
        == os.path.join(submission_dir, "pbs-job.stdout"),
        "pbs_stderr": option_value(argv, "-e")
        == os.path.join(submission_dir, "pbs-job.stderr"),
    }
)
if not all(checks.values()):
    raise SystemExit("submit binding mismatch: " + repr(checks))
PY

# BEGIN T2195 POLICY BINDING GATE
if ! policy_binding_output=$(python3 - "$POLICY" "$ATTEMPT_RECEIPT" \
    "$SUBMIT_RECEIPT_SHA" "$REPO_ROOT" \
    "$EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON" \
    "$POLICY_PARSE_RAW_SHA256" "$IZANAGI_MOCC_POLICY_RAW_SHA256" \
    2>&1 <<'PY_T2195_POLICY_BINDING'
import hashlib
import json
import os
import stat
import sys

(
    policy_path,
    receipt_path,
    pinned_receipt_sha,
    repo_root,
    shell_mapping_json,
    parsed_policy_sha,
    exported_policy_sha,
) = sys.argv[1:]


def reject_duplicate_keys(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key: {key}")
        document[key] = value
    return document


def _reject_non_finite(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def read_policy_bytes(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise ValueError("policy cannot be opened without following") from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("policy is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    finally:
        if fd >= 0:
            os.close(fd)


def read_receipt_bytes(path):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    except OSError as exc:
        raise ValueError(
            "pinned submit receipt cannot be opened without following"
        ) from exc
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise ValueError("pinned submit receipt is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            return handle.read()
    finally:
        if fd >= 0:
            os.close(fd)


def parse_document(raw, label):
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"{label} is not strict duplicate-free JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{label} top level is not an object")
    return value


def require_sha(value, label):
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{label} is not 64 lowercase hex")
    return value


def require_mapping(value, label):
    if type(value) is not dict or set(value) != {"gcc", "g++"}:
        raise ValueError(f"{label} keys differ")
    for role, digest in value.items():
        require_sha(digest, f"{label}.{role}")
    return value


try:
    policy_bytes = read_policy_bytes(policy_path)
    receipt_bytes = read_receipt_bytes(receipt_path)
    live_policy_sha = hashlib.sha256(policy_bytes).hexdigest()
    if hashlib.sha256(receipt_bytes).hexdigest() != pinned_receipt_sha:
        raise ValueError("pinned submit receipt digest differs")
    policy = parse_document(policy_bytes, "policy")
    receipt = parse_document(receipt_bytes, "pinned submit receipt")
    live_mapping = require_mapping(
        policy.get("expected_compiler_version_body_sha256"),
        "live policy compiler mapping",
    )
    try:
        shell_mapping = require_mapping(
            json.loads(
                shell_mapping_json,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=_reject_non_finite,
            ),
            "early policy compiler mapping",
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("early policy compiler mapping is invalid") from exc
    receipt_policy = receipt.get("policy")
    if not isinstance(receipt_policy, dict):
        raise ValueError("submit receipt policy is not an object")
    receipt_policy_sha = require_sha(
        receipt_policy.get("raw_sha256"), "submit receipt policy raw sha"
    )
    receipt_mapping = require_mapping(
        receipt_policy.get("expected_compiler_version_body_sha256"),
        "submit receipt compiler mapping",
    )
    require_sha(parsed_policy_sha, "early policy raw sha")
    require_sha(exported_policy_sha, "exported policy raw sha")
    if live_policy_sha != parsed_policy_sha:
        raise ValueError("live policy raw sha differs from early parse")
    if live_policy_sha != receipt_policy_sha:
        raise ValueError("live policy raw sha differs from submit receipt")
    if live_policy_sha != exported_policy_sha:
        raise ValueError("live policy raw sha differs from qsub environment")
    if live_mapping != shell_mapping:
        raise ValueError("live policy compiler mapping differs from early parse")
    if live_mapping != receipt_mapping:
        raise ValueError("live policy compiler mapping differs from submit receipt")
    if os.path.relpath(policy_path, repo_root) != (
        "tools/pegasus/mocc_trace_v1_policy.json"
    ):
        raise ValueError("live policy repo path differs")
    qsub = receipt.get("qsub")
    if not isinstance(qsub, dict):
        raise ValueError("submit receipt qsub is not an object")
    argv = qsub.get("argv")
    if not isinstance(argv, list) or argv.count("-v") != 1:
        raise ValueError("submit receipt qsub -v differs")
    export_index = argv.index("-v") + 1
    if export_index >= len(argv) or not isinstance(argv[export_index], str):
        raise ValueError("submit receipt qsub -v value differs")
    prefix = "IZANAGI_MOCC_POLICY_RAW_SHA256="
    raw_exports = [
        item for item in argv[export_index].split(",") if item.startswith(prefix)
    ]
    if raw_exports != [prefix + exported_policy_sha]:
        raise ValueError("submit receipt policy raw sha export differs")
except (OSError, ValueError) as exc:
    raise SystemExit(str(exc)) from exc

print(live_policy_sha)
PY_T2195_POLICY_BINDING
); then
  write_failure 2 policy_binding "$policy_binding_output"
  exit 2
fi
POLICY_RAW_SHA256=$policy_binding_output
# END T2195 POLICY BINDING GATE

QSTAT_JOBID=${PBS_JOBID#0:}
qstat_rc=0
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-f.stdout" \
  2>"$ATTEMPT_DIR/qstat-f.stderr" || qstat_rc=$?
printf '%s\n' "$qstat_rc" >"$ATTEMPT_DIR/qstat-f.rc"
HOSTNAME_SHORT=$(hostname)
HOSTNAME_FQDN=$(hostname -f 2>/dev/null || hostname)
printf '%s\n' "$HOSTNAME_SHORT" >"$ATTEMPT_DIR/hostname.stdout"
printf '%s\n' "$HOSTNAME_FQDN" >"$ATTEMPT_DIR/hostname-f.stdout"

readarray -t qstat_values < <(python3 - "$ATTEMPT_DIR/qstat-f.stdout" "$HOSTNAME_SHORT" "$qstat_rc" <<'PY'
import re
import subprocess
import sys

path, observed, rc = sys.argv[1:]
text = open(path, encoding="utf-8", errors="replace").read()
assigned = "unavailable"
started = "unavailable"
if rc == "0":
    for key in ("exec_host", "exec_vnode", "assigned_host", "vnode"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*([^\n]+)", text)
        if match:
            raw = match.group(1).strip()
            if raw.lower() == "(none)":
                continue
            token = re.split(r"[:+/,()\s]", raw.lstrip("("))[0]
            if token:
                assigned = token
                break
    if assigned == "unavailable":
        match = re.search(
            r"(?im)^\s*Execution Hosts\(JSVNO\):\s*$\n[ \t]+([^\s(),:+/]+)",
            text,
        )
        if match and match.group(1).lower() != "none":
            assigned = match.group(1)
    if assigned == "unavailable" and observed.split(".")[0] in text:
        assigned = observed.split(".")[0]
    for key in ("stime", "start_time", "start", "Started Request Time"):
        match = re.search(rf"(?im)^\s*{re.escape(key)}\s*=\s*(.+?)\s*$", text)
        if not match:
            continue
        raw = match.group(1).strip()
        if raw.lower() == "(none)":
            continue
        if raw.isdigit() and int(raw) > 1_000_000_000:
            started = raw
            break
        proc = subprocess.run(["date", "-d", raw, "+%s"], capture_output=True, text=True)
        if proc.returncode == 0 and proc.stdout.strip().isdigit():
            started = proc.stdout.strip()
            break
print(assigned)
print(started)
PY
)
ASSIGNED_HOST=${qstat_values[0]:-unavailable}
SCHEDULER_STARTED_EPOCH=${qstat_values[1]:-unavailable}
if [[ "$qstat_rc" -ne 0 || "$ASSIGNED_HOST" == unavailable || "$SCHEDULER_STARTED_EPOCH" == unavailable ]]; then
  python3 - "$ATTEMPT_DIR/allocation-unavailable.json" "$PBS_JOBID" "$qstat_rc" \
    "$ASSIGNED_HOST" "$HOSTNAME_SHORT" "$SCHEDULER_STARTED_EPOCH" <<'PY'
import json
import sys
import time

path, job, rc, assigned, host, started = sys.argv[1:]
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-pilot-allocation/v1",
            "pbs_jobid": job,
            "qstat_rc": int(rc),
            "assigned_host_qstat": assigned,
            "hostname_observed": host,
            "scheduler_started_epoch": started,
            "recorded_epoch": int(time.time()),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  write_failure 2 allocation "qstat allocation/start binding unavailable"
  exit 2
fi
if [[ "$ASSIGNED_HOST" != "$HOSTNAME_SHORT" &&
      "$ASSIGNED_HOST" != "$HOSTNAME_FQDN" ]]; then
  write_failure 2 allocation "qstat assigned host has no exact hostname observation"
  exit 2
fi

BOOT_ID=$(cat /proc/sys/kernel/random/boot_id)
DEADLINE_EPOCH=$((SCHEDULER_STARTED_EPOCH + REQUESTED_S))
export IZANAGI_RESERVATION_JOB_ID="$PBS_JOBID"
export IZANAGI_RESERVATION_REQUESTED_S="$REQUESTED_S"
export IZANAGI_RESERVATION_SCHEDULER_STARTED_EPOCH="$SCHEDULER_STARTED_EPOCH"
export IZANAGI_RESERVATION_DEADLINE_EPOCH="$DEADLINE_EPOCH"
export IZANAGI_RESERVATION_HOST="$HOSTNAME_SHORT"
export IZANAGI_RESERVATION_BOOT_ID="$BOOT_ID"
export IZANAGI_RESERVATION_SCRIPT_SHA256="$CURRENT_SCRIPT_SHA"
export IZANAGI_RESERVATION_NONCE="$IZANAGI_SUBMISSION_NONCE"

python3 - "$ATTEMPT_DIR/reservation.json" <<'PY'
import json
import os
import sys
import time

keys = (
    "JOB_ID", "REQUESTED_S", "SCHEDULER_STARTED_EPOCH", "DEADLINE_EPOCH",
    "HOST", "BOOT_ID", "SCRIPT_SHA256", "NONCE",
)
payload = {
    key.lower(): os.environ["IZANAGI_RESERVATION_" + key]
    for key in keys
}
for key in ("requested_s", "scheduler_started_epoch", "deadline_epoch"):
    payload[key] = int(payload[key])
payload["recorded_epoch"] = int(time.time())
with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

check_window() {
  local now remaining
  now=$(date +%s)
  remaining=$((DEADLINE_EPOCH - now - FINALIZE_RESERVE_S))
  printf '%s\n' "$remaining" >"$ATTEMPT_DIR/window-remaining-${1}.stdout"
  if [[ "$remaining" -le 0 ]]; then
    write_failure 2 reservation "no measured window remains before finalize reserve ($1)"
    exit 2
  fi
}
check_window before-build

python3 - "$ATTEMPT_DIR/topology.json" "$EXPECTED_CORES" <<'PY'
import json
import os
import pathlib
import sys

path, expected = sys.argv[1:]
visible = sorted(os.sched_getaffinity(0))
pairs = set()
for cpu in visible:
    root = pathlib.Path("/sys/devices/system/cpu") / f"cpu{cpu}" / "topology"
    try:
        package = int((root / "physical_package_id").read_text().strip())
        core = int((root / "core_id").read_text().strip())
    except (OSError, ValueError) as exc:
        raise SystemExit(f"cannot derive physical core topology: {exc}")
    pairs.add((package, core))
payload = {
    "affinity_cpus": visible,
    "cpuset_size": len(visible),
    "physical_visible": len(pairs),
    "ht_off": len(visible) == len(pairs),
    "expected_physical_cores": int(expected),
}
if len(pairs) != int(expected) or len(visible) != int(expected):
    raise SystemExit("cpuset/physical core count differs from policy")
with open(path, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY

CPU_MODEL=$(awk -F: '/^[[:space:]]*model name[[:space:]]*:/ {
  sub(/^[[:space:]]+/, "", $2); print $2; exit
}' /proc/cpuinfo)
printf '%s\n' "$CPU_MODEL" >"$ATTEMPT_DIR/cpu-model.stdout"
CPU_MODEL_NORMALIZED=$(sed -E \
  's/\((R|TM)\)//g; s/[[:space:]]+/ /g; s/^[[:space:]]+//; s/[[:space:]]+$//' \
  <<<"$CPU_MODEL")
if [[ "$CPU_MODEL_NORMALIZED" != "$EXPECTED_CPU" ]]; then
  write_failure 2 environment \
    "CPU model mismatch: expected=$EXPECTED_CPU observed_normalized=$CPU_MODEL_NORMALIZED"
  exit 2
fi

module_rc=0
module -t list >"$ATTEMPT_DIR/module-list.stdout" 2>"$ATTEMPT_DIR/module-list.stderr" || module_rc=$?
printf '%s\n' "$module_rc" >"$ATTEMPT_DIR/module-list.rc"
if [[ "$module_rc" -ne 0 ]]; then
  write_failure "$module_rc" environment "module -t list failed"
  exit "$module_rc"
fi

if ! CC_COMMAND=$(command -v gcc) || [[ -z "$CC_COMMAND" ]] ||
    ! CC_PATH=$(realpath -- "$CC_COMMAND"); then
  write_failure 2 compiler "gcc compiler version body mismatch/probe failed"
  exit 2
fi
if ! CXX_COMMAND=$(command -v g++) || [[ -z "$CXX_COMMAND" ]] ||
    ! CXX_PATH=$(realpath -- "$CXX_COMMAND"); then
  write_failure 2 compiler "g++ compiler version body mismatch/probe failed"
  exit 2
fi
CMAKE_PATH=$(realpath "$(command -v cmake)")
printf '%s\n' "$CC_PATH" >"$ATTEMPT_DIR/compiler-gcc.path"
printf '%s\n' "$CXX_PATH" >"$ATTEMPT_DIR/compiler-gxx.path"
printf '%s\n' "$CMAKE_PATH" >"$ATTEMPT_DIR/cmake.path"
if ! "$CC_PATH" --version >"$ATTEMPT_DIR/compiler-gcc.version" 2>&1; then
  write_failure 2 compiler "gcc compiler version body mismatch/probe failed"
  exit 2
fi
if ! "$CXX_PATH" --version >"$ATTEMPT_DIR/compiler-gxx.version" 2>&1; then
  write_failure 2 compiler "g++ compiler version body mismatch/probe failed"
  exit 2
fi
"$CMAKE_PATH" --version >"$ATTEMPT_DIR/cmake.version" 2>&1

# BEGIN T1718 COMPILER VERSION BODY GATE
# この gate が検出するのは、承認 policy と実行時 archive の非 debug 射影の差、および
# `tool_version_body(--version)` の差である。同じ射影を出す道具の置換、debug 情報だけの差、
# 同じ version body を保った compiler binary の置換、gcc と g++ の role 混成は検出しない。
# 適用範囲は S8b `sort_best` の masstree prebuild と mocc trace pilot の compiler であり、
# 全 CCBench consumer を覆うものではない。
if ! compiler_gate_error=$(python3 - \
    "$REPO_ROOT" "$EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON" \
    "$ATTEMPT_DIR/compiler-gcc.version" \
    "$ATTEMPT_DIR/compiler-gxx.version" 2>&1 <<'PY_T1718_COMPILER_GATE'
import hashlib
import json
from pathlib import Path
import sys

repo_root = Path(sys.argv[1])
sys.path.insert(0, str(repo_root))
from orchestrator.campaign.toolchain_binding import tool_version_body

expected = json.loads(sys.argv[2])
for role, version_path in (("gcc", Path(sys.argv[3])), ("g++", Path(sys.argv[4]))):
    try:
        raw = version_path.read_text(encoding="utf-8", errors="strict")
        observed = hashlib.sha256(
            tool_version_body(raw).encode("utf-8")
        ).hexdigest()
        if observed != expected[role]:
            raise ValueError(
                f"expected={expected[role]} observed={observed}"
            )
    except (OSError, UnicodeError, ValueError, KeyError, TypeError) as exc:
        raise SystemExit(
            f"{role} compiler version body mismatch/probe failed: {exc}"
        )
PY_T1718_COMPILER_GATE
); then
  write_failure 2 compiler "$compiler_gate_error"
  exit 2
fi
# END T1718 COMPILER VERSION BODY GATE

CACHE_ROOT=${!THIRD_PARTY_CACHE_ENV:-}
if [[ -z "$CACHE_ROOT" ]]; then
  write_failure 2 third_party "$THIRD_PARTY_CACHE_ENV is missing"
  exit 2
fi
THIRD_PARTY_STAGING_ROOT="$TMPDIR/thirdparty-src"
# BEGIN T2780 HYDRATE INTERPRETER GATE
HYDRATE_PY=""
hydrate_py_rejected=""
for py_name in python3 python3.10 python3.11 python3.12; do
  py_cmd=$(command -v -- "$py_name") || continue
  py_resolved=$(realpath -e -- "$py_cmd") || continue
  [[ -x "$py_resolved" ]] || continue
  if (
    cd "$REPO_ROOT" &&
    PYTHONPATH="$REPO_ROOT/orchestrator:$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
    "$py_resolved" -c \
      'import sys; import orchestrator.campaign.silo_ladder_rung1; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
      "$REPO_ROOT"
  ) >/dev/null 2>&1; then
    HYDRATE_PY="$py_resolved"
    break
  fi
  hydrate_py_rejected+="${hydrate_py_rejected:+ }$py_name=$py_resolved"
done
if [[ -z "$HYDRATE_PY" ]]; then
  hydrate_gate_message="no python3 >= 3.10 candidate can import orchestrator.campaign.silo_ladder_rung1 (rejected: ${hydrate_py_rejected:-none})"
  printf '%s\n' "$hydrate_gate_message" \
    >"$ATTEMPT_DIR/third-party-hydrate.stderr"
  write_failure 2 third_party "$hydrate_gate_message"
  exit 2
fi
# END T2780 HYDRATE INTERPRETER GATE
timeout 20 "$HYDRATE_PY" "$TOOLS/fetch_third_party.py" hydrate --repo-root "$REPO_ROOT" \
  --cache-root "$CACHE_ROOT" --staging-root "$THIRD_PARTY_STAGING_ROOT" \
  >"$ATTEMPT_DIR/third-party-hydrate.json" \
  2>"$ATTEMPT_DIR/third-party-hydrate.stderr"
THIRD_PARTY_SOURCE_ROOT=$(python3 - "$ATTEMPT_DIR/third-party-hydrate.json" <<'PY'
import json
import os
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
value = payload.get("source_root")
if type(value) is not str or not os.path.isabs(value):
    raise SystemExit("hydrate output .source_root is not an absolute path")
print(value)
PY
)
if [[ ! -d "$THIRD_PARTY_SOURCE_ROOT" ]]; then
  write_failure 2 third_party "hydrate source_root is missing"
  exit 2
fi
printf '%s\n' "$THIRD_PARTY_SOURCE_ROOT" >"$ATTEMPT_DIR/third-party-source-root.stdout"
THIRDPARTY_SOURCE_ROOT="$THIRD_PARTY_SOURCE_ROOT"
GFLAGS_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/gflags"
GLOG_SOURCE_PATH="$THIRDPARTY_SOURCE_ROOT/glog"

if [[ ! -d "$GFLAGS_SOURCE_PATH" ]]; then
  write_failure 2 gflags "gflags source path missing"
  exit 2
fi
GFLAGS_SOURCE_HEAD=$(git -C "$GFLAGS_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GFLAGS_SOURCE_HEAD" >"$ATTEMPT_DIR/gflags-source-head.stdout"
if [[ "$GFLAGS_SOURCE_HEAD" != "$GFLAGS_EXPECTED_HEAD" ]]; then
  write_failure 2 gflags "gflags source HEAD mismatch"
  exit 2
fi
GFLAGS_STATUS=$(git -C "$GFLAGS_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GFLAGS_STATUS" >"$ATTEMPT_DIR/gflags-source-status.stdout"
if [[ -n "$GFLAGS_STATUS" ]]; then
  write_failure 2 gflags "gflags working tree is dirty"
  exit 2
fi
GFLAGS_BUILD_DIR="$TMPDIR/gflags-build"
GFLAGS_INSTALL_DIR="$TMPDIR/gflags-install"
mkdir "$GFLAGS_BUILD_DIR"
unset CMAKE_C_COMPILER_LAUNCHER CMAKE_CXX_COMPILER_LAUNCHER RULE_LAUNCH_COMPILE
gflags_configure_argv=(
  cmake -S "$GFLAGS_SOURCE_PATH" -B "$GFLAGS_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DREGISTER_INSTALL_PREFIX=OFF
  "-DCMAKE_INSTALL_PREFIX=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$CC_PATH"
  "-DCMAKE_CXX_COMPILER=$CXX_PATH"
  -DCMAKE_C_COMPILER_LAUNCHER=
  -DCMAKE_CXX_COMPILER_LAUNCHER=
  -DRULE_LAUNCH_COMPILE=
  -DCMAKE_TOOLCHAIN_FILE=
)
gflags_build_argv=(cmake --build "$GFLAGS_BUILD_DIR" -j 48)
gflags_install_argv=(cmake --install "$GFLAGS_BUILD_DIR")
python3 - "$ATTEMPT_DIR/gflags-configure.argv.json" "${gflags_configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
timeout 60 "${gflags_configure_argv[@]}" >"$ATTEMPT_DIR/gflags-configure.stdout" 2>"$ATTEMPT_DIR/gflags-configure.stderr"
timeout 60 "${gflags_build_argv[@]}" >"$ATTEMPT_DIR/gflags-build.stdout" 2>"$ATTEMPT_DIR/gflags-build.stderr"
timeout 60 "${gflags_install_argv[@]}" >"$ATTEMPT_DIR/gflags-install.stdout" 2>"$ATTEMPT_DIR/gflags-install.stderr"

if [[ ! -d "$GLOG_SOURCE_PATH" ]]; then
  write_failure 2 glog "glog source path missing"
  exit 2
fi
GLOG_SOURCE_HEAD=$(git -C "$GLOG_SOURCE_PATH" rev-parse HEAD)
printf '%s\n' "$GLOG_SOURCE_HEAD" >"$ATTEMPT_DIR/glog-source-head.stdout"
if [[ "$GLOG_SOURCE_HEAD" != "$GLOG_EXPECTED_HEAD" ]]; then
  write_failure 2 glog "glog source HEAD mismatch"
  exit 2
fi
GLOG_STATUS=$(git -C "$GLOG_SOURCE_PATH" status --porcelain --untracked-files=all)
printf '%s' "$GLOG_STATUS" >"$ATTEMPT_DIR/glog-source-status.stdout"
if [[ -n "$GLOG_STATUS" ]]; then
  write_failure 2 glog "glog working tree is dirty"
  exit 2
fi
GLOG_BUILD_DIR="$TMPDIR/glog-build"
GLOG_INSTALL_DIR="$TMPDIR/glog-install"
mkdir "$GLOG_BUILD_DIR"
glog_configure_argv=(
  cmake -S "$GLOG_SOURCE_PATH" -B "$GLOG_BUILD_DIR"
  -DCMAKE_BUILD_TYPE=Release
  -DBUILD_SHARED_LIBS=OFF
  -DCMAKE_POSITION_INDEPENDENT_CODE=ON
  -DWITH_GTEST=OFF
  -DBUILD_TESTING=OFF
  -DWITH_UNWIND=OFF
  "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"
  "-DCMAKE_INSTALL_PREFIX=$GLOG_INSTALL_DIR"
  "-DCMAKE_C_COMPILER=$CC_PATH"
  "-DCMAKE_CXX_COMPILER=$CXX_PATH"
  -DCMAKE_C_COMPILER_LAUNCHER=
  -DCMAKE_CXX_COMPILER_LAUNCHER=
  -DRULE_LAUNCH_COMPILE=
  -DCMAKE_TOOLCHAIN_FILE=
)
glog_build_argv=(cmake --build "$GLOG_BUILD_DIR" -j 48)
glog_install_argv=(cmake --install "$GLOG_BUILD_DIR")
python3 - "$ATTEMPT_DIR/glog-configure.argv.json" "${glog_configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
timeout 120 "${glog_configure_argv[@]}" >"$ATTEMPT_DIR/glog-configure.stdout" 2>"$ATTEMPT_DIR/glog-configure.stderr"
timeout 120 "${glog_build_argv[@]}" >"$ATTEMPT_DIR/glog-build.stdout" 2>"$ATTEMPT_DIR/glog-build.stderr"
timeout 120 "${glog_install_argv[@]}" >"$ATTEMPT_DIR/glog-install.stdout" 2>"$ATTEMPT_DIR/glog-install.stderr"

export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR;$GLOG_INSTALL_DIR"

CCBENCH_BASE="$REPO_ROOT/external/ccbench"
if [[ ! -d "$CCBENCH_BASE" ]]; then
  write_failure 2 source_materialization "external/ccbench is missing"
  exit 2
fi
RESOLVED_NEW=$(git -C "$CCBENCH_BASE" rev-parse "$NEW_OID^{commit}")
if [[ "$RESOLVED_NEW" != "$NEW_OID" ]]; then
  write_failure 2 source_materialization "policy new_oid is absent from submodule"
  exit 2
fi
if ! git -C "$CCBENCH_BASE" merge-base --is-ancestor "$BASE_OID" "$NEW_OID"; then
  write_failure 2 source_materialization "policy base_oid is not an ancestor of new_oid"
  exit 2
fi
printf '%s\n' "$(git -C "$CCBENCH_BASE" rev-parse HEAD)" >"$ATTEMPT_DIR/submodule-head.stdout"
git -C "$CCBENCH_BASE" status --porcelain --untracked-files=all \
  >"$ATTEMPT_DIR/submodule-status.stdout"
if [[ -s "$ATTEMPT_DIR/submodule-status.stdout" ]]; then
  write_failure 2 source_materialization "submodule working tree is dirty"
  exit 2
fi
BUILD_SOURCE="$TMPDIR/ccbench-source"
git -C "$CCBENCH_BASE" worktree add --detach "$BUILD_SOURCE" "$NEW_OID" \
  >"$ATTEMPT_DIR/worktree-add.stdout" 2>"$ATTEMPT_DIR/worktree-add.stderr"

PATCH_PATH=""
PATCH_SHA=""
PATCHED_SOURCE_SHA=""
# BEGIN T2780 INSTRUMENTATION PATCH
if [[ "$T1943_G2" -eq 1 ]]; then
  if ! PATCH_PATH=$(realpath -e -- \
    "$REPO_ROOT/patches/instr-mocc-lock-coverage.patch"); then
    write_failure 2 instrumentation_patch "instrumentation patch cannot be resolved"
    exit 2
  fi
  if [[ ! -f "$PATCH_PATH" || -L "$PATCH_PATH" ]]; then
    write_failure 2 instrumentation_patch "instrumentation patch is not a real file"
    exit 2
  fi
  if ! PATCH_SHA=$(sha256sum "$PATCH_PATH" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "instrumentation patch hash failed"
    exit 2
  fi
  printf '%s\n' "$PATCH_SHA" >"$ATTEMPT_DIR/instr-patch.sha256"
  : >"$ATTEMPT_DIR/instr-patch-apply.stdout"
  : >"$ATTEMPT_DIR/instr-patch-apply.stderr"

  if ! git -C "$BUILD_SOURCE" apply --numstat "$PATCH_PATH" \
    >"$ATTEMPT_DIR/instr-patch.numstat" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch numstat failed"
    exit 2
  fi
  if ! awk -F '\t' '
    NF != 3 || $1 !~ /^[0-9]+$/ || $2 !~ /^[0-9]+$/ ||
      $3 != "cc/mocc/transaction.cc" { bad=1 }
    END { exit (bad || NR != 1) }
  ' "$ATTEMPT_DIR/instr-patch.numstat"; then
    write_failure 2 instrumentation_patch "instrumentation patch touch set differs"
    exit 2
  fi
  if ! git -C "$BUILD_SOURCE" apply --check "$PATCH_PATH" \
    >>"$ATTEMPT_DIR/instr-patch-apply.stdout" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch check failed"
    exit 2
  fi
  if ! git -C "$BUILD_SOURCE" apply "$PATCH_PATH" \
    >>"$ATTEMPT_DIR/instr-patch-apply.stdout" \
    2>>"$ATTEMPT_DIR/instr-patch-apply.stderr"; then
    write_failure 2 instrumentation_patch "instrumentation patch apply failed"
    exit 2
  fi
  if ! patch_sha_after=$(sha256sum "$PATCH_PATH" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "instrumentation patch post-apply hash failed"
    exit 2
  fi
  if [[ "$patch_sha_after" != "$PATCH_SHA" ]]; then
    write_failure 2 instrumentation_patch "instrumentation patch changed during application"
    exit 2
  fi
  if ! PATCHED_SOURCE_SHA=$(sha256sum \
    "$BUILD_SOURCE/cc/mocc/transaction.cc" | awk '{print $1}'); then
    write_failure 2 instrumentation_patch "patched source hash failed"
    exit 2
  fi
  printf '%s\n' "$PATCHED_SOURCE_SHA" >"$ATTEMPT_DIR/instr-patch-source.sha256"
fi
# END T2780 INSTRUMENTATION PATCH

build_mode() {
  local mode=$1
  BUILD_DIR="$BUILD_SOURCE-build-trace$mode"
  mkdir "$BUILD_DIR"
  local -a configure_argv=(
    cmake -S "$BUILD_SOURCE" -B "$BUILD_DIR"
    -DCMAKE_BUILD_TYPE=Release
    -DENABLE_SANITIZER=OFF
    "-DCCBENCH_TRACE=$mode"
    -DCCBENCH_BACK_OFF=0
    -DCCBENCH_BACKOFF_FIXED=-1
    -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
    -DCCBENCH_NO_WAIT_OF_TICTOC=0
    -DCCBENCH_WAL=0
    -DCCBENCH_CCACHE=OFF
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
    -DCMAKE_C_COMPILER_LAUNCHER=
    -DCMAKE_CXX_COMPILER_LAUNCHER=
    -DRULE_LAUNCH_COMPILE=
    -DCMAKE_TOOLCHAIN_FILE=
    "-DCMAKE_PREFIX_PATH=$CMAKE_PREFIX_PATH"
    "-DFETCHCONTENT_SOURCE_DIR_MASSTREE=$THIRD_PARTY_SOURCE_ROOT/masstree"
    "-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=$THIRD_PARTY_SOURCE_ROOT/mimalloc"
    "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$THIRD_PARTY_SOURCE_ROOT/googletest"
    "-DIZANAGI_GFLAGS_SRC_HEAD=$GFLAGS_SOURCE_HEAD"
    "-DIZANAGI_GLOG_SRC_HEAD=$GLOG_SOURCE_HEAD"
    "-DCMAKE_C_COMPILER=$CC_PATH"
    "-DCMAKE_CXX_COMPILER=$CXX_PATH"
    -DCMAKE_CXX_FLAGS=
  )
  local -a build_argv=(cmake --build "$BUILD_DIR" --target "$CMAKE_TARGET" -j 48)
  python3 - "$ATTEMPT_DIR/configure-trace$mode.argv.json" "${configure_argv[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(sys.argv[2:], handle, ensure_ascii=False, indent=2)
    handle.write("\n")
PY
  timeout 180 "${configure_argv[@]}" \
    >"$ATTEMPT_DIR/configure-trace$mode.stdout" \
    2>"$ATTEMPT_DIR/configure-trace$mode.stderr"
  timeout 600 "${build_argv[@]}" \
    >"$ATTEMPT_DIR/build-trace$mode.stdout" \
    2>"$ATTEMPT_DIR/build-trace$mode.stderr"
  BINARY="$BUILD_DIR/cc/mocc/$CMAKE_TARGET"
  if [[ ! -x "$BINARY" ]]; then
    write_failure 2 build "Mocc binary is missing after TRACE=$mode build"
    exit 2
  fi
  BINARY_SHA=$(sha256sum "$BINARY" | awk '{print $1}')
  printf '%s\n' "$BINARY_SHA" >"$ATTEMPT_DIR/binary-trace$mode.sha256"
  realpath "$BINARY" >"$ATTEMPT_DIR/binary-trace$mode.path"
  "$CXX_PATH" --version >"$ATTEMPT_DIR/compiler-used.version" 2>&1
}

if [[ "$TRACE_MODE" -eq 0 || "$T1943_G2" -eq 1 ]]; then
  # D297 checker is deliberately a hard gate.  Its nonzero result means that
  # TRACE=0 execution is skipped; no fallback or relaxed branch is permitted.
  # This check proves the D297 guarantee and is one necessary condition for
  # complete trace removal from the measurement build; it does not prove that removal.
  build_mode 0
  CHECKER_TOOL_PATH=$(realpath -e -- "$REPO_ROOT/tools/check_trace0_preprocess_identity.py")
  if [[ ! -f "$CHECKER_TOOL_PATH" || -L "$CHECKER_TOOL_PATH" ]]; then
    write_failure 2 trace0_preprocess_identity \
      "TRACE=0 identity checker implementation is not a real file"
    exit 2
  fi
  CHECKER_TOOL_SHA=$(sha256sum "$CHECKER_TOOL_PATH" | awk '{print $1}')
  CHECKER_PY=""
  checker_py_rejected=""
  for py_name in python3 python3.10 python3.11 python3.12; do
    py_cmd=$(command -v -- "$py_name") || continue
    py_resolved=$(realpath -e -- "$py_cmd") || continue
    [[ -x "$py_resolved" ]] || continue
    if (
      cd "$REPO_ROOT" &&
      PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
      "$py_resolved" -c \
        'import sys; import orchestrator.campaign.source_digest; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
        "$REPO_ROOT"
    ) >/dev/null 2>&1; then
      CHECKER_PY="$py_resolved"
      break
    fi
    checker_py_rejected+="${checker_py_rejected:+ }$py_name=$py_resolved"
  done

  CHECKER_RC=0
  if [[ -n "$CHECKER_PY" ]]; then
    (
      cd "$REPO_ROOT" &&
      PYTHONPATH="$REPO_ROOT${PYTHONPATH:+:$PYTHONPATH}" \
      "$CHECKER_PY" "$REPO_ROOT/tools/check_trace0_preprocess_identity.py" \
        --repo "$BUILD_SOURCE" --old "$BASE_OID" --new "$NEW_OID" \
        --cxx "$CXX_PATH" --expect-paths cc/mocc/transaction.cc
    ) >"$ATTEMPT_DIR/trace0-preprocess-identity.json" \
      2>"$ATTEMPT_DIR/trace0-preprocess-identity.stderr" || CHECKER_RC=$?
  else
    CHECKER_RC=2
    checker_gate_message="no python3 >= 3.10 candidate can import orchestrator.campaign.source_digest (rejected: ${checker_py_rejected:-none})"
    printf '%s\n' "$checker_gate_message" \
      >"$ATTEMPT_DIR/trace0-preprocess-identity.stderr"
  fi
  printf '%s\n' "$CHECKER_RC" >"$ATTEMPT_DIR/trace0-preprocess-identity.rc"
  if [[ "$CHECKER_RC" -ne 0 ]]; then
    python3 - "$ATTEMPT_DIR/trace0-execution.json" "$CHECKER_RC" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace0-execution/v1",
            "status": "skipped",
            "reason": "TRACE=0 preprocess identity checker failed closed",
            "checker_rc": int(sys.argv[2]),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  fi
  if [[ "${T1943_G2:-0}" -ne 1 ]]; then
    if ! verify_post_judgment_source_state; then
      exit 2
    fi
  fi
  if [[ "$CHECKER_RC" -ne 0 ]]; then
    write_failure "$CHECKER_RC" trace0_preprocess_identity \
      "TRACE=0 workload skipped because preprocess identity checker failed closed"
    exit "$CHECKER_RC"
  fi
  checker_report_sha_rc=0
  CHECKER_REPORT_SHA=$(sha256sum "$ATTEMPT_DIR/trace0-preprocess-identity.json" | awk '{print $1}') || checker_report_sha_rc=$?
  if [[ "$checker_report_sha_rc" -ne 0 ]]; then
    write_failure 2 trace0_preprocess_identity_report_binding \
      "failed to hash TRACE=0 preprocess identity report after checker success"
    exit 2
  fi
  if [[ ! "$CHECKER_REPORT_SHA" =~ ^[0-9a-f]{64}$ ]]; then
    write_failure 2 trace0_preprocess_identity_report_binding \
      "TRACE=0 preprocess identity report hash is not 64 lowercase hex"
    exit 2
  fi
  if [[ "${T1943_G2:-0}" -eq 1 ]]; then
    python3 - "$BINARY" "$ATTEMPT_DIR/trace0-watermark-absence.json" <<'PY_T1943_TRACE0'
import json
import os
import pathlib
import stat
import subprocess
import sys

binary = pathlib.Path(sys.argv[1])
marker = b"IZANAGI_MOCC_G2_WATERMARK_V1"
forbidden_tokens = {
    "enable_env": b"IZANAGI_MOCC_G2_WITNESS",
    "directory_env": b"IZANAGI_MOCC_G2_WITNESS_DIR",
    "marker": marker,
    "symbol": b"izanagi_mocc_g2",
    "witness_file_prefix": b"witness_",
}
binary_fd = os.open(binary, os.O_RDONLY | os.O_NOFOLLOW)
try:
    binary_info = os.fstat(binary_fd)
    if not stat.S_ISREG(binary_info.st_mode):
        raise SystemExit("T-1943 TRACE=0 binary is not a regular file")
    with os.fdopen(os.dup(binary_fd), "rb") as handle:
        raw = handle.read()
    os.lseek(binary_fd, 0, os.SEEK_SET)
    nm = subprocess.run(
        ["nm", "-a", f"/proc/self/fd/{binary_fd}"],
        pass_fds=(binary_fd,),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
finally:
    os.close(binary_fd)
symbol_token = b"izanagi_mocc_g2"
present_tokens = sorted(
    name for name, token in forbidden_tokens.items() if token in raw
)
payload = {
    "schema_version": "mocc-g2-trace0-watermark-absence/v1",
    "binary_sha256": __import__("hashlib").sha256(raw).hexdigest(),
    "marker": marker.decode("ascii"),
    "marker_absent": marker not in raw,
    "symbol_token": symbol_token.decode("ascii"),
    "symbol_absent": nm.returncode == 0 and symbol_token not in nm.stdout,
    "forbidden_binary_tokens": sorted(forbidden_tokens),
    "present_binary_tokens": present_tokens,
    "binary_tokens_absent": not present_tokens,
    "nm_rc": nm.returncode,
}
if (
    not payload["marker_absent"]
    or not payload["symbol_absent"]
    or not payload["binary_tokens_absent"]
):
    raise SystemExit("T-1943 witness surface leaked into TRACE=0")
with open(sys.argv[2], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, sort_keys=True, indent=2)
    handle.write("\n")
PY_T1943_TRACE0
    TRACE0_WATERMARK_ABSENCE_SHA=$(sha256sum \
      "$ATTEMPT_DIR/trace0-watermark-absence.json" | awk '{print $1}')
    build_mode 1
  fi
else
  build_mode 1
fi

check_window before-workload

RUN_DIR="$ATTEMPT_DIR/run"
TRACE_DIR="$RUN_DIR/trace"
mkdir "$RUN_DIR"
mkdir "$TRACE_DIR"
if [[ "$T1943_G2" -eq 1 ]]; then
  WITNESS_DIR="$RUN_DIR/witness"
  mkdir "$WITNESS_DIR"
fi
RUN_STDOUT="$RUN_DIR/workload.stdout"
RUN_STDERR="$RUN_DIR/workload.stderr"
RUN_ARGV_JSON="$RUN_DIR/workload.argv.json"

# These are the exact gflags spellings observed in the existing probe.  The
# policy's semantic keys are intentionally not treated as CLI flag names.
RECORDS=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["records"])
PY
)
THREADS=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["threads"])
PY
)
ZIPF_SKEW=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["zipf_skew"])
PY
)
RRATIO=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["ycsb_rratio"])
PY
)
RMW=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["ycsb_rmw"])
PY
)
EXTIME=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["extime_s"])
PY
)
MAX_OPE=$(python3 - "$WORKLOAD_JSON" <<'PY'
import json
import sys
workload = json.loads(sys.argv[1])
print(workload["ycsb_max_ope"])
PY
)
if [[ "$RMW" == 0 ]]; then
  RMW_FLAG=0
elif [[ "$RMW" == 1 ]]; then
  RMW_FLAG=true
else
  RMW_FLAG="$RMW"
fi
WORKLOAD_ARGV=(
  "-ycsb_tuple_num=$RECORDS"
  "-thread_num=$THREADS"
  "-ycsb_zipf_skew=$ZIPF_SKEW"
  "-ycsb_rratio=$RRATIO"
  "-ycsb_rmw=$RMW_FLAG"
  "-ycsb_max_ope=$MAX_OPE"
  "-extime=$EXTIME"
)
python3 - "$RUN_ARGV_JSON" "$TRACE_MODE" "$WORKLOAD_JSON" "${WORKLOAD_ARGV[@]}" <<'PY'
import json
import sys

with open(sys.argv[1], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "trace_mode": int(sys.argv[2]),
            "workload": json.loads(sys.argv[3]),
            "argv": sys.argv[4:],
            "argv_source": "t139_r4_env_probe.py gflags spelling",
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY

RUN_START_NS=$(python3 - <<'PY'
import time
print(time.monotonic_ns())
PY
)
pushd "$TRACE_DIR" >/dev/null
set +e
if [[ "$T1943_G2" -eq 1 ]]; then
  IZANAGI_MOCC_G2_WITNESS=1 \
  IZANAGI_MOCC_G2_WITNESS_DIR="$WITNESS_DIR" \
    timeout --foreground --signal=TERM --kill-after=30 120 \
      "$BINARY" "${WORKLOAD_ARGV[@]}" >"$RUN_STDOUT" 2>"$RUN_STDERR"
else
  timeout --foreground --signal=TERM --kill-after=30 120 \
    "$BINARY" "${WORKLOAD_ARGV[@]}" >"$RUN_STDOUT" 2>"$RUN_STDERR"
fi
RUN_RC=$?
set -e
popd >/dev/null
RUN_END_NS=$(python3 - <<'PY'
import time
print(time.monotonic_ns())
PY
)
RUN_ELAPSED_NS=$((RUN_END_NS - RUN_START_NS))
printf '%s\n' "$RUN_RC" >"$RUN_DIR/workload.rc"
printf '%s\n' "$RUN_ELAPSED_NS" >"$RUN_DIR/workload.elapsed_ns"
if [[ "$RUN_RC" -ne 0 ]]; then
  write_failure "$RUN_RC" workload "Mocc workload returned nonzero"
  exit "$RUN_RC"
fi

counter_witness_rc=0
python3 - "$RUN_STDOUT" "$ATTEMPT_DIR/commit-count.json" <<'PY' || counter_witness_rc=$?
import json
import re
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read()
patterns = (
    re.compile(r"(?im)^\s*#?\s*commit_counts?[_ ]*[:=]\s*(\d+)\s*$"),
    re.compile(r"(?im)^\s*#?\s*committed[_ ]+(?:transactions?|txns?|count)[_ ]*[:=]\s*(\d+)\s*$"),
)
matches = []
for pattern in patterns:
    matches.extend(pattern.finditer(text))
if len(matches) != 1:
    raise SystemExit(
        "expected exactly one commit counter witness line; "
        f"observed {len(matches)}"
    )
match = matches[0]
count = int(match.group(1))
if count < 0:
    raise SystemExit("commit counter must be non-negative")
with open(sys.argv[2], "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-commit-counter-witness/v1",
            "count": count,
            "matched_line": match.group(0),
            "source": "CCBench stdout commit_counts_ witness",
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
if [[ "$counter_witness_rc" -ne 0 ]]; then
  write_failure "$counter_witness_rc" commit_counter \
    "CCBench stdout commit_counts_ witness was absent or ambiguous"
  exit "$counter_witness_rc"
fi
COMMIT_COUNT=$(python3 - "$ATTEMPT_DIR/commit-count.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    value = json.load(handle)["count"]
if type(value) is not int or value < 0:
    raise SystemExit("invalid commit count witness")
print(value)
PY
)

if [[ "$TRACE_MODE" -eq 1 ]]; then
  python3 - "$TRACE_DIR" "$ATTEMPT_DIR/trace-manifest.json" "$T1943_G2" \
    "$NEW_OID" "$BINARY_SHA" "$WORKLOAD_JSON" <<'PY'
import hashlib
import json
import os
import pathlib
import stat
import sys

trace_dir = pathlib.Path(sys.argv[1])
output = sys.argv[2]
t1943_g2 = int(sys.argv[3])
paths = sorted(trace_dir.glob("trace_*.log"))
records = []
for path in paths:
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(f"trace artifact is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
    finally:
        if fd >= 0:
            os.close(fd)
    records.append(
        {
            "name": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }
    )
if not records:
    raise SystemExit("standard trace manifest would be empty")
if t1943_g2:
    payload = {
        "schema_version": "mocc-g2-standard-trace-manifest/v1",
        "artifact_kind": "standard-trace",
        "root_dir": str(trace_dir),
        "source_oid": sys.argv[4],
        "binary_sha256": sys.argv[5],
        "workload": json.loads(sys.argv[6]),
        "files": records,
    }
else:
    payload = {
            "schema_version": "mocc-trace-artifact-manifest/v1",
            "trace_dir": str(trace_dir),
            "files": records,
    }
with open(output, "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY
  TRACE_MANIFEST_SHA=$(sha256sum "$ATTEMPT_DIR/trace-manifest.json" | awk '{print $1}')
  if [[ "$T1943_G2" -eq 1 ]]; then
    python3 - "$WITNESS_DIR" "$ATTEMPT_DIR/witness-manifest.json" \
      "$NEW_OID" "$BINARY_SHA" "$WORKLOAD_JSON" <<'PY_T1943_WITNESS_MANIFEST'
import hashlib
import json
import os
import pathlib
import stat
import sys

root = pathlib.Path(sys.argv[1])
records = []
for path in sorted(root.glob("witness_*.log")):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode):
            raise SystemExit(f"witness artifact is not a regular file: {path}")
        with os.fdopen(fd, "rb") as handle:
            fd = -1
            raw = handle.read()
    finally:
        if fd >= 0:
            os.close(fd)
    records.append(
        {
            "name": path.name,
            "sha256": hashlib.sha256(raw).hexdigest(),
            "size_bytes": len(raw),
        }
    )
if not records:
    raise SystemExit("payload witness manifest would be empty")
payload = {
    "schema_version": "mocc-g2-payload-witness-manifest/v1",
    "artifact_kind": "payload-witness",
    "root_dir": str(root),
    "source_oid": sys.argv[3],
    "binary_sha256": sys.argv[4],
    "workload": json.loads(sys.argv[5]),
    "files": records,
}
with open(sys.argv[2], "x", encoding="utf-8") as handle:
    json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
    handle.write("\n")
PY_T1943_WITNESS_MANIFEST
    WITNESS_MANIFEST_SHA=$(sha256sum \
      "$ATTEMPT_DIR/witness-manifest.json" | awk '{print $1}')
  fi
  VERIFIER_TOOL_PATH=$(realpath -e -- "$REPO_ROOT/orchestrator/verifier/__main__.py")
  if [[ ! -f "$VERIFIER_TOOL_PATH" || -L "$VERIFIER_TOOL_PATH" ]]; then
    write_failure 2 verifier "verifier implementation is not a real file"
    exit 2
  fi
  VERIFIER_TOOL_SHA=$(sha256sum "$VERIFIER_TOOL_PATH" | awk '{print $1}')
  VERIFIER_PY=""
  verifier_py_rejected=""
  for py_name in python3 python3.10 python3.11 python3.12; do
    py_cmd=$(command -v -- "$py_name") || continue
    py_resolved=$(realpath -e -- "$py_cmd") || continue
    [[ -x "$py_resolved" ]] || continue
    if (
      cd "$REPO_ROOT" &&
      "$py_resolved" -c \
        'import sys; import orchestrator.verifier; raise SystemExit(0 if sys.version_info >= (3, 10) else 1)' \
        "$REPO_ROOT"
    ) >/dev/null 2>&1; then
      VERIFIER_PY="$py_resolved"
      break
    fi
    verifier_py_rejected+="${verifier_py_rejected:+ }$py_name=$py_resolved"
  done
  if [[ -z "$VERIFIER_PY" ]]; then
    verifier_gate_message="no python3 >= 3.10 candidate can import orchestrator.verifier (rejected: ${verifier_py_rejected:-none})"
    write_failure 2 verifier "$verifier_gate_message"
    printf '%s\n' 2 >"$ATTEMPT_DIR/verifier.rc"
    echo "$verifier_gate_message" >&2
    exit 2
  fi

  VERIFIER_SOURCE_ROOT="$CCBENCH_BASE"
  if [[ "$T1943_G2" -eq 1 ]]; then
    VERIFIER_SOURCE_ROOT="$BUILD_SOURCE"
  fi
  verifier_rc=0
  (
    cd "$REPO_ROOT" &&
    "$VERIFIER_PY" -m orchestrator.verifier "$TRACE_DIR" --json \
      --expected-commits "$COMMIT_COUNT" --protocol mocc \
      --ccbench-root "$VERIFIER_SOURCE_ROOT"
  ) >"$ATTEMPT_DIR/verifier.json" 2>"$ATTEMPT_DIR/verifier.stderr" || verifier_rc=$?
  VERIFIER_RC=$verifier_rc
  printf '%s\n' "$VERIFIER_RC" >"$ATTEMPT_DIR/verifier.rc"
  if ! verify_post_judgment_source_state; then
    exit 2
  fi
  if [[ "$T1943_G2" -eq 1 ]]; then
    if [[ "$VERIFIER_RC" -ne 0 && "$VERIFIER_RC" -ne 1 ]]; then
      write_failure "$VERIFIER_RC" verifier \
        "T-1943 verifier returned an infrastructure or indeterminate rc"
      exit "$VERIFIER_RC"
    fi
    "$VERIFIER_PY" - "$ATTEMPT_DIR/verifier.json" "$VERIFIER_RC" <<'PY_T1943_VERIFIER_COMPLETE'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
if set(payload) != {
    "runs", "certified_serializable", "non_serializable",
    "indeterminate", "results",
}:
    raise SystemExit("verifier aggregate shape differs")
if (
    type(payload["runs"]) is not int
    or payload["runs"] != 1
    or not isinstance(payload["results"], list)
):
    raise SystemExit("verifier result count differs")
if len(payload["results"]) != 1:
    raise SystemExit("verifier result count differs")
result = payload["results"][0]
if not isinstance(result, dict) or set(result) != {
    "trace_dir", "verdict", "certified", "serializable", "stats",
    "integrity", "anomaly_count", "total_cycles", "anomalies",
}:
    raise SystemExit("verifier result shape differs")
if (
    not isinstance(result["anomalies"], list)
    or type(result["anomaly_count"]) is not int
    or result["anomaly_count"] != len(result["anomalies"])
    or type(result["total_cycles"]) is not int
    or result["total_cycles"] < 0
):
    raise SystemExit("verifier anomaly framing differs")
rc = int(sys.argv[2])
if rc == 1:
    if (
        payload["non_serializable"] != 1
        or result.get("verdict") != "non-serializable"
        or not result.get("anomalies")
    ):
        raise SystemExit("rc=1 is not a completed anomaly result")
elif (
    payload["certified_serializable"] != 1
    or result.get("verdict") != "serializable"
    or result.get("anomalies") != []
):
    raise SystemExit("rc=0 is not a completed certified result")
PY_T1943_VERIFIER_COMPLETE
    DISCRIMINATOR_TOOL_PATH=$(realpath -e -- \
      "$REPO_ROOT/orchestrator/campaign/mocc_g2_discriminator.py")
    if [[ ! -f "$DISCRIMINATOR_TOOL_PATH" || -L "$DISCRIMINATOR_TOOL_PATH" ]]; then
      write_failure 2 discriminator "payload discriminator is not a real file"
      exit 2
    fi
    DISCRIMINATOR_TOOL_SHA=$(sha256sum "$DISCRIMINATOR_TOOL_PATH" | awk '{print $1}')
    discriminator_rc=0
    discriminator_stdout=$(cd "$REPO_ROOT" && "$VERIFIER_PY" -m \
      orchestrator.campaign.mocc_g2_discriminator \
      --trace-manifest "$ATTEMPT_DIR/trace-manifest.json" \
      --witness-manifest "$ATTEMPT_DIR/witness-manifest.json" \
      --verifier "$ATTEMPT_DIR/verifier.json" \
      --output "$ATTEMPT_DIR/discriminator.json" \
      2>"$ATTEMPT_DIR/discriminator.stderr") || discriminator_rc=$?
    DISCRIMINATOR_RC=$discriminator_rc
    printf '%s\n' "$DISCRIMINATOR_RC" >"$ATTEMPT_DIR/discriminator.rc"
    if [[ "$DISCRIMINATOR_RC" -ne 0 ]]; then
      write_failure "$DISCRIMINATOR_RC" discriminator \
        "payload discriminator rejected its bound inputs"
      exit "$DISCRIMINATOR_RC"
    fi
    DISCRIMINATOR_RESULT=$("$VERIFIER_PY" - \
      "$ATTEMPT_DIR/discriminator.json" "$discriminator_stdout" <<'PY_T1943_RESULT'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    payload = json.load(handle)
conclusion = payload.get("conclusion")
if payload.get("schema_version") != "mocc-g2-payload-discriminator/v1":
    raise SystemExit("discriminator schema differs")
if conclusion not in {"supported", "contradicted", "indeterminate", "no-g2"}:
    raise SystemExit("discriminator conclusion differs")
if sys.argv[2].strip() != conclusion:
    raise SystemExit("discriminator stdout differs from result")
print(conclusion)
PY_T1943_RESULT
    )
    DISCRIMINATOR_RESULT_SHA=$(sha256sum \
      "$ATTEMPT_DIR/discriminator.json" | awk '{print $1}')
  elif [[ "$VERIFIER_RC" -ne 0 ]]; then
    write_failure "$VERIFIER_RC" verifier \
      "TRACE=1 verifier did not certify the captured trace"
    exit "$VERIFIER_RC"
  fi
else
  python3 - "$ATTEMPT_DIR/throughput.json" "$COMMIT_COUNT" "$RUN_ELAPSED_NS" <<'PY'
import json
import sys

path, count, elapsed_ns = sys.argv[1:]
count_i = int(count)
elapsed_i = int(elapsed_ns)
if elapsed_i <= 0:
    raise SystemExit("workload elapsed time must be positive")
elapsed_s = elapsed_i / 1_000_000_000
throughput = count_i / elapsed_s
average_latency_s = elapsed_s / count_i if count_i else None
average_latency_us = average_latency_s * 1_000_000 if average_latency_s is not None else None
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-throughput/v1",
            "measurement_role": "pilot-only; not official calibration",
            "completed_txns": count_i,
            "elapsed_ns": elapsed_i,
            "elapsed_s": elapsed_s,
            "throughput_txns_per_s": throughput,
            "average_latency_s": average_latency_s,
            "average_latency_us": average_latency_us,
        },
        handle,
        ensure_ascii=False,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
fi

# Recollect scheduler/accounting material after the run.  It is evidence, not a
# success shortcut: missing or malformed scheduler data remains visible in rc files.
qstat_final_rc=0
timeout 30 qstat -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-final.stdout" \
  2>"$ATTEMPT_DIR/qstat-final.stderr" || qstat_final_rc=$?
printf '%s\n' "$qstat_final_rc" >"$ATTEMPT_DIR/qstat-final.rc"
qstat_accounting_rc=0
timeout 30 qstat -x -f "$QSTAT_JOBID" >"$ATTEMPT_DIR/qstat-accounting.stdout" \
  2>"$ATTEMPT_DIR/qstat-accounting.stderr" || qstat_accounting_rc=$?
printf '%s\n' "$qstat_accounting_rc" >"$ATTEMPT_DIR/qstat-accounting.rc"

if [[ "$T1943_G2" -eq 1 ]]; then
  if ! validate_artifact_classification_manifest; then
    write_failure 2 artifact_classification_manifest \
      "artifact classification manifest does not cover T-1943 job outputs"
    exit 2
  fi
fi

# BEGIN T2195 POLICY FINALIZATION CHECK
if ! policy_finalization_output=$(python3 - "$ATTEMPT_RECEIPT" \
    "$SUBMIT_RECEIPT_SHA" "$POLICY_RAW_SHA256" \
    "$EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON" \
    2>&1 <<'PY_T2195_POLICY_FINALIZATION'
import hashlib
import json
import os
import stat
import sys

receipt_path, pinned_sha, policy_raw_sha, shell_mapping_json = sys.argv[1:]


def reject_duplicate_keys(pairs):
    document = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key: {key}")
        document[key] = value
    return document


def _reject_non_finite(value):
    raise ValueError(f"non-finite JSON constant: {value}")


def require_sha(value, label):
    if (
        type(value) is not str
        or len(value) != 64
        or any(char not in "0123456789abcdef" for char in value)
    ):
        raise ValueError(f"{label} is not 64 lowercase hex")
    return value


def require_mapping(value, label):
    if type(value) is not dict or set(value) != {"gcc", "g++"}:
        raise ValueError(f"{label} keys differ")
    for role, digest in value.items():
        require_sha(digest, f"{label}.{role}")
    return value


try:
    receipt_fd = os.open(
        receipt_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK
    )
    try:
        receipt_info = os.fstat(receipt_fd)
        if not stat.S_ISREG(receipt_info.st_mode):
            raise ValueError("pinned submit receipt is not a regular file")
        with os.fdopen(receipt_fd, "rb") as handle:
            receipt_fd = -1
            receipt_bytes = handle.read()
    finally:
        if receipt_fd >= 0:
            os.close(receipt_fd)
    if hashlib.sha256(receipt_bytes).hexdigest() != pinned_sha:
        raise ValueError("pinned submit receipt digest differs at finalization")
    receipt = json.loads(
        receipt_bytes.decode("utf-8"),
        object_pairs_hook=reject_duplicate_keys,
        parse_constant=_reject_non_finite,
    )
    if not isinstance(receipt, dict):
        raise ValueError("pinned submit receipt top level is not an object")
    receipt_policy = receipt.get("policy")
    if not isinstance(receipt_policy, dict):
        raise ValueError("submit receipt policy is not an object")
    require_sha(policy_raw_sha, "bound policy raw sha")
    if require_sha(
        receipt_policy.get("raw_sha256"), "submit receipt policy raw sha"
    ) != policy_raw_sha:
        raise ValueError("bound policy raw sha differs at finalization")
    shell_mapping = require_mapping(
        json.loads(
            shell_mapping_json,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=_reject_non_finite,
        ),
        "bound policy compiler mapping",
    )
    if require_mapping(
        receipt_policy.get("expected_compiler_version_body_sha256"),
        "submit receipt compiler mapping",
    ) != shell_mapping:
        raise ValueError("bound policy compiler mapping differs at finalization")
except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
    raise SystemExit(str(exc)) from exc
PY_T2195_POLICY_FINALIZATION
); then
  write_failure 2 policy_binding "$policy_finalization_output"
  exit 2
fi
# END T2195 POLICY FINALIZATION CHECK

RECEIPT_WRITER_SHA=$(python3 - "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" "$ATTEMPT_RECEIPT" \
  "$ATTEMPT_DIR/topology.json" "$SUBMIT_RECEIPT_SHA" \
  "$POLICY_RAW_SHA256" "$EXPECTED_COMPILER_VERSION_BODY_SHA256_JSON" \
  "$CURRENT_COMMIT" "$CURRENT_SCRIPT_SHA" \
  "$PBS_JOBID" "$HOSTNAME_SHORT" "$HOSTNAME_FQDN" "$CPU_MODEL" "$TRACE_MODE" \
  "$CXX_PATH" \
  "$BASE_OID" "$NEW_OID" "$BUILD_DIR" "$BINARY" "$BINARY_SHA" "$RUN_DIR" \
  "$TRACE_DIR" "$RUN_ARGV_JSON" "$COMMIT_COUNT" "$RUN_ELAPSED_NS" \
  "$CHECKER_RC" "$VERIFIER_RC" "$RUN_RC" "$qstat_final_rc" \
  "$qstat_accounting_rc" "$WORKLOAD_JSON" "$CMAKE_TARGET" \
  "$ATTEMPT_DIR/trace0-preprocess-identity.json" "$BUILD_SOURCE" \
  "$CHECKER_PY" "$VERIFIER_PY" "$CHECKER_REPORT_SHA" \
  "$CHECKER_TOOL_PATH" "$CHECKER_TOOL_SHA" \
  "$VERIFIER_TOOL_PATH" "$VERIFIER_TOOL_SHA" \
  "$JUDGMENT_PRE_CAPTURE" "$JUDGMENT_PRE_SHA" \
  "$JUDGMENT_POST_CAPTURE" "$JUDGMENT_POST_SHA" \
  "${T1943_G2:-0}" "${TRACE_MANIFEST_SHA:-}" \
  "$ATTEMPT_DIR/witness-manifest.json" "${WITNESS_MANIFEST_SHA:-}" \
  "${DISCRIMINATOR_TOOL_PATH:-}" "${DISCRIMINATOR_TOOL_SHA:-}" \
  "$ATTEMPT_DIR/discriminator.json" "${DISCRIMINATOR_RESULT_SHA:-}" \
  "${DISCRIMINATOR_RESULT:-not-run}" "${DISCRIMINATOR_RC:-not-run}" \
  "$ATTEMPT_DIR/trace0-watermark-absence.json" \
  "${TRACE0_WATERMARK_ABSENCE_SHA:-}" \
  "${PATCH_PATH:-}" "${PATCH_SHA:-}" "${PATCHED_SOURCE_SHA:-}" <<'PY'
import base64
import binascii
import hashlib
import json
import os
import re
import stat
import sys
import time

(
    output, submit_receipt_path, topology_path, pinned_submit_receipt_sha,
    policy_raw_sha, expected_compiler_mapping_json,
    outer_commit, script_sha,
    job_id, host, host_fqdn, cpu_model, trace_mode, cxx_path, base_oid, new_oid,
    build_dir, binary, binary_sha, run_dir, trace_dir, run_argv_path,
    commit_count, elapsed_ns, checker_rc, verifier_rc, run_rc,
    qstat_final_rc, qstat_accounting_rc, workload_json, cmake_target,
    checker_report_path, build_source, checker_py, verifier_py,
    checker_report_sha, checker_tool_path, checker_tool_sha,
    verifier_tool_path, verifier_tool_sha,
    judgment_pre_path, judgment_pre_sha,
    judgment_post_path, judgment_post_sha,
    t1943_g2, trace_manifest_sha,
    witness_manifest_path, witness_manifest_sha,
    discriminator_tool_path, discriminator_tool_sha,
    discriminator_result_path, discriminator_result_sha,
    discriminator_result, discriminator_rc,
    trace0_watermark_absence_path, trace0_watermark_absence_sha,
    patch_path, patch_sha, patched_source_sha,
) = sys.argv[1:]


def reject(message):
    raise ValueError(message)


def is_resolved_absolute_file(path):
    return (
        isinstance(path, str)
        and bool(path)
        and os.path.isabs(path)
        and os.path.realpath(path) == path
        and os.path.isfile(path)
    )


trace_mode_i = int(trace_mode)
t1943_g2_i = int(t1943_g2)
if t1943_g2_i not in {0, 1}:
    reject("T-1943 discriminator mode differs")
attempt_dir = os.path.dirname(os.path.abspath(output))
expected_report_path = os.path.join(attempt_dir, "trace0-preprocess-identity.json")
if os.path.abspath(checker_report_path) != expected_report_path:
    reject("checker report path is outside the attempt directory")


def strict_path_identity(path, expected_type, label):
    if not isinstance(path, str) or not path:
        reject(f"{label} is not a nonempty path")
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    try:
        identity_stat = os.fstat(fd)
    finally:
        os.close(fd)
    if expected_type == "directory":
        if not stat.S_ISDIR(identity_stat.st_mode):
            reject(f"{label} is not a directory")
    elif expected_type == "regular file":
        if not stat.S_ISREG(identity_stat.st_mode):
            reject(f"{label} is not a regular file")
    else:
        reject("unsupported strict path identity type")
    return identity_stat.st_dev, identity_stat.st_ino


def read_regular_bytes(path, label):
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError(f"{label} is unavailable") from exc
    try:
        identity_stat = os.fstat(fd)
        if not stat.S_ISREG(identity_stat.st_mode):
            reject(f"{label} is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = None
            return handle.read()
    finally:
        if fd is not None:
            os.close(fd)


def bound_judgment_capture(path, expected_sha, expected_phase):
    expected_path = os.path.join(
        attempt_dir,
        f"judgment-source-{'pre' if expected_phase == 'pre_judgment' else 'post'}.json",
    )
    if os.path.abspath(path) != expected_path:
        reject(f"{expected_phase} capture path is outside the attempt directory")
    capture_bytes = read_regular_bytes(path, f"{expected_phase} source capture")
    capture_sha = hashlib.sha256(capture_bytes).hexdigest()
    if capture_sha != expected_sha:
        reject(f"{expected_phase} source capture changed after capture")
    try:
        capture = json.loads(capture_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{expected_phase} source capture is not strict JSON") from exc
    if not isinstance(capture, dict) or set(capture) != {
        "schema_version",
        "capture_phase",
        "capture_ok",
        "head",
        "clean",
        "pathspec",
        "status_format",
        "status_bytes_base64",
        "command_rc",
    }:
        reject(f"{expected_phase} source capture shape differs")
    if capture["schema_version"] != "mocc-trace-judgment-source-capture/v1":
        reject(f"{expected_phase} source capture schema differs")
    if capture["capture_phase"] != expected_phase:
        reject(f"{expected_phase} source capture phase differs")
    if capture["capture_ok"] is not True:
        reject(f"{expected_phase} source capture did not complete")
    if not isinstance(capture["head"], str) or not re.fullmatch(
        r"[0-9a-f]{40}", capture["head"]
    ):
        reject(f"{expected_phase} source capture HEAD is invalid")
    if type(capture["clean"]) is not bool:
        reject(f"{expected_phase} source capture clean is not boolean")
    if capture["pathspec"] != [".", ":(exclude)output"]:
        reject(f"{expected_phase} source capture pathspec differs")
    if (
        capture["status_format"]
        != "git status --porcelain=v1 -z --untracked-files=all"
    ):
        reject(f"{expected_phase} source capture status format differs")
    encoded_status = capture["status_bytes_base64"]
    if not isinstance(encoded_status, str):
        reject(f"{expected_phase} source status bytes are not encoded text")
    try:
        status_bytes = base64.b64decode(encoded_status, validate=True)
    except (ValueError, binascii.Error) as exc:
        raise ValueError(
            f"{expected_phase} source status bytes are not valid base64"
        ) from exc
    if capture["clean"] != (status_bytes == b"") or not capture["clean"]:
        reject(f"{expected_phase} source capture is dirty")
    if capture["command_rc"] != {"head": 0, "status": 0}:
        reject(f"{expected_phase} source capture command rc differs")
    return {
        "capture_path": os.path.basename(path),
        "capture_sha256": capture_sha,
        "head": capture["head"],
        "clean": capture["clean"],
    }


def bound_tool(path, expected_sha, label):
    if not is_resolved_absolute_file(path):
        reject(f"{label} path is not a resolved absolute file")
    actual_sha = hashlib.sha256(read_regular_bytes(path, label)).hexdigest()
    if actual_sha != expected_sha:
        reject(f"{label} changed after execution")
    return {"path": path, "sha256": actual_sha}


def revalidate_leaf_manifest(
    manifest_path,
    expected_sha,
    expected_root,
    expected_schema,
    expected_kind,
    name_pattern,
):
    manifest_bytes = read_regular_bytes(
        manifest_path, f"T-1943 {expected_kind} manifest"
    )
    if hashlib.sha256(manifest_bytes).hexdigest() != expected_sha:
        reject(f"T-1943 {expected_kind} manifest changed after capture")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            f"T-1943 {expected_kind} manifest is not strict JSON"
        ) from exc
    if not isinstance(manifest, dict) or set(manifest) != {
        "artifact_kind",
        "binary_sha256",
        "files",
        "root_dir",
        "schema_version",
        "source_oid",
        "workload",
    }:
        reject(f"T-1943 {expected_kind} manifest shape differs")
    if (
        manifest["schema_version"] != expected_schema
        or manifest["artifact_kind"] != expected_kind
        or manifest["root_dir"] != expected_root
        or manifest["source_oid"] != new_oid
        or manifest["binary_sha256"] != binary_sha
        or manifest["workload"] != json.loads(workload_json)
    ):
        reject(f"T-1943 {expected_kind} manifest bindings differ")
    try:
        root_fd = os.open(
            expected_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        )
    except OSError as exc:
        raise ValueError(f"T-1943 {expected_kind} root is unavailable") from exc
    try:
        if not stat.S_ISDIR(os.fstat(root_fd).st_mode):
            reject(f"T-1943 {expected_kind} root is not a real directory")
        files = manifest["files"]
        if not isinstance(files, list) or not files:
            reject(f"T-1943 {expected_kind} manifest has no leaves")
        bound_names = set()
        for entry in files:
            if not isinstance(entry, dict) or set(entry) != {
                "name",
                "sha256",
                "size_bytes",
            }:
                reject(f"T-1943 {expected_kind} leaf binding shape differs")
            name = entry["name"]
            digest = entry["sha256"]
            size = entry["size_bytes"]
            if (
                not isinstance(name, str)
                or re.fullmatch(name_pattern, name) is None
                or name in bound_names
                or not isinstance(digest, str)
                or re.fullmatch(r"[0-9a-f]{64}", digest) is None
                or type(size) is not int
                or size < 0
            ):
                reject(f"T-1943 {expected_kind} leaf binding differs")
            thread = int(name.removeprefix(
                "trace_" if expected_kind == "standard-trace" else "witness_"
            ).removesuffix(".log"))
            if thread >= json.loads(workload_json)["threads"]:
                reject(f"T-1943 {expected_kind} leaf thread is outside workload")
            try:
                leaf_fd = os.open(
                    name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=root_fd
                )
            except OSError as exc:
                raise ValueError(
                    f"T-1943 {expected_kind} leaf {name} is unavailable"
                ) from exc
            try:
                if not stat.S_ISREG(os.fstat(leaf_fd).st_mode):
                    reject(f"T-1943 {expected_kind} leaf is not a regular file")
                with os.fdopen(leaf_fd, "rb") as handle:
                    leaf_fd = -1
                    leaf_bytes = handle.read()
            finally:
                if leaf_fd >= 0:
                    os.close(leaf_fd)
            if (
                len(leaf_bytes) != size
                or hashlib.sha256(leaf_bytes).hexdigest() != digest
            ):
                reject(f"T-1943 {expected_kind} leaf changed after discriminator")
            bound_names.add(name)
        actual_names = set()
        for actual_name in os.listdir(root_fd):
            try:
                actual_info = os.stat(
                    actual_name, dir_fd=root_fd, follow_symlinks=False
                )
            except OSError as exc:
                raise ValueError(
                    f"T-1943 {expected_kind} root entry is unavailable"
                ) from exc
            if not stat.S_ISREG(actual_info.st_mode):
                reject(f"T-1943 {expected_kind} root contains a non-regular entry")
            if re.fullmatch(name_pattern, actual_name) is None:
                reject(f"T-1943 {expected_kind} root contains an unexpected file")
            actual_names.add(actual_name)
    finally:
        os.close(root_fd)
    if actual_names != bound_names:
        reject(f"T-1943 {expected_kind} leaf file set changed after discriminator")
    return manifest_bytes


judgment_pre = bound_judgment_capture(
    judgment_pre_path, judgment_pre_sha, "pre_judgment"
)
judgment_post = bound_judgment_capture(
    judgment_post_path, judgment_post_sha, "post_judgment"
)
if judgment_pre["head"] != outer_commit:
    reject("pre_judgment source capture HEAD differs from outer commit")
if judgment_post["head"] != outer_commit:
    reject("post_judgment source capture HEAD differs from outer commit")

commit_count_path = os.path.join(attempt_dir, "commit-count.json")
commit_count_bytes = read_regular_bytes(
    commit_count_path, "commit count witness"
)
try:
    commit_count_witness = json.loads(commit_count_bytes.decode("utf-8"))
except (UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise ValueError("commit count witness is not strict JSON") from exc
if (
    not isinstance(commit_count_witness, dict)
    or commit_count_witness.get("schema_version")
    != "mocc-commit-counter-witness/v1"
    or type(commit_count_witness.get("count")) is not int
    or commit_count_witness["count"] < 0
    or commit_count_witness["count"] != int(commit_count)
):
    reject("commit count witness does not match the workload result")
commit_count_sha = hashlib.sha256(commit_count_bytes).hexdigest()

if hashlib.sha256(
    read_regular_bytes(binary, "executed workload binary")
).hexdigest() != binary_sha:
    reject("executed workload binary changed after build")

if trace_mode_i == 0 or t1943_g2_i == 1:
    if checker_rc != "0":
        reject("TRACE=0 checker rc is not zero")
    if not is_resolved_absolute_file(checker_py):
        reject("TRACE=0 checker interpreter is not a resolved absolute file")
    if verifier_py and not t1943_g2_i:
        reject("TRACE=0 unexpectedly selected a verifier interpreter")
    try:
        checker_report_path = os.open(
            checker_report_path, os.O_RDONLY | os.O_NOFOLLOW
        )
    except OSError as exc:
        raise ValueError("checker report is unavailable") from exc
    try:
        report_stat = os.fstat(checker_report_path)
        if not stat.S_ISREG(report_stat.st_mode):
            reject("checker report is not a regular file")
        # The pathname variable now holds the pinned fd; open() wraps that same fd.
        with open(checker_report_path, "rb") as handle:
            checker_report_path = None
            report_bytes = handle.read()
    finally:
        if checker_report_path is not None:
            os.close(checker_report_path)
    try:
        report = json.loads(report_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("checker report is not strict UTF-8 JSON") from exc
    if not isinstance(report, dict):
        reject("checker report top level is not an object")
    report_sha = hashlib.sha256(report_bytes).hexdigest()
    if report_sha != checker_report_sha:
        reject("checker report changed after the checker completed")
    schema = report.get("schema")
    if (
        not isinstance(schema, str)
        or not schema.strip()
        or not schema.startswith("izanagi-trace0-preprocess-identity/")
    ):
        reject("checker report schema is outside the accepted family")
    guarantee = report.get("guarantee")
    if not isinstance(guarantee, str) or not guarantee.strip():
        reject("checker report guarantee is not a nonempty string")
    if report.get("result") != "pass":
        reject("checker report result is not pass")
    if report.get("old_oid") != base_oid:
        reject("checker report old oid does not match the invocation")
    if report.get("new_oid") != new_oid:
        reject("checker report new oid does not match the invocation")
    report_repo = report.get("repo")
    if strict_path_identity(
        report_repo, "directory", "checker report repo"
    ) != strict_path_identity(
        os.path.realpath(build_source), "directory", "invocation repo"
    ):
        reject("checker report repo does not match the invocation")
    compiler = report.get("compiler")
    if not isinstance(compiler, dict):
        reject("checker report compiler is not an object")
    compiler_path = compiler.get("path")
    if strict_path_identity(
        compiler_path, "regular file", "checker report compiler"
    ) != strict_path_identity(
        os.path.realpath(cxx_path), "regular file", "invocation compiler"
    ):
        reject("checker report compiler does not match the invocation")
    if report.get("expected_paths") != ["cc/mocc/transaction.cc"]:
        reject("checker report expected paths do not match the invocation")
    report_binding = {
        "path": "trace0-preprocess-identity.json",
        "sha256": report_sha,
        "schema": schema,
        "guarantee": guarantee,
    }
    checker_interpreter_path = checker_py
    verifier_interpreter_path = verifier_py if t1943_g2_i else None
    correctness_tools = {
        "trace0_preprocess_identity_checker": bound_tool(
            checker_tool_path, checker_tool_sha, "TRACE=0 identity checker"
        ),
        "verifier": (
            bound_tool(verifier_tool_path, verifier_tool_sha, "TRACE=1 verifier")
            if t1943_g2_i
            else None
        ),
    }
    if t1943_g2_i:
        if trace_mode_i != 1:
            reject("T-1943 receipt is not TRACE=1")
        if not is_resolved_absolute_file(verifier_py):
            reject("T-1943 verifier interpreter is not a resolved file")
        verifier_sha = hashlib.sha256(
            read_regular_bytes(
                os.path.join(attempt_dir, "verifier.json"),
                "T-1943 verifier evidence",
            )
        ).hexdigest()
        throughput_sha = None
    else:
        if verifier_py:
            reject("TRACE=0 unexpectedly selected a verifier interpreter")
        throughput_sha = hashlib.sha256(
            read_regular_bytes(
                os.path.join(attempt_dir, "throughput.json"),
                "TRACE=0 throughput evidence",
            )
        ).hexdigest()
        verifier_sha = None
elif trace_mode_i == 1:
    if checker_rc != "not-run":
        reject("TRACE=1 checker rc is not not-run")
    if checker_py:
        reject("TRACE=1 unexpectedly selected a checker interpreter")
    if os.path.lexists(checker_report_path):
        reject("TRACE=1 checker report must be absent")
    if not is_resolved_absolute_file(verifier_py):
        reject("TRACE=1 verifier interpreter is not a resolved absolute file")
    if checker_report_sha:
        reject("TRACE=1 checker report sha must be empty")
    report_binding = {
        "path": None,
        "sha256": None,
        "schema": None,
        "guarantee": None,
    }
    checker_interpreter_path = None
    verifier_interpreter_path = verifier_py
    correctness_tools = {
        "trace0_preprocess_identity_checker": None,
        "verifier": bound_tool(
            verifier_tool_path, verifier_tool_sha, "TRACE=1 verifier"
        ),
    }
    verifier_sha = hashlib.sha256(
        read_regular_bytes(
            os.path.join(attempt_dir, "verifier.json"),
            "TRACE=1 verifier evidence",
        )
    ).hexdigest()
    throughput_sha = None
else:
    reject("trace mode is not zero or one")

t1943_binding = None
if t1943_g2_i:
    if (
        not patch_path
        or re.fullmatch(r"[0-9a-f]{64}", patch_sha) is None
        or re.fullmatch(r"[0-9a-f]{64}", patched_source_sha) is None
    ):
        reject("T-1943 instrumentation patch capture is absent or invalid")
    for path, expected_sha, sidecar, label in (
        (patch_path, patch_sha, "instr-patch.sha256", "instrumentation patch"),
        (os.path.join(build_source, "cc/mocc/transaction.cc"), patched_source_sha,
         "instr-patch-source.sha256", "patched source"),
    ):
        if hashlib.sha256(read_regular_bytes(path, label)).hexdigest() != expected_sha:
            reject("T-1943 " + label + " changed after capture")
        if read_regular_bytes(os.path.join(attempt_dir, sidecar), label + " sidecar") != (
            expected_sha + "\n"
        ).encode("ascii"):
            reject("T-1943 " + label + " sidecar differs")
    numstat = read_regular_bytes(
        os.path.join(attempt_dir, "instr-patch.numstat"), "instrumentation patch numstat"
    ).decode("ascii").splitlines()
    if len(numstat) != 1 or re.fullmatch(
        r"[0-9]+\t[0-9]+\tcc/mocc/transaction[.]cc", numstat[0]
    ) is None:
        reject("T-1943 instrumentation patch touch set differs")
    if verifier_rc not in {"0", "1"} or discriminator_rc != "0":
        reject("T-1943 verifier/discriminator rc differs")
    trace_manifest_path = os.path.join(attempt_dir, "trace-manifest.json")
    if os.path.abspath(witness_manifest_path) != os.path.join(
        attempt_dir, "witness-manifest.json"
    ):
        reject("T-1943 witness manifest path differs")
    revalidate_leaf_manifest(
        trace_manifest_path,
        trace_manifest_sha,
        trace_dir,
        "mocc-g2-standard-trace-manifest/v1",
        "standard-trace",
        r"trace_(?:0|[1-9][0-9]*)[.]log",
    )
    revalidate_leaf_manifest(
        witness_manifest_path,
        witness_manifest_sha,
        os.path.join(run_dir, "witness"),
        "mocc-g2-payload-witness-manifest/v1",
        "payload-witness",
        r"witness_(?:0|[1-9][0-9]*)[.]log",
    )
    if os.path.abspath(discriminator_result_path) != os.path.join(
        attempt_dir, "discriminator.json"
    ):
        reject("T-1943 discriminator result path differs")
    result_bytes = read_regular_bytes(
        discriminator_result_path, "T-1943 discriminator result"
    )
    if hashlib.sha256(result_bytes).hexdigest() != discriminator_result_sha:
        reject("T-1943 discriminator result changed after execution")
    try:
        discriminator_payload = json.loads(result_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("T-1943 discriminator result is not strict JSON") from exc
    if (
        discriminator_payload.get("schema_version")
        != "mocc-g2-payload-discriminator/v1"
        or discriminator_payload.get("conclusion") != discriminator_result
        or discriminator_result
        not in {"supported", "contradicted", "indeterminate", "no-g2"}
    ):
        reject("T-1943 discriminator result fields differ")
    bindings = discriminator_payload.get("bindings")
    if not isinstance(bindings, dict) or bindings != {
        "source_oid": new_oid,
        "binary_sha256": binary_sha,
        "workload": json.loads(workload_json),
        "trace_manifest_sha256": trace_manifest_sha,
        "witness_manifest_sha256": witness_manifest_sha,
        "verifier_sha256": verifier_sha,
    }:
        reject("T-1943 discriminator input bindings differ")
    expected_absence_path = os.path.join(
        attempt_dir, "trace0-watermark-absence.json"
    )
    if os.path.abspath(trace0_watermark_absence_path) != expected_absence_path:
        reject("T-1943 TRACE=0 absence path differs")
    absence_bytes = read_regular_bytes(
        trace0_watermark_absence_path, "T-1943 TRACE=0 absence result"
    )
    if hashlib.sha256(absence_bytes).hexdigest() != trace0_watermark_absence_sha:
        reject("T-1943 TRACE=0 absence result changed after capture")
    absence = json.loads(absence_bytes.decode("utf-8"))
    trace0_binary_path = os.path.join(
        build_source + "-build-trace0", "cc", "mocc", cmake_target
    )
    trace0_binary_sha = hashlib.sha256(
        read_regular_bytes(trace0_binary_path, "T-1943 TRACE=0 binary")
    ).hexdigest()
    try:
        trace0_sidecar_sha = read_regular_bytes(
            os.path.join(attempt_dir, "binary-trace0.sha256"),
            "T-1943 TRACE=0 binary digest sidecar",
        ).decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise ValueError("T-1943 TRACE=0 binary digest is not ASCII") from exc
    if (
        absence.get("schema_version")
        != "mocc-g2-trace0-watermark-absence/v1"
        or absence.get("binary_sha256") != trace0_binary_sha
        or trace0_sidecar_sha != trace0_binary_sha
        or absence.get("marker_absent") is not True
        or absence.get("symbol_absent") is not True
        or absence.get("binary_tokens_absent") is not True
        or absence.get("present_binary_tokens") != []
        or set(absence.get("forbidden_binary_tokens", ())) != {
            "enable_env",
            "directory_env",
            "marker",
            "symbol",
            "witness_file_prefix",
        }
        or absence.get("nm_rc") != 0
    ):
        reject("T-1943 TRACE=0 absence result did not pass")
    correctness_tools["payload_discriminator"] = bound_tool(
        discriminator_tool_path,
        discriminator_tool_sha,
        "T-1943 payload discriminator",
    )
    t1943_binding = {
        "instrumentation_patch": {
            "repo_path": "patches/instr-mocc-lock-coverage.patch",
            "sha256": patch_sha,
            "touched_paths": ["cc/mocc/transaction.cc"],
            "patched_source_sha256": patched_source_sha,
            "trace0_built_from_patched_source": True,
        },
        "trace_manifest": {
            "path": "trace-manifest.json",
            "sha256": trace_manifest_sha,
        },
        "witness_manifest": {
            "path": "witness-manifest.json",
            "sha256": witness_manifest_sha,
        },
        "trace0_watermark_absence": {
            "path": "trace0-watermark-absence.json",
            "sha256": trace0_watermark_absence_sha,
            "binary_sha256": trace0_binary_sha,
        },
        "discriminator_result": {
            "path": "discriminator.json",
            "sha256": discriminator_result_sha,
            "conclusion": discriminator_result,
        },
    }

elif patch_path or patch_sha or patched_source_sha:
    reject("T-1943 instrumentation patch capture leaked into general mode")

submit_receipt_bytes = read_regular_bytes(
    submit_receipt_path, "submit receipt parent"
)
try:
    submit_receipt = json.loads(submit_receipt_bytes.decode("utf-8"))
except (UnicodeDecodeError, json.JSONDecodeError) as exc:
    raise ValueError("submit receipt parent is not strict JSON") from exc
submit_receipt_sha = hashlib.sha256(submit_receipt_bytes).hexdigest()
if submit_receipt_sha != pinned_submit_receipt_sha:
    reject("submit receipt parent changed after initial digest pin")
submit_mocc_trace = submit_receipt.get("mocc_trace")
if (
    submit_receipt.get("schema_version") != "pegasus-submit-receipt/v2"
    or submit_receipt.get("source_commit") != outer_commit
    or not isinstance(submit_mocc_trace, dict)
    or submit_mocc_trace.get("base_oid") != base_oid
    or submit_mocc_trace.get("new_oid") != new_oid
    or submit_mocc_trace.get("trace_mode") != trace_mode_i
    or submit_mocc_trace.get("workload") != json.loads(workload_json)
    or (
        submit_mocc_trace.get("t1943_g2_discriminator") is not True
        if t1943_g2_i
        else "t1943_g2_discriminator" in submit_mocc_trace
    )
):
    reject("submit receipt parent bindings differ at finalization")
with open(topology_path, encoding="utf-8") as handle:
    topology = json.load(handle)
with open(run_argv_path, encoding="utf-8") as handle:
    run_argv = json.load(handle)
mocc_trace = dict(submit_receipt["mocc_trace"])
mocc_trace["trace_mode"] = int(trace_mode)
mocc_trace["base_oid"] = base_oid
mocc_trace["new_oid"] = new_oid
mocc_trace["cmake_target"] = cmake_target
mocc_trace["workload"] = json.loads(workload_json)
if t1943_g2_i:
    mocc_trace["t1943_g2_discriminator"] = True
mocc_trace["workload_note"] = (
    "parent-selected pilot workload; not a reproduction of historical T-816 measurements"
)
workload_receipt = {
    "config": json.loads(workload_json),
    "argv": run_argv["argv"],
    "argv_source": run_argv["argv_source"],
}
if trace_mode_i == 0:
    workload_receipt.update(
        {
            "completed_txns": int(commit_count),
            "elapsed_ns": int(elapsed_ns),
            "elapsed_s": int(elapsed_ns) / 1_000_000_000,
        }
    )
payload = {
    "schema_version": (
        "mocc-trace-pilot-receipt/t1943-g2-v2"
        if t1943_g2_i
        else "mocc-trace-pilot-receipt/v4"
    ),
    "status": "completed",
    "pilot": True,
    "eligible_for_refreeze": False,
    "official_certification": False,
    "created_epoch": int(time.time()),
    "pbs": {
        "jobid": job_id,
        "queue": os.environ.get("PBS_QUEUE", "gen_S"),
        "account": os.environ.get("PBS_ACCOUNT", "SFC"),
        "requested_s": int(os.environ.get("IZANAGI_RESERVATION_REQUESTED_S", "0")),
        "hostname": host,
        "hostname_fqdn": host_fqdn,
        "qstat_final_rc": int(qstat_final_rc),
        "qstat_accounting_rc": int(qstat_accounting_rc),
        "scheduler_material": {
            "qstat_final": "qstat-final.stdout/stderr/rc",
            "qstat_accounting": "qstat-accounting.stdout/stderr/rc",
        },
    },
    "environment": {
        "environment_tag": "pegasus",
        "cpu_model": cpu_model,
        "expected_cpu_model": submit_receipt["policy"]["expected_cpu_model"],
        "topology": topology,
        "compiler": {
            "path": cxx_path,
            "version": open(os.path.join(os.path.dirname(output), "compiler-used.version"), encoding="utf-8").read().strip(),
        },
        "trace0_preprocess_identity_checker_interpreter_path": checker_interpreter_path,
        "verifier_interpreter_path": verifier_interpreter_path,
    },
    "policy": {
        "repo_path": "tools/pegasus/mocc_trace_v1_policy.json",
        "raw_sha256": policy_raw_sha,
        "expected_compiler_version_body_sha256": json.loads(
            expected_compiler_mapping_json
        ),
    },
    "source": {
        "outer_repo_commit": outer_commit,
        "submodule_base_oid": base_oid,
        "submodule_new_oid": new_oid,
        "materialization": "git worktree add --detach in qsub job body",
        "outer_gitlink_advanced": False,
        "judgment_source_state": {
            "guarantee_name": "pre/post endpoint consistency",
            "pre": judgment_pre,
            "post": judgment_post,
            "head_unchanged": judgment_pre["head"] == judgment_post["head"],
            "residual_windows": [
                "temporary source changes between captures can be missed",
                "source changes after the post_judgment capture can be missed",
            ],
        },
    },
    "mocc_trace": mocc_trace,
    "trace0_preprocess_identity_report": report_binding,
    "correctness_tools": correctness_tools,
    "build": {
        "cmake_target": cmake_target,
        "trace_mode": int(trace_mode),
        "build_dir": build_dir,
        "binary": binary,
        "binary_sha256": binary_sha,
        "compiler_path": cxx_path,
    },
    "workload": workload_receipt,
    "artifacts": {
        "attempt_dir": os.path.dirname(output),
        "run_dir": run_dir,
        "trace_dir": trace_dir,
        "submit_receipt": "submit-receipt.json",
        "receipt_sha256_sidecar": "mocc-trace-pilot-receipt.sha256",
        "commit_count_json": "commit-count.json",
        "commit_count_sha256": commit_count_sha,
        "verifier_json": "verifier.json" if int(trace_mode) == 1 else None,
        "verifier_sha256": verifier_sha,
        "throughput_json": "throughput.json" if int(trace_mode) == 0 else None,
        "throughput_sha256": throughput_sha,
    },
    "gates": {
        "trace0_preprocess_identity_rc": checker_rc,
        "verifier_rc": verifier_rc,
        "workload_rc": run_rc,
    },
}
if t1943_g2_i:
    payload["t1943_g2_discriminator"] = t1943_binding
    payload["artifacts"].update(
        {
            "trace_manifest_json": "trace-manifest.json",
            "trace_manifest_sha256": trace_manifest_sha,
            "witness_manifest_json": "witness-manifest.json",
            "witness_manifest_sha256": witness_manifest_sha,
            "instr_patch_sha256": "instr-patch.sha256",
            "instr_patch_numstat": "instr-patch.numstat",
            "instr_patch_source_sha256": "instr-patch-source.sha256",
            "instr_patch_apply_stdout": "instr-patch-apply.stdout",
            "instr_patch_apply_stderr": "instr-patch-apply.stderr",
            "discriminator_json": "discriminator.json",
            "discriminator_sha256": discriminator_result_sha,
            "trace0_binary_sha256": trace0_binary_sha,
            "submit_receipt_sha256": submit_receipt_sha,
        }
    )
    payload["gates"].update(
        {
            "discriminator_rc": discriminator_rc,
            "discriminator_conclusion": discriminator_result,
        }
    )
receipt_bytes = (
    json.dumps(payload, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
).encode("utf-8")
receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
with open(output, "xb") as handle:
    handle.write(receipt_bytes)
receipt_sha_path = os.path.join(attempt_dir, "mocc-trace-pilot-receipt.sha256")
with open(receipt_sha_path, "x", encoding="ascii") as handle:
    handle.write(receipt_sha + "\n")
print(receipt_sha)
PY
) || {
  write_failure 2 trace0_preprocess_identity_report_binding \
    "preprocess identity report binding failed"
  exit 2
}

if [[ ! "$RECEIPT_WRITER_SHA" =~ ^[0-9a-f]{64}$ ]]; then
  write_failure 2 trace0_preprocess_identity_report_binding \
    "receipt writer did not return a 64 lowercase hex sha"
  exit 2
fi

RECEIPT_SHA=$(sha256sum "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" | awk '{print $1}')
if [[ "$RECEIPT_SHA" != "$RECEIPT_WRITER_SHA" ]]; then
  write_failure 2 job_result_report_binding \
    "job result report binding failed"
  exit 2
fi
python3 - "$ATTEMPT_DIR/job-result.json" "$PBS_JOBID" "$RECEIPT_WRITER_SHA" \
  "$BINARY_SHA" "$CURRENT_SCRIPT_SHA" \
  "$ATTEMPT_DIR/mocc-trace-pilot-receipt.json" \
  "$ATTEMPT_DIR/mocc-trace-pilot-receipt.sha256" <<'PY' || {
import hashlib
import json
import os
import re
import stat
import sys
import time

path, job_id, receipt_sha, binary_sha, script_sha, receipt_path, receipt_sha_path = sys.argv[1:]


def read_regular_file_no_follow(candidate):
    try:
        fd = os.open(candidate, os.O_RDONLY | os.O_NOFOLLOW)
    except OSError as exc:
        raise ValueError("receipt binding input is unavailable") from exc
    try:
        candidate_stat = os.fstat(fd)
        if not stat.S_ISREG(candidate_stat.st_mode):
            raise ValueError("receipt binding input is not a regular file")
        with os.fdopen(fd, "rb") as handle:
            fd = None
            return handle.read()
    finally:
        if fd is not None:
            os.close(fd)


receipt_bytes = read_regular_file_no_follow(receipt_path)
actual_receipt_sha = hashlib.sha256(receipt_bytes).hexdigest()
try:
    writer_receipt_sha = read_regular_file_no_follow(receipt_sha_path).decode("ascii").strip()
except UnicodeDecodeError as exc:
    raise ValueError("receipt sha sidecar is not ASCII") from exc
if actual_receipt_sha != receipt_sha or writer_receipt_sha != receipt_sha:
    raise ValueError("receipt sha does not match writer stdout and sidecar")
receipt = json.loads(receipt_bytes.decode("utf-8"))
receipt_schema = receipt.get("schema_version")
if receipt_schema not in {
    "mocc-trace-pilot-receipt/v4",
    "mocc-trace-pilot-receipt/t1943-g2-v2",
}:
    raise ValueError("job result requires an exact admitted pilot receipt schema")
if receipt_schema == "mocc-trace-pilot-receipt/t1943-g2-v2":
    discriminator_binding = receipt.get("t1943_g2_discriminator")
    if not isinstance(discriminator_binding, dict):
        raise ValueError("T-1943 receipt discriminator binding is absent")
    patch_binding = discriminator_binding.get("instrumentation_patch")
    if (
        not isinstance(patch_binding, dict)
        or set(patch_binding) != {
            "repo_path", "sha256", "touched_paths", "patched_source_sha256",
            "trace0_built_from_patched_source",
        }
        or type(patch_binding.get("repo_path")) is not str
        or patch_binding["repo_path"] != "patches/instr-mocc-lock-coverage.patch"
        or any(
            type(patch_binding.get(key)) is not str
            or re.fullmatch(r"[0-9a-f]{64}", patch_binding[key]) is None
            for key in ("sha256", "patched_source_sha256")
        )
        or type(patch_binding.get("touched_paths")) is not list
        or patch_binding["touched_paths"] != ["cc/mocc/transaction.cc"]
        or patch_binding.get("trace0_built_from_patched_source") is not True
    ):
        raise ValueError("T-1943 receipt instrumentation patch binding differs")
    result_binding = discriminator_binding.get("discriminator_result")
    if (
        not isinstance(result_binding, dict)
        or result_binding.get("conclusion")
        not in {"supported", "contradicted", "indeterminate", "no-g2"}
    ):
        raise ValueError("T-1943 receipt conclusion binding differs")
report_binding = receipt.get("trace0_preprocess_identity_report")
if not isinstance(report_binding, dict) or set(report_binding) != {
    "path", "sha256", "schema", "guarantee",
}:
    raise ValueError("receipt report binding must contain exactly four fields")
if any(value is not None and not isinstance(value, str) for value in report_binding.values()):
    raise ValueError("receipt report binding fields must be scalar strings or null")
with open(path, "x", encoding="utf-8") as handle:
    json.dump(
        {
            "schema_version": "mocc-trace-pilot-job-result/v2",
            "pbs_jobid": job_id,
            "receipt_sha256": receipt_sha,
            "binary_sha256": binary_sha,
            "job_script_sha256": script_sha,
            "completed_epoch": int(time.time()),
            "trace0_preprocess_identity_report": dict(report_binding),
        },
        handle,
        sort_keys=True,
        indent=2,
    )
    handle.write("\n")
PY
  write_failure 2 job_result_report_binding \
    "job result report binding failed"
  exit 2
}

git -C "$CCBENCH_BASE" worktree remove --force "$BUILD_SOURCE" \
  >"$ATTEMPT_DIR/worktree-remove.stdout" \
  2>"$ATTEMPT_DIR/worktree-remove.stderr"
BUILD_SOURCE=""
if [[ "$T1943_G2" -ne 1 ]]; then
  if ! validate_artifact_classification_manifest; then
    write_failure 2 artifact_classification_manifest \
      "artifact classification manifest does not cover job outputs"
    exit 2
  fi
fi
exit 0
