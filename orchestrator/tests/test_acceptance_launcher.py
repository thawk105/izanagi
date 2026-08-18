import hashlib
import json
from pathlib import Path
import sys
import tempfile

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import acceptance_launcher as launcher


_SHA1_A = "a" * 40
_SHA1_B = "b" * 40
_SHA1_C = "c" * 40
_SHA1_D = "d" * 40
_SHA256_E = "e" * 64
_SHA256_F = "f" * 64
_SHA256_3 = "3" * 64
_SHA256_4 = "4" * 64
_SOURCE = b"def main(argv):\n    return 0\n"


def _config(root: Path, source_revision: str = "tested-main") -> launcher._Config:
    return launcher._Config(
        repo_root=root,
        wave="t1283-trusted-launcher",
        lease_holder="0123456789ab",
        tested_main=_SHA1_A,
        tested_tip=_SHA1_B,
        launcher_source_revision=source_revision,
        launcher_blob_sha=_SHA1_C,
        launcher_executed_sha256=_SHA256_E,
        waiter_executed_sha256=_SHA256_F,
        waiter_blob_sha=_SHA1_D,
        receipt_file=root / "receipt.json",
        log_file=root / "runner.log",
        outcome_fd=10,
        completion_fd=11,
        pre_fingerprint={
            "digest": _SHA256_3,
            "head_sha": _SHA1_A,
            "status_bytes": 0,
            "diff_bytes": 1,
            "submodule_status_bytes": 2,
        },
        env_projection={
            "PYTEST_ADDOPTS": "-q",
            "PYTEST_PLUGINS": None,
            "IZANAGI_TASK_RUN_ID": "run-1",
            "IZANAGI_TASK_RUNS_ROOT": "/tmp/task-runs",
        },
    )


def _completion():
    return {
        "effective_scheduler": "loadgroup",
        "post_fingerprint": {
            "digest": _SHA256_4,
            "head_sha": _SHA1_B,
            "status_bytes": 3,
            "diff_bytes": 4,
            "submodule_status_bytes": 5,
        },
        "red_check": None,
    }


def _touch_empty(path: Path) -> None:
    path.open("xb").close()


def _successful_blob_runner(source: bytes, canonical_path: Path, log_file: Path) -> int:
    assert source == _SOURCE
    assert canonical_path.is_absolute()
    log_file.write_bytes(b"runner output\n")
    return 0


def test_m3_runner_digest_mismatch_is_rejected():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        launcher._launch(
            config,
            ("python3", "tools/run_tests.py"),
            blob_reader=lambda _repo, _tip: _SOURCE,
            blob_runner=_successful_blob_runner,
            outcome_writer=lambda _value: None,
            completion_reader=_completion,
        )
        assert config.receipt_file.read_bytes()
        config.receipt_file.write_bytes(b"")
        sources = iter((_SOURCE, _SOURCE + b"# drift\n"))
        try:
            launcher._launch(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=lambda _repo, _tip: next(sources),
                blob_runner=_successful_blob_runner,
                outcome_writer=lambda _value: None,
                completion_reader=_completion,
            )
        except launcher.LauncherFailure as exc:
            assert "tested-tip blob" in str(exc)
        else:
            raise AssertionError("runner digest mismatch was accepted")
        assert config.receipt_file.read_bytes() == b""


def test_nonexact_runner_argv_is_rejected():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        for argv in (
            ("/usr/bin/python3", "tools/run_tests.py"),
            ("python3", str(root / "tools/run_tests.py")),
            ("python3", "tools/run_tests.py", "-q"),
        ):
            try:
                launcher._validate_config(config, argv)
            except launcher.LauncherFailure as exc:
                assert "argv" in str(exc)
            else:
                raise AssertionError(f"nonexact argv was accepted: {argv!r}")


def test_blob_bootstrap_uses_canonical_file_without_pathname_reload():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        (root / "tools").mkdir()
        canonical_path = root / "tools/run_tests.py"
        canonical_path.write_text("raise RuntimeError('pathname read')\n")
        source = (
            "def main(argv):\n"
            f"    expected = {str(canonical_path)!r}\n"
            "    return 0 if __file__ == expected and argv == [] else 9\n"
        ).encode("ascii")
        log_file = root / "runner.log"
        assert launcher._run_blob(source, canonical_path, log_file) == 0


def test_receipt_is_exact_canonical_json_bytes():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        (root / "tools").mkdir()
        # A pathname reload would execute this instead of the supplied blob.
        (root / "tools/run_tests.py").write_text(
            "raise RuntimeError('pathname read')\n"
        )
        config = _config(root)
        _touch_empty(config.receipt_file)
        outcomes = []
        launcher._launch(
            config,
            ("python3", "tools/run_tests.py"),
            blob_reader=lambda _repo, _tip: _SOURCE,
            blob_runner=_successful_blob_runner,
            outcome_writer=outcomes.append,
            completion_reader=_completion,
        )
        runner_sha = hashlib.sha256(_SOURCE).hexdigest()
        log_sha = hashlib.sha256(b"runner output\n").hexdigest()
        expected_outcome = (
            '{"child_rc":0,"log_sha256":"'
            + log_sha
            + '","runner_executed_sha256":"'
            + runner_sha
            + '"}\n'
        ).encode("ascii")
        assert outcomes == [expected_outcome]
        expected = (
            '{"acceptance_wave":"t1283-trusted-launcher",'
            '"argv":["python3","tools/run_tests.py"],'
            '"authority_kind":"dev-wave-acceptance-launcher",'
            '"checker_blob_sha":null,"checker_rc":null,'
            '"checker_receipt_sha256":null,"checker_status":null,'
            '"child_rc":0,"effective_scheduler":"loadgroup",'
            '"env_projection":{"IZANAGI_TASK_RUNS_ROOT":"/tmp/task-runs",'
            '"IZANAGI_TASK_RUN_ID":"run-1",'
            '"PYTEST_ADDOPTS":"-q","PYTEST_PLUGINS":null},'
            '"flake_nodeids":[],'
            '"launcher_blob_sha":"' + _SHA1_C + '",'
            '"launcher_executed_sha256":"' + _SHA256_E + '",'
            '"launcher_source_revision":"tested-main",'
            '"lease_holder":"0123456789ab","log_sha256":"' + log_sha + '",'
            '"post_fingerprint":{"diff_bytes":4,"digest":"' + _SHA256_4
            + '","head_sha":"' + _SHA1_B
            + '","status_bytes":3,"submodule_status_bytes":5},'
            '"pre_fingerprint":{"diff_bytes":1,"digest":"' + _SHA256_3
            + '","head_sha":"' + _SHA1_A
            + '","status_bytes":0,"submodule_status_bytes":2},'
            '"red_nodeids":[],"resolved_runner_path":"tools/run_tests.py",'
            '"runner_executed_sha256":"' + runner_sha + '",'
            '"schema_version":"dev-wave-acceptance-receipt/v5",'
            '"tested_main":"' + _SHA1_A + '","tested_tip":"' + _SHA1_B + '",'
            '"verdict":"child-green","waiter_blob_sha":"' + _SHA1_D + '",'
            '"waiter_executed_sha256":"' + _SHA256_F + '"}\n'
        ).encode("ascii")
        assert config.receipt_file.read_bytes() == expected
        assert expected == launcher._canonical_json_bytes(json.loads(expected))


def test_trusted_mode_authority_kind():
    with tempfile.TemporaryDirectory() as raw_root:
        config = _config(Path(raw_root).resolve(), "tested-main")
        receipt = launcher._receipt_bytes(
            config,
            ("python3", "tools/run_tests.py"),
            0,
            "1" * 64,
            "2" * 64,
            _completion(),
        )
        assert json.loads(receipt)["authority_kind"] == (
            "dev-wave-acceptance-launcher"
        )


def test_unknown_effective_scheduler_is_rejected() -> None:
    with tempfile.TemporaryDirectory() as raw_root:
        config = _config(Path(raw_root).resolve())
        completion = _completion()
        completion["effective_scheduler"] = "unknown"

        try:
            launcher._receipt_bytes(
                config,
                ("python3", "tools/run_tests.py"),
                0,
                "1" * 64,
                "2" * 64,
                completion,
            )
        except launcher.LauncherFailure as exc:
            assert str(exc) == "invalid effective scheduler"
        else:
            raise AssertionError("unknown effective scheduler was accepted")


def test_bootstrap_mode_authority_kind():
    with tempfile.TemporaryDirectory() as raw_root:
        config = _config(Path(raw_root).resolve(), "tested-tip-bootstrap")
        receipt = launcher._receipt_bytes(
            config,
            ("python3", "tools/run_tests.py"),
            0,
            "1" * 64,
            "2" * 64,
            _completion(),
        )
        assert json.loads(receipt)["authority_kind"] == (
            "dev-wave-acceptance-launcher-bootstrap-tip"
        )


def test_negative_child_rc_is_normalized():
    assert launcher._normalize_child_rc(-9) == 137
    assert launcher._normalize_child_rc(7) == 7


def _run() -> int:
    passed = 0
    failed = 0
    for name, test in sorted(globals().items()):
        if not name.startswith("test_") or not callable(test):
            continue
        try:
            test()
            print(f"PASS {name}")
            passed += 1
        except AssertionError as exc:
            print(f"FAIL {name}: {exc}")
            failed += 1
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR {name}: {type(exc).__name__}: {exc}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
