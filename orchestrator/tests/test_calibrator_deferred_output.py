# -*- coding: utf-8 -*-
"""Deferred calibrator output remains sealed until its one-shot open."""
from __future__ import annotations

import builtins
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator.calibrator import runner  # noqa: E402


_BENCH_BYTES = (
    b"actual_extime:\t1\n"
    b"abort_counts_:\t1\n"
    b"commit_counts_:\t9\n"
    b"maxrss:\t100 kB\n"
    b"latency[ns]:\t10\n"
    b"throughput[tps]:\t1000\n"
)
_PERF_BYTES = (
    b"11,,LLC-load-misses,0,100.00,,\n"
    b"22,,LLC-loads,0,100.00,,\n"
    b"33,,instructions,0,100.00,,\n"
    b"44,,cycles,0,100.00,,\n"
)


def _completed(returncode: int = 0, *, stdout=_BENCH_BYTES, stderr=b""):
    return SimpleNamespace(
        returncode=returncode, stdout=stdout, stderr=stderr,
    )


def test_capture_seals_raw_readers_perf_open_and_sinks_until_open(monkeypatch):
    calls = {"decode": 0, "bench_parse": 0, "throughput": 0, "perf_open": 0}
    returncodes = [91]
    observations = [{"sentinel": True}]
    original_decode = runner._decode_captured_output
    original_bench_parse = runner.parse_bench_stdout
    original_throughput = runner.throughput_tps
    original_open = builtins.open

    def decode_spy(raw):
        calls["decode"] += 1
        return original_decode(raw)

    def bench_parse_spy(text):
        calls["bench_parse"] += 1
        return original_bench_parse(text)

    def throughput_spy(metrics):
        calls["throughput"] += 1
        return original_throughput(metrics)

    def open_spy(path, *args, **kwargs):
        if Path(path).name == "perf.csv":
            calls["perf_open"] += 1
        return original_open(path, *args, **kwargs)

    def fake_run(argv, **kwargs):
        # MUT-T1668-DEFERRED-LEAK: changing this back to text=True turns red.
        assert kwargs["text"] is False
        Path(argv[argv.index("-o") + 1]).write_bytes(_PERF_BYTES)
        return _completed()

    monkeypatch.setattr(runner, "_decode_captured_output", decode_spy)
    monkeypatch.setattr(runner, "parse_bench_stdout", bench_parse_spy)
    monkeypatch.setattr(runner, "throughput_tps", throughput_spy)
    monkeypatch.setattr(runner, "open", open_spy, raising=False)

    token = runner.capture_measure_point(
        "/bench", records=1000, threads=4, clocks_per_us=1800, reps=1,
        subprocess_runner=fake_run, rep_returncodes=returncodes,
        rep_observations=observations,
    )

    assert token.opened is False
    assert token.launch_failures == ()
    assert calls == {
        "decode": 0, "bench_parse": 0, "throughput": 0, "perf_open": 0,
    }
    assert returncodes == [91]
    assert observations == [{"sentinel": True}]
    assert not hasattr(token, "__dict__")
    assert not hasattr(token, "stdout")
    assert not hasattr(token, "stderr")
    assert not hasattr(token, "perf_out")

    point = token.open()

    assert token.opened is True
    assert calls == {
        "decode": 2, "bench_parse": 1, "throughput": 1, "perf_open": 1,
    }
    assert returncodes == [91, 0]
    assert observations[0]["returncode"] == 0
    assert observations[0]["throughput"] == 1000.0
    assert observations[0]["perf_raw"] == {
        "LLC-load-misses": 11,
        "LLC-loads": 22,
        "instructions": 33,
        "cycles": 44,
    }
    assert point.throughputs == [1000.0]
    assert point.rep_observations == observations
    with pytest.raises(RuntimeError, match="already opened"):
        token.open()


def test_output_failures_are_deferred_but_launch_failure_is_preopen_visible():
    strict_returncodes = []
    strict = runner.capture_run_once(
        "/bench", [], strict_returncode=True,
        subprocess_runner=lambda *_args, **_kwargs: _completed(
            9, stderr=b"strict stderr",
        ),
        rep_returncodes=strict_returncodes, use_perf=False,
    )
    assert strict.opened is False
    assert strict.launch_failures == ()
    assert strict_returncodes == []
    with pytest.raises(RuntimeError, match="ccbench failed. rc=9"):
        strict.open()
    assert strict_returncodes == [9]

    timeout_error = subprocess.TimeoutExpired(["/bench"], 1.0, output=b"partial")
    timed_out = runner.capture_run_once(
        "/bench", [],
        subprocess_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            timeout_error
        ),
        use_perf=False,
    )
    assert timed_out.launch_failures == ()
    with pytest.raises(subprocess.TimeoutExpired) as caught_timeout:
        timed_out.open()
    assert caught_timeout.value is timeout_error

    launch_error = OSError(2, "spawn failed")
    launch_failed = runner.capture_run_once(
        "/bench", [],
        subprocess_runner=lambda *_args, **_kwargs: (_ for _ in ()).throw(
            launch_error
        ),
        use_perf=False,
    )
    assert launch_failed.opened is False
    assert launch_failed.launch_failures == (
        runner.MeasurementLaunchFailure(
            exception_type="FileNotFoundError", errno=2,
            message="[Errno 2] spawn failed",
        ),
    )
    assert launch_error.__traceback__ is None
    with pytest.raises(OSError) as caught_launch:
        launch_failed.open()
    assert caught_launch.value is launch_error


def test_decode_parse_and_no_metrics_begin_only_on_open(monkeypatch):
    parse_calls = []
    original_parse = runner.parse_bench_stdout

    def parse_spy(text):
        parse_calls.append(text)
        return original_parse(text)

    monkeypatch.setattr(runner, "parse_bench_stdout", parse_spy)
    undecodable = runner.capture_run_once(
        "/bench", [],
        subprocess_runner=lambda *_args, **_kwargs: _completed(stdout=b"\xff"),
        use_perf=False,
    )
    assert parse_calls == []
    with pytest.raises(UnicodeDecodeError):
        undecodable.open()
    assert parse_calls == []

    no_metrics = runner.capture_run_once(
        "/bench", [],
        subprocess_runner=lambda *_args, **_kwargs: _completed(stdout=b""),
        use_perf=False,
    )
    assert parse_calls == []
    with pytest.raises(RuntimeError, match="produced no metrics"):
        no_metrics.open()
    assert parse_calls == [""]


def test_measure_point_wrapper_preserves_value_exception_and_out_parameters():
    wrapper_returncodes = []
    wrapper_observations = []
    point = runner.measure_point(
        "/bench", records=1000, threads=4, clocks_per_us=1800, reps=2,
        subprocess_runner=lambda *_args, **_kwargs: _completed(),
        rep_returncodes=wrapper_returncodes,
        rep_observations=wrapper_observations, use_perf=False,
    )
    assert point.throughputs == [1000.0, 1000.0]
    assert point.maxrss_kb == 100
    assert wrapper_returncodes == [0, 0]
    assert [item["returncode"] for item in wrapper_observations] == [0, 0]
    assert [item["counter_status"] for item in wrapper_observations] == [
        "not_required", "not_required",
    ]
    assert point.rep_observations == wrapper_observations

    direct_returncodes = []
    direct_result = runner.run_once(
        "/bench", [],
        subprocess_runner=lambda *_args, **_kwargs: _completed(7),
        rep_returncodes=direct_returncodes, use_perf=False,
    )
    assert len(direct_result) == 3
    assert direct_returncodes == [7]

    strict_returncodes = []
    with pytest.raises(RuntimeError) as caught:
        runner.measure_point(
            "/bench", records=1000, threads=4, clocks_per_us=1800, reps=1,
            require_all_reps=True,
            subprocess_runner=lambda *_args, **_kwargs: _completed(9),
            rep_returncodes=strict_returncodes, use_perf=False,
        )
    assert str(caught.value).startswith(
        "rep0/1 fatal at records=1000 threads=4: RuntimeError: "
        "ccbench failed. rc=9"
    )
    assert strict_returncodes == [9]


def test_deferred_reps_cleanup_tmp_before_the_next_spawn() -> None:
    spawned_cwds: list[Path] = []

    def fake_run(argv, **kwargs):
        if spawned_cwds:
            assert not spawned_cwds[-1].exists()
        cwd = Path(kwargs["cwd"])
        spawned_cwds.append(cwd)
        Path(argv[argv.index("-o") + 1]).write_bytes(_PERF_BYTES)
        return _completed()

    token = runner.capture_measure_point(
        "/bench",
        records=1000,
        threads=4,
        clocks_per_us=1800,
        reps=3,
        subprocess_runner=fake_run,
    )

    assert len(spawned_cwds) == 3
    assert all(not path.exists() for path in spawned_cwds)
    assert token.opened is False
    assert token.open().throughputs == [1000.0, 1000.0, 1000.0]


def test_capture_measure_point_execution_failure_is_exact_bool_for_all_outcomes():
    """The deferred public surface distinguishes caught exceptions from rc alone."""

    def observe(*, failure=None, returncode=0):
        observations = []
        calls = {"n": 0}

        def fake_run(*_args, **_kwargs):
            index = calls["n"]
            calls["n"] += 1
            if index == 0 and failure is not None:
                raise failure
            return _completed(returncode if index == 0 else 0)

        token = runner.capture_measure_point(
            "/bench", records=1000, threads=4, clocks_per_us=1800,
            reps=2 if failure is not None else 1,
            subprocess_runner=fake_run, rep_observations=observations,
            use_perf=False,
        )
        point = token.open()
        assert point.rep_observations == observations
        assert all(type(row["execution_failure"]) is bool
                   for row in observations)
        return observations

    success = observe()
    nonzero = observe(returncode=7)
    runtime = observe(failure=RuntimeError("injected runtime failure"))
    timeout = observe(failure=subprocess.TimeoutExpired(["/bench"], 1.0))
    generic = observe(failure=Exception("injected generic failure"))

    assert success[0]["execution_failure"] is False
    assert nonzero[0]["returncode"] == 7
    assert nonzero[0]["execution_failure"] is False
    for observations in (runtime, timeout, generic):
        assert observations[0]["execution_failure"] is True
        assert observations[1]["execution_failure"] is False


@pytest.mark.parametrize("failure", ("nonzero", "timeout"))
def test_deferred_real_run_once_seam_preserves_strict_spawn_count(
    failure: str,
) -> None:
    spawn_count = 0

    def fake_run(*_args, **_kwargs):
        nonlocal spawn_count
        spawn_count += 1
        if failure == "timeout":
            raise subprocess.TimeoutExpired(["/bench"], 1.0, output=b"partial")
        return _completed(9, stderr=b"strict stderr")

    token = runner.capture_measure_point(
        "/bench",
        records=1000,
        threads=4,
        clocks_per_us=1800,
        reps=3,
        require_all_reps=True,
        subprocess_runner=fake_run,
        use_perf=False,
    )

    assert spawn_count == 1
    assert token.launch_failures == ()
    assert not hasattr(token, "returncode")
    with pytest.raises(RuntimeError, match="rep0/3 fatal"):
        token.open()


@pytest.mark.parametrize("failure", ("nonzero", "timeout"))
def test_public_measure_point_real_run_once_seam_preserves_strict_spawn_count(
    failure: str,
) -> None:
    spawn_count = 0

    def fake_run(*_args, **_kwargs):
        nonlocal spawn_count
        spawn_count += 1
        if failure == "timeout":
            raise subprocess.TimeoutExpired(["/bench"], 1.0, output=b"partial")
        return _completed(9, stderr=b"strict stderr")

    with pytest.raises(RuntimeError, match="rep0/3 fatal"):
        runner.measure_point(
            "/bench",
            records=1000,
            threads=4,
            clocks_per_us=1800,
            reps=3,
            require_all_reps=True,
            subprocess_runner=fake_run,
            use_perf=False,
        )

    assert spawn_count == 1


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
