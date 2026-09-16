"""Synthetic admission and diagnostic pins for the v2 gate core (D1872)."""
from dataclasses import replace
import hashlib
import inspect
import json
from unittest import mock

import pytest

from orchestrator.campaign import s8b_oracle_driver as driver


MISSING = "v2-execution: launch-validate: LaunchValidatedFreeze exact type が必要"
FLOOR_NULL = "floor-null: freeze.floor が null"
BUDGET_NULL = "budget-null: freeze.budget が null"
SHAPES = [
    pytest.param("both", set(), id="both"),
    pytest.param("floor-only", {BUDGET_NULL}, id="floor-only"),
    pytest.param("budget-only", {FLOOR_NULL}, id="budget-only"),
]


def _assert_exact_refusals(actual, expected):
    assert len(actual) == len(expected), actual
    assert set(actual) == expected, actual


def _synthetic(tmp_path, shape="both"):
    document = {
        "floor": {}, "budget": {},
        "known_axes_freeze": {"path": "known.json"},
    }
    if shape in ("budget-only", "v1"):
        document["floor"] = None
    if shape in ("floor-only", "v1"):
        document["budget"] = None
    raw = json.dumps(document).encode()
    path = tmp_path / "freeze.json"
    path.write_bytes(raw)
    sha = hashlib.sha256(raw).hexdigest()
    verified = driver._freeze_io.VerifiedFreeze(document, sha)
    ratified = driver.s8b_ratified_freeze.RatifiedFreeze(
        document=document, sha256=sha, generation_number=1,
        activation_head="a" * 40, generation_commit="b" * 40,
    )
    floor = driver.s8b_ratified_freeze.VerifiedFloorArtifact(
        path="floor.json", raw_bytes=b"{}",
        sha256=hashlib.sha256(b"{}").hexdigest(), document={},
    )
    token = driver.s8b_ratified_freeze.LaunchValidatedFreeze(
        ratified=ratified, activation_head=ratified.activation_head,
        search_digest="c" * 64, symlink_gitlink_inventory=(),
        floor_artifact=floor, binaries_by_cell={},
    )
    return path, verified, token


@pytest.fixture
def resolution():
    return driver._t080_migration.ReceiptResolution(
        "never-issued", (), None, "a" * 40,
    )


@pytest.fixture
def seams(resolution):
    with (
        mock.patch.object(driver, "_resolve_t080_receipt", return_value=resolution),
        mock.patch.object(driver.s1_known_axes_freeze, "verify", lambda *a, **k: None),
        mock.patch.object(driver, "_load_verified_freeze") as reads,
        mock.patch.object(driver.s8b_ratified_freeze, "load_ratified_freeze") as static,
        mock.patch.object(driver.s8b_ratified_freeze, "launch_validate") as launch,
    ):
        yield reads, static, launch


def _core(path, resolution, **kwargs):
    return driver._gate_check_core(
        freeze_path=path, root=path.parent, t080_resolution=resolution,
        approved_spec=None, manifest_verification_error=None,
        standalone_manifest_verification=False, **kwargs,
    )


def test_public_reread_v2_requires_launch_validated(tmp_path, seams):
    path, verified, token = _synthetic(tmp_path)
    reads, static, launch = seams
    reads.side_effect = [driver.OracleDriverError("first read failed"), verified]
    # The old fallback admits this hash-matching static candidate.
    static.return_value = token.ratified
    decision = driver.gate_check(freeze_path=path, root=tmp_path)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {MISSING})
    assert reads.call_count == 2
    static.assert_not_called()
    launch.assert_not_called()


def test_public_reread_v2_ignores_injected_ratified(tmp_path, seams):
    path, verified, token = _synthetic(tmp_path)
    reads, static, launch = seams
    reads.side_effect = [driver.OracleDriverError("first read failed"), verified]
    static.return_value = token.ratified
    decision = driver.gate_check(
        freeze_path=path, root=tmp_path, ratified=token.ratified,
    )
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {MISSING})
    assert reads.call_count == 2
    static.assert_not_called()
    launch.assert_not_called()


@pytest.mark.parametrize("shape,null_refusals", SHAPES)
def test_core_v2_without_launch_validated_is_refused(
        tmp_path, resolution, seams, shape, null_refusals):
    path, verified, token = _synthetic(tmp_path, shape)
    reads, static, launch = seams
    static.return_value = token.ratified
    decision = _core(path, resolution, verified=verified)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {MISSING} | null_refusals)
    reads.assert_not_called()
    static.assert_not_called()
    launch.assert_not_called()


@pytest.mark.parametrize("shape,null_refusals", SHAPES)
def test_core_exact_launch_validated_preserves_predicates(
        tmp_path, resolution, seams, shape, null_refusals):
    path, verified, token = _synthetic(tmp_path, shape)
    decision = _core(path, resolution, verified=verified, launch_validated=token)
    assert decision.allowed is (not null_refusals)
    _assert_exact_refusals(decision.refusals, null_refusals)
    for seam in seams:
        seam.assert_not_called()


def test_core_rejects_launch_validated_subclass(tmp_path, resolution, seams):
    class Derived(driver.s8b_ratified_freeze.LaunchValidatedFreeze):
        pass

    path, verified, token = _synthetic(tmp_path)
    derived = Derived(**vars(token))
    decision = _core(path, resolution, verified=verified, launch_validated=derived)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {
        "v2-execution: launch-validate: validated freeze object の型が不正",
    })
    for seam in seams:
        seam.assert_not_called()


@pytest.mark.parametrize("error,expected", [
    pytest.param(
        driver.s8b_ratified_freeze.RatifiedFreezeError("reason", "detail"),
        "freeze-ratify: [reason] [reason] detail", id="RatifiedFreezeError",
    ),
    pytest.param(RuntimeError("detail"), "freeze-ratify: RuntimeError: detail",
                 id="RuntimeError"),
])
def test_public_ratified_load_errors_preserve_refusals(tmp_path, seams, error, expected):
    path, verified, _ = _synthetic(tmp_path, "floor-only")
    reads, static, launch = seams
    reads.return_value = verified
    static.side_effect = error
    decision = driver.gate_check(freeze_path=path, root=tmp_path)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {expected, BUDGET_NULL})
    reads.assert_called_once_with(path)
    static.assert_called_once_with(tmp_path)
    launch.assert_not_called()


def test_public_explicit_ratified_error_keeps_early_return(tmp_path, seams):
    path, _, _ = _synthetic(tmp_path)
    decision = driver.gate_check(
        freeze_path=path, root=tmp_path, ratified_error="sentinel",
    )
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {"freeze-ratify: sentinel"})
    for seam in seams:
        seam.assert_not_called()


def test_public_two_failed_reads_preserve_refusals(tmp_path, seams):
    path, _, _ = _synthetic(tmp_path)
    reads, static, launch = seams
    reads.side_effect = [driver.OracleDriverError("first read failed"),
                         driver.OracleDriverError("second read failed")]
    decision = driver.gate_check(freeze_path=path, root=tmp_path)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {
        "holdout-freeze-verify: OracleDriverError: second read failed",
        "known-axes-freeze-verify: OracleDriverError: known_axes_freeze source record がない",
        FLOOR_NULL, BUDGET_NULL,
    })
    assert reads.call_count == 2
    static.assert_not_called()
    launch.assert_not_called()


def test_core_launch_validated_missing_hash_remains_refused(tmp_path, resolution, seams):
    path, _, token = _synthetic(tmp_path)
    token = replace(token, ratified=replace(token.ratified, sha256=None))
    decision = _core(path, resolution, launch_validated=token)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {
        "freeze-not-active-generation: "
        "与えられた freeze bytes sha256 が承認束縛済み active 世代と不一致",
    })
    for seam in seams:
        seam.assert_not_called()


def test_public_reread_v1_never_gets_missing_token_refusal(tmp_path, seams):
    path, verified, _ = _synthetic(tmp_path, "v1")
    reads, static, launch = seams
    reads.side_effect = [driver.OracleDriverError("first read failed"), verified]
    with mock.patch.object(driver.s8b_holdout_freeze, "verify", lambda *a, **k: None):
        decision = driver.gate_check(freeze_path=path, root=tmp_path)
    assert decision.allowed is False
    _assert_exact_refusals(decision.refusals, {FLOOR_NULL, BUDGET_NULL})
    assert reads.call_count == 2
    static.assert_not_called()
    launch.assert_not_called()


def test_cli_gate_check_transports_missing_token_refusal(tmp_path, seams, capsys):
    path, verified, token = _synthetic(tmp_path)
    reads, static, launch = seams
    reads.side_effect = [driver.OracleDriverError("first read failed"), verified]
    static.return_value = token.ratified
    rc = driver.main(["gate-check", "--freeze", str(path), "--root", str(tmp_path)])
    assert rc == driver._exit_code("refused")
    result = json.loads(capsys.readouterr().out)
    assert result["allowed"] is False
    _assert_exact_refusals(result["refusals"], {MISSING})
    assert reads.call_count == 2
    static.assert_not_called()
    launch.assert_not_called()


def test_gate_core_signature_has_no_ratified_injection_port():
    assert "ratified" not in inspect.signature(driver._gate_check_core).parameters
