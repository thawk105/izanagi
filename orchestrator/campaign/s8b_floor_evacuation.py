"""Cumulative evacuation of an official floor namespace after wrapper exit.

References record hashes, not saved payload. Direct filesystem replacement of
the fixed bundle is outside this transfer's integrity guarantees.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import tempfile

from .s8b_launch_cert import LaunchCertError, parse_official_run_path

SCHEMA = "s8b-floor-evacuation/v1"


class FloorEvacuationError(RuntimeError):
    """A transfer could not preserve the complete namespace."""


def _namespace(env_tag):
    if not isinstance(env_tag, str) or not re.fullmatch(r"[a-z0-9][a-z0-9._-]*", env_tag):
        raise FloorEvacuationError("invalid env_tag")
    return f"output/env/{env_tag}/calibration/s8b-floor-official"


def _safe(path):
    for part in (path, *path.parents):
        if part.is_symlink():
            raise FloorEvacuationError(f"symlink: {part}")


def bundle_root(repo_root, *, env_tag) -> Path:
    """Derive the sole bundle location; no argument or environment override."""
    _namespace(env_tag)
    root = Path(repo_root).resolve()
    env = os.environ.copy()
    # Derive from root's Git metadata, never the caller's repository selection
    # or injected configuration/discovery settings. No configurable override.
    for key in ("GIT_DIR", "GIT_COMMON_DIR", "GIT_WORK_TREE",
                "GIT_IMPLICIT_WORK_TREE", "GIT_CEILING_DIRECTORIES",
                "GIT_DISCOVERY_ACROSS_FILESYSTEM", "GIT_CONFIG",
                "GIT_CONFIG_SYSTEM", "GIT_CONFIG_GLOBAL", "GIT_CONFIG_NOSYSTEM",
                "GIT_CONFIG_PARAMETERS", "GIT_CONFIG_COUNT"):
        env.pop(key, None)
    try:
        raw = subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "--git-common-dir"],
            stderr=subprocess.PIPE, text=True, env=env).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise FloorEvacuationError("git common directory unavailable") from exc
    common = Path(raw)
    if not common.is_absolute():
        common = root / common
    return common.resolve() / "izanagi/s8b-floor-evacuation" / env_tag


def _inventory(base):
    """Read only ordinary files/directories, including empty directories."""
    _safe(base)
    dirs, files = [], {}

    def visit(path):
        mode = path.lstat().st_mode
        rel = path.relative_to(base).as_posix()
        if stat.S_ISDIR(mode):
            if path != base:
                dirs.append(rel)
            for child in sorted(path.iterdir()):
                visit(child)
        elif stat.S_ISREG(mode) and path != base:
            files[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
        else:
            raise FloorEvacuationError(f"not an ordinary file/directory: {path}")

    visit(base)
    return sorted(dirs), files


def _run(rel, env_tag):
    try:
        parsed = parse_official_run_path(rel + "/result.json", expected_basename="result.json")
    except LaunchCertError as exc:
        raise FloorEvacuationError(str(exc)) from exc
    if parsed["env_tag"] != env_tag:
        raise FloorEvacuationError("run env mismatch")
    return {"run_id": parsed["run_id"], "dir": rel, "env_tag": env_tag,
            "proto8": parsed["proto8"], "ts": parsed["ts"].isoformat()}


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise FloorEvacuationError(f"duplicate manifest key/path: {key}")
        result[key] = value
    return result


def _validate(bundle, env_tag):
    _safe(bundle)
    if {p.name for p in bundle.iterdir()} != {"manifest.json", "payload"}:
        raise FloorEvacuationError("unexpected or missing bundle entry")
    manifest_path = bundle / "manifest.json"
    if not stat.S_ISREG(manifest_path.lstat().st_mode):
        raise FloorEvacuationError("manifest is not an ordinary file")
    doc = json.loads(manifest_path.read_bytes(), object_pairs_hook=_pairs)
    namespace = _namespace(env_tag)
    if doc["schema"] != SCHEMA or doc["namespace"] != namespace or doc["env_tag"] != env_tag:
        raise FloorEvacuationError("manifest env/namespace/schema mismatch")
    runs = doc["runs"]
    run_dirs = [run["dir"] for run in runs]
    if len(set(run_dirs)) != len(run_dirs) or any(run != _run(run["dir"], env_tag) for run in runs):
        raise FloorEvacuationError("duplicate or inconsistent run")
    dirs, files = _inventory(bundle / "payload")
    if dirs != sorted(doc["dirs"]) or files != doc["files"]:
        raise FloorEvacuationError("manifest/payload mismatch")
    ancestors = {namespace, *(p.as_posix() for p in Path(namespace).parents if p != Path('.'))}
    for rel in dirs + list(files):
        if rel in dirs and rel in ancestors:
            continue
        if not any(rel == run or rel.startswith(run + "/") for run in run_dirs):
            raise FloorEvacuationError("payload outside declared runs")
    if any(run not in dirs for run in run_dirs):
        raise FloorEvacuationError("missing manifest run")
    return doc


def _references(root, references):
    result = {}
    for raw in references or ():
        path = Path(raw)
        if not path.is_absolute():
            path = root / path
        _safe(path)
        mode = path.lstat().st_mode
        if stat.S_ISDIR(mode):
            _, files = _inventory(path)
            result[str(raw)] = {"type": "directory", "files": files}
        elif stat.S_ISREG(mode):
            result[str(raw)] = {"type": "file", "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
        else:
            raise FloorEvacuationError("reference is not an ordinary file/directory")
    return result


def evacuate(*, root, env_tag, references=None) -> dict:
    """Save all runs before removing any source bytes; accumulate across calls."""
    try:
        root = Path(root).resolve()
        namespace = _namespace(env_tag)
        source = root / namespace
        _safe(source)
        bundle = bundle_root(root, env_tag=env_tag)
        _safe(bundle)
        old = _validate(bundle, env_tag) if bundle.exists() else None
        entries = sorted(source.iterdir()) if source.exists() else []
        runs = [_run(p.relative_to(root).as_posix(), env_tag) for p in entries]
        snapshots = {entry.name: _inventory(entry) for entry in entries}
        refs = dict(old["references"]) if old else {}
        refs.update(_references(root, references))
        bundle.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".evacuate-", dir=bundle.parent) as tmp:
            stage = Path(tmp) / "bundle"
            if old:
                shutil.copytree(bundle, stage)
                _validate(stage, env_tag)
            else:
                (stage / "payload").mkdir(parents=True)
            all_runs = {run["dir"]: run for run in old["runs"]} if old else {}
            for entry, run in zip(entries, runs):
                dest = stage / "payload" / run["dir"]
                if dest.exists():
                    if _inventory(dest) != snapshots[entry.name]:
                        raise FloorEvacuationError("existing run has different bytes/paths")
                else:
                    shutil.copytree(entry, dest)
                if _inventory(dest) != snapshots[entry.name]:
                    raise FloorEvacuationError("copied paths/sha256 mismatch")
                all_runs[run["dir"]] = run
            dirs, files = _inventory(stage / "payload")
            doc = {"schema": SCHEMA, "namespace": namespace, "env_tag": env_tag,
                   "runs": [all_runs[key] for key in sorted(all_runs)],
                   "dirs": dirs, "files": files, "references": refs}
            (stage / "manifest.json").write_text(json.dumps(doc, sort_keys=True, indent=2) + "\n")
            _validate(stage, env_tag)
            backup = None
            if bundle.exists():
                # Never put the only accumulated copy under automatic cleanup.
                backup = Path(tempfile.mkdtemp(prefix=f".{env_tag}-previous-", dir=bundle.parent))
                bundle.rename(backup)
            try:
                stage.rename(bundle)
            except OSError as publish_error:
                if backup is not None:
                    try:
                        backup.rename(bundle)
                    except OSError as rollback_error:
                        raise FloorEvacuationError(
                            f"publication failed: {publish_error}; rollback failed: {rollback_error}; "
                            f"previous bundle retained at {backup}") from rollback_error
                    raise FloorEvacuationError(
                        f"publication failed: {publish_error}; previous bundle restored at {bundle}"
                    ) from publish_error
                raise
            if backup is not None:
                shutil.rmtree(backup)
        # Publication succeeded. Retry may encounter some already removed runs.
        for entry in entries:
            shutil.rmtree(entry)
        if source.exists():
            source.rmdir()
        return doc
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FloorEvacuationError(f"evacuation failed: {exc}") from exc


def restore(*, root, env_tag) -> tuple[str, ...]:
    """Verify and restore every recorded run, retaining the complete bundle."""
    try:
        root = Path(root).resolve()
        bundle = bundle_root(root, env_tag=env_tag)
        doc = _validate(bundle, env_tag)
        dest = root / _namespace(env_tag)
        _safe(dest)
        if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
            raise FloorEvacuationError("destination namespace already contains runs/entries")
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".restore-", dir=dest.parent) as tmp:
            stage = Path(tmp) / "bundle"
            shutil.copytree(bundle, stage)
            _validate(stage, env_tag)
            namespace = stage / "payload" / doc["namespace"]
            namespace.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                dest.rmdir()
            namespace.rename(dest)
        return tuple(run["dir"] for run in doc["runs"])
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise FloorEvacuationError(f"restore failed: {exc}") from exc


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("evacuate", "restore"):
        child = sub.add_parser(command)
        child.add_argument("--repo-root", type=Path, default=Path.cwd())
        child.add_argument("--env-tag", required=True)
    args = parser.parse_args(argv)
    try:
        result = globals()[args.command](root=args.repo_root, env_tag=args.env_tag)
    except FloorEvacuationError as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
