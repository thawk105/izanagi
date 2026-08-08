# -*- coding: utf-8 -*-
"""Activation record leaf と lazy env-contract authority の回帰テスト。"""
from __future__ import annotations

import ast
import hashlib
import importlib.util
import json
import os
import re
import select
import signal
import shutil
import stat
import subprocess
import sys
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path, PurePosixPath
from types import MappingProxyType

import pytest


ORCHESTRATOR = Path(__file__).resolve().parent.parent
REPO_ROOT = ORCHESTRATOR.parent
if str(ORCHESTRATOR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from campaign import env_contract as ec  # noqa: E402
from campaign import env_contract_activation as activation  # noqa: E402


INITIAL_STATE_SHA256 = (
    "f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed"
)
INITIAL_BYTES = (
    b'{"activation_serial":1,"activation_state_sha256":"f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed",'
    b'"active_contracts":[{"contract_sha256":"1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7",'
    b'"env_tag":"linux-baremetal","generation":1},{"contract_sha256":"e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01",'
    b'"env_tag":"pegasus","generation":1}],"previous_activation_state_sha256":null,'
    b'"schema_version":"env-contract-activation/v1"}\n'
)
H_A1 = "1" * 64
H_A2 = "2" * 64
H_A3 = "5" * 64
H_B1 = "3" * 64
H_B2 = "4" * 64
CATALOG = MappingProxyType({
    "env-a": ((1, H_A1), (2, H_A2), (3, H_A3)),
    "env-b": ((1, H_B1), (2, H_B2)),
})


def _raw(document: dict[str, object]) -> bytes:
    return activation.canonical_record_bytes(document) + b"\n"


def _rehash(document: dict[str, object]) -> dict[str, object]:
    body = {
        key: value for key, value in document.items()
        if key != "activation_state_sha256"
    }
    document["activation_state_sha256"] = hashlib.sha256(
        activation.canonical_record_bytes(body)
    ).hexdigest()
    return document


def _record1() -> dict[str, object]:
    return activation.build_activation_record(
        activation_serial=1,
        previous_activation_state_sha256=None,
        active_contracts=(
            activation.ActiveContract("env-a", 1, H_A1),
            activation.ActiveContract("env-b", 1, H_B1),
        ),
    )


def _record2(first: dict[str, object] | None = None) -> dict[str, object]:
    first = _record1() if first is None else first
    return activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=(
            activation.ActiveContract("env-a", 2, H_A2),
            activation.ActiveContract("env-b", 1, H_B1),
        ),
    )


def _validate(records, head):
    return activation.validate_activation_records(
        records,
        registered_contracts=CATALOG,
        expected_head_serial=head["activation_serial"],
        expected_head_state_sha256=head["activation_state_sha256"],
    )


def _write(directory: Path, name: str, document: dict[str, object]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / name).write_bytes(_raw(document))


def _actual_serial2(directory: Path) -> dict[str, object]:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "00000001.json").write_bytes(INITIAL_BYTES)
    first = json.loads(INITIAL_BYTES)
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
    _write(directory, "00000002.json", second)
    return second


def _actual_serial3_downgrade(directory: Path) -> dict[str, object]:
    second = _actual_serial2(directory)
    third = activation.build_activation_record(
        activation_serial=3,
        previous_activation_state_sha256=second["activation_state_sha256"],
        active_contracts=tuple(
            activation.ActiveContract(
                env_tag=env_tag,
                generation=1,
                contract_sha256=ec.GENERATIONS[env_tag][0].contract.contract_sha256,
            )
            for env_tag in sorted(ec.GENERATIONS)
        ),
    )
    _write(directory, "00000003.json", third)
    return third


def _git_archive_source_stage(tmp_path: Path) -> Path:
    """HEAD archive を基礎に、未 commit の現 wave 所有物だけを overlay する。"""
    archive = tmp_path / "source-stage.tar"
    stage = tmp_path / "source-stage"
    stage.mkdir()
    completed = subprocess.run(
        ["git", "archive", "--format=tar", f"--output={archive}", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    shutil.unpack_archive(archive, stage, format="tar")
    current_runtime = (
        "orchestrator/campaign/__init__.py",
        "orchestrator/campaign/calibration_verify.py",
        "orchestrator/campaign/env_contract.py",
        "orchestrator/campaign/env_contract_activation.py",
        "orchestrator/campaign/env_attestation.py",
        "orchestrator/calibrator/__init__.py",
        "orchestrator/calibrator/effective_clock_policy.py",
        "orchestrator/calibrator/schema_v2.py",
        "orchestrator/calibrator/tsc.py",
    )
    for relative in current_runtime:
        destination = stage / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(REPO_ROOT / relative, destination)
    shutil.copytree(
        REPO_ROOT / "orchestrator/campaign/env_contract_activations",
        stage / "orchestrator/campaign/env_contract_activations",
        dirs_exist_ok=True,
    )
    return stage


def _pin_source_stage_head(stage: Path, head: dict[str, object]) -> None:
    module = stage / "orchestrator/campaign/env_contract.py"
    source = module.read_text(encoding="utf-8")
    source, serial_count = re.subn(
        r"_ACTIVATION_HEAD_SERIAL: int = [0-9]+",
        f"_ACTIVATION_HEAD_SERIAL: int = {head['activation_serial']}",
        source,
    )
    source, hash_count = re.subn(
        r'(_ACTIVATION_HEAD_STATE_SHA256: str = \(\n\s+")[0-9a-f]{64}("\n\))',
        rf"\g<1>{head['activation_state_sha256']}\g<2>",
        source,
    )
    assert (serial_count, hash_count) == (1, 1)
    module.write_text(source, encoding="utf-8")


def _run_import_io_guard(source_root: Path, cwd: Path) -> subprocess.CompletedProcess[str]:
    script = r'''
import builtins
import io
import os
from pathlib import Path

def is_authority_path(value):
    try:
        text = os.fsdecode(os.fspath(value)).replace("\\", "/")
    except TypeError:
        return False
    return (
        "orchestrator/campaign/env_contract_activations" in text
        or ("output/env/" in text and "/calibration/" in text)
    )

def guard(name, original):
    def wrapped(*args, **kwargs):
        if args and is_authority_path(args[0]):
            raise AssertionError(f"authority I/O during import: {name}: {args[0]!r}")
        return original(*args, **kwargs)
    return wrapped

for owner, names in (
    (builtins, ("open",)),
    (io, ("open",)),
    (os, ("open", "stat", "lstat", "scandir", "listdir", "access")),
    (Path, ("open", "read_bytes", "read_text", "stat", "lstat", "is_file", "is_dir", "exists")),
):
    for name in names:
        setattr(owner, name, guard(f"{owner.__name__}.{name}", getattr(owner, name)))

import campaign.env_contract as module
assert module._AUTHORITY_SNAPSHOT is None
print("import-only-ok")
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source_root / "orchestrator")
    return subprocess.run(
        [sys.executable, "-c", script],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )


def _use_authority(monkeypatch, directory: Path, head: dict[str, object]):
    context = monkeypatch.context()
    patch = context.__enter__()
    patch.setattr(ec, "_ACTIVATION_DIRECTORY", PurePosixPath(directory.as_posix()))
    patch.setattr(ec, "_ACTIVATION_HEAD_SERIAL", head["activation_serial"])
    patch.setattr(ec, "_ACTIVATION_HEAD_STATE_SHA256", head["activation_state_sha256"])
    ec._clear_authority_cache_for_tests()

    class _Context:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, traceback):
            context.__exit__(exc_type, exc, traceback)
            ec._clear_authority_cache_for_tests()
            return False

    return _Context()


def _use_source_head_authority(monkeypatch, directory: Path):
    """Source head 定数には触れず、production directory seam だけを差し替える。"""
    context = monkeypatch.context()
    patch = context.__enter__()
    patch.setattr(ec, "_ACTIVATION_DIRECTORY", PurePosixPath(directory.as_posix()))
    ec._clear_authority_cache_for_tests()

    class _Context:
        def __enter__(self):
            return None

        def __exit__(self, exc_type, exc, traceback):
            context.__exit__(exc_type, exc, traceback)
            ec._clear_authority_cache_for_tests()
            return False

    return _Context()


def test_initial_record_is_exact_canonical_hash_bound_and_selects_both_g1():
    path = REPO_ROOT / "orchestrator/campaign/env_contract_activations/00000001.json"
    assert path.read_bytes() == INITIAL_BYTES
    state = activation.load_activation_state(
        path.parent,
        registered_contracts=ec._REGISTERED_CONTRACT_CATALOG,
        expected_head_serial=1,
        expected_head_state_sha256=INITIAL_STATE_SHA256,
    )
    assert state.activation_serial == 1
    assert state.activation_state_sha256 == INITIAL_STATE_SHA256
    assert tuple((row.env_tag, row.generation) for row in state.active_contracts) == (
        ("linux-baremetal", 1), ("pegasus", 1),
    )
    assert state.ever_active_contract_sha256s == frozenset(
        row.contract_sha256 for row in state.active_contracts
    )


def test_record_rejects_duplicate_unknown_noncanonical_and_bool_integer_fields():
    first = _record1()
    canonical = _raw(first)
    duplicate = canonical.replace(
        b'"schema_version":',
        b'"schema_version":"env-contract-activation/v1","schema_version":',
        1,
    )
    with pytest.raises(activation.ActivationRecordError, match="重複 key"):
        _validate((("00000001.json", duplicate),), first)

    unknown = json.loads(canonical)
    unknown["extra"] = None
    _rehash(unknown)
    with pytest.raises(activation.ActivationRecordError, match="key 集合"):
        _validate((("00000001.json", _raw(unknown)),), unknown)

    noncanonical = json.dumps(first, indent=2, sort_keys=True).encode() + b"\n"
    with pytest.raises(activation.ActivationRecordError, match="canonical JSON"):
        _validate((("00000001.json", noncanonical),), first)

    for field in ("activation_serial",):
        mutated = json.loads(canonical)
        mutated[field] = True
        _rehash(mutated)
        with pytest.raises(activation.ActivationRecordError, match="exact int"):
            activation.validate_activation_records(
                (("00000001.json", _raw(mutated)),),
                registered_contracts=CATALOG,
                expected_head_serial=1,
                expected_head_state_sha256=mutated["activation_state_sha256"],
            )
    mutated = json.loads(canonical)
    mutated["active_contracts"][0]["generation"] = True
    _rehash(mutated)
    with pytest.raises(activation.ActivationRecordError, match="exact int"):
        activation.validate_activation_records(
            (("00000001.json", _raw(mutated)),),
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=mutated["activation_state_sha256"],
        )


def test_chain_rejects_gap_filename_mismatch_and_bad_predecessor():
    first = _record1()
    second = _record2(first)
    with pytest.raises(activation.ActivationRecordError, match="filename / serial / 連番"):
        _validate((("00000001.json", _raw(first)), ("00000003.json", _raw(second))), second)

    bad_predecessor = json.loads(_raw(second))
    bad_predecessor["previous_activation_state_sha256"] = "f" * 64
    _rehash(bad_predecessor)
    with pytest.raises(activation.ActivationRecordError, match="predecessor hash chain"):
        activation.validate_activation_records(
            (("00000001.json", _raw(first)), ("00000002.json", _raw(bad_predecessor))),
            registered_contracts=CATALOG,
            expected_head_serial=2,
            expected_head_state_sha256=bad_predecessor["activation_state_sha256"],
        )


def test_chain_rejects_symlink_nonregular_and_extra_entry(tmp_path: Path):
    target = tmp_path / "target.json"
    target.write_bytes(_raw(_record1()))
    authority = tmp_path / "authority"
    authority.mkdir()
    (authority / "00000001.json").symlink_to(target)
    with pytest.raises(activation.ActivationRecordError, match="symlink|regular file"):
        activation.read_activation_record_files(authority)
    (authority / "00000001.json").unlink()
    (authority / "00000001.json").mkdir()
    with pytest.raises(activation.ActivationRecordError, match="regular file"):
        activation.read_activation_record_files(authority)
    shutil.rmtree(authority / "00000001.json")
    _write(authority, "00000001.json", _record1())
    (authority / "README").write_text("extra", encoding="utf-8")
    with pytest.raises(activation.ActivationRecordError, match="不正な entry"):
        activation.read_activation_record_files(authority)
    directory_link = tmp_path / "authority-link"
    directory_link.symlink_to(authority, target_is_directory=True)
    with pytest.raises(activation.ActivationRecordError, match="symlink でない directory"):
        activation.read_activation_record_files(directory_link)


def test_head_pin_rejects_tail_rollback():
    first = _record1()
    second = _record2(first)
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"activation head (?:serial|state hash) 不一致",
    ):
        activation.validate_activation_records(
            (("00000001.json", _raw(first)),),
            registered_contracts=CATALOG,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )


def test_head_pin_rejects_valid_suffix_injection():
    first = _record1()
    second = _record2(first)
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"activation head (?:serial|state hash) 不一致",
    ):
        activation.validate_activation_records(
            (("00000001.json", _raw(first)), ("00000002.json", _raw(second))),
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=first["activation_state_sha256"],
        )


def test_head_pin_rejects_same_serial_state_hash_mismatch():
    first = _record1()
    second = _record2(first)
    alternate_second = activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=(
            activation.ActiveContract("env-a", 3, H_A3),
            activation.ActiveContract("env-b", 1, H_B1),
        ),
    )
    assert (
        alternate_second["activation_state_sha256"]
        != second["activation_state_sha256"]
    )
    with pytest.raises(activation.ActivationRecordError, match="head state hash 不一致"):
        activation.validate_activation_records(
            (("00000001.json", _raw(first)), ("00000002.json", _raw(second))),
            registered_contracts=CATALOG,
            expected_head_serial=2,
            expected_head_state_sha256=alternate_second["activation_state_sha256"],
        )


def test_record_requires_exact_registered_env_set_and_contract_pair():
    first = _record1()
    missing = json.loads(_raw(first))
    missing["active_contracts"].pop()
    _rehash(missing)
    with pytest.raises(activation.ActivationRecordError, match="env 集合"):
        activation.validate_activation_records(
            (("00000001.json", _raw(missing)),),
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=missing["activation_state_sha256"],
        )


def test_chain_intentionally_does_not_enforce_generation_delta_predicates():
    records = []
    previous = None
    rows_by_serial = (
        ((1, H_A1), (1, H_B1)),
        ((1, H_A1), (1, H_B1)),  # no-op
        ((3, H_A3), (1, H_B1)),  # skip
        ((2, H_A2), (1, H_B1)),  # downgrade
    )
    head = None
    for serial, ((a_generation, a_hash), (b_generation, b_hash)) in enumerate(
        rows_by_serial, start=1,
    ):
        head = activation.build_activation_record(
            activation_serial=serial,
            previous_activation_state_sha256=previous,
            active_contracts=(
                activation.ActiveContract("env-a", a_generation, a_hash),
                activation.ActiveContract("env-b", b_generation, b_hash),
            ),
        )
        records.append((f"{serial:08d}.json", _raw(head)))
        previous = head["activation_state_sha256"]
    assert head is not None
    state = _validate(tuple(records), head)
    assert state.activation_serial == 4
    assert state.active_contracts[0].generation == 2
    assert state.ever_active_contract_sha256s == frozenset({
        H_A1, H_A2, H_A3, H_B1,
    })
    first = json.loads(records[0][1])
    mismatch = json.loads(_raw(first))
    mismatch["active_contracts"][0]["contract_sha256"] = H_A2
    _rehash(mismatch)
    with pytest.raises(activation.ActivationRecordError, match="registry と不一致"):
        activation.validate_activation_records(
            (("00000001.json", _raw(mismatch)),),
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=mismatch["activation_state_sha256"],
        )


def test_real_pegasus_g2_serial2_is_accepted_and_switches_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """通常の回帰正例であり、DW-G04 の発火証拠には数えない。"""
    second = _actual_serial2(tmp_path / "authority")
    with _use_authority(monkeypatch, tmp_path / "authority", second):
        assert ec.lookup("pegasus") is ec.GENERATIONS["pegasus"][1].contract
        assert ec.lookup("linux-baremetal") is ec.GENERATIONS["linux-baremetal"][0].contract


def test_production_loader_rejects_tail_deletion_with_source_head_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    shutil.copytree(
        REPO_ROOT / "orchestrator/campaign/env_contract_activations", authority
    )
    max(authority.glob("[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9].json")).unlink()
    original_head = (
        ec._ACTIVATION_HEAD_SERIAL,
        ec._ACTIVATION_HEAD_STATE_SHA256,
    )
    with _use_source_head_authority(monkeypatch, authority):
        with pytest.raises(ec.EnvContractError, match="activation authority 検証失敗"):
            ec.current_activation_state()
        assert (
            ec._ACTIVATION_HEAD_SERIAL,
            ec._ACTIVATION_HEAD_STATE_SHA256,
        ) == original_head


def test_issued_valid_suffix_is_not_active_until_source_head_update_and_restart(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """発行→head 更新→同一 commit→再起動の全段が揃って初めて有効になる。"""
    issuer = _load_issue_tool()
    authority = tmp_path / "authority"
    shutil.copytree(
        REPO_ROOT / "orchestrator/campaign/env_contract_activations", authority
    )
    current = ec.current_activation_state()
    suffix = activation.build_activation_record(
        activation_serial=current.activation_serial + 1,
        previous_activation_state_sha256=current.activation_state_sha256,
        active_contracts=current.active_contracts,
    )
    issuer._write_create_only(
        authority,
        f"{suffix['activation_serial']:08d}.json",
        _raw(suffix),
    )
    original_head = (
        ec._ACTIVATION_HEAD_SERIAL,
        ec._ACTIVATION_HEAD_STATE_SHA256,
    )
    with _use_source_head_authority(monkeypatch, authority):
        with pytest.raises(ec.EnvContractError, match="activation authority 検証失敗"):
            ec.lookup("pegasus")
        assert (
            ec._ACTIVATION_HEAD_SERIAL,
            ec._ACTIVATION_HEAD_STATE_SHA256,
        ) == original_head


def test_production_loader_passes_source_head_constants_to_leaf(monkeypatch):
    observed = {}
    original = activation.load_activation_state

    def spy(*args, **kwargs):
        observed.update(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(activation, "load_activation_state", spy)
    ec._clear_authority_cache_for_tests()
    state = ec.current_activation_state()
    assert state.activation_serial == ec._ACTIVATION_HEAD_SERIAL
    assert observed["expected_head_serial"] == ec._ACTIVATION_HEAD_SERIAL
    assert (
        observed["expected_head_state_sha256"]
        == ec._ACTIVATION_HEAD_STATE_SHA256
    )


def test_pegasus_g2_authorization_reaches_certified_sink_without_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """serial 2 の g2 解決を authorize→guard→pipeline sink まで固定する。"""
    from campaign import pipeline, site_policy
    from campaign.model import Genome
    from campaign.pipeline import PerfConfig
    from test_campaign import _BUILD_CONTEXT, _mock_pipeline, _tmp_layout

    second = _actual_serial2(tmp_path / "authority")
    with _use_authority(monkeypatch, tmp_path / "authority", second):
        authorization = ec.authorize("pegasus")
        g2 = ec.GENERATIONS["pegasus"][1].contract
        g1 = ec.GENERATIONS["pegasus"][0].contract
        assert authorization.contract is g2
        monkeypatch.setattr(
            ec, "lookup",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("certified sink が lookup fallback を呼んだ")
            ),
        )
        monkeypatch.setattr(
            ec, "lookup_required_attestation_contract",
            lambda *_args, **_kwargs: (_ for _ in ()).throw(
                AssertionError("certified sink が required lookup fallback を呼んだ")
            ),
        )
        monkeypatch.setattr(
            pipeline.execution_guard._site_policy,
            "current_site",
            lambda: site_policy.PEGASUS_COMPUTE,
        )
        with _mock_pipeline(certified=True):
            result = pipeline.evaluate(
                Genome("silo", {"BACK_OFF": 1}), _tmp_layout(), g2.env_tag,
                "deadbeef", PerfConfig(records=1000, threads=2),
                g2.clocks_per_us, numactl=g2.numactl,
                authorization_contract=authorization,
                env_contract=g2, do_bench=False,
                build_context=_BUILD_CONTEXT, log=lambda *_args: None,
            )
        assert result.certified and not result.aborted

        forged_g1 = replace(authorization, contract=g1)
        with pytest.raises(
            pipeline.execution_guard.CertifiedWriterAuthorizationError
        ):
            pipeline.execution_guard.require_certified_writer_authorization(
                forged_g1,
                env_tag=g1.env_tag,
                clocks_per_us=g1.clocks_per_us,
                numactl=g1.numactl,
            )


def test_serial2_preserves_g1_as_ever_active_and_verifies_history_on_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    second = _actual_serial2(tmp_path / "authority")
    with _use_authority(monkeypatch, tmp_path / "authority", second):
        ec.lookup("pegasus")
        pegasus_g1 = ec.GENERATIONS["pegasus"][0]
        assert pegasus_g1.contract.contract_sha256 not in ec._VERIFIED_CONTRACT_SHA256S
        resolved = ec.resolve_by_contract_sha256(
            pegasus_g1.contract.contract_sha256,
            expected_env_tag="pegasus",
        )
        assert resolved is pegasus_g1
        assert pegasus_g1.contract.contract_sha256 in ec._VERIFIED_CONTRACT_SHA256S


def test_downgrade_preserves_pegasus_g2_for_historical_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    third = _actual_serial3_downgrade(authority)
    with _use_authority(monkeypatch, authority, third):
        assert ec.lookup("pegasus") is ec.GENERATIONS["pegasus"][0].contract
        g2 = ec.GENERATIONS["pegasus"][1]
        assert (
            ec.resolve_by_contract_sha256(
                g2.contract.contract_sha256,
                expected_env_tag="pegasus",
            )
            is g2
        )


@pytest.mark.parametrize("historical_damage", ["missing", "modified"])
def test_historical_calibration_is_verified_only_when_resolved_in_source_stage(
    tmp_path: Path, historical_damage: str,
):
    stage = _git_archive_source_stage(tmp_path)
    authority = stage / "orchestrator/campaign/env_contract_activations"
    second = _actual_serial2(authority)
    _pin_source_stage_head(stage, second)
    g1 = ec.GENERATIONS["pegasus"][0]
    calibration = stage / g1.contract.calibration_ref.path
    if historical_damage == "missing":
        calibration.unlink()
    else:
        calibration.write_bytes(calibration.read_bytes() + b"\n")
    script = f'''
from campaign import env_contract as module
current = module.lookup("pegasus")
assert current.contract_sha256 == {ec.GENERATIONS["pegasus"][1].contract.contract_sha256!r}
try:
    module.resolve_by_contract_sha256(
        {g1.contract.contract_sha256!r}, expected_env_tag="pegasus"
    )
except module.EnvContractError as exc:
    assert "calibration 検証失敗" in str(exc), str(exc)
else:
    raise AssertionError("壊れた historical calibration が resolver を通過した")
print("current-ok-historical-rejected")
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(stage / "orchestrator")
    completed = subprocess.run(
        [sys.executable, "-c", script],
        cwd=stage,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "current-ok-historical-rejected"


def test_registered_but_never_active_hash_has_distinct_refusal_reason():
    ec._clear_authority_cache_for_tests()
    g2_hash = ec.GENERATIONS["pegasus"][1].contract.contract_sha256
    with pytest.raises(ec.EnvContractError, match="登録済み.*ever-active でない"):
        ec.resolve_by_contract_sha256(g2_hash)
    with pytest.raises(ec.EnvContractError, match="未知の contract_sha256"):
        ec.resolve_by_contract_sha256("f" * 64)


def test_lazy_registry_mapping_contract_is_compatible_and_read_only():
    ec._clear_authority_cache_for_tests()
    assert isinstance(ec.REGISTRY, MappingProxyType)
    assert isinstance(ec.REGISTRY, Mapping)
    assert issubclass(ec._ActivationRegistryView, Mapping)
    assert list(ec.REGISTRY) == ["linux-baremetal", "pegasus"]
    assert len(ec.REGISTRY) == 2
    assert sorted(ec.REGISTRY) == ["linux-baremetal", "pegasus"]
    assert "pegasus" in ec.REGISTRY
    items = tuple(ec.REGISTRY.items())
    assert tuple(key for key, _value in items) == ("linux-baremetal", "pegasus")
    assert tuple(ec.REGISTRY.values()) == tuple(value for _key, value in items)
    assert ec.REGISTRY["pegasus"] is ec.lookup("pegasus")
    with pytest.raises(TypeError):
        ec.REGISTRY["pegasus"] = ec.lookup("pegasus")  # type: ignore[index]


def test_import_performs_no_open_or_stat_io_in_worktree_or_archive_source_stage(
    tmp_path: Path,
):
    stage = _git_archive_source_stage(tmp_path)
    worktree_result = _run_import_io_guard(REPO_ROOT, tmp_path)
    stage_result = _run_import_io_guard(stage, stage)
    for completed in (worktree_result, stage_result):
        assert completed.returncode == 0, completed.stdout + completed.stderr
        assert completed.stdout.strip() == "import-only-ok"


def test_authority_validation_is_cached_once_per_pid(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    authority.mkdir()
    (authority / "00000001.json").write_bytes(INITIAL_BYTES)
    first = json.loads(INITIAL_BYTES)
    with _use_authority(monkeypatch, authority, first):
        expected = ec.lookup("pegasus")
        (authority / "00000001.json").unlink()
        assert ec.lookup("pegasus") is expected
        assert tuple(ec.REGISTRY) == ("linux-baremetal", "pegasus")


def test_held_lock_fork_reinitializes_child_cache_without_deadlock():
    if not hasattr(os, "fork"):
        pytest.skip("os.fork がない")
    ec._clear_authority_cache_for_tests()
    read_fd, write_fd = os.pipe()
    ec._AUTHORITY_LOCK.acquire()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            contract = ec.lookup("pegasus")
            os.write(write_fd, b"ok:" + contract.contract_sha256.encode("ascii"))
        except BaseException as exc:  # noqa: BLE001 - child diagnostic
            os.write(write_fd, f"error:{type(exc).__name__}:{exc}".encode())
        finally:
            os.close(write_fd)
            os._exit(0)
    os.close(write_fd)
    ready = []
    observed = b""
    try:
        ready, _writeable, _exceptional = select.select([read_fd], [], [], 15)
        if ready:
            observed = os.read(read_fd, 4096)
        else:
            os.kill(pid, signal.SIGKILL)
    finally:
        ec._AUTHORITY_LOCK.release()
        os.close(read_fd)
        _waited, status = os.waitpid(pid, 0)
    assert ready, "fork child が inherited lock で停止した"
    assert os.waitstatus_to_exitcode(status) == 0
    assert observed == (
        b"ok:" + ec.GENERATIONS["pegasus"][0].contract.contract_sha256.encode("ascii")
    )


def test_repo_root_is_cwd_independent(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(ORCHESTRATOR)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from campaign.env_contract import lookup; print(lookup('pegasus').generation if False else lookup('pegasus').env_tag)",
        ],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert completed.stdout.strip() == "pegasus"


def test_activation_leaf_is_stdlib_only_campaign_import_free_and_env_neutral():
    path = REPO_ROOT / "orchestrator/campaign/env_contract_activation.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.append(node.module or "")
    assert not [name for name in imports if name.startswith(("campaign", "orchestrator", "calibrator"))]
    forbidden = ("linux-baremetal", "pegasus", 1800, 2100, "--interleave=all")
    assert ec.find_env_literals(path.read_text(encoding="utf-8"), forbidden, None) == []


def _load_issue_tool():
    path = REPO_ROOT / "tools/issue_env_contract_activation.py"
    spec = importlib.util.spec_from_file_location("issue_env_contract_activation_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_issue_cli_parses_before_authority_load_and_writes_create_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    issuer = _load_issue_tool()
    monkeypatch.setattr(
        ec, "_authority_snapshot",
        lambda: (_ for _ in ()).throw(AssertionError("loader called before parse")),
    )
    with pytest.raises(SystemExit) as exc_info:
        issuer.main(["--active", "not-an-assignment"])
    assert exc_info.value.code == 2

    directory = tmp_path / "authority"
    directory.mkdir()
    issued = issuer._write_create_only(directory, "00000002.json", b"first\n")
    assert issued.read_bytes() == b"first\n"
    assert not list(tmp_path.glob(".00000002.json.*.stage"))
    with pytest.raises(FileExistsError):
        issuer._write_create_only(directory, "00000002.json", b"replacement\n")
    assert issued.read_bytes() == b"first\n"
    assert not list(tmp_path.glob(".00000002.json.*.stage"))


def test_issue_publish_never_exposes_partial_bytes_and_fsyncs_directories(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    issuer = _load_issue_tool()
    directory = tmp_path / "authority"
    directory.mkdir()
    target = directory / "00000002.json"
    original_write = issuer.os.write
    original_fsync = issuer.os.fsync
    fsynced_modes = []

    def short_write(descriptor, raw):
        assert not target.exists()
        return original_write(descriptor, raw[:max(1, len(raw) // 2)])

    def record_fsync(descriptor):
        fsynced_modes.append(os.fstat(descriptor).st_mode)
        return original_fsync(descriptor)

    monkeypatch.setattr(issuer.os, "write", short_write)
    monkeypatch.setattr(issuer.os, "fsync", record_fsync)
    issued = issuer._write_create_only(directory, target.name, b"complete-record\n")
    assert issued.read_bytes() == b"complete-record\n"
    assert sum(1 for mode in fsynced_modes if not stat.S_ISDIR(mode)) == 1
    assert sum(1 for mode in fsynced_modes if stat.S_ISDIR(mode)) == 2
    assert not list(tmp_path.glob(".00000002.json.*.stage"))


@pytest.mark.parametrize("failure_point", ["write", "file_fsync", "directory_fsync"])
def test_issue_failure_removes_all_residue_and_allows_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_point: str,
):
    issuer = _load_issue_tool()
    directory = tmp_path / "authority"
    directory.mkdir()
    target = directory / "00000002.json"
    original_write = issuer.os.write
    original_fsync = issuer.os.fsync

    with monkeypatch.context() as patch:
        if failure_point == "write":
            calls = 0

            def fail_after_partial_write(descriptor, raw):
                nonlocal calls
                calls += 1
                if calls == 1:
                    return original_write(descriptor, raw[:1])
                raise OSError("injected write failure")

            patch.setattr(issuer.os, "write", fail_after_partial_write)
        else:
            fsync_calls = 0

            def fail_selected_fsync(descriptor):
                nonlocal fsync_calls
                fsync_calls += 1
                selected = 1 if failure_point == "file_fsync" else 2
                if fsync_calls == selected:
                    raise OSError(f"injected {failure_point} failure")
                return original_fsync(descriptor)

            patch.setattr(issuer.os, "fsync", fail_selected_fsync)
        with pytest.raises(OSError, match="injected"):
            issuer._write_create_only(directory, target.name, b"complete-record\n")

    assert not target.exists()
    assert not list(tmp_path.glob(".00000002.json.*.stage"))
    assert issuer._write_create_only(
        directory, target.name, b"retry-record\n"
    ).read_bytes() == b"retry-record\n"


def test_issue_success_message_names_inactive_state_head_constants_and_restart(
    tmp_path: Path,
):
    issuer = _load_issue_tool()
    issued = tmp_path / "orchestrator/campaign/env_contract_activations/00000002.json"
    state_hash = "a" * 64
    message = issuer._activation_handoff(
        issued=issued,
        repo_root=tmp_path,
        serial=2,
        state_hash=state_hash,
    )
    assert "NOT ACTIVE" in message
    assert "_ACTIVATION_HEAD_SERIAL: int = 2" in message
    assert f'_ACTIVATION_HEAD_STATE_SHA256: str = "{state_hash}"' in message
    assert "同一 commit" in message
    assert "全 process を再起動" in message


def test_issue_main_success_prints_required_head_and_inactive_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    issuer = _load_issue_tool()
    authority = tmp_path / "authority"
    authority.mkdir()
    (authority / "00000001.json").write_bytes(INITIAL_BYTES)
    monkeypatch.setattr(
        ec,
        "current_activation_state",
        lambda: activation.ActivationState(
            activation_serial=1,
            activation_state_sha256=INITIAL_STATE_SHA256,
            active_contracts=tuple(
                activation.ActiveContract(
                    env_tag=env_tag,
                    generation=1,
                    contract_sha256=ec.GENERATIONS[env_tag][0].contract.contract_sha256,
                )
                for env_tag in sorted(ec.GENERATIONS)
            ),
            ever_active_contract_sha256s=frozenset(
                ec.GENERATIONS[env_tag][0].contract.contract_sha256
                for env_tag in ec.GENERATIONS
            ),
        ),
    )
    monkeypatch.setattr(ec, "_repository_root", lambda: tmp_path)
    monkeypatch.setattr(ec, "_ACTIVATION_DIRECTORY", PurePosixPath("authority"))
    monkeypatch.setattr(
        issuer, "__file__", str(tmp_path / "tools/issue_env_contract_activation.py")
    )
    assert issuer.main([
        "--active", "linux-baremetal=1",
        "--active", "pegasus=1",
    ]) == 0
    output = capsys.readouterr().out
    issued_document = json.loads((authority / "00000002.json").read_bytes())
    assert "NOT ACTIVE" in output
    assert "_ACTIVATION_HEAD_SERIAL: int = 2" in output
    assert (
        f'_ACTIVATION_HEAD_STATE_SHA256: str = "'
        f'{issued_document["activation_state_sha256"]}"'
    ) in output
    assert "同一 commit" in output
    assert "全 process を再起動" in output


def _run() -> int:
    """Keep this new test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
