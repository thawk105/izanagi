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
    APPROVED_ERRATA,
    DRAFT_ERRATA,
    ComposedDigestMismatchError,
    EmptyErratumSetError,
    LineCountMismatchError,
    LocatorOverlapError,
    OccurrenceCountError,
    OldDigestMismatchError,
    OperationCountError,
    OperationDeltaError,
    ReplacementTextMismatchError,
    UnknownErratumError,
    approved_erratum_ids,
    compose_core,
    parse_erratum,
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
DRAFT_ERRATUM_PATH = REPOSITORY_ROOT / (
    "output/insights/2026-08-10_t139-manifest-w1/"
    "erratum-core-s7-stresscheck.md"
)
DRAFT_ERRATUM_REF = BlobRef(
    path=(
        "output/insights/2026-08-10_t139-manifest-w1/"
        "erratum-core-s7-stresscheck.md"
    ),
    commit="0" * 40,
    sha256="0" * 64,
)
ADDENDUM_REF = BlobRef(
    path="output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md",
    commit="622bd786191d40bda388596fa2adbf119ee84c9a",
    sha256="f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec",
)
EXPECTED_COMPOSED_SHA256 = "d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82"
EXPECTED_TWO_ERRATA_COMPOSED_SHA256 = (
    "dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c"
)
EXPECTED_OPERATION_LINE_SHA256 = (
    "6e87b981b2d3550ea56278a50f9544a86bab575d18de3ea7f3984abdeca5681e",
    "b5e2c7b290c1c21aff84f4b520468df551c9d0e4bd76d2102ace3208b3e1b7d1",
)
EXPECTED_S7_OPERATION_LINE_SHA256 = (
    "225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89"
)
S7_OLD_TEXT = "事前 simulation で較正する"
S7_NEW_TEXT = (
    "事前固定した stress model のもとで名目水準を超えないことを"
    "事前 simulation で確認する。"
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
    section: str = "15",
) -> str:
    old_text = old_line.decode()
    replacement = new_line.decode() if new_line is not None else old_text.replace("a12", "a13")
    digest = old_sha256 or hashlib.sha256(old_line).hexdigest()
    return (
        f"  - index: {index}\n"
        "    locator:\n"
        f'      section: "{section}"\n'
        f'      anchor: "synthetic operation {index}"\n'
        f"      line_number_at_target_commit: {line_number}\n"
        f"    old_sha256: {digest}\n"
        f"{_block_scalar('old_text', old_text.encode())}"
        f"{_block_scalar('new_text', replacement.encode())}"
    )


def _block_scalar(key: str, value: bytes) -> str:
    lines = value.decode().splitlines(keepends=True)
    return f"    {key}: |\n" + "".join(f"      {line}" for line in lines)


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
    replacements = dict(new_line_overrides or {})
    if erratum_id == "t139-core-s7-stresscheck-v1":
        for index, line_number in enumerate(line_numbers, start=1):
            replacements.setdefault(
                index,
                lines[line_number - 1].replace(
                    f"{S7_OLD_TEXT}。".encode(), S7_NEW_TEXT.encode()
                ),
            )
    operations = "".join(
        _operation_yaml(
            index=index,
            line_number=line_number,
            old_line=lines[line_number - 1],
            old_sha256=(old_sha_overrides or {}).get(index),
            new_line=replacements.get(index),
            section="7" if erratum_id == "t139-core-s7-stresscheck-v1" else "15",
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
        "## 4. ignored prose\n"
    ).encode()


def _synthetic_s7_core(*, occurrences: int = 1) -> bytes:
    phrase = f"{S7_OLD_TEXT}。\n"
    lines = ["# synthetic core\n", phrase, "unrelated line\n"]
    if occurrences == 0:
        lines[1] = "no calibration claim here\n"
    elif occurrences == 2:
        lines[2] = phrase
    return "".join(lines).encode()


def _expected_synthetic_composed_sha256(
    core: bytes, line_numbers: tuple[int, ...] = (2, 4)
) -> str:
    lines = core.splitlines(keepends=True)
    for line_number in line_numbers:
        lines[line_number - 1] = lines[line_number - 1].replace(b"a12", b"a13", 1)
    return hashlib.sha256(b"".join(lines)).hexdigest()


def _expected_s7_composed_sha256(
    core: bytes,
    line_numbers: tuple[int, ...] = (2,),
    *,
    new_line_overrides: dict[int, bytes] | None = None,
) -> str:
    lines = core.splitlines(keepends=True)
    for index, line_number in enumerate(line_numbers, start=1):
        replacement = (new_line_overrides or {}).get(index)
        if replacement is None:
            replacement = lines[line_number - 1].replace(
                f"{S7_OLD_TEXT}。".encode(), S7_NEW_TEXT.encode()
            )
        lines[line_number - 1] = replacement
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

    monkeypatch.setattr(
        "orchestrator.preregistration.erratum.read_pinned_blob", fake_read
    )
    return compose_core(
        "unused",
        core_ref=core_ref,
        erratum_refs=(erratum_ref,),
        expected_composed_sha256=(
            expected_composed_sha256
            or (
                _expected_synthetic_composed_sha256(core)
                if b"t139-core-s15-exactkey-v1" in erratum
                else hashlib.sha256(core).hexdigest()
            )
        ),
    )


def _compose_synthetic_errata(
    monkeypatch: pytest.MonkeyPatch,
    core: bytes,
    errata: tuple[bytes, ...],
    *,
    expected_composed_sha256: str,
):
    refs = tuple(
        BlobRef(f"synthetic-{index}.md", "0" * 40, f"{index}" * 64)
        for index in range(1, len(errata) + 1)
    )

    def fake_read(_root: str, ref: BlobRef) -> bytes:
        if ref is CORE_REF:
            return core
        for candidate, blob in zip(refs, errata, strict=True):
            if ref is candidate:
                return blob
        raise AssertionError(ref)

    monkeypatch.setattr("orchestrator.preregistration.erratum.read_pinned_blob", fake_read)
    return compose_core(
        "unused",
        core_ref=CORE_REF,
        erratum_refs=refs,
        expected_composed_sha256=expected_composed_sha256,
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


def test_unknown_erratum_id_fails_closed(monkeypatch: pytest.MonkeyPatch):
    core, _ = _synthetic_core()
    erratum = _synthetic_erratum(core, erratum_id="unknown-erratum-v1")
    with pytest.raises(UnknownErratumError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_synthetic_composed_sha256(core),
        )


def test_s7_erratum_rejects_operation_count_not_one(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    erratum = _synthetic_erratum(
        core, (2, 3), erratum_id="t139-core-s7-stresscheck-v1"
    )
    with pytest.raises(OperationCountError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(core, (2, 3)),
        )


def test_s7_erratum_rejects_old_sha256_mismatch(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    erratum = _synthetic_erratum(
        core,
        (2,),
        old_sha_overrides={1: "0" * 64},
        erratum_id="t139-core-s7-stresscheck-v1",
    )
    with pytest.raises(OldDigestMismatchError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(core),
        )


def test_s7_erratum_rejects_old_text_bytes_mismatch(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    erratum = _synthetic_erratum(
        core, (2,), erratum_id="t139-core-s7-stresscheck-v1"
    ).replace(
        f"{S7_OLD_TEXT}。\n".encode(),
        b"different old text\n",
        1,
    )
    with pytest.raises(OldDigestMismatchError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(core),
        )


def test_s7_erratum_rejects_occurrence_count_not_one(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core(occurrences=2)
    erratum = _synthetic_erratum(
        core, (2,), erratum_id="t139-core-s7-stresscheck-v1"
    )
    with pytest.raises(OccurrenceCountError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(core),
        )


def test_s7_erratum_occurrence_must_bind_to_operation_line(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    erratum = _synthetic_erratum(
        core, (3,), erratum_id="t139-core-s7-stresscheck-v1"
    )
    with pytest.raises(OccurrenceCountError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=hashlib.sha256(core).hexdigest(),
        )


def test_s7_erratum_rejects_new_text_line_count_change(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    erratum = _synthetic_erratum(
        core,
        (2,),
        new_line_overrides={1: b"first replacement line\nsecond replacement line\n"},
        erratum_id="t139-core-s7-stresscheck-v1",
    )
    with pytest.raises(LineCountMismatchError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(
                core,
                new_line_overrides={
                    1: b"first replacement line\nsecond replacement line\n"
                },
            ),
        )


def test_s7_erratum_rejects_strong_calibration_claim(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    replacement = (
        "事前 simulation で cluster level の型 I 誤りを較正済みである。\n"
    ).encode()
    erratum = _synthetic_erratum(
        core,
        (2,),
        new_line_overrides={1: replacement},
        erratum_id="t139-core-s7-stresscheck-v1",
    )
    with pytest.raises(ReplacementTextMismatchError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(
                core, new_line_overrides={1: replacement}
            ),
        )


def test_s7_erratum_rejects_unconstrained_reassurance(
    monkeypatch: pytest.MonkeyPatch,
):
    core = _synthetic_s7_core()
    replacement = "型 I 誤りは問題ない。\n".encode()
    erratum = _synthetic_erratum(
        core,
        (2,),
        new_line_overrides={1: replacement},
        erratum_id="t139-core-s7-stresscheck-v1",
    )
    with pytest.raises(ReplacementTextMismatchError):
        _compose_synthetic(
            monkeypatch,
            core,
            erratum,
            expected_composed_sha256=_expected_s7_composed_sha256(
                core, new_line_overrides={1: replacement}
            ),
        )


def test_draft_erratum_is_not_in_approved_set():
    draft_id = "t139-core-s7-stresscheck-v1"
    approved_id = "t139-core-s15-exactkey-v1"
    assert DRAFT_ERRATA == frozenset({draft_id})
    assert APPROVED_ERRATA == frozenset({approved_id})
    assert approved_erratum_ids() == APPROVED_ERRATA
    assert draft_id not in approved_erratum_ids()
    assert DRAFT_ERRATA.isdisjoint(approved_erratum_ids())
    assert parse_erratum(DRAFT_ERRATUM_PATH.read_bytes()).erratum_id == draft_id


def test_overlapping_locators_rejected(monkeypatch: pytest.MonkeyPatch):
    core = (
        "# synthetic core\n"
        "5. exact fields are `a01`〜`a12` only.\n"
        "unrelated line\n"
        f"The addendum sets `a01`〜`a12`; {S7_OLD_TEXT}。\n"
    ).encode()
    s15_erratum = _synthetic_erratum(core)
    s7_new_text = f"{S7_NEW_TEXT}\n".encode()
    s7_erratum = _synthetic_erratum(
        core,
        (4,),
        new_line_overrides={1: s7_new_text},
        erratum_id="t139-core-s7-stresscheck-v1",
    )
    composed_lines = core.splitlines(keepends=True)
    composed_lines[1] = composed_lines[1].replace(b"a12", b"a13", 1)
    composed_lines[3] = s7_new_text
    with pytest.raises(LocatorOverlapError):
        _compose_synthetic_errata(
            monkeypatch,
            core,
            (s15_erratum, s7_erratum),
            expected_composed_sha256=hashlib.sha256(
                b"".join(composed_lines)
            ).hexdigest(),
        )


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


def test_s7_erratum_target_line_digest_is_frozen():
    core = read_pinned_blob(REPOSITORY_ROOT, CORE_REF)
    actual = hashlib.sha256(core.splitlines(keepends=True)[220]).hexdigest()
    assert actual == EXPECTED_S7_OPERATION_LINE_SHA256


def test_approved_erratum_composes_to_expected_digest():
    composed = compose_core(
        str(REPOSITORY_ROOT),
        core_ref=CORE_REF,
        erratum_refs=(ERRATUM_REF,),
        expected_composed_sha256=EXPECTED_COMPOSED_SHA256,
    )
    assert composed.composed_sha256 == EXPECTED_COMPOSED_SHA256


def test_two_errata_locators_are_disjoint_and_compose_to_expected_digest(
    monkeypatch: pytest.MonkeyPatch,
):
    approved_blob = read_pinned_blob(REPOSITORY_ROOT, ERRATUM_REF)
    draft_blob = DRAFT_ERRATUM_PATH.read_bytes()
    approved = parse_erratum(approved_blob)
    draft = parse_erratum(draft_blob)
    approved_locators = {
        operation.locator.line_number_at_target_commit
        for operation in approved.operations
    }
    draft_locators = {
        operation.locator.line_number_at_target_commit for operation in draft.operations
    }
    assert approved_locators == {404, 424}
    assert draft_locators == {221}
    assert approved_locators.isdisjoint(draft_locators)

    real_read_pinned_blob = read_pinned_blob

    def read_with_draft(_root: str, ref: BlobRef) -> bytes:
        if ref is DRAFT_ERRATUM_REF:
            return draft_blob
        return real_read_pinned_blob(REPOSITORY_ROOT, ref)

    monkeypatch.setattr(
        "orchestrator.preregistration.erratum.read_pinned_blob", read_with_draft
    )
    composed = compose_core(
        str(REPOSITORY_ROOT),
        core_ref=CORE_REF,
        erratum_refs=(ERRATUM_REF, DRAFT_ERRATUM_REF),
        expected_composed_sha256=EXPECTED_TWO_ERRATA_COMPOSED_SHA256,
    )
    assert EXPECTED_TWO_ERRATA_COMPOSED_SHA256 != EXPECTED_COMPOSED_SHA256
    assert composed.composed_sha256 == EXPECTED_TWO_ERRATA_COMPOSED_SHA256


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
