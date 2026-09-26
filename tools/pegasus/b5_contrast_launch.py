"""Submit B-5 pilot or registered stage jobs from dedicated clean checkouts.

The 8h/3h walltimes are provisional pilot limits, not cohort authorization.
Dry-run prints exact environment and argv; only --submit creates directories.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass, replace
import datetime
from decimal import Decimal, InvalidOperation, ROUND_CEILING, localcontext
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign.b5_generator_contrast import (
    B_EVALUATIONS, N_EVAL, BLOCK_STOCK_SESSIONS, PILOT_LOGICAL_SESSION_CAP,
    COHORT_REGISTERED, WORKLOADS,
)
from orchestrator.campaign import p3_s4_loop
from orchestrator.campaign import b5_generator_contrast as core
from tools.pegasus.b5_llm_parent import Parent, read_config

JOB_BODY = "tools/pegasus/p3_s4_loop_pegasus.sh"
PILOT_ARMS = ("random", "sweep-matched", "llm", "stock")


@dataclass(frozen=True)
class SubmitTree:
    repo: Path
    expected_head: str
    common_repo: Path
    thirdparty_source_root: Path | None = None


@dataclass(frozen=True)
class K2:
    manifest: Path
    classification: str
    de_novo_claim: str
    coder_role: str = "coder-v4-autonomous-k2"


@dataclass(frozen=True)
class PilotJob:
    mode: str
    arm: str
    workload: str
    series: int
    block: int
    ledger_root: Path
    evidence_root: Path
    k2: K2 | None = None


def _value(value: object) -> str:
    text = str(value)
    if not text or any(c.isspace() or c in ",\x00" for c in text):
        raise ValueError("qsub -v values must be nonempty, without commas or whitespace")
    return text


def _absolute(path: Path, label: str) -> Path:
    path = Path(_value(path))
    if not path.is_absolute():
        raise ValueError(f"{label} must be absolute")
    return Path(_value(path.resolve()))


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args], check=True,
        capture_output=True, text=True,
    )
    return result.stdout.strip()


def validate_submit_tree(repo: Path, expected_head: str) -> SubmitTree:
    """Read-only admission: full OIDs, tracked status and dedicated location."""
    original = Path(repo)
    repo = _absolute(original, "repository root")
    if original.is_symlink() or not repo.is_dir():
        raise ValueError("repository root is unavailable or a symlink")
    if any(f"/{name}/worktrees/" in str(repo) + "/" for name in (".claude", ".codex")):
        raise ValueError("repository root must not be inside an AI worktree container")
    if re.fullmatch(r"[0-9a-f]{40}", expected_head) is None:
        raise ValueError("expected HEAD must be a full lowercase commit")
    if _git(repo, "rev-parse", "--show-toplevel") != str(repo):
        raise ValueError("repository root must be the checkout root")
    if _git(repo, "rev-parse", "--verify", "HEAD^{commit}") != expected_head:
        raise ValueError("expected HEAD mismatch")
    if _git(repo, "status", "--porcelain", "--untracked-files=no", "--ignore-submodules=all"):
        raise ValueError("superproject tracked worktree is not clean")
    ccbench = repo / "external/ccbench"
    if ccbench.is_symlink() or not ccbench.is_dir():
        raise ValueError("CCBench source root is unavailable")
    if _git(ccbench, "rev-parse", "--show-toplevel") != str(ccbench):
        raise ValueError("CCBench is not a separate checkout")
    pins = re.findall(r'^PIN = "([0-9a-f]{40})"$',
                      (repo / "orchestrator/campaign/p3_s4_loop.py").read_text(), re.MULTILINE)
    if len(pins) != 1:
        raise ValueError("target checkout must declare exactly one P3 S4 PIN")
    if _git(ccbench, "rev-parse", "--verify", "HEAD^{commit}") != pins[0]:
        raise ValueError("CCBench P3 S4 campaign pin mismatch")
    if _git(ccbench, "status", "--porcelain", "--untracked-files=no"):
        raise ValueError("CCBench source tree is not clean")
    common_dir = Path(_git(repo, "rev-parse", "--path-format=absolute", "--git-common-dir"))
    return SubmitTree(repo, expected_head, common_dir.parent.resolve())


def _validate_job(spec: PilotJob) -> None:
    if (spec.arm not in PILOT_ARMS or spec.workload != "write-heavy"
            or type(spec.series) is not int or spec.series != 1
            or type(spec.block) is not int or spec.block != 1
            or spec.mode != ("block-stock" if spec.arm == "stock" else "series")):
        raise ValueError("pilot requires write-heavy, series 1, block 1 and registered arms")
    if (spec.arm == "llm") != (spec.k2 is not None):
        raise ValueError("K2 is required only for llm")
    if spec.k2 is not None:
        if spec.k2.coder_role != "coder-v4-autonomous-k2":
            raise ValueError("pilot requires coder-v4-autonomous-k2")
        _absolute(spec.k2.manifest, "knowledge manifest")
        _value(spec.k2.classification)
        if spec.k2.de_novo_claim not in ("true", "false"):
            raise ValueError("invalid knowledge de novo claim")
    _absolute(spec.ledger_root, "ledger root")
    _absolute(spec.evidence_root, "evidence root")


def validate_pilot_cap(jobs: tuple[PilotJob, ...]) -> int:
    """Freeze the authorized shape as well as its arithmetic upper bound."""
    if (B_EVALUATIONS, N_EVAL, BLOCK_STOCK_SESSIONS, PILOT_LOGICAL_SESSION_CAP) != (10, 5, 5, 60):
        raise ValueError("registered pilot budgets changed")
    if len(jobs) != 4 or tuple(job.arm for job in jobs) != PILOT_ARMS:
        raise ValueError("pilot must contain exactly four registered jobs")
    for job in jobs:
        _validate_job(job)
    roots = [_absolute(root, "job root") for job in jobs
             for root in (job.ledger_root, job.evidence_root)]
    if any(a == b or a in b.parents or b in a.parents
           for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ValueError("pilot ledger and evidence roots must be disjoint")
    sessions = sum(BLOCK_STOCK_SESSIONS if j.mode == "block-stock"
                   else 1 + B_EVALUATIONS + N_EVAL for j in jobs)
    if sessions > PILOT_LOGICAL_SESSION_CAP:
        raise ValueError("pilot logical session cap exceeded")
    return sessions


def pilot_jobs(workload: str, ledger_root: Path, evidence_root: Path,
               k2: K2) -> tuple[PilotJob, ...]:
    ledger_root = _absolute(ledger_root, "ledger root")
    evidence_root = _absolute(evidence_root, "evidence root")
    jobs = tuple(
        PilotJob("block-stock" if arm == "stock" else "series", arm, workload,
                 1, 1, ledger_root / ("block-stock" if arm == "stock" else arm),
                 evidence_root / ("block-stock" if arm == "stock" else arm),
                 k2 if arm == "llm" else None)
        for arm in PILOT_ARMS
    )
    validate_pilot_cap(jobs)
    return jobs


def _outside_repository(path: Path, tree: SubmitTree) -> Path:
    path = _absolute(path, "output root")
    for root in (tree.repo, tree.common_repo):
        if path == root or root in path.parents:
            raise ValueError("output root resolves inside a repository")
    return path


def build_job_environment(spec: PilotJob, tree: SubmitTree) -> dict[str, str]:
    _validate_job(spec)
    if tree.thirdparty_source_root is None:
        raise ValueError("third-party source root required")
    thirdparty = _absolute(tree.thirdparty_source_root, "third-party source root")
    if not thirdparty.is_dir() or tree.thirdparty_source_root.is_symlink():
        raise ValueError("third-party source root is unavailable")
    evidence = _outside_repository(spec.evidence_root, tree)
    ledger = _outside_repository(spec.ledger_root, tree)
    env = {
        "IZANAGI_S4_REPO_ROOT": str(tree.repo),
        "IZANAGI_S4_EXPECTED_HEAD": tree.expected_head,
        "IZANAGI_S4_EVIDENCE_ROOT": str(evidence),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty),
        "IZANAGI_S4_B5_MODE": spec.mode,
        "IZANAGI_S4_B5_ARM": spec.arm,
        "IZANAGI_S4_B5_WORKLOAD": spec.workload,
        "IZANAGI_S4_B5_SERIES": str(spec.series),
        "IZANAGI_S4_B5_BLOCK": str(spec.block),
        "IZANAGI_S4_B5_LEDGER_ROOT": str(ledger),
    }
    if spec.k2 is not None:
        env.update({
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": str(_absolute(spec.k2.manifest, "manifest")),
            "IZANAGI_S4_CODER_ROLE": spec.k2.coder_role,
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": spec.k2.classification,
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": spec.k2.de_novo_claim,
        })
    return {key: _value(value) for key, value in env.items()}


def qsub_argv(spec: PilotJob, tree: SubmitTree) -> list[str]:
    return _qsub_argv(spec, build_job_environment(spec, tree))


def _qsub_argv(spec: PilotJob, env: dict[str, str]) -> list[str]:
    evidence = Path(env["IZANAGI_S4_EVIDENCE_ROOT"])
    walltime = "03:00:00" if spec.mode == "block-stock" else "08:00:00"
    return ["qsub", "-v", ",".join(f"{k}={v}" for k, v in env.items()),
            "-l", f"elapstim_req={walltime}",
            "-o", str(evidence / "job.stdout"),
            "-e", str(evidence / "job.stderr"), JOB_BODY]


def launch(jobs: tuple[PilotJob, ...], trees_by_arm: Mapping[str, SubmitTree], *, submit: bool,
           runner=None) -> int:
    """Validate the entire pilot before the first mkdir or scheduler call."""
    validate_pilot_cap(jobs)
    commands = []
    for job in jobs:
        tree = trees_by_arm[job.arm]
        env = build_job_environment(job, tree)
        commands.append((job, tree, env, _qsub_argv(job, env)))
    for job, tree, env, argv in commands:
        for path in (job.evidence_root, job.ledger_root):
            if path.exists() or path.is_symlink():
                raise ValueError(f"pilot root is not fresh: {path}")
    if not submit:
        for job, tree, env, argv in commands:
            print(json.dumps({"arm": job.arm, "environment": env, "argv": argv}, sort_keys=True))
        return 0
    if runner is None:
        runner = subprocess.run
    for job, tree, env, argv in commands:
        # The attempt directory belongs to the job body; never put a log here.
        Path(env["IZANAGI_S4_EVIDENCE_ROOT"]).mkdir(mode=0o700, parents=True)
        result = runner(argv, cwd=tree.repo)
        if result.returncode:
            return result.returncode  # no retry after partial submission
    return 0


@dataclass(frozen=True)
class RegisteredJob:
    job_id: str
    stage: int
    mode: str
    arm: str
    workload: str
    series: int
    block: int
    ledger_root: Path
    evidence_root: Path
    k2: K2 | None = None


def registered_schedule() -> dict:
    """D-2 reverse pairs; execution barriers remain an operator procedure.

    The 36 order rows describe 108 arm series. Job IDs also key submit-trees.
    """
    pairs = (("LRS", "SRL"), ("LSR", "RSL"), ("RLS", "SLR"))
    arms = {"L": "llm", "R": "random", "S": "sweep-matched"}
    orders, jobs = [], []
    for w, workload in enumerate(WORKLOADS):
        for series in range(1, 13):
            block = (series - 1) // 4 + 1
            excluded = (w + block - 1) % 3
            x, y = [pair for i, pair in enumerate(pairs) if i != excluded]
            order = (x[0], y[0], x[1], y[1])[(series - 1) % 4]
            orders.append(dict(workload=workload, series=series, block=block, order=order))
            for stage, letter in enumerate(order, 1):
                arm = arms[letter]
                jobs.append(dict(job_id=f"b{block}-{workload}-r{series:02d}-{arm}",
                                 workload=workload, series=series, block=block,
                                 stage=stage, arm=arm, mode="series"))
        for block in range(1, 4):
            jobs.append(dict(job_id=f"b{block}-{workload}-stock", workload=workload,
                             series=block, block=block, stage=2, arm="stock", mode="block-stock"))
    jobs.sort(key=lambda j: (j["block"], j["stage"], WORKLOADS.index(j["workload"]),
                             j["series"], j["arm"]))
    return {"cohort": COHORT_REGISTERED, "orders": orders, "jobs": jobs}


def registered_walltimes(k: str) -> dict:
    """Exact Decimal multiplier, ceilings in seconds, unwrapped scheduler hours."""
    try:
        factor = Decimal(k)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ValueError("walltime factor must be finite and 0 < k <= 4.06") from exc
    if not factor.is_finite() or not 0 < factor <= Decimal("4.06"):
        raise ValueError("walltime factor must be finite and 0 < k <= 4.06")
    result = {}
    # Preserve long decimal inputs even immediately above an integral boundary.
    with localcontext() as context:
        context.prec = max(28, len(factor.as_tuple().digits) + 6)
        for mode, base in (("series", 21259), ("block-stock", 5447)):
            seconds = int((base * factor).to_integral_value(rounding=ROUND_CEILING))
            result[mode] = {"seconds": seconds,
                            "walltime": f"{seconds // 3600:02d}:{seconds % 3600 // 60:02d}:{seconds % 60:02d}"}
    return result


def registered_jobs(block: int, stage: int, ledger_root: Path, evidence_root: Path,
                    k2: K2) -> tuple[RegisteredJob, ...]:
    if block not in (1, 2, 3) or stage not in (1, 2, 3):
        raise ValueError("block and stage must be 1, 2 or 3")
    ledger_root = _absolute(ledger_root, "ledger root")
    evidence_root = _absolute(evidence_root, "evidence root")
    jobs = []
    for row in registered_schedule()["jobs"]:
        if (row["block"], row["stage"]) != (block, stage):
            continue
        suffix = Path(COHORT_REGISTERED) / f"block-{block}" / row["workload"]
        suffix /= "block-stock" if row["arm"] == "stock" else f"r{row['series']:02d}/{row['arm']}"
        jobs.append(RegisteredJob(**row, ledger_root=ledger_root / suffix,
                                  evidence_root=evidence_root / suffix,
                                  k2=k2 if row["arm"] == "llm" else None))
    return tuple(jobs)


def build_registered_environment(job: RegisteredJob, tree: SubmitTree) -> dict[str, str]:
    if tree.thirdparty_source_root is None:
        raise ValueError("third-party source root required")
    thirdparty = _absolute(tree.thirdparty_source_root, "third-party source root")
    if not thirdparty.is_dir() or tree.thirdparty_source_root.is_symlink():
        raise ValueError("third-party source root is unavailable")
    env = {
        "IZANAGI_S4_REPO_ROOT": str(tree.repo),
        "IZANAGI_S4_EXPECTED_HEAD": tree.expected_head,
        "IZANAGI_S4_EVIDENCE_ROOT": str(_outside_repository(job.evidence_root, tree)),
        "IZANAGI_S4_THIRDPARTY_SOURCE_ROOT": str(thirdparty),
        "IZANAGI_S4_B5_MODE": job.mode,
        "IZANAGI_S4_B5_ARM": job.arm,
        "IZANAGI_S4_B5_WORKLOAD": job.workload,
        "IZANAGI_S4_B5_SERIES": str(job.series),
        "IZANAGI_S4_B5_BLOCK": str(job.block),
        "IZANAGI_S4_B5_LEDGER_ROOT": str(_outside_repository(job.ledger_root, tree)),
        "IZANAGI_S4_B5_PURPOSE": "registered",
    }
    if (job.arm == "llm") != (job.k2 is not None):
        raise ValueError("K2 is required only for llm")
    if job.k2 is not None:
        if job.k2.coder_role != "coder-v4-autonomous-k2":
            raise ValueError("registered requires coder-v4-autonomous-k2")
        if job.k2.de_novo_claim not in ("true", "false"):
            raise ValueError("invalid knowledge de novo claim")
        env.update({
            "IZANAGI_S4_KNOWLEDGE_MANIFEST": str(_absolute(job.k2.manifest, "manifest")),
            "IZANAGI_S4_CODER_ROLE": job.k2.coder_role,
            "IZANAGI_S4_KNOWLEDGE_CLASSIFICATION": job.k2.classification,
            "IZANAGI_S4_KNOWLEDGE_DE_NOVO_CLAIM": job.k2.de_novo_claim,
        })
    return {key: _value(value) for key, value in env.items()}


def launch_registered(jobs: tuple[RegisteredJob, ...], submit_trees: Mapping[str, str], *,
                      expected_head: str, thirdparty_source_root: Path,
                      walltime_factor: str, submit: bool, runner=None) -> int:
    """Finish all tree, output and freshness checks before any stage submission."""
    walltimes = registered_walltimes(walltime_factor)
    trees = {}
    for job in jobs:
        if job.job_id not in submit_trees:
            raise ValueError(f"missing submit-tree for {job.job_id}")
        trees[job.job_id] = replace(
            validate_submit_tree(Path(submit_trees[job.job_id]), expected_head),
            thirdparty_source_root=thirdparty_source_root)
    if len({tree.repo for tree in trees.values()}) != len(jobs):
        raise ValueError("registered jobs require distinct submit-trees")
    roots = [_absolute(root, "job root") for job in jobs
             for root in (job.ledger_root, job.evidence_root)]
    if any(a == b or a in b.parents or b in a.parents
           for i, a in enumerate(roots) for b in roots[i + 1:]):
        raise ValueError("registered ledger and evidence roots must be disjoint")
    for root in roots:
        for tree in trees.values():
            _outside_repository(root, tree)
        if root.exists() or root.is_symlink():
            raise ValueError(f"registered root is not fresh: {root}")
    commands = []
    for job in jobs:
        tree = trees[job.job_id]
        env = build_registered_environment(job, tree)
        argv = _qsub_argv(job, env)
        argv[argv.index("-l") + 1] = "elapstim_req=" + walltimes[job.mode]["walltime"]
        commands.append((job, tree, env, argv))
    if not submit:
        for job, tree, env, argv in commands:
            print(json.dumps({"job_id": job.job_id, "cwd": str(tree.repo),
                              "environment": env, "argv": argv}, sort_keys=True))
        return 0
    if runner is None:
        runner = subprocess.run
    for job, tree, env, argv in commands:
        Path(env["IZANAGI_S4_EVIDENCE_ROOT"]).mkdir(mode=0o700, parents=True)
        result = runner(argv, cwd=tree.repo)
        if result.returncode:
            return result.returncode
    return 0


def registered_v2_schedule() -> dict:
    """Reuse the v1 balanced arm order, restricted to the two v2 workloads."""
    old = registered_schedule()
    orders = [row for row in old["orders"] if row["workload"] in ("write-heavy", "balanced")]
    jobs = []
    for row in orders:
        for stage, letter in enumerate(row["order"], 1):
            arm = {"L": "llm", "R": "random", "S": "sweep-matched"}[letter]
            jobs.append({"job_id": f"b{row['block']}-{row['workload']}-r{row['series']:02d}-{arm}",
                         "workload": row["workload"], "series": row["series"],
                         "block": row["block"], "stage": stage, "arm": arm, "mode": "series-step"})
    for workload in ("write-heavy", "balanced"):
        for block in range(1, 4):
            jobs.append({"job_id": f"b{block}-{workload}-stock", "workload": workload,
                         "series": block, "block": block, "stage": 0, "arm": "stock",
                         "mode": "block-stock"})
    return {"cohort": core.COHORT_REGISTERED_V2, "orders": orders, "jobs": jobs}


def registered_v2_jobs(ledger_root: Path, evidence_root: Path, k2: K2) -> tuple[RegisteredJob, ...]:
    jobs = []
    for row in registered_v2_schedule()["jobs"]:
        suffix = (Path(core.COHORT_REGISTERED_V2) / f"block-{row['block']}" /
                  row["workload"] / ("block-stock" if row["arm"] == "stock" else
                                     f"r{row['series']:02d}/{row['arm']}"))
        jobs.append(RegisteredJob(**row, ledger_root=ledger_root / suffix,
                                  evidence_root=evidence_root / suffix,
                                  k2=k2 if row["arm"] == "llm" else None))
    return tuple(jobs)


class V2Launcher:
    """One login writer. Each tick advances at most one unit of each open series."""

    def __init__(self, jobs: tuple[RegisteredJob, ...], trees: Mapping[str, SubmitTree],
                 *, parent_config: dict, state_root: Path, max_active_series: int,
                 submitter=subprocess.run, parent_factory=Parent):
        if not 1 <= max_active_series <= 72:
            raise ValueError("invalid active series limit")
        self.jobs = jobs
        self.trees = trees
        self.parent_config = parent_config
        self.state_root = Path(state_root)
        self.max_active_series = max_active_series
        self.submitter = submitter
        self.parent_factory = parent_factory
        self.parents = {}
        self.inflight = set()
        self.lock = None
        if set(job.job_id for job in jobs) - set(trees):
            raise ValueError("missing submit tree")
        parents = {item["job_id"]: item for item in parent_config.get("series", [])}
        for job in jobs:
            if job.arm != "llm":
                continue
            item = parents.get(job.job_id)
            if item is None or (item["workload"], item["series"], item["block"],
                                Path(item["ledger_root"])) != (
                                    job.workload, job.series, job.block, job.ledger_root):
                raise ValueError(f"parent series coordinates mismatch: {job.job_id}")

    def __enter__(self):
        self.state_root.mkdir(parents=True, exist_ok=True)
        self.lock = (self.state_root / "launcher.lock").open("a+")
        try:
            fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("another v2 launcher owns the lock") from exc
        self.lock.seek(0)
        self.lock.truncate()
        self.lock.write(str(os.getpid()) + "\n")
        self.lock.flush()
        return self

    def __exit__(self, *_):
        fcntl.flock(self.lock, fcntl.LOCK_UN)
        self.lock.close()

    def _parent(self, job, a):
        key = (job.job_id, a)
        if key not in self.parents:
            self.parents[key] = self.parent_factory(
                self.parent_config, self.state_root / "parents" / job.job_id)
        return self.parents[key]

    def _parent_item(self, job):
        matches = [item for item in self.parent_config["series"] if item["job_id"] == job.job_id]
        if len(matches) != 1:
            raise ValueError(f"parent config lacks {job.job_id}")
        return matches[0]

    def _request(self, ledger, a, b):
        directory = ledger.root / "handshake"
        directory.mkdir(exist_ok=True)
        request = directory / f"request-{a}.json"
        if not request.exists():
            core._publish(request, {"a": a, **core.expected_inputs(ledger, b + 1),
                                    "deadline_utc": core._utc(time.time() + core.LLM_WAIT_S)})
        return request

    def _drive_parent(self, job, ledger, a, *, first):
        handshake = ledger.root / "handshake"
        proposal = handshake / f"proposal-{a}.json"
        rejected = handshake / f"proposal-{a}.rejected.json"
        inputs = handshake / f"inputs-{a}.json"
        if proposal.exists() and inputs.exists() or rejected.exists():
            if first and any(e["kind"] == "proposal-opportunity" and e["a"] == a
                             for e in ledger.events):
                return "ready"
            if proposal.exists() and rejected.exists():
                if first:
                    marker = handshake / f"stop-{a}.json"
                    if not marker.exists():
                        core._publish(marker, {"reason": "inheritance-mismatch"})
                else:
                    core._finish(ledger, "inheritance-mismatch", a - 1,
                                 sum(e["kind"] == "evaluation-result" for e in ledger.events))
                return "done"
            if rejected.exists():
                core._v2_proposal(ledger, a, sum(e["kind"] == "evaluation-result" for e in ledger.events),
                                  None, core._read_json(rejected))
            else:
                try:
                    actual = core._read_json(inputs)
                    b = sum(e["kind"] == "evaluation-result" for e in ledger.events)
                    core.assert_inherited_inputs(ledger, actual["planner_input"],
                                                 actual["coder_input"], next_evaluation=b + 1)
                except (ValueError, KeyError, TypeError):
                    if first:
                        marker = handshake / f"stop-{a}.json"
                        if not marker.exists():
                            core._publish(marker, {"reason": "inheritance-mismatch"})
                    else:
                        core._finish(ledger, "inheritance-mismatch", a - 1, b)
                    return "done"
                core._v2_proposal(ledger, a, b, proposal,
                                  {"inputs_path": str(inputs),
                                   "inputs_sha256": core.hashlib.sha256(inputs.read_bytes()).hexdigest()})
            return "ready"
        request = self._request(ledger, a, sum(e["kind"] == "evaluation-result" for e in ledger.events))
        if not first:
            outage = handshake / f"outage-{a}.json"
            if outage.exists():
                document = core._read_json(request)
                document["deadline_utc"] = core._utc(time.time() + core.LLM_WAIT_S)
                core._publish(request, document, replace=True)
                outage.unlink()
            deadline = datetime.datetime.fromisoformat(
                core._read_json(request)["deadline_utc"].replace("Z", "+00:00")).timestamp()
            if time.time() >= deadline:
                b = sum(e["kind"] == "evaluation-result" for e in ledger.events)
                parent = self._parent(job, a)
                if hasattr(parent, "stop"):
                    parent.stop(a)
                core._finish(ledger, "proposal-wait-timeout", a - 1, b, score=None)
                return "done"
        status = self._parent(job, a).tick(self._parent_item(job), a, request, handshake)
        if status == "success":
            if proposal.exists() != inputs.exists():
                if first:
                    marker = handshake / f"stop-{a}.json"
                    if not marker.exists():
                        core._publish(marker, {"reason": "inheritance-mismatch"})
                else:
                    b = sum(e["kind"] == "evaluation-result" for e in ledger.events)
                    core._finish(ledger, "inheritance-mismatch", a - 1, b)
                return "done"
            if not proposal.exists() and not rejected.exists():
                core._publish(rejected, {"reason": "empty-output"})
            return self._drive_parent(job, ledger, a, first=first)
        if status == "exhausted":
            b = sum(e["kind"] == "evaluation-result" for e in ledger.events)
            if first:
                core._publish(handshake / f"stop-{a}.json", {"reason": "unclassified-missing"})
            else:
                core._finish(ledger, "unclassified-missing", a - 1, b, score=None)
            return "done"
        return status

    def _submit(self, job, step=None):
        tree = self.trees[job.job_id]
        env = build_registered_environment(job, tree)
        env["IZANAGI_S4_B5_PURPOSE"] = "registered-v2"
        if step:
            env["IZANAGI_S4_B5_STEP"] = step
        existing = sorted(job.evidence_root.glob("job-*"))
        if any(not (path / "qsub-answer.txt").exists() for path in existing):
            raise RuntimeError(f"unanswered qsub for {job.job_id}")
        count = 1
        if job.evidence_root.exists():
            count += len(existing)
        evidence = job.evidence_root / f"job-{count:02d}"
        evidence.mkdir(parents=True, exist_ok=False)
        env["IZANAGI_S4_EVIDENCE_ROOT"] = str(evidence)
        argv = _qsub_argv(job, env)
        result = self.submitter(argv, cwd=tree.repo, capture_output=True, text=True, timeout=60)
        if result.returncode or not result.stdout.strip():
            raise RuntimeError(f"qsub failed or did not answer for {job.job_id}")
        (evidence / "qsub-answer.txt").write_text(result.stdout)
        self.inflight.add(job.job_id)
        return evidence

    def tick(self) -> dict[str, str]:
        status = {}
        active = 0
        # Schedule is frozen in pair order and arm order. Stock opens each batch.
        stock_busy = False
        for job in self.jobs:
            if job.arm != "stock":
                continue
            ledger = job.ledger_root
            if (ledger / "series.json").exists():
                end = core.SeriesLedger(ledger).events[-1]
                if end["kind"] == "series-end":
                    status[job.job_id] = "done" if end["reason"] == "b-complete" else "failed"
                    continue
            active_root = sorted(job.evidence_root.glob("job-*/compute-result.json"))
            if active_root:
                result = core._read_json(active_root[-1])
                if result["driver_rc"] != 0:
                    status[job.job_id] = "failed"
                    continue
            if job.evidence_root.exists() and any(job.evidence_root.glob("job-*/qsub-answer.txt")):
                if (ledger / "header.json").exists() and job.job_id not in self.inflight:
                    events = core.SeriesLedger(ledger).events
                    pending = next((e for e in reversed(events) if e["kind"] == "slot-attempt-start"
                                    and not any((later.get("logical_slot"), later.get("attempt")) ==
                                                (e["logical_slot"], e["attempt"]) and later["kind"] in
                                                {"machine-retry", "stock-start"}
                                                for later in events[e["event_seq"]:])), None)
                    if pending:
                        status[job.job_id] = "interrupted-slot"
                        continue
                status[job.job_id] = "running"
                stock_busy = True
                continue
            if stock_busy:
                status[job.job_id] = "pending-stock"
                continue
            self._submit(job)
            status[job.job_id] = "running"
            stock_busy = True
        for job in self.jobs:
            if job.arm == "stock":
                continue
            # Do not open a series until its batch stock has finished.
            stock = next(s for s in self.jobs if s.arm == "stock" and
                         (s.workload, s.block) == (job.workload, job.block))
            if status.get(stock.job_id) != "done":
                status[job.job_id] = ("blocked-stock" if status.get(stock.job_id) in
                                      ("failed", "interrupted-slot") else "pending-stock")
                continue
            if not job.ledger_root.joinpath("header.json").exists() and active >= self.max_active_series:
                status[job.job_id] = "pending-cap"
                continue
            if job.ledger_root.joinpath("header.json").exists():
                ledger = core.SeriesLedger(job.ledger_root)
                action, a = core.next_series_action(ledger)
                if action == "done":
                    status[job.job_id] = ("done" if ledger.events[-1]["reason"] in
                                          ("b-complete", "a-exhausted", "grid-exhausted") else "failed")
                    continue
                if action == "interrupted-slot":
                    evidence = sorted(job.evidence_root.glob("job-*/qsub-answer.txt"))
                    if (job.job_id in self.inflight and evidence and
                            not (evidence[-1].parent / "compute-result.json").exists()):
                        status[job.job_id] = "running"
                        continue
                    status[job.job_id] = "interrupted-slot"
                    continue
                active += 1
            else:
                ledger = None
                action, a = "stock-evaluation-1", None
                active += 1
            evidence = sorted(job.evidence_root.glob("job-*/qsub-answer.txt"))
            if evidence:
                last_dir = evidence[-1].parent
                result = last_dir / "compute-result.json"
                if not result.exists():
                    if job.arm == "llm" and ledger is not None:
                        first_a = sum(e["kind"] == "proposal-opportunity" for e in ledger.events) + 1
                        handshake = ledger.root / "handshake"
                        if (handshake / f"request-{first_a}.json").exists() and not (
                                handshake / f"outage-{first_a}.json").exists():
                            self._drive_parent(job, ledger, first_a, first=True)
                    status[job.job_id] = "running"
                    continue
                if core._read_json(result)["driver_rc"] != 0:
                    status[job.job_id] = "job-failed"
                    continue
                self.inflight.discard(job.job_id)
                # Only submit another job after the previous job has published its result.
                if ledger is not None:
                    action, a = core.next_series_action(core.SeriesLedger(job.ledger_root))
            if action == "proposal":
                if job.arm == "llm":
                    status[job.job_id] = self._drive_parent(job, ledger, a, first=False)
                else:
                    proposal, provenance = core._v2_machine_proposal(ledger, a)
                    core._v2_proposal(ledger, a,
                                      sum(e["kind"] == "evaluation-result" for e in ledger.events),
                                      proposal, provenance)
                    status[job.job_id] = "proposal-confirmed"
                continue
            if action in ("done", "interrupted-slot"):
                status[job.job_id] = ("done" if action == "done" and
                                      core.SeriesLedger(job.ledger_root).events[-1]["reason"] in
                                      ("b-complete", "a-exhausted", "grid-exhausted") else action)
                continue
            if action == "stock-evaluation-1" and job.arm == "llm" and ledger is not None:
                next_a = sum(e["kind"] == "proposal-opportunity" for e in ledger.events) + 1
                if (ledger.root / "handshake" / f"outage-{next_a}.json").exists():
                    state_path = self.state_root / "parents" / job.job_id / "state.json"
                    if state_path.exists() and time.time() < core._read_json(state_path)["next_retry"]:
                        status[job.job_id] = "outage"
                        continue
                (ledger.root / "handshake" / f"request-{next_a}.json").unlink(missing_ok=True)
            self._submit(job, action)
            status[job.job_id] = "running"
        return status


def _registered_main(argv) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("registered-schedule")
    registered = sub.add_parser("registered")
    registered.add_argument("--block", type=int, choices=(1, 2, 3), required=True)
    registered.add_argument("--stage", type=int, choices=(1, 2, 3), required=True)
    registered.add_argument("--walltime-factor", required=True)
    registered.add_argument("--submit-trees", type=Path, required=True)
    registered.add_argument("--expected-head", required=True)
    for name in ("ledger-root", "evidence-root", "thirdparty-source-root", "knowledge-manifest"):
        registered.add_argument("--" + name, type=Path, required=True)
    registered.add_argument("--knowledge-classification", required=True)
    registered.add_argument("--knowledge-de-novo-claim", choices=("true", "false"), required=True)
    action = registered.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--submit", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "registered-schedule":
        print(json.dumps(registered_schedule(), sort_keys=True))
        return 0
    try:
        mapping = json.loads(args.submit_trees.read_text())
        if not isinstance(mapping, dict) or any(not isinstance(v, str) for v in mapping.values()):
            raise ValueError("submit-trees must map job IDs to absolute paths")
        jobs = registered_jobs(args.block, args.stage, args.ledger_root, args.evidence_root,
                               K2(args.knowledge_manifest, args.knowledge_classification,
                                  args.knowledge_de_novo_claim))
        return launch_registered(jobs, mapping, expected_head=args.expected_head,
                                 thirdparty_source_root=args.thirdparty_source_root,
                                 walltime_factor=args.walltime_factor, submit=args.submit)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"b5_contrast_launch: {exc}", file=sys.stderr)
        return 2


def _registered_v2_main(argv) -> int:
    parser = argparse.ArgumentParser(description="B-5 v2 login launcher")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("registered-v2-schedule")
    run = sub.add_parser("registered-v2")
    for name in ("ledger-root", "evidence-root", "state-root", "submit-trees",
                 "thirdparty-source-root", "knowledge-manifest", "parent-config"):
        run.add_argument("--" + name, type=Path, required=True)
    run.add_argument("--expected-head", required=True)
    run.add_argument("--knowledge-classification", required=True)
    run.add_argument("--knowledge-de-novo-claim", choices=("true", "false"), required=True)
    run.add_argument("--max-active-series", type=int, required=True)
    run.add_argument("--poll-s", type=float, default=20)
    run.add_argument("--once", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "registered-v2-schedule":
        print(json.dumps(registered_v2_schedule(), sort_keys=True))
        return 0
    if args.poll_s <= 0:
        parser.error("poll period must be positive")
    try:
        mapping = json.loads(args.submit_trees.read_text())
        config = read_config(args.parent_config)
        jobs = registered_v2_jobs(args.ledger_root, args.evidence_root,
                                  K2(args.knowledge_manifest, args.knowledge_classification,
                                     args.knowledge_de_novo_claim))
        trees = {job.job_id: replace(
            validate_submit_tree(Path(mapping[job.job_id]), args.expected_head),
            thirdparty_source_root=args.thirdparty_source_root) for job in jobs}
        with V2Launcher(jobs, trees, parent_config=config, state_root=args.state_root,
                        max_active_series=args.max_active_series) as launcher:
            while True:
                status = launcher.tick()
                print(json.dumps(status, sort_keys=True), flush=True)
                if args.once or all(value in ("done", "interrupted-slot", "job-failed", "failed",
                                           "blocked-stock")
                                    for value in status.values()):
                    return 0 if all(value == "done" for value in status.values()) else 1
                time.sleep(args.poll_s)
    except (ValueError, OSError, KeyError, RuntimeError, subprocess.SubprocessError) as exc:
        print(f"b5_contrast_launch: {exc}", file=sys.stderr)
        return 2


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] in ("registered-v2-schedule", "registered-v2"):
        return _registered_v2_main(argv)
    if argv and argv[0] in ("registered-schedule", "registered"):
        return _registered_main(argv)
    parser = argparse.ArgumentParser(description=__doc__)
    for arm in PILOT_ARMS:
        parser.add_argument(f"--repo-root-{arm}", type=Path, required=True)
    parser.add_argument("--expected-head", required=True)
    parser.add_argument("--thirdparty-source-root", type=Path, required=True)
    parser.add_argument("--ledger-root", type=Path, required=True)
    parser.add_argument("--evidence-root", type=Path, required=True)
    parser.add_argument("--workload", choices=("write-heavy",), default="write-heavy")
    parser.add_argument("--knowledge-manifest", type=Path, required=True)
    parser.add_argument("--knowledge-classification", required=True)
    parser.add_argument("--knowledge-de-novo-claim", choices=("true", "false"), required=True)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--dry-run", action="store_true")
    action.add_argument("--submit", action="store_true")
    args = parser.parse_args(argv)
    try:
        trees_by_arm = {
            arm: replace(validate_submit_tree(
                getattr(args, f"repo_root_{arm.replace('-', '_')}"), args.expected_head),
                thirdparty_source_root=args.thirdparty_source_root)
            for arm in PILOT_ARMS
        }
        jobs = pilot_jobs(args.workload, args.ledger_root, args.evidence_root,
                          K2(args.knowledge_manifest, args.knowledge_classification,
                             args.knowledge_de_novo_claim))
        return launch(jobs, trees_by_arm, submit=args.submit)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"b5_contrast_launch: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
