import os
import hashlib
import inspect
import shutil
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_sweep
from orchestrator.campaign.durable_root import DurableRootPolicy


def _stub_run_workload_dependencies(monkeypatch, captured):
    captured.setdefault("events", [])
    captured.setdefault("masstree_prepare_calls", [])
    captured.setdefault("condition_gate_calls", [])
    contract = SimpleNamespace(
        env_tag="test-env",
        clocks_per_us=123,
        numactl=(),
        attestation_mode="none",
    )
    context = SimpleNamespace(policy=object())

    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "resolve_site_runtime",
        lambda: ("test-site", contract, object()),
    )
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "_assert_matches_calibration",
        lambda _contract: None,
    )
    monkeypatch.setattr(
        backoff_sweep,
        "genomes",
        lambda: [backoff_sweep.Genome("silo", {"BACKOFF_FIXED": 5})],
    )
    monkeypatch.setattr(backoff_sweep, "config_for", lambda *args, **kwargs: object())
    monkeypatch.setattr(
        backoff_sweep.p2_2,
        "_campaign_cfg_for_site",
        lambda cfg, _site, _contract: cfg,
    )
    monkeypatch.setattr(
        backoff_sweep,
        "_compilers_for_current_site",
        lambda: ("cc", "cxx"),
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache,
        "observed_toolchain_manifest",
        lambda cc, cxx: {"cc": cc, "cxx": cxx},
    )
    monkeypatch.setattr(backoff_sweep, "build_run_context", lambda **kwargs: context)
    monkeypatch.setattr(
        backoff_sweep.ident,
        "bind_admission_policy",
        lambda cfg, _policy: cfg,
    )

    def capture_run_campaign(*_args, **kwargs):
        captured.update(kwargs)
        return SimpleNamespace(results=[], committed=0, aborted=0)

    monkeypatch.setattr(backoff_sweep, "run_campaign", capture_run_campaign)

    @contextmanager
    def checkout(*_args, **_kwargs):
        yield "/stock"

    @contextmanager
    def applied(*_args, **_kwargs):
        yield []

    monkeypatch.setattr(backoff_sweep.patchharness, "checkout", checkout)
    monkeypatch.setattr(backoff_sweep.patchharness, "applied", applied)

    def prepare_masstree_fetchcontent(**kwargs):
        captured.setdefault("events", []).append("prepare_masstree_fetchcontent")
        captured.setdefault("masstree_prepare_calls", []).append(kwargs)

    monkeypatch.setattr(
        backoff_sweep.buildcache,
        "prepare_masstree_fetchcontent",
        prepare_masstree_fetchcontent,
    )

    def require_condition_gate(*args, **kwargs):
        captured.setdefault("events", []).append("condition_gate")
        captured.setdefault("condition_gate_calls", []).append((args, kwargs))
        return object()

    monkeypatch.setattr(
        backoff_sweep,
        "_require_backoff_condition_gate",
        require_condition_gate,
    )
    monkeypatch.setattr(
        backoff_sweep.buildcache, "_ccbench_dir", lambda: "/ccbench",
    )


def _condition_fixture(name: str) -> Path:
    return (
        Path(__file__).parent / "fixtures" / "condition_meaning_gate" / name
    )


def _available_executable(*names: str) -> str:
    for name in names:
        resolved = shutil.which(name)
        if resolved is not None:
            return resolved
    pytest.skip(f"required executable is unavailable: {names!r}")


def _independent_replay_digest(record) -> str:
    argv = list(record.evidence["requested_replay_argv"])
    index = 0
    while index < len(argv):
        if argv[index] in {"-MD", "-MMD", "-MP", "-MG"}:
            del argv[index]
            continue
        if argv[index] == "-MF":
            del argv[index:index + 2]
            continue
        index += 1
    completed = subprocess.run(argv, check=True, capture_output=True)
    assert completed.stderr == b""
    return hashlib.sha256(completed.stdout).hexdigest()


def test_real_family_helper_admits_effective_define_and_recomputes_file_digest():
    """A real owner-TU byte difference admits the raw build request."""
    configure_arg = "-DCMAKE_VERBOSE_MAKEFILE=ON"
    run = backoff_sweep._require_backoff_condition_gate(
        str(_condition_fixture("supplied")),
        stock_root=None,
        driver_id="orchestrator/campaign/backoff_sweep.py",
        macro_values={"BACKOFF_FIXED": (5,)},
        cxx=_available_executable("g++-13", "g++-12", "g++"),
        cmake=_available_executable("cmake"),
        configure_args=(configure_arg,),
    )

    supply = run.supply_records[0]
    assert run.admission.admitted is True
    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    assert configure_arg in supply.evidence["requested_configure_argv"]
    assert configure_arg in supply.evidence["control_configure_argv"]
    assert _independent_replay_digest(supply) == supply.evidence["requested_digest"]
    assert run.meaning_records[0].terminal_status == "unestablished"


def test_real_family_helper_treats_minus_one_as_stock_identity():
    """The inert -1 request admits only when patched and stock owner bytes match."""
    source_root = _condition_fixture("supplied")
    run = backoff_sweep._require_backoff_condition_gate(
        str(source_root),
        stock_root=str(source_root / "stock"),
        driver_id="orchestrator/campaign/backoff_sweep.py",
        macro_values={"BACKOFF_FIXED": (-1,)},
        cxx=_available_executable("g++-13", "g++-12", "g++"),
        cmake=_available_executable("cmake"),
    )

    supply = run.supply_records[0]
    assert run.admission.admitted is True
    assert (supply.terminal_status, supply.reason_code) == (
        "green", "stock-inert-preprocess-identical",
    )
    assert supply.evidence["requested_digest"] == supply.evidence["control_digest"]
    assert _independent_replay_digest(supply) == supply.evidence["requested_digest"]
    meaning = run.meaning_records[0]
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )
    assert meaning.evidence["observed_branch"] == (
        backoff_sweep.condition_meaning_gate.STOCK_ADAPTIVE_BRANCH
    )


def test_real_family_helper_rejects_minus_one_without_stock_tree():
    """An inert request cannot reach a driver without its stock control tree."""
    with pytest.raises(RuntimeError, match="stock-tree-unavailable"):
        backoff_sweep._require_backoff_condition_gate(
            str(_condition_fixture("supplied")),
            stock_root=None,
            driver_id="orchestrator/campaign/backoff_sweep.py",
            macro_values={"BACKOFF_FIXED": (-1,)},
            cxx=_available_executable("g++-13", "g++-12", "g++"),
            cmake=_available_executable("cmake"),
        )


def test_real_family_helper_rejects_ignored_define_before_any_driver_build():
    """Identical real owner-TU bytes reject the raw build request."""
    with pytest.raises(RuntimeError, match="preprocess-bytes-identical"):
        backoff_sweep._require_backoff_condition_gate(
            str(_condition_fixture("effectuation-ignored")),
            stock_root=None,
            driver_id="orchestrator/campaign/backoff_sweep.py",
            macro_values={"BACKOFF_FIXED": (5,)},
            cxx=_available_executable("g++-13", "g++-12", "g++"),
            cmake=_available_executable("cmake"),
        )


def test_sweep_condition_gate_dominates_screened_and_direct_campaign_paths():
    source = inspect.getsource(backoff_sweep.run_workload)
    checkout = source.index("with patchharness.checkout")
    patch = source.index("with patchharness.applied")
    prepare = source.index("prepare_masstree_fetchcontent")
    gate = source.index("_require_backoff_condition_gate")
    screened = source.index("_run_screened_workload")
    direct = source.index("run_campaign(")
    assert checkout < patch < prepare < gate < screened
    assert checkout < patch < prepare < gate < direct


def test_run_workload_prepares_masstree_once_before_condition_gate(monkeypatch):
    captured = {}
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    assert len(captured["masstree_prepare_calls"]) == 1
    assert captured["events"] == [
        "prepare_masstree_fetchcontent", "condition_gate",
    ]
    prepare = captured["masstree_prepare_calls"][0]
    assert prepare["expected_toolchain_manifest"] == {"cc": "cc", "cxx": "cxx"}
    assert prepare["configure_timeout_s"] == 900
    assert prepare["target_timeout_s"] == 900
    assert prepare["site"] == "test-site"
    assert "dependency_prefix" not in prepare


def test_run_workload_gates_the_prepared_patched_tree_with_fetchcontent_base(
        monkeypatch):
    captured = {}
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    prepare = captured["masstree_prepare_calls"][0]
    gate_args, gate_kwargs = captured["condition_gate_calls"][0]
    canonical_base = prepare["fetchcontent_base_dir"]
    assert gate_kwargs["configure_args"] == (
        f"-DFETCHCONTENT_BASE_DIR={canonical_base}",
    )
    prepared_root = Path(prepare["ccbench_dir"]).resolve()
    gated_root = Path(gate_args[0]).resolve()
    patched_root = Path(backoff_sweep.buildcache._ccbench_dir()).resolve()
    assert prepared_root == gated_root == patched_root
    assert gated_root != Path(gate_kwargs["stock_root"]).resolve()
    assert Path(canonical_base).is_absolute()
    assert os.path.realpath(canonical_base) == os.path.abspath(canonical_base)


def test_official_output_root_policy_is_passed_to_run_campaign(monkeypatch, tmp_path):
    captured = {}
    monkeypatch.setenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", str(tmp_path))
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    policy = captured["durable_root_policy"]
    assert isinstance(policy, DurableRootPolicy)
    assert policy.approved_roots == (tmp_path.resolve(),)
    assert policy.forbidden_roots == ()


def test_without_official_output_root_policy_is_omitted(monkeypatch):
    captured = {}
    monkeypatch.delenv("IZANAGI_OFFICIAL_OUTPUT_ROOT", raising=False)
    _stub_run_workload_dependencies(monkeypatch, captured)

    backoff_sweep.run_workload(
        "read-heavy",
        {"ycsb_zipf_skew": "0.9", "ycsb_rratio": "95", "ycsb_rmw": "0"},
        log=lambda _message: None,
    )

    assert captured["durable_root_policy"] is None


# ---- 素の runner (直接起動でも pytest を実行) ----

def _run():
    import pytest
    return pytest.main([__file__, "-q"])


if __name__ == "__main__":
    sys.exit(_run())
