from __future__ import annotations

import inspect
import json
import os
import stat
from pathlib import Path

import pytest

from orchestrator.campaign import reflux_origin_artifacts as artifacts
from orchestrator.tests.reflux_origin_fixture_builder import (
    build_result_evidence_record,
)


def _independent_canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def test_canonical_json_bytes_have_literal_wire_format() -> None:
    value = {"z": "日本語", "a": [True, None, 3]}
    expected = b'{"a":[true,null,3],"z":"\xe6\x97\xa5\xe6\x9c\xac\xe8\xaa\x9e"}'

    assert artifacts.canonical_json_bytes(value) == expected
    assert not expected.endswith(b"\n")


def test_create_only_write_succeeds_with_exact_canonical_bytes(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    parent = root / "records"
    parent.mkdir(parents=True)
    record = build_result_evidence_record()
    expected = _independent_canonical_bytes(record)

    target = artifacts.write_json_create_only(
        root=root,
        relative_path=Path("records/result.json"),
        value=record,
    )

    assert target == parent / "result.json"
    assert target.read_bytes() == expected
    assert artifacts.canonical_json_bytes(record) == expected
    assert not expected.endswith(b"\n")
    assert artifacts.strict_json_loads(expected) == record


def test_create_only_write_rejects_parent_escape(tmp_path: Path) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    with pytest.raises(artifacts.ArtifactError, match="relative path"):
        artifacts.write_create_only(
            root=root,
            relative_path=Path("../outside.json"),
            raw=b"{}",
        )

    assert not (tmp_path / "outside.json").exists()


def test_create_only_write_rejects_absolute_path_even_inside_root(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()

    with pytest.raises(artifacts.ArtifactError, match="relative path"):
        artifacts.write_create_only(
            root=root,
            relative_path=root / "absolute.json",
            raw=b"{}",
        )


def test_create_only_write_rejects_intermediate_symlink_ancestor(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    real_parent = root / "real-parent"
    real_parent.mkdir(parents=True)
    (root / "alias").symlink_to("real-parent", target_is_directory=True)

    with pytest.raises(artifacts.ArtifactError, match="symlink ancestor"):
        artifacts.write_create_only(
            root=root,
            relative_path=Path("alias/result.json"),
            raw=b"{}",
        )

    assert not (real_parent / "result.json").exists()


def test_create_only_write_rejects_existing_path_without_changing_it(
    tmp_path: Path,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    target = root / "result.json"
    target.write_bytes(b"first-writer")

    with pytest.raises(artifacts.ArtifactError, match="create artifact"):
        artifacts.write_create_only(
            root=root,
            relative_path=Path("result.json"),
            raw=b"second-writer",
        )

    assert target.read_bytes() == b"first-writer"


def test_create_only_write_fails_closed_on_read_back_mismatch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    monkeypatch.setattr(
        artifacts,
        "_read_back",
        lambda _path, _identity: b"different bytes",
    )

    with pytest.raises(artifacts.ArtifactError, match="read-back mismatch"):
        artifacts.write_create_only(
            root=root,
            relative_path=Path("result.json"),
            raw=b"expected bytes",
        )

    assert (root / "result.json").read_bytes() == b"expected bytes"


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), -float("inf")])
def test_canonical_json_rejects_non_finite_numbers(non_finite: float) -> None:
    with pytest.raises(artifacts.ArtifactError, match="canonical JSON"):
        artifacts.canonical_json_bytes({"value": non_finite})


def test_strict_json_parser_rejects_duplicate_keys() -> None:
    with pytest.raises(artifacts.ArtifactError, match="duplicate JSON key"):
        artifacts.strict_json_loads(b'{"key":1,"key":2}')


def test_strict_json_parser_rejects_noncanonical_whitespace() -> None:
    with pytest.raises(artifacts.ArtifactError, match="not canonical"):
        artifacts.strict_json_loads(b'{"key": 1}')


def test_create_only_open_flags_and_fsync_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "evidence"
    root.mkdir()
    target = root / "result.json"
    open_flags: list[int] = []
    fsync_kinds: list[str] = []
    real_open = os.open
    real_fsync = os.fsync

    def tracked_open(path, flags, mode=0o777):
        if Path(path) == target and flags & os.O_WRONLY:
            open_flags.append(flags)
        return real_open(path, flags, mode)

    def tracked_fsync(fd: int) -> None:
        mode = os.fstat(fd).st_mode
        fsync_kinds.append("directory" if stat.S_ISDIR(mode) else "file")
        real_fsync(fd)

    monkeypatch.setattr(artifacts.os, "open", tracked_open)
    monkeypatch.setattr(artifacts.os, "fsync", tracked_fsync)

    artifacts.write_create_only(
        root=root,
        relative_path=Path("result.json"),
        raw=b"{}",
    )

    assert len(open_flags) == 1
    required = os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    assert open_flags[0] & required == required
    assert fsync_kinds == ["file", "directory"]


def test_artifact_module_has_no_atomic_replace_writer() -> None:
    source = inspect.getsource(artifacts)
    forbidden_call = "os." + "replace"
    assert forbidden_call not in source
