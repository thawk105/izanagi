import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from tools import acceptance_launcher as launcher
from tools.pegasus import dispatch_compute as dispatcher


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


def _binding_report(
    index: int,
    *,
    nonce: str,
    tested_main: str,
    digest: str,
    shard_count: int,
) -> dict[str, object]:
    return {
        "schema_version": launcher._BINDING_REPORT_SCHEMA,
        "tested_main": tested_main,
        "nonce": nonce,
        "runner_executed_sha256": digest,
        "shard_count": shard_count,
        "shard_index": index,
    }


def _emit_binding_reports(
    source: bytes,
    environment: dict[str, str],
    pass_fds: tuple[int, ...],
    *,
    indexes: tuple[int, ...] | None = None,
    nonce: str | None = None,
    tested_main: str | None = None,
    digest: str | None = None,
    self_reported_k: int | None = None,
) -> None:
    assert pass_fds == (int(environment[launcher._BINDING_FD_ENV]),)
    shard_count = int(environment[launcher._ACCEPTANCE_SHARDS_ENV])
    report_k = shard_count if self_reported_k is None else self_reported_k
    report_indexes = tuple(range(shard_count)) if indexes is None else indexes
    for index in report_indexes:
        payload = _binding_report(
            index,
            nonce=environment[launcher._BINDING_NONCE_ENV] if nonce is None else nonce,
            tested_main=(
                environment[launcher._BINDING_TESTED_MAIN_ENV]
                if tested_main is None else tested_main
            ),
            digest=hashlib.sha256(source).hexdigest() if digest is None else digest,
            shard_count=report_k,
        )
        os.write(pass_fds[0], launcher._canonical_json_bytes(payload))


def _launch_with_reports(
    config: launcher._Config,
    runner_argv: tuple[str, ...],
    *,
    blob_reader,
    blob_runner,
    shard_count: str = "1",
    report_options: dict[str, object] | None = None,
    **kwargs,
) -> None:
    previous = os.environ.get(launcher._ACCEPTANCE_SHARDS_ENV)
    os.environ[launcher._ACCEPTANCE_SHARDS_ENV] = shard_count

    def run_bound(source, canonical_path, log_file, *, environment, pass_fds):
        rc = blob_runner(source, canonical_path, log_file)
        _emit_binding_reports(
            source,
            environment,
            pass_fds,
            **({} if report_options is None else report_options),
        )
        return rc

    try:
        launcher._launch(
            config,
            runner_argv,
            blob_reader=blob_reader,
            blob_runner=run_bound,
            **kwargs,
        )
    finally:
        if previous is None:
            os.environ.pop(launcher._ACCEPTANCE_SHARDS_ENV, None)
        else:
            os.environ[launcher._ACCEPTANCE_SHARDS_ENV] = previous


def _unreachable(*_args, **_kwargs):
    raise AssertionError("unreachable callback was called")


def test_matching_main_and_tip_runner_blobs_execute_tested_main_source():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        main_source = bytes(bytearray(_SOURCE))
        tip_source = bytes(bytearray(_SOURCE))
        refreshed_main_source = bytes(bytearray(_SOURCE))
        assert main_source is not tip_source
        sources = iter((main_source, tip_source, refreshed_main_source))
        revisions = []
        executed_sources = []
        outcomes = []
        completion_calls = []

        def read_blob(_repo, revision):
            revisions.append(revision)
            return next(sources)

        def run_blob(source, canonical_path, log_file):
            executed_sources.append(source)
            assert canonical_path.is_absolute()
            log_file.write_bytes(b"runner output\n")
            return 0

        def read_completion():
            completion_calls.append(True)
            return _completion()

        _launch_with_reports(
            config,
            ("python3", "tools/run_tests.py"),
            blob_reader=read_blob,
            blob_runner=run_blob,
            shard_count="3",
            outcome_writer=outcomes.append,
            completion_reader=read_completion,
        )

        assert revisions == [_SHA1_A, _SHA1_B, _SHA1_A]
        assert len(executed_sources) == 1
        assert executed_sources[0] is main_source
        assert len(outcomes) == 1
        assert completion_calls == [True]
        assert config.receipt_file.read_bytes()


def test_main_tip_runner_blob_mismatch_is_rejected_before_execution():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        revisions = []

        def read_blob(_repo, revision):
            revisions.append(revision)
            return _SOURCE if revision == _SHA1_A else _SOURCE + b"# tip\n"

        try:
            launcher._launch(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=read_blob,
                blob_runner=_unreachable,
                outcome_writer=_unreachable,
                completion_reader=_unreachable,
            )
        except launcher.LauncherFailure as exc:
            assert str(exc) == "tested-main and tested-tip runner blobs differ"
        else:
            raise AssertionError("runner blob divergence was accepted")

        assert revisions == [_SHA1_A, _SHA1_B]
        assert config.receipt_file.read_bytes() == b""


def test_missing_tested_main_runner_is_rejected_before_execution():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        revisions = []

        def read_blob(_repo, revision):
            revisions.append(revision)
            if revision == _SHA1_A:
                raise launcher.LauncherFailure("missing tested-main runner")
            return _SOURCE

        try:
            launcher._launch(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=read_blob,
                blob_runner=_unreachable,
                outcome_writer=_unreachable,
                completion_reader=_unreachable,
            )
        except launcher.LauncherFailure as exc:
            assert str(exc) == "missing tested-main runner"
        else:
            raise AssertionError("missing tested-main runner was accepted")

        assert revisions == [_SHA1_A]
        assert config.receipt_file.read_bytes() == b""


def test_missing_tested_tip_runner_is_rejected_before_execution():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        revisions = []

        def read_blob(_repo, revision):
            revisions.append(revision)
            if revision == _SHA1_B:
                raise launcher.LauncherFailure("missing tested-tip runner")
            return _SOURCE

        try:
            launcher._launch(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=read_blob,
                blob_runner=_unreachable,
                outcome_writer=_unreachable,
                completion_reader=_unreachable,
            )
        except launcher.LauncherFailure as exc:
            assert str(exc) == "missing tested-tip runner"
        else:
            raise AssertionError("missing tested-tip runner was accepted")

        assert revisions == [_SHA1_A, _SHA1_B]
        assert config.receipt_file.read_bytes() == b""


def test_m3_runner_digest_mismatch_is_rejected():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        _launch_with_reports(
            config,
            ("python3", "tools/run_tests.py"),
            blob_reader=lambda _repo, _tip: _SOURCE,
            blob_runner=_successful_blob_runner,
            outcome_writer=lambda _value: None,
            completion_reader=_completion,
        )
        assert config.receipt_file.read_bytes()
        config.receipt_file.write_bytes(b"")
        sources = iter((_SOURCE, _SOURCE, _SOURCE + b"# drift\n"))
        revisions = []

        def read_blob(_repo, revision):
            revisions.append(revision)
            return next(sources)

        try:
            _launch_with_reports(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=read_blob,
                blob_runner=_successful_blob_runner,
                outcome_writer=lambda _value: None,
                completion_reader=_completion,
            )
        except launcher.LauncherFailure as exc:
            assert "tested-main blob" in str(exc)
        else:
            raise AssertionError("runner digest mismatch was accepted")
        assert revisions == [_SHA1_A, _SHA1_B, _SHA1_A]
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


def test_shard_activation_does_not_expand_exact_outer_runner_argv():
    saved = os.environ.get("IZANAGI_ACCEPTANCE_SHARDS")
    os.environ["IZANAGI_ACCEPTANCE_SHARDS"] = "3"
    try:
        with tempfile.TemporaryDirectory() as raw_root:
            config = _config(Path(raw_root).resolve())
            for argv in (
                ("python3", "tools/run_tests.py", "--izanagi-acceptance-shard-count=3"),
                ("python3", "tools/run_tests.py", "-q"),
            ):
                try:
                    launcher._validate_config(config, argv)
                except launcher.LauncherFailure as exc:
                    assert "argv" in str(exc)
                else:
                    raise AssertionError(f"shard mode expanded outer argv: {argv!r}")
    finally:
        if saved is None:
            os.environ.pop("IZANAGI_ACCEPTANCE_SHARDS", None)
        else:
            os.environ["IZANAGI_ACCEPTANCE_SHARDS"] = saved


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
        assert launcher._run_blob(
            source,
            canonical_path,
            log_file,
            environment=dict(os.environ),
            pass_fds=(),
        ) == 0


def test_binding_reports_k3_positive_creates_receipt():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        previous = os.environ.get(launcher._ACCEPTANCE_SHARDS_ENV)
        os.environ[launcher._ACCEPTANCE_SHARDS_ENV] = "3"
        inherited = dict(os.environ)

        def run_blob(source, canonical_path, log_file, *, environment, pass_fds):
            assert canonical_path == root / "tools/run_tests.py"
            assert environment[launcher._ACCEPTANCE_SHARDS_ENV] == "3"
            assert {
                key: environment[key]
                for key in inherited
            } == inherited
            assert set(environment) - set(inherited) == {
                launcher._BINDING_FD_ENV,
                launcher._BINDING_NONCE_ENV,
                launcher._BINDING_TESTED_MAIN_ENV,
            }
            _emit_binding_reports(source, environment, pass_fds)
            log_file.write_bytes(b"runner output\n")
            return 0

        try:
            launcher._launch(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=lambda _repo, _revision: _SOURCE,
                blob_runner=run_blob,
                outcome_writer=lambda _payload: None,
                completion_reader=_completion,
            )
        finally:
            if previous is None:
                os.environ.pop(launcher._ACCEPTANCE_SHARDS_ENV, None)
            else:
                os.environ[launcher._ACCEPTANCE_SHARDS_ENV] = previous

        assert config.receipt_file.read_bytes()


def _report_object(
    index: int,
    *,
    nonce: str = "1" * 64,
    tested_main: str = _SHA1_A,
    digest: str = _SHA256_E,
    shard_count: int = 3,
) -> launcher._BindingReport:
    return launcher._BindingReport(
        tested_main=tested_main,
        nonce=nonce,
        runner_executed_sha256=digest,
        shard_count=shard_count,
        shard_index=index,
    )


def test_binding_reports_reject_extra_count():
    reports = [_report_object(index) for index in (0, 1, 2, 0)]
    with pytest.raises(launcher.LauncherFailure, match="count mismatch"):
        launcher._enforce_binding_reports(
            reports, 3, "1" * 64, _SHA1_A, _SHA256_E
        )


def test_binding_report_digest_mismatch_is_rejected():
    reports = [
        _report_object(index, digest=("2" * 64 if index == 1 else _SHA256_E))
        for index in range(3)
    ]
    with pytest.raises(launcher.LauncherFailure, match="digest mismatch"):
        launcher._enforce_binding_reports(
            reports, 3, "1" * 64, _SHA1_A, _SHA256_E
        )


def test_binding_report_nonce_mismatch_is_rejected():
    reports = [
        _report_object(index, nonce=("2" * 64 if index == 1 else "1" * 64))
        for index in range(3)
    ]
    with pytest.raises(launcher.LauncherFailure, match="nonce mismatch"):
        launcher._enforce_binding_reports(
            reports, 3, "1" * 64, _SHA1_A, _SHA256_E
        )


@pytest.mark.parametrize("case", ["dup"], ids=("dup",))
def test_binding_reports_require_exact_index_multiset(case: str):
    assert case == "dup"
    reports = [_report_object(index) for index in (0, 0, 2)]
    with pytest.raises(launcher.LauncherFailure, match="indexes mismatch"):
        launcher._enforce_binding_reports(
            reports, 3, "1" * 64, _SHA1_A, _SHA256_E
        )


def test_binding_enforcement_precedes_receipt():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        outcomes: list[bytes] = []
        with pytest.raises(launcher.LauncherFailure, match="digest mismatch"):
            _launch_with_reports(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=lambda _repo, _revision: _SOURCE,
                blob_runner=_successful_blob_runner,
                report_options={"digest": "2" * 64},
                outcome_writer=outcomes.append,
                completion_reader=_completion,
            )
        assert len(outcomes) == 1
        assert config.receipt_file.read_bytes() == b""


def test_launcher_owns_k_from_environment_not_reports():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        with pytest.raises(launcher.LauncherFailure, match="count mismatch"):
            _launch_with_reports(
                config,
                ("python3", "tools/run_tests.py"),
                blob_reader=lambda _repo, _revision: _SOURCE,
                blob_runner=_successful_blob_runner,
                shard_count="3",
                report_options={
                    "indexes": (0, 1),
                    "self_reported_k": 2,
                },
                outcome_writer=lambda _payload: None,
                completion_reader=_completion,
            )
        assert config.receipt_file.read_bytes() == b""


def test_unset_shard_env_fails_closed_before_runner():
    with tempfile.TemporaryDirectory() as raw_root:
        root = Path(raw_root).resolve()
        config = _config(root)
        _touch_empty(config.receipt_file)
        runner_calls: list[bool] = []

        def run_blob(*_args, **_kwargs):
            runner_calls.append(True)
            return 0

        previous = os.environ.pop(launcher._ACCEPTANCE_SHARDS_ENV, None)
        try:
            with pytest.raises(launcher.LauncherFailure):
                launcher._launch(
                    config,
                    ("python3", "tools/run_tests.py"),
                    blob_reader=lambda _repo, _revision: _SOURCE,
                    blob_runner=run_blob,
                    outcome_writer=lambda _payload: None,
                    completion_reader=_unreachable,
                )
        finally:
            if previous is not None:
                os.environ[launcher._ACCEPTANCE_SHARDS_ENV] = previous
        assert runner_calls == []
        assert config.log_file.exists() is False
        assert config.receipt_file.read_bytes() == b""


def test_empty_and_invalid_shard_env_fail_closed():
    for value in ("", "0", "4", "03", "x"):
        with pytest.raises(launcher.LauncherFailure, match="explicitly set"):
            launcher._resolve_binding_shard_count(
                {launcher._ACCEPTANCE_SHARDS_ENV: value}
            )


def test_binding_report_tested_main_mismatch_is_rejected():
    reports = [
        _report_object(index, tested_main=(_SHA1_B if index == 1 else _SHA1_A))
        for index in range(3)
    ]
    with pytest.raises(launcher.LauncherFailure, match="tested-main mismatch"):
        launcher._enforce_binding_reports(
            reports, 3, "1" * 64, _SHA1_A, _SHA256_E
        )


def test_binding_report_writer_output_parses_in_launcher():
    payload = _binding_report(
        0,
        nonce="1" * 64,
        tested_main=_SHA1_A,
        digest=_SHA256_E,
        shard_count=1,
    )
    read_fd, write_fd = os.pipe()
    try:
        dispatcher._write_runner_binding_report(write_fd, payload)
    finally:
        os.close(write_fd)
    try:
        raw = os.read(read_fd, 65536)
    finally:
        os.close(read_fd)

    assert launcher._parse_binding_reports(raw) == [
        launcher._BindingReport(
            tested_main=_SHA1_A,
            nonce="1" * 64,
            runner_executed_sha256=_SHA256_E,
            shard_count=1,
            shard_index=0,
        )
    ]


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
        _launch_with_reports(
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
