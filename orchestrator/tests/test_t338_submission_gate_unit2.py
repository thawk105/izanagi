from __future__ import annotations

import hashlib
import inspect
import json
import os
from pathlib import Path

import pytest

from orchestrator.preregistration.blobref import BlobRef
from orchestrator.submission_gate import _receipt_io as receipt_io
from orchestrator.submission_gate import _receipt_schema as receipt_schema
from orchestrator.submission_gate import _safe_io as safe_io


@pytest.fixture
def repository_root(tmp_path: Path) -> Path:
    root = tmp_path / "repository"
    root.mkdir()
    (root / "nested").mkdir()
    (root / "nested" / "deeper").mkdir()
    return root


def _assert_rejected(callable_object, *args, **kwargs) -> None:
    with pytest.raises(Exception):
        callable_object(*args, **kwargs)


@pytest.mark.parametrize(
    "relative_path",
    [
        "/absolute/receipt.json",
        "../receipt.json",
        "nested/../receipt.json",
        "nested//receipt.json",
        "nested/./receipt.json",
        "./receipt.json",
        "",
    ],
)
def test_safe_io_rejects_absolute_traversal_and_empty_components(
    repository_root: Path, relative_path: str
):
    _assert_rejected(
        safe_io.read_relative_regular_bytes,
        repository_root,
        relative_path,
        max_bytes=1024,
    )
    _assert_rejected(
        safe_io.create_only_relative_bytes,
        repository_root,
        relative_path,
        b"receipt",
    )


def test_safe_io_rejects_symlinked_parent_and_final_component(
    repository_root: Path, tmp_path: Path
):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "receipt.json").write_bytes(b"outside")
    (repository_root / "parent-link").symlink_to(outside, target_is_directory=True)
    (repository_root / "final-link").symlink_to(outside / "receipt.json")

    for relative_path in ("parent-link/receipt.json", "final-link"):
        _assert_rejected(
            safe_io.read_relative_regular_bytes,
            repository_root,
            relative_path,
            max_bytes=1024,
        )
        _assert_rejected(
            safe_io.create_only_relative_bytes,
            repository_root,
            relative_path,
            b"must not escape",
        )
    assert (outside / "receipt.json").read_bytes() == b"outside"


def test_safe_io_rejects_symlinked_repository_root(tmp_path: Path):
    real_root = tmp_path / "real-root"
    real_root.mkdir()
    (real_root / "receipt.json").write_bytes(b"root")
    root_link = tmp_path / "root-link"
    root_link.symlink_to(real_root, target_is_directory=True)
    _assert_rejected(
        safe_io.read_relative_regular_bytes,
        root_link,
        "receipt.json",
        max_bytes=1024,
    )


def test_safe_io_requires_regular_final_target(repository_root: Path):
    _assert_rejected(
        safe_io.read_relative_regular_bytes,
        repository_root,
        "nested",
        max_bytes=1024,
    )
    (repository_root / "not-a-directory").write_bytes(b"x")
    _assert_rejected(
        safe_io.read_relative_regular_bytes,
        repository_root,
        "not-a-directory/receipt.json",
        max_bytes=1024,
    )


def test_safe_io_uses_no_follow_and_dir_fd_for_every_component(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    target = repository_root / "nested" / "deeper" / "receipt.json"
    target.write_bytes(b"exact")
    calls: list[tuple[object, int, object]] = []
    real_open = os.open

    def recording_open(path, flags, mode=0o777, *, dir_fd=None):
        calls.append((path, flags, dir_fd))
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(safe_io.os, "open", recording_open)
    assert safe_io.read_relative_regular_bytes(
        repository_root, "nested/deeper/receipt.json", max_bytes=1024
    ) == b"exact"

    assert len(calls) == 4
    assert calls[0][2] is None
    nofollow = getattr(os, "O_NOFOLLOW")
    directory_flag = getattr(os, "O_DIRECTORY")
    for path, flags, dir_fd in calls:
        assert flags & nofollow
        if dir_fd is None:
            assert path == os.fspath(repository_root)
            assert flags & directory_flag
        elif path in {"nested", "deeper"}:
            assert flags & directory_flag
            assert isinstance(dir_fd, int)
        elif path == "receipt.json" or (
            isinstance(path, str) and path.startswith(".receipt.json.create-")
        ):
            assert not flags & directory_flag
            assert isinstance(dir_fd, int)
        else:
            raise AssertionError(f"unexpected open path: {path!r}")


def test_safe_io_create_path_keeps_staging_and_final_open_no_follow(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    calls: list[tuple[object, int, object]] = []
    real_open = os.open

    def recording_open(path, flags, mode=0o777, *, dir_fd=None):
        calls.append((path, flags, dir_fd))
        if dir_fd is None:
            return real_open(path, flags, mode)
        return real_open(path, flags, mode, dir_fd=dir_fd)

    monkeypatch.setattr(safe_io.os, "open", recording_open)
    safe_io.create_only_relative_bytes(repository_root, "nested/receipt.json", b"x")

    assert len(calls) == 4
    nofollow = getattr(os, "O_NOFOLLOW")
    directory_flag = getattr(os, "O_DIRECTORY")
    exclusive = getattr(os, "O_EXCL")
    assert calls[0][2] is None
    assert calls[0][1] & directory_flag
    assert calls[1][0] == "nested"
    assert calls[1][2] is not None
    assert calls[1][1] & directory_flag
    stage_path, stage_flags, stage_dir_fd = calls[2]
    assert isinstance(stage_path, str) and stage_path.startswith(
        ".receipt.json.create-"
    )
    assert stage_flags & nofollow
    assert stage_flags & exclusive
    assert stage_dir_fd is not None
    assert calls[3][0] == "receipt.json"
    assert calls[3][1] & nofollow
    assert calls[3][2] is not None


def test_safe_io_fails_closed_when_no_follow_is_unavailable(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.delattr(safe_io.os, "O_NOFOLLOW", raising=False)
    _assert_rejected(
        safe_io.read_relative_regular_bytes,
        repository_root,
        "nested/receipt.json",
        max_bytes=1024,
    )
    _assert_rejected(
        safe_io.create_only_relative_bytes,
        repository_root,
        "nested/receipt.json",
        b"x",
    )


def test_safe_io_create_only_writes_exact_bytes_and_fsyncs_file_and_parent(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    fsync_fds: list[int] = []
    real_fsync = os.fsync

    def recording_fsync(fd: int) -> None:
        fsync_fds.append(fd)
        real_fsync(fd)

    monkeypatch.setattr(safe_io.os, "fsync", recording_fsync)
    raw = b'{ "b": 2, "a": 1 }\n'
    safe_io.create_only_relative_bytes(repository_root, "nested/receipt.json", raw)
    assert (repository_root / "nested/receipt.json").read_bytes() == raw
    assert len(fsync_fds) >= 3

    with pytest.raises(safe_io.SafeIOError):
        safe_io.create_only_relative_bytes(repository_root, "nested/receipt.json", raw)
    assert (repository_root / "nested/receipt.json").read_bytes() == raw


def test_safe_io_create_only_handles_short_writes(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    real_write = os.write
    calls = 0

    def short_write(fd: int, data: bytes) -> int:
        nonlocal calls
        calls += 1
        return real_write(fd, data[:1])

    monkeypatch.setattr(safe_io.os, "write", short_write)
    raw = b"short writes still require every byte"
    safe_io.create_only_relative_bytes(repository_root, "nested/short.bin", raw)
    assert (repository_root / "nested/short.bin").read_bytes() == raw
    assert calls == len(raw)


def test_safe_io_create_only_rejects_existing_symlink_without_following(
    repository_root: Path, tmp_path: Path
):
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    (repository_root / "receipt.bin").symlink_to(outside)
    with pytest.raises(safe_io.SafeIOError):
        safe_io.create_only_relative_bytes(repository_root, "receipt.bin", b"new")
    assert outside.read_bytes() == b"outside"


def test_parse_receipt_preserves_noncanonical_but_valid_json_bytes():
    raw = b'{ "nested": { "z": 1, "a": [true, null] }, "first": 2 }\n'
    document = receipt_io.parse_receipt_bytes(raw)
    assert document.raw_bytes == raw
    assert document.sha256 == hashlib.sha256(raw).hexdigest()
    assert document.value["nested"]["z"] == 1
    assert document.value["first"] == 2
    assert raw != json.dumps(document.value, sort_keys=True, separators=(",", ":")).encode()


@pytest.mark.parametrize(
    "raw",
    [
        b'{"key": 1, "key": 2}',
        b'{"nested": {"key": 1, "key": 2}}',
        b'{"nested": [{"key": 1, "key": 2}]}',
    ],
)
def test_parse_receipt_rejects_duplicate_keys_at_every_object_level(raw: bytes):
    with pytest.raises(receipt_io.ReceiptParseError, match="duplicate"):
        receipt_io.parse_receipt_bytes(raw)


@pytest.mark.parametrize(
    "raw",
    [b'{"x": NaN}', b'{"x": Infinity}', b'{"x": -Infinity}'],
)
def test_parse_receipt_rejects_nonfinite_constants(raw: bytes):
    with pytest.raises(receipt_io.ReceiptParseError, match="non-finite"):
        receipt_io.parse_receipt_bytes(raw)


@pytest.mark.parametrize("raw", [b"\xff", b'{"x":"\xff"}'])
def test_parse_receipt_rejects_non_utf8(raw: bytes):
    with pytest.raises(receipt_io.ReceiptParseError, match="UTF-8"):
        receipt_io.parse_receipt_bytes(raw)


@pytest.mark.parametrize("raw", [b"[]", b"1", b"null", b'"scalar"'])
def test_parse_receipt_requires_object_root(raw: bytes):
    with pytest.raises(receipt_io.ReceiptParseError, match="root"):
        receipt_io.parse_receipt_bytes(raw)


def test_read_and_create_receipt_use_exact_bytes_and_no_binding_argument(
    repository_root: Path,
):
    raw = b'{"z":0, "a": 1}'
    receipt_io.create_receipt_bytes(repository_root, "nested/receipt.json", raw)
    document = receipt_io.read_receipt(repository_root, "nested/receipt.json")
    assert document.raw_bytes == raw
    assert document.sha256 == hashlib.sha256(raw).hexdigest()
    assert "binding" not in inspect.signature(
        receipt_io.create_receipt_bytes
    ).parameters
    with pytest.raises(safe_io.SafeIOError):
        receipt_io.create_receipt_bytes(repository_root, "nested/receipt.json", raw)


def test_read_receipt_honors_max_bytes(repository_root: Path):
    (repository_root / "nested" / "large.json").write_bytes(b"{" + b"x" * 20)
    with pytest.raises(safe_io.SafeIOError):
        receipt_io.read_receipt(
            repository_root, "nested/large.json", max_bytes=4
        )


def _blob_ref(raw_bytes: bytes, *, sha256: str | None = None) -> BlobRef:
    return BlobRef(
        "approved/receipt-schema-v1.json",
        "a" * 40,
        sha256 if sha256 is not None else hashlib.sha256(raw_bytes).hexdigest(),
    )


def _minimal_schema() -> dict[str, object]:
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "additionalProperties": False,
        "required": ["schema_version", "compile_commands"],
        "properties": {
            "schema_version": {"const": "unit2/v1"},
            "compile_commands": {"$ref": "#/definitions/fileRecord"},
        },
        "definitions": {
            "fileRecord": {
                "type": "object",
                "additionalProperties": False,
                "required": ["path", "size", "sha256"],
                "properties": {
                    "path": {
                        "type": "string",
                        "minLength": 1,
                        "pattern": r"^(?!/)(?!.*(?:^|/)\.\.(?:/|$)).+$",
                    },
                    "size": {"type": "integer", "minimum": 0},
                    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
                },
            }
        },
    }


def test_schema_digest_and_private_loader_use_exact_fixed_blob(
    repository_root: Path, monkeypatch: pytest.MonkeyPatch
):
    raw = json.dumps(_minimal_schema(), separators=(",", ":")).encode("utf-8")
    ref = _blob_ref(raw)
    parsed = receipt_schema.parse_schema_bytes(raw, ref=ref)
    assert parsed.ref == ref
    assert parsed.sha256 == hashlib.sha256(raw).hexdigest()
    assert parsed.document["$schema"] == "http://json-schema.org/draft-07/schema#"

    monkeypatch.setattr(
        receipt_schema,
        "read_pinned_blob",
        lambda root, candidate: raw if candidate == ref else b"wrong",
    )
    loaded = receipt_schema._load_schema_from_ref(repository_root, ref)
    assert loaded.sha256 == parsed.sha256

    wrong_ref = _blob_ref(raw, sha256="0" * 64)
    with pytest.raises(receipt_schema.ReceiptSchemaError, match="mismatch"):
        receipt_schema.parse_schema_bytes(raw, ref=wrong_ref)


def test_approved_receipt_schema_fixture_is_draft7_and_keeps_file_record_ref():
    schema_path = (
        Path(__file__).resolve().parents[2]
        / "output"
        / "insights"
        / "2026-08-11_t139-manifest-land1"
        / "receipt-schema-v1.json"
    )
    raw = schema_path.read_bytes()
    schema = receipt_schema.parse_schema_bytes(raw, ref=_blob_ref(raw))
    assert schema.document["$schema"] == "http://json-schema.org/draft-07/schema#"
    file_record = schema.document["definitions"]["fileRecord"]
    assert set(file_record["required"]) == {"path", "size", "sha256"}
    assert file_record["additionalProperties"] is False
    assert (
        schema.document["definitions"]["performanceCompileStock"]["properties"]
        ["compile_commands"]
        == {"$ref": "#/definitions/fileRecord"}
    )
    assert (
        schema.document["definitions"]["performanceCompileMode"]["properties"]
        ["compile_commands"]
        == {"$ref": "#/definitions/fileRecord"}
    )


def test_public_schema_loader_does_not_accept_caller_selected_ref():
    parameters = inspect.signature(receipt_schema.load_schema).parameters
    assert "ref" not in parameters
    assert "approved_manifest" in parameters
    with pytest.raises(TypeError):
        receipt_schema.load_schema(Path("/unused"), ref=_blob_ref(b"{}"))


def test_validate_receipt_shape_checks_draft7_top_level_required_key():
    raw = json.dumps(_minimal_schema(), separators=(",", ":")).encode("utf-8")
    schema = receipt_schema.parse_schema_bytes(raw, ref=_blob_ref(raw))
    valid = {
        "schema_version": "unit2/v1",
        "compile_commands": {
            "path": "build/compile_commands.json",
            "size": 17,
            "sha256": "a" * 64,
        },
    }
    receipt_schema.validate_receipt_shape(valid, schema=schema)
    assert set(valid["compile_commands"]) == {"path", "size", "sha256"}

    missing = dict(valid)
    del missing["compile_commands"]
    with pytest.raises(receipt_schema.ReceiptSchemaError, match="required"):
        receipt_schema.validate_receipt_shape(missing, schema=schema)

    extra = {**valid, "unexpected": True}
    with pytest.raises(receipt_schema.ReceiptSchemaError, match="additional"):
        receipt_schema.validate_receipt_shape(extra, schema=schema)


@pytest.mark.parametrize(
    "compile_commands",
    [
        {"path": "/absolute.json", "size": 1, "sha256": "a" * 64},
        {"path": "../escape.json", "size": 1, "sha256": "a" * 64},
        {"path": "ok.json", "size": -1, "sha256": "a" * 64},
        {"path": "ok.json", "size": 1.5, "sha256": "a" * 64},
        {"path": "ok.json", "size": 1, "sha256": "A" * 64},
        {"path": "ok.json", "size": 1, "sha256": "short"},
        {
            "path": "ok.json",
            "size": 1,
            "sha256": "a" * 64,
            "extra": "reject",
        },
    ],
)
def test_compile_commands_preserves_file_record_shape_and_rejects_bad_values(
    compile_commands: dict[str, object]
):
    raw = json.dumps(_minimal_schema(), separators=(",", ":")).encode("utf-8")
    schema = receipt_schema.parse_schema_bytes(raw, ref=_blob_ref(raw))
    receipt = {
        "schema_version": "unit2/v1",
        "compile_commands": compile_commands,
    }
    with pytest.raises(receipt_schema.ReceiptSchemaError):
        receipt_schema.validate_receipt_shape(receipt, schema=schema)


def test_compile_commands_file_record_is_kept_without_reader_recalculation():
    raw = (
        b'{"compile_commands":{"sha256":"'
        + b"b" * 64
        + b'","size":999,"path":"build/compile_commands.json"},'
        b'"schema_version":"unit2/v1"}'
    )
    document = receipt_io.parse_receipt_bytes(raw)
    record = document.value["compile_commands"]
    assert record == {
        "sha256": "b" * 64,
        "size": 999,
        "path": "build/compile_commands.json",
    }
    assert set(record) == {"path", "size", "sha256"}
