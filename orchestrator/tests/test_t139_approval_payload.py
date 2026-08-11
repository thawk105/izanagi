from __future__ import annotations

from pathlib import Path
import subprocess
import sys

import pytest

from orchestrator.preregistration import approval_payload as approval
from orchestrator.preregistration.blobref import read_pinned_blob


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]

EXPECTED_TRIPLETS = {
    "target_core": (
        "output/insights/2026-08-07_t139-mainrun-design/preregistration.md",
        "88d68f9127b31df5aafc3d59607896626a1652e8",
        "ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9",
    ),
    "addendum_a": (
        "output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md",
        "622bd786191d40bda388596fa2adbf119ee84c9a",
        "f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec",
    ),
    "derivation_map": (
        "output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md",
        "7ec088163dee920f0b8e1e9783faa6e36b22b730",
        "bf5b6783b5a1a0b6c495618fe5292a968e44712d857cf84bdc436dcf027f6025",
    ),
    "erratum_t139_core_s15_exactkey_v1": (
        "output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md",
        "1d235e0e455020cf54e66cf83304961910c369d8",
        "a1abc60ef8e3f4346f61fbdd8282c295f353ca272062af02a856e3c5de9dd6d3",
    ),
    "record_items": (
        "output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md",
        "d0e7645192d56f429fc8d8a04f9c1776d50978d9",
        "61ba2f8b009ab6a17d657a5e3af3ce8a3afb251e3da664fc0117cd46a048a480",
    ),
    "receipt_schema": (
        "output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json",
        "d0e7645192d56f429fc8d8a04f9c1776d50978d9",
        "d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e",
    ),
    "erratum_t139_core_s7_stresscheck_v1": (
        "output/insights/2026-08-11_t139-manifest-land1/erratum-core-s7-stresscheck-v2.md",
        "d0e7645192d56f429fc8d8a04f9c1776d50978d9",
        "deedd71b97640213035c76dac1b22ea15bb21d447991000b0e433de873684df2",
    ),
}
EXPECTED_OPERATIONAL_BOUNDARY = """この保証は、指定された一つの canonical local main、その Git common directory、
tools/dev_wave_land.py を通り同一 land lock 下で取り込まれた予約履歴、およびその全履歴を
毎回再検査する trusted resolver / report の範囲に限る。独立 clone、別 common directory、
権威台帳外の投入、履歴を共有しない writer、同一権限の非協調 writer、canonical main の外で
作られた競合予約は保証しない。"""
EXPECTED_ENTRY_SERIALIZATION = """UTF-8 の RFC 8259 JSON object。key は Unicode code point 昇順、
separators は "," と ":"、挿入空白なし、行内に LF を含まない。
行は末尾 LF で終端し、reservation_entry_sha256 はその LF を含まない
142 bytes に対する SHA-256 である。ledger_blob_sha256 は LF を含む
file 全体 (143 bytes) の SHA-256 である。"""
EXPECTED_LEDGER_INTRODUCTION = """本 payload を fold する land と同一 land lock 内で exact 1 回。
mode は regular (100644)。以後は append-only であり、既存行の編集・
削除・並べ替え・rename/copy・delete-and-recreate を拒否する"""
EXPECTED_RESERVATION_COMMIT = """pin しない。record-items-v2.md §6.7 (7) に従い validator が
「当該行が初めて出現した commit」として全履歴から再導出する"""


@pytest.fixture(scope="module")
def fixed_decisions_bytes() -> bytes:
    return read_pinned_blob(REPOSITORY_ROOT, approval.D282_DECISIONS_REF)


def _target_fence(document: bytes) -> str:
    text = document.decode("utf-8")
    start = text.index("```text\ndecision_kind = t139-preregistration-approval-supersession/v1")
    end = text.index("\n```", start) + len("\n```")
    return text[start:end]


def _mutate_once(document: bytes, old: str, new: str) -> bytes:
    text = document.decode("utf-8")
    fence = _target_fence(document)
    assert text.count(fence) == 1, "target fence"
    assert fence.count(old) == 1, old
    mutated_fence = fence.replace(old, new, 1)
    return text.replace(fence, mutated_fence, 1).encode("utf-8")


def _mutate_document_once(document: bytes, old: str, new: str) -> bytes:
    text = document.decode("utf-8")
    assert text.count(old) == 1, old
    return text.replace(old, new, 1).encode("utf-8")


def _assert_rejected(document: bytes) -> None:
    with pytest.raises(approval.ApprovalPayloadError):
        approval._parse_approval_payload(document)


def test_real_fr_payload_has_exact_approved_values() -> None:
    payload = approval.load_approval_payload(REPOSITORY_ROOT)
    assert payload.forward_supersedes == (
        "D262.approved_blobs.record_items   "
        "(旧 blob は post-F_r manifest の record_items role では非承認)",
        "D263.reason                        "
        "(「同じ core に対する第 2 の erratum が既に承認済みである」の事実文)",
    )
    assert payload.preserved == (
        "D262 の target_core / addendum_a / derivation_map / "
        "erratum(t139-core-s15-exactkey-v1) の承認",
        "D263 の決定本文 (erratum_id 別 validator、未知 ID の fail-closed)",
        "D264 の gate 完成までの 4 名前非 export",
    )
    refs = {"target_core": payload.target_core, **payload.approved_blobs}
    assert len(refs) == 7
    assert set(payload.approved_blobs) == approval.APPROVED_BLOB_ROLES
    assert {
        role: (ref.path, ref.commit, ref.sha256) for role, ref in refs.items()
    } == EXPECTED_TRIPLETS
    assert payload.erratum_application_order == (
        "t139-core-s15-exactkey-v1",
        "t139-core-s7-stresscheck-v1",
    )
    assert payload.composed_sha256 == (
        "e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c"
    )
    assert payload.operational_boundary == EXPECTED_OPERATIONAL_BOUNDARY

    alpha = payload.alpha_reservation
    assert alpha.ledger_path == "output/registry/t139-alpha-reservations.jsonl"
    assert alpha.family_root == "dce4ae4fed6f4fb33747165c5b92c16d01822850"
    assert alpha.ordinal == 1
    assert alpha.entry_canonical_bytes == (
        b'{"family_root":"dce4ae4fed6f4fb33747165c5b92c16d01822850",'
        b'"kind":"alpha_reservation","ordinal":1,'
        b'"schema_version":"t139-alpha-reservation/v1"}'
    )
    assert alpha.reservation_entry_sha256 == (
        "52ba3d2c86f7554d78433a1dec4f3364f1db2b8dd1e6aa0360f4428f93127cf3"
    )
    assert alpha.ledger_blob_sha256 == (
        "38968a7b248af2bce089edc2e37024cb9b1fbe21fc20edb7914d82600579dc65"
    )
    assert alpha.entry_serialization == EXPECTED_ENTRY_SERIALIZATION
    assert alpha.ledger_introduction == EXPECTED_LEDGER_INTRODUCTION
    assert alpha.reservation_commit == EXPECTED_RESERVATION_COMMIT


def test_not_approved_root_has_no_invented_commit(fixed_decisions_bytes: bytes) -> None:
    payload = approval._parse_approval_payload(fixed_decisions_bytes)
    excluded = payload.not_approved_as_record_items_root
    assert excluded.path.endswith("/record-items.md")
    assert excluded.sha256 == (
        "1957026c83db3486a39508a9aae07fd03ff5ac84d4edfc0d24b7051758f78fd3"
    )
    assert excluded.note == (
        "D262 時点の承認記録は改変しない。ただし F_r 以後の T-139 approval manifest において\n"
        "本 blob は record_items role の承認対象ではなく、resolver はこれを拒否しなければならない。"
    )
    assert not hasattr(excluded, "commit")


def test_missing_d282_heading_is_rejected_without_unicode_normalization(
    fixed_decisions_bytes: bytes,
) -> None:
    _assert_rejected(
        _mutate_document_once(fixed_decisions_bytes, "## D282.", "## D２８２.")
    )


def test_duplicate_d282_heading_is_rejected(fixed_decisions_bytes: bytes) -> None:
    heading = "## D282. T-139 の再発行"
    _assert_rejected(
        _mutate_document_once(
            fixed_decisions_bytes, heading, "## D282. duplicate\n\n" + heading
        )
    )


def test_missing_target_fence_is_rejected(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(
        _mutate_document_once(
            fixed_decisions_bytes, "```text\ndecision_kind", "```yaml\ndecision_kind"
        )
    )


def test_duplicate_target_fence_is_rejected(fixed_decisions_bytes: bytes) -> None:
    fence = _target_fence(fixed_decisions_bytes)
    _assert_rejected(
        _mutate_document_once(fixed_decisions_bytes, fence, fence + "\n\n" + fence)
    )


def test_nested_fence_is_rejected(fixed_decisions_bytes: bytes) -> None:
    marker = "decision_kind = t139-preregistration-approval-supersession/v1\n"
    _assert_rejected(
        _mutate_once(fixed_decisions_bytes, marker, marker + "```text\nnested\n```\n")
    )


def test_mismatched_fence_delimiter_length_is_rejected(
    fixed_decisions_bytes: bytes,
) -> None:
    fence = _target_fence(fixed_decisions_bytes)
    _assert_rejected(
        _mutate_document_once(fixed_decisions_bytes, fence, fence[:-3] + "````")
    )


def test_unknown_top_level_key_is_rejected(fixed_decisions_bytes: bytes) -> None:
    marker = "\nforward_supersedes:\n"
    _assert_rejected(
        _mutate_once(fixed_decisions_bytes, marker, "\nunknown_key = value\n" + marker)
    )


def test_missing_top_level_key_is_rejected(fixed_decisions_bytes: bytes) -> None:
    line = (
        "composed_sha256           = "
        "e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c\n"
    )
    _assert_rejected(_mutate_once(fixed_decisions_bytes, line, ""))


def test_duplicate_top_level_key_is_rejected(fixed_decisions_bytes: bytes) -> None:
    line = (
        "composed_sha256           = "
        "e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c"
    )
    _assert_rejected(_mutate_once(fixed_decisions_bytes, line, line + "\n" + line))


def test_approved_blob_role_count_not_six_is_rejected(
    fixed_decisions_bytes: bytes,
) -> None:
    block = (
        "  addendum_a\n"
        "    path   = output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md\n"
        "    commit = 622bd786191d40bda388596fa2adbf119ee84c9a\n"
        "    sha256 = f7db96ce8ecb12359fedf56baea24939c629d4d16a1ec167c183425ea198cfec\n"
    )
    _assert_rejected(_mutate_once(fixed_decisions_bytes, block, ""))


def test_unknown_approved_blob_role_is_rejected(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(_mutate_once(fixed_decisions_bytes, "  addendum_a\n", "  unknown_role\n"))


def test_duplicate_approved_blob_role_is_rejected(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(_mutate_once(fixed_decisions_bytes, "  derivation_map\n", "  addendum_a\n"))


def test_triplet_commit_must_be_40_lowercase_hex(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(
        _mutate_once(
            fixed_decisions_bytes,
            "commit = 88d68f9127b31df5aafc3d59607896626a1652e8",
            "commit = 88d68f9127b31df5aafc3d59607896626a1652e",
        )
    )


def test_triplet_sha256_must_be_64_lowercase_hex(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(
        _mutate_once(
            fixed_decisions_bytes,
            "sha256 = ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9",
            "sha256 = Ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9",
        )
    )


def test_erratum_application_order_must_match_approval(
    fixed_decisions_bytes: bytes,
) -> None:
    old = "[t139-core-s15-exactkey-v1, t139-core-s7-stresscheck-v1]"
    new = "[t139-core-s7-stresscheck-v1, t139-core-s15-exactkey-v1]"
    _assert_rejected(_mutate_once(fixed_decisions_bytes, old, new))


def test_not_approved_root_commit_key_is_rejected(fixed_decisions_bytes: bytes) -> None:
    marker = "not_approved_as_record_items_root:\n"
    _assert_rejected(
        _mutate_once(fixed_decisions_bytes, marker, marker + "  commit = " + "0" * 40 + "\n")
    )


def test_alpha_reservation_missing_descriptor_key_is_rejected(
    fixed_decisions_bytes: bytes,
) -> None:
    _assert_rejected(_mutate_once(fixed_decisions_bytes, "  ordinal                  = 1\n", ""))


def test_alpha_reservation_commit_must_remain_unpinned(
    fixed_decisions_bytes: bytes,
) -> None:
    old = "reservation_commit       = pin しない。"
    _assert_rejected(
        _mutate_once(
            fixed_decisions_bytes, old, "reservation_commit       = 0" + "0" * 39
        )
    )


def test_non_utf8_document_is_rejected(fixed_decisions_bytes: bytes) -> None:
    _assert_rejected(fixed_decisions_bytes + b"\xff")


def test_module_import_has_no_git_side_effect() -> None:
    code = (
        "import subprocess; from unittest import mock; "
        "p=mock.patch.object(subprocess, 'run', side_effect=AssertionError('Git on import')); "
        "p.start(); import orchestrator.preregistration.approval_payload; p.stop()"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPOSITORY_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
        timeout=15,
    )
    assert completed.returncode == 0, completed.stderr


def test_parser_api_is_not_exported_from_package() -> None:
    import orchestrator.preregistration as preregistration

    assert "ApprovalPayload" not in preregistration.__all__
    assert not hasattr(preregistration, "ApprovalPayload")


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
