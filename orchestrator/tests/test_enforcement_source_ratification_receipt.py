# -*- coding: utf-8 -*-
"""[T-1629] signed enforcement-source ratification receipt tests."""
from __future__ import annotations

import ast
import base64
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
import pytest

from orchestrator.campaign import campaign_lock
from orchestrator.campaign import contract_loader_binding as B
from orchestrator.campaign import enforcement_source_ratification as V1
from orchestrator.campaign import enforcement_source_ratification_receipt as R


_DOMAIN = b"izanagi/enforcement-source-ratification-receipt/v2\x00"
_TRUST_SCHEMA = "enforcement-source-ratification-trust-root/v1"
_GIT_ENV_ALLOWLIST = (
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "PATH",
    "SYSTEMROOT",
    "TMPDIR",
    "TZ",
)
_SOURCE_CLOSURE_PATHS = (
    "orchestrator/campaign/env_contract.py",
    "orchestrator/campaign/env_contract_activation.py",
    "orchestrator/campaign/execution_guard.py",
    "orchestrator/campaign/loop.py",
    "orchestrator/campaign/pipeline.py",
    "orchestrator/campaign/wal.py",
    "orchestrator/campaign/ident.py",
    "orchestrator/campaign/artifact_admission.py",
    "orchestrator/verifier/core.py",
    "orchestrator/verifier/dsg.py",
    "orchestrator/verifier/model.py",
    "orchestrator/verifier/parse.py",
    "orchestrator/verifier/__init__.py",
    "orchestrator/verifier/report.py",
    "orchestrator/campaign/s8c_preregistration.py",
    "orchestrator/campaign/s8c_preregistration_evidence.py",
    "orchestrator/campaign/s8c_generation_projection.py",
    "orchestrator/campaign/campaign_lock.py",
    "orchestrator/campaign/contract_loader_binding.py",
    "orchestrator/campaign/enforcement_source_ratification.py",
    "orchestrator/campaign/ed25519_verify.py",
    "orchestrator/campaign/enforcement_source_ratification_receipt.py",
    "orchestrator/campaign/guided.py",
    "orchestrator/campaign/replay.py",
    "orchestrator/qualification/artifacts.py",
    "orchestrator/qualification/t126_driver.py",
    "orchestrator/verifier/commit_receipt.py",
)
assert _SOURCE_CLOSURE_PATHS == campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
_UNSET = object()


@dataclass(frozen=True)
class _Closure:
    blob_map: dict[str, str]
    source_commit: str


@dataclass(frozen=True)
class _SignedRepo:
    path: Path
    key: Ed25519PrivateKey
    public_key: bytes
    closure: _Closure


def _git(repo: Path, *args: str) -> bytes:
    executable = shutil.which("git")
    if executable is None:
        pytest.fail("ratification receipt test requires git")
    env = {
        key: os.environ[key]
        for key in _GIT_ENV_ALLOWLIST
        if key in os.environ
    }
    env.update({
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_NO_REPLACE_OBJECTS": "1",
        "GIT_OPTIONAL_LOCKS": "0",
    })
    completed = subprocess.run(
        [executable, "-C", str(repo), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        env=env,
        timeout=30,
    )
    if completed.returncode != 0:
        pytest.fail(
            f"ratification receipt test git failed: args={args!r} "
            f"stderr={completed.stderr.decode(errors='replace')!r}"
        )
    return completed.stdout


def _head(repo: Path) -> str:
    return _git(repo, "rev-parse", "--verify", "HEAD^{commit}").decode(
        "ascii"
    ).strip()


def _commit(repo: Path, message: str, *relative_paths: str) -> str:
    _git(repo, "add", "--", *relative_paths)
    _git(
        repo,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", message,
    )
    return _head(repo)


def _repo(tmp_path: Path, name: str = "ratification-receipt-repo") -> Path:
    repo = tmp_path / name
    repo.mkdir()
    _git(repo, "init", "-q")
    marker = repo / "marker"
    marker.write_text("ratification receipt fixture\n", encoding="ascii")
    _commit(repo, "initialize receipt fixture", "marker")
    return repo


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("ascii")


def _public_bytes(key: Ed25519PrivateKey) -> bytes:
    return key.public_key().public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )


def _trust_root_document(public_key: bytes) -> bytes:
    return _canonical({
        "public_key_ed25519_base64": base64.b64encode(public_key).decode(
            "ascii"
        ),
        "schema_version": _TRUST_SCHEMA,
    }) + b"\n"


def _write(repo: Path, relative: str, raw: bytes) -> None:
    path = repo / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.is_symlink() or path.exists():
        path.unlink()
    path.write_bytes(raw)


def _write_closure(repo: Path, seed: str) -> dict[str, str]:
    all_raw: dict[str, bytes] = {}
    for relative in _SOURCE_CLOSURE_PATHS:
        raw = f"{seed}:{relative}\n".encode("ascii")
        _write(repo, relative, raw)
        all_raw[relative] = raw
    return {
        relative: hashlib.sha256(all_raw[relative]).hexdigest()
        for relative in campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS
    }


def _bootstrap(
    repo: Path,
    public_key: bytes,
    *,
    trust_raw: bytes | None = None,
) -> _Closure:
    blob_map = _write_closure(repo, "bootstrap")
    _write(
        repo,
        R.TRUST_ROOT_RELATIVE_PATH,
        _trust_root_document(public_key) if trust_raw is None else trust_raw,
    )
    _write(repo, R.RECEIPT_LEDGER_RELATIVE_PATH, b"")
    source_commit = _commit(
        repo,
        "install closure, trust root, and empty receipt ledger",
        *_SOURCE_CLOSURE_PATHS,
        R.TRUST_ROOT_RELATIVE_PATH,
        R.RECEIPT_LEDGER_RELATIVE_PATH,
    )
    return _Closure(blob_map, source_commit)


def _set_closure(repo: Path, seed: str) -> _Closure:
    blob_map = _write_closure(repo, seed)
    source_commit = _commit(
        repo,
        f"install source closure {seed}",
        *_SOURCE_CLOSURE_PATHS,
    )
    return _Closure(blob_map, source_commit)


def _signed_row(
    signed_repo: _SignedRepo,
    closure: _Closure,
    *,
    previous: bytes | None,
    serial: int,
    key: Ed25519PrivateKey | None = None,
    paths: list[str] | None = None,
    decision: str = "ratify",
    source_commit: str | None = None,
    closure_digest: str | None = None,
    closure_paths_sha256: str | None = None,
    trust_public_key: bytes | None = None,
    trust_root_sha256: str | None = None,
    previous_receipt_sha256: object = _UNSET,
    domain: bytes = _DOMAIN,
) -> bytes:
    signer = signed_repo.key if key is None else key
    if paths is None:
        paths = sorted(campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS)
    if closure_paths_sha256 is None:
        closure_paths_sha256 = hashlib.sha256(_canonical(paths)).hexdigest()
    if trust_public_key is None:
        trust_public_key = signed_repo.public_key
    if trust_root_sha256 is None:
        trust_root_sha256 = hashlib.sha256(trust_public_key).hexdigest()
    if previous_receipt_sha256 is _UNSET:
        previous_receipt_sha256 = (
            None if previous is None else hashlib.sha256(previous).hexdigest()
        )
    body: dict[str, object] = {
        "schema_version": R.RECEIPT_SCHEMA_VERSION,
        "source_commit": (
            closure.source_commit if source_commit is None else source_commit
        ),
        "ratification_serial": serial,
        "previous_receipt_sha256": previous_receipt_sha256,
        "decision": decision,
        "closure_paths": paths,
        "closure_paths_sha256": closure_paths_sha256,
        "closure_digest_sha256": (
            V1.closure_digest_sha256(closure.blob_map)
            if closure_digest is None
            else closure_digest
        ),
        "trust_root_sha256": trust_root_sha256,
    }
    body["signature_ed25519_base64"] = base64.b64encode(
        signer.sign(domain + _canonical(body))
    ).decode("ascii")
    return _canonical(body)


def _commit_ledger(repo: Path, raw: bytes, message: str) -> str:
    _write(repo, R.RECEIPT_LEDGER_RELATIVE_PATH, raw)
    return _commit(repo, message, R.RECEIPT_LEDGER_RELATIVE_PATH)


def _append_row(
    signed_repo: _SignedRepo,
    raw: bytes,
    closure: _Closure,
    *,
    serial: int,
    **overrides: object,
) -> tuple[bytes, bytes]:
    previous = raw.split(b"\n")[-2] if raw else None
    line = _signed_row(
        signed_repo,
        closure,
        previous=previous,
        serial=serial,
        **overrides,
    )
    extended = raw + line + b"\n"
    _commit_ledger(
        signed_repo.path, extended, f"append receipt serial {serial}"
    )
    return extended, line


def _commit_with_parents(
    repo: Path,
    tree_commit: str,
    parents: tuple[str, ...],
    message: str,
) -> str:
    tree = _git(repo, "rev-parse", f"{tree_commit}^{{tree}}").decode(
        "ascii"
    ).strip()
    args = [
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit-tree", tree,
    ]
    for parent in parents:
        args.extend(("-p", parent))
    args.extend(("-m", message))
    commit = _git(repo, *args).decode("ascii").strip()
    _git(repo, "update-ref", "HEAD", commit)
    return commit


def _dangling_same_tree_commit(repo: Path, tree_commit: str) -> str:
    tree = _git(repo, "rev-parse", f"{tree_commit}^{{tree}}").decode(
        "ascii"
    ).strip()
    return _git(
        repo,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit-tree", tree, "-m", "dangling same closure",
    ).decode("ascii").strip()


@pytest.fixture
def signed_repo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> _SignedRepo:
    repo = _repo(tmp_path)
    key = Ed25519PrivateKey.generate()
    public_key = _public_bytes(key)
    closure = _bootstrap(repo, public_key)
    monkeypatch.setattr(R, "_REPO_ROOT", repo)
    return _SignedRepo(repo, key, public_key, closure)


def test_valid_signed_receipt_for_current_closure_is_accepted(
    signed_repo: _SignedRepo,
) -> None:
    raw, _line = _append_row(
        signed_repo, b"", signed_repo.closure, serial=1
    )
    assert raw.endswith(b"\n")
    expected = V1.closure_digest_sha256(signed_repo.closure.blob_map)

    assert R.require_signed_ratification(signed_repo.closure.blob_map) == expected


def test_single_repository_binding_and_receipt_are_accepted(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    monkeypatch.setattr(B, "_REPO_ROOT", signed_repo.path)
    binding = B.capture_contract_loader_binding()

    assert binding.contract_loader_commit == _head(signed_repo.path)
    assert dict(binding.contract_loader_blob_sha256s) == signed_repo.closure.blob_map
    assert B.verify_ratified_contract_loader_binding(binding) == (
        V1.closure_digest_sha256(signed_repo.closure.blob_map)
    )


def test_three_receipt_chain_accepts_the_matching_earlier_row(
    signed_repo: _SignedRepo,
) -> None:
    raw = b""
    closures: list[_Closure] = []
    for serial in range(1, 4):
        closure = _set_closure(signed_repo.path, f"chain-{serial}")
        closures.append(closure)
        raw, _line = _append_row(
            signed_repo, raw, closure, serial=serial
        )

    target = closures[0]
    assert R.require_signed_ratification(
        target.blob_map
    ) == V1.closure_digest_sha256(target.blob_map)


def test_different_signing_key_on_earlier_row_rejects_the_whole_ledger(
    signed_repo: _SignedRepo,
) -> None:
    other_key = Ed25519PrivateKey.generate()
    raw, _line = _append_row(
        signed_repo,
        b"",
        signed_repo.closure,
        serial=1,
        key=other_key,
    )
    target = _set_closure(signed_repo.path, "right-key-target")
    _append_row(signed_repo, raw, target, serial=2)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="signature is invalid",
    ):
        R.require_signed_ratification(target.blob_map)


def test_signature_without_domain_prefix_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(
        signed_repo,
        b"",
        signed_repo.closure,
        serial=1,
        domain=b"",
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="signature is invalid",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_correctly_signed_duplicate_serial_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    raw, _line = _append_row(
        signed_repo, b"", signed_repo.closure, serial=1
    )
    target = _set_closure(signed_repo.path, "duplicate-serial")
    _append_row(signed_repo, raw, target, serial=1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="serial is not contiguous",
    ):
        R.require_signed_ratification(target.blob_map)


def test_correctly_signed_wrong_previous_hash_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    raw, _line = _append_row(
        signed_repo, b"", signed_repo.closure, serial=1
    )
    target = _set_closure(signed_repo.path, "wrong-previous")
    _append_row(
        signed_repo,
        raw,
        target,
        serial=2,
        previous_receipt_sha256="0" * 64,
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="previous hash is invalid",
    ):
        R.require_signed_ratification(target.blob_map)


def test_matching_digest_with_different_closure_paths_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    paths = sorted(campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS)[1:]
    _append_row(
        signed_repo,
        b"",
        signed_repo.closure,
        serial=1,
        paths=paths,
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="matching signed receipt is absent",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_v2_shallow_repository_is_rejected(
    signed_repo: _SignedRepo,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    shallow = tmp_path / "shallow"
    _git(
        tmp_path,
        "clone", "-q", "--depth", "2",
        f"file://{signed_repo.path}", os.fspath(shallow),
    )
    monkeypatch.setattr(R, "_REPO_ROOT", shallow)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="non-shallow repository",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)

    monkeypatch.setattr(R, "_assert_full_history_repository", lambda _root: None)
    assert R.require_signed_ratification(
        signed_repo.closure.blob_map
    ) == V1.closure_digest_sha256(signed_repo.closure.blob_map)


def test_v2_repository_with_grafts_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    raw_path = _git(
        signed_repo.path, "rev-parse", "--git-path", "info/grafts"
    ).decode("utf-8").strip()
    grafts = Path(raw_path)
    if not grafts.is_absolute():
        grafts = signed_repo.path / grafts
    grafts.parent.mkdir(parents=True, exist_ok=True)
    grafts.write_text(f"{_head(signed_repo.path)}\n", encoding="ascii")

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="cannot use Git grafts",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


@pytest.mark.parametrize("kind", ("symlink", "gitlink"), ids=("symlink", "gitlink"))
def test_v2_non_regular_ledger_entries_are_rejected(
    signed_repo: _SignedRepo,
    kind: str,
) -> None:
    disguised_ledger = _signed_row(
        signed_repo, signed_repo.closure, previous=None, serial=1
    ) + b"\n"
    ledger = signed_repo.path / R.RECEIPT_LEDGER_RELATIVE_PATH
    _git(
        signed_repo.path,
        "rm", "-q", "--cached", "--",
        R.RECEIPT_LEDGER_RELATIVE_PATH,
    )
    ledger.unlink()
    if kind == "symlink":
        payload = signed_repo.path / "disguised-ledger-payload"
        payload.write_bytes(disguised_ledger)
        payload_oid = _git(
            signed_repo.path, "hash-object", "-w", "--", payload.name
        ).decode("ascii").strip()
        _git(
            signed_repo.path,
            "update-index", "--add", "--cacheinfo",
            "120000", payload_oid, R.RECEIPT_LEDGER_RELATIVE_PATH,
        )
    else:
        _git(
            signed_repo.path,
            "update-index", "--add", "--cacheinfo",
            "160000", _head(signed_repo.path),
            R.RECEIPT_LEDGER_RELATIVE_PATH,
        )
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", f"replace ledger with {kind}",
    )
    tree_entry = _git(
        signed_repo.path,
        "ls-tree", "HEAD", "--", R.RECEIPT_LEDGER_RELATIVE_PATH,
    )
    expected_mode = b"120000" if kind == "symlink" else b"160000"
    assert tree_entry.startswith(expected_mode + b" ")
    if kind == "symlink":
        assert _git(
            signed_repo.path,
            "cat-file", "blob", f"HEAD:{R.RECEIPT_LEDGER_RELATIVE_PATH}",
        ) == disguised_ledger

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="ledger is not a regular file",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_source_commit_must_bind_signed_closure(
    signed_repo: _SignedRepo,
) -> None:
    signed_closure = signed_repo.closure
    different_source = _set_closure(signed_repo.path, "different-source")
    _append_row(
        signed_repo,
        b"",
        signed_closure,
        serial=1,
        source_commit=different_source.source_commit,
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="source commit closure digest disagrees",
    ):
        R.require_signed_ratification(signed_closure.blob_map)


def test_symlink_mode_source_path_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    relative = _SOURCE_CLOSURE_PATHS[0]
    oid = _git(
        signed_repo.path,
        "rev-parse",
        f"HEAD:{relative}",
    ).decode("ascii").strip()
    _git(
        signed_repo.path,
        "update-index",
        "--add",
        "--cacheinfo",
        "120000",
        oid,
        relative,
    )
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", "install symlink-mode source path",
    )
    source_commit = _head(signed_repo.path)
    tree_entry = _git(
        signed_repo.path,
        "ls-tree",
        source_commit,
        "--",
        relative,
    )
    assert tree_entry.startswith(b"120000 blob " + oid.encode("ascii"))

    _git(
        signed_repo.path,
        "update-index",
        "--add",
        "--cacheinfo",
        "100644",
        oid,
        relative,
    )
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", "restore regular-mode source path",
    )
    assert _git(
        signed_repo.path,
        "rev-parse",
        f"HEAD:{relative}",
    ).decode("ascii").strip() == oid

    symlink_source = _Closure(
        dict(signed_repo.closure.blob_map),
        source_commit,
    )
    _append_row(signed_repo, b"", symlink_source, serial=1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="source closure path is not a regular file",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_unreachable_source_commit_with_same_closure_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    dangling = _dangling_same_tree_commit(
        signed_repo.path, signed_repo.closure.source_commit
    )
    _append_row(
        signed_repo,
        b"",
        signed_repo.closure,
        serial=1,
        source_commit=dangling,
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="source commit is not reachable from HEAD",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_trust_root_changed_across_history_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    replacement_key = Ed25519PrivateKey.generate()
    replacement_public = _public_bytes(replacement_key)
    _write(
        signed_repo.path,
        R.TRUST_ROOT_RELATIVE_PATH,
        _trust_root_document(replacement_public),
    )
    _commit(
        signed_repo.path,
        "replace trust root while ledger is empty",
        R.TRUST_ROOT_RELATIVE_PATH,
    )
    target = _set_closure(signed_repo.path, "replacement-key-source")
    replacement_repo = _SignedRepo(
        signed_repo.path, replacement_key, replacement_public, target
    )
    _append_row(replacement_repo, b"", target, serial=1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="trust root changed across reachable history",
    ):
        R.require_signed_ratification(target.blob_map)


def test_divergent_signed_parent_chains_are_rejected_with_guidance(
    signed_repo: _SignedRepo,
) -> None:
    first_raw, _first = _append_row(
        signed_repo, b"", signed_repo.closure, serial=1
    )
    base = _head(signed_repo.path)

    _git(signed_repo.path, "checkout", "-q", "-b", "left", base)
    left_closure = _set_closure(signed_repo.path, "left-branch")
    left_raw, _left = _append_row(
        signed_repo, first_raw, left_closure, serial=2
    )
    left_tip = _head(signed_repo.path)

    _git(signed_repo.path, "checkout", "-q", "-b", "right", base)
    right_closure = _set_closure(signed_repo.path, "right-branch")
    right_raw, _right = _append_row(
        signed_repo, first_raw, right_closure, serial=2
    )
    right_tip = _head(signed_repo.path)
    merge = _commit_with_parents(
        signed_repo.path,
        left_tip,
        (left_tip, right_tip),
        "merge divergent signed chains",
    )

    parents = _git(
        signed_repo.path, "show", "-s", "--format=%P", merge
    ).decode("ascii").split()
    parent_oids = {
        _git(
            signed_repo.path,
            "rev-parse", f"{parent}:{R.RECEIPT_LEDGER_RELATIVE_PATH}",
        ).decode("ascii").strip()
        for parent in parents
    }
    assert len(parents) == 2
    assert len(parent_oids) == 2
    assert left_raw.startswith(first_raw) and right_raw.startswith(first_raw)
    assert not left_raw.startswith(right_raw)
    assert not right_raw.startswith(left_raw)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="divergent signed chains; serialize ledger appends through a "
        "single writer",
    ):
        R.require_signed_ratification(left_closure.blob_map)


def test_merge_with_identical_parent_ledgers_is_accepted(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    base = _head(signed_repo.path)
    _git(signed_repo.path, "checkout", "-q", "-b", "left", base)
    left_marker = signed_repo.path / "left-marker"
    left_marker.write_text("left\n", encoding="ascii")
    left_tip = _commit(signed_repo.path, "left non-ledger change", "left-marker")
    _git(signed_repo.path, "checkout", "-q", "-b", "right", base)
    right_marker = signed_repo.path / "right-marker"
    right_marker.write_text("right\n", encoding="ascii")
    right_tip = _commit(signed_repo.path, "right non-ledger change", "right-marker")
    merge = _commit_with_parents(
        signed_repo.path,
        left_tip,
        (left_tip, right_tip),
        "merge identical ledger parents",
    )

    parents = _git(
        signed_repo.path, "show", "-s", "--format=%P", merge
    ).decode("ascii").split()
    parent_oids = [
        _git(
            signed_repo.path,
            "rev-parse", f"{parent}:{R.RECEIPT_LEDGER_RELATIVE_PATH}",
        ).decode("ascii").strip()
        for parent in parents
    ]
    history = R._reachable_commit_parents(signed_repo.path, merge)
    assert merge in history
    assert len(parents) == 2
    assert parent_oids[0] == parent_oids[1]

    assert R.require_signed_ratification(
        signed_repo.closure.blob_map
    ) == V1.closure_digest_sha256(signed_repo.closure.blob_map)


def test_merge_with_prefix_parent_ledgers_is_accepted(
    signed_repo: _SignedRepo,
) -> None:
    first_raw, _first = _append_row(
        signed_repo, b"", signed_repo.closure, serial=1
    )
    base = _head(signed_repo.path)

    _git(signed_repo.path, "checkout", "-q", "-b", "short", base)
    marker = signed_repo.path / "short-parent-marker"
    marker.write_text("short parent\n", encoding="ascii")
    short_tip = _commit(
        signed_repo.path, "short parent keeps ledger", marker.name
    )

    _git(signed_repo.path, "checkout", "-q", "-b", "long", base)
    target = _set_closure(signed_repo.path, "long-parent")
    long_raw, _second = _append_row(
        signed_repo, first_raw, target, serial=2
    )
    long_tip = _head(signed_repo.path)
    merge = _commit_with_parents(
        signed_repo.path,
        long_tip,
        (long_tip, short_tip),
        "merge prefix ledger parents",
    )

    parents = _git(
        signed_repo.path, "show", "-s", "--format=%P", merge
    ).decode("ascii").split()
    parent_blobs = [
        _git(
            signed_repo.path,
            "cat-file", "blob", f"{parent}:{R.RECEIPT_LEDGER_RELATIVE_PATH}",
        )
        for parent in parents
    ]
    assert len(parents) == 2
    assert first_raw in parent_blobs
    assert long_raw in parent_blobs
    assert long_raw.startswith(first_raw)

    assert R.require_signed_ratification(
        target.blob_map
    ) == V1.closure_digest_sha256(target.blob_map)


def test_each_final_receipt_signature_is_verified_once(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    raw = b""
    target = signed_repo.closure
    for serial in range(1, 6):
        target = _set_closure(signed_repo.path, f"verify-once-{serial}")
        raw, _line = _append_row(
            signed_repo, raw, target, serial=serial
        )
    calls = 0
    real_verify = R.verify

    def recording_verify(
        public_key: bytes, message: bytes, signature: bytes,
    ) -> None:
        nonlocal calls
        calls += 1
        real_verify(public_key, message, signature)

    monkeypatch.setattr(R, "verify", recording_verify)
    R.require_signed_ratification(target.blob_map)

    assert calls == 5


def test_repeated_ledger_blob_oid_is_loaded_once(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    for index in range(3):
        marker = signed_repo.path / f"marker-{index}"
        marker.write_text(f"{index}\n", encoding="ascii")
        _commit(signed_repo.path, f"non-ledger commit {index}", marker.name)
    ledger_oid = _git(
        signed_repo.path,
        "rev-parse", f"HEAD:{R.RECEIPT_LEDGER_RELATIVE_PATH}",
    ).decode("ascii").strip()
    loaded: list[str] = []
    real_load = R._load_blob_exact

    def recording_load(
        root: Path, oid: str, expected_size: int, label: str,
    ) -> bytes:
        if label == "ledger":
            loaded.append(oid)
        return real_load(root, oid, expected_size, label)

    monkeypatch.setattr(R, "_load_blob_exact", recording_load)
    R.require_signed_ratification(signed_repo.closure.blob_map)

    assert loaded.count(ledger_oid) == 1


@pytest.mark.parametrize(
    "limit_kind",
    ("total-bytes", "line-bytes", "row-count", "json-depth"),
    ids=("total-bytes", "line-bytes", "row-count", "json-depth"),
)
def test_ledger_input_limits_fail_closed(
    signed_repo: _SignedRepo,
    limit_kind: str,
) -> None:
    if limit_kind == "total-bytes":
        raw = b"x" * (R._MAX_LEDGER_BYTES + 1)
        message = "ledger exceeds the byte limit"
    elif limit_kind == "line-bytes":
        raw = b"x" * (R._MAX_LEDGER_LINE_BYTES + 1) + b"\n"
        message = "row exceeds the byte limit"
    elif limit_kind == "row-count":
        raw = b"{}\n" * (R._MAX_LEDGER_ROWS + 1)
        message = "ledger exceeds the row limit"
    else:
        depth = R._MAX_JSON_NESTING + 1
        raw = b"[" * depth + b"0" + b"]" * depth + b"\n"
        message = "JSON nesting exceeds the limit"
    _commit_ledger(signed_repo.path, raw, f"install {limit_kind} ledger")

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match=message,
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_history_commit_limit_fails_closed(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(R, "_MAX_HISTORY_COMMITS", 1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="history exceeds the commit limit",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_historical_ledger_aggregate_byte_limit_fails_closed(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    monkeypatch.setattr(R, "_MAX_HISTORY_LEDGER_BYTES", 1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="historical ledger blobs exceed the aggregate byte limit",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_source_batch_aggregate_byte_limit_fails_closed(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    monkeypatch.setattr(R, "_MAX_SOURCE_BATCH_BYTES", 1)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="source closure batch exceeds the aggregate byte limit",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


@pytest.mark.parametrize(
    "variant",
    ("whitespace", "extra-lf"),
    ids=("whitespace", "extra-lf"),
)
def test_trust_root_requires_canonical_json_and_one_lf(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    variant: str,
) -> None:
    repo = _repo(tmp_path)
    key = Ed25519PrivateKey.generate()
    canonical = _trust_root_document(_public_bytes(key))
    if variant == "whitespace":
        trust_raw = canonical.replace(b"{", b"{ ", 1)
    else:
        trust_raw = canonical + b"\n"
    closure = _bootstrap(repo, _public_bytes(key), trust_raw=trust_raw)
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="not canonical JSON with exactly one trailing LF",
    ):
        R.require_signed_ratification(closure.blob_map)


def test_non_regular_trust_root_entry_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    trust = signed_repo.path / R.TRUST_ROOT_RELATIVE_PATH
    _git(
        signed_repo.path,
        "rm", "-q", "--cached", "--", R.TRUST_ROOT_RELATIVE_PATH,
    )
    trust.unlink()
    trust.symlink_to(_trust_root_document(signed_repo.public_key).decode("ascii"))
    _git(signed_repo.path, "add", "--", R.TRUST_ROOT_RELATIVE_PATH)
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", "replace trust root with symlink",
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="trust root is not a regular file",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_trust_root_deletion_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    trust = signed_repo.path / R.TRUST_ROOT_RELATIVE_PATH
    trust.unlink()
    _git(
        signed_repo.path,
        "add", "-u", "--", R.TRUST_ROOT_RELATIVE_PATH,
    )
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", "delete trust root",
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="trust root was deleted across reachable history",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_trust_root_must_be_introduced_exactly_once(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = _repo(tmp_path)
    key = Ed25519PrivateKey.generate()
    public_key = _public_bytes(key)
    base = _head(repo)

    _git(repo, "checkout", "-q", "-b", "left-root", base)
    left_marker = repo / "left-root-marker"
    left_marker.write_text("left root\n", encoding="ascii")
    _git(repo, "add", "--", left_marker.name)
    left_closure = _bootstrap(repo, public_key)
    left_tip = _head(repo)

    _git(repo, "checkout", "-q", "-b", "right-root", base)
    right_marker = repo / "right-root-marker"
    right_marker.write_text("right root\n", encoding="ascii")
    _git(repo, "add", "--", right_marker.name)
    _bootstrap(repo, public_key)
    right_tip = _head(repo)
    _commit_with_parents(
        repo,
        left_tip,
        (left_tip, right_tip),
        "merge two trust-root introductions",
    )
    monkeypatch.setattr(R, "_REPO_ROOT", repo)

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="trust root must be introduced exactly once",
    ):
        R.require_signed_ratification(left_closure.blob_map)


def test_committed_receipt_rewrite_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    replacement = _set_closure(signed_repo.path, "replacement-row")
    line = _signed_row(
        signed_repo, replacement, previous=None, serial=1
    )
    _commit_ledger(signed_repo.path, line + b"\n", "rewrite receipt row")

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="not a strict prefix extension",
    ):
        R.require_signed_ratification(replacement.blob_map)


@pytest.mark.parametrize(
    "variant",
    ("whitespace", "duplicate-key", "missing-lf"),
    ids=("whitespace", "duplicate-key", "missing-lf"),
)
def test_receipt_rows_require_canonical_jsonl(
    signed_repo: _SignedRepo,
    variant: str,
) -> None:
    line = _signed_row(
        signed_repo, signed_repo.closure, previous=None, serial=1
    )
    if variant == "whitespace":
        raw = line.replace(b"{", b"{ ", 1) + b"\n"
        message = "not canonical JSON"
    elif variant == "duplicate-key":
        raw = line.replace(b"{", b'{"decision":"ratify",', 1) + b"\n"
        message = "duplicate key"
    else:
        raw = line
        message = "not newline terminated"
    _commit_ledger(signed_repo.path, raw, f"install {variant} receipt row")

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match=message,
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_one_commit_cannot_add_two_receipt_rows(
    signed_repo: _SignedRepo,
) -> None:
    first = _signed_row(
        signed_repo, signed_repo.closure, previous=None, serial=1
    )
    second = _signed_row(
        signed_repo, signed_repo.closure, previous=first, serial=2
    )
    _commit_ledger(
        signed_repo.path, first + b"\n" + second + b"\n", "add two rows"
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="added more than one row",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_committed_ledger_deletion_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(signed_repo, b"", signed_repo.closure, serial=1)
    ledger = signed_repo.path / R.RECEIPT_LEDGER_RELATIVE_PATH
    ledger.unlink()
    _git(
        signed_repo.path,
        "add", "-u", "--", R.RECEIPT_LEDGER_RELATIVE_PATH,
    )
    _git(
        signed_repo.path,
        "-c", "user.email=t1629-fixture@example.invalid",
        "-c", "user.name=T1629 fixture",
        "commit", "-q", "-m", "delete receipt ledger",
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="ledger was deleted in committed history",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_non_ratify_decision_is_rejected(
    signed_repo: _SignedRepo,
) -> None:
    _append_row(
        signed_repo,
        b"",
        signed_repo.closure,
        serial=1,
        decision="reject",
    )

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="decision is not ratify",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_ambient_git_repository_override_is_rejected(
    signed_repo: _SignedRepo,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("GIT_DIR", os.fspath(signed_repo.path / ".git"))

    with pytest.raises(
        R.EnforcementSourceRatificationReceiptError,
        match="repository/object overrides",
    ):
        R.require_signed_ratification(signed_repo.closure.blob_map)


def test_v1_dag_and_git_hardening_are_reused() -> None:
    assert R._v1_git is V1._git
    assert R._git_env is V1._git_env
    assert R._ledger_blob_oids is V1._ledger_blob_oids
    assert R._reachable_commit_parents is V1._reachable_commit_parents
    assert R._assert_full_history_repository is V1._assert_full_history_repository
    assert R._GIT_HARDEN is V1._GIT_HARDEN
    assert R._GIT_EXECUTABLE == Path("/usr/bin/git")
    assert "PATH" not in R._GIT_ENV_ALLOWLIST
    assert R._FORBIDDEN_AMBIENT_GIT_ENV is V1._FORBIDDEN_AMBIENT_GIT_ENV
    assert not hasattr(R, "_is_subsequence")


def test_production_has_no_cryptography_dependency() -> None:
    tree = ast.parse(Path(R.__file__).read_text(encoding="utf-8"))
    imported = {
        alias.name.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported.update(
        node.module.split(".", 1)[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
        and node.level == 0
        and node.module not in (None, "__future__")
    )
    assert "cryptography" not in imported


def test_plain_runner_harness_invokes_pytest_main() -> None:
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    run_functions = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name == "_run"
    ]
    assert len(run_functions) == 1
    pytest_main_calls = [
        node
        for node in ast.walk(run_functions[0])
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "pytest"
        and node.func.attr == "main"
    ]
    assert len(pytest_main_calls) == 1


def _run() -> int:
    """Keep this new test file inside the repository plain-runner contract."""
    return int(pytest.main([__file__, "-q"]))


if __name__ == "__main__":
    raise SystemExit(_run())
