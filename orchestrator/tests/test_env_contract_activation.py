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
import threading
from collections.abc import Mapping
from dataclasses import replace
from functools import lru_cache
from pathlib import Path, PurePosixPath
from types import MappingProxyType

import pytest


ORCHESTRATOR = Path(__file__).resolve().parent.parent
REPO_ROOT = ORCHESTRATOR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from orchestrator.campaign import env_contract as ec  # noqa: E402
from orchestrator.campaign import env_contract_activation as activation  # noqa: E402


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
H_B3 = "6" * 64
H_C1 = "7" * 64
H_C2 = "8" * 64
H_C3 = "9" * 64
H_D1 = "a" * 64
H_D2 = "b" * 64
H_D3 = "c" * 64
CATALOG = MappingProxyType({
    "env-a": ((1, H_A1), (2, H_A2), (3, H_A3)),
    "env-b": ((1, H_B1), (2, H_B2), (3, H_B3)),
})
THREE_ENV_CATALOG = MappingProxyType({
    **CATALOG,
    "env-c": ((1, H_C1), (2, H_C2), (3, H_C3)),
})
FOUR_ENV_CATALOG = MappingProxyType({
    **THREE_ENV_CATALOG,
    "env-d": ((1, H_D1), (2, H_D2), (3, H_D3)),
})
_PIN_ENV_COUNT = 65


@lru_cache(maxsize=1)
def _synthetic_registry():
    base = ec.GENERATIONS["linux-baremetal"][0].contract
    generations = MappingProxyType({
        env_tag: tuple(
            ec.GenerationEntry(
                generation=generation,
                contract=replace(
                    base,
                    env_tag=env_tag,
                    calibration_ref=ec.CalibrationRef(
                        path=(
                            f"output/synthetic-activation/{env_tag}/"
                            f"g{generation}.json"
                        ),
                        sha256=hashlib.sha256(
                            f"{env_tag}:g{generation}".encode("ascii")
                        ).hexdigest(),
                    ),
                ),
            )
            for generation in range(
                1,
                4 if index == _PIN_ENV_COUNT - 1 else 3,
            )
        )
        for index, env_tag in enumerate(
            f"pin-env-{index:03d}" for index in range(_PIN_ENV_COUNT)
        )
    })
    ec.validate_generations(generations)
    catalog = MappingProxyType({
        env_tag: tuple(
            (entry.generation, entry.contract.contract_sha256)
            for entry in sequence
        )
        for env_tag, sequence in generations.items()
    })
    return generations, catalog


_PIN_GENERATIONS, _PIN_CATALOG = _synthetic_registry()
_PIN_ENV_TAGS = tuple(sorted(_PIN_GENERATIONS))
_LAST_PIN_ENV_TAG = _PIN_ENV_TAGS[-1]


def _is_synthetic_successor(
    predecessor: activation.ActiveContract,
    successor: activation.ActiveContract,
) -> bool:
    allowed = {
        ("env-a", 1, H_A1, 2, H_A2),
        ("env-a", 2, H_A2, 3, H_A3),
        ("env-b", 1, H_B1, 2, H_B2),
        ("env-b", 2, H_B2, 3, H_B3),
    }
    return (
        predecessor.env_tag,
        predecessor.generation,
        predecessor.contract_sha256,
        successor.generation,
        successor.contract_sha256,
    ) in allowed


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


def _chain(
    *states: tuple[int, ...],
    registered_contracts=CATALOG,
):
    records = []
    previous = None
    env_tags = sorted(registered_contracts)
    for serial, state in enumerate(states, start=1):
        assert len(state) == len(env_tags)
        rows = tuple(
            activation.ActiveContract(
                env_tag,
                generation,
                dict(registered_contracts[env_tag])[generation],
            )
            for env_tag, generation in zip(env_tags, state)
        )
        head = activation.build_activation_record(
            activation_serial=serial,
            previous_activation_state_sha256=previous,
            active_contracts=rows,
        )
        records.append((f"{serial:08d}.json", _raw(head)))
        previous = head["activation_state_sha256"]
    return tuple(records), head


def _write_raw_records(directory: Path, records) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for filename, raw in records:
        (directory / filename).write_bytes(raw)


def _initial_state_from_head(head: dict[str, object]) -> activation.ActivationState:
    rows = tuple(
        activation.ActiveContract(
            env_tag=row["env_tag"],
            generation=row["generation"],
            contract_sha256=row["contract_sha256"],
        )
        for row in head["active_contracts"]
    )
    return activation.ActivationState(
        activation_serial=head["activation_serial"],
        activation_state_sha256=head["activation_state_sha256"],
        active_contracts=rows,
        ever_active_contract_sha256s=frozenset(
            row.contract_sha256 for row in rows
        ),
    )


def _active_argv(
    env_tags: tuple[str, ...],
    target_generations: tuple[int, ...],
) -> list[str]:
    assert len(env_tags) == len(target_generations) == _PIN_ENV_COUNT
    argv = [
        part
        for env_tag, generation in zip(env_tags, target_generations)
        for part in ("--active", f"{env_tag}={generation}")
    ]
    assert argv.count("--active") == _PIN_ENV_COUNT
    assert len(argv) == 2 * _PIN_ENV_COUNT
    return argv


def _entry_names(directory: Path) -> frozenset[str]:
    return frozenset(entry.name for entry in directory.iterdir())


def _entry_sha256s(directory: Path) -> dict[str, str]:
    return {
        entry.name: hashlib.sha256(entry.read_bytes()).hexdigest()
        for entry in directory.iterdir()
    }


def _validate(
    records,
    head,
    *,
    registered_contracts=CATALOG,
    predicate=_is_synthetic_successor,
):
    return activation.validate_activation_records(
        records,
        registered_contracts=registered_contracts,
        is_valid_registered_successor=predicate,
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

import orchestrator.campaign.env_contract as module
assert module._AUTHORITY_SNAPSHOT is None
print("import-only-ok")
'''
    env = dict(os.environ)
    env["PYTHONPATH"] = str(source_root)
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
        is_valid_registered_successor=ec._is_valid_activation_successor,
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
                is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
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
            is_valid_registered_successor=_is_synthetic_successor,
            expected_head_serial=1,
            expected_head_state_sha256=missing["activation_state_sha256"],
        )


def test_transition_accepts_one_plus_one_with_other_env_unchanged():
    records, head = _chain((1, 1), (2, 1))
    state = _validate(records, head)
    assert tuple((row.env_tag, row.generation) for row in state.active_contracts) == (
        ("env-a", 2),
        ("env-b", 1),
    )
    assert state.ever_active_contract_sha256s == frozenset({H_A1, H_A2, H_B1})


def test_transition_accepts_multiple_simultaneous_plus_one():
    records, head = _chain((1, 1), (2, 2))
    state = _validate(records, head)
    assert tuple(row.generation for row in state.active_contracts) == (2, 2)


def test_transition_accepts_three_env_simultaneous_plus_one():
    records, head = _chain(
        (1, 1, 1),
        (2, 2, 2),
        registered_contracts=THREE_ENV_CATALOG,
    )
    state = _validate(
        records,
        head,
        registered_contracts=THREE_ENV_CATALOG,
        predicate=lambda _old, _new: True,
    )
    assert tuple(row.generation for row in state.active_contracts) == (2, 2, 2)


def test_transition_accepts_four_env_simultaneous_plus_one():
    """4 env matrix 境界だけを固定する。N >= 5 の truncation は、
    有限 fixture では検出できない既知の残穴であり、保証しない。"""
    records, head = _chain(
        (1, 1, 1, 1),
        (2, 2, 2, 2),
        registered_contracts=FOUR_ENV_CATALOG,
    )
    state = _validate(
        records,
        head,
        registered_contracts=FOUR_ENV_CATALOG,
        predicate=lambda _old, _new: True,
    )
    assert tuple(row.generation for row in state.active_contracts) == (2, 2, 2, 2)


def test_transition_rejects_fourth_env_downgrade():
    records, head = _chain(
        (1, 1, 1, 2),
        (2, 2, 2, 1),
        registered_contracts=FOUR_ENV_CATALOG,
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-d.*g2 -> g1",
    ):
        _validate(
            records,
            head,
            registered_contracts=FOUR_ENV_CATALOG,
            predicate=lambda _old, _new: True,
        )


def test_transition_rejects_all_env_noop():
    records, head = _chain((1, 1), (1, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"no-op: serial=2",
    ):
        _validate(records, head)


def test_transition_rejects_noop_in_middle_of_chain():
    records, head = _chain((1, 1), (1, 1), (2, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"no-op: serial=2",
    ):
        _validate(records, head)


def test_transition_accepts_three_record_forward_chain():
    records, head = _chain((1, 1), (2, 1), (3, 1))
    state = _validate(records, head)
    assert state.activation_serial == 3
    assert tuple(row.generation for row in state.active_contracts) == (3, 1)
    assert state.ever_active_contract_sha256s == frozenset({
        H_A1, H_A2, H_A3, H_B1,
    })


def test_transition_rejects_invalid_successor_in_later_pair():
    records, head = _chain((1, 1), (2, 1), (3, 1))

    def predicate(predecessor, successor):
        if (
            predecessor.env_tag == "env-a"
            and predecessor.generation == 2
            and successor.generation == 3
        ):
            return False
        return _is_synthetic_successor(predecessor, successor)

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*serial=3.*env_tag=env-a",
    ):
        _validate(records, head, predicate=predicate)


def test_transition_rejects_generation_skip_in_later_pair():
    later_skip_catalog = MappingProxyType({
        "env-a": (*CATALOG["env-a"], (4, "d" * 64)),
        "env-b": CATALOG["env-b"],
    })
    records, head = _chain(
        (1, 1),
        (2, 1),
        (4, 1),
        registered_contracts=later_skip_catalog,
    )

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*serial=3.*env-a.*g2 -> g4",
    ):
        _validate(
            records,
            head,
            registered_contracts=later_skip_catalog,
            predicate=lambda _old, _new: True,
        )


def test_transition_rejects_skip_even_when_successor_predicate_accepts():
    records, head = _chain((1, 1), (3, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-a.*g1 -> g3",
    ):
        _validate(records, head, predicate=lambda _old, _new: True)


def test_transition_rejects_downgrade_even_when_successor_predicate_accepts():
    records, head = _chain((2, 1), (1, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-a.*g2 -> g1",
    ):
        _validate(records, head, predicate=lambda _old, _new: True)


def test_transition_rejects_compensating_plus_two_minus_one():
    records, head = _chain((1, 2), (3, 1))
    with pytest.raises(activation.ActivationRecordError, match=r"exactly \+1"):
        _validate(records, head, predicate=lambda _old, _new: True)


def test_transition_rejects_compensating_plus_one_minus_one():
    records, head = _chain((1, 2), (2, 1))
    with pytest.raises(activation.ActivationRecordError, match=r"exactly \+1"):
        _validate(records, head, predicate=lambda _old, _new: True)


def test_transition_matrix_matches_d228_rule():
    states = tuple(
        (a_generation, b_generation)
        for a_generation in (1, 2, 3)
        for b_generation in (1, 2, 3)
    )
    for predecessor_state in states:
        for successor_state in states:
            records, head = _chain(predecessor_state, successor_state)
            deltas = tuple(
                successor - predecessor
                for predecessor, successor in zip(
                    predecessor_state, successor_state
                )
            )
            expected = all(delta in {0, 1} for delta in deltas) and any(
                delta == 1 for delta in deltas
            )
            if expected:
                state = _validate(
                    records,
                    head,
                    predicate=lambda _old, _new: True,
                )
                assert tuple(row.generation for row in state.active_contracts) == (
                    successor_state
                )
            else:
                with pytest.raises(
                    activation.ActivationRecordError,
                    match=r"no-op|exactly \+1",
                ):
                    _validate(
                        records,
                        head,
                        predicate=lambda _old, _new: True,
                    )


def test_transition_three_env_matrix_matches_d228_rule():
    states = tuple(
        (a_generation, b_generation, c_generation)
        for a_generation in (1, 2, 3)
        for b_generation in (1, 2, 3)
        for c_generation in (1, 2, 3)
    )
    for predecessor_state in states:
        for successor_state in states:
            records, head = _chain(
                predecessor_state,
                successor_state,
                registered_contracts=THREE_ENV_CATALOG,
            )
            deltas = tuple(
                successor - predecessor
                for predecessor, successor in zip(
                    predecessor_state, successor_state
                )
            )
            expected = all(delta in {0, 1} for delta in deltas) and any(
                delta == 1 for delta in deltas
            )
            if expected:
                state = _validate(
                    records,
                    head,
                    registered_contracts=THREE_ENV_CATALOG,
                    predicate=lambda _old, _new: True,
                )
                assert tuple(row.generation for row in state.active_contracts) == (
                    successor_state
                )
            else:
                with pytest.raises(
                    activation.ActivationRecordError,
                    match=r"no-op|exactly \+1",
                ):
                    _validate(
                        records,
                        head,
                        registered_contracts=THREE_ENV_CATALOG,
                        predicate=lambda _old, _new: True,
                    )


def test_transition_checks_generation_change_even_when_hash_is_reused():
    reused_hash_catalog = MappingProxyType({
        "env-a": ((1, H_A1), (2, H_A1)),
        "env-b": ((1, H_B1), (2, H_B2)),
    })
    records, head = _chain(
        (1, 1),
        (2, 2),
        registered_contracts=reused_hash_catalog,
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    state = _validate(
        records,
        head,
        registered_contracts=reused_hash_catalog,
        predicate=predicate,
    )
    assert tuple(row.generation for row in state.active_contracts) == (2, 2)
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b",
    ]


def test_transition_rejects_generation_change_with_reused_hash_when_successor_is_false():
    reused_hash_catalog = MappingProxyType({
        "env-a": ((1, H_A1), (2, H_A1)),
        "env-b": ((1, H_B1),),
    })
    records, head = _chain(
        (1, 1),
        (2, 1),
        registered_contracts=reused_hash_catalog,
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return False

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-a",
    ):
        _validate(
            records,
            head,
            registered_contracts=reused_hash_catalog,
            predicate=predicate,
        )
    assert calls == [
        (
            activation.ActiveContract("env-a", 1, H_A1),
            activation.ActiveContract("env-a", 2, H_A1),
        ),
    ]


def test_transition_accepts_generation_change_when_hash_is_reused_and_other_env_is_unchanged():
    reused_hash_catalog = MappingProxyType({
        "env-a": ((1, H_A1), (2, H_A1)),
        "env-b": ((1, H_B1),),
    })
    records, head = _chain(
        (1, 1),
        (2, 1),
        registered_contracts=reused_hash_catalog,
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    state = _validate(
        records,
        head,
        registered_contracts=reused_hash_catalog,
        predicate=predicate,
    )
    assert tuple(row.generation for row in state.active_contracts) == (2, 1)
    assert calls == [
        (
            activation.ActiveContract("env-a", 1, H_A1),
            activation.ActiveContract("env-a", 2, H_A1),
        ),
    ]


def test_transition_gate_rejects_same_generation_hash_substitution_when_other_env_advances():
    """public 経路では外側の registry pair gate が所有者である。

    この private gate 直接呼出しは defense-in-depth の pin である。
    """
    predecessor_rows = (
        activation.ActiveContract("env-a", 1, H_A1),
        activation.ActiveContract("env-b", 1, H_B1),
    )
    successor_rows = (
        activation.ActiveContract("env-a", 1, H_A2),
        activation.ActiveContract("env-b", 2, H_B2),
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exactly \+1.*env-a.*g1 -> g1",
    ):
        activation._validate_activation_transition(
            predecessor_rows,
            successor_rows,
            activation_serial=2,
            is_valid_registered_successor=lambda _old, _new: True,
        )


def test_transition_rejects_skip_when_catalog_order_is_not_generation_order():
    unordered_catalog = MappingProxyType({
        "env-a": ((1, H_A1), (3, H_A3), (2, H_A2)),
        "env-b": ((1, H_B1),),
    })
    records, head = _chain(
        (1, 1),
        (3, 1),
        registered_contracts=unordered_catalog,
    )
    with pytest.raises(activation.ActivationRecordError, match=r"g1 -> g3"):
        _validate(
            records,
            head,
            registered_contracts=unordered_catalog,
            predicate=lambda _old, _new: True,
        )


def test_transition_rejects_plus_one_when_bound_contract_successor_is_false():
    records, head = _chain((1, 1), (2, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match="正当な successor でない",
    ):
        _validate(records, head, predicate=lambda _old, _new: False)


def test_transition_rejects_when_second_changed_env_successor_is_false():
    records, head = _chain((1, 1), (2, 2))
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return successor.env_tag == "env-a"

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-b",
    ):
        _validate(records, head, predicate=predicate)
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b",
    ]


def test_transition_rejects_when_third_changed_env_successor_is_false():
    records, head = _chain(
        (1, 1, 1),
        (2, 2, 2),
        registered_contracts=THREE_ENV_CATALOG,
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return successor.env_tag != "env-c"

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-c",
    ):
        _validate(
            records,
            head,
            registered_contracts=THREE_ENV_CATALOG,
            predicate=predicate,
        )
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b", "env-c",
    ]


def test_transition_rejects_when_fourth_changed_env_successor_is_false():
    records, head = _chain(
        (1, 1, 1, 1),
        (2, 2, 2, 2),
        registered_contracts=FOUR_ENV_CATALOG,
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return successor.env_tag != "env-d"

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-d",
    ):
        _validate(
            records,
            head,
            registered_contracts=FOUR_ENV_CATALOG,
            predicate=predicate,
        )
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b", "env-c", "env-d",
    ]


def test_transition_preserves_first_failure_when_later_successor_is_true():
    records, head = _chain((1, 1), (2, 2))
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return successor.env_tag == "env-b"

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"successor でない.*env_tag=env-a",
    ):
        _validate(records, head, predicate=predicate)
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b",
    ]


def test_transition_preserves_first_non_bool_failure_when_later_successor_is_true():
    records, head = _chain((1, 1), (2, 2))
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        if successor.env_tag == "env-a":
            return 1
        return True

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exact bool でない.*env_tag=env-a",
    ):
        _validate(records, head, predicate=predicate)
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b",
    ]


def test_transition_preserves_first_exception_when_later_successor_is_true():
    records, head = _chain((1, 1), (2, 2))
    calls = []
    injected = RuntimeError("injected first successor failure")

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        if successor.env_tag == "env-a":
            raise injected
        return True

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"registered successor 判定中に例外.*env_tag=env-a",
    ) as exc_info:
        _validate(records, head, predicate=predicate)
    assert exc_info.value.__cause__ is injected
    assert [successor.env_tag for _predecessor, successor in calls] == [
        "env-a", "env-b",
    ]


def test_transition_rejects_non_bool_result_from_second_changed_env():
    records, head = _chain((1, 1), (2, 2))

    def predicate(_predecessor, successor):
        if successor.env_tag == "env-b":
            return 1
        return True

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"exact bool でない.*env_tag=env-b",
    ):
        _validate(records, head, predicate=predicate)


def test_transition_wraps_exception_from_second_changed_env():
    records, head = _chain((1, 1), (2, 2))
    injected = RuntimeError("injected second successor failure")

    def predicate(_predecessor, successor):
        if successor.env_tag == "env-b":
            raise injected
        return True

    with pytest.raises(
        activation.ActivationRecordError,
        match=r"registered successor 判定中に例外.*env_tag=env-b",
    ) as exc_info:
        _validate(records, head, predicate=predicate)
    assert exc_info.value.__cause__ is injected


def test_successor_predicate_is_called_once_for_each_changed_env():
    records, head = _chain((1, 1), (2, 2))
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    _validate(records, head, predicate=predicate)
    assert calls == [
        (
            activation.ActiveContract("env-a", 1, H_A1),
            activation.ActiveContract("env-a", 2, H_A2),
        ),
        (
            activation.ActiveContract("env-b", 1, H_B1),
            activation.ActiveContract("env-b", 2, H_B2),
        ),
    ]


def test_successor_predicate_receives_exact_generation_hash_rows():
    records, head = _chain((1, 1), (2, 1))
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    _validate(records, head, predicate=predicate)
    assert calls == [
        (
            activation.ActiveContract("env-a", 1, H_A1),
            activation.ActiveContract("env-a", 2, H_A2),
        ),
    ]


def test_record_rejects_registered_generation_with_wrong_contract_hash():
    first = _record1()
    mismatch = json.loads(_raw(first))
    mismatch["active_contracts"][0]["contract_sha256"] = H_A2
    _rehash(mismatch)
    with pytest.raises(activation.ActivationRecordError, match="registry と不一致"):
        activation.validate_activation_records(
            (("00000001.json", _raw(mismatch)),),
            registered_contracts=CATALOG,
            is_valid_registered_successor=_is_synthetic_successor,
            expected_head_serial=1,
            expected_head_state_sha256=mismatch["activation_state_sha256"],
        )


def test_transition_rejects_non_bool_successor_result():
    records, head = _chain((1, 1), (2, 1))
    with pytest.raises(
        activation.ActivationRecordError,
        match="exact bool でない",
    ):
        _validate(records, head, predicate=lambda _old, _new: 1)


def test_transition_wraps_successor_exception_fail_closed():
    records, head = _chain((1, 1), (2, 1))

    def broken(_predecessor, _successor):
        raise RuntimeError("injected successor failure")

    with pytest.raises(
        activation.ActivationRecordError,
        match="registered successor 判定中に例外",
    ) as exc_info:
        _validate(records, head, predicate=broken)
    assert type(exc_info.value.__cause__) is RuntimeError


def test_production_successor_adapter_resolves_bound_generation_entries(
    monkeypatch: pytest.MonkeyPatch,
):
    predecessor_entry, successor_entry = ec.GENERATIONS["pegasus"]
    predecessor = activation.ActiveContract(
        "pegasus", 1, predecessor_entry.contract.contract_sha256
    )
    successor = activation.ActiveContract(
        "pegasus", 2, successor_entry.contract.contract_sha256
    )
    calls = []

    def spy(old_contract, new_contract):
        calls.append((old_contract, new_contract))
        return True

    monkeypatch.setattr(ec, "is_valid_successor", spy)
    assert ec._is_valid_activation_successor(predecessor, successor) is True
    assert calls == [(predecessor_entry.contract, successor_entry.contract)]


def test_production_successor_adapter_reads_current_generations_global(
    monkeypatch: pytest.MonkeyPatch,
):
    original_predecessor, original_successor = ec.GENERATIONS["pegasus"]
    replacement_predecessor = ec.GenerationEntry(
        generation=1,
        contract=replace(
            original_predecessor.contract,
            clocks_per_us=original_predecessor.contract.clocks_per_us + 1,
        ),
    )
    replacement_successor = ec.GenerationEntry(
        generation=2,
        contract=replace(
            original_successor.contract,
            clocks_per_us=original_successor.contract.clocks_per_us + 1,
        ),
    )
    predecessor = activation.ActiveContract(
        "pegasus", 1, replacement_predecessor.contract.contract_sha256
    )
    successor = activation.ActiveContract(
        "pegasus", 2, replacement_successor.contract.contract_sha256
    )
    assert ec._is_valid_activation_successor(predecessor, successor) is False

    replacement_generations = MappingProxyType({
        "pegasus": (replacement_predecessor, replacement_successor),
    })
    calls = []

    def accept(old_contract, new_contract):
        calls.append((old_contract, new_contract))
        return True

    monkeypatch.setattr(ec, "GENERATIONS", replacement_generations)
    monkeypatch.setattr(ec, "is_valid_successor", accept)
    assert ec._resolve_activation_entry(predecessor) is replacement_predecessor
    assert ec._resolve_activation_entry(successor) is replacement_successor
    assert ec._is_valid_activation_successor(predecessor, successor) is True
    assert calls == [
        (replacement_predecessor.contract, replacement_successor.contract),
    ]


def test_production_successor_adapter_returns_false_when_is_valid_successor_is_false(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    predecessor_entry, successor_entry = ec.GENERATIONS["pegasus"]
    predecessor = activation.ActiveContract(
        "pegasus", 1, predecessor_entry.contract.contract_sha256
    )
    successor = activation.ActiveContract(
        "pegasus", 2, successor_entry.contract.contract_sha256
    )
    calls = []

    def reject(old_contract, new_contract):
        calls.append((old_contract, new_contract))
        return False

    monkeypatch.setattr(ec, "is_valid_successor", reject)
    assert ec._is_valid_activation_successor(predecessor, successor) is False
    assert calls == [(predecessor_entry.contract, successor_entry.contract)]

    authority = tmp_path / "authority"
    second = _actual_serial2(authority)
    with pytest.raises(
        activation.ActivationRecordError,
        match="正当な successor でない",
    ):
        activation.validate_activation_records(
            activation.read_activation_record_files(authority),
            registered_contracts=ec._REGISTERED_CONTRACT_CATALOG,
            is_valid_registered_successor=ec._is_valid_activation_successor,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )
    assert calls == [
        (predecessor_entry.contract, successor_entry.contract),
        (predecessor_entry.contract, successor_entry.contract),
    ]


def test_production_successor_adapter_returns_false_for_resolved_invalid_contract(
    monkeypatch: pytest.MonkeyPatch,
):
    predecessor_entry = ec.GENERATIONS["pegasus"][0]
    invalid_successor_entry = ec.GenerationEntry(
        generation=2,
        contract=replace(
            predecessor_entry.contract,
            clocks_per_us=predecessor_entry.contract.clocks_per_us + 1,
        ),
    )
    generations = MappingProxyType({
        "pegasus": (predecessor_entry, invalid_successor_entry),
    })
    monkeypatch.setattr(ec, "GENERATIONS", generations)
    predecessor = activation.ActiveContract(
        "pegasus", 1, predecessor_entry.contract.contract_sha256
    )
    successor = activation.ActiveContract(
        "pegasus", 2, invalid_successor_entry.contract.contract_sha256
    )
    assert ec._resolve_activation_entry(predecessor) is predecessor_entry
    assert ec._resolve_activation_entry(successor) is invalid_successor_entry
    assert (
        ec.is_valid_successor(
            predecessor_entry.contract,
            invalid_successor_entry.contract,
        )
        is False
    )
    assert ec._is_valid_activation_successor(predecessor, successor) is False

    catalog = MappingProxyType({
        "pegasus": (
            (1, predecessor.contract_sha256),
            (2, successor.contract_sha256),
        ),
    })
    first = activation.build_activation_record(
        activation_serial=1,
        previous_activation_state_sha256=None,
        active_contracts=(predecessor,),
    )
    second = activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=(successor,),
    )
    with pytest.raises(
        activation.ActivationRecordError,
        match="正当な successor でない",
    ):
        activation.validate_activation_records(
            (("00000001.json", _raw(first)), ("00000002.json", _raw(second))),
            registered_contracts=catalog,
            is_valid_registered_successor=ec._is_valid_activation_successor,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )


def test_production_successor_adapter_rejects_rows_that_do_not_resolve(
    monkeypatch: pytest.MonkeyPatch,
):
    predecessor_entry, successor_entry = ec.GENERATIONS["pegasus"]
    predecessor = activation.ActiveContract(
        "pegasus", 1, predecessor_entry.contract.contract_sha256
    )
    unresolved = (
        activation.ActiveContract(
            "pegasus", 3, successor_entry.contract.contract_sha256
        ),
        activation.ActiveContract("pegasus", 2, "f" * 64),
        activation.ActiveContract(
            "unknown-env", 2, successor_entry.contract.contract_sha256
        ),
    )
    calls = []

    def spy(old_contract, new_contract):
        calls.append((old_contract, new_contract))
        return True

    monkeypatch.setattr(ec, "is_valid_successor", spy)
    for successor in unresolved:
        assert ec._is_valid_activation_successor(predecessor, successor) is False
    assert calls == []


def test_validate_activation_records_requires_successor_predicate(tmp_path: Path):
    first = _record1()
    records = (("00000001.json", _raw(first)),)
    directory = tmp_path / "authority"
    _write(directory, "00000001.json", first)
    with pytest.raises(TypeError):
        activation.validate_activation_records(
            records,
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=first["activation_state_sha256"],
        )
    with pytest.raises(TypeError):
        activation.load_activation_state(
            directory,
            registered_contracts=CATALOG,
            expected_head_serial=1,
            expected_head_state_sha256=first["activation_state_sha256"],
        )
    with pytest.raises(
        activation.ActivationRecordError,
        match="successor は callable",
    ):
        activation.validate_activation_records(
            records,
            registered_contracts=CATALOG,
            is_valid_registered_successor=None,
            expected_head_serial=1,
            expected_head_state_sha256=first["activation_state_sha256"],
        )
    with pytest.raises(
        activation.ActivationRecordError,
        match="successor は callable",
    ):
        activation.load_activation_state(
            directory,
            registered_contracts=CATALOG,
            is_valid_registered_successor=None,
            expected_head_serial=1,
            expected_head_state_sha256=first["activation_state_sha256"],
        )


def test_transition_rejects_missing_env_before_calling_predicate():
    """実際に発火する外側の catalog 照合層を固定する診断 pin である。

    transition gate 自体の env 集合検査へ到達する node ではない。
    """
    first = _record1()
    second = activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=(
            activation.ActiveContract("env-a", 2, H_A2),
        ),
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    with pytest.raises(activation.ActivationRecordError, match="env 集合"):
        activation.validate_activation_records(
            (
                ("00000001.json", _raw(first)),
                ("00000002.json", _raw(second)),
            ),
            registered_contracts=CATALOG,
            is_valid_registered_successor=predicate,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )
    assert calls == []


def test_transition_rejects_extra_env_fail_closed_before_calling_predicate():
    first = _record1()
    second = activation.build_activation_record(
        activation_serial=2,
        previous_activation_state_sha256=first["activation_state_sha256"],
        active_contracts=(
            activation.ActiveContract("env-a", 2, H_A2),
            activation.ActiveContract("env-b", 1, H_B1),
            activation.ActiveContract("env-c", 1, H_C1),
        ),
    )
    calls = []

    def predicate(predecessor, successor):
        calls.append((predecessor, successor))
        return True

    with pytest.raises(
        activation.ActivationRecordError,
        match="env 集合",
    ) as exc_info:
        activation.validate_activation_records(
            (
                ("00000001.json", _raw(first)),
                ("00000002.json", _raw(second)),
            ),
            registered_contracts=CATALOG,
            is_valid_registered_successor=predicate,
            expected_head_serial=2,
            expected_head_state_sha256=second["activation_state_sha256"],
        )
    assert type(exc_info.value) is activation.ActivationRecordError
    assert calls == []


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
        with pytest.raises(
            ec.EnvContractError,
            match=r"activation authority 検証失敗: activation head (?:serial|state hash) 不一致",
        ):
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
    assert (
        observed["is_valid_registered_successor"]
        is ec._is_valid_activation_successor
    )


def test_production_loader_rejects_generation_skip_at_last_of_65_envs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        (2,) * (_PIN_ENV_COUNT - 1) + (3,),
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", _PIN_CATALOG)

    with _use_authority(monkeypatch, authority, head):
        with pytest.raises(ec.EnvContractError) as exc_info:
            ec.current_activation_state()
    message = str(exc_info.value)
    assert "activation authority 検証失敗" in message
    assert "exactly +1" in message
    assert _LAST_PIN_ENV_TAG in message
    assert "g1 -> g3" in message


def test_production_loader_rejects_invalid_successor_at_last_of_65_changed_envs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        (2,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    original_is_valid_successor = ec.is_valid_successor

    def reject_last_successor(predecessor, successor):
        if successor.env_tag == _LAST_PIN_ENV_TAG:
            return False
        return original_is_valid_successor(predecessor, successor)

    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", _PIN_CATALOG)
    monkeypatch.setattr(ec, "is_valid_successor", reject_last_successor)

    with _use_authority(monkeypatch, authority, head):
        with pytest.raises(ec.EnvContractError) as exc_info:
            ec.current_activation_state()
    message = str(exc_info.value)
    assert "activation authority 検証失敗" in message
    assert "successor でない" in message
    assert _LAST_PIN_ENV_TAG in message


def test_loader_leaf_rejects_generation_skip_at_last_of_65_envs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        (2,) * (_PIN_ENV_COUNT - 1) + (3,),
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)

    with pytest.raises(activation.ActivationRecordError) as exc_info:
        activation.load_activation_state(
            authority,
            registered_contracts=_PIN_CATALOG,
            is_valid_registered_successor=ec._is_valid_activation_successor,
            expected_head_serial=head["activation_serial"],
            expected_head_state_sha256=head["activation_state_sha256"],
        )
    message = str(exc_info.value)
    assert "exactly +1" in message
    assert _LAST_PIN_ENV_TAG in message
    assert "g1 -> g3" in message


def test_loader_leaf_rejects_invalid_successor_at_last_of_65_changed_envs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        (2,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    original_is_valid_successor = ec.is_valid_successor

    def reject_last_successor(predecessor, successor):
        if successor.env_tag == _LAST_PIN_ENV_TAG:
            return False
        return original_is_valid_successor(predecessor, successor)

    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "is_valid_successor", reject_last_successor)

    with pytest.raises(activation.ActivationRecordError) as exc_info:
        activation.load_activation_state(
            authority,
            registered_contracts=_PIN_CATALOG,
            is_valid_registered_successor=ec._is_valid_activation_successor,
            expected_head_serial=head["activation_serial"],
            expected_head_state_sha256=head["activation_state_sha256"],
        )
    message = str(exc_info.value)
    assert "successor でない" in message
    assert _LAST_PIN_ENV_TAG in message


def test_loader_leaf_accepts_65_env_plus_one(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        (2,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)

    state = activation.load_activation_state(
        authority,
        registered_contracts=_PIN_CATALOG,
        is_valid_registered_successor=ec._is_valid_activation_successor,
        expected_head_serial=head["activation_serial"],
        expected_head_state_sha256=head["activation_state_sha256"],
    )
    assert state.activation_serial == 2
    assert len(state.active_contracts) == _PIN_ENV_COUNT
    assert all(row.generation == 2 for row in state.active_contracts)


def test_pegasus_g2_authorization_reaches_certified_sink_without_lookup(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    """serial 2 の g2 解決を authorize→guard→pipeline sink まで固定する。"""
    from orchestrator.campaign import pipeline, site_policy
    from orchestrator.campaign.model import Genome
    from orchestrator.campaign.pipeline import PerfConfig
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


def test_forward_activation_preserves_pegasus_g1_for_historical_resolution(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    authority = tmp_path / "authority"
    second = _actual_serial2(authority)
    with _use_authority(monkeypatch, authority, second):
        assert ec.lookup("pegasus") is ec.GENERATIONS["pegasus"][1].contract
        g1 = ec.GENERATIONS["pegasus"][0]
        assert g1.contract.contract_sha256 in (
            ec.current_activation_state().ever_active_contract_sha256s
        )
        assert (
            ec.resolve_by_contract_sha256(
                g1.contract.contract_sha256,
                expected_env_tag="pegasus",
            )
            is g1
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
from orchestrator.campaign import env_contract as module
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
    env["PYTHONPATH"] = str(stage)
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
    held = threading.Event()
    release = threading.Event()

    def hold_authority_lock():
        with ec._AUTHORITY_LOCK:
            held.set()
            release.wait(20)

    worker = threading.Thread(target=hold_authority_lock)
    worker.start()
    assert held.wait(5), "worker が authority lock を保持できなかった"
    read_fd, write_fd = os.pipe()
    pid = os.fork()
    if pid == 0:
        try:
            os.close(read_fd)
            with ec._AUTHORITY_LOCK:
                pass
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
        release.set()
        worker.join(5)
        os.close(read_fd)
        _waited, status = os.waitpid(pid, 0)
    assert ready, "fork child が inherited lock で停止した"
    assert not worker.is_alive()
    assert os.waitstatus_to_exitcode(status) == 0
    assert observed == (
        b"ok:" + ec.GENERATIONS["pegasus"][0].contract.contract_sha256.encode("ascii")
    )


def test_repo_root_is_cwd_independent(tmp_path: Path):
    env = dict(os.environ)
    env["PYTHONPATH"] = str(REPO_ROOT)
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            "from orchestrator.campaign.env_contract import lookup; print(lookup('pegasus').generation if False else lookup('pegasus').env_tag)",
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
        "--active", "pegasus=2",
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
    rows = {
        row["env_tag"]: (row["generation"], row["contract_sha256"])
        for row in issued_document["active_contracts"]
    }
    assert rows == {
        "linux-baremetal": (
            1,
            ec.GENERATIONS["linux-baremetal"][0].contract.contract_sha256,
        ),
        "pegasus": (
            2,
            ec.GENERATIONS["pegasus"][1].contract.contract_sha256,
        ),
    }


def test_issue_main_passes_production_successor_adapter_by_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
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
                    contract_sha256=(
                        ec.GENERATIONS[env_tag][0].contract.contract_sha256
                    ),
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
    observed = []
    original_validate = activation.validate_activation_records

    def spy(*args, **kwargs):
        observed.append(kwargs["is_valid_registered_successor"])
        return original_validate(*args, **kwargs)

    monkeypatch.setattr(activation, "validate_activation_records", spy)
    assert issuer.main([
        "--active", "linux-baremetal=1",
        "--active", "pegasus=2",
    ]) == 0
    assert len(observed) == 1
    assert observed[0] is ec._is_valid_activation_successor


def test_issue_main_rejects_when_production_successor_adapter_rejects(
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
                    contract_sha256=(
                        ec.GENERATIONS[env_tag][0].contract.contract_sha256
                    ),
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
    monkeypatch.setattr(ec, "is_valid_successor", lambda _old, _new: False)

    with pytest.raises(SystemExit) as exc_info:
        issuer.main([
            "--active", "linux-baremetal=1",
            "--active", "pegasus=2",
        ])
    assert exc_info.value.code == 1
    assert "正当な successor でない" in capsys.readouterr().err
    assert not (authority / "00000002.json").exists()


def test_issue_main_rejects_noop_without_publishing(
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
    with pytest.raises(SystemExit) as exc_info:
        issuer.main([
            "--active", "linux-baremetal=1",
            "--active", "pegasus=1",
        ])
    assert exc_info.value.code == 1
    assert "no-op" in capsys.readouterr().err
    assert not (authority / "00000002.json").exists()


def test_issue_main_rejects_generation_skip_at_last_of_65_envs_without_publishing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    issuer = _load_issue_tool()
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    initial_state = _initial_state_from_head(head)
    target_generations = (2,) * (_PIN_ENV_COUNT - 1) + (3,)
    argv = _active_argv(_PIN_ENV_TAGS, target_generations)

    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", _PIN_CATALOG)
    monkeypatch.setattr(ec, "current_activation_state", lambda: initial_state)
    monkeypatch.setattr(
        ec, "_ACTIVATION_DIRECTORY", PurePosixPath(authority.as_posix())
    )
    monkeypatch.setattr(
        issuer, "__file__", str(tmp_path / "tools/issue_env_contract_activation.py")
    )

    published = authority / "00000002.json"
    assert not published.exists()
    real_authority = (
        REPO_ROOT / "orchestrator/campaign/env_contract_activations"
    )
    real_entries_before = _entry_sha256s(real_authority)
    sys_path_before = tuple(sys.path)
    assert sys.modules["campaign.env_contract"] is ec
    try:
        with pytest.raises(SystemExit) as exc_info:
            issuer.main(argv)
    finally:
        sys.path[:] = sys_path_before
        assert _entry_sha256s(real_authority) == real_entries_before
    assert exc_info.value.code == 1
    error = capsys.readouterr().err
    assert "exactly +1" in error
    assert _LAST_PIN_ENV_TAG in error
    assert "g1 -> g3" in error
    assert not published.exists()


def test_issue_main_rejects_invalid_successor_at_last_of_65_changed_envs_without_publishing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str],
):
    issuer = _load_issue_tool()
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    initial_state = _initial_state_from_head(head)
    argv = _active_argv(_PIN_ENV_TAGS, (2,) * _PIN_ENV_COUNT)
    original_is_valid_successor = ec.is_valid_successor

    def reject_last_successor(predecessor, successor):
        if successor.env_tag == _LAST_PIN_ENV_TAG:
            return False
        return original_is_valid_successor(predecessor, successor)

    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", _PIN_CATALOG)
    monkeypatch.setattr(ec, "current_activation_state", lambda: initial_state)
    monkeypatch.setattr(
        ec, "_ACTIVATION_DIRECTORY", PurePosixPath(authority.as_posix())
    )
    monkeypatch.setattr(ec, "is_valid_successor", reject_last_successor)
    monkeypatch.setattr(
        issuer, "__file__", str(tmp_path / "tools/issue_env_contract_activation.py")
    )

    published = authority / "00000002.json"
    assert not published.exists()
    real_authority = (
        REPO_ROOT / "orchestrator/campaign/env_contract_activations"
    )
    real_entries_before = _entry_sha256s(real_authority)
    sys_path_before = tuple(sys.path)
    assert sys.modules["campaign.env_contract"] is ec
    try:
        with pytest.raises(SystemExit) as exc_info:
            issuer.main(argv)
    finally:
        sys.path[:] = sys_path_before
        assert _entry_sha256s(real_authority) == real_entries_before
    assert exc_info.value.code == 1
    error = capsys.readouterr().err
    assert "successor でない" in error
    assert _LAST_PIN_ENV_TAG in error
    assert not published.exists()


def test_issue_main_accepts_65_env_plus_one_and_publishes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
):
    issuer = _load_issue_tool()
    authority = tmp_path / "authority"
    records, head = _chain(
        (1,) * _PIN_ENV_COUNT,
        registered_contracts=_PIN_CATALOG,
    )
    _write_raw_records(authority, records)
    initial_state = _initial_state_from_head(head)
    argv = _active_argv(_PIN_ENV_TAGS, (2,) * _PIN_ENV_COUNT)

    monkeypatch.setattr(ec, "GENERATIONS", _PIN_GENERATIONS)
    monkeypatch.setattr(ec, "_REGISTERED_CONTRACT_CATALOG", _PIN_CATALOG)
    monkeypatch.setattr(ec, "current_activation_state", lambda: initial_state)
    monkeypatch.setattr(
        ec, "_ACTIVATION_DIRECTORY", PurePosixPath(authority.as_posix())
    )
    monkeypatch.setattr(
        issuer, "__file__", str(tmp_path / "tools/issue_env_contract_activation.py")
    )

    real_authority = (
        REPO_ROOT / "orchestrator/campaign/env_contract_activations"
    )
    real_entries_before = _entry_sha256s(real_authority)
    sys_path_before = tuple(sys.path)
    assert sys.modules["campaign.env_contract"] is ec
    try:
        result = issuer.main(argv)
    finally:
        sys.path[:] = sys_path_before
        assert _entry_sha256s(real_authority) == real_entries_before

    assert result == 0
    published = authority / "00000002.json"
    raw = published.read_bytes()
    document = json.loads(raw)
    assert raw == activation.canonical_record_bytes(document) + b"\n"
    assert document["activation_serial"] == 2
    assert len(document["active_contracts"]) == _PIN_ENV_COUNT
    assert all(
        row["generation"] == 2 for row in document["active_contracts"]
    )


def _run() -> int:
    """Keep this new test file covered by the repository plain-runner contract."""
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
