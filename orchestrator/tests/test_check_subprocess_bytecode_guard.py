from __future__ import annotations

import os
import sys
import textwrap
from pathlib import Path

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from tools import check_subprocess_bytecode_guard as checker


_REPO = Path(__file__).resolve().parents[2]


def _parse_violations(output: str) -> set[tuple[str, int, str]]:
    parsed = []
    for line in output.splitlines():
        path, lineno, _column, callee = line.split(":", 3)
        parsed.append((path, int(lineno), callee))
    assert len(parsed) == len(set(parsed))
    return set(parsed)


def _write(root: Path, relative: str, source: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(source), encoding="utf-8")


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "fixture_repo"
    (root / "orchestrator").mkdir(parents=True)
    (root / "tools").mkdir()
    return root


def test_guard_patterns_and_direct_callees(tmp_path, capsys):
    root = _repo(tmp_path)
    _write(
        root,
        "orchestrator/cases.py",
        """
        import os
        import subprocess
        import sys

        def dict_guard():
            subprocess.run([sys.executable, "case.py"], env={"PYTHONDONTWRITEBYTECODE": "1"})

        def dict_call_guard():
            subprocess.run([sys.executable, "case.py"], env=dict(PYTHONDONTWRITEBYTECODE="1"))

        def name_guard():
            environment = {"PYTHONDONTWRITEBYTECODE": "1"}
            subprocess.run([sys.executable, "case.py"], env=environment)

        def make_environment(extra=None):
            return {"PYTHONDONTWRITEBYTECODE": "1"}

        module_environment = make_environment()

        def one_hop_guard():
            environment = make_environment()
            subprocess.run([sys.executable, "case.py"], env=environment)

        def module_one_hop_guard():
            subprocess.run([sys.executable, "case.py"], env=module_environment)

        def flag_guard():
            subprocess.run([sys.executable, "-B", "-c", "pass"], env={})

        def all_callees():
            subprocess.run([sys.executable, "case.py"], env={})
            subprocess.Popen([sys.executable, "case.py"], env={})
            subprocess.call([sys.executable, "case.py"], env={})
            subprocess.check_call([sys.executable, "case.py"], env={})
            subprocess.check_output([sys.executable, "case.py"], env={})
        """,
    )

    rc = checker.main(["--repo", str(root)])
    output = capsys.readouterr().out

    assert rc == checker.VIOLATION_RC
    assert _parse_violations(output) == {
        ("orchestrator/cases.py", 32, "run"),
        ("orchestrator/cases.py", 33, "Popen"),
        ("orchestrator/cases.py", 34, "call"),
        ("orchestrator/cases.py", 35, "check_call"),
        ("orchestrator/cases.py", 36, "check_output"),
    }


def test_non_python_argv_and_function_boundary(tmp_path, capsys):
    root = _repo(tmp_path)
    _write(
        root,
        "tools/cases.py",
        """
        import subprocess
        import sys

        PYTHONDONTWRITEBYTECODE = "1"

        def make_environment():
            return {"PYTHONDONTWRITEBYTECODE": "1"}

        module_environment = make_environment()

        def git_calls():
            subprocess.run(["git", "add", "tools/case.py"], env={})
            subprocess.run(["git", "-m", "pytest"], env={})

        def python_call_without_local_guard():
            environment = {}
            subprocess.run([sys.executable, "case.py"], env=environment)

        def module_one_hop_is_not_a_literal_leak():
            subprocess.run([sys.executable, "case.py"], env=module_environment)
        """,
    )
    _write(
        root,
        "orchestrator/__pycache__/ignored.py",
        """
        import subprocess, sys
        subprocess.run([sys.executable, "ignored.py"], env={})
        """,
    )

    rc = checker.main(["--repo", str(root)])
    output = capsys.readouterr().out

    assert rc == checker.VIOLATION_RC
    assert _parse_violations(output) == {
        ("tools/cases.py", 18, "run"),
    }


def test_literal_python_argv0_variants(tmp_path, capsys):
    root = _repo(tmp_path)
    _write(
        root,
        "orchestrator/cases.py",
        """\
        import subprocess

        def python_argv0_variants():
            subprocess.run(["python", "case.py"], env={})
            subprocess.run(["python3", "case.py"], env={})
            subprocess.run(["tools/case.py", "--flag"], env={})
        """,
    )

    rc = checker.main(["--repo", str(root)])
    output = capsys.readouterr().out

    assert rc == checker.VIOLATION_RC
    assert _parse_violations(output) == {
        ("orchestrator/cases.py", 4, "run"),
        ("orchestrator/cases.py", 5, "run"),
        ("orchestrator/cases.py", 6, "run"),
    }


def test_dict_unpack_guard_and_nested_scope_boundary(tmp_path, capsys):
    root = _repo(tmp_path)
    _write(
        root,
        "tools/cases.py",
        """\
        import subprocess
        import sys

        def dict_unpack_guard():
            subprocess.run([sys.executable, "case.py"], env=dict(**{"PYTHONDONTWRITEBYTECODE": "1"}))

        def nested_guard_is_not_local():
            environment = {}

            def nested():
                return {"PYTHONDONTWRITEBYTECODE": "1"}

            subprocess.run([sys.executable, "case.py"], env=environment)
        """,
    )

    rc = checker.main(["--repo", str(root)])
    output = capsys.readouterr().out

    assert rc == checker.VIOLATION_RC
    assert _parse_violations(output) == {
        ("tools/cases.py", 13, "run"),
    }


def test_broken_python_is_indeterminate_even_with_violation(tmp_path, capsys):
    root = _repo(tmp_path)
    _write(
        root,
        "orchestrator/bad.py",
        """
        import subprocess, sys
        subprocess.run([sys.executable, "bad.py"], env={})
        """,
    )
    _write(root, "tools/broken.py", "def broken(:\n")

    rc = checker.main(["--repo", str(root)])
    captured = capsys.readouterr()

    assert rc == checker.INDETERMINATE_RC
    assert "bad.py:" in captured.out
    assert "broken.py" in captured.err


def test_real_repo_clean():
    assert checker.main(["--repo", str(_REPO)]) == checker.CLEAN_RC


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-x"]))
