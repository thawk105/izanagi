# -*- coding: utf-8 -*-
"""T-762: campaign identity は verified activation wrapper だけを使う。"""
from __future__ import annotations

import ast
import json
import shutil
import sys
from pathlib import Path, PurePosixPath

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign import campaign_lock  # noqa: E402
from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign import env_contract_activation as activation  # noqa: E402
from orchestrator.campaign import ident  # noqa: E402


_ACTIVATION_SOURCE = (
    REPO_ROOT / "orchestrator/campaign/env_contract_activations/00000001.json"
)


def _copy_calibration(root: Path, entry: ec.GenerationEntry) -> Path:
    relative = Path(entry.contract.calibration_ref.path)
    destination = root / relative
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(REPO_ROOT / relative, destination)
    return destination


def _configure_authority(
        monkeypatch: pytest.MonkeyPatch,
        root: Path,
        *,
        head_serial: int,
        head_state_sha256: str,
) -> None:
    monkeypatch.setattr(ec, "_repository_root", lambda: root)
    monkeypatch.setattr(ec, "_ACTIVATION_DIRECTORY", PurePosixPath("authority"))
    monkeypatch.setattr(ec, "_ACTIVATION_HEAD_SERIAL", head_serial)
    monkeypatch.setattr(
        ec, "_ACTIVATION_HEAD_STATE_SHA256", head_state_sha256,
    )
    ec._clear_authority_cache_for_tests()


def _serial2_authority(root: Path) -> tuple[dict[str, object], dict[str, object]]:
    authority = root / "authority"
    authority.mkdir(parents=True)
    first_raw = _ACTIVATION_SOURCE.read_bytes()
    first = json.loads(first_raw)
    (authority / "00000001.json").write_bytes(first_raw)
    second = activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=tuple(
            activation.ActiveContract(
                env_tag=env_tag,
                generation=2 if env_tag == "pegasus" else 1,
                contract_sha256=(
                    ec.GENERATIONS[env_tag][1 if env_tag == "pegasus" else 0]
                    .contract.contract_sha256
                ),
            )
            for env_tag in sorted(ec.GENERATIONS)
        ),
    )
    (authority / "00000002.json").write_bytes(
        activation.canonical_record_bytes(second) + b"\n"
    )
    for sequence in ec.GENERATIONS.values():
        for entry in sequence:
            _copy_calibration(root, entry)
    return first, second


def _old_v2_lock(
        *, contract_sha256: str, serial: int, state_sha256: str,
) -> campaign_lock.DecodedCampaignLock:
    identity = campaign_lock.canonical_json({
        "spec_content": "t762-historical-prefix",
        "ccbench_commit": "0" * 40,
        "search_tag": "activation-wrapper",
        "search_config": {},
        "trial": None,
    })
    authority = campaign_lock.CampaignLockAuthority(
        environment_contract_sha256=contract_sha256,
        activation_serial=serial,
        activation_state_sha256=state_sha256,
        contract_loader_commit="0" * 40,
        contract_loader_blob_sha256s={
            path: "0" * 64
            for path in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
        },
    )
    return campaign_lock.decode_campaign_lock(
        campaign_lock.encode_campaign_lock_v2(identity, authority)
    )


def test_serial1_broken_calibration_passes_old_direct_shape_but_wrapper_rejects(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """M8 killer: serial-1 では successor callback が無い差分を実入力で固定する。"""
    authority = tmp_path / "authority"
    authority.mkdir()
    first_raw = _ACTIVATION_SOURCE.read_bytes()
    first = json.loads(first_raw)
    (authority / "00000001.json").write_bytes(first_raw)
    for env_tag, sequence in ec.GENERATIONS.items():
        active = sequence[0]
        calibration = _copy_calibration(tmp_path, active)
        if env_tag == "pegasus":
            calibration.write_bytes(calibration.read_bytes() + b"\n")

    _configure_authority(
        monkeypatch,
        tmp_path,
        head_serial=1,
        head_state_sha256=first["activation_state_sha256"],
    )

    direct = activation.load_activation_state(
        authority,
        registered_contracts=ec._REGISTERED_CONTRACT_CATALOG,
        is_valid_registered_successor=(
            ec._is_valid_activation_successor_with_artifact
        ),
        expected_head_serial=1,
        expected_head_state_sha256=first["activation_state_sha256"],
    )
    assert direct.activation_serial == 1
    assert {
        row.contract_sha256 for row in direct.active_contracts
    } == {
        sequence[0].contract.contract_sha256
        for sequence in ec.GENERATIONS.values()
    }

    try:
        with pytest.raises(ec.EnvContractError, match="calibration 検証失敗"):
            ident._load_current_activation_state()
    finally:
        ec._clear_authority_cache_for_tests()


def test_broken_serial1_prefix_passes_old_direct_shape_but_wrapper_rejects(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Prefix route も successor callback の無い serial-1 差分で検出する。"""
    first, second = _serial2_authority(tmp_path)
    pegasus_g1 = ec.GENERATIONS["pegasus"][0]
    calibration = tmp_path / pegasus_g1.contract.calibration_ref.path
    calibration.write_bytes(calibration.read_bytes() + b"\n")
    _configure_authority(
        monkeypatch,
        tmp_path,
        head_serial=2,
        head_state_sha256=second["activation_state_sha256"],
    )

    direct = activation.validate_activation_records(
        activation.read_activation_record_files(tmp_path / "authority")[:1],
        registered_contracts=ec._REGISTERED_CONTRACT_CATALOG,
        is_valid_registered_successor=(
            ec._is_valid_activation_successor_with_artifact
        ),
        expected_head_serial=1,
        expected_head_state_sha256=first["activation_state_sha256"],
    )
    assert direct.activation_serial == 1
    decoded = _old_v2_lock(
        contract_sha256=pegasus_g1.contract.contract_sha256,
        serial=1,
        state_sha256=first["activation_state_sha256"],
    )
    try:
        with pytest.raises(
            ident.IdentityMismatch, match="calibration 検証失敗",
        ):
            ident.verify_recorded_activation_tuple(decoded)
    finally:
        ec._clear_authority_cache_for_tests()


def test_current_wrapper_accepts_valid_serial2(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    _first, second = _serial2_authority(tmp_path)
    _configure_authority(
        monkeypatch,
        tmp_path,
        head_serial=2,
        head_state_sha256=second["activation_state_sha256"],
    )
    try:
        current = ident._load_current_activation_state()
        assert current.activation_serial == 2
        assert (
            current.activation_state_sha256
            == second["activation_state_sha256"]
        )
        assert ec.current_activation_state() is current
    finally:
        ec._clear_authority_cache_for_tests()


def test_historical_wrapper_accepts_recorded_serial1_under_serial2_head(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _serial2_authority(tmp_path)
    _configure_authority(
        monkeypatch,
        tmp_path,
        head_serial=2,
        head_state_sha256=second["activation_state_sha256"],
    )
    try:
        recorded = ec.verified_historical_activation_state(
            1, first["activation_state_sha256"],
        )
        assert recorded.activation_serial == 1
        assert (
            recorded.activation_state_sha256
            == first["activation_state_sha256"]
        )
        assert {
            row.contract_sha256 for row in recorded.active_contracts
        } <= ec._VERIFIED_CONTRACT_SHA256S
        (tmp_path / "authority/00000001.json").unlink()
        assert ec.verified_historical_activation_state(
            1, first["activation_state_sha256"],
        ) is recorded
    finally:
        ec._clear_authority_cache_for_tests()


def test_old_v2_lock_prefix_is_not_rejected_by_current_head_wrapper(
        tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    first, second = _serial2_authority(tmp_path)
    _configure_authority(
        monkeypatch,
        tmp_path,
        head_serial=2,
        head_state_sha256=second["activation_state_sha256"],
    )
    pegasus_g1 = ec.GENERATIONS["pegasus"][0].contract
    decoded = _old_v2_lock(
        contract_sha256=pegasus_g1.contract_sha256,
        serial=1,
        state_sha256=first["activation_state_sha256"],
    )
    try:
        ident.verify_recorded_activation_tuple(decoded)
    finally:
        ec._clear_authority_cache_for_tests()


def test_ident_has_no_direct_activation_leaf_route() -> None:
    tree = ast.parse(Path(ident.__file__).read_text(encoding="utf-8"))
    forbidden_functions = {
        "load_activation_state",
        "read_activation_record_files",
        "validate_activation_records",
    }
    imported_names = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    referenced_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    } | {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }
    assert "env_contract_activation" not in imported_names
    assert forbidden_functions.isdisjoint(referenced_names)


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
