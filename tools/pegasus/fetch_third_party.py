#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Pegasus third-party source を永続 cache へ取得し、offline 配置する。"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from types import ModuleType
from typing import Any, Mapping, Sequence


SCHEMA_VERSION = "pegasus-thirdparty-fetch/v1"
CACHE_ENV = "IZANAGI_PEGASUS_THIRDPARTY_CACHE"
_CODE_ROOT = Path(__file__).resolve().parents[2]
_ORCHESTRATOR_ROOT = _CODE_ROOT / "orchestrator"
_GIT_OPTIONS = (
    "-c", "core.fsmonitor=",
    "-c", "core.hooksPath=/dev/null",
    "-c", "core.useReplaceRefs=false",
    "-c", "protocol.version=2",
)
_CONFIG_SECTION_RE = re.compile(
    r'^\[\s*([A-Za-z][A-Za-z0-9.-]*)(?:\s+"(?:[^"\\]|\\.)*")?\s*\]'
    r'\s*(?:[#;].*)?$'
)
_CONFIG_KEY_RE = re.compile(r"^([A-Za-z][A-Za-z0-9-]*)\s*(?:=.*)?$")
_TRUE_VALUES = frozenset({"true", "yes", "on", "1"})
_FALSE_VALUES = frozenset({"false", "no", "off", "0"})


class SourceVerificationError(RuntimeError):
    """Source が pinned-clean / hardened contract を満たさない。"""


class OperationalError(RuntimeError):
    """引数、policy、Git 起動、取得、publish の運用失敗。"""


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        raise OperationalError(message)


def _driver_module() -> ModuleType:
    """driver の両 import root を一時挿入し、元の sys.path を復元する。"""
    original_sys_path = list(sys.path)
    for root in (_CODE_ROOT, _ORCHESTRATOR_ROOT):
        value = str(root)
        if value not in sys.path:
            sys.path.insert(0, value)
    try:
        from orchestrator.campaign import silo_ladder_rung1

        return silo_ladder_rung1
    finally:
        sys.path[:] = original_sys_path


def _build_dependency_sources(document: Mapping[str, Any]) -> tuple[dict[str, str], ...]:
    """find_package で使う gflags / glog の調達記述を列挙する。"""
    sources = tuple(
        {
            "name": name,
            "source_name": name,
            "url": document[f"{name}_source_url"],
            "pin": document[f"{name}_expected_head"],
        }
        for name in ("gflags", "glog")
    )
    keys = {"name", "source_name", "url", "pin"}
    if (
        any(set(item) != keys for item in sources)
        or any(type(item[key]) is not str or not item[key]
               for item in sources for key in keys)
        or any(item["source_name"] != item["name"] for item in sources)
        or any(not item["url"].startswith("https://github.com/")
               or not item["url"].endswith(".git") for item in sources)
        or any(re.fullmatch(r"[0-9a-f]{40}", item["pin"]) is None
               for item in sources)
    ):
        raise OperationalError("build dependency source policy is invalid")
    return sources


def _load_policy(
    repo_root: Path,
) -> tuple[tuple[dict[str, str], ...], tuple[dict[str, str], ...], Path]:
    """FetchContent の同期検査に、find_package の 2 依存を加える。"""
    driver = _driver_module()
    try:
        sources = driver.third_party_policy(repo_root)
        document = driver._load_json(repo_root / "tools/pegasus/policy.json")
        dependencies = _build_dependency_sources(document)
        driver._dependency_pins(repo_root)
        staging_relative = Path(driver.THIRD_PARTY_STAGING_RELATIVE)
    except Exception as exc:
        raise OperationalError(f"policy validation failed: {exc}") from exc
    return tuple(dict(item) for item in sources), dependencies, staging_relative


def _resolve_repo_root(value: Path) -> Path:
    try:
        root = value.resolve(strict=True)
    except OSError as exc:
        raise OperationalError(f"repo root cannot be resolved: {value}: {exc}") from exc
    if not root.is_dir():
        raise OperationalError(f"repo root is not a directory: {root}")
    return root


def _resolve_cache_root(value: Path | None, repo_root: Path) -> Path:
    configured = value
    if configured is None:
        raw = os.environ.get(CACHE_ENV)
        configured = Path(raw) if raw else None
    if configured is None:
        raise OperationalError(
            f"cache root is required via --cache-root or {CACHE_ENV}"
        )
    if not configured.is_absolute():
        raise OperationalError("cache root must be an absolute path")
    try:
        cache_root = configured.resolve(strict=False)
    except OSError as exc:
        raise OperationalError(f"cache root cannot be resolved: {configured}: {exc}") from exc
    try:
        inside_repo = os.path.commonpath((str(cache_root), str(repo_root))) == str(repo_root)
    except ValueError as exc:
        raise OperationalError(f"cache root comparison failed: {exc}") from exc
    if inside_repo:
        raise OperationalError("cache root must be outside the repository")
    return cache_root


def _resolve_staging_root(
    value: Path | None,
    repo_root: Path,
    cache_root: Path,
    staging_relative: Path,
) -> Path:
    if value is None:
        configured = repo_root / staging_relative
    else:
        if not value.is_absolute():
            raise OperationalError("staging root must be an absolute path")
        configured = value
    try:
        staging_root = configured.resolve(strict=False)
    except OSError as exc:
        raise OperationalError(
            f"staging root cannot be resolved: {configured}: {exc}"
        ) from exc
    try:
        common = Path(os.path.commonpath((str(staging_root), str(cache_root))))
    except ValueError as exc:
        raise OperationalError(f"staging/cache root comparison failed: {exc}") from exc
    if common in (staging_root, cache_root):
        raise OperationalError("staging root and cache root must not overlap")
    return staging_root


def _git_environment(protocol: str) -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.pop("SSH_ASKPASS", None)
    env.update(
        {
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": os.devnull,
            "GIT_NO_LAZY_FETCH": "1",
            "GIT_TERMINAL_PROMPT": "0",
            "GIT_ALLOW_PROTOCOL": protocol,
        }
    )
    return env


def _git(
    args: Sequence[str], *, protocol: str, check: bool = True,
) -> subprocess.CompletedProcess[str]:
    command = ["git", *_GIT_OPTIONS, *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="strict",
            env=_git_environment(protocol),
        )
    except (OSError, UnicodeError) as exc:
        raise OperationalError(f"git could not run: {args[0]}: {exc}") from exc
    if check and completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git failed"
        raise OperationalError(f"git {args[0]} failed: {detail}")
    return completed


def _without_unquoted_comment(line: str) -> str:
    quoted = False
    escaped = False
    for index, character in enumerate(line):
        if escaped:
            escaped = False
            continue
        if character == "\\":
            escaped = True
            continue
        if character == '"':
            quoted = not quoted
        elif character in "#;" and not quoted:
            return line[:index]
    return line


def _has_continuation(line: str) -> bool:
    body = _without_unquoted_comment(line).rstrip()
    trailing = len(body) - len(body.rstrip("\\"))
    return trailing % 2 == 1


def _config_entries(config_path: Path) -> list[tuple[str, str, str]]:
    try:
        text = config_path.read_text(encoding="utf-8", errors="strict")
    except (OSError, UnicodeError) as exc:
        raise SourceVerificationError(
            f"cannot read Git config as text: {config_path}: {exc}"
        ) from exc
    section = ""
    entries: list[tuple[str, str, str]] = []
    for number, raw_line in enumerate(text.splitlines(), 1):
        line = raw_line.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if _has_continuation(raw_line):
            raise SourceVerificationError(
                f"Git config continuation is forbidden: {config_path}:{number}"
            )
        match = _CONFIG_SECTION_RE.fullmatch(line)
        if match:
            section_name = match.group(1)
            if "." in section_name:
                raise SourceVerificationError(
                    f"legacy dotted Git config section is forbidden: "
                    f"{config_path}:{number}"
                )
            section = section_name.lower()
            continue
        content = _without_unquoted_comment(raw_line).strip()
        match = _CONFIG_KEY_RE.fullmatch(content)
        if not match or not section:
            raise SourceVerificationError(
                f"Git config is not safely parseable as text: {config_path}:{number}"
            )
        key = match.group(1).lower()
        value = (
            content.split("=", 1)[1].strip().lower()
            if "=" in content else "true"
        )
        entries.append((section, key, value))
    return entries


def _inspect_cache_config(config_path: Path) -> None:
    entries = _config_entries(config_path)
    for section, key, value in entries:
        dangerous = (
            (section == "core" and key in {"fsmonitor", "sshcommand", "hookspath"})
            or section == "filter"
            or section in {"include", "includeif"}
            or (section == "url" and key == "insteadof")
            or (section == "remote" and key in {"uploadpack", "receivepack"})
        )
        if dangerous:
            raise SourceVerificationError(
                f"dangerous Git config key is forbidden: {section}.{key}"
            )
        if (
            section == "remote" and key == "promisor"
        ) or (
            section == "extensions" and key == "partialclone"
        ):
            raise SourceVerificationError(
                f"partial/promisor repository is forbidden: {section}.{key}"
            )
        if section == "extensions" and key == "worktreeconfig":
            raise SourceVerificationError("worktree Git config is forbidden")
        if section == "core" and key == "sparsecheckout":
            normalized = value.strip()
            if (
                len(normalized) >= 2
                and normalized[0] == normalized[-1]
                and normalized[0] in {'"', "'"}
            ):
                normalized = normalized[1:-1].strip()
            if normalized in _TRUE_VALUES or normalized not in _FALSE_VALUES:
                raise SourceVerificationError("sparse checkout is forbidden")


def _lexists(path: Path) -> bool:
    return os.path.lexists(os.fspath(path))


def _require_real_directory(path: Path, name: str) -> Path:
    if not _lexists(path):
        raise SourceVerificationError(f"source is absent: {name}")
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise SourceVerificationError(f"source cannot be inspected: {name}: {exc}") from exc
    if not stat.S_ISDIR(mode):
        raise SourceVerificationError(f"source is not a real directory: {name}")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise SourceVerificationError(f"source cannot be resolved: {name}: {exc}") from exc


def _metadata_path_exists(path: Path) -> bool:
    try:
        return _lexists(path)
    except OSError as exc:
        raise SourceVerificationError(f"Git metadata cannot be inspected: {path}: {exc}") from exc


def _inspect_hardened_metadata(
    source: Path, name: str, *, allow_shallow: bool,
) -> None:
    git_dir = source / ".git"
    try:
        mode = git_dir.lstat().st_mode
    except OSError as exc:
        raise SourceVerificationError(f".git is absent or unreadable: {name}: {exc}") from exc
    if not stat.S_ISDIR(mode):
        raise SourceVerificationError(f".git must be a real directory: {name}")
    for relative, label in (
        (Path("commondir"), "commondir"),
        (Path("config.worktree"), "worktree Git config"),
    ):
        if _metadata_path_exists(git_dir / relative):
            raise SourceVerificationError(f"{label} is forbidden: {name}")
    _inspect_cache_config(git_dir / "config")
    for relative, label in (
        (Path("objects/info/alternates"), "alternates"),
        (Path("info/grafts"), "grafts"),
        (Path("info/sparse-checkout"), "sparse checkout"),
    ):
        if _metadata_path_exists(git_dir / relative):
            raise SourceVerificationError(f"{label} is forbidden: {name}")
    if not allow_shallow and _metadata_path_exists(git_dir / "shallow"):
        raise SourceVerificationError(f"shallow repository is forbidden: {name}")


def _source_git(
    source: Path, args: Sequence[str], *, protocol: str = "file",
) -> subprocess.CompletedProcess[str]:
    completed = _git(["-C", str(source), *args], protocol=protocol, check=False)
    if completed.returncode != 0:
        detail = completed.stderr.strip() or completed.stdout.strip() or "git failed"
        raise SourceVerificationError(
            f"Git source inspection failed: {args[0]}: {detail}"
        )
    return completed


def _verify_source(
    path: Path,
    *,
    name: str,
    pin: str,
    expected_url: str | None,
    allow_shallow: bool = False,
    reject_ignored: bool = False,
    protocol: str = "file",
) -> dict[str, str]:
    source = _require_real_directory(path, name)
    _inspect_hardened_metadata(source, name, allow_shallow=allow_shallow)
    replace_refs = _source_git(
        source,
        ["for-each-ref", "--format=%(refname)", "refs/replace/"],
        protocol=protocol,
    ).stdout
    if replace_refs:
        raise SourceVerificationError(f"replace refs are forbidden: {name}")
    top = _source_git(
        source, ["rev-parse", "--show-toplevel"], protocol=protocol
    ).stdout.strip()
    try:
        top_path = Path(top).resolve(strict=True)
    except OSError as exc:
        raise SourceVerificationError(
            f"repository root cannot be resolved: {name}: {exc}"
        ) from exc
    if top_path != source:
        raise SourceVerificationError(f"repository root mismatch: {name}")
    head = _source_git(
        source, ["rev-parse", "--verify", "HEAD"], protocol=protocol
    ).stdout.strip()
    if head != pin:
        raise SourceVerificationError(f"HEAD does not match policy pin: {name}")
    status_result = _source_git(
        source,
        ["status", "--porcelain", "--untracked-files=all"],
        protocol=protocol,
    )
    if status_result.stdout:
        raise SourceVerificationError(f"source is not clean: {name}")
    if reject_ignored:
        ignored = _source_git(
            source,
            ["ls-files", "--others", "--ignored", "--exclude-standard", "-z"],
            protocol=protocol,
        ).stdout
        if ignored:
            raise SourceVerificationError(
                f"ignored artifacts are forbidden in hydrated source: {name}"
            )
    index = _source_git(
        source, ["ls-files", "-v", "-z"], protocol=protocol
    ).stdout
    tags = (entry[0] for entry in index.split("\0") if entry)
    if any(tag == "S" or tag.islower() for tag in tags):
        raise SourceVerificationError(
            f"assume-unchanged/skip-worktree index bit is forbidden: {name}"
        )
    if expected_url is not None:
        origins = _source_git(
            source,
            ["config", "--local", "--get-all", "remote.origin.url"],
            protocol=protocol,
        ).stdout.splitlines()
        if origins != [expected_url]:
            raise SourceVerificationError(f"origin URL does not match policy: {name}")
    return {
        "name": name,
        "pin": pin,
        "resolved_path": str(source),
        "head": head,
    }


def _path_identity(path: Path) -> tuple[int, int]:
    status = path.lstat()
    return status.st_dev, status.st_ino


def _remove_empty_reservation(
    destination: Path, reservation_identity: tuple[int, int],
) -> None:
    try:
        if _path_identity(destination) != reservation_identity:
            return
        if any(destination.iterdir()):
            return
        if _path_identity(destination) != reservation_identity:
            return
        os.rmdir(destination)
    except OSError:
        return


def _rollback_published_source(
    stage: Path, destination: Path, published_identity: tuple[int, int],
) -> None:
    try:
        if _lexists(stage) or _path_identity(destination) != published_identity:
            return
        os.rename(destination, stage)
    except OSError:
        return


def _publish_create_only(stage: Path, destination: Path) -> tuple[int, int]:
    try:
        os.mkdir(destination)
    except FileExistsError as exc:
        raise OperationalError(f"publish destination already exists: {destination}") from exc
    except OSError as exc:
        raise OperationalError(f"publish reservation failed: {destination}: {exc}") from exc
    try:
        reservation_identity = _path_identity(destination)
    except OSError as exc:
        raise OperationalError(
            f"publish reservation cannot be inspected: {destination}: {exc}"
        ) from exc
    try:
        published_identity = _path_identity(stage)
    except OSError as exc:
        _remove_empty_reservation(destination, reservation_identity)
        raise OperationalError(
            f"publish source cannot be inspected: {stage}: {exc}"
        ) from exc
    try:
        os.rename(stage, destination)
    except OSError as exc:
        _remove_empty_reservation(destination, reservation_identity)
        raise OperationalError(f"publish rename failed: {destination}: {exc}") from exc
    return published_identity


def _make_stage(parent: Path, name: str) -> tuple[Path, Path]:
    try:
        stage_parent = Path(tempfile.mkdtemp(prefix=f".{name}.", dir=parent))
    except OSError as exc:
        raise OperationalError(f"cannot create stage for {name}: {exc}") from exc
    return stage_parent, stage_parent / "repo"


def _checkout_stage(
    clone_args: Sequence[str], stage: Path, pin: str, *, protocol: str,
) -> None:
    _git(["clone", *clone_args, str(stage)], protocol=protocol)
    _git(["-C", str(stage), "checkout", "--detach", pin], protocol=protocol)


def _ensure_root(root: Path, *, create: bool, label: str) -> None:
    if _lexists(root):
        try:
            mode = root.lstat().st_mode
        except OSError as exc:
            raise OperationalError(f"{label} cannot be inspected: {root}: {exc}") from exc
        if not stat.S_ISDIR(mode):
            raise OperationalError(f"{label} is not a real directory: {root}")
        return
    if not create:
        raise SourceVerificationError(f"{label} is absent: {root}")
    try:
        root.mkdir(parents=True, exist_ok=False)
    except OSError as exc:
        raise OperationalError(f"cannot create {label}: {root}: {exc}") from exc


def _verify_cache(
    cache_root: Path, sources: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    _ensure_root(cache_root, create=False, label="cache root")
    return [
        _verify_source(
            cache_root / item["source_name"],
            name=item["name"],
            pin=item["pin"],
            expected_url=item["url"],
        )
        for item in sources
    ]


def _fetch(
    cache_root: Path, sources: Sequence[Mapping[str, str]],
) -> list[dict[str, str]]:
    if _lexists(cache_root):
        _ensure_root(cache_root, create=False, label="cache root")
    for item in sources:
        destination = cache_root / item["source_name"]
        if _lexists(destination):
            _verify_source(
                destination,
                name=item["name"],
                pin=item["pin"],
                expected_url=item["url"],
                protocol="https",
            )
    _ensure_root(cache_root, create=True, label="cache root")
    records: list[dict[str, str]] = []
    for item in sources:
        destination = cache_root / item["source_name"]
        if _lexists(destination):
            records.append(
                _verify_source(
                    destination,
                    name=item["name"],
                    pin=item["pin"],
                    expected_url=item["url"],
                    protocol="https",
                )
            )
            continue
        stage_parent, stage = _make_stage(cache_root, item["source_name"])
        try:
            _checkout_stage(
                ["--no-checkout", "--", item["url"]],
                stage,
                item["pin"],
                protocol="https",
            )
            _verify_source(
                stage,
                name=item["name"],
                pin=item["pin"],
                expected_url=item["url"],
                protocol="https",
            )
            published_identity = _publish_create_only(stage, destination)
            try:
                record = _verify_source(
                    destination,
                    name=item["name"],
                    pin=item["pin"],
                    expected_url=item["url"],
                    protocol="https",
                )
            except Exception:
                _rollback_published_source(
                    stage, destination, published_identity
                )
                raise
            records.append(record)
        finally:
            shutil.rmtree(stage_parent, ignore_errors=True)
    return records


def _hydrate(
    repo_root: Path,
    cache_root: Path,
    sources: Sequence[Mapping[str, str]],
    staging_relative: Path,
    *,
    staging_root: Path | None = None,
) -> list[dict[str, str]]:
    _verify_cache(cache_root, sources)
    if staging_root is None:
        staging_root = repo_root / staging_relative
    if _lexists(staging_root):
        _ensure_root(staging_root, create=False, label="hydrate root")
        for item in sources:
            destination = staging_root / item["source_name"]
            if _lexists(destination):
                _verify_source(
                    destination,
                    name=item["name"],
                    pin=item["pin"],
                    expected_url=str((cache_root / item["source_name"]).resolve()),
                    reject_ignored=True,
                )
    _ensure_root(staging_root, create=True, label="hydrate root")
    for item in sources:
        destination = staging_root / item["source_name"]
        if _lexists(destination):
            continue
        cache_source = (cache_root / item["source_name"]).resolve(strict=True)
        stage_parent, stage = _make_stage(staging_root, item["source_name"])
        try:
            _checkout_stage(
                ["--no-hardlinks", "--no-checkout", "--", str(cache_source)],
                stage,
                item["pin"],
                protocol="file",
            )
            _verify_source(
                cache_source,
                name=item["name"],
                pin=item["pin"],
                expected_url=item["url"],
            )
            _verify_source(
                stage,
                name=item["name"],
                pin=item["pin"],
                expected_url=str(cache_source),
            )
            published_identity = _publish_create_only(stage, destination)
            try:
                _verify_source(
                    destination,
                    name=item["name"],
                    pin=item["pin"],
                    expected_url=str(cache_source),
                    reject_ignored=True,
                )
            except Exception:
                _rollback_published_source(
                    stage, destination, published_identity
                )
                raise
        finally:
            shutil.rmtree(stage_parent, ignore_errors=True)
    return [
        _verify_source(
            staging_root / item["source_name"],
            name=item["name"],
            pin=item["pin"],
            expected_url=str((cache_root / item["source_name"]).resolve()),
            reject_ignored=True,
        )
        for item in sources
    ]


def _parser() -> argparse.ArgumentParser:
    parser = _ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(
        dest="operation", required=True, parser_class=_ArgumentParser
    )
    for operation in ("fetch", "hydrate", "verify"):
        command = subparsers.add_parser(operation)
        command.add_argument(
            "--repo-root", type=Path, default=_CODE_ROOT,
            help="policy/CMake を読む repository root",
        )
        command.add_argument("--cache-root", type=Path)
        if operation == "hydrate":
            command.add_argument(
                "--staging-root",
                type=Path,
                help="hydrate destination (default: the established repository staging root)",
            )
    return parser


def _failure_line(exc: BaseException) -> str:
    message = " ".join(str(exc).splitlines()).strip() or type(exc).__name__
    return f"fetch_third_party: {message}"


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = _parser().parse_args(argv)
        repo_root = _resolve_repo_root(args.repo_root)
        sources, dependencies, staging_relative = _load_policy(repo_root)
        sources += dependencies
        cache_root = _resolve_cache_root(args.cache_root, repo_root)
        staging_root = None
        if args.operation == "hydrate":
            staging_root = _resolve_staging_root(
                args.staging_root,
                repo_root,
                cache_root,
                staging_relative,
            )
        if args.operation == "fetch":
            records = _fetch(cache_root, sources)
        elif args.operation == "hydrate":
            assert staging_root is not None
            records = _hydrate(
                repo_root,
                cache_root,
                sources,
                staging_relative,
                staging_root=staging_root,
            )
        else:
            records = _verify_cache(cache_root, sources)
        payload = {
            "schema_version": SCHEMA_VERSION,
            "operation": args.operation,
            "cache_root": str(cache_root),
            "sources": records,
        }
        if args.operation == "hydrate":
            assert staging_root is not None
            payload["source_root"] = str(staging_root)
        json.dump(payload, sys.stdout, ensure_ascii=False, sort_keys=True)
        sys.stdout.write("\n")
        return 0
    except SourceVerificationError as exc:
        print(_failure_line(exc), file=sys.stderr)
        return 1
    except OperationalError as exc:
        print(_failure_line(exc), file=sys.stderr)
        return 2
    except Exception as exc:
        print(_failure_line(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
