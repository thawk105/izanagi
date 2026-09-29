"""Scoped receipt acceptance and rejection in a synthetic linked worktree."""

import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from orchestrator.tests import test_dev_wave_land as BASE


LAND = BASE.LAND
SCOPED = LAND._scoped_acceptance


def _setup(repo, *, gate_failure=False):
    main = repo.main
    for name in ("scoped_acceptance.py", "scoped_acceptance_launcher.py"):
        (main / "tools" / name).write_bytes((BASE.ROOT / "tools" / name).read_bytes())
    (main / "tools/acceptance_launcher.py").write_bytes(
        (BASE.ROOT / "tools/acceptance_launcher.py").read_bytes()
    )
    if gate_failure:
        (main / "tools/check_docs.py").write_text("raise SystemExit(1)\n")
    (main / "tools/spool_fold.py").write_text("raise SystemExit(0)\n")
    tests = main / "orchestrator/tests"
    tests.mkdir(parents=True)
    (tests / "conftest.py").write_text(
        '_REAL_REPO_NODE_INVENTORY = frozenset({"test_real_repo_serialization.py::test_real"})\n'
    )
    for name in SCOPED.FIXED_FILES:
        (tests / name).write_text("def test_present(): pass\n")
    (tests / "test_campaign.py").write_text(
        "def test_certified_writer_authorization_caller_inventory_is_closed(): pass\n"
    )
    BASE._git(main, "add", "-A", "tools", "orchestrator/tests")
    BASE._git(main, "commit", "-qm", "scoped main")
    repo.base = BASE._git(main, "rev-parse", "HEAD")
    wave = repo.waves["one"]
    BASE._git(wave, "merge", "--ff-only", repo.base)
    return wave


def _request(repo, *, implementation=False, gate_failure=False):
    wave = _setup(repo, gate_failure=gate_failure)
    doc = wave / "docs/notes.md"
    doc.write_text("# note\n")
    if implementation:
        (wave / "tools/changed.py").write_text("pass\n")
    BASE._git(wave, "add", "-A")
    BASE._git(wave, "commit", "-qm", "wave")
    request = repo.request(wave, base=repo.base)
    return request


def _scoped_payload(request):
    payload = BASE._receipt_payload(request.acceptance_receipt)
    main, tip = request.tested_main_sha, request.tested_wave_tip_sha
    plan = SCOPED.plan(request.wave_worktree, main, tip)
    payload.update({
        "schema_version": LAND._SCOPED_RECEIPT_SCHEMA,
        "authority_kind": "dev-wave-scoped-acceptance-launcher",
        "launcher_source_revision": "tested-main",
        "launcher_blob_sha": BASE._git(
            request.wave_worktree, "rev-parse",
            f"{main}:tools/scoped_acceptance_launcher.py",
        ),
        "launcher_executed_sha256": BASE._git_blob_sha256(
            request.wave_worktree, main, "tools/scoped_acceptance_launcher.py",
        ),
        "selector_blob_sha": BASE._git(
            request.wave_worktree, "rev-parse", f"{main}:tools/scoped_acceptance.py",
        ),
        "selector_executed_sha256": BASE._git_blob_sha256(
            request.wave_worktree, main, "tools/scoped_acceptance.py",
        ),
        "classification": plan["classification"],
        "selection": plan["selection"],
        "direct_gate_results": [
            {"argv": argv, "rc": 0, "log_sha256": hashlib.sha256(b"").hexdigest()}
            for argv in SCOPED.GATES
        ],
    })
    BASE._write_receipt(request.acceptance_receipt, payload)
    return payload


def test_scoped_docs_land_and_v5_control():
    with BASE._repo() as repo:
        request = _request(repo)
        payload = _scoped_payload(request)
        assert payload["classification"]["eligible"] is True
        assert BASE._land(request).rc == LAND.RC_OK
    BASE.test_land_accepts_receipt_bound_to_wave_tip_and_emits_digest()


def test_implementation_tip_rejected_independent_of_receipt_claim():
    with BASE._repo() as repo:
        request = _request(repo, implementation=True)
        payload = _scoped_payload(request)
        assert payload["classification"]["eligible"] is False
        payload["classification"]["eligible"] = True
        payload["classification"]["reasons"] = []
        BASE._write_receipt(request.acceptance_receipt, payload)
        original = SCOPED.plan
        try:
            SCOPED.plan = lambda *_args: {
                "classification": payload["classification"],
                "selection": payload["selection"],
            }
            assert BASE._land(request).reason == "acceptance-receipt-rejected"
        finally:
            SCOPED.plan = original


def test_scoped_receipt_rederived_on_eligible_tip():
    with BASE._repo() as repo:
        request = _request(repo)
        payload = _scoped_payload(request)
        assert payload["classification"]["eligible"] is True
        assert payload["selection"]["eligible"] is True
        assert payload["selection"]["files"]
        payload["selection"]["files"] = []
        payload["selection"]["selection_digest"] = SCOPED._digest({
            "nodes": payload["selection"]["nodes"], "files": [],
        })
        BASE._write_receipt(request.acceptance_receipt, payload)
        assert BASE._land(request).reason == "acceptance-receipt-rejected"


def test_v5_rejects_only_extra_scoped_field():
    with BASE._repo() as repo:
        request = _request(repo)
        payload = BASE._receipt_payload(request.acceptance_receipt)
        assert payload["schema_version"] == LAND._ACCEPTANCE_RECEIPT_SCHEMA
        assert payload["authority_kind"] == LAND._ACCEPTANCE_AUTHORITY_KINDS[
            payload["launcher_source_revision"]
        ]
        assert set(payload) == LAND._ACCEPTANCE_RECEIPT_FIELDS
        payload["classification"] = SCOPED.plan(
            request.wave_worktree, request.tested_main_sha,
            request.tested_wave_tip_sha,
        )["classification"]
        BASE._write_receipt(request.acceptance_receipt, payload)
        assert BASE._land(request).reason == "acceptance-receipt-rejected"


@pytest.mark.parametrize("mutation", [
    "schema", "wave", "main", "tip", "selection", "classification",
    "gate", "selector", "launcher",
])
def test_scoped_receipt_drift_rejected(mutation):
    with BASE._repo() as repo:
        request = _request(repo)
        payload = _scoped_payload(request)
        if mutation == "schema":
            payload["schema_version"] = LAND._ACCEPTANCE_RECEIPT_SCHEMA
        elif mutation == "wave":
            payload["acceptance_wave"] = "wrong-wave"
        elif mutation == "main":
            payload["tested_main"] = "0" * 40
        elif mutation == "tip":
            payload["tested_tip"] = "0" * 40
        elif mutation == "selection":
            payload["selection"]["files"] = []
        elif mutation == "classification":
            payload["classification"]["eligible"] = False
        elif mutation == "gate":
            payload["direct_gate_results"][0]["rc"] = 1
        elif mutation == "selector":
            payload["selector_blob_sha"] = "0" * 40
        elif mutation == "launcher":
            payload["launcher_blob_sha"] = "0" * 40
        BASE._write_receipt(request.acceptance_receipt, payload)
        assert BASE._land(request).reason == "acceptance-receipt-rejected"


def test_release_authority_dispatches_scoped():
    with BASE._repo() as repo:
        request = _request(repo)
        _scoped_payload(request)
        assert LAND._release_authority_digest(
            request.acceptance_receipt, request.acceptance_wave,
        ) == hashlib.sha256(request.acceptance_receipt.read_bytes()).hexdigest()


@pytest.mark.parametrize("path", LAND._SCOPED_FORWARD_BLOBS)
def test_scoped_forward_main_blob_drift_rejected(path):
    with BASE._repo() as repo:
        request = _request(repo)
        _scoped_payload(request)
        main = repo.main
        file = main / path
        file.write_bytes(file.read_bytes() + b"\n# drift\n")
        BASE._git(main, "add", path)
        BASE._git(main, "commit", "-qm", "drift")
        incorporated = BASE._git(main, "rev-parse", "HEAD")
        merge = type("Forward", (), {"incorporated_main_sha": incorporated})()
        with pytest.raises(LAND._Reject):
            LAND._verify_forward_main_scoped_blobs(
                SimpleNamespace(wave=request.wave_worktree),
                request.tested_main_sha, (merge,),
            )


def test_gate_failure_leaves_no_receipt(tmp_path):
    from tools import scoped_acceptance_launcher as LAUNCHER
    import os
    with BASE._repo() as repo:
        request = _request(repo, gate_failure=True)
        payload = BASE._receipt_payload(request.acceptance_receipt)
        empty_receipt = tmp_path / "scoped-receipt.json"
        empty_receipt.write_bytes(b"")
        read_outcome, write_outcome = os.pipe()
        read_completion, write_completion = os.pipe()
        try:
            argv = [
                "--repo-root", str(request.wave_worktree),
                "--wave", request.acceptance_wave,
                "--lease-holder", payload["lease_holder"],
                "--tested-main", request.tested_main_sha,
                "--tested-tip", request.tested_wave_tip_sha,
                "--launcher-source-revision", "tested-main",
                "--launcher-blob-sha", BASE._git(
                    request.wave_worktree, "rev-parse",
                    f"{request.tested_main_sha}:tools/scoped_acceptance_launcher.py",
                ),
                "--launcher-executed-sha256", BASE._git_blob_sha256(
                    request.wave_worktree, request.tested_main_sha,
                    "tools/scoped_acceptance_launcher.py",
                ),
                "--waiter-executed-sha256", payload["waiter_executed_sha256"],
                "--waiter-blob-sha", payload["waiter_blob_sha"],
                "--receipt-file", str(empty_receipt),
                "--log-file", str(tmp_path / "runner.log"),
                "--pre-fingerprint-json", json.dumps(payload["pre_fingerprint"]),
                "--env-projection-json", json.dumps(payload["env_projection"]),
                "--outcome-fd", str(write_outcome),
                "--completion-fd", str(read_completion),
                "--", "python3", "tools/run_tests.py",
            ]
            assert LAUNCHER.main(argv) != 0
            assert empty_receipt.read_bytes() == b""
        finally:
            for fd in (read_outcome, write_outcome, read_completion, write_completion):
                os.close(fd)


def test_runner_scoped_shape_keeps_full_suite_shape_closed():
    import os
    from tools import run_tests as RUNNER
    targets = ["orchestrator/tests/test_check_docs.py"]
    digest = hashlib.sha256(json.dumps(targets, separators=(",", ":")).encode()).hexdigest()
    key = "IZANAGI_SCOPED_ACCEPTANCE_TARGETS_SHA256"
    previous = os.environ.get(key)
    try:
        os.environ[key] = digest
        normalized = RUNNER._normalize_args(targets)
        assert RUNNER._is_scoped_acceptance_run(normalized)
        assert RUNNER._is_receipted_acceptance_run(normalized)
        assert not RUNNER._is_acceptance_run(normalized)
        os.environ[key] = "0" * 64
        assert not RUNNER._is_scoped_acceptance_run(normalized)
    finally:
        if previous is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = previous


def test_wait_scoped_flag_is_opt_in():
    from tools import dev_wave_wait as WAIT
    common = ["acceptance", "--wave", "wave", "--receipt-file", "/tmp/receipt.json",
              "--log-file", "/tmp/log.txt", "--", "python3", "tools/run_tests.py"]
    assert WAIT._parse_cli(common)[1].scoped is False
    scoped = common[:1] + ["--scoped"] + common[1:]
    assert WAIT._parse_cli(scoped)[1].scoped is True
