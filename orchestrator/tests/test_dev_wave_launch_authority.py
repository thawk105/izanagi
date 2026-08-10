"""docs 由来 dev-wave launch authority の fail-closed 回帰。"""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

import pytest

from tools.dev_waves.launch_authority import (
    STAGES,
    AuthorityError,
    derive_launch,
    snapshot_authority,
)


_ROOT = Path(__file__).resolve().parents[2]
_OPERATIONS = "docs/dev-wave/operations.md"
_WORKERS = "docs/dev-wave/workers.md"


def _git(root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-C", os.fspath(root), *args],
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return completed.stdout.strip()


def _authority_line(text: str) -> str:
    matches = [line for line in text.splitlines() if "`<model>`:" in line]
    assert len(matches) == 1
    return matches[0]


def _prepare_repo(tmp_path: Path, *, operations: str | None = None) -> Path:
    root = tmp_path / "repo"
    (root / "docs/dev-wave").mkdir(parents=True)
    (root / _OPERATIONS).write_text(
        operations
        if operations is not None
        else (_ROOT / _OPERATIONS).read_text(encoding="utf-8"),
        encoding="utf-8",
    )
    (root / _WORKERS).write_text(
        (_ROOT / _WORKERS).read_text(encoding="utf-8"), encoding="utf-8"
    )
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "authority-test")
    _git(root, "config", "user.email", "authority-test@example.invalid")
    _git(root, "add", _OPERATIONS, _WORKERS)
    _git(root, "commit", "-qm", "authority fixture")
    return root


def test_snapshot_and_derive_current_authority_positive(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    snapshot = snapshot_authority(root)
    requirements = {
        (stage, lane): derive_launch(snapshot, stage=stage, lane=lane)
        for stage, lane in (
            ("plan", None),
            ("consult", "sol"),
            ("consult", "luna"),
            ("author", None),
            ("review", None),
            ("fix", None),
            ("focus", None),
        )
    }
    assert tuple(dict.fromkeys(item[0] for item in requirements)) == STAGES
    assert (
        requirements[("consult", "sol")].model
        != requirements[("consult", "luna")].model
    )
    assert (
        requirements[("author", None)].model
        == requirements[("consult", "sol")].model
    )
    assert requirements[("review", None)].effort_authority == "docs"
    assert requirements[("focus", None)].effort_authority == "docs"
    assert requirements[("author", None)].effort is None
    assert requirements[("author", None)].effort_authority == "unbound"
    assert len(snapshot.sections) == 3


def _mutate_normative_line(text: str, case: str) -> str:
    line = _authority_line(text)
    if case == "blockquote":
        replacement = f"> {line}"
    elif case == "list":
        replacement = f"- {line}"
    elif case == "raw_html":
        replacement = f"<div>\n{line}\n</div>\n"
    elif case == "negation":
        replacement = f"この例では次を規範として採用しない: {line}"
    elif case == "link_example":
        replacement = f"[{line}](https://example.invalid/example)"
    elif case == "zero":
        replacement = "model authority は dispatcher 例に置かない。"
    elif case == "duplicate":
        replacement = f"{line}\n{line}"
    elif case == "u2028":
        replacement = line.replace("段 3", "段\u20283", 1)
    elif case == "u2029":
        replacement = line.replace("段 3", "段\u20293", 1)
    else:  # pragma: no cover - registration meta-test が閉じる
        raise AssertionError(case)
    changed = text.replace(line, replacement, 1)
    assert changed != text
    return changed


_NORMATIVE_DECOY_CASES = (
    "blockquote",
    "list",
    "raw_html",
    "negation",
    "link_example",
    "zero",
    "duplicate",
    "u2028",
    "u2029",
)


@pytest.mark.parametrize("case", _NORMATIVE_DECOY_CASES)
def test_model_normative_line_decoys_fail_closed(
    tmp_path: Path, case: str
) -> None:
    original = (_ROOT / _OPERATIONS).read_text(encoding="utf-8")
    root = _prepare_repo(
        tmp_path, operations=_mutate_normative_line(original, case)
    )
    with pytest.raises(AuthorityError):
        snapshot_authority(root)


def test_authority_decoy_case_registration_is_complete() -> None:
    assert set(_NORMATIVE_DECOY_CASES) == {
        "blockquote",
        "list",
        "raw_html",
        "negation",
        "link_example",
        "zero",
        "duplicate",
        "u2028",
        "u2029",
    }


def test_dirty_working_tree_authority_is_rejected(tmp_path: Path) -> None:
    root = _prepare_repo(tmp_path)
    path = root / _OPERATIONS
    path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")
    with pytest.raises(AuthorityError):
        snapshot_authority(root)


def test_historical_commit_is_reconstructed_without_live_head(
    tmp_path: Path,
) -> None:
    root = _prepare_repo(tmp_path)
    historical_commit = _git(root, "rev-parse", "HEAD")
    historical = snapshot_authority(root, commit=historical_commit)
    path = root / _OPERATIONS
    text = path.read_text(encoding="utf-8")
    line = _authority_line(text)
    models = re.findall(r"gpt-[A-Za-z0-9._-]+", line)
    assert len(models) == 3 and models[0] == models[2] and models[0] != models[1]
    swapped = (
        line.replace(models[0], "MODEL-TEMP")
        .replace(models[1], models[0])
        .replace("MODEL-TEMP", models[1])
    )
    path.write_text(text.replace(line, swapped, 1), encoding="utf-8")
    _git(root, "add", _OPERATIONS)
    _git(root, "commit", "-qm", "change authority")
    current = snapshot_authority(root)
    reconstructed = snapshot_authority(root, commit=historical_commit)
    assert reconstructed == historical
    assert reconstructed.digest != current.digest
    assert (
        derive_launch(reconstructed, stage="author", lane=None).model
        != derive_launch(current, stage="author", lane=None).model
    )


def test_lane_validation_is_not_inferred_from_model_value(tmp_path: Path) -> None:
    snapshot = snapshot_authority(_prepare_repo(tmp_path))
    with pytest.raises(AuthorityError):
        derive_launch(snapshot, stage="consult", lane=None)
    with pytest.raises(AuthorityError):
        derive_launch(snapshot, stage="author", lane="sol")


def _run() -> int:
    """新規 test file を repository の plain-runner 契約へ載せる。"""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
