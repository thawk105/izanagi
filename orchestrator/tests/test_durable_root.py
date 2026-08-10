# -*- coding: utf-8 -*-
"""durable root policy と write capability の負例。"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ORCHESTRATOR = Path(__file__).resolve().parent.parent
if str(ORCHESTRATOR.parent) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR.parent))

from orchestrator.campaign.durable_root import (  # noqa: E402
    DurableRootError,
    DurableRootPolicy,
    resolve_policy_root,
)


def _mount_line(mount_id: int, parent_id: int, mount_point: Path) -> str:
    escaped = str(mount_point).replace("\\", "\\134").replace(" ", "\\040")
    return f"{mount_id} {parent_id} 0:1 / {escaped} rw - tmpfs synthetic rw"


def _base_mountinfo() -> str:
    return _mount_line(1, 0, Path("/")) + "\n"


def test_resolve_and_open_for_write(tmp_path: Path):
    approved = tmp_path / "approved"
    candidate = approved / "campaign"
    candidate.mkdir(parents=True)
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=())

    resolved = resolve_policy_root(policy, str(candidate), mountinfo_text=_base_mountinfo())
    capability = resolved.acquire_write_capability()
    with capability.open_for_write("result.bin") as stream:
        stream.write(b"ok")
    assert (candidate / "result.bin").read_bytes() == b"ok"


def test_resolve_rejects_symlink_escape(tmp_path: Path):
    approved = tmp_path / "approved"
    outside = tmp_path / "outside"
    approved.mkdir()
    outside.mkdir()
    (approved / "via-link").symlink_to(outside, target_is_directory=True)
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=())

    with pytest.raises(DurableRootError):
        resolve_policy_root(
            policy,
            str(approved / "via-link"),
            mountinfo_text=_base_mountinfo(),
        )


def test_resolve_rejects_forbidden_subtree(tmp_path: Path):
    approved = tmp_path / "approved"
    forbidden = approved / "forbidden"
    forbidden.mkdir(parents=True)
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=(forbidden,))
    with pytest.raises(DurableRootError):
        resolve_policy_root(policy, str(forbidden), mountinfo_text=_base_mountinfo())


def test_resolve_rejects_mount_id_crossing(tmp_path: Path):
    approved = tmp_path / "approved"
    mounted = approved / "mounted"
    mounted.mkdir(parents=True)
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=())
    mountinfo = _base_mountinfo() + _mount_line(2, 1, mounted) + "\n"

    with pytest.raises(DurableRootError):
        resolve_policy_root(policy, str(mounted), mountinfo_text=mountinfo)


def test_open_rejects_root_replaced_after_capability_acquisition(tmp_path: Path):
    approved = tmp_path / "approved"
    candidate = approved / "campaign"
    candidate.mkdir(parents=True)
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=())
    capability = resolve_policy_root(
        policy, str(candidate), mountinfo_text=_base_mountinfo()
    ).acquire_write_capability()

    candidate.rename(approved / "old-campaign")
    candidate.mkdir()
    with pytest.raises(DurableRootError):
        capability.open_for_write("must-not-exist.bin")
    assert not (candidate / "must-not-exist.bin").exists()


def test_open_rejects_symlink_leaf_without_touching_external_file(tmp_path: Path):
    approved = tmp_path / "approved"
    approved.mkdir()
    external = tmp_path / "external.bin"
    external.write_bytes(b"must-survive")
    (approved / "result.bin").symlink_to(external)
    capability = resolve_policy_root(
        DurableRootPolicy(approved_roots=(approved,), forbidden_roots=()),
        str(approved), mountinfo_text=_base_mountinfo(),
    ).acquire_write_capability()
    with pytest.raises(DurableRootError):
        capability.open_for_write("result.bin")
    assert external.read_bytes() == b"must-survive"


@pytest.mark.parametrize("relpath", ["../escape", "/absolute", "nested/../../escape"])
def test_open_rejects_non_relative_child_path(tmp_path: Path, relpath: str):
    approved = tmp_path / "approved"
    approved.mkdir()
    policy = DurableRootPolicy(approved_roots=(approved,), forbidden_roots=())
    capability = resolve_policy_root(
        policy, str(approved), mountinfo_text=_base_mountinfo()
    ).acquire_write_capability()
    with pytest.raises(DurableRootError):
        capability.open_for_write(relpath)


if __name__ == "__main__":
    sys.exit(pytest.main([__file__]))
