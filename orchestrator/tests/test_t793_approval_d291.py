from __future__ import annotations

import inspect
import subprocess
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

import orchestrator.publication as publication
from orchestrator.preregistration.blobref import BlobRef
from orchestrator.publication.approval_d291 import (
    D291_FOLD_COMMIT,
    D291PayloadError,
    D291ResolutionError,
    _parse_d291_payload,
    _resolve_d291_approvals,
    load_d291_payload,
    require_d291_projection_exact,
    resolve_d291_approvals,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
CANONICAL_D291_FOLD_COMMIT = "b13b7ea840ad51199f40b3a534c9d1cdb422af2e"


@pytest.fixture(scope="module")
def canonical_decisions_blob() -> bytes:
    return subprocess.run(
        ["git", "show", f"{CANONICAL_D291_FOLD_COMMIT}:docs/decisions.md"],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    ).stdout


def test_d291_fold_commit_matches_independent_literal() -> None:
    assert D291_FOLD_COMMIT == CANONICAL_D291_FOLD_COMMIT


def _replace_once(blob: bytes, old: bytes, new: bytes) -> bytes:
    assert blob.count(old) == 1, old
    return blob.replace(old, new, 1)


def _approved_projection() -> dict[str, object]:
    return {
        "p01.candidate_cap": 1,
        "p01.admissible_ordinals": [1],
        "p02.familywise_alpha": Decimal("0.05"),
        "p02.spending.domain": "k = 1, 2, 3, …",
        "p02.spending.alpha_pub_k": "0.05 / (k * (k + 1))",
        "p02.current_study.k": 1,
        "p02.current_study.alpha_pub": Decimal("0.025"),
        "p02.unspent_tail.reclaim": False,
        "p02.unspent_tail.redistribute": False,
    }


def test_p1_real_fp_d291_payload_at_eof_is_accepted(canonical_decisions_blob: bytes) -> None:
    """P1/A6: F_p では D291 が最後の H2 であり、EOF 終端を受理する。"""

    assert b"\n## D292." not in canonical_decisions_blob
    payload = _parse_d291_payload(canonical_decisions_blob)
    assert tuple(role for role, _ in payload.approved_blobs) == (
        "publication_core",
        "source_addendum_b",
    )
    assert payload.pilot_submission == "forbidden"
    assert payload.main_submission == "forbidden"


def test_fixed_public_loader_and_all_role_resolver_accept_canonical_blobs() -> None:
    payload = load_d291_payload(REPOSITORY_ROOT)
    assert payload.document_relation_roles == {
        "source_addendum_b",
        "publication_core",
        "future_publication_addendum_p",
    }
    resolutions = resolve_d291_approvals(REPOSITORY_ROOT)
    assert tuple(resolutions) == ("publication_core", "source_addendum_b")
    assert all(
        resolution.approval_status == "approved_by_canonical_decision"
        and resolution.submission_authority == "not_granted"
        for resolution in resolutions.values()
    )


@pytest.mark.parametrize(
    "mutation",
    (
        lambda blob: _replace_once(blob, b"authority_field_note:\n", b""),
        lambda blob: _replace_once(
            blob,
            (
                'operational_boundary = """\n'
                "この保証は、指定された一つの canonical local main、その Git common directory、\n"
                "tools/dev_wave_land.py が同一 land lock 下で本 payload を fold した履歴、および F_p の\n"
            ).encode(),
            (
                "unexpected_top_level = closed\n\n"
                'operational_boundary = """\n'
                "この保証は、指定された一つの canonical local main、その Git common directory、\n"
                "tools/dev_wave_land.py が同一 land lock 下で本 payload を fold した履歴、および F_p の\n"
            ).encode(),
        ),
        lambda blob: _replace_once(
            blob,
            b"decision_kind = t139-publication-core-approval/v1\n",
            b"decision_kind = t139-publication-core-approval/v1\n"
            b"decision_kind = t139-publication-core-approval/v1\n",
        ),
    ),
    ids=("missing", "extra", "duplicate"),
)
def test_top_level_exact_14_keys_reject_missing_extra_and_duplicate(
    canonical_decisions_blob: bytes,
    mutation,
) -> None:
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(mutation(canonical_decisions_blob))


def test_approved_blobs_rejects_missing_role(canonical_decisions_blob: bytes) -> None:
    block = (
        b"  source_addendum_b\n"
        b"    path   = output/insights/2026-08-11_t139-pubcore-stage2/addendum-b-v2.md\n"
        b"    commit = 25a66d2042a4fff1021e033c23fc2b814a735de9\n"
        b"    sha256 = ad12b60d29bb94ff67c3302b0779cb4765cd1c77768149d7cf6587698febb048\n"
    )
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(_replace_once(canonical_decisions_blob, block, b""))


def test_approved_blobs_rejects_extra_role(canonical_decisions_blob: bytes) -> None:
    marker = b"\napproved_values_for_future_addendum_p:\n"
    extra = (
        b"  future_publication_addendum_p\n"
        b"    path   = output/future.md\n"
        b"    commit = 0000000000000000000000000000000000000000\n"
        b"    sha256 = 0000000000000000000000000000000000000000000000000000000000000000\n"
    )
    mutated = _replace_once(canonical_decisions_blob, marker, b"\n" + extra + marker[1:])
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(mutated)


def test_same_path_with_different_digest_is_rejected(canonical_decisions_blob: bytes) -> None:
    mutated = _replace_once(
        canonical_decisions_blob,
        b"    commit = 66934dda7f28893110a64a2011e213c2bda5e821\n"
        b"    sha256 = ad326dae70584d86470ff861e9bfd517b4f5b8406247f8047ae6cdb3ddabef67",
        b"    commit = 66934dda7f28893110a64a2011e213c2bda5e821\n"
        b"    sha256 = 45d83e7ab471ef9db0aaf9705168a333a8c317de06674fa23ef9164428d03065",
    )
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(mutated)


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (b"note = \xe7\x8b\xac\xe7\xab\x8b study", b"note = \xe7\x8b\xac\xe7\xab\x8b Study"),
        (
            b"    independent_of = publication_core\n",
            b"    independent_of = publication_core\n    unexpected = value\n",
        ),
        (b"    independent_of = publication_core\n", b""),
    ),
    ids=("note_changed", "key_added", "key_deleted"),
)
def test_document_relations_entire_section_is_exact(
    canonical_decisions_blob: bytes,
    old: bytes,
    new: bytes,
) -> None:
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(_replace_once(canonical_decisions_blob, old, new))


@pytest.mark.parametrize(
    ("old", "new"),
    (
        (b"familywise_alpha          = 0.05", b"familywise_alpha          = 0.06"),
        (b"admissible_ordinals = [ 1 ]", b"admissible_ordinals = [ 1, 2 ]"),
        (b"unspent_tail_reclaim      = false", b"unspent_tail_reclaim      = true"),
        (
            b"alpha_pub_k               = 0.05 / (k * (k + 1))",
            b"alpha_pub_k               = 0.05 / (k * (k + 2))",
        ),
    ),
    ids=("decimal", "ordinal_set", "boolean", "canonical_string"),
)
def test_approved_value_comparison_units_reject_mismatch(
    canonical_decisions_blob: bytes,
    old: bytes,
    new: bytes,
) -> None:
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(_replace_once(canonical_decisions_blob, old, new))


def test_numeric_and_canonical_string_allowed_normalization_is_accepted(
    canonical_decisions_blob: bytes,
) -> None:
    mutated = _replace_once(
        canonical_decisions_blob,
        b"alpha_pub                 = 0.025",
        b"alpha_pub                 = 2.5e-2",
    )
    mutated = _replace_once(
        mutated,
        b"spending_domain           = k = 1, 2, 3, \xe2\x80\xa6",
        b"spending_domain           =   k = 1,  2, 3, \xe2\x80\xa6  ",
    )
    _parse_d291_payload(mutated)


def test_value_projection_requires_exact_nine_mapping_rows(
    canonical_decisions_blob: bytes,
) -> None:
    mutated = _replace_once(
        canonical_decisions_blob,
        b"p02.current_k                 <-> p02.current_study.k",
        b"p02.current_k                 <-> p02.current_study.ordinal",
    )
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(mutated)


@pytest.mark.parametrize(
    "field",
    ("pilot_submission", "main_submission"),
)
def test_operational_submission_state_must_remain_forbidden(
    canonical_decisions_blob: bytes,
    field: str,
) -> None:
    old = f"  {field.ljust(17)}= forbidden".encode()
    new = f"  {field.ljust(17)}= allowed".encode()
    with pytest.raises(D291PayloadError):
        _parse_d291_payload(_replace_once(canonical_decisions_blob, old, new))


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("p02.familywise_alpha", Decimal("0.06")),
        ("p01.admissible_ordinals", [1, 2]),
        ("p02.unspent_tail.reclaim", True),
        ("p02.spending.alpha_pub_k", "0.05 / (k * (k + 2))"),
    ),
    ids=("decimal", "ordinal_set", "boolean", "canonical_string"),
)
def test_projection_candidate_rejects_each_comparison_unit(key: str, value: object) -> None:
    projection = _approved_projection()
    projection[key] = value
    with pytest.raises(D291ResolutionError):
        require_d291_projection_exact(REPOSITORY_ROOT, projection)


def test_projection_candidate_accepts_decimal_set_and_whitespace_equivalence() -> None:
    projection = _approved_projection()
    projection["p02.current_study.alpha_pub"] = "2.5e-2"
    projection["p01.admissible_ordinals"] = {1}
    projection["p02.spending.domain"] = "  k = 1,   2, 3, …  "
    assert require_d291_projection_exact(REPOSITORY_ROOT, projection) is None


def test_public_projection_api_rejects_caller_forged_payload_authority() -> None:
    payload = load_d291_payload(REPOSITORY_ROOT)
    forged = replace(
        payload,
        approved_values=(("p01.candidate_cap", Decimal("9")),),
        value_projection=(("p01.candidate_cap", "p01.candidate_cap"),),
    )
    with pytest.raises(TypeError):
        require_d291_projection_exact(forged, {"p01.candidate_cap": 9})


def test_historical_candidate_cannot_be_passed_as_approved() -> None:
    payload = load_d291_payload(REPOSITORY_ROOT)
    candidates = dict(payload.approved_blobs)
    historical = dict(payload.historical_candidates_rejected_for_role)
    candidates["publication_core"] = historical["publication_core"]
    with pytest.raises(D291ResolutionError):
        _resolve_d291_approvals(REPOSITORY_ROOT, candidates=candidates)


@pytest.mark.parametrize("role_change", ("missing", "extra"))
def test_public_resolver_requires_full_exact_role_mapping(role_change: str) -> None:
    payload = load_d291_payload(REPOSITORY_ROOT)
    candidates: dict[str, BlobRef] = dict(payload.approved_blobs)
    if role_change == "missing":
        del candidates["source_addendum_b"]
    else:
        candidates["unexpected"] = next(iter(candidates.values()))
    with pytest.raises(D291ResolutionError):
        _resolve_d291_approvals(REPOSITORY_ROOT, candidates=candidates)


def test_public_api_has_fixed_fold_and_no_single_role_or_boolean_success_api() -> None:
    assert tuple(inspect.signature(load_d291_payload).parameters) == ("repository_root",)
    assert tuple(inspect.signature(require_d291_projection_exact).parameters) == (
        "repository_root",
        "projection",
    )
    assert tuple(inspect.signature(resolve_d291_approvals).parameters) == (
        "repository_root",
    )
    forbidden = {
        "is_submission_allowed",
        "ready_for_main",
        "admitted",
        "can_submit",
        "approval_complete",
    }
    assert forbidden.isdisjoint(publication.__all__)
    assert all(not hasattr(publication, name) for name in forbidden)
    assert "D291ApprovalPayload" not in publication.__all__
    assert "D291RoleResolution" not in publication.__all__
    assert not hasattr(publication, "D291ApprovalPayload")
    assert not hasattr(publication, "D291RoleResolution")
    assert "_parse_d291_payload" not in publication.__all__


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
