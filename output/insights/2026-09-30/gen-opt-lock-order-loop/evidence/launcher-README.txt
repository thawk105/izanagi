md20 U-D: one compute-node fixture-liveness job

Run with Python 3.10 on a compute node. TMPDIR must point to node-local storage.
Use an empty output directory. The launcher keeps checkouts, dependencies, gate
scratch and builds in TMPDIR. Only result.json, run logs, and trace/gate archives
are written to --out-dir. It makes no commit or tracked repository edit.

Example (replace OUT with a new, empty output directory):
  /usr/bin/python3.10 launch_md20_liveness.py \
    --out-dir OUT \
    --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/md20-u3 \
    --bundle /work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1.bundle \
    --u1-oid dcb9a41f3e538744298b0e5c42dc37349bac114e \
    --silo-patch /work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_14-gate-verifier/u1-final/patches/fix-silo-intra-txn-values.patch \
    --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache

Prerequisites: CMake >= 3.21, numactl, nm, the repository's pinned CCBench
commit, the U1 bundle and third-party cache. The launcher compares complete
SHA-1 object IDs, bundle parent and changed paths. git apply --check precedes
each exact git apply; --verbose output records any offset. A trace build must
contain izanagi_trace symbols. Any failed check stops the job and records an
error. The launcher does no test or build when merely copied to this directory.

Conditions registered before the run:
  M: version_desc, origin initial, production model registry is unregistered.
     Expect model-unregistered, a closed rejected history row, zero builds.
  X: U1 + Silo intra-transaction fix + lock-order skeleton + version_desc.
     Expect D1 and D2 counts zero, D5 pass, required true, certified verifier
     result, and certified history row in both RMW and blind-write workloads.
  S: U1 + lock-order skeleton + version_desc, without the Silo fix.
     Expect D2b_i or D2b_ii > 0, a non-certified history row with a rejection
     code and gate counts in both workloads.

The fixture model result uses sha256: followed by 64 f characters, one
completed/exhausted scenario with one configuration and a reached witness.
It checks model-gate plumbing only. The launcher outcome is fixture-liveness;
the history row's word certified describes the standalone verifier projection,
not a production campaign certification. A direct fixture build has no
pipeline-issued SourceEvidence or BuildAdmission, so the launcher records
capability_unavailable and uses verify_trace_dir with the required pre-build
D5 source snapshot. It does not invent a verification capability.

result.json fields:
  started, finished, seconds, host: job timing and location.
  stages: UTC start/end and elapsed seconds for dependencies, each checkout,
    admission, build, and each run plus verification.
  inputs: repository HEAD, pin, bundle and patch paths and sha256 hashes.
  M: production model decision, build count, exact driver history row.
  fixture: deliberately synthetic digest, bytes hash, and evidence kind.
  conditions.X/S: checkout SHA, git status after checkout/each patch/hole write,
    patch check/apply rc and verbose output, gate preview/write decisions,
    fixture model decision, source snapshot, trace build rc and binary hash.
  conditions.X/S.runs: workload flags, run rc, commits, batch commits, aborts,
    verifier path and capability reason, verdict/certified, gate required/version,
    D5, D1/D2/unreachable counts, occurrence counts, integrity and history row.
    archive.path and archive.sha256 identify the trace/gate tarball; members
    gives each archived file's sha256. Run stdout/stderr hashes are included.
  errors: the stage, exception type and message when execution stops early.

The serial job has two condition trace builds, four runs, and four verifications
when all admissions succeed. The precedent dependency preparer also performs
one stock bootstrap build; this is not an X/S condition build. Expected wall
time is 3 to 6 minutes, based on the
md14 precedent of 117 to 130 seconds for one build plus two workloads.
No runtime outcome has been observed by the author of this launcher.
