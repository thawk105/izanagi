#!/usr/bin/env python3
"""Run a tested-main scoped plan through the existing launcher protocol."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import types


SCHEMA = "dev-wave-scoped-acceptance-receipt/v1"


def _git_blob(repo: Path, revision: str, path: str) -> bytes:
    if re.fullmatch(r"[0-9a-f]{40}", revision) is None:
        raise ValueError("invalid revision")
    result = subprocess.run(
        ["git", "-c", "core.hooksPath=/dev/null", "-c", "credential.helper=",
         "-C", str(repo), "cat-file", "blob", f"{revision}:{path}"],
        capture_output=True,
        env={**os.environ, "GIT_NO_REPLACE_OBJECTS": "1",
             "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull},
    )
    if result.returncode:
        raise ValueError(f"missing tested-main blob: {path}")
    return result.stdout


def _module(name: str, source: bytes, path: str):
    module = types.ModuleType(name)
    module.__file__ = path
    sys.modules[name] = module
    exec(compile(source, path, "exec"), module.__dict__)
    return module


def _load_plan(repo: Path, tested_main: str, tested_tip: str):
    source = _git_blob(repo, tested_main, "tools/scoped_acceptance.py")
    selector = _module("_tested_main_scoped_selector", source,
                       str(repo / "tools/scoped_acceptance.py"))
    result = selector.plan(repo, tested_main, tested_tip)
    if not result["classification"]["eligible"] or not result["selection"]["eligible"]:
        raise ValueError("tip is not eligible for scoped acceptance")
    return result, source


def _gate(repo: Path, argv: list[str], index: int) -> dict:
    result = subprocess.run(argv, cwd=repo, capture_output=True)
    digest = hashlib.sha256(result.stdout + result.stderr).hexdigest()
    if result.returncode:
        raise ValueError(f"direct gate {index} failed with rc={result.returncode}")
    return {"argv": argv, "rc": 0, "log_sha256": digest}


def main(argv=None) -> int:
    # v5 parses the common protocol fields. Its code is loaded from the
    # tested-main blob, while this file is independently bound by the waiter.
    raw = list(sys.argv[1:] if argv is None else argv)
    def value(flag):
        at = raw.index(flag)
        return raw[at + 1]
    try:
        repo = Path(value("--repo-root"))
        if not repo.is_absolute() or repo.resolve() != repo:
            raise ValueError("repo must be canonical absolute path")
        tested_main = value("--tested-main")
        tested_tip = value("--tested-tip")
        plan, selector_source = _load_plan(repo, tested_main, tested_tip)
        base_source = _git_blob(repo, tested_main, "tools/acceptance_launcher.py")
        base = _module("_tested_main_acceptance_launcher", base_source,
                       str(repo / "tools/acceptance_launcher.py"))
        config, runner_argv = base._parse_args(raw)
        targets = sorted(set(
            list(plan["selection"]["files"])
            + ["orchestrator/tests/" + node for node in plan["selection"]["nodes"]]
        ))
        if not targets:
            raise ValueError("empty scoped test selection")
        target_json = json.dumps(targets, ensure_ascii=False, separators=(",", ":"))
        marker = hashlib.sha256(target_json.encode()).hexdigest()
        bootstrap = base._RUNNER_BOOTSTRAP
        needle = "namespace['main'](sys.argv[2:])"
        if bootstrap.count(needle) != 1:
            raise ValueError("runner bootstrap changed")
        base._RUNNER_BOOTSTRAP = bootstrap.replace(needle, f"namespace['main']({targets!r})")
        original_run = base._run_blob
        original_receipt = base._receipt_bytes
        gate_results = []

        def run_blob(source, path, log_file, *, environment, pass_fds):
            for index, gate_argv in enumerate(plan["selection"]["direct_gates"]):
                gate_results.append(_gate(repo, gate_argv, index))
            scoped_env = dict(environment)
            scoped_env["IZANAGI_SCOPED_ACCEPTANCE_TARGETS_SHA256"] = marker
            scoped_env["IZANAGI_ACCEPTANCE_SHARDS"] = "1"
            return original_run(source, path, log_file,
                                environment=scoped_env, pass_fds=pass_fds)

        def receipt_bytes(*args):
            payload = json.loads(original_receipt(*args))
            payload.update({"schema_version": SCHEMA,
                            "authority_kind": "dev-wave-scoped-acceptance-launcher",
                            "classification": plan["classification"],
                            "selection": plan["selection"],
                            "direct_gate_results": gate_results,
                            "selector_blob_sha": subprocess.check_output(
                                ["git", "-C", str(repo), "rev-parse",
                                 f"{tested_main}:tools/scoped_acceptance.py"],
                                text=True).strip(),
                            "selector_executed_sha256": hashlib.sha256(selector_source).hexdigest()})
            return base._canonical_json_bytes(payload)

        base._receipt_bytes = receipt_bytes
        os.environ["IZANAGI_ACCEPTANCE_SHARDS"] = "1"
        base._launch(config, runner_argv, blob_runner=run_blob)
    except (ValueError, OSError, IndexError, subprocess.SubprocessError) as exc:
        print(f"scoped acceptance launcher: {exc}", file=sys.stderr, flush=True)
        return 70
    except Exception as exc:
        print(f"scoped acceptance launcher: {type(exc).__name__}: {exc}",
              file=sys.stderr, flush=True)
        return 70
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
