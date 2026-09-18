#!/usr/bin/env python3
"""dev-wave Codex worker launcher への thin dispatcher。"""
from __future__ import annotations

import argparse
import hashlib
import os
import re
import subprocess
import sys
import textwrap
from decimal import Decimal
from pathlib import Path
from typing import Sequence


_ROOT = Path(__file__).resolve().parents[1]
if os.fspath(_ROOT) not in sys.path:
    sys.path.insert(0, os.fspath(_ROOT))

from tools.dev_waves.schema import canonical_decimal
from tools.dev_waves.git_state import commit_worker_worktree
from tools.dev_waves.time_values import positive_safe_nanosecond_decimal


STAGES = ("plan", "consult", "author", "review", "fix", "focus")
LANES = ("sol", "luna")
AUTHORITY_BOUND_STAGES = frozenset({"review", "focus", "author", "fix"})

# These are deliberately operational defaults, not docs authority.
DEFAULT_WALL_CLOCK_ADMISSION_BOUND_S = 3600
DEFAULT_PREPARATION_ADMISSION_BOUND_S = 60
DEFAULT_FINALIZATION_ADMISSION_BOUND_S = 60
DEFAULT_MAX_MODEL_CALLS = 100
DEFAULT_MAX_CLI_REPORTED_TOKENS = 1_000_000
DEFAULT_EVIDENCE_GRACE_S = Decimal("90")

_SLUG_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
_HEX40_RE = re.compile(r"[0-9a-f]{40}\Z")
_NON_AUTHORITY_HELP = "これは非権威の運用既定であり docs 権威ではない"


class _NoHyphenBreakFormatter(argparse.HelpFormatter):
    def _split_lines(self, text: str, width: int) -> list[str]:
        text = self._whitespace_matcher.sub(" ", text).strip()
        return textwrap.wrap(text, width, break_on_hyphens=False)


def _positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("正整数が必要") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("正整数が必要")
    return parsed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "dev-wave の入力から codex_worker_launch.py run の必須 argv を生成する"
        ),
        formatter_class=_NoHyphenBreakFormatter,
    )
    parser.add_argument("--stage", choices=STAGES, required=True)
    parser.add_argument("--lane", choices=LANES)
    parser.add_argument("--wave", required=True, help="wave slug")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("-o", "--output-file", type=Path, required=True)
    parser.add_argument("--reasoning")
    parser.add_argument(
        "--sandbox", choices=("read-only", "workspace-write"), required=True
    )
    parser.add_argument("--repo-root", type=Path, default=_ROOT)
    parser.add_argument("--job-id")
    parser.add_argument(
        "--preparation-admission-bound-s",
        type=_positive_int,
        default=DEFAULT_PREPARATION_ADMISSION_BOUND_S,
        help=(
            "job 起点から初回 Popen 直前までの準備 admission 上限 "
            "(--version の実測時間は除外)。"
            f"(既定: {DEFAULT_PREPARATION_ADMISSION_BOUND_S}); "
            f"{_NON_AUTHORITY_HELP}"
        ),
    )
    parser.add_argument(
        "--wall-clock-admission-bound-s",
        type=_positive_int,
        default=DEFAULT_WALL_CLOCK_ADMISSION_BOUND_S,
        help=(
            "--version の実測時間と、初回 Popen 直前から最終 attempt の "
            "wall-clock 採取完了までの和に対する上限 "
            f"(既定: {DEFAULT_WALL_CLOCK_ADMISSION_BOUND_S}); "
            f"{_NON_AUTHORITY_HELP}"
        ),
    )
    parser.add_argument(
        "--finalization-admission-bound-s",
        type=_positive_int,
        default=DEFAULT_FINALIZATION_ADMISSION_BOUND_S,
        help=(
            "最終 attempt の wall-clock 採取完了から receipt の atomic 公開 "
            "完了まで (attempt seal を含む) の最終化 admission 上限 "
            f"(既定: {DEFAULT_FINALIZATION_ADMISSION_BOUND_S}); "
            f"{_NON_AUTHORITY_HELP}"
        ),
    )
    parser.add_argument(
        "--max-model-calls",
        type=_positive_int,
        default=DEFAULT_MAX_MODEL_CALLS,
        help=(
            f"model call 観測上限 (既定: {DEFAULT_MAX_MODEL_CALLS}); "
            f"{_NON_AUTHORITY_HELP}"
        ),
    )
    parser.add_argument(
        "--max-cli-reported-tokens",
        type=_positive_int,
        default=DEFAULT_MAX_CLI_REPORTED_TOKENS,
        help=(
            "CLI reported token 観測上限 "
            f"(既定: {DEFAULT_MAX_CLI_REPORTED_TOKENS}); {_NON_AUTHORITY_HELP}"
        ),
    )
    parser.add_argument(
        "--max-attempts",
        type=_positive_int,
        default=None,
        help="同一 job の最大 attempt 数 (省略時は launcher 既定の 1)",
    )
    parser.add_argument(
        "--evidence-grace-s",
        type=positive_safe_nanosecond_decimal,
        default=None,
        help=(
            "evidence 待機猶予 "
            "(既定: min(90, --wall-clock-admission-bound-s); 90 秒を上限とする"
            "暫定運用値であり測定された最小値ではない); "
            f"{_NON_AUTHORITY_HELP}。ただし受理集合に影響するため、"
            "--wall-clock-admission-bound-s が 90 未満ならそれに切り下げる "
            "(子の起動完了時を起点とする)。wall deadline は Popen 直前を"
            "起点とし --version 所要も加算するため、version と spawn の"
            "所要分だけ evidence grace の終端より早い"
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="生成した argv を 1 行 1 引数で表示し、起動しない",
    )
    return parser


def _absolute(parser: argparse.ArgumentParser, path: Path, option: str) -> Path:
    if not path.is_absolute():
        parser.error(f"{option} は absolute path が必要")
    return path.resolve(strict=False)


def _resolve_base_commit(
    parser: argparse.ArgumentParser, repo_root: Path
) -> str:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                os.fspath(repo_root),
                "rev-parse",
                "--verify",
                "HEAD^{commit}",
            ],
            check=False,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except OSError as exc:
        parser.error(f"--repo-root の HEAD を解決できない: {exc}")
    commit = result.stdout.strip()
    if result.returncode != 0 or _HEX40_RE.fullmatch(commit) is None:
        detail = result.stderr.strip() or "40 桁 commit を得られなかった"
        parser.error(f"--repo-root の HEAD を解決できない: {detail}")
    return commit


def _validate_combinations(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    if args.evidence_grace_s is None:
        args.evidence_grace_s = min(
            DEFAULT_EVIDENCE_GRACE_S, Decimal(args.wall_clock_admission_bound_s)
        )
    if args.evidence_grace_s > args.wall_clock_admission_bound_s:
        parser.error(
            "--evidence-grace-s は --wall-clock-admission-bound-s 以下でなければならない"
        )
    if _SLUG_RE.fullmatch(args.wave) is None:
        parser.error("--wave は path separator を含まない slug が必要")
    if args.job_id is not None and _SLUG_RE.fullmatch(args.job_id) is None:
        parser.error("--job-id は path separator を含まない id が必要")
    if args.stage == "consult":
        if args.lane is None:
            parser.error("--stage consult には --lane が必要")
    elif args.lane is not None:
        parser.error("--lane は --stage consult でだけ指定できる")
    if args.stage in AUTHORITY_BOUND_STAGES:
        if args.reasoning is not None:
            parser.error(
                "--reasoning は --stage review/focus/author/fix では指定できない"
            )
    elif args.reasoning is None or not args.reasoning.strip():
        parser.error(
            "--reasoning は --stage review/focus/author/fix 以外では必須"
        )
    if args.max_attempts is not None and args.max_attempts > 1:
        if args.sandbox != "read-only":
            parser.error(
                "--max-attempts > 1 は --sandbox read-only のときだけ許可される"
            )


def _launcher_argv(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> list[str]:
    _validate_combinations(parser, args)
    repo_root = _absolute(parser, args.repo_root, "--repo-root")
    prompt_file = _absolute(parser, args.prompt_file, "--prompt-file")
    artifact_root = _absolute(parser, args.artifact_root, "--artifact-root")
    output_file = _absolute(parser, args.output_file, "--output-file")
    base_commit = _resolve_base_commit(parser, repo_root)
    job_key = args.stage + (f"-{args.lane}" if args.lane else "")
    job_id = args.job_id
    if job_id is None:
        try:
            prompt_bytes = prompt_file.read_bytes()
        except OSError as exc:
            parser.error(f"--prompt-file を読めない: {exc}")
        if not prompt_bytes:
            parser.error("--prompt-file は non-empty file が必要")
        prompt_sha256 = hashlib.sha256(prompt_bytes).hexdigest()
        job_id = f"{args.wave}-{job_key}-{prompt_sha256}"
    if len(job_id) > 128:
        parser.error("生成した --job-id は 128 文字以内でなければならない")
    wave_artifact_root = artifact_root / args.wave
    artifact_dir = wave_artifact_root / job_id
    args.generated_directories = (wave_artifact_root, artifact_dir)
    receipt = artifact_dir / "receipt.json"
    args.receipt_path = receipt
    args.job_id = job_id
    manifest = wave_artifact_root / "manifest.json"

    argv = [
        "python3",
        os.fspath(repo_root / "tools" / "codex_worker_launch.py"),
        "run",
        "--stage",
        args.stage,
    ]
    if args.lane is not None:
        argv.extend(("--lane", args.lane))
    argv.extend(
        (
            "--job-id",
            job_id,
            "--wave-id",
            args.wave,
            "--repo-root",
            os.fspath(repo_root),
            "--base-commit",
            base_commit,
            "--prompt-file",
            os.fspath(prompt_file),
            "--cwd",
            os.fspath(repo_root),
            "--sandbox",
            args.sandbox,
        )
    )
    if args.stage not in AUTHORITY_BOUND_STAGES:
        argv.extend(("--reasoning", args.reasoning))
    argv.extend(
        (
            "--preparation-admission-bound-s",
            str(args.preparation_admission_bound_s),
            "--wall-clock-admission-bound-s",
            str(args.wall_clock_admission_bound_s),
            "--finalization-admission-bound-s",
            str(args.finalization_admission_bound_s),
            "--evidence-grace-s",
            canonical_decimal(args.evidence_grace_s),
            "--max-model-calls",
            str(args.max_model_calls),
            "--max-cli-reported-tokens",
            str(args.max_cli_reported_tokens),
        )
    )
    if args.max_attempts is not None:
        argv.extend(("--max-attempts", str(args.max_attempts)))
    argv.extend(
        (
            "--artifact-dir",
            os.fspath(artifact_dir),
            "--output-file",
            os.fspath(output_file),
            "--receipt",
            os.fspath(receipt),
            "--manifest",
            os.fspath(manifest),
        )
    )
    return argv


def _create_generated_directories(
    parser: argparse.ArgumentParser, directories: Sequence[Path]
) -> None:
    for directory in directories:
        created = False
        try:
            directory.mkdir(mode=0o700)
            created = True
        except FileExistsError:
            pass
        except OSError as exc:
            parser.error(f"生成 directory を作れない: {directory}: {exc}")
        if not directory.is_dir():
            parser.error(f"生成 path が directory ではない: {directory}")
        if created:
            try:
                directory.chmod(0o700)
            except OSError as exc:
                parser.error(
                    f"生成 directory を mode 0o700 にできない: {directory}: {exc}"
                )


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    launcher_argv = _launcher_argv(parser, args)
    _create_generated_directories(parser, args.generated_directories)
    if args.dry_run:
        print("\n".join(launcher_argv))
        return 0
    try:
        launcher_rc = subprocess.run(launcher_argv, check=False).returncode
    except OSError as exc:
        parser.error(f"launcher を起動できない: {exc}")
    if args.sandbox == "workspace-write":
        if args.stage in ("author", "fix"):
            status, _detail = commit_worker_worktree(
                args.repo_root, wave=args.wave, job_id=args.job_id,
                stage=args.stage, launcher_rc=launcher_rc,
                receipt_path=args.receipt_path,
            )
            if launcher_rc == 0 and status in ("refused", "failed"):
                return 3
        else:
            print("worktree-commit: skipped reason=stage", flush=True)
    return launcher_rc


if __name__ == "__main__":
    raise SystemExit(main())
