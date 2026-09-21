"""Submit four bounded B-5 pilot jobs, each from its own dedicated clean checkout.

The 8h/3h walltimes are provisional pilot limits, not cohort authorization.
Dry-run prints exact environment and argv; only --submit creates directories.
"""
from __future__ import annotations

import argparse
from collections.abc import Mapping
from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
import subprocess
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from orchestrator.campaign.b5_generator_contrast import (
    B_EVALUATIONS, N_EVAL, BLOCK_STOCK_SESSIONS, PILOT_LOGICAL_SESSION_CAP,
)
from orchestrator.campaign import p3_s4_loop

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


def main(argv=None) -> int:
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
