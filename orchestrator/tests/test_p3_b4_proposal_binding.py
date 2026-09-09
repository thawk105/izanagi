"""Bootstrap proposal-to-registry binding tests for all formal B-4 drivers."""
from __future__ import annotations

import builtins
from dataclasses import replace
import json
import os
from pathlib import Path
from unittest import mock

import pytest

from orchestrator.campaign import buildcache
from orchestrator.campaign import loop as campaign_loop
from orchestrator.campaign import p2_2
from orchestrator.campaign import p3_b4_launcher as B4L
from orchestrator.campaign import p3_s4_loop as L
from orchestrator.campaign import p3_s4_loop_sort as S
from orchestrator.campaign import p3_s4_loop_trigger_gating as T
from orchestrator.campaign import patchharness
from orchestrator.campaign import site_policy
from orchestrator.campaign import wal
from p3_b4_proposal_binding_support import (
    issue_proposal_binding_fixture,
    proposal_document,
)


_DRIVERS = {
    "base": (L, L.load_proposal_file),
    "sort": (S, S.load_proposal_file),
    "trigger": (T, T.load_proposal_file),
}


def _write_document(path: Path, document: dict[str, object]) -> None:
    path.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")


def _binding_kwargs(binding) -> dict[str, object]:
    return {
        "b4_reflux_ablation": True,
        "b4_prerun_publication": binding.publication.publication_root,
        "b4_attempt_id": binding.attempt_id,
    }


def test_canonical_identity_distinguishes_int_float_and_excludes_receipt() -> None:
    integer = {"value": 1, "label": "同じ表記ではない"}
    floating = {"label": "同じ表記ではない", "value": 1.0}
    assert L.canonical_b4_proposal_sha256(integer) != (
        L.canonical_b4_proposal_sha256(floating)
    )
    with_receipt = {
        **integer,
        L.B4_PROPOSAL_RECEIPT_SHA256_KEY: "a" * 64,
    }
    assert L.canonical_b4_proposal_sha256(with_receipt) == (
        L.canonical_b4_proposal_sha256(integer)
    )
    with pytest.raises(L.B4ProtocolError, match="no canonical JSON hash"):
        L.canonical_b4_proposal_sha256({"value": float("nan")})


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_matching_bootstrap_accepts_reordered_spaced_unicode_spelling(
    driver_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _module, loader = _DRIVERS[driver_kind]
    document = proposal_document(driver_kind)
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind=driver_kind,
        document=document,
    )
    proposal_path = tmp_path / "proposal.json"
    reordered = {key: document[key] for key in reversed(tuple(document))}
    proposal_path.write_text(
        json.dumps(reordered, ensure_ascii=True, indent=3), encoding="utf-8"
    )
    gate_spy = mock.Mock(wraps=L.require_b4_proposal_registry_binding)
    monkeypatch.setattr(L, "require_b4_proposal_registry_binding", gate_spy)

    loaded = loader(str(proposal_path), **_binding_kwargs(binding))

    assert len(loaded) == (3 if driver_kind == "base" else 4)
    gate_spy.assert_called_once()
    assert gate_spy.call_args.kwargs["driver_kind"] == driver_kind


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_registry_attempt_outside_analysis_manifest_rejects(
    driver_kind: str,
    tmp_path: Path,
) -> None:
    _module, loader = _DRIVERS[driver_kind]
    document = proposal_document(driver_kind)
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind=driver_kind,
        document=document,
        attempt_count=202,
        bound_attempt_index=201,
    )
    publication = binding.publication
    registry_only = publication.registry.scheduled_attempts[201]
    assert len(publication.registry.scheduled_attempts) == 202
    assert registry_only.attempt_id == binding.attempt_id
    assert registry_only.driver == driver_kind
    assert registry_only.initial_proposal_sha256 == (
        L.canonical_b4_proposal_sha256(document)
    )
    assert registry_only.attempt_id not in {
        row.attempt_id for row in publication.manifest.rows
    }
    proposal_path = tmp_path / "proposal.json"
    _write_document(proposal_path, document)

    with pytest.raises(L.B4ProtocolError, match="analysis manifest.*membership"):
        loader(
            str(proposal_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=binding.publication.publication_root,
            b4_attempt_id=registry_only.attempt_id,
        )


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_same_publication_and_attempt_reject_schema_valid_proposal_mutation(
    driver_kind: str,
    tmp_path: Path,
) -> None:
    _module, loader = _DRIVERS[driver_kind]
    registered = proposal_document(driver_kind, variant=20)
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind=driver_kind,
        document=registered,
    )
    proposal_path = tmp_path / "mutated-proposal.json"
    _write_document(proposal_path, proposal_document(driver_kind, variant=21))

    with pytest.raises(L.B4ProtocolError, match="canonical hash differs"):
        loader(str(proposal_path), **_binding_kwargs(binding))


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_receipt_and_closed_schema_gates_precede_registry_binding(
    driver_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _module, loader = _DRIVERS[driver_kind]
    gate_spy = mock.Mock(
        side_effect=AssertionError("registry binding ran before existing gates")
    )
    monkeypatch.setattr(L, "require_b4_proposal_registry_binding", gate_spy)
    binding_args = {
        "b4_prerun_publication": tmp_path / "unopened-publication",
        "b4_attempt_id": "attempt-0000",
    }

    receipt_mismatch = {
        **proposal_document(driver_kind),
        L.B4_PROPOSAL_RECEIPT_SHA256_KEY: "b" * 64,
    }
    receipt_path = tmp_path / "receipt-mismatch.json"
    _write_document(receipt_path, receipt_mismatch)
    with pytest.raises(L.B4ProtocolError, match="differs from terminal"):
        loader(
            str(receipt_path),
            b4_reflux_ablation=True,
            b4_closed_critic_receipt_sha256="a" * 64,
            **binding_args,
        )

    bad_schema = {**proposal_document(driver_kind), "unexpected": True}
    bad_schema_path = tmp_path / "bad-schema.json"
    _write_document(bad_schema_path, bad_schema)
    with pytest.raises(ValueError, match="unknown"):
        loader(
            str(bad_schema_path),
            b4_reflux_ablation=True,
            **binding_args,
        )
    gate_spy.assert_not_called()


def test_bootstrap_binding_missing_halves_empty_values_and_load_failure_reject(
    tmp_path: Path,
) -> None:
    document = proposal_document("base")
    proposal_path = tmp_path / "proposal.json"
    _write_document(proposal_path, document)
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind="base",
        document=document,
    )
    root = binding.publication.publication_root
    invalid_pairs = (
        (None, None),
        (root, None),
        (None, binding.attempt_id),
        ("", binding.attempt_id),
        (root, ""),
    )
    for publication_root, attempt_id in invalid_pairs:
        with pytest.raises(L.B4ProtocolError):
            L.load_proposal_file(
                str(proposal_path),
                b4_reflux_ablation=True,
                b4_prerun_publication=publication_root,
                b4_attempt_id=attempt_id,
            )

    with pytest.raises(
        L.B4ProtocolError, match="publication load failed"
    ) as missing_publication:
        L.load_proposal_file(
            str(proposal_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=tmp_path / "missing-publication",
            b4_attempt_id=binding.attempt_id,
        )
    assert missing_publication.value.__cause__ is not None
    with pytest.raises(L.B4ProtocolError, match="publication load failed"):
        L.load_proposal_file(
            str(proposal_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=Path("relative-publication"),
            b4_attempt_id=binding.attempt_id,
        )


def test_unknown_duplicate_invalid_hash_and_driver_mismatch_reject(
    tmp_path: Path,
) -> None:
    base_document = proposal_document("base")
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind="base",
        document=base_document,
    )
    base_path = tmp_path / "base.json"
    _write_document(base_path, base_document)
    with pytest.raises(L.B4ProtocolError, match="exactly one"):
        L.load_proposal_file(
            str(base_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=binding.publication.publication_root,
            b4_attempt_id="absent-attempt",
        )

    loaded = binding.publication.registry.scheduled_attempts[0]
    with pytest.raises(L.B4ProtocolError, match="exactly one"):
        L._require_b4_registry_attempt_hash(
            (loaded, loaded), loaded.attempt_id, driver_kind="base"
        )
    invalid_hash_row = replace(loaded, initial_proposal_sha256="g" * 64)
    with pytest.raises(L.B4ProtocolError, match="64 lowercase hex"):
        L._require_b4_registry_attempt_hash(
            (invalid_hash_row,), loaded.attempt_id, driver_kind="base"
        )
    corrupt_binding = issue_proposal_binding_fixture(
        tmp_path / "corrupt-fixture",
        driver_kind="base",
        document=base_document,
        label="corrupt",
    )
    registry_path = Path(corrupt_binding.publication.registry_path)
    registry_text = registry_path.read_text(encoding="utf-8")
    expected_hash = loaded.initial_proposal_sha256
    corrupt_text = registry_text.replace(expected_hash, "g" * 64, 1)
    assert corrupt_text != registry_text
    registry_path.write_text(corrupt_text, encoding="utf-8")
    with pytest.raises(L.B4ProtocolError, match="publication load failed"):
        L.load_proposal_file(
            str(base_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=corrupt_binding.publication.publication_root,
            b4_attempt_id=corrupt_binding.attempt_id,
        )
    duplicate_binding = issue_proposal_binding_fixture(
        tmp_path / "duplicate-fixture",
        driver_kind="base",
        document=base_document,
        label="duplicate",
    )
    duplicate_registry_path = Path(duplicate_binding.publication.registry_path)
    duplicate_registry_text = duplicate_registry_path.read_text(encoding="utf-8")
    second_attempt_id = (
        duplicate_binding.publication.registry.scheduled_attempts[1].attempt_id
    )
    duplicate_registry_text = duplicate_registry_text.replace(
        f'"attempt_id":"{second_attempt_id}"',
        f'"attempt_id":"{duplicate_binding.attempt_id}"',
        1,
    )
    duplicate_registry_path.write_text(duplicate_registry_text, encoding="utf-8")
    with pytest.raises(L.B4ProtocolError, match="publication load failed"):
        L.load_proposal_file(
            str(base_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=duplicate_binding.publication.publication_root,
            b4_attempt_id=duplicate_binding.attempt_id,
        )

    sort_document = proposal_document("sort")
    sort_path = tmp_path / "sort.json"
    _write_document(sort_path, sort_document)
    with pytest.raises(L.B4ProtocolError, match="driver differs"):
        S.load_proposal_file(
            str(sort_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=binding.publication.publication_root,
            b4_attempt_id=binding.attempt_id,
        )
    hash_matching_wrong_driver_binding = issue_proposal_binding_fixture(
        tmp_path / "hash-matching-wrong-driver-fixture",
        driver_kind="base",
        document=sort_document,
        label="hash-matching-wrong-driver",
    )
    wrong_driver_row = (
        hash_matching_wrong_driver_binding.publication.registry.scheduled_attempts[0]
    )
    assert wrong_driver_row.initial_proposal_sha256 == (
        L.canonical_b4_proposal_sha256(sort_document)
    )
    with pytest.raises(L.B4ProtocolError, match="driver differs"):
        S.load_proposal_file(
            str(sort_path),
            b4_reflux_ablation=True,
            b4_prerun_publication=(
                hash_matching_wrong_driver_binding.publication.publication_root
            ),
            b4_attempt_id=hash_matching_wrong_driver_binding.attempt_id,
        )


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_continuation_and_non_b4_reject_bootstrap_binding_arguments(
    driver_kind: str,
    tmp_path: Path,
) -> None:
    _module, loader = _DRIVERS[driver_kind]
    core = proposal_document(driver_kind)
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind=driver_kind,
        document=core,
    )
    receipt_sha256 = "c" * 64
    continuation = {
        **core,
        L.B4_PROPOSAL_RECEIPT_SHA256_KEY: receipt_sha256,
    }
    continuation_path = tmp_path / "continuation.json"
    _write_document(continuation_path, continuation)
    accepted = loader(
        str(continuation_path),
        b4_reflux_ablation=True,
        b4_closed_critic_receipt_sha256=receipt_sha256,
    )
    assert len(accepted) == (3 if driver_kind == "base" else 4)
    with pytest.raises(L.B4ProtocolError, match="bootstrap-only"):
        loader(
            str(continuation_path),
            b4_reflux_ablation=True,
            b4_closed_critic_receipt_sha256=receipt_sha256,
            b4_prerun_publication=binding.publication.publication_root,
            b4_attempt_id=binding.attempt_id,
        )

    ordinary_path = tmp_path / "ordinary.json"
    ordinary = {**core, "prior_critic_reverse": None}
    _write_document(ordinary_path, ordinary)
    with pytest.raises(L.B4ProtocolError, match="requires B-4 bootstrap"):
        loader(
            str(ordinary_path),
            b4_prerun_publication=binding.publication.publication_root,
            b4_attempt_id=binding.attempt_id,
        )


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_mismatch_is_single_read_and_precedes_all_campaign_effects(
    driver_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, _loader = _DRIVERS[driver_kind]
    binding = issue_proposal_binding_fixture(
        tmp_path / "fixture",
        driver_kind=driver_kind,
        document=proposal_document(driver_kind, variant=20),
    )
    proposal_path = tmp_path / "mutated-proposal.json"
    _write_document(proposal_path, proposal_document(driver_kind, variant=21))

    drive_spy = mock.Mock(side_effect=AssertionError("drive_iteration reached"))
    identity_lock_spy = mock.Mock(
        side_effect=AssertionError("campaign.lock creation reached")
    )
    advisory_lock_spy = mock.Mock(
        side_effect=AssertionError("advisory campaign lock reached")
    )
    wal_spy = mock.Mock(side_effect=AssertionError("WAL write reached"))
    build_spy = mock.Mock(side_effect=AssertionError("build reached"))
    build_v2_spy = mock.Mock(side_effect=AssertionError("build_v2 reached"))
    run_campaign_spy = mock.Mock(
        side_effect=AssertionError("run_campaign reached")
    )
    binding_spy = mock.Mock(wraps=L.require_b4_proposal_registry_binding)
    monkeypatch.setattr(module, "drive_iteration", drive_spy)
    monkeypatch.setattr(module.ident, "ensure_resumable_attempts", identity_lock_spy)
    monkeypatch.setattr(campaign_loop, "campaign_lock", advisory_lock_spy)
    monkeypatch.setattr(wal, "append", wal_spy)
    monkeypatch.setattr(buildcache, "build", build_spy)
    monkeypatch.setattr(buildcache, "build_v2", build_v2_spy)
    monkeypatch.setattr(module, "run_campaign", run_campaign_spy)
    monkeypatch.setattr(L, "require_b4_proposal_registry_binding", binding_spy)
    monkeypatch.setattr(p2_2, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(patchharness, "assert_pinned_clean", lambda *_a: None)
    if hasattr(module, "_current_site"):
        monkeypatch.setattr(module, "_current_site", lambda: site_policy.OTHER)

    real_open = builtins.open
    proposal_opens: list[str] = []

    def counted_open(path, *args, **kwargs):
        try:
            raw_path = os.fspath(path)
        except TypeError:
            raw_path = None
        if raw_path is not None and os.path.abspath(raw_path) == os.path.abspath(
            proposal_path
        ):
            proposal_opens.append(raw_path)
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", counted_open)
    argv = [
        "--b4-reflux-ablation",
        "--run-iteration",
        str(proposal_path),
        "--b4-prerun-publication",
        binding.publication.publication_root,
        "--b4-attempt-id",
        binding.attempt_id,
        "--allow-coder-derived-build",
    ]
    if driver_kind != "base":
        argv.append("--no-isolate-worktree")
    context = B4L.create_b4_launch_context_for_test(driver_kind=driver_kind)

    with pytest.raises(L.B4ProtocolError, match="canonical hash differs"):
        module.main(argv, _b4_launch_context=context)

    assert proposal_opens == [str(proposal_path)]
    binding_spy.assert_called_once()
    assert binding_spy.call_args.kwargs["driver_kind"] == driver_kind
    for effect_spy in (
        drive_spy,
        identity_lock_spy,
        advisory_lock_spy,
        wal_spy,
        build_spy,
        build_v2_spy,
        run_campaign_spy,
    ):
        effect_spy.assert_not_called()


@pytest.mark.parametrize("driver_kind", tuple(_DRIVERS))
def test_driver_main_requires_binding_and_rejects_it_outside_bootstrap(
    driver_kind: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    module, _loader = _DRIVERS[driver_kind]
    preflight_spy = mock.Mock(side_effect=AssertionError("preflight reached"))
    monkeypatch.setattr(p2_2, "_assert_single_tenant", preflight_spy)
    context = B4L.create_b4_launch_context_for_test(driver_kind=driver_kind)
    common = [
        "--run-iteration",
        str(tmp_path / "proposal.json"),
        "--allow-coder-derived-build",
    ]
    with pytest.raises(L.B4ProtocolError, match="requires publication root"):
        module.main(
            ["--b4-reflux-ablation", *common],
            _b4_launch_context=context,
        )

    binding_args = [
        "--b4-prerun-publication",
        str(tmp_path / "publication"),
        "--b4-attempt-id",
        "attempt-0000",
    ]
    with pytest.raises(L.B4ProtocolError, match="bootstrap-only"):
        module.main(
            [
                "--b4-reflux-ablation",
                "--b4-closed-critic-receipt",
                str(tmp_path / "receipt.json"),
                *common,
                *binding_args,
            ],
            _b4_launch_context=context,
        )
    with pytest.raises(L.B4ProtocolError, match="requires B-4 bootstrap"):
        module.main([*common, *binding_args])
    preflight_spy.assert_not_called()


def test_launcher_cli_requires_bootstrap_binding_and_rejects_continuation_binding(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    bootstrap_spy = mock.Mock(side_effect=AssertionError("bootstrap reached"))
    continuation_spy = mock.Mock(side_effect=AssertionError("continuation reached"))
    monkeypatch.setattr(B4L, "launch_bootstrap", bootstrap_spy)
    monkeypatch.setattr(B4L, "launch_continuation", continuation_spy)
    common = [
        "--driver",
        "base",
        "--arm",
        "on",
        "--admission-record",
        str(tmp_path / "admission.json"),
        "--proposal",
        str(tmp_path / "proposal.json"),
    ]
    with pytest.raises(SystemExit):
        B4L.main(["bootstrap", *common])
    with pytest.raises(SystemExit):
        B4L.main([
            "continuation",
            *common,
            "--artifact-root",
            str(tmp_path / "artifacts"),
            "--b4-prerun-publication",
            str(tmp_path / "publication"),
            "--b4-attempt-id",
            "attempt-0000",
        ])
    bootstrap_spy.assert_not_called()
    continuation_spy.assert_not_called()


def test_non_guarantees_are_the_verbatim_ruling_set() -> None:
    assert L.B4_PROPOSAL_BINDING_NON_GUARANTEES == (
        "continuation の提案は内容束縛されない (裁定パッケージ 1)。",
        "どの publication が権威かは強制されない (裁定パッケージ 2)。",
        "bootstrap 束縛は読み込んだ publication の manifest 外 attempt を拒否するが、"
        "その manifest の権威性は保証しない (D1880)。",
        "束縛の成功は耐久証拠に残らない (S12)。",
        "束縛されるのは実行される提案 (parse 結果の canonical 形) であって file の raw bytes ではない。",
        "照合の前に単独性検査 (`pgrep`)、Git pin 検査、launcher sidecar と campaign directory 作成が起きる。",
        "`1` と `1.0` は別の提案として扱う。実行 genome が同じでも hash は異なる。",
    )


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
