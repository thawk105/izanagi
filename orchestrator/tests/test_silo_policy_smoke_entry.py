"""Smoke entry wiring with real quarantine, effects, grammar and TU compiler."""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from skiputil import Skip
from test_silo_function_policy_template import _cxx, _git, HOLE_BEGIN, HOLE_END
from orchestrator.campaign import silo_policy_coverage as coverage
from orchestrator.campaign.silo_policy_compile import compile_policy
from orchestrator.campaign.silo_policy_grammar import validate_policy


class _BuildReached(Exception):
    """Stop at the first policy build; no benchmark execution is needed."""


@contextmanager
def _checkout(pin_commit, base_dir):
    # The checkout seam is outside the four validators. Use real pinned source
    # in a disposable clone, avoiding worktree metadata in the shared repo.
    with tempfile.TemporaryDirectory(prefix="policy-smoke-source-") as tmp:
        source = Path(tmp) / "ccbench"
        subprocess.run(["git", "clone", "--shared", "--no-checkout",
                        str(ROOT / "external/ccbench"), str(source)],
                       check=True, capture_output=True)
        _git(source, "checkout", "--detach", pin_commit)
        yield str(source)


@contextmanager
def _entry(body, compiler):
    with tempfile.TemporaryDirectory(prefix="policy-smoke-entry-") as tmp:
        root = Path(tmp)
        (root / "patches").symlink_to(ROOT / "patches", target_is_directory=True)
        hand = root / coverage.axis.HAND_POLICY_DIR
        hand.mkdir(parents=True)
        # run_smoke visits stock then abort0. Feed the exact test body through
        # its existing file input; the positive body is static5.cpp unchanged.
        (hand / "abort0.cpp").write_text(body)
        scratch = root / "scratch"
        scratch.mkdir()
        seen = []
        stock_builds = []

        def build(source, build_dir, **kwargs):
            if kwargs["stock"]:
                stock_builds.append(kwargs["trace"])
                return build_dir / "unused", {}
            materialized = (source / coverage.axis.SOURCE_REL).read_bytes()
            policy = materialized.split(HOLE_BEGIN, 1)[1].split(HOLE_END, 1)[0]
            assert policy.endswith(b"\n")
            seen.append(hashlib.sha256(policy[:-1]).hexdigest())
            raise _BuildReached

        # Identity/benchmark work is outside the policy gates. The stock pass
        # needs these seams so the real run_smoke loop reaches its policy arm.
        evidence = SimpleNamespace(src_token=coverage.source_digest.STOCK,
                                   as_receipt=lambda: {})
        with patch.object(coverage, "ROOT", root), \
             patch.object(coverage, "checkout", _checkout), \
             patch.object(coverage, "_build_variant", build), \
             patch.object(coverage, "_run", return_value={"commits": 1}), \
             patch.object(coverage.source_digest, "resolve_evidence", return_value=evidence):
            yield (lambda: coverage.run_smoke(scratch, {"cxx_path": compiler}, {})), seen, stock_builds


def _body():
    return (ROOT / coverage.axis.HAND_POLICY_DIR / "static5.cpp").read_text()


def test_smoke_entry_rejects_grammar_violation_before_build():
    """M-SMOKE-SKIP: C++ accepts this body; policy-C++ rejects its conversion."""
    body = _body().replace("return 5u;", "return true;", 1)
    grammar = validate_policy(body)
    assert grammar.accepted is False and grammar.rule_id == "type.conversion"
    compiler = _cxx()
    with tempfile.TemporaryDirectory() as tmp:
        assert compile_policy(body, compiler=compiler, scratch_dir=tmp).accepted is True
    with _entry(body, compiler) as (run, seen, stock):
        try:
            run()
        except ValueError as exc:
            assert "grammar/compile rejected" in str(exc)
            assert "type.conversion" in str(exc)
        else:
            raise AssertionError("invalid policy passed smoke entry")
        assert seen == []
        assert stock == [1, 0]


def test_smoke_entry_builds_checked_body_once_with_matching_sha256():
    body = _body()
    with _entry(body, _cxx()) as (run, seen, stock):
        try:
            run()
        except _BuildReached:
            pass
        else:
            raise AssertionError("legal policy did not reach its first build")
        assert seen == [hashlib.sha256(body.encode()).hexdigest()]
        assert stock == [1, 0]


def test_smoke_entry_rejects_unavailable_compiler_before_build():
    with _entry(_body(), "/nonexistent-t2857-policy-compiler/c++") as (run, seen, stock):
        try:
            run()
        except ValueError as exc:
            assert "grammar/compile rejected" in str(exc)
            assert "unavailable=True" in str(exc)
        else:
            raise AssertionError("unavailable compiler passed smoke entry")
        assert seen == []
        assert stock == [1, 0]


def test_smoke_entry_compile_exception_stops_before_build():
    # A malformed executable path raises in the real subprocess implementation;
    # no call inside any of the four validators is replaced.
    with _entry(_body(), "invalid\x00compiler") as (run, seen, stock):
        try:
            run()
        except ValueError as exc:
            assert "embedded null byte" in str(exc)
        else:
            raise AssertionError("compiler exception did not propagate")
        assert seen == []
        assert stock == [1, 0]


def test_smoke_entry_compile_timeout_stops_before_build():
    # Reuse the real delayed-compiler fixture from the compile contract test.
    compiler = _cxx()
    with tempfile.TemporaryDirectory() as tmp:
        wrapper = Path(tmp) / "delayed-compiler"
        wrapper.write_text('#!/bin/sh\nif [ "$1" = "--version" ]; then exec "' + compiler + '" "$@"; fi\n'
                           'sleep 60 &\nwait\nexec "' + compiler + '" "$@"\n')
        wrapper.chmod(0o700)
        with _entry(_body(), str(wrapper)) as (run, seen, stock):
            try:
                run()
            except ValueError as exc:
                assert "grammar/compile rejected" in str(exc)
                assert "timed_out=True" in str(exc)
            else:
                raise AssertionError("compiler timeout passed smoke entry")
            assert seen == []
            assert stock == [1, 0]


def _run():
    passed = failed = skipped = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"PASS {name}")
            passed += 1
        except Skip as exc:
            print(f"SKIP {name}: {exc}")
            skipped += 1
        except Exception as exc:
            print(f"FAIL {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
