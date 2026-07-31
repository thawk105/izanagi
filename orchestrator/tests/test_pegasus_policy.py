# -*- coding: utf-8 -*-
"""Pegasus site policy の分類・fail-closed・worker 境界テスト。

pytest と素の ``python3 orchestrator/tests/test_pegasus_policy.py`` の両方で走る。
"""

from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import subprocess
import sys


_REPO = Path(__file__).resolve().parents[2]
_TOOLS = _REPO / "tools"
sys.path.insert(0, str(_TOOLS))

import pegasus_policy as pp  # noqa: E402


def _raises(error_type, message, fn, *args, **kwargs):
    try:
        fn(*args, **kwargs)
    except error_type as exc:
        assert str(exc) == message
        return exc
    except Exception as exc:  # pragma: no cover - failure explanation
        raise AssertionError(
            f"expected {error_type.__name__}, got {type(exc).__name__}: {exc}"
        ) from exc
    raise AssertionError(f"expected {error_type.__name__}: {message}")


def _classify(hostname, pbs_job_id=None, affinity=(0, 1, 2, 3)):
    return pp.classify_site(hostname, pbs_job_id, affinity)


def test_login_short_exact_fqdn_case_and_trailing_dot():
    for hostname in (
        "pegasus01",
        "pegasus02.ccs.tsukuba.ac.jp",
        "PEGASUS03.CCS.TSUKUBA.AC.JP.",
    ):
        observation = _classify(hostname)
        assert observation.site_kind is pp.PEGASUS_LOGIN
        assert observation.hostname_raw == hostname
        assert observation.hostname_canonical == hostname.lower().removesuffix(".")
        assert observation.pbs_job_id_raw is None
        assert observation.pbs_job_id_normalized is None
        assert observation.affinity_cpus == (0, 1, 2, 3)


def test_compute_short_exact_fqdn_case_trailing_dot_and_pbs_normalization():
    cases = (
        ("bnode000", "19.nqsv", "19.nqsv"),
        ("bnode114.ccs.tsukuba.ac.jp", "0:874129.nqsv", "874129.nqsv"),
        ("BNODE999.CCS.TSUKUBA.AC.JP.", "7.nqsv", "7.nqsv"),
    )
    for hostname, raw_pbs, normalized_pbs in cases:
        observation = _classify(hostname, raw_pbs, affinity=(9, 3))
        assert observation.site_kind is pp.PEGASUS_COMPUTE
        assert observation.hostname_canonical == hostname.lower().removesuffix(".")
        assert observation.pbs_job_id_raw == raw_pbs
        assert observation.pbs_job_id_normalized == normalized_pbs
        assert observation.affinity_cpus == (3, 9)


def test_observation_is_frozen_and_exposes_stable_compatibility_properties():
    observation = _classify("host-7", affinity=(4, 2))
    assert observation.site_kind is pp.OTHER
    assert observation.raw_hostname == "host-7"
    assert observation.hostname == "host-7"
    assert observation.normalized_hostname == "host-7"
    assert observation.raw_pbs_job_id is None
    assert observation.pbs_job_id is None
    assert observation.normalized_pbs_job_id is None
    assert observation.site is pp.OTHER
    assert observation.available_cpu_count == 2
    _raises(
        FrozenInstanceError,
        "cannot assign to field 'site_kind'",
        setattr,
        observation,
        "site_kind",
        pp.PEGASUS_LOGIN,
    )


def test_direct_observation_construction_rejects_noncanonical_fields():
    base = {
        "hostname_raw": "worker",
        "hostname_canonical": "worker",
        "pbs_job_id_raw": None,
        "pbs_job_id_normalized": None,
        "affinity_cpus": (0,),
        "site_kind": pp.OTHER,
    }
    cases = (
        (
            {"hostname_canonical": "WORKER"},
            "site observation hostname fields are inconsistent",
        ),
        (
            {"pbs_job_id_normalized": "1.nqsv"},
            "site observation PBS fields are inconsistent",
        ),
        (
            {"affinity_cpus": ()},
            "CPU affinity must be a non-empty set of unique non-negative integers",
        ),
        (
            {"site_kind": "OTHER"},
            "site observation has an invalid site kind",
        ),
    )
    for changes, message in cases:
        values = dict(base)
        values.update(changes)
        _raises(pp.SitePolicyError, message, pp.SiteObservation, **values)


def test_evil_suffix_and_unknown_pegasus_domain_fail_closed():
    _raises(
        pp.SitePolicyError,
        "Pegasus-like hostname is not recognized",
        _classify,
        "pegasus01.ccs.tsukuba.ac.jp.evil",
    )
    for hostname in (
        "pegasus04.ccs.tsukuba.ac.jp",
        "worker.ccs.tsukuba.ac.jp",
        "ccs.tsukuba.ac.jp",
    ):
        _raises(
            pp.SitePolicyError,
            "Pegasus domain hostname is not recognized",
            _classify,
            hostname,
        )


def test_unknown_nqsv_future_bnode_and_qlogin_without_pbs_fail_closed():
    _raises(
        pp.SitePolicyError,
        "NQSV PBS_JOBID is inconsistent with hostname",
        _classify,
        "ci-host",
        "0:874129.nqsv",
    )
    for hostname in ("bnode1000", "bnode-next", "pegasus04", "bnode114.evil"):
        _raises(
            pp.SitePolicyError,
            "Pegasus-like hostname is not recognized",
            _classify,
            hostname,
        )
    _raises(
        pp.SitePolicyError,
        "Pegasus compute host requires an NQSV PBS_JOBID",
        _classify,
        "bnode114",
    )


def test_login_with_any_pbs_identity_fails_closed():
    for pbs_job_id in ("874129.nqsv", "0:874129.nqsv", "", "other"):
        _raises(
            pp.SitePolicyError,
            "Pegasus login host must not have PBS_JOBID",
            _classify,
            "pegasus01",
            pbs_job_id,
        )


def test_unrelated_host_without_pbs_is_other():
    for hostname in ("localhost", "worker-17", "node.example.org"):
        observation = _classify(hostname, affinity=(5,))
        assert observation.site_kind is pp.OTHER
        assert observation.affinity_cpus == (5,)


def test_unrelated_non_nqsv_pbs_is_other_and_preserves_raw_value():
    for raw_pbs in ("123.server", "batch-7.cluster.example", "opaque scheduler id"):
        observation = _classify("worker.example", raw_pbs, affinity=(5, 3))
        assert observation.site_kind is pp.OTHER
        assert observation.pbs_job_id_raw == raw_pbs
        assert observation.pbs_job_id_normalized is None
        assert observation.affinity_cpus == (3, 5)


def test_non_nqsv_pbs_does_not_relax_pegasus_identity_fail_closed_rules():
    for hostname, pbs_job_id, message in (
        (
            "pegasus04",
            "123.server",
            "Pegasus-like hostname is not recognized",
        ),
        (
            "bnode-next",
            "123.server",
            "Pegasus-like hostname is not recognized",
        ),
        (
            "worker.ccs.tsukuba.ac.jp",
            "123.server",
            "Pegasus domain hostname is not recognized",
        ),
    ):
        _raises(
            pp.SitePolicyError,
            message,
            _classify,
            hostname,
            pbs_job_id,
        )


def test_invalid_hostname_and_pbs_values_have_fixed_causes():
    for hostname in ("", ".bad", "bad..host", "host..", "höst", "bad_host", True):
        _raises(
            pp.SitePolicyError,
            "hostname must be a non-empty ASCII DNS name",
            _classify,
            hostname,
        )
    for pbs_job_id in (
        "",
        " ",
        "0:0:1.nqsv",
        "1.NQSV",
        "1.nqsv.evil",
        "１２.nqsv",
        True,
    ):
        _raises(
            pp.SitePolicyError,
            "PBS_JOBID must be an NQSV job ID",
            _classify,
            "bnode114",
            pbs_job_id,
        )


def test_affinity_rejects_empty_bool_duplicates_and_invalid_cpu_values():
    for affinity in ((), [], True, (True,), (-1,), (1, 1), ("1",), None):
        _raises(
            pp.SitePolicyError,
            "CPU affinity must be a non-empty set of unique non-negative integers",
            _classify,
            "worker",
            None,
            affinity,
        )


def test_observe_site_uses_injected_observers_and_preserves_raw_values():
    observation = pp.observe_site(
        hostname_fn=lambda: "BNODE114.CCS.TSUKUBA.AC.JP.",
        environ={"PBS_JOBID": "0:874129.nqsv"},
        affinity_fn=lambda pid: {11, 7} if pid == 0 else (),
    )
    assert observation.hostname_raw == "BNODE114.CCS.TSUKUBA.AC.JP."
    assert observation.hostname_canonical == "bnode114.ccs.tsukuba.ac.jp"
    assert observation.pbs_job_id_raw == "0:874129.nqsv"
    assert observation.pbs_job_id_normalized == "874129.nqsv"
    assert observation.affinity_cpus == (7, 11)
    assert observation.site_kind is pp.PEGASUS_COMPUTE


def test_observation_exceptions_are_fail_closed_without_payloads():
    def fail_hostname():
        raise RuntimeError("volatile hostname payload")

    class BadEnvironment:
        def get(self, key):
            raise RuntimeError(f"volatile environment payload: {key}")

    def fail_affinity(_pid):
        raise RuntimeError("volatile affinity payload")

    _raises(
        pp.SitePolicyError,
        "hostname observation failed",
        pp.observe_site,
        hostname_fn=fail_hostname,
        environ={},
        affinity_fn=lambda _pid: (0,),
    )
    _raises(
        pp.SitePolicyError,
        "PBS_JOBID observation failed",
        pp.observe_site,
        hostname_fn=lambda: "worker",
        environ=BadEnvironment(),
        affinity_fn=lambda _pid: (0,),
    )
    _raises(
        pp.SitePolicyError,
        "CPU affinity observation failed",
        pp.observe_site,
        hostname_fn=lambda: "worker",
        environ={},
        affinity_fn=fail_affinity,
    )


def test_other_without_affinity_api_uses_cpu_count_fallback():
    original_affinity = getattr(pp.os, "sched_getaffinity", None)
    had_affinity = hasattr(pp.os, "sched_getaffinity")
    calls = []

    def cpu_count():
        calls.append("cpu_count")
        return 6

    if had_affinity:
        delattr(pp.os, "sched_getaffinity")
    try:
        observation = pp.observe_site(
            hostname_fn=lambda: "worker.example",
            environ={"PBS_JOBID": "123.server"},
            cpu_count_fn=cpu_count,
        )
    finally:
        if had_affinity:
            setattr(pp.os, "sched_getaffinity", original_affinity)

    assert calls == ["cpu_count"]
    assert observation.site_kind is pp.OTHER
    assert observation.pbs_job_id_raw == "123.server"
    assert observation.pbs_job_id_normalized is None
    assert observation.affinity_cpus == tuple(range(6))


def test_affinity_fallback_never_resolves_pegasus_or_nqsv_uncertainty():
    original_affinity = getattr(pp.os, "sched_getaffinity", None)
    had_affinity = hasattr(pp.os, "sched_getaffinity")
    calls = []

    def cpu_count():
        calls.append("cpu_count")
        return 64

    if had_affinity:
        delattr(pp.os, "sched_getaffinity")
    try:
        cases = (
            (
                "worker.example",
                "874129.nqsv",
                "NQSV PBS_JOBID is inconsistent with hostname",
            ),
            (
                "pegasus04",
                None,
                "Pegasus-like hostname is not recognized",
            ),
            (
                "bnode114",
                None,
                "Pegasus compute host requires an NQSV PBS_JOBID",
            ),
            (
                "bnode114",
                "874129.nqsv",
                "CPU affinity observation failed",
            ),
        )
        for hostname, pbs_job_id, message in cases:
            _raises(
                pp.SitePolicyError,
                message,
                pp.observe_site,
                hostname_fn=lambda hostname=hostname: hostname,
                environ=(
                    {} if pbs_job_id is None else {"PBS_JOBID": pbs_job_id}
                ),
                cpu_count_fn=cpu_count,
            )
    finally:
        if had_affinity:
            setattr(pp.os, "sched_getaffinity", original_affinity)

    assert calls == []


def test_affinity_fallback_rejects_unusable_cpu_count():
    original_affinity = getattr(pp.os, "sched_getaffinity", None)
    had_affinity = hasattr(pp.os, "sched_getaffinity")
    if had_affinity:
        delattr(pp.os, "sched_getaffinity")
    try:
        for cpu_count in (None, 0, -1, True, "8"):
            _raises(
                pp.SitePolicyError,
                "CPU affinity observation failed",
                pp.observe_site,
                hostname_fn=lambda: "worker.example",
                environ={},
                cpu_count_fn=lambda cpu_count=cpu_count: cpu_count,
            )
    finally:
        if had_affinity:
            setattr(pp.os, "sched_getaffinity", original_affinity)


def test_default_pytest_workers_use_full_compute_affinity_and_other_cap_32():
    compute = _classify("bnode114", "874129.nqsv", range(48))
    other_many = _classify("worker", affinity=range(48))
    other_few = _classify("worker", affinity=range(7))
    assert pp.default_pytest_workers(compute) == 48
    assert pp.default_pytest_workers(other_many) == 32
    assert pp.default_pytest_workers(other_few) == 7


def test_policy_exports_no_pytest_collectable_or_build_jobs_names():
    assert "default_pytest_workers" in pp.__all__
    assert not hasattr(pp, "test_default_workers")
    assert not hasattr(pp, "test_default_jobs")
    assert all(
        not (name.startswith("test_") and callable(getattr(pp, name)))
        for name in pp.__all__
    )


def test_explicit_worker_precedence_serial_and_compute_boundaries():
    compute = _classify("bnode114", "874129.nqsv", range(4))
    other = _classify("worker", affinity=(0,))
    assert pp.resolve_test_workers(None, compute) == 4
    assert pp.resolve_test_workers(0, compute) == 0
    assert pp.resolve_test_workers(3, compute) == 3
    assert pp.resolve_test_workers(4, compute) == 4
    assert pp.resolve_test_workers(0, other) == 0
    assert pp.resolve_test_workers(99, other) == 99
    _raises(
        pp.SitePolicyError,
        "test worker count exceeds compute CPU affinity",
        pp.resolve_test_workers,
        5,
        compute,
    )
    for invalid in (True, False, -1, "4", 1.5):
        _raises(
            pp.SitePolicyError,
            (
                "test worker count must be auto, logical, or an integer "
                "greater than or equal to zero"
            ),
            pp.resolve_test_workers,
            invalid,
            other,
        )


def test_symbolic_xdist_values_are_preserved_only_for_other():
    compute = _classify("bnode114", "874129.nqsv", range(4))
    other = _classify("worker", affinity=(0,))
    for symbolic in ("auto", "logical"):
        assert pp.resolve_test_workers(symbolic, other) == symbolic
        assert pp.resolve_test_workers(symbolic, compute) == 4
    assert pp.resolve_test_workers(0, other) == 0
    assert pp.resolve_test_workers(0, compute) == 0
    for invalid in ("AUTO", "all", "max", "", "-1"):
        _raises(
            pp.SitePolicyError,
            (
                "test worker count must be auto, logical, or an integer "
                "greater than or equal to zero"
            ),
            pp.resolve_test_workers,
            invalid,
            other,
        )


def test_login_worker_resolution_never_allows_local_execution():
    login = _classify("pegasus01")
    for explicit in (None, 0, 1, "auto", "logical"):
        _raises(
            pp.SitePolicyError,
            "test workers cannot be resolved on a Pegasus login host",
            pp.resolve_test_workers,
            explicit,
            login,
        )


def test_policy_is_stdlib_only_and_has_no_build_jobs_resolver():
    tree = ast.parse((_TOOLS / "pegasus_policy.py").read_text(encoding="utf-8"))
    imported_roots = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots <= {
        "__future__",
        "collections",
        "dataclasses",
        "enum",
        "os",
        "re",
        "socket",
    }
    assert not hasattr(pp, "resolve_build_jobs")


def test_canonical_import_succeeds_under_python_isolated_mode():
    code = (
        "import sys;"
        f"sys.path.insert(0, {str(_TOOLS)!r});"
        "import pegasus_policy as p;"
        "assert p.__name__ == 'pegasus_policy';"
        "assert p.classify_site('worker', None, (0,)).site is p.OTHER"
    )
    completed = subprocess.run(
        [sys.executable, "-I", "-B", "-c", code],
        cwd=_REPO,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr


def _run():
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS {test.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {test.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed} passed, {failed} failed")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_run())
