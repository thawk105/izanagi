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

from orchestrator.campaign import backoff_extended_sweep, backoff_sweep
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


@pytest.mark.parametrize("baseline_raw", [-1, 5])
def test_backoff_screened_caller_forwards_intent_to_real_gate(monkeypatch, baseline_raw):
    """Caller spy runs real condition arms; campaign/performance setup is simulated."""
    driver = backoff_sweep.screening_driver
    source = _condition_fixture("supplied")
    cxx = _available_executable("g++-13", "g++-12", "g++")
    cmake = _available_executable("cmake")
    gs = [backoff_sweep.Genome("silo", {"BACKOFF_FIXED": raw})
          for raw in (baseline_raw, 5, 3000)]
    cfg = backoff_sweep.config_for("balanced", backoff_sweep.WORKLOADS[1][1])
    build_context = backoff_sweep.build_run_context(
        generator_id=backoff_sweep.GeneratorId.BACKOFF_SWEEP,
    )
    cfg = backoff_sweep.ident.bind_admission_policy(cfg, build_context.policy)
    contract = cfg.bound_environment_contract
    monkeypatch.setattr(backoff_sweep, "_compilers_for_current_site",
                        lambda: (cxx, cxx))
    monkeypatch.setattr(backoff_sweep.source_digest, "resolve",
                        lambda *args, **kwargs: "fixture-source")
    monkeypatch.setattr(backoff_sweep, "_assert_single_tenant", lambda: None)
    monkeypatch.setattr(driver, "attest_runtime_contract",
                        lambda *args, **kwargs: (None, None))

    @contextmanager
    def checkout(*args, **kwargs):
        yield str(source / "stock")

    monkeypatch.setattr(driver.patchharness, "checkout", checkout)

    def prepare(cfg, workload, baseline_ref, measure_baseline, **kwargs):
        layout = SimpleNamespace(root="fixture-screening")
        measure_baseline(cfg, layout)
        return SimpleNamespace(cfg=cfg, layout=layout, screening=None)

    monkeypatch.setattr(driver, "prepare_screening_campaign", prepare)
    observed = []

    def evaluate(cfg, layout, genome, *args, **kwargs):
        declaration = kwargs.get("backoff_fixed_declaration")
        run = driver._require_condition_gate_before_evaluation(
            str(source), cfg.ccbench_commit, genome, cxx=cxx, cmake=cmake,
            backoff_fixed_declaration=declaration,
        )
        raw = genome.flags["BACKOFF_FIXED"]
        assert run.admission.admitted
        assert [r.terminal_status for r in run.meaning_records] == [
            "unestablished" if raw == -1 else "green",
        ]
        assert (declaration is None) == (raw == -1)
        observed.append(raw)
        return SimpleNamespace(aborted=False, certified=True)

    monkeypatch.setattr(driver, "evaluate_candidate", evaluate)
    summary = backoff_sweep._run_screened_workload(
        cfg, gs, None, backoff_sweep.WORKLOADS[1][1], "", lambda *args: None,
        backoff_fixed_physical_us={5: 5, 3000: 1000},
        build_context=build_context,
        capability_resolver=None, runtime_contract=contract,
        authorization_contract=object(),
    )
    assert observed == [baseline_raw, 5, 3000]
    assert summary.evaluated == 3


def test_run_workload_shares_physical_mapping_with_screened_caller(monkeypatch):
    """Outer workflow wiring only; real screening meaning is tested separately."""
    captured = {}
    _stub_run_workload_dependencies(monkeypatch, captured)
    screened = []

    def run_screened(*args, **kwargs):
        screened.append(kwargs["backoff_fixed_physical_us"])
        return SimpleNamespace(results=[], committed=0, aborted=0)

    monkeypatch.setattr(backoff_sweep, "_run_screened_workload", run_screened)
    backoff_sweep.run_workload(
        "balanced", backoff_sweep.WORKLOADS[1][1],
        screening_enabled=True, log=lambda *args: None,
    )
    outer = captured["condition_gate_calls"][0][1]["backoff_fixed_physical_us"]
    assert outer == {5: 5}
    assert len(screened) == 1 and screened[0] is outer


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
        backoff_fixed_physical_us={5: 5},
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
    meaning = run.meaning_records[0]
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )
    expected_bits = backoff_sweep.condition_meaning_gate.canonical_float64_bits(5.0)
    assert {
        (row.expected_bits, row.observed_bits)
        for row in meaning.evidence["observations"]
    } == {(expected_bits, expected_bits)}
    assert run.admission.unestablished_meaning_macros == ()


def test_real_family_helper_observes_raw_3000_as_intended_static_1000():
    """An extended-style encoded point is checked against driver intent."""
    _available_executable("cmake")
    run = backoff_extended_sweep._require_condition_gate_before_measurement(
        str(_condition_fixture("supplied")),
        stock_root=str(_condition_fixture("supplied") / "stock"),
        points=[backoff_sweep.Genome("silo", {"BACKOFF_FIXED": 3000})],
        physical_grid=(1000,),
        cxx=_available_executable("g++-13", "g++-12", "g++"),
    )

    meaning = run.meaning_records[0]
    assert run.admission.admitted is True
    assert (meaning.terminal_status, meaning.reason_code) == (
        "green", "declared-meaning-observed",
    )
    expected_bits = backoff_sweep.condition_meaning_gate.canonical_float64_bits(
        1000.0
    )
    assert {
        (row.expected_bits, row.observed_bits)
        for row in meaning.evidence["observations"]
    } == {(expected_bits, expected_bits)}
    assert run.admission.unestablished_meaning_macros == ()


def test_real_family_helper_rejects_f718_intent_and_evaluator_records_red():
    """Raw 1000 cannot masquerade as the driver's intended static 1000 us."""
    condition_gate = backoff_sweep.condition_meaning_gate
    source_root = str(_condition_fixture("supplied"))
    cxx = _available_executable("g++-13", "g++-12", "g++")
    cmake = _available_executable("cmake")
    with pytest.raises(RuntimeError) as excinfo:
        backoff_sweep._require_backoff_condition_gate(
            source_root,
            stock_root=None,
            driver_id="orchestrator/campaign/backoff_sweep.py",
            macro_values={"BACKOFF_FIXED": (1000,)},
            backoff_fixed_physical_us={1000: 1000},
            cxx=cxx,
            cmake=cmake,
        )
    assert "BACKOFF_FIXED=red/decoded-meaning-mismatch" in str(excinfo.value)

    captured = condition_gate.capture_define_inputs(source_root)
    request = condition_gate.make_define_request(
        driver_id="orchestrator/campaign/backoff_sweep.py",
        macro="BACKOFF_FIXED",
        requested_value=1000,
        default_value=-1,
    )
    supply = condition_gate.evaluate_define_supply_effectuation(
        captured,
        request=request,
        cxx=cxx,
        cmake=cmake,
    )
    assert (supply.terminal_status, supply.reason_code) == (
        "green", "requested-default-preprocess-different",
    )
    expected_bits = condition_gate.canonical_float64_bits(1000.0)
    declaration = condition_gate.MeaningWitnessDeclaration(
        "BACKOFF_FIXED",
        (condition_gate.MeaningCase(1000, (expected_bits, expected_bits)),),
    )
    meaning = condition_gate.evaluate_define_runtime_meaning(
        captured,
        request=request,
        declaration=declaration,
        cxx=cxx,
    )
    assert (meaning.terminal_status, meaning.reason_code) == (
        "red", "decoded-meaning-mismatch",
    )
    assert meaning.evidence["expected"] == expected_bits
    assert meaning.evidence["observed"] == condition_gate.canonical_float64_bits(0.0)


def test_family_helper_rejects_physical_intent_contract_before_source_capture():
    """Missing, extra, and malformed intent entries fail before any build input."""
    common = {
        "source_root": "/source-must-not-be-captured",
        "stock_root": None,
        "driver_id": "orchestrator/campaign/backoff_sweep.py",
        "macro_values": {"BACKOFF_FIXED": (5,)},
        "cxx": "compiler-must-not-be-resolved",
    }
    for mapping in ({}, {5: 5, 6: 6}):
        with pytest.raises(RuntimeError, match="physical intent key mismatch"):
            backoff_sweep._require_backoff_condition_gate(
                **common, backoff_fixed_physical_us=mapping,
            )
    for mapping in ({5: True}, {5: -1}):
        with pytest.raises(RuntimeError, match="non-negative exact integers"):
            backoff_sweep._require_backoff_condition_gate(
                **common, backoff_fixed_physical_us=mapping,
            )


def test_real_family_helper_treats_minus_one_as_stock_identity():
    """The inert -1 request admits only when patched and stock owner bytes match."""
    source_root = _condition_fixture("supplied")
    run = backoff_sweep._require_backoff_condition_gate(
        str(source_root),
        stock_root=str(source_root / "stock"),
        driver_id="orchestrator/campaign/backoff_sweep.py",
        macro_values={"BACKOFF_FIXED": (-1,)},
        backoff_fixed_physical_us={},
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
            backoff_fixed_physical_us={},
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
            backoff_fixed_physical_us={5: 5},
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
    assert gate_kwargs["backoff_fixed_physical_us"] == {5: 5}
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
