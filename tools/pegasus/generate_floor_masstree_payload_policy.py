#!/usr/bin/env python3
"""Generate the independently reviewed masstree config policy.

This is an administrative producer.  The floor runtime deliberately does not
import this module: it only consumes the committed JSON and verifies the
recorded values against the staged payload.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from typing import Any


SCHEMA_VERSION = "s8b-floor-masstree-payload/v2"
SOURCE_NAME = "masstree"
PIN_RE = re.compile(r"[0-9a-f]{40}\Z")
HASH_RE = re.compile(r"[0-9a-f]{64}\Z")


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _policy_path() -> Path:
    return _repo_root() / "tools/pegasus/policy.json"


def _default_output_path() -> Path:
    return _repo_root() / "tools/pegasus/policies/floor_masstree_payload_v1.json"


def _reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    document: dict[str, Any] = {}
    for key, value in pairs:
        if key in document:
            raise ValueError(f"duplicate JSON key: {key}")
        document[key] = value
    return document


def _load_policy(path: Path) -> tuple[str, str]:
    try:
        with path.open(encoding="utf-8") as handle:
            policy = json.load(handle, object_pairs_hook=_reject_duplicate_keys)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"cannot read shared policy: {path}: {exc}") from exc

    try:
        sources = policy["silo_ladder_rung1"]["third_party_sources"]
        matches = [item for item in sources if item.get("name") == SOURCE_NAME]
    except (AttributeError, KeyError, TypeError) as exc:
        raise RuntimeError("shared policy has no valid masstree source entry") from exc
    if len(matches) != 1:
        raise RuntimeError("shared policy must contain exactly one masstree source entry")
    url = matches[0].get("url")
    pin = matches[0].get("pin")
    if (not isinstance(url, str) or not url or "\x00" in url
            or not isinstance(pin, str) or PIN_RE.fullmatch(pin) is None):
        raise RuntimeError("shared policy masstree url/pin is invalid")
    return url, pin


def _git_environment() -> dict[str, str]:
    environment = {
        key: value for key, value in os.environ.items()
        if not key.startswith("GIT_")
    }
    environment.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
    })
    return environment


def _run_git(*args: str, cwd: Path | None = None) -> str:
    process = subprocess.run(
        ["git", *args], cwd=str(cwd) if cwd is not None else None,
        env=_git_environment(), capture_output=True, text=True,
    )
    if process.returncode != 0:
        detail = process.stderr.strip() or process.stdout.strip()
        raise RuntimeError(
            f"git command failed ({process.returncode}): {' '.join(args)}"
            + (f": {detail}" if detail else "")
        )
    return process.stdout


def _verify_pinned_clean(source_dir: Path, pin: str) -> None:
    if source_dir.is_symlink() or not source_dir.is_dir():
        raise RuntimeError(f"masstree source is not a real directory: {source_dir}")
    resolved = source_dir.resolve(strict=True)
    if source_dir.absolute() != resolved:
        raise RuntimeError(f"masstree source is not a canonical path: {source_dir}")
    head = _run_git(
        "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
        "-c", "core.useReplaceRefs=false", "-C", str(source_dir),
        "rev-parse", "--verify", "HEAD",
    ).strip()
    status = _run_git(
        "-c", "core.fsmonitor=", "-c", "core.hooksPath=",
        "-c", "core.useReplaceRefs=false", "-C", str(source_dir),
        "status", "--porcelain=v1", "--untracked-files=all",
        "--ignored=matching", "--ignore-submodules=none",
    )
    if head != pin or status:
        raise RuntimeError(
            "masstree source is not pinned-clean: "
            f"head={head!r} expected={pin!r} status={status!r}"
        )


def _prepare_source(
        source_dir: Path | None, *, url: str, pin: str, work_dir: Path,
) -> Path:
    clone_source = url
    if source_dir is not None:
        candidate = source_dir.expanduser().absolute()
        _verify_pinned_clean(candidate, pin)
        clone_source = str(candidate)

    clone_dir = work_dir / "masstree-src"
    _run_git(
        "clone", "--no-hardlinks", "--no-checkout", clone_source,
        str(clone_dir),
    )
    _run_git("-C", str(clone_dir), "checkout", "--detach", pin)
    _verify_pinned_clean(clone_dir, pin)
    return clone_dir


def _sha256_file(path: Path) -> str:
    try:
        info = path.lstat()
    except OSError as exc:
        raise RuntimeError(f"masstree artifact is unavailable: {path}") from exc
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f"masstree artifact is not a regular file: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    del info
    value = digest.hexdigest()
    if HASH_RE.fullmatch(value) is None:
        raise RuntimeError(f"cannot calculate sha256: {path}")
    return value


def _configure_and_hash(source_dir: Path) -> str:
    """Run only masstree bootstrap/configure in the temporary clone."""
    bootstrap = source_dir / "bootstrap.sh"
    if bootstrap.is_symlink() or not bootstrap.is_file():
        raise RuntimeError(f"masstree bootstrap script is unavailable: {bootstrap}")

    subprocess.run(["./bootstrap.sh"], cwd=str(source_dir), check=True)
    subprocess.run(
        ["./configure", "--disable-assertions"],
        cwd=str(source_dir), check=True,
    )
    return _sha256_file(source_dir / "config.h")


def _write_policy(path: Path, *, pin: str, config_sha256: str) -> None:
    if HASH_RE.fullmatch(config_sha256) is None:
        raise RuntimeError("generated artifact hash is invalid")
    document = {
        "schema_version": SCHEMA_VERSION,
        "name": SOURCE_NAME,
        "pin": pin,
        "config_sha256": config_sha256,
    }
    path = path.expanduser().absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", dir=path.parent,
                prefix=f".{path.name}.", suffix=".tmp", delete=False) as handle:
            temporary = Path(handle.name)
            json.dump(document, handle, ensure_ascii=False, sort_keys=True, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        temporary = None
    finally:
        if temporary is not None:
            try:
                temporary.unlink()
            except FileNotFoundError:
                pass


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="generate the independent floor masstree config policy",
    )
    parser.add_argument(
        "--source-dir", type=Path, default=None,
        help="pinned, clean masstree checkout; omit to clone the shared policy pin",
    )
    parser.add_argument(
        "--output", type=Path, default=_default_output_path(),
        help="output JSON path (default: tools/pegasus/policies/floor_masstree_payload_v1.json)",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="allow replacing an existing output JSON file",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        output_path = args.output.expanduser().absolute()
        if os.path.lexists(output_path) and not args.force:
            raise RuntimeError(
                f"output already exists (use --force to replace): {output_path}"
            )
        url, pin = _load_policy(_policy_path())
        with tempfile.TemporaryDirectory(prefix="izanagi-floor-masstree-policy-") as temporary:
            work_dir = Path(temporary)
            source_dir = _prepare_source(
                args.source_dir, url=url, pin=pin, work_dir=work_dir,
            )
            config_sha256 = _configure_and_hash(source_dir)
        _write_policy(
            output_path, pin=pin, config_sha256=config_sha256,
        )
    except (OSError, RuntimeError, subprocess.SubprocessError, ValueError) as exc:
        print(f"generate_floor_masstree_payload_policy: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
