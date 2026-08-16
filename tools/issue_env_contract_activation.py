#!/usr/bin/env python3
"""Reviewed env-contract activation record を create-only で発行する保守 tool。"""
from __future__ import annotations

import argparse
import os
import re
import secrets
import sys
from pathlib import Path
from typing import Sequence


_ASSIGNMENT_RE = re.compile(r"([a-z0-9][a-z0-9._-]*)=([1-9][0-9]*)")


def _active_assignment(value: str) -> tuple[str, int]:
    match = _ASSIGNMENT_RE.fullmatch(value)
    if match is None:
        raise argparse.ArgumentTypeError(
            "--active は canonical ENV_TAG=GENERATION でなければならない"
        )
    return match.group(1), int(match.group(2), 10)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "現在の reviewed activation head に、全 env を明示した record を一件追加する。"
            "発行だけでは有効化されず、表示された head 定数を record と同一 commit で更新し、"
            "全 process を再起動して初めて有効になる"
        ),
    )
    parser.add_argument(
        "--active",
        action="append",
        required=True,
        type=_active_assignment,
        metavar="ENV_TAG=GENERATION",
        help="全登録 env について一度ずつ指定する",
    )
    return parser


def _write_create_only(directory: Path, filename: str, raw: bytes) -> Path:
    """Live directory 外で完全化し、hard-link no-replace で一件だけ publish する。"""
    parent = directory.parent
    directory_flags = (
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | getattr(os, "O_CLOEXEC", 0)
    )
    parent_fd = os.open(parent, directory_flags)
    try:
        directory_fd = os.open(directory, directory_flags)
    except BaseException:
        os.close(parent_fd)
        raise
    descriptor = -1
    staging_name: str | None = None
    published = False
    try:
        if os.fstat(parent_fd).st_dev != os.fstat(directory_fd).st_dev:
            raise OSError("activation staging parent が live directory と同一 filesystem でない")
        staging_flags = (
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
            | getattr(os, "O_CLOEXEC", 0)
        )
        for _attempt in range(128):
            candidate = f".{filename}.{secrets.token_hex(16)}.stage"
            try:
                descriptor = os.open(
                    candidate, staging_flags, 0o600, dir_fd=parent_fd
                )
            except FileExistsError:
                continue
            staging_name = candidate
            break
        else:
            raise OSError("activation staging filename を確保できない")
        if os.fstat(descriptor).st_dev != os.fstat(directory_fd).st_dev:
            raise OSError("activation staging file が live directory と同一 filesystem でない")
        os.fchmod(descriptor, 0o644)
        offset = 0
        while offset < len(raw):
            try:
                written = os.write(descriptor, raw[offset:])
            except InterruptedError:
                continue
            if written <= 0:
                raise OSError("activation record write が進捗しない")
            offset += written
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1

        os.link(
            staging_name,
            filename,
            src_dir_fd=parent_fd,
            dst_dir_fd=directory_fd,
            follow_symlinks=False,
        )
        published = True
        os.fsync(directory_fd)
        os.unlink(staging_name, dir_fd=parent_fd)
        staging_name = None
        os.fsync(parent_fd)
    except BaseException:
        cleanup_errors: list[OSError] = []
        if descriptor >= 0:
            try:
                os.close(descriptor)
            except OSError as exc:
                cleanup_errors.append(exc)
            descriptor = -1
        if published:
            try:
                os.unlink(filename, dir_fd=directory_fd)
                os.fsync(directory_fd)
            except OSError as exc:
                cleanup_errors.append(exc)
        if staging_name is not None:
            try:
                os.unlink(staging_name, dir_fd=parent_fd)
                os.fsync(parent_fd)
            except FileNotFoundError:
                pass
            except OSError as exc:
                cleanup_errors.append(exc)
        if cleanup_errors:
            raise OSError(
                "activation publish 失敗後の残骸回収を完了できない: "
                + "; ".join(str(exc) for exc in cleanup_errors)
            ) from cleanup_errors[0]
        raise
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        os.close(directory_fd)
        os.close(parent_fd)
    return directory / filename


def _activation_handoff(*, issued: Path, repo_root: Path, serial: int, state_hash: str) -> str:
    """発行と有効化を区別し、reviewed head の次値を明示する。"""
    return "\n".join((
        f"issued {issued.relative_to(repo_root)} state_sha256={state_hash}",
        "NOT ACTIVE: activation record の発行だけでは有効化されない。",
        "orchestrator/campaign/env_contract.py の reviewed head を次へ更新する:",
        f"_ACTIVATION_HEAD_SERIAL: int = {serial}",
        f'_ACTIVATION_HEAD_STATE_SHA256: str = "{state_hash}"',
        "record と head 更新を同一 commit に収容し、配備後に全 process を再起動して初めて有効になる。",
    ))


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)

    # Authority import/load は argparse が入力を受理した後に限る。
    repo_root = Path(__file__).resolve().parents[1]
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from orchestrator.campaign import env_contract as contract
    from orchestrator.campaign import env_contract_activation as activation

    assignments: dict[str, int] = {}
    for env_tag, generation in args.active:
        if env_tag in assignments:
            parser.error(f"--active が重複している: {env_tag!r}")
        assignments[env_tag] = generation
    registered_envs = set(contract.GENERATIONS)
    if set(assignments) != registered_envs:
        parser.error(
            "--active の env 集合が登録 env と exact 一致しない: "
            f"active={sorted(assignments)} registered={sorted(registered_envs)}"
        )

    try:
        current_state = contract.current_activation_state()
        rows = []
        for env_tag in sorted(assignments):
            generation = assignments[env_tag]
            sequence = contract.GENERATIONS[env_tag]
            if generation > len(sequence):
                raise activation.ActivationRecordError(
                    f"未登録 generation を指定した: {env_tag!r} g{generation}"
                )
            entry = sequence[generation - 1]
            rows.append(activation.ActiveContract(
                env_tag=env_tag,
                generation=generation,
                contract_sha256=entry.contract.contract_sha256,
            ))
        document = activation.build_activation_record(
            activation_serial=current_state.activation_serial + 1,
            previous_activation_state_sha256=(
                current_state.activation_state_sha256
            ),
            active_contracts=rows,
        )
        raw = activation.canonical_record_bytes(document) + b"\n"
        directory = contract._repository_root() / Path(contract._ACTIVATION_DIRECTORY)
        filename = f"{document['activation_serial']:08d}.json"
        existing_records = activation.read_activation_record_files(directory)
        activation.validate_activation_records(
            (*existing_records, (filename, raw)),
            registered_contracts=contract._REGISTERED_CONTRACT_CATALOG,
            is_valid_registered_successor=(
                contract._is_valid_activation_successor_with_artifact
            ),
            expected_head_serial=document["activation_serial"],
            expected_head_state_sha256=document["activation_state_sha256"],
        )
        issued = _write_create_only(directory, filename, raw)
    except (contract.EnvContractError, activation.ActivationRecordError, OSError) as exc:
        parser.exit(1, f"activation record を発行できない: {exc}\n")
    print(_activation_handoff(
        issued=issued,
        repo_root=repo_root,
        serial=document["activation_serial"],
        state_hash=document["activation_state_sha256"],
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
