# -*- coding: utf-8 -*-
from __future__ import annotations

import ast
from collections.abc import Sequence
import copy
import dataclasses
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
from orchestrator.campaign import trial_registry  # noqa: E402


def _freeze() -> dict[str, object]:
    return {
        "holdouts": {
            "rr80": {
                "candidate_id": "H1",
                "ycsb": {"ycsb_rratio": "80"},
            },
            "rr20": {
                "candidate_id": "H2",
                "ycsb": {"ycsb_rratio": "20"},
            },
        },
    }


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
         item.trial_workload_name, item.ycsb_rratio)
        for item in signatures
    } == {
        ("rr80", "H1", "rr80", "80"),
        ("rr20", "H2", "rr20", "20"),
    }


def test_no_supported_public_api_can_issue_an_observation_token():
    assert "issue_holdout_observation_admission" not in observation.__all__
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
        "ycsb": {"ycsb_rratio": "30"},
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
            "ycsb_rratio": item.ycsb_rratio,
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
        "/bench", ["--ycsb_rratio=80"],
        subprocess_runner=lambda *args, **kwargs: (
            calls.append((args, kwargs)) or _completed_process()
        ),
        use_perf=False,
        holdout_observation_admission=_issued("rr80"),
    )
    assert len(result) == 3
    assert len(calls) == 1


def test_attempt_admission_rejects_run_once_beyond_permitted_count():
    token = _issued("rr80", attempt_id="planned:2", uses=2)
    calls = []
    for _ in range(2):
        runner.run_once(
            "/bench", ["--ycsb_rratio=80"],
            subprocess_runner=lambda *_args, **_kwargs: (
                calls.append("spawn") or _completed_process()
            ),
            use_perf=False,
            holdout_observation_admission=token,
        )
    with pytest.raises(observation.HoldoutObservationError, match="exhausted"):
        runner.run_once(
            "/bench", ["--ycsb_rratio=80"],
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == ["spawn", "spawn"]


def test_one_attempt_allows_exactly_one_measure_point_repetition_set():
    token = _issued("rr80", attempt_id="planned:3", uses=5)
    calls = []
    runner.measure_point(
        "/bench", records=1000, threads=4, clocks_per_us=1800,
        workload={"ycsb_rratio": "80"}, reps=5,
        subprocess_runner=lambda *_args, **_kwargs: (
            calls.append("spawn") or _completed_process()
        ),
        rep_observations=[], use_perf=False,
        holdout_observation_admission=token,
    )
    with pytest.raises(observation.HoldoutObservationError, match="exhausted"):
        runner.run_once(
            "/bench", ["--ycsb_rratio=80"],
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == ["spawn"] * 5


def test_issued_admission_cannot_be_reused_for_another_protected_ratio():
    calls = []
    with pytest.raises(observation.HoldoutObservationError, match="does not match"):
        runner.run_once(
            "/bench", ["--ycsb_rratio=20"],
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
                "ycsb": {"ycsb_rratio": "79"},
            },
            "rr23": {
                "candidate_id": "S2",
                "ycsb": {"ycsb_rratio": "23"},
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
    with pytest.raises(observation.HoldoutObservationError, match="does not match"):
        runner.run_once(
            "/bench", ["--ycsb_rratio=23"],
            subprocess_runner=lambda *_args, **_kwargs: calls.append("spawn"),
            use_perf=False,
            holdout_observation_admission=token,
        )
    assert calls == []
    runner.run_once(
        "/bench", ["--ycsb_rratio=79"],
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
            freeze_holdout_key=token.freeze_holdout_key,
            freeze_candidate_id=token.freeze_candidate_id,
            trial_workload_name=token.trial_workload_name,
            ycsb_rratio=token.ycsb_rratio,
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
            "/bench", ["-ycsb_rratio=80"],
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


def _run() -> int:
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    raise SystemExit(_run())
