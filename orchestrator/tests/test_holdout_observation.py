# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from collections.abc import Mapping, Sequence
import copy
import dataclasses
import hashlib
import json
import pickle
from pathlib import Path
import sys

import pytest

_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_ROOT))

from orchestrator import holdout_observation as observation  # noqa: E402
from orchestrator.calibrator import runner  # noqa: E402
from orchestrator.calibrator.model import PerfCounters  # noqa: E402
from orchestrator.campaign import pipeline, trial_registry  # noqa: E402
from orchestrator.campaign.s8b_experiment_numbers import (  # noqa: E402
    APPROVED_EXTIME_S,
)


_TEST_ZIPF_SKEW = "0" + ".9"
_TEST_RMW = "0"
_TEST_RECORDS = 1_000_000
_TEST_THREADS = 48
_TEST_RR80 = "8" + "0"
_TEST_RR20 = "2" + "0"
_TEST_CLOCKS_PER_US = 1800
_TEST_EXTIME = APPROVED_EXTIME_S
_MISMATCH_ZIPF_SKEW = "0" + ".8"
_MISMATCH_RMW = "1"
_MISMATCH_RECORDS = "999999"
_MISMATCH_THREADS = "47"


def _freeze() -> dict[str, object]:
    return {
        "holdouts": {
            "rr80": {
                "candidate_id": "H1",
                "records": _TEST_RECORDS,
                "threads": _TEST_THREADS,
                "ycsb": {
                    "ycsb_zipf_skew": _TEST_ZIPF_SKEW,
                    "ycsb_rratio": _TEST_RR80,
                    "ycsb_rmw": _TEST_RMW,
                },
            },
            "rr20": {
                "candidate_id": "H2",
                "records": _TEST_RECORDS,
                "threads": _TEST_THREADS,
                "ycsb": {
                    "ycsb_zipf_skew": _TEST_ZIPF_SKEW,
                    "ycsb_rratio": _TEST_RR20,
                    "ycsb_rmw": _TEST_RMW,
                },
            },
        },
    }


def _full_gflags(
    key: str = "rr80", *, overrides: Mapping[str, str] | None = None,
) -> list[str]:
    entry = _freeze()["holdouts"][key]
    ycsb = entry["ycsb"]
    values = {
        "ycsb_zipf_skew": ycsb["ycsb_zipf_skew"],
        "ycsb_rratio": ycsb["ycsb_rratio"],
        "ycsb_rmw": ycsb["ycsb_rmw"],
        "ycsb_tuple_num": str(entry["records"]),
        "thread_num": str(entry["threads"]),
    }
    if overrides is not None:
        values.update(overrides)
    return [f"--{name}={value}" for name, value in values.items()]


def _old_ratio_only_signature(
    gflags: Sequence[str],
) -> observation.MinimalHoldoutSignature | None:
    """Model the pre-fix ratio-only gate, including its spelling blind spot."""

    effective = {}
    for raw in gflags:
        if not raw.startswith("-") or raw == "-":
            continue
        body = raw[2:] if raw.startswith("--") else raw[1:]
        name, separator, value = body.partition("=")
        if separator and name:
            effective[name] = value
    return observation._NEUTRAL_BY_RATIO.get(effective.get("ycsb_rratio"))


def _completed_process(returncode: int = 0):
    return type("Completed", (), {
        "returncode": returncode,
        "stdout": "throughput[tps]:\t1000\nmaxrss:\t100 kB\n",
        "stderr": "",
    })()


def _issued(
    key: str = "rr80", *, attempt_id: str = "planned:0", uses: int = 1,
) -> observation.HoldoutObservationAdmission:
    receipt = observation._new_durable_attempt_consumption_receipt(
        attempt_id=attempt_id,
        permitted_run_once_calls=uses,
    )
    return observation._issue_holdout_observation_admission_from_receipt(
        receipt=receipt,
        verified_freeze_document=_freeze(),
        freeze_holdout_key=key,
    )


def _issued_calibration(
    binary_sha256: str, *, start_records: int = 100,
    max_records: int = 200, sweep_reps: int = 2, noise_reps: int = 2,
    use_perf: bool = False, numactl=(), extra_env=None,
) -> observation.CalibrationObservationCapability:
    sweep_points = 0
    records = start_records
    while records <= max_records:
        sweep_points += 1
        records *= 2
    receipt = observation._new_calibration_observation_receipt(
        attempt_id="calibration:0", env_tag="test-env",
        receipt_sha256="a" * 64, binary_sha256=binary_sha256,
        ycsb_rratio="80",
        permitted_run_once_calls=(
            sweep_points * sweep_reps + noise_reps
        ),
        sweep_gflags=(
            "-thread_num=2", "-extime=1", "-clocks_per_us=1800",
            "-ycsb_rratio=80",
        ),
        sweep_reps=sweep_reps, noise_reps=noise_reps,
        start_records=start_records, max_records=max_records,
        numactl=numactl, timeout_s=120.0, use_perf=use_perf,
        extra_env=extra_env,
    )
    return observation._issue_calibration_observation_capability_from_receipt(
        receipt=receipt,
    )


def test_holdout_observation_module_is_a_stdlib_only_leaf():
    source = (_ROOT / "orchestrator" / "holdout_observation.py").read_text(
        encoding="utf-8"
    )
    imported_roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots == {
        "__future__", "collections", "dataclasses", "threading", "typing",
    }


def test_protected_signatures_are_derived_from_freeze_and_match_exactly():
    signatures = observation.protected_signatures_from_verified_freeze(_freeze())
    assert {
        (item.freeze_holdout_key, item.freeze_candidate_id,
         item.trial_workload_name, item.ycsb_zipf_skew,
         item.ycsb_rratio, item.ycsb_rmw, item.records, item.threads)
        for item in signatures
    } == {
        ("rr80", "H1", "rr80", _TEST_ZIPF_SKEW,
         _TEST_RR80, _TEST_RMW, _TEST_RECORDS, _TEST_THREADS),
        ("rr20", "H2", "rr20", _TEST_ZIPF_SKEW,
         _TEST_RR20, _TEST_RMW, _TEST_RECORDS, _TEST_THREADS),
    }


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("ycsb_zipf_skew", None, r"rr80\.ycsb\.ycsb_zipf_skew"),
        ("ycsb_rmw", None, r"rr80\.ycsb\.ycsb_rmw"),
        ("records", 0, r"rr80\.records must be a positive exact int"),
        ("threads", True, r"rr80\.threads must be a positive exact int"),
    ],
)
def test_signature_derivation_requires_each_complete_condition_field(
    field, value, match,
):
    document = _freeze()
    entry = document["holdouts"]["rr80"]
    container = entry["ycsb"] if field.startswith("ycsb_") else entry
    if value is None:
        del container[field]
    else:
        container[field] = value
    with pytest.raises(observation.HoldoutObservationError, match=match):
        observation._derive_protected_signatures(document)


def test_no_supported_public_api_can_issue_an_observation_token():
    assert "issue_holdout_observation_admission" not in observation.__all__
    assert "_issue_calibration_observation_capability_from_receipt" not in observation.__all__
    assert not hasattr(observation, "issue_holdout_observation_admission")


def test_private_consumption_receipt_is_single_use_and_attempt_bound():
    receipt = observation._new_durable_attempt_consumption_receipt(
        attempt_id="retry:1", permitted_run_once_calls=5,
    )
    token = observation._issue_holdout_observation_admission_from_receipt(
        receipt=receipt,
        verified_freeze_document=_freeze(),
        freeze_holdout_key="rr80",
    )
    assert token.attempt_id == "retry:1"
    assert token.permitted_run_once_calls == 5
    with pytest.raises(observation.HoldoutObservationError, match="reused"):
        observation._issue_holdout_observation_admission_from_receipt(
            receipt=receipt,
            verified_freeze_document=_freeze(),
            freeze_holdout_key="rr80",
        )


def test_unknown_freeze_holdout_is_rejected_instead_of_classified_unprotected():
    document = _freeze()
    document["holdouts"]["rr30"] = {
        "candidate_id": "H3",
        "records": _TEST_RECORDS,
        "threads": _TEST_THREADS,
        "ycsb": {
            "ycsb_zipf_skew": _TEST_ZIPF_SKEW,
            "ycsb_rratio": "30",
            "ycsb_rmw": _TEST_RMW,
        },
    }
    with pytest.raises(observation.HoldoutObservationError, match="exactly match"):
        observation.protected_signatures_from_verified_freeze(document)


def test_real_freeze_projection_exactly_matches_trial_registry_neutral_table():
    freeze_path = _ROOT / "output" / "s8b-freeze" / "holdout_freeze.json"
    document = json.loads(freeze_path.read_text(encoding="utf-8"))
    signatures = observation.protected_signatures_from_verified_freeze(document)
    projected = {
        item.freeze_candidate_id: {
            "workload": item.trial_workload_name,
            "ycsb_zipf_skew": item.ycsb_zipf_skew,
            "ycsb_rratio": item.ycsb_rratio,
            "ycsb_rmw": item.ycsb_rmw,
            "records": item.records,
            "threads": item.threads,
        }
        for item in signatures
    }
    assert projected == dict(trial_registry.HOLDOUT_BINDINGS)
    assert {item.trial_workload_name for item in signatures} == (
        trial_registry.HOLDOUT_WORKLOADS
    )


@pytest.mark.parametrize(
    "gflags",
    [
        ["--flagfile=/tmp/flags"],
        ["-flagfile=/tmp/flags"],
        ["--fromenv=ycsb_rratio"],
        ["-tryfromenv=ycsb_rratio"],
        ["--flagfile"],
    ],
)
def test_indirect_gflags_are_rejected_before_tempdir_or_subprocess(
    monkeypatch, gflags,
):
    effects = []
    monkeypatch.setattr(
        runner.tempfile, "mkdtemp",
        lambda **_kwargs: effects.append("tempdir"),
    )
    with pytest.raises(observation.HoldoutObservationError, match="indirect"):
        runner.run_once(
            "/bench", gflags,
            subprocess_runner=lambda *_args, **_kwargs: effects.append("spawn"),
            use_perf=False,
        )
    assert effects == []


def test_direct_gflags_are_normalized_with_last_wins_semantics():
    assert observation.classify_minimal_holdout_signature([
        "-ycsb_rratio=80", "--ycsb_rratio=50",
    ]) is None
    classified = observation.classify_minimal_holdout_signature([
        "--ycsb_rratio=50", "-ycsb_rratio=80",
    ])
    assert classified is not None
    assert classified.ycsb_rratio == "80"


def test_direct_gflags_apply_gflags_hyphen_normalization_before_classification():
    classified = observation.classify_minimal_holdout_signature([
        "--ycsb-rratio=80",
    ])
    assert classified is not None
    assert classified.freeze_holdout_key == "rr80"
    assert observation.normalized_direct_gflags([
        "--ycsb-rratio", "20",
    ])["ycsb_rratio"] == "20"


def test_tokenless_hyphen_alias_for_protected_ratio_is_not_unprotected():
    with pytest.raises(observation.HoldoutObservationError, match="required"):
        observation.assert_holdout_observation_admitted(
            gflags=["--ycsb-rratio=80"], admission=None,
        )


@pytest.mark.parametrize(
    "ratio",
    [
        "+80", "080", " 80", "80 ", "-80", "80+", "80x", "",
        "18446744073709551616",
    ],
)
def test_noncanonical_or_out_of_range_uint64_ratio_is_rejected_before_effect(
    monkeypatch, ratio,
):
    effects = []
    monkeypatch.setattr(
        runner.tempfile, "mkdtemp",
        lambda **_kwargs: effects.append("tempdir"),
    )
    with pytest.raises(
        observation.HoldoutObservationError,
        match="canonical unsigned decimal|uint64 range",
    ):
        runner.run_once(
            "/bench", [f"--ycsb_rratio={ratio}"],
            subprocess_runner=lambda *_args, **_kwargs: effects.append("spawn"),
            use_perf=False,
        )
    assert effects == []


@pytest.mark.parametrize("ratio", ["0", "19", "21", "79", "81", "18446744073709551615"])
def test_canonical_uint64_boundary_controls_remain_unprotected(ratio):
    assert observation.classify_minimal_holdout_signature(
        [f"--ycsb_rratio={ratio}"]
    ) is None


def test_run_once_snapshots_stateful_gflags_exactly_once():
    class StatefulFlags(Sequence[str]):
        def __init__(self):
            self.iterations = 0

        def __len__(self):
            return 1

        def __getitem__(self, index):
            if index == 0:
                return "--ycsb_rratio=50"
            raise IndexError

        def __iter__(self):
            self.iterations += 1
            ratio = "50" if self.iterations == 1 else "80"
            return iter((f"--ycsb_rratio={ratio}",))

    flags = StatefulFlags()
    seen = []
    runner.run_once(
        "/bench", flags,
        subprocess_runner=lambda cmd, **_kwargs: (
            seen.append(tuple(cmd)) or _completed_process()
        ),
        use_perf=False,
    )
    assert flags.iterations == 1
    assert seen == [("/bench", "--ycsb_rratio=50")]


def test_run_once_snapshot_rejects_non_exact_str_before_effect(monkeypatch):
    class StringSubclass(str):
        pass

    effects = []
    monkeypatch.setattr(
        runner.tempfile, "mkdtemp",
        lambda **_kwargs: effects.append("tempdir"),
    )
    with pytest.raises(observation.HoldoutObservationError, match="exact strings"):
        runner.run_once(
            "/bench", [StringSubclass("--ycsb_rratio=50")],
            subprocess_runner=lambda *_args, **_kwargs: effects.append("spawn"),
            use_perf=False,
        )
    assert effects == []


@pytest.mark.parametrize("ratio", ["20", "80"])
def test_protected_ratio_without_admission_stops_before_any_effect(
    monkeypatch, ratio,
):
    effects = []
    monkeypatch.setattr(
        runner.tempfile, "mkdtemp",
        lambda **_kwargs: effects.append("tempdir"),
    )
    with pytest.raises(observation.HoldoutObservationError, match="required"):
        runner.run_once(
            "/bench", [f"-ycsb_rratio={ratio}"],
            subprocess_runner=lambda *_args, **_kwargs: effects.append("spawn"),
            use_perf=False,
        )
    assert effects == []


def test_tokenless_rr80_gate_is_only_barrier_before_accepting_subprocess():
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="required"):
        runner.run_once(
            "/bench", ["-ycsb_rratio=80"],
            subprocess_runner=lambda *_args, **_kwargs: (
                calls.append("spawn") or _completed_process()
            ),
            use_perf=False,
        )
    assert calls == []


def test_flagfile_gate_is_only_barrier_before_accepting_subprocess():
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="indirect"):
        runner.run_once(
            "/bench", ["--flagfile=/tmp/holdout-flags"],
            subprocess_runner=lambda *_args, **_kwargs: (
                calls.append("spawn") or _completed_process()
            ),
            use_perf=False,
        )
    assert calls == []


def test_issued_identity_admission_allows_matching_protected_ratio():
    calls = []
    result = runner.run_once(
        "/bench", _full_gflags(),
        subprocess_runner=lambda *args, **kwargs: (
            calls.append((args, kwargs)) or _completed_process()
        ),
        use_perf=False,
        holdout_observation_admission=_issued("rr80"),
    )
    assert len(result) == 3
    assert len(calls) == 1


def test_matching_complete_condition_keeps_one_dash_direct_form_accepted():
    flags = [f"-{raw[2:]}" for raw in _full_gflags()]
    observation.assert_holdout_observation_admitted(
        gflags=flags, admission=_issued("rr80"),
    )


@pytest.mark.parametrize(
    ("field", "reason", "replacement", "match"),
    [
        ("ycsb_zipf_skew", "missing", None,
         r"requires explicit ycsb_zipf_skew"),
        ("ycsb_zipf_skew", "malformed", "0.90",
         r"ycsb_zipf_skew must be canonical nonnegative decimal"),
        ("ycsb_zipf_skew", "mismatch", "0.8",
         r"holdout observation ycsb_zipf_skew does not match"),
        ("ycsb_rratio", "missing", None,
         r"requires explicit ycsb_rratio"),
        ("ycsb_rratio", "malformed", "080",
         r"ycsb_rratio must be canonical unsigned decimal"),
        ("ycsb_rratio", "mismatch", "20",
         r"holdout observation ycsb_rratio does not match"),
        ("ycsb_rmw", "missing", None,
         r"requires explicit ycsb_rmw"),
        ("ycsb_rmw", "malformed", "false",
         r"ycsb_rmw must be canonical unsigned decimal"),
        ("ycsb_rmw", "mismatch", "1",
         r"holdout observation ycsb_rmw does not match"),
        ("ycsb_tuple_num", "missing", None,
         r"requires explicit ycsb_tuple_num"),
        ("ycsb_tuple_num", "malformed", "0",
         r"ycsb_tuple_num must be canonical positive decimal"),
        ("ycsb_tuple_num", "mismatch", "999999",
         r"holdout observation ycsb_tuple_num does not match"),
        ("thread_num", "missing", None,
         r"requires explicit thread_num"),
        ("thread_num", "malformed", "00",
         r"thread_num must be canonical positive decimal"),
        ("thread_num", "mismatch", "47",
         r"holdout observation thread_num does not match"),
    ],
    ids=lambda case: str(case),
)
def test_formal_gate_rejects_each_field_by_distinct_reason_without_consuming(
    field, reason, replacement, match,
):
    del reason  # Included in the parameter id and failure report.
    token = _issued("rr80")
    flags = _full_gflags()
    prefix = f"--{field}="
    if replacement is None:
        flags = [raw for raw in flags if not raw.startswith(prefix)]
    else:
        flags = [
            f"{prefix}{replacement}" if raw.startswith(prefix) else raw
            for raw in flags
        ]
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match=match):
        runner.run_once(
            "/bench", flags,
            subprocess_runner=lambda *_args, **_kwargs: calls.append("rejected"),
            use_perf=False, holdout_observation_admission=token,
        )
    runner.run_once(
        "/bench", _full_gflags(),
        subprocess_runner=lambda *_args, **_kwargs: (
            calls.append("accepted") or _completed_process()
        ),
        use_perf=False, holdout_observation_admission=token,
    )
    assert calls == ["accepted"]


@pytest.mark.parametrize(
    ("form", "match"),
    [
        ("bare", r"must use name=value direct gflag form"),
        ("no_alias", r"no-prefix alias is forbidden"),
        ("after_terminator", r"is forbidden after --"),
        ("undashed", r"must use name=value direct gflag form"),
    ],
)
@pytest.mark.parametrize(
    "field",
    [
        "ycsb_zipf_skew", "ycsb_rratio", "ycsb_rmw",
        "ycsb_tuple_num", "thread_num",
    ],
)
def test_formal_gate_rejects_every_noncanonical_protected_field_occurrence(
    field, form, match,
):
    token = _issued("rr80")
    flags = _full_gflags()
    canonical = next(raw for raw in flags if raw.startswith(f"--{field}="))
    value = canonical.partition("=")[2]
    if form == "bare":
        flags.append(f"--{field}")
    elif form == "no_alias":
        flags.append(f"--no{field}")
    elif form == "after_terminator":
        flags.extend(("--", f"--{field}={value}"))
    else:
        flags.append(f"{field}={value}")
    with pytest.raises(observation.HoldoutObservationError, match=match):
        observation.assert_holdout_observation_admitted(
            gflags=flags, admission=token,
        )
    observation.assert_holdout_observation_admitted(
        gflags=_full_gflags(), admission=token,
    )


def test_gflags_alias_two_token_and_terminator_bypasses_are_all_closed():
    expected_values = {
        "ycsb_zipf_skew": _TEST_ZIPF_SKEW,
        "ycsb_rratio": _TEST_RR80,
        "ycsb_rmw": _TEST_RMW,
        "ycsb_tuple_num": str(_TEST_RECORDS),
        "thread_num": str(_TEST_THREADS),
    }
    mismatch_values = {
        "ycsb_zipf_skew": _MISMATCH_ZIPF_SKEW,
        "ycsb_rratio": _TEST_RR20,
        "ycsb_rmw": _MISMATCH_RMW,
        "ycsb_tuple_num": _MISMATCH_RECORDS,
        "thread_num": _MISMATCH_THREADS,
    }
    cases = []
    for field in expected_values:
        alias = field.replace("_", "-")
        cases.extend((
            (
                f"{field}:hyphen-alias",
                [*_full_gflags(), f"--{alias}={mismatch_values[field]}"],
                r"hyphen alias is forbidden",
            ),
            (
                f"{field}:two-token",
                [*_full_gflags(), f"--{field}", mismatch_values[field]],
                r"must use name=value direct gflag form",
            ),
            (
                f"{field}:after-terminator",
                [*_full_gflags(), "--", f"--{field}={expected_values[field]}"],
                r"is forbidden after --",
            ),
        ))

    assert cases
    rejected_count = 0
    for _case_name, flags, match in cases:
        token = _issued("rr80")
        old_classification = _old_ratio_only_signature(flags)
        assert old_classification is not None
        assert old_classification.freeze_holdout_key == token.freeze_holdout_key
        with pytest.raises(observation.HoldoutObservationError, match=match):
            observation.assert_holdout_observation_admitted(
                gflags=flags, admission=token,
            )
        observation.assert_holdout_observation_admitted(
            gflags=_full_gflags(), admission=token,
        )
        rejected_count += 1
    assert rejected_count == len(cases)
    assert rejected_count > 0


@pytest.mark.parametrize(
    "extra_flag",
    [
        "--batch_th_num=48",
        "--epoch_time=40",
        "--batch_ratio=10",
        "--ycsb_max_ope=10",
    ],
)
def test_protected_run_rejects_every_direct_flag_outside_closed_allowlist(
    extra_flag,
):
    flags = [*_full_gflags(), extra_flag]
    token = _issued("rr80")
    old_classification = _old_ratio_only_signature(flags)
    assert old_classification is not None
    assert old_classification.freeze_holdout_key == token.freeze_holdout_key
    with pytest.raises(
        observation.HoldoutObservationError,
        match=r"direct gflag .* is not admitted",
    ):
        observation.assert_holdout_observation_admitted(
            gflags=flags, admission=token,
        )
    observation.assert_holdout_observation_admitted(
        gflags=[
            *_full_gflags(),
            f"--extime={_TEST_EXTIME}",
            f"--clocks_per_us={_TEST_CLOCKS_PER_US}",
        ],
        admission=token,
    )


@pytest.mark.parametrize(
    "extra_flag",
    ["--extime", f"--clocks-per-us={_TEST_CLOCKS_PER_US}"],
)
def test_allowlisted_direct_flags_still_require_canonical_name_value_form(
    extra_flag,
):
    token = _issued("rr80")
    with pytest.raises(
        observation.HoldoutObservationError,
        match=r"allowlisted direct gflag .* canonical name=value",
    ):
        observation.assert_holdout_observation_admitted(
            gflags=[*_full_gflags(), extra_flag], admission=token,
        )
    observation.assert_holdout_observation_admitted(
        gflags=[*_full_gflags(), f"--extime={_TEST_EXTIME}"],
        admission=token,
    )


def test_positive_controls_pass_the_old_ratio_gate_but_fail_the_full_gate():
    cases = [
        ("skew", _full_gflags(overrides={"ycsb_zipf_skew": "0.8"})),
        ("rmw", _full_gflags(overrides={"ycsb_rmw": "1"})),
        ("records", _full_gflags(overrides={"ycsb_tuple_num": "999999"})),
        ("threads", _full_gflags(overrides={"thread_num": "47"})),
        ("bare-bool", [*_full_gflags(), "--ycsb_rmw"]),
    ]
    assert cases
    rejected_count = 0
    for _name, flags in cases:
        token = _issued("rr80")
        old_classification = observation.classify_minimal_holdout_signature(flags)
        assert old_classification is not None
        assert old_classification.freeze_holdout_key == token.freeze_holdout_key
        assert old_classification.ycsb_rratio == token.ycsb_rratio
        with pytest.raises(observation.HoldoutObservationError):
            observation.assert_holdout_observation_admitted(
                gflags=flags, admission=token,
            )
        rejected_count += 1
    assert rejected_count == len(cases)
    assert rejected_count > 0


@pytest.mark.parametrize(
    "caller",
    [
        "s8b_floor_campaign.measure_fn",
        "s8b_oracle_driver.pipeline.evaluate",
        "s8b_oracle_n_pilot.run_sessions",
        "pipeline._run_bench.measure_point",
    ],
)
def test_current_protected_measure_point_callers_pass_closed_argv_allowlist(
    monkeypatch, caller,
):
    token = _issued("rr80")
    seen = []

    def fake_run_once(binary, gflags, **kwargs):
        observation.assert_holdout_observation_admitted(
            gflags=gflags,
            admission=kwargs["holdout_observation_admission"],
        )
        seen.append((binary, list(gflags)))
        return (
            {"throughput[tps]": "1000", "maxrss": "100 kB"},
            PerfCounters(),
            0.5,
        )

    monkeypatch.setattr(runner, "run_once", fake_run_once)
    runner.measure_point(
        "/bench",
        records=_TEST_RECORDS,
        threads=_TEST_THREADS,
        clocks_per_us=_TEST_CLOCKS_PER_US,
        extime=_TEST_EXTIME,
        reps=1,
        workload=dict(_freeze()["holdouts"]["rr80"]["ycsb"]),
        use_perf=False,
        holdout_observation_admission=token,
    )

    assert caller
    assert seen == [(
        "/bench",
        [
            f"-thread_num={_TEST_THREADS}",
            f"-ycsb_tuple_num={_TEST_RECORDS}",
            f"-extime={_TEST_EXTIME}",
            f"-clocks_per_us={_TEST_CLOCKS_PER_US}",
            f"-ycsb_zipf_skew={_TEST_ZIPF_SKEW}",
            f"-ycsb_rratio={_TEST_RR80}",
            f"-ycsb_rmw={_TEST_RMW}",
        ],
    )]


def test_pipeline_correctness_workload_nonprotected_argv_remains_unrestricted():
    workload = pipeline.CorrectnessWorkload()
    gflags = [
        *(f"-{name}={value}" for name, value in workload.flags.items()),
        f"-clocks_per_us={_TEST_CLOCKS_PER_US}",
    ]
    cmd = runner._build_cmd(
        "/bench", gflags, "/tmp/perf.csv", None, use_perf=False,
    )
    assert cmd == ["/bench", *gflags]
    assert observation.assert_holdout_observation_admitted(
        gflags=gflags, admission=None,
    ) is None


def test_calibrator_build_cmd_argv_uses_capability_before_formal_allowlist():
    binary_sha256 = "0" * 64
    capability = _issued_calibration(binary_sha256)
    gflags = [
        "-thread_num=2",
        "-ycsb_tuple_num=100",
        "-extime=1",
        "-clocks_per_us=1800",
        "-ycsb_rratio=80",
    ]
    cmd = runner._build_cmd(
        "/bench", gflags, "/tmp/perf.csv", None, use_perf=False,
    )
    assert cmd == ["/bench", *gflags]
    assert observation.assert_holdout_observation_admitted(
        gflags=gflags,
        admission=None,
        calibration_observation_capability=capability,
        calibration_observation_phase="sweep",
        binary_sha256=binary_sha256,
        use_perf=False,
    ) == ((), ())


def test_attempt_admission_rejects_run_once_beyond_permitted_count():
    token = _issued("rr80", attempt_id="planned:2", uses=2)
    calls = []
    for _ in range(2):
        runner.run_once(
            "/bench", _full_gflags(),
            subprocess_runner=lambda *_args, **_kwargs: (
                calls.append("spawn") or _completed_process()
            ),
            use_perf=False,
            holdout_observation_admission=token,
        )
    with pytest.raises(observation.HoldoutObservationError, match="exhausted"):
        runner.run_once(
            "/bench", _full_gflags(),
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == ["spawn", "spawn"]


def test_calibration_capability_tracks_sweep_then_noise_and_binds_binary(
    tmp_path,
):
    binary = tmp_path / "ycsb_fixture.exe"
    binary.write_bytes(b"calibration-binary")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()
    capability = _issued_calibration(digest)
    static = [
        "-thread_num=2", "-extime=1", "-clocks_per_us=1800",
        "-ycsb_rratio=80",
    ]

    def run(records, phase):
        return runner.run_once(
            str(binary),
            [static[0], f"-ycsb_tuple_num={records}", *static[1:]],
            use_perf=False, subprocess_runner=lambda *_args, **_kwargs: (
                _completed_process()
            ),
            calibration_observation_capability=capability,
            calibration_observation_phase=phase,
        )

    run(100, "sweep")
    with pytest.raises(observation.HoldoutObservationError, match="doubling"):
        run(200, "sweep")
    run(100, "sweep")
    run(200, "sweep")
    run(200, "sweep")
    with pytest.raises(observation.HoldoutObservationError, match="completed sweep"):
        run(100, "noise")

    observation._transition_calibration_observation_to_noise(
        capability, saturation_records=100,
    )
    with pytest.raises(observation.HoldoutObservationError, match="noise records"):
        run(200, "noise")
    run(100, "noise")
    run(100, "noise")


def test_calibration_capability_recomputes_binary_hash_before_spawn(tmp_path):
    binary = tmp_path / "ycsb_fixture.exe"
    binary.write_bytes(b"actual-binary")
    capability = _issued_calibration(hashlib.sha256(b"different").hexdigest())
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="binary hash"):
        runner.run_once(
            str(binary),
            ["-thread_num=2", "-ycsb_tuple_num=100", "-extime=1",
             "-clocks_per_us=1800", "-ycsb_rratio=80"],
            use_perf=False,
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            calibration_observation_capability=capability,
            calibration_observation_phase="sweep",
        )
    assert calls == []


def test_calibration_gateway_reuses_normalized_runtime_values_for_spawn(
    monkeypatch, tmp_path,
):
    binary = tmp_path / "ycsb_fixture.exe"
    binary.write_bytes(b"calibration-binary")
    digest = hashlib.sha256(binary.read_bytes()).hexdigest()

    class StatefulNumactl:
        def __init__(self):
            self.iterations = 0

        def __iter__(self):
            self.iterations += 1
            if self.iterations == 1:
                return iter(("numactl", "--physcpubind=0"))
            return iter(("numactl", "--physcpubind=0", "/attacker-wrapper"))

    class InjectingEnvironment(Mapping[str, str]):
        def __init__(self):
            self.items_calls = 0
            self.iterations = 0

        def items(self):
            self.items_calls += 1
            return ()

        def __iter__(self):
            self.iterations += 1
            return iter(("LD_PRELOAD",))

        def __len__(self):
            return 1

        def __getitem__(self, key):
            if key == "LD_PRELOAD":
                return "/attacker/preload.so"
            raise KeyError(key)

    numactl = StatefulNumactl()
    extra_env = InjectingEnvironment()
    capability = _issued_calibration(
        digest, use_perf=False,
        numactl=("numactl", "--physcpubind=0"),
    )
    seen = []
    monkeypatch.delenv("LD_PRELOAD", raising=False)

    runner.run_once(
        str(binary),
        ["-thread_num=2", "-ycsb_tuple_num=100", "-extime=1",
         "-clocks_per_us=1800", "-ycsb_rratio=80"],
        numactl=numactl,
        extra_env=extra_env,
        use_perf=False,
        subprocess_runner=lambda cmd, **kwargs: (
            seen.append((cmd, kwargs["env"])) or _completed_process()
        ),
        calibration_observation_capability=capability,
        calibration_observation_phase="sweep",
    )

    assert numactl.iterations == 1
    assert extra_env.items_calls == 1
    assert extra_env.iterations == 0
    assert seen[0][0][:2] == ["numactl", "--physcpubind=0"]
    assert "/attacker-wrapper" not in seen[0][0]
    assert "LD_PRELOAD" not in seen[0][1]


def test_calibration_capability_rejects_noise_transition_with_unconsumed_sweep(
    tmp_path,
):
    binary = tmp_path / "ycsb_fixture.exe"
    binary.write_bytes(b"calibration-binary")
    capability = _issued_calibration(
        hashlib.sha256(binary.read_bytes()).hexdigest(),
        start_records=1, max_records=4, sweep_reps=1, noise_reps=1,
        use_perf=False,
    )
    runner.run_once(
        str(binary),
        ["-thread_num=2", "-ycsb_tuple_num=1", "-extime=1",
         "-clocks_per_us=1800", "-ycsb_rratio=80"],
        use_perf=False,
        subprocess_runner=lambda *_args, **_kwargs: _completed_process(),
        calibration_observation_capability=capability,
        calibration_observation_phase="sweep",
    )

    with pytest.raises(
        observation.HoldoutObservationError,
        match="unconsumed records",
    ):
        observation._transition_calibration_observation_to_noise(
            capability, saturation_records=1,
        )


def test_calibration_capability_allows_noise_transition_after_three_sweep_points(
    tmp_path,
):
    binary = tmp_path / "ycsb_fixture.exe"
    binary.write_bytes(b"calibration-binary")
    capability = _issued_calibration(
        hashlib.sha256(binary.read_bytes()).hexdigest(),
        start_records=1, max_records=8, sweep_reps=1, noise_reps=1,
        use_perf=False,
    )

    for records in (1, 2, 4):
        runner.run_once(
            str(binary),
            ["-thread_num=2", f"-ycsb_tuple_num={records}", "-extime=1",
             "-clocks_per_us=1800", "-ycsb_rratio=80"],
            use_perf=False,
            subprocess_runner=lambda *_args, **_kwargs: _completed_process(),
            calibration_observation_capability=capability,
            calibration_observation_phase="sweep",
        )

    observation._transition_calibration_observation_to_noise(
        capability, saturation_records=4,
    )


def test_one_attempt_allows_exactly_one_measure_point_repetition_set():
    token = _issued("rr80", attempt_id="planned:3", uses=5)
    calls = []
    runner.measure_point(
        "/bench", records=_TEST_RECORDS, threads=_TEST_THREADS,
        clocks_per_us=1800,
        workload=dict(_freeze()["holdouts"]["rr80"]["ycsb"]), reps=5,
        subprocess_runner=lambda *_args, **_kwargs: (
            calls.append("spawn") or _completed_process()
        ),
        rep_observations=[], use_perf=False,
        holdout_observation_admission=token,
    )
    with pytest.raises(observation.HoldoutObservationError, match="exhausted"):
        runner.run_once(
            "/bench", _full_gflags(),
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == ["spawn"] * 5


def test_issued_admission_cannot_be_reused_for_another_protected_ratio():
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="does not match"):
        runner.run_once(
            "/bench", _full_gflags("rr20"),
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=_issued("rr80"),
        )
    assert calls == []


def test_private_signature_token_cannot_authorize_another_private_signature():
    freeze = {
        "holdouts": {
            "rr79": {
                "candidate_id": "S1",
                "records": 79_000,
                "threads": 7,
                "ycsb": {
                    "ycsb_zipf_skew": "0.79",
                    "ycsb_rratio": "79",
                    "ycsb_rmw": "1",
                },
            },
            "rr23": {
                "candidate_id": "S2",
                "records": 23_000,
                "threads": 3,
                "ycsb": {
                    "ycsb_zipf_skew": "0.23",
                    "ycsb_rratio": "23",
                    "ycsb_rmw": "2",
                },
            },
        },
    }
    receipt = observation._new_durable_attempt_consumption_receipt(
        attempt_id="synthetic:0", permitted_run_once_calls=1,
    )
    token = observation._issue_holdout_observation_admission_from_receipt(
        receipt=receipt,
        verified_freeze_document=freeze,
        freeze_holdout_key="rr79",
        _neutral_holdouts=freeze["holdouts"],
    )
    calls = []

    def flags_for(key):
        entry = freeze["holdouts"][key]
        return [
            f"--ycsb_zipf_skew={entry['ycsb']['ycsb_zipf_skew']}",
            f"--ycsb_rratio={entry['ycsb']['ycsb_rratio']}",
            f"--ycsb_rmw={entry['ycsb']['ycsb_rmw']}",
            f"--ycsb_tuple_num={entry['records']}",
            f"--thread_num={entry['threads']}",
        ]
    with pytest.raises(observation.HoldoutObservationError, match="does not match"):
        runner.run_once(
            "/bench", flags_for("rr23"),
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == []
    runner.run_once(
        "/bench", flags_for("rr79"),
        subprocess_runner=lambda *_args, **_kwargs: (
            calls.append("spawn") or _completed_process()
        ),
        use_perf=False,
        holdout_observation_admission=token,
    )
    assert calls == ["spawn"]


def test_identity_capability_rejects_construction_copy_replace_pickle_and_dict():
    token = _issued("rr80")
    attacks = [
        observation.HoldoutObservationAdmission(
            signature=token.signature,
            attempt_id=token.attempt_id,
            permitted_run_once_calls=token.permitted_run_once_calls,
        ),
        copy.copy(token),
        dataclasses.replace(token),
        pickle.loads(pickle.dumps(token)),
        observation.HoldoutObservationAdmission(**dataclasses.asdict(token)),
    ]
    assert not hasattr(observation, "_seal")
    for forged in attacks:
        assert forged is not token
        with pytest.raises(observation.HoldoutObservationError, match="not issued"):
            observation.assert_issued_holdout_observation(forged)


def test_caller_constructed_token_cannot_reach_subprocess():
    genuine = _issued("rr80")
    forged = observation.HoldoutObservationAdmission(**dataclasses.asdict(genuine))
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="not issued"):
        runner.run_once(
            "/bench", _full_gflags(),
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=forged,
        )
    assert calls == []


@pytest.mark.parametrize("ratio", ["5", "50", "95"])
def test_non_holdout_ratios_keep_tokenless_spawn_and_return_shape(ratio):
    calls = []
    result = runner.run_once(
        "/bench", [f"-ycsb_rratio={ratio}"],
        subprocess_runner=lambda *_args, **_kwargs: (
            calls.append("spawn") or _completed_process()
        ),
        use_perf=False,
    )
    assert len(result) == 3
    assert calls == ["spawn"]


def test_private_neutral_source_still_requires_exact_signature_equality():
    freeze = _freeze()
    source = copy.deepcopy(freeze["holdouts"])
    first = next(iter(source.values()))
    first["candidate_id"] = "synthetic-drift"
    with pytest.raises(observation.HoldoutObservationError, match="exactly match"):
        observation._protected_signatures_from_verified_freeze_core(
            freeze,
            _neutral_holdouts=source,
        )


def test_subprocess_environment_removes_all_flags_prefix_inputs(monkeypatch):
    monkeypatch.setenv("FLAGS_ycsb_rratio", "80")
    monkeypatch.setenv("IZANAGI_ENV_CONTROL", "kept")
    seen = []

    def fake_run(*_args, **kwargs):
        seen.append(kwargs["env"])
        return _completed_process()

    runner.run_once(
        "/bench", ["-ycsb_rratio=50"],
        extra_env={"FLAGS_flagfile": "/tmp/indirect", "EXTRA_CONTROL": "kept"},
        subprocess_runner=fake_run,
        use_perf=False,
    )
    assert len(seen) == 1
    assert not any(key.startswith("FLAGS_") for key in seen[0])
    assert seen[0]["IZANAGI_ENV_CONTROL"] == "kept"
    assert seen[0]["EXTRA_CONTROL"] == "kept"


def test_measure_point_forwards_admission_only_when_non_none(monkeypatch):
    calls = []

    def fake_run_once(binary, gflags, **kwargs):
        calls.append((binary, list(gflags), dict(kwargs)))
        return ({"throughput[tps]": "1000", "maxrss": "100 kB"},
                PerfCounters(), 0.5)

    monkeypatch.setattr(runner, "run_once", fake_run_once)
    runner.measure_point(
        "/bench", records=1000, threads=4, clocks_per_us=1800,
        workload={"ycsb_rratio": "50"}, reps=1,
    )
    assert "holdout_observation_admission" not in calls[-1][2]

    token = _issued("rr80")
    runner.measure_point(
        "/bench", records=1000, threads=4, clocks_per_us=1800,
        workload={"ycsb_rratio": "80"}, reps=1,
        holdout_observation_admission=token,
    )
    assert calls[-1][2]["holdout_observation_admission"] is token

    capability = _issued_calibration("0" * 64)
    runner.measure_point(
        "/bench", records=100, threads=2, clocks_per_us=1800,
        workload={"ycsb_rratio": "80"}, reps=1,
        holdout_observation_admission=None,
        calibration_observation_capability=capability,
        calibration_observation_phase="sweep",
    )
    assert calls[-1][2]["calibration_observation_capability"] is capability
    assert calls[-1][2]["calibration_observation_phase"] == "sweep"


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
