from __future__ import annotations

import hashlib
import inspect
import os
from pathlib import Path
import subprocess

import pytest

import orchestrator.preregistration as preregistration
from orchestrator.preregistration.addendum_envelope import (
    ExtraFieldsError,
    FieldsSectionNotFoundError,
    MissingFieldsError,
    T139_EXACT_FIELDS,
)
from orchestrator.preregistration.blobref import (
    BlobRef,
    BlobResolutionError,
    read_pinned_blob,
)
from orchestrator.preregistration.erratum import (
    ComposedDigestMismatchError,
    EmptyErratumSetError,
    OccurrenceCountError,
    OldDigestMismatchError,
    OperationCountError,
    OperationDeltaError,
    UnknownErratumError,
    compose_core,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CORE_REF = BlobRef(
    path="output/insights/2026-08-07_t139-mainrun-design/preregistration.md",
    commit="88d68f9127b31df5aafc3d59607896626a1652e8",
    sha256="ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9",
)
ERRATUM_REF = BlobRef(
    path="output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md",
    commit="1d235e0e455020cf54e66cf83304961910c369d8",
    sha256="a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3",
)
ADDENDUM_REF = BlobRef(
    path="output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md",
    commit="622bd786191d40bda388596fa2adbf119ee84c9a",
    sha256="f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec",
)
EXPECTED_COMPOSED_SHA256 = "d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82"
EXPECTED_OPERATION_LINE_SHA256 = (
    "6e87b981b2d3550ea56278a50f9544a86bab575d18de3ea7f3984abdeca5681e",
    "b5e2c7b290c1c21aff84f4b520468df551c9d0e4bd76d2102ace3208b3e1b7d1",
)
EXPECTED_FIELDS = frozenset(
    {
        "a01",
        "a02",
        "a03",
        "a04",
        "a05",
        "a06",
        "a07",
        "a08",
        "a09",
        "a10",
        "a11",
        "a12",
        "a13",
    }
)


def _synthetic_core(
    *, third_occurrence: bool = False, misbound_occurrences: bool = False
) -> tuple[bytes, tuple[int, int]]:
    lines = [
        "# synthetic core\n",
        "5. exact fields are `a01`〜`a12` only.\n",
        "unrelated line\n",
        "The addendum sets `a01`〜`a12` before the pilot.\n",
    ]
    if misbound_occurrences:
        lines[2] = "A second exact `a01`〜`a12` reference.\n"
        lines[3] = "A differently spelled a12 token.\n"
    if third_occurrence:
        lines.append("A third accidental `a01`〜`a12` reference.\n")
    return "".join(lines).encode(), (2, 4)


def _operation_yaml(
    *,
    index: int,
    line_number: int,
    old_line: bytes,
    old_sha256: str | None = None,
    new_line: bytes | None = None,
) -> str:
    old_text = old_line.decode()
    replacement = new_line.decode() if new_line is not None else old_text.replace("a12", "a13")
    digest = old_sha256 or hashlib.sha256(old_line).hexdigest()
    return (
        f"  - index: {index}\n"
        "    locator:\n"
        '      section: "15"\n'
        f'      anchor: "synthetic operation {index}"\n'
        f"      line_number_at_target_commit: {line_number}\n"
        f"    old_sha256: {digest}\n"
        "    old_text: |\n"
        f"      {old_text}"
        "    new_text: |\n"
        f"      {replacement}"
    )


def _synthetic_erratum(
    core: bytes,
    line_numbers: tuple[int, ...] = (2, 4),
    *,
    old_sha_overrides: dict[int, str] | None = None,
    new_line_overrides: dict[int, bytes] | None = None,
    decoy_operations: bool = False,
    erratum_id: str = "t139-core-s15-exactkey-v1",
) -> bytes:
    lines = core.splitlines(keepends=True)
    operations = "".join(
        _operation_yaml(
            index=index,
            line_number=line_number,
            old_line=lines[line_number - 1],
            old_sha256=(old_sha_overrides or {}).get(index),
            new_line=(new_line_overrides or {}).get(index),
        )
        for index, line_number in enumerate(line_numbers, start=1)
    )
    decoy = "decoy:\n" if decoy_operations else ""
    return (
        "# synthetic erratum\n\n"
        "```text\n"
        f"erratum_id: {erratum_id}\n"
        "```\n\n"
        "## 2. ignored prose\n\n"
        "## 3. supersede operations\n\n"
        "```yaml\n"
        "operations:\n"
        f"{decoy}"
        f"{operations}"
        "```\n\n"
        "## 4. ignored prose with `a01`〜`a12`\n"
    ).encode()


def _expected_synthetic_composed_sha256(
    core: bytes, line_numbers: tuple[int, ...] = (2, 4)
) -> str:
    lines = core.splitlines(keepends=True)
    for line_number in line_numbers:
        lines[line_number - 1] = lines[line_number - 1].replace(b"a12", b"a13", 1)
    return hashlib.sha256(b"".join(lines)).hexdigest()


def _compose_synthetic(
    monkeypatch: pytest.MonkeyPatch,
    core: bytes,
    erratum: bytes,
    *,
    expected_composed_sha256: str | None = None,
):
    core_ref = CORE_REF
    erratum_ref = ERRATUM_REF

    def fake_read(_root: str, ref: BlobRef) -> bytes:
        if ref is core_ref:
            return core
        if ref is erratum_ref:
            return erratum
        raise AssertionError(ref)

    monkeypatch.setattr("orchestrator.preregistration.erratum.read_pinned_blob", fake_read)
    return compose_core(
        "unused",
        core_ref=core_ref,
        erratum_refs=(erratum_ref,),
        expected_composed_sha256=(
            expected_composed_sha256 or _expected_synthetic_composed_sha256(core)
        ),
    )


def test_erratum_rejects_operation_count_not_two(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    for count in (1, 3):
        erratum = _synthetic_erratum(core, (2, 4, 2)[:count])
        with pytest.raises(OperationCountError):
            _compose_synthetic(monkeypatch, core, erratum)


def test_erratum_operations_must_be_direct_sequence(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    erratum = _synthetic_erratum(core, decoy_operations=True)
    with pytest.raises(OperationCountError):
        _compose_synthetic(monkeypatch, core, erratum)


def test_erratum_rejects_old_sha256_mismatch(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    erratum = _synthetic_erratum(core, old_sha_overrides={1: "0" * 64})
    with pytest.raises(OldDigestMismatchError):
        _compose_synthetic(monkeypatch, core, erratum)


def test_erratum_rejects_occurrence_count_not_two(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core(third_occurrence=True)
    erratum = _synthetic_erratum(core)
    with pytest.raises(OccurrenceCountError):
        _compose_synthetic(monkeypatch, core, erratum)


def test_erratum_occurrences_must_bind_to_operation_lines(
    monkeypatch: pytest.MonkeyPatch,
):
    core, operation_lines = _synthetic_core(misbound_occurrences=True)
    erratum = _synthetic_erratum(core, operation_lines)
    with pytest.raises(OccurrenceCountError):
        _compose_synthetic(monkeypatch, core, erratum)


def test_erratum_rejects_multi_token_delta(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    first_line = core.splitlines(keepends=True)[1]
    changed = first_line.replace(b"5.", b"6.").replace(b"a12", b"a13")
    erratum = _synthetic_erratum(core, new_line_overrides={1: changed})
    expected_lines = core.splitlines(keepends=True)
    expected_lines[1] = changed
    expected_lines[3] = expected_lines[3].replace(b"a12", b"a13", 1)
    with pytest.raises(OperationDeltaError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=hashlib.sha256(
                b"".join(expected_lines)
            ).hexdigest(),
        )


def test_erratum_composed_digest_must_match(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    actual_digest = _expected_synthetic_composed_sha256(core)
    with pytest.raises(ComposedDigestMismatchError) as raised:
        _compose_synthetic(
            monkeypatch,
            core,
            _synthetic_erratum(core),
            expected_composed_sha256="0" * 64,
        )
    assert actual_digest not in str(raised.value)


def test_erratum_empty_reference_set_is_rejected(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    monkeypatch.setattr(
        "orchestrator.preregistration.erratum.read_pinned_blob",
        lambda _root, ref: core if ref is CORE_REF else pytest.fail(str(ref)),
    )
    with pytest.raises(EmptyErratumSetError):
        compose_core(
            "unused",
            core_ref=CORE_REF,
            erratum_refs=(),
            expected_composed_sha256=hashlib.sha256(core).hexdigest(),
        )


def test_expected_composed_sha256_is_required_keyword_only():
    parameter = inspect.signature(compose_core).parameters["expected_composed_sha256"]
    assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert parameter.default is inspect.Parameter.empty


def test_erratum_unknown_id_is_rejected(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    erratum = _synthetic_erratum(core, erratum_id="unknown-erratum-v1")
    with pytest.raises(UnknownErratumError):
        _compose_synthetic(monkeypatch, core, erratum)


def test_envelope_parser_ignores_headings_outside_fields():
    blob = (
        b"# title\n\n### outside_before\n\n## fields\n\n"
        b"### a01 -- one\n### a02 -- two\n\n## tail\n\n### outside_after\n"
    )
    assert preregistration.parse_addendum_fields(blob) == ("a01", "a02")


def test_envelope_parser_ignores_fenced_headings_and_boundaries():
    blob = (
        b"## fields\n### a01\n"
        b"```text\n### a13\n## false-tail\n```\n"
        b"~~~\n### a14\n## another-false-tail\n~~~\n"
        b"### a02\n## tail\n"
    )
    assert preregistration.parse_addendum_fields(blob) == ("a01", "a02")


def test_envelope_parser_rejects_extra_key():
    blob = b"## fields\n### a01\n### a02\n### a03\n"
    with pytest.raises(ExtraFieldsError) as raised:
        preregistration.require_exact_fields(blob, frozenset({"a01", "a02"}))
    assert raised.value.reason_code == "extra_fields"


def test_envelope_parser_rejects_missing_key():
    blob = b"## fields\n### a01\n### a02\n"
    with pytest.raises(MissingFieldsError) as raised:
        preregistration.require_exact_fields(
            blob, frozenset({"a01", "a02", "a03"})
        )
    assert raised.value.reason_code == "missing_fields"


def test_default_exact_fields_constant_rejects_a13_missing():
    blob = b"## fields\n" + b"".join(
        f"### a{index:02d}\n".encode() for index in range(1, 13)
    )
    with pytest.raises(MissingFieldsError):
        preregistration.require_exact_fields(blob)
    assert T139_EXACT_FIELDS == EXPECTED_FIELDS


def test_fields_section_missing_is_fail_closed():
    with pytest.raises(FieldsSectionNotFoundError):
        preregistration.parse_addendum_fields(b"## not-fields\n### a01\n")


def test_missing_commit_is_fail_closed():
    missing_commit = BlobRef(CORE_REF.path, "0" * 40, CORE_REF.sha256)
    with pytest.raises(BlobResolutionError):
        read_pinned_blob(REPOSITORY_ROOT, missing_commit)


def _git(root: Path, *arguments: str) -> bytes:
    return subprocess.run(
        ["git", *arguments],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


@pytest.fixture
def git_blob_fixture(tmp_path: Path) -> tuple[Path, bytes, str, str]:
    root = tmp_path / "repository"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "T139 test")
    _git(root, "config", "user.email", "t139@example.invalid")
    regular = root / "regular.txt"
    regular.write_bytes(b"regular bytes\n")
    os.symlink("regular.txt", root / "link.txt")
    (root / "literal[1].txt").write_bytes(b"literal bracket bytes\n")
    (root / "literal1.txt").write_bytes(b"glob decoy bytes\n")
    _git(root, "add", "regular.txt", "link.txt", "literal[1].txt", "literal1.txt")
    _git(root, "commit", "-q", "-m", "fixture")
    commit = _git(root, "rev-parse", "HEAD").decode().strip()
    tree = _git(root, "rev-parse", "HEAD^{tree}").decode().strip()
    return root, regular.read_bytes(), commit, tree


def test_blob_reference_requires_exact_commit(git_blob_fixture):
    root, regular_bytes, _commit, tree = git_blob_fixture

    tree_ref = BlobRef(
        "regular.txt", tree, hashlib.sha256(regular_bytes).hexdigest()
    )
    with pytest.raises(BlobResolutionError):
        read_pinned_blob(root, tree_ref)


def test_blob_reference_rejects_symlink_mode(git_blob_fixture):
    root, _regular_bytes, commit, _tree = git_blob_fixture

    symlink_ref = BlobRef(
        "link.txt", commit, hashlib.sha256(b"regular.txt").hexdigest()
    )
    with pytest.raises(BlobResolutionError):
        read_pinned_blob(root, symlink_ref)


def test_blob_resolution_does_not_inherit_git_repository_overrides(
    git_blob_fixture, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    root, regular_bytes, commit, _tree = git_blob_fixture
    attacker = tmp_path / "attacker"
    attacker.mkdir()
    _git(attacker, "init", "-q")
    monkeypatch.setenv("GIT_DIR", os.fspath(attacker / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", os.fspath(attacker))
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    assert read_pinned_blob(root, ref) == regular_bytes


def test_blob_resolution_requires_exact_git_top_level(git_blob_fixture):
    root, regular_bytes, commit, _tree = git_blob_fixture
    subdirectory = root / "subdirectory"
    subdirectory.mkdir()
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    with pytest.raises(BlobResolutionError):
        read_pinned_blob(subdirectory, ref)


def test_blob_resolution_uses_literal_pathspec(git_blob_fixture):
    root, _regular_bytes, commit, _tree = git_blob_fixture
    expected = b"literal bracket bytes\n"
    ref = BlobRef("literal[1].txt", commit, hashlib.sha256(expected).hexdigest())

    assert read_pinned_blob(root, ref) == expected


def test_blob_resolution_rejects_replace_refs(git_blob_fixture):
    root, regular_bytes, commit, tree = git_blob_fixture
    replacement = _git(root, "commit-tree", tree, "-m", "replacement")
    _git(root, "replace", commit, replacement.decode().strip())
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    with pytest.raises(BlobResolutionError):
        read_pinned_blob(root, ref)


def test_blob_resolution_rejects_shallow_repository(
    git_blob_fixture, tmp_path: Path
):
    root, regular_bytes, commit, _tree = git_blob_fixture
    shallow = tmp_path / "shallow"
    _git(tmp_path, "clone", "-q", "--depth", "1", root.as_uri(), os.fspath(shallow))
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    with pytest.raises(BlobResolutionError):
        read_pinned_blob(shallow, ref)


def test_blob_resolution_rejects_grafts(git_blob_fixture):
    root, regular_bytes, commit, _tree = git_blob_fixture
    grafts = root / ".git" / "info" / "grafts"
    grafts.write_text(f"{commit}\n", encoding="ascii")
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    with pytest.raises(BlobResolutionError):
        read_pinned_blob(root, ref)


def test_blob_resolution_enforces_blob_size_limit(
    git_blob_fixture, monkeypatch: pytest.MonkeyPatch
):
    root, regular_bytes, commit, _tree = git_blob_fixture
    monkeypatch.setattr("orchestrator.preregistration.blobref.MAX_BLOB_BYTES", 1)
    ref = BlobRef("regular.txt", commit, hashlib.sha256(regular_bytes).hexdigest())

    with pytest.raises(BlobResolutionError):
        read_pinned_blob(root, ref)


def test_approved_addendum_parses_to_exact_thirteen():
    blob = read_pinned_blob(REPOSITORY_ROOT, ADDENDUM_REF)
    assert preregistration.parse_addendum_fields(blob) == (
        "a01",
        "a02",
        "a03",
        "a04",
        "a05",
        "a06",
        "a07",
        "a08",
        "a09",
        "a10",
        "a11",
        "a12",
        "a13",
    )
    preregistration.require_exact_fields(blob, EXPECTED_FIELDS)


def test_approved_addendum_is_accepted_by_default_exact_fields():
    blob = read_pinned_blob(REPOSITORY_ROOT, ADDENDUM_REF)
    assert preregistration.require_approved_addendum_a_fields(blob) is None


def test_approved_erratum_target_line_digests_are_frozen():
    core = read_pinned_blob(REPOSITORY_ROOT, CORE_REF)
    lines = core.splitlines(keepends=True)
    actual = (
        hashlib.sha256(lines[403]).hexdigest(),
        hashlib.sha256(lines[423]).hexdigest(),
    )
    assert actual == EXPECTED_OPERATION_LINE_SHA256


def test_approved_erratum_composes_to_expected_digest():
    composed = compose_core(
        str(REPOSITORY_ROOT),
        core_ref=CORE_REF,
        erratum_refs=(ERRATUM_REF,),
        expected_composed_sha256=EXPECTED_COMPOSED_SHA256,
    )
    assert composed.composed_sha256 == EXPECTED_COMPOSED_SHA256


def test_module_exports_no_admission_api():
    forbidden = {
        "resolve_effective_preregistration",
        "PreregBinding",
        "submit_pilot",
        "verify_receipt",
    }
    assert forbidden.isdisjoint(preregistration.__all__)
    assert all(not hasattr(preregistration, name) for name in forbidden)
    assert "本 module は投入 gate (admission gate) ではない。" in (
        preregistration.__doc__ or ""
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
