# -*- coding: utf-8 -*-
"""Tests for the repository-local P3 B-4 admission record validator."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest.mock

_HERE = Path(__file__).resolve().parent
_ORCH = _HERE.parent
sys.path.insert(0, str(_ORCH.parent))

from orchestrator.campaign import p3_b4_admission_record as A  # noqa: E402


_MODEL = "claude-opus-5"
_PROMPT = "1" * 64
_PROJECTION = "2" * 64
_SCHEMA_VERSION = "p3-b4-prerun-admission/v1"
_PREREGISTRATION_REPOSITORY_PATH = (
    "docs/phase3-b4-reflux-ablation-preregistration.md"
)
_SECTION5_LABELS = (
    "対象 driver と軸",
    "赤 precursor の母集合 (workload・赤形状・初期 proposal)",
    "アームあたり block 数 n と検定単位",
    "primary outcome の演算定義 (純関数)",
    "floor (対象動作点で再実測した between-run floor) の artifact パスと hash",
    "校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash",
    "総計測予算 (role query 数・build/verify/bench admission 数・累積 bench 秒) と arm ごとの上限",
    "env_tag (実測環境)",
    "model snapshot / prompt hash / projection hash",
    "実行責任者・開始時刻",
)
_EXPECTATION_ROW_LABEL = "model snapshot / prompt hash / projection hash"
_SECTION5_ERROR = (
    "[admission-preregistration] section 5 fixed table requires nonempty "
    "source cells and no reserved sentinel; types, meanings, and rendered "
    "non-emptiness are not checked"
)


def _raises(error_type, callable_, *, exact: str | None = None):
    try:
        callable_()
    except error_type as exc:
        if exact is not None:
            assert str(exc) == exact
        return exc
    raise AssertionError(f"expected {error_type.__name__}")


def _canonical(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _section5_document(
    *,
    model: str = _MODEL,
    prompt: str = _PROMPT,
    projection: str = _PROJECTION,
    value_overrides: dict[str, str] | None = None,
) -> bytes:
    values = {
        label: f"fixture-value-{index}"
        for index, label in enumerate(_SECTION5_LABELS, start=1)
    }
    values[_EXPECTATION_ROW_LABEL] = (
        f"expected_claude_model_snapshot={model}; "
        f"expected_effective_critic_prompt_sha256={prompt}; "
        "expected_closed_critic_projection_closure_sha256="
        f"{projection}"
    )
    if value_overrides:
        values.update(value_overrides)
    rows = [
        "# Fixture preregistration",
        "",
        "## 5. 実走前に数値で埋める欄",
        "",
        "|欄|値|",
        "|---|---|",
    ]
    rows.extend(f"|{label}|{values[label]}|" for label in _SECTION5_LABELS)
    rows.extend(("", "### 5.1 欄別の解除条件", "", "fixture"))
    return "\n".join(rows).encode("utf-8")


def _record_value(
    *,
    content_commit: str,
    content_sha256: str,
    model: str = _MODEL,
    prompt: str = _PROMPT,
    projection: str = _PROJECTION,
):
    return {
        "schema_version": _SCHEMA_VERSION,
        "preregistration_binding": {
            "repository_path": _PREREGISTRATION_REPOSITORY_PATH,
            "content_commit": content_commit,
            "content_sha256": content_sha256,
        },
        "closed_critic_expectations": {
            "expected_claude_model_snapshot": model,
            "expected_effective_critic_prompt_sha256": prompt,
            "expected_closed_critic_projection_closure_sha256": projection,
        },
    }


def _git(repository: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    completed = subprocess.run(
        [
            "/usr/bin/git",
            "-c",
            "commit.gpgsign=false",
            "-C",
            str(repository),
            *args,
        ],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    return completed.stdout


def _init_repository() -> Path:
    repository = Path(tempfile.mkdtemp(prefix="izanagi-b4-admission-git-"))
    _git(repository, "init")
    _git(repository, "config", "user.name", "B4 Admission Test")
    _git(repository, "config", "user.email", "b4-admission@example.invalid")
    return repository


@dataclass
class _CommittedFixture:
    repository: Path
    document_path: Path
    record_path: Path
    document_bytes: bytes
    content_commit: str
    record_value: dict


def _committed_fixture(
    *,
    model: str = _MODEL,
    prompt: str = _PROMPT,
    projection: str = _PROJECTION,
) -> _CommittedFixture:
    repository = _init_repository()
    document_path = repository / _PREREGISTRATION_REPOSITORY_PATH
    document_path.parent.mkdir(parents=True)
    document_bytes = _section5_document(
        model=model,
        prompt=prompt,
        projection=projection,
    )
    document_path.write_bytes(document_bytes)
    _git(repository, "add", _PREREGISTRATION_REPOSITORY_PATH)
    _git(repository, "commit", "-m", "document")
    content_commit = _git(repository, "rev-parse", "HEAD").decode().strip()
    assert len(content_commit) == 40
    value = _record_value(
        content_commit=content_commit,
        content_sha256=hashlib.sha256(document_bytes).hexdigest(),
        model=model,
        prompt=prompt,
        projection=projection,
    )
    record_path = repository / "admission.json"
    record_path.write_bytes(_canonical(value))
    _git(repository, "add", "admission.json")
    _git(repository, "commit", "-m", "record")
    return _CommittedFixture(
        repository=repository,
        document_path=document_path,
        record_path=record_path,
        document_bytes=document_bytes,
        content_commit=content_commit,
        record_value=value,
    )


def test_canonical_schema_accepts_exact_bytes_and_rejects_noncanonical_shapes():
    value = _record_value(
        content_commit="a" * 40,
        content_sha256="b" * 64,
    )
    parsed = A._parse_canonical_record(_canonical(value))
    assert parsed.expected_claude_model_snapshot == _MODEL

    variants = []
    unknown = dict(value)
    unknown["unknown"] = None
    variants.append(_canonical(unknown))
    missing = dict(value)
    missing.pop("schema_version")
    variants.append(_canonical(missing))
    boolean = dict(value)
    boolean["schema_version"] = True
    variants.append(_canonical(boolean))
    variants.append(_canonical(value) + b"\n")
    variants.append(b"\xef\xbb\xbf" + _canonical(value))
    canonical_text = _canonical(value).decode("utf-8")
    duplicate = canonical_text.replace(
        '"schema_version":"p3-b4-prerun-admission/v1"',
        '"schema_version":"p3-b4-prerun-admission/v1",'
        '"schema_version":"p3-b4-prerun-admission/v1"',
    ).encode("utf-8")
    variants.append(duplicate)
    for raw in variants:
        _raises(A._RecordSchemaFailure, lambda raw=raw: A._parse_canonical_record(raw))


def test_section5_source_cells_exclude_only_registered_sentinels_and_bind_three_values():
    document = _section5_document()
    A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
        document,
        expected_claude_model_snapshot=_MODEL,
        expected_effective_critic_prompt_sha256=_PROMPT,
        expected_closed_critic_projection_closure_sha256=_PROJECTION,
    )

    for label, value in (
        (_SECTION5_LABELS[0], ""),
        (_SECTION5_LABELS[1], "TBD after calibration"),
        (_SECTION5_LABELS[2], "x"),
        (_SECTION5_LABELS[3], "N/A"),
        (_SECTION5_LABELS[4], "status: TBD"),
    ):
        rejected = _section5_document(value_overrides={label: value})
        _raises(
            A.B4AdmissionRecordError,
            lambda rejected=rejected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    rejected,
                    expected_claude_model_snapshot=_MODEL,
                    expected_effective_critic_prompt_sha256=_PROMPT,
                    expected_closed_critic_projection_closure_sha256=_PROJECTION,
                )
            ),
            exact=_SECTION5_ERROR,
        )

    duplicate_row = document.replace(
        f"|{_SECTION5_LABELS[1]}|fixture-value-2|".encode("utf-8"),
        f"|{_SECTION5_LABELS[0]}|fixture-value-2|".encode("utf-8"),
    )
    _raises(
        A.B4AdmissionRecordError,
        lambda: (
            A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                duplicate_row,
                expected_claude_model_snapshot=_MODEL,
                expected_effective_critic_prompt_sha256=_PROMPT,
                expected_closed_critic_projection_closure_sha256=_PROJECTION,
            )
        ),
        exact=_SECTION5_ERROR,
    )

    for field, expected, actual_document in (
        (
            "expected_claude_model_snapshot",
            _MODEL,
            _section5_document(model="claude-opus-other"),
        ),
        (
            "expected_effective_critic_prompt_sha256",
            _PROMPT,
            _section5_document(prompt="3" * 64),
        ),
        (
            "expected_closed_critic_projection_closure_sha256",
            _PROJECTION,
            _section5_document(projection="4" * 64),
        ),
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda actual_document=actual_document, field=field, expected=expected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    actual_document,
                    expected_claude_model_snapshot=(
                        expected if field == "expected_claude_model_snapshot" else _MODEL
                    ),
                    expected_effective_critic_prompt_sha256=(
                        expected
                        if field == "expected_effective_critic_prompt_sha256"
                        else _PROMPT
                    ),
                    expected_closed_critic_projection_closure_sha256=(
                        expected
                        if field
                        == "expected_closed_critic_projection_closure_sha256"
                        else _PROJECTION
                    ),
                )
            ),
            exact=f"[admission-mismatch] {field}",
        )


def test_section5_ordinary_words_with_na_and_unregistered_source_values_pass():
    for value in (
        "final",
        "internal",
        "signature",
        "snapshot",
        "担当者=NA太郎",
        "expected_claude_model_snapshot=claude-opus-5",
        "pending",
        "未確定",
        "<!-- -->",
        "&nbsp;",
    ):
        document = _section5_document(
            value_overrides={_SECTION5_LABELS[0]: value}
        )
        A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
            document,
            expected_claude_model_snapshot=_MODEL,
            expected_effective_critic_prompt_sha256=_PROMPT,
            expected_closed_critic_projection_closure_sha256=_PROJECTION,
        )


def test_section5_commonmark_fence_openers_and_marker_lengths():
    document = _section5_document()
    invalid_backtick_opener = b"\x60\x60\x60meta\x60tag\n\n" + document
    closed_only_by_outer_marker = (
        b"````markdown\ninside\n```\n````\n\n" + document
    )
    for accepted in (invalid_backtick_opener, closed_only_by_outer_marker):
        A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
            accepted,
            expected_claude_model_snapshot=_MODEL,
            expected_effective_critic_prompt_sha256=_PROMPT,
            expected_closed_critic_projection_closure_sha256=_PROJECTION,
        )

    for rejected in (
        b"```markdown\n" + document + b"\n```",
        b"~~~meta`tag\n" + document + b"\n~~~",
        document.replace(b"## 5.", b"    ## 5.", 1),
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda rejected=rejected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    rejected,
                    expected_claude_model_snapshot=_MODEL,
                    expected_effective_critic_prompt_sha256=_PROMPT,
                    expected_closed_critic_projection_closure_sha256=_PROJECTION,
                )
            ),
            exact=_SECTION5_ERROR,
        )


def test_section5_rejects_html_commented_region_but_accepts_comment_outside():
    document = _section5_document()
    unrelated_comment = b"<!--\nunrelated\n-->\n\n" + document
    A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
        unrelated_comment,
        expected_claude_model_snapshot=_MODEL,
        expected_effective_critic_prompt_sha256=_PROMPT,
        expected_closed_critic_projection_closure_sha256=_PROJECTION,
    )

    commented_section = b"<!--\n" + document + b"\n-->"
    _raises(
        A.B4AdmissionRecordError,
        lambda: (
            A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                commented_section,
                expected_claude_model_snapshot=_MODEL,
                expected_effective_critic_prompt_sha256=_PROMPT,
                expected_closed_critic_projection_closure_sha256=_PROJECTION,
            )
        ),
        exact=_SECTION5_ERROR,
    )


def test_section5_accepts_one_leading_bom_and_rejects_bom_hidden_fence():
    document = _section5_document()
    section5 = document[document.index(b"## 5.") :]
    A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
        b"\xef\xbb\xbf" + section5,
        expected_claude_model_snapshot=_MODEL,
        expected_effective_critic_prompt_sha256=_PROMPT,
        expected_closed_critic_projection_closure_sha256=_PROJECTION,
    )

    for rejected in (
        b"\xef\xbb\xbf```markdown\n" + document + b"\n```",
        b"\xef\xbb\xbf\xef\xbb\xbf" + section5,
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda rejected=rejected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    rejected,
                    expected_claude_model_snapshot=_MODEL,
                    expected_effective_critic_prompt_sha256=_PROMPT,
                    expected_closed_critic_projection_closure_sha256=_PROJECTION,
                )
            ),
            exact=_SECTION5_ERROR,
        )


def test_section5_known_over_rejection_for_literal_comment_openers():
    """These literal comment-opener cases are a known over-rejection."""
    document = _section5_document()
    for rejected in (
        b"# Literal `<!--` token\n\n" + document,
        b"    <!--\n\n" + document,
        b"\t<!--\n\n" + document,
        b"\\<!-- literal\n\n" + document,
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda rejected=rejected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    rejected,
                    expected_claude_model_snapshot=_MODEL,
                    expected_effective_critic_prompt_sha256=_PROMPT,
                    expected_closed_critic_projection_closure_sha256=_PROJECTION,
                )
            ),
            exact=_SECTION5_ERROR,
        )


def test_section5_rejects_fenced_region_nfkc_sentinel_and_format_character():
    document = _section5_document()
    fenced = b"```markdown\n" + document.replace(
        b"\n\nfixture", b"\n```\n\nfixture"
    )
    for rejected in (
        fenced,
        _section5_document(
            value_overrides={_SECTION5_LABELS[0]: "ＴＢＤ"}
        ),
        _section5_document(
            value_overrides={_SECTION5_LABELS[0]: "T\u200bBD"}
        ),
    ):
        _raises(
            A.B4AdmissionRecordError,
            lambda rejected=rejected: (
                A.assert_section5_fixed_table_has_nonempty_source_cells_and_no_reserved_sentinel(
                    rejected,
                    expected_claude_model_snapshot=_MODEL,
                    expected_effective_critic_prompt_sha256=_PROMPT,
                    expected_closed_critic_projection_closure_sha256=_PROJECTION,
                )
            ),
            exact=_SECTION5_ERROR,
        )


def test_committed_record_and_current_document_blob_use_fixed_git_env_allowlist():
    fixture = _committed_fixture()
    forged = _init_repository()
    with unittest.mock.patch.dict(
        os.environ,
        {
            "GIT_DIR": str(forged / ".git"),
            "GIT_OBJECT_DIRECTORY": str(forged / ".git" / "objects"),
            "GIT_ALTERNATE_OBJECT_DIRECTORIES": str(
                forged / ".git" / "objects"
            ),
            "GIT_CONFIG_PARAMETERS": "'core.repositoryformatversion=99'",
            "GIT_CONFIG_GLOBAL": str(forged / "global-config"),
            "GIT_CONFIG_SYSTEM": str(forged / "system-config"),
            "PATH": str(forged),
            "LD_PRELOAD": str(forged / "interpose.so"),
            "LD_LIBRARY_PATH": str(forged / "libraries"),
            "HOME": str(forged / "home"),
            "XDG_CONFIG_HOME": str(forged / "xdg"),
            "LANG": "forged_LOCALE",
            "LC_ALL": "forged_LOCALE",
        },
    ):
        verified = A.verify_b4_admission_record(
            fixture.record_path,
            repository_root=fixture.repository,
        )
        assert A._git_environment() == {
            "GIT_ATTR_NOSYSTEM": "1",
            "GIT_CONFIG_GLOBAL": "/dev/null",
            "GIT_CONFIG_NOSYSTEM": "1",
            "GIT_CONFIG_SYSTEM": "/dev/null",
            "GIT_NO_REPLACE_OBJECTS": "1",
        }
    assert verified.admission_record_repository_path == "admission.json"
    assert verified.admission_record_commit == _git(
        fixture.repository, "rev-parse", "HEAD"
    ).decode().strip()
    assert verified.preregistration_content_commit == fixture.content_commit
    assert verified.preregistration_content_sha256 == hashlib.sha256(
        fixture.document_bytes
    ).hexdigest()


def test_missing_untracked_staged_or_worktree_changed_record_is_rejected_at_head():
    fixture = _committed_fixture()
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            fixture.repository / "missing.json",
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is unavailable",
    )

    untracked = fixture.repository / "untracked.json"
    untracked.write_bytes(fixture.record_path.read_bytes())
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            untracked,
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is not committed at execution HEAD",
    )

    original = fixture.record_path.read_bytes()
    fixture.record_path.write_bytes(original + b"\n")
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            fixture.record_path,
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is not committed at execution HEAD",
    )
    fixture.record_path.write_bytes(original)
    staged_value = dict(fixture.record_value)
    staged_value["schema_version"] = "p3-b4-prerun-admission/changed"
    fixture.record_path.write_bytes(_canonical(staged_value))
    _git(fixture.repository, "add", "admission.json")
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            fixture.record_path,
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is not committed at execution HEAD",
    )


def test_document_binding_rejects_nonancestor_hash_and_head_blob_differences():
    nonancestor = _committed_fixture()
    document_tree = _git(
        nonancestor.repository,
        "rev-parse",
        f"{nonancestor.content_commit}^{{tree}}",
    ).decode().strip()
    isolated_commit = _git(
        nonancestor.repository,
        "commit-tree",
        document_tree,
        input_bytes=b"isolated document\n",
    ).decode().strip()
    value = _record_value(
        content_commit=isolated_commit,
        content_sha256=hashlib.sha256(nonancestor.document_bytes).hexdigest(),
    )
    nonancestor.record_path.write_bytes(_canonical(value))
    _git(nonancestor.repository, "add", "admission.json")
    _git(nonancestor.repository, "commit", "-m", "nonancestor record")
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            nonancestor.record_path,
            repository_root=nonancestor.repository,
        ),
        exact=(
            "[admission-preregistration] document binding is not verifiable"
        ),
    )

    bad_hash = _committed_fixture()
    value = dict(bad_hash.record_value)
    value["preregistration_binding"] = dict(value["preregistration_binding"])
    value["preregistration_binding"]["content_sha256"] = "f" * 64
    bad_hash.record_path.write_bytes(_canonical(value))
    _git(bad_hash.repository, "add", "admission.json")
    _git(bad_hash.repository, "commit", "-m", "bad hash")
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            bad_hash.record_path,
            repository_root=bad_hash.repository,
        ),
        exact=(
            "[admission-preregistration] document binding is not verifiable"
        ),
    )

    stale = _committed_fixture()
    stale.document_path.write_bytes(stale.document_bytes + b"\nnew HEAD text\n")
    _git(stale.repository, "add", _PREREGISTRATION_REPOSITORY_PATH)
    _git(stale.repository, "commit", "-m", "new document")
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            stale.record_path,
            repository_root=stale.repository,
        ),
        exact=(
            "[admission-preregistration] document binding is not verifiable"
        ),
    )


def test_record_path_rejects_symlink_components_and_git_control_paths():
    fixture = _committed_fixture()
    directory = fixture.repository / "record-directory"
    directory.mkdir()
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            directory,
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is unavailable",
    )
    link = fixture.repository / "record-link.json"
    link.symlink_to(fixture.record_path)
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            link,
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is unavailable",
    )
    directory_link = fixture.repository / "directory-link"
    directory_link.symlink_to(fixture.repository, target_is_directory=True)
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            directory_link / "admission.json",
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is unavailable",
    )
    _raises(
        A.B4AdmissionRecordError,
        lambda: A.verify_b4_admission_record(
            fixture.repository / ".git" / "HEAD",
            repository_root=fixture.repository,
        ),
        exact="[admission-record] record is unavailable",
    )


if __name__ == "__main__":
    import traceback

    functions = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_")
    ]
    failures = 0
    for function in functions:
        try:
            function()
            print(f"[PASS] {function.__name__}")
        except Exception:
            failures += 1
            print(f"[FAIL] {function.__name__}")
            traceback.print_exc()
    print(f"\n{len(functions) - failures}/{len(functions)} passed")
    raise SystemExit(1 if failures else 0)
